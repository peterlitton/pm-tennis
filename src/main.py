"""FastAPI app.

Serves the dashboard HTML at /, the current state as JSON at /api/matches,
and pushes state snapshots over WS at /ws/matches.

The API-Tennis worker runs as a background asyncio task started on lifespan.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from . import api_tennis_worker, polymarket_global_worker, polymarket_worker, state, state_recorder

# Step 7 trade attribution. Module is shipped but not activated by default.
# Set TRADE_ATTRIBUTION_ENABLED=1 to activate without a code change.
# Sequencing decision per working log 2026-04-27: activate ~7-10 days
# after Step 8 begins capturing data (target 2026-05-04 to 2026-05-07).
from . import trade_attribution

# Trades CSV — operator-friendly daily trade export.
from . import trades_csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Jinja2Templates(directory=ROOT / "templates")

# Push cadence for WS snapshots. Tighten if it feels laggy in real use.
WS_PUSH_INTERVAL_SEC = 1.0

TRADE_ATTRIBUTION_ENABLED = os.environ.get("TRADE_ATTRIBUTION_ENABLED", "").strip() in ("1", "true", "yes", "on")

# CSV endpoint config — token reused as REPORTS_TOKEN env var
REPORTS_TOKEN = os.environ.get("REPORTS_TOKEN", "").strip()
CSV_DEFAULT_TZ = os.environ.get("CSV_DEFAULT_TZ", "America/New_York")


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_task = asyncio.create_task(api_tennis_worker.run(), name="api_tennis_worker")
    pm_task = asyncio.create_task(polymarket_worker.run(), name="polymarket_worker")
    # v0.8.0 LIVE (cutover from shadow mode 2026-05-06): Polymarket
    # Global price feed is now the source of truth for the production
    # dashboard. The polymarket_worker resolver (in
    # polymarket_worker._resolver_iteration) reads
    # polymarket_global_worker.slug_prices instead of its own US-derived
    # slug_prices. The US worker continues running for trade attribution
    # and position/order reads (which are NOT migrated this shipment;
    # see PM-Tennis-Pricing-Architecture-Handoff.md section 4.1).
    # Inspect via /api/global-diag, /dashboard-replica, /validation-live,
    # /raw-stream-live for live debugging.
    pm_global_task = asyncio.create_task(
        polymarket_global_worker.run(), name="polymarket_global_worker"
    )
    # Step 8: state recorder. Pure capture of dashboard state to JSONL on
    # disk. Writes to /var/data/state_log (Render Disk mount) by default.
    recorder_task = asyncio.create_task(state_recorder.run(), name="state_recorder")

    workers = [api_task, pm_task, pm_global_task, recorder_task]
    worker_names = "api_tennis_worker, polymarket_worker (US, trades/positions/orders), polymarket_global_worker (Global, prices — LIVE), state_recorder"

    # Step 7: trade attribution. Behind env flag — see module docstring.
    attr_task = None
    if TRADE_ATTRIBUTION_ENABLED:
        attr_task = asyncio.create_task(trade_attribution.run(), name="trade_attribution")
        workers.append(attr_task)
        worker_names += ", trade_attribution"
        log.info("Step 7 trade attribution: ENABLED")
    else:
        log.info("Step 7 trade attribution: shipped but not activated (set TRADE_ATTRIBUTION_ENABLED=1 to activate)")

    log.info("workers started: %s", worker_names)
    try:
        yield
    finally:
        for t in workers:
            t.cancel()
        for t in workers:
            try:
                await t
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception("worker shutdown error")
        log.info("workers stopped")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
async def dashboard(request: Request):
    return TEMPLATES.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/matches")
async def matches_json():
    return JSONResponse(state.snapshot())


@app.get("/api/extraction-diag")
async def extraction_diag():
    """v0.7.7 EXTRACTION DIAGNOSTIC endpoint — per-frame WS price candidates.

    Returns a JSON dump of the per-slug ring buffers populated by
    `polymarket_worker._capture_extraction_diag`. Each entry corresponds to
    one WS market_data frame and records all candidate side-A and side-B
    price sources alongside the value the dashboard rendered at that moment.

    Used by the off-process render script (diag-snapshot.sh) to produce
    per-player tables comparing source cadences over time.

    Diagnostic-only. Public (matches /api/matches pattern). Removable when
    the asymmetric-stuck-side investigation closes.
    """
    out: dict[str, list[dict]] = {}
    metadata: dict[str, dict] = {}
    # Snapshot copy — buffers may be appended to while we serialize
    for slug, buf in list(polymarket_worker._extraction_diag_buffers.items()):
        out[slug] = list(buf)
        meta = polymarket_worker.slug_metadata.get(slug)
        if meta:
            metadata[slug] = {
                "player_a_name": meta.get("player_a_name"),
                "player_b_name": meta.get("player_b_name"),
                "event_key": meta.get("event_key"),
            }
    return JSONResponse({
        "version": "v0.7.7",
        "buffer_size_per_slug": polymarket_worker.EXTRACTION_DIAG_BUFFER_SIZE,
        "slugs": out,
        "metadata": metadata,
    })


@app.get("/api/global-diag")
async def global_diag():
    """v0.8.0 SHADOW MODE diagnostic endpoint — Polymarket Global price feed.

    Returns the full state of the new ``polymarket_global_worker`` for
    side-by-side comparison with the existing ``polymarket_worker`` and
    with the operator's iPhone app.

    Per-slug payload includes:
      - player_a_name, player_b_name, tournament_name, event_date
      - global_question (matched Gamma market question)
      - token_a, token_b (ERC1155 token IDs)
      - global_status: "resolved" | "no_global_market"
      - side_a_cents, side_b_cents (validated display rule: best_bid in cents)
      - side_a_bid_cents/ask_cents/last_cents/age_ms (diagnostic)
      - side_b_bid_cents/ask_cents/last_cents/age_ms (diagnostic)
      - updated_ms (local timestamp of last projection)

    Used during Phase 2 validation to compare against /api/matches
    and the iPhone app. Will be retired or scoped down when Phase 4
    cleanup happens.
    """
    out: dict[str, dict] = {}
    # Snapshot copy — dicts may be mutated while we serialize
    for slug in list(polymarket_global_worker.slug_metadata.keys()):
        meta = polymarket_global_worker.slug_metadata.get(slug, {})
        prices = polymarket_global_worker.slug_prices.get(slug, {})
        out[slug] = {
            "player_a_name": meta.get("player_a_name"),
            "player_b_name": meta.get("player_b_name"),
            "tournament_name": meta.get("tournament_name"),
            "event_date": meta.get("event_date"),
            "polymarket_event_id": meta.get("polymarket_event_id"),
            "global_question": meta.get("global_question"),
            "global_status": meta.get("global_status"),
            "token_a": meta.get("token_a"),
            "token_b": meta.get("token_b"),
            **prices,
        }
    return JSONResponse({
        "version": "v0.8.0-live",
        "match_count": len(out),
        "matches": out,
    })


@app.get("/global-diag-live", response_class=HTMLResponse)
async def global_diag_live():
    """Live browser view of polymarket_global_worker prices.

    Renders a self-contained HTML page that:
      - Lets the operator pick a match from a dropdown
      - Shows both players side-by-side with bid/ask/display/last/age
      - Auto-refreshes from /api/global-diag every 500ms
      - Logs each refresh as a timestamped row so price history is visible

    No external assets, no React, no JSON-API churn — just a fetch loop
    and a table. Used for one-match iPhone comparison during Phase 2
    validation.
    """
    return HTMLResponse(_GLOBAL_DIAG_LIVE_HTML)


_GLOBAL_DIAG_LIVE_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>PM Global Diag — Live</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; margin: 16px; background:#fafafa; color:#222; }
  h1 { font-size: 16px; margin: 0 0 12px; }
  .controls { margin-bottom: 12px; display: flex; gap: 12px; align-items: center; }
  select { font-size: 14px; padding: 6px 10px; min-width: 380px; }
  .meta { font-size: 12px; color:#666; }
  table { border-collapse: collapse; width: 100%; background: white; }
  th, td { padding: 4px 8px; text-align: left; border-bottom: 1px solid #eee; font-size: 12px; }
  th { background:#f0f0f0; font-weight: 600; position: sticky; top: 0; z-index: 1; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  td.time { font-variant-numeric: tabular-nums; color:#666; width: 80px; }
  td.player-name { font-weight: 600; padding: 8px 8px; }
  .a-cells { background: #f7faff; }
  .b-cells { background: #fff7f7; }
  .a-cells.changed { background: #fff5b8; transition: background 1.5s; }
  .b-cells.changed { background: #fff5b8; transition: background 1.5s; }
  .display { font-weight: 700; }
  .stale { color: #c00; }
  .empty { padding: 24px; color:#888; font-size: 14px; text-align: center; }
</style>
</head><body>
<h1>PM Global Diag — Live (validated rule: display = best bid)</h1>
<div class="controls">
  <select id="picker"><option>loading matches…</option></select>
  <span class="meta" id="meta">—</span>
</div>
<table id="t">
<thead>
  <tr>
    <th rowspan="2" class="time">Time</th>
    <th colspan="6" id="hdrA" class="player-name a-cells">Player A</th>
    <th colspan="6" id="hdrB" class="player-name b-cells">Player B</th>
  </tr>
  <tr>
    <th class="num a-cells">Bid</th><th class="num a-cells">Ask</th>
    <th class="num a-cells">Display</th><th class="num a-cells">Last</th>
    <th class="num a-cells">Age</th><th class="num a-cells">Frames</th>
    <th class="num b-cells">Bid</th><th class="num b-cells">Ask</th>
    <th class="num b-cells">Display</th><th class="num b-cells">Last</th>
    <th class="num b-cells">Age</th><th class="num b-cells">Frames</th>
  </tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div class="empty" id="empty" style="display:none">No data for this match yet.</div>
<script>
const POLL_MS = 500;
const MAX_ROWS = 600;

let lastSelectedSlug = null;
let prevA = null, prevB = null;

function fmtCents(c) {
  if (c === null || c === undefined) return "—";
  return c + "c";
}
function fmtAge(ms) {
  if (ms === null || ms === undefined) return "—";
  return (ms/1000).toFixed(1) + "s";
}
function ageClass(ms) {
  if (ms === null || ms === undefined) return "";
  return ms > 5000 ? "stale" : "";
}
function nowStr() {
  return new Date().toLocaleTimeString();
}

async function refreshPicker(currentSlug) {
  // Repopulate dropdown if matches changed (new live match starts, etc).
  // Preserve current selection.
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const picker = document.getElementById("picker");
    const oldVal = picker.value;
    const slugs = Object.keys(data.matches).sort((a,b) => {
      // alphabetical by player A surname
      const pa = (data.matches[a].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      const pb = (data.matches[b].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      return pa.localeCompare(pb);
    });
    const expected = slugs.map(s => {
      const m = data.matches[s];
      return s + "|" + (m.player_a_name||"") + "|" + (m.player_b_name||"");
    }).join(";");
    if (picker.dataset.signature === expected) return;  // unchanged
    picker.dataset.signature = expected;
    picker.innerHTML = "";
    if (slugs.length === 0) {
      const o = document.createElement("option");
      o.textContent = "no live matches";
      o.value = "";
      picker.appendChild(o);
      return;
    }
    for (const s of slugs) {
      const m = data.matches[s];
      const o = document.createElement("option");
      o.value = s;
      o.textContent = (m.player_a_name || "?") + "  vs  " + (m.player_b_name || "?")
                    + (m.tournament_name ? "  ("+m.tournament_name+")" : "");
      picker.appendChild(o);
    }
    if (slugs.includes(oldVal)) {
      picker.value = oldVal;
    } else {
      picker.value = slugs[0];
      onMatchChange();
    }
  } catch (e) {
    document.getElementById("meta").textContent = "picker fetch error: " + e.message;
  }
}

function onMatchChange() {
  const slug = document.getElementById("picker").value;
  if (slug === lastSelectedSlug) return;
  lastSelectedSlug = slug;
  prevA = null; prevB = null;
  document.getElementById("tbody").innerHTML = "";
  document.getElementById("empty").style.display = "none";
}

async function pollAndAppend() {
  const slug = document.getElementById("picker").value;
  if (!slug) return;
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const m = data.matches[slug];
    if (!m) {
      document.getElementById("empty").style.display = "";
      document.getElementById("empty").textContent = "match no longer live";
      return;
    }
    document.getElementById("empty").style.display = "none";
    document.getElementById("hdrA").textContent = m.player_a_name || "Player A";
    document.getElementById("hdrB").textContent = m.player_b_name || "Player B";

    const a = {
      bid: m.side_a_bid_cents,
      ask: m.side_a_ask_cents,
      display: m.side_a_cents,
      last: m.side_a_last_cents,
      age: m.side_a_age_ms,
      frames: m.side_a_bid_cents !== undefined ? "—" : "—",  // not in payload; placeholder
    };
    const b = {
      bid: m.side_b_bid_cents,
      ask: m.side_b_ask_cents,
      display: m.side_b_cents,
      last: m.side_b_last_cents,
      age: m.side_b_age_ms,
      frames: "—",
    };

    const aChanged = !prevA || prevA.display !== a.display || prevA.bid !== a.bid || prevA.ask !== a.ask;
    const bChanged = !prevB || prevB.display !== b.display || prevB.bid !== b.bid || prevB.ask !== b.ask;
    prevA = a; prevB = b;

    // Only append a row if SOMETHING changed (else table fills with duplicates).
    if (!aChanged && !bChanged) return;

    const tbody = document.getElementById("tbody");
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td class="time">' + nowStr() + '</td>' +
      '<td class="num a-cells '+(aChanged?"changed":"")+'">' + fmtCents(a.bid) + '</td>' +
      '<td class="num a-cells '+(aChanged?"changed":"")+'">' + fmtCents(a.ask) + '</td>' +
      '<td class="num a-cells display '+(aChanged?"changed":"")+'">' + fmtCents(a.display) + '</td>' +
      '<td class="num a-cells '+(aChanged?"changed":"")+'">' + fmtCents(a.last) + '</td>' +
      '<td class="num a-cells '+ageClass(a.age)+'">' + fmtAge(a.age) + '</td>' +
      '<td class="num a-cells">—</td>' +
      '<td class="num b-cells '+(bChanged?"changed":"")+'">' + fmtCents(b.bid) + '</td>' +
      '<td class="num b-cells '+(bChanged?"changed":"")+'">' + fmtCents(b.ask) + '</td>' +
      '<td class="num b-cells display '+(bChanged?"changed":"")+'">' + fmtCents(b.display) + '</td>' +
      '<td class="num b-cells '+(bChanged?"changed":"")+'">' + fmtCents(b.last) + '</td>' +
      '<td class="num b-cells '+ageClass(b.age)+'">' + fmtAge(b.age) + '</td>' +
      '<td class="num b-cells">—</td>';
    tbody.insertBefore(tr, tbody.firstChild);

    while (tbody.children.length > MAX_ROWS) {
      tbody.removeChild(tbody.lastChild);
    }
    document.getElementById("meta").textContent =
      "status: " + (m.global_status || "?") + "  |  " + tbody.children.length + " events shown";
  } catch (e) {
    document.getElementById("meta").textContent = "fetch error: " + e.message;
  }
}

document.getElementById("picker").addEventListener("change", onMatchChange);
refreshPicker();
setInterval(refreshPicker, 5000);
setInterval(pollAndAppend, POLL_MS);
</script>
</body></html>
"""


@app.get("/validation-live", response_class=HTMLResponse)
async def validation_live():
    """Three-column validation waterfall.

    Pick a match. New row appears every time either player's best_bid
    changes. Columns: date/time | player A best_bid | player B best_bid.
    """
    return HTMLResponse(_VALIDATION_LIVE_HTML)


_VALIDATION_LIVE_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>PM Validation — Live</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; margin: 16px; background:#fafafa; color:#222; }
  h1 { font-size: 15px; margin: 0 0 12px; }
  .controls { margin-bottom: 12px; display: flex; gap: 12px; align-items: center; }
  select { font-size: 14px; padding: 6px 10px; min-width: 380px; }
  .meta { font-size: 12px; color:#666; }
  table { border-collapse: collapse; background: white; }
  th, td { padding: 6px 14px; border-bottom: 1px solid #eee; font-size: 13px; font-variant-numeric: tabular-nums; }
  th { background:#f0f0f0; font-weight: 600; text-align: left; }
  td.time { color:#444; }
  td.price { text-align: right; font-weight: 700; }
  .empty { padding: 24px; color:#888; font-size: 13px; }
</style>
</head><body>
<h1>PM Validation — Live (best_bid waterfall)</h1>
<div class="controls">
  <select id="picker"><option>loading matches…</option></select>
  <span class="meta" id="meta">—</span>
</div>
<table id="t">
<thead>
  <tr>
    <th>Date / Time</th>
    <th id="hdrA">Player A best_bid</th>
    <th id="hdrB">Player B best_bid</th>
  </tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div class="empty" id="empty" style="display:none">No data for this match yet.</div>
<script>
const POLL_MS = 500;
const MAX_ROWS = 1000;

let lastSelectedSlug = null;
let lastA = null, lastB = null;

function fmtCents(c) {
  if (c === null || c === undefined) return "—";
  return c + "¢";
}
function nowStr() {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth()+1).padStart(2,'0');
  const dd = String(d.getDate()).padStart(2,'0');
  const hh = String(d.getHours()).padStart(2,'0');
  const mi = String(d.getMinutes()).padStart(2,'0');
  const ss = String(d.getSeconds()).padStart(2,'0');
  return yyyy+"-"+mm+"-"+dd+" "+hh+":"+mi+":"+ss;
}

async function refreshPicker() {
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const picker = document.getElementById("picker");
    const oldVal = picker.value;
    const slugs = Object.keys(data.matches).sort((a,b) => {
      const pa = (data.matches[a].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      const pb = (data.matches[b].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      return pa.localeCompare(pb);
    });
    const sig = slugs.map(s => {
      const m = data.matches[s];
      return s + "|" + (m.player_a_name||"") + "|" + (m.player_b_name||"");
    }).join(";");
    if (picker.dataset.signature === sig) return;
    picker.dataset.signature = sig;
    picker.innerHTML = "";
    if (slugs.length === 0) {
      const o = document.createElement("option");
      o.textContent = "no live matches"; o.value = "";
      picker.appendChild(o);
      return;
    }
    for (const s of slugs) {
      const m = data.matches[s];
      const o = document.createElement("option");
      o.value = s;
      o.textContent = (m.player_a_name||"?") + "  vs  " + (m.player_b_name||"?")
                    + (m.tournament_name ? "  ("+m.tournament_name+")" : "");
      picker.appendChild(o);
    }
    if (slugs.includes(oldVal)) {
      picker.value = oldVal;
    } else {
      picker.value = slugs[0];
      onMatchChange();
    }
  } catch (e) {
    document.getElementById("meta").textContent = "picker fetch error: " + e.message;
  }
}

function onMatchChange() {
  const slug = document.getElementById("picker").value;
  if (slug === lastSelectedSlug) return;
  lastSelectedSlug = slug;
  lastA = null; lastB = null;
  document.getElementById("tbody").innerHTML = "";
  document.getElementById("empty").style.display = "none";
}

async function pollAndAppend() {
  const slug = document.getElementById("picker").value;
  if (!slug) return;
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const m = data.matches[slug];
    if (!m) {
      document.getElementById("empty").style.display = "";
      document.getElementById("empty").textContent = "match no longer live";
      return;
    }
    document.getElementById("empty").style.display = "none";
    document.getElementById("hdrA").textContent = (m.player_a_name||"Player A") + " best_bid";
    document.getElementById("hdrB").textContent = (m.player_b_name||"Player B") + " best_bid";

    const a = m.side_a_bid_cents;
    const b = m.side_b_bid_cents;

    if (a === lastA && b === lastB) return;
    lastA = a; lastB = b;

    const tbody = document.getElementById("tbody");
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td class="time">' + nowStr() + '</td>' +
      '<td class="price">' + fmtCents(a) + '</td>' +
      '<td class="price">' + fmtCents(b) + '</td>';
    tbody.insertBefore(tr, tbody.firstChild);
    while (tbody.children.length > MAX_ROWS) tbody.removeChild(tbody.lastChild);

    document.getElementById("meta").textContent = tbody.children.length + " rows";
  } catch (e) {
    document.getElementById("meta").textContent = "fetch error: " + e.message;
  }
}

document.getElementById("picker").addEventListener("change", onMatchChange);
refreshPicker();
setInterval(refreshPicker, 5000);
setInterval(pollAndAppend, POLL_MS);
</script>
</body></html>
"""


@app.get("/dashboard-replica", response_class=HTMLResponse)
async def dashboard_replica():
    """Production-dashboard-replica view of polymarket_global_worker prices.

    One row per currently-live tennis match. Each row shows Player A,
    A best_bid, Player B, B best_bid. Prices update IN PLACE every
    500ms (no waterfall, no per-event row). This mirrors what the
    production dashboard will look like after Phase 3 cutover.

    Used for iPhone comparison: open this page, open iPhone, watch
    the in-place price for each player in each match, confirm match
    within ~1 percentage point.
    """
    return HTMLResponse(_DASHBOARD_REPLICA_HTML)


_DASHBOARD_REPLICA_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>PM Dashboard Replica — Live</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; margin: 16px; background:#fafafa; color:#222; }
  h1 { font-size: 15px; margin: 0 0 4px; }
  .sub { font-size: 12px; color:#666; margin-bottom: 12px; }
  table { border-collapse: collapse; background: white; width: 100%; max-width: 900px; }
  th, td { padding: 8px 14px; border-bottom: 1px solid #eee; font-size: 14px; }
  th { background:#f0f0f0; font-weight: 600; text-align: left; }
  td.player { font-weight: 500; }
  td.price {
    text-align: right;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    transition: background 1.2s;
  }
  td.price.flash { background: #fff5b8; transition: background 0s; }
  td.tournament { color:#666; font-size: 12px; }
  td.sum { text-align: right; color:#555; font-variant-numeric: tabular-nums; font-size: 12px; }
  td.sum.ok { color:#070; }
  td.sum.bad { color:#a00; }
  .empty { padding: 24px; color:#888; font-size: 14px; }
</style>
</head><body>
<h1>PM Dashboard Replica — Live</h1>
<div class="sub">One row per live match. Updates in place every 500ms. Yellow flash = price just changed.</div>
<table id="t">
<thead>
  <tr>
    <th>Tournament</th>
    <th>Player A</th>
    <th style="text-align:right">A bid</th>
    <th style="text-align:right">A mid</th>
    <th>Player B</th>
    <th style="text-align:right">B bid</th>
    <th style="text-align:right">B mid</th>
    <th style="text-align:right">bids ∑</th>
    <th style="text-align:right">mids ∑</th>
  </tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div class="empty" id="empty" style="display:none">No live matches.</div>
<script>
const POLL_MS = 500;
const lastABid = {}; const lastBBid = {};
const lastAMid = {}; const lastBMid = {};

function fmtCents(c) {
  if (c === null || c === undefined) return "—";
  return c + "¢";
}
function midCents(bid, ask) {
  if (bid === null || bid === undefined || ask === null || ask === undefined) return null;
  return Math.round((bid + ask) / 2);
}
function sumClass(s, target_lo, target_hi) {
  if (s === null || s === undefined) return "sum";
  if (s >= target_lo && s <= target_hi) return "sum ok";
  return "sum bad";
}

async function refresh() {
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const tbody = document.getElementById("tbody");
    const empty = document.getElementById("empty");

    const slugs = Object.keys(data.matches).sort((a,b) => {
      const pa = (data.matches[a].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      const pb = (data.matches[b].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      return pa.localeCompare(pb);
    });

    if (slugs.length === 0) {
      tbody.innerHTML = "";
      empty.style.display = "";
      return;
    }
    empty.style.display = "none";

    const seenSlugs = new Set(slugs);

    for (const slug of slugs) {
      const m = data.matches[slug];
      const aBid = m.side_a_bid_cents;
      const aAsk = m.side_a_ask_cents;
      const bBid = m.side_b_bid_cents;
      const bAsk = m.side_b_ask_cents;
      const aMid = midCents(aBid, aAsk);
      const bMid = midCents(bBid, bAsk);
      const sumBids = (aBid !== null && aBid !== undefined && bBid !== null && bBid !== undefined) ? (aBid + bBid) : null;
      const sumMids = (aMid !== null && bMid !== null) ? (aMid + bMid) : null;

      let tr = document.getElementById("row-" + slug);
      const isNew = !tr;
      if (isNew) {
        tr = document.createElement("tr");
        tr.id = "row-" + slug;
        tr.innerHTML =
          '<td class="tournament"></td>' +
          '<td class="player"></td>' +
          '<td class="price" data-side="a-bid"></td>' +
          '<td class="price" data-side="a-mid"></td>' +
          '<td class="player"></td>' +
          '<td class="price" data-side="b-bid"></td>' +
          '<td class="price" data-side="b-mid"></td>' +
          '<td class="sum"></td>' +
          '<td class="sum"></td>';
        tbody.appendChild(tr);
      }
      const cells = tr.children;
      const tournament = m.tournament_name || "";
      if (cells[0].textContent !== tournament) cells[0].textContent = tournament;
      const aName = m.player_a_name || "";
      if (cells[1].textContent !== aName) cells[1].textContent = aName;
      const aBidT = fmtCents(aBid);
      if (cells[2].textContent !== aBidT) cells[2].textContent = aBidT;
      const aMidT = fmtCents(aMid);
      if (cells[3].textContent !== aMidT) cells[3].textContent = aMidT;
      const bName = m.player_b_name || "";
      if (cells[4].textContent !== bName) cells[4].textContent = bName;
      const bBidT = fmtCents(bBid);
      if (cells[5].textContent !== bBidT) cells[5].textContent = bBidT;
      const bMidT = fmtCents(bMid);
      if (cells[6].textContent !== bMidT) cells[6].textContent = bMidT;
      // Bids sum: expected to be < 100 (spread eats some)
      const sumBidsT = (sumBids !== null) ? (sumBids + "¢") : "—";
      if (cells[7].textContent !== sumBidsT) cells[7].textContent = sumBidsT;
      cells[7].className = sumClass(sumBids, 95, 99);
      // Mids sum: expected to be ~100 ± 3 per spec
      const sumMidsT = (sumMids !== null) ? (sumMids + "¢") : "—";
      if (cells[8].textContent !== sumMidsT) cells[8].textContent = sumMidsT;
      cells[8].className = sumClass(sumMids, 97, 103);

      // Flash on change (skip first paint)
      if (!isNew && lastABid[slug] !== undefined && aBid !== lastABid[slug]) {
        cells[2].classList.remove("flash"); void cells[2].offsetWidth; cells[2].classList.add("flash");
      }
      if (!isNew && lastAMid[slug] !== undefined && aMid !== lastAMid[slug]) {
        cells[3].classList.remove("flash"); void cells[3].offsetWidth; cells[3].classList.add("flash");
      }
      if (!isNew && lastBBid[slug] !== undefined && bBid !== lastBBid[slug]) {
        cells[5].classList.remove("flash"); void cells[5].offsetWidth; cells[5].classList.add("flash");
      }
      if (!isNew && lastBMid[slug] !== undefined && bMid !== lastBMid[slug]) {
        cells[6].classList.remove("flash"); void cells[6].offsetWidth; cells[6].classList.add("flash");
      }
      lastABid[slug] = aBid; lastAMid[slug] = aMid;
      lastBBid[slug] = bBid; lastBMid[slug] = bMid;
    }

    for (const tr of Array.from(tbody.children)) {
      const slug = tr.id.replace(/^row-/, "");
      if (!seenSlugs.has(slug)) {
        tbody.removeChild(tr);
        delete lastABid[slug]; delete lastAMid[slug];
        delete lastBBid[slug]; delete lastBMid[slug];
      }
    }

    const rows = Array.from(tbody.children);
    rows.sort((x, y) => {
      const sx = x.id.replace(/^row-/, "");
      const sy = y.id.replace(/^row-/, "");
      return slugs.indexOf(sx) - slugs.indexOf(sy);
    });
    for (const tr of rows) tbody.appendChild(tr);
  } catch (e) {
    console.error("refresh error:", e);
  }
}

setInterval(refresh, POLL_MS);
refresh();
</script>
</body></html>
"""


@app.get("/api/raw-stream")
async def api_raw_stream(slug: str, since_seq: int = 0):
    """Return new per-event A/B best_bid snapshots for one slug.

    Each entry was captured atomically inside the polymarket_global_worker
    WS event handler — both books read in the same stack frame as the
    event that fired. Sums should be tight (within platform overround).

    Used by /raw-stream-live to drive a true event-driven waterfall
    rather than the projection-loop sampling that produces stale-side
    artifacts in /validation-live.
    """
    rows, latest_seq = polymarket_global_worker.slug_events_since(slug, since_seq)
    return JSONResponse({"rows": rows, "latest_seq": latest_seq})


@app.get("/raw-stream-live", response_class=HTMLResponse)
async def raw_stream_live():
    """Event-driven waterfall view, one row per WS event for selected match.

    Pick a match. Each WS event for either of its two tokens produces
    one row with: timestamp, player A best_bid, player B best_bid.
    Both prices are read from the same stack frame as the WS event,
    so sums won't show the read-skew artifacts seen in /validation-live.
    """
    return HTMLResponse(_RAW_STREAM_LIVE_HTML)


_RAW_STREAM_LIVE_HTML = """<!doctype html>
<html><head>
<meta charset="utf-8">
<title>PM Raw Stream — Live</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; margin: 16px; background:#fafafa; color:#222; }
  h1 { font-size: 15px; margin: 0 0 12px; }
  .controls { margin-bottom: 12px; display: flex; gap: 12px; align-items: center; }
  select { font-size: 14px; padding: 6px 10px; min-width: 380px; }
  .meta { font-size: 12px; color:#666; }
  table { border-collapse: collapse; background: white; }
  th, td { padding: 5px 14px; border-bottom: 1px solid #eee; font-size: 13px; font-variant-numeric: tabular-nums; }
  th { background:#f0f0f0; font-weight: 600; text-align: left; }
  td.time { color:#444; }
  td.price { text-align: right; font-weight: 700; }
  td.sum { text-align: right; color:#555; }
  td.sum.ok { color:#070; }
  td.sum.bad { color:#a00; }
  .empty { padding: 24px; color:#888; font-size: 13px; }
</style>
</head><body>
<h1>PM Raw Stream — Live (one row per WebSocket event; atomic A/B snapshot)</h1>
<div class="controls">
  <select id="picker"><option>loading matches…</option></select>
  <span class="meta" id="meta">—</span>
</div>
<table id="t">
<thead>
  <tr>
    <th>Date / Time</th>
    <th id="hdrA">Player A best_bid</th>
    <th id="hdrB">Player B best_bid</th>
    <th>A+B</th>
  </tr>
</thead>
<tbody id="tbody"></tbody>
</table>
<div class="empty" id="empty" style="display:none">No events yet for this match.</div>
<script>
const POLL_MS = 500;
const MAX_ROWS = 1000;

let lastSelectedSlug = null;
let lastSeq = 0;

function fmtCents(c) {
  if (c === null || c === undefined) return "—";
  return c + "¢";
}
function sumClass(s) {
  if (s === null || s === undefined) return "sum";
  if (s >= 99 && s <= 102) return "sum ok";
  return "sum bad";
}

async function refreshPicker() {
  try {
    const r = await fetch("/api/global-diag");
    const data = await r.json();
    const picker = document.getElementById("picker");
    const oldVal = picker.value;
    const slugs = Object.keys(data.matches).sort((a,b) => {
      const pa = (data.matches[a].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      const pb = (data.matches[b].player_a_name || "").split(" ").slice(-1)[0].toLowerCase();
      return pa.localeCompare(pb);
    });
    const sig = slugs.map(s => {
      const m = data.matches[s];
      return s + "|" + (m.player_a_name||"") + "|" + (m.player_b_name||"");
    }).join(";");
    if (picker.dataset.signature === sig) return;
    picker.dataset.signature = sig;
    picker.innerHTML = "";
    if (slugs.length === 0) {
      const o = document.createElement("option");
      o.textContent = "no live matches"; o.value = "";
      picker.appendChild(o);
      return;
    }
    for (const s of slugs) {
      const m = data.matches[s];
      const o = document.createElement("option");
      o.value = s;
      o.textContent = (m.player_a_name||"?") + "  vs  " + (m.player_b_name||"?")
                    + (m.tournament_name ? "  ("+m.tournament_name+")" : "");
      picker.appendChild(o);
    }
    if (slugs.includes(oldVal)) {
      picker.value = oldVal;
    } else {
      picker.value = slugs[0];
      onMatchChange();
    }
    // Update headers if names changed
    const slug = picker.value;
    const m = data.matches[slug];
    if (m) {
      document.getElementById("hdrA").textContent = (m.player_a_name||"Player A") + " best_bid";
      document.getElementById("hdrB").textContent = (m.player_b_name||"Player B") + " best_bid";
    }
  } catch (e) {
    document.getElementById("meta").textContent = "picker fetch error: " + e.message;
  }
}

function onMatchChange() {
  const slug = document.getElementById("picker").value;
  if (slug === lastSelectedSlug) return;
  lastSelectedSlug = slug;
  lastSeq = 0;
  document.getElementById("tbody").innerHTML = "";
  document.getElementById("empty").style.display = "";
  document.getElementById("empty").textContent = "waiting for first event…";
}

async function pollAndAppend() {
  const slug = document.getElementById("picker").value;
  if (!slug) return;
  try {
    const r = await fetch("/api/raw-stream?slug=" + encodeURIComponent(slug) + "&since_seq=" + lastSeq);
    const data = await r.json();
    if (!data.rows || data.rows.length === 0) return;

    const tbody = document.getElementById("tbody");
    document.getElementById("empty").style.display = "none";

    // Append newest events first (latest at top)
    const newRows = data.rows.slice().reverse();
    for (const ev of newRows) {
      const a = ev.side_a_bid_cents;
      const b = ev.side_b_bid_cents;
      const s = (a !== null && b !== null) ? (a + b) : null;
      const tr = document.createElement("tr");
      tr.innerHTML =
        '<td class="time">' + ev.ts_iso + '</td>' +
        '<td class="price">' + fmtCents(a) + '</td>' +
        '<td class="price">' + fmtCents(b) + '</td>' +
        '<td class="' + sumClass(s) + '">' + (s !== null ? s + "¢" : "—") + '</td>';
      tbody.insertBefore(tr, tbody.firstChild);
    }
    while (tbody.children.length > MAX_ROWS) tbody.removeChild(tbody.lastChild);

    lastSeq = data.latest_seq;
    document.getElementById("meta").textContent =
      tbody.children.length + " events  |  seq=" + lastSeq;
  } catch (e) {
    document.getElementById("meta").textContent = "fetch error: " + e.message;
  }
}

document.getElementById("picker").addEventListener("change", onMatchChange);
refreshPicker();
setInterval(refreshPicker, 5000);
setInterval(pollAndAppend, POLL_MS);
</script>
</body></html>
"""


@app.websocket("/ws/matches")
async def matches_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(state.snapshot())
            await asyncio.sleep(WS_PUSH_INTERVAL_SEC)
    except WebSocketDisconnect:
        return
    except Exception:
        log.exception("ws send failed")
        try:
            await ws.close()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Trades CSV endpoint — operator-friendly daily download
# ---------------------------------------------------------------------------

def _check_csv_token(authorization: Optional[str], query_token: Optional[str]) -> None:
    """Validate token from either Authorization header or ?token= query param.
    Raises HTTPException(401) on failure.
    """
    if not REPORTS_TOKEN:
        log.warning("trades CSV called but REPORTS_TOKEN unset")
        raise HTTPException(status_code=401)

    expected_header = f"Bearer {REPORTS_TOKEN}"
    if authorization and hmac.compare_digest(expected_header, authorization):
        return
    if query_token and hmac.compare_digest(REPORTS_TOKEN, query_token):
        return
    raise HTTPException(status_code=401)


@app.get("/reports/today.csv")
async def trades_csv_today(
    tz: Optional[str] = Query(None, description="Timezone (e.g. America/New_York). Default: env CSV_DEFAULT_TZ."),
    date: Optional[str] = Query(None, description="Specific date YYYY-MM-DD (in tz). Default: today."),
    from_date: Optional[str] = Query(None, alias="from", description="Range start YYYY-MM-DD (inclusive)"),
    to_date: Optional[str] = Query(None, alias="to", description="Range end YYYY-MM-DD (inclusive)"),
    token: Optional[str] = Query(None, description="Auth token (alternative to Authorization header)"),
    authorization: Optional[str] = Header(None),
):
    """Serve a CSV of trades for today (or a specified date/range) in the
    operator's local timezone.

    Auth: Authorization: Bearer <token> header OR ?token=<token> query.
    Token comes from REPORTS_TOKEN env var.

    Query params:
      tz=America/New_York            (default; override per request if needed)
      date=2026-04-27                (single day; YYYY-MM-DD in chosen tz)
      from=2026-04-25&to=2026-04-28  (Phase 3: inclusive multi-day range)
      (no params)                    (default: today)

    Range params (from/to) take precedence over date if both are given.
    """
    _check_csv_token(authorization, token)

    tz_str = tz or CSV_DEFAULT_TZ
    local_tz = trades_csv._resolve_local_tz(tz_str)

    key_id = os.environ.get("POLYMARKET_US_API_KEY_ID", "")
    secret_key = os.environ.get("POLYMARKET_US_API_SECRET_KEY", "")
    if not key_id or not secret_key:
        raise HTTPException(
            status_code=500,
            detail="POLYMARKET_US credentials not configured on server",
        )
    try:
        from polymarket_us import PolymarketUS  # type: ignore
    except ImportError:
        raise HTTPException(status_code=500, detail="polymarket-us SDK not installed")

    client = PolymarketUS(key_id=key_id, secret_key=secret_key)

    loop = asyncio.get_event_loop()

    # Determine fetch cutoff: range start, single date, or today.
    # Phase 3: range params take precedence over date.
    from datetime import datetime as _dt, timezone as _tz
    if from_date and to_date:
        try:
            range_start = _dt.strptime(from_date, "%Y-%m-%d").replace(tzinfo=local_tz)
            _dt.strptime(to_date, "%Y-%m-%d")  # validate format only
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from/to; use YYYY-MM-DD")
        cutoff_utc = range_start.astimezone(_tz.utc)
        result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz, cutoff_utc)
        )
    elif date:
        try:
            target = _dt.strptime(date, "%Y-%m-%d").replace(tzinfo=local_tz)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
        cutoff_utc = target.astimezone(_tz.utc)
        result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz, cutoff_utc)
        )
    else:
        result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz)
        )
    activities, diag = result

    reject_reasons: dict[str, int] = {}
    rows = []
    for a in activities:
        row = trades_csv.parse_activity(a, local_tz, reject_reasons=reject_reasons)
        if row is not None:
            rows.append(row)
    diag["rows_after_parse"] = len(rows)

    # Phase 2: assign Lifecycle (Open/Add/Reduce/Close/Settled) per-contract
    # on the FULL fetched window before date filtering. This way a contract
    # opened earlier in the fetch window has correct lifecycle on its later
    # rows. Contracts opened BEFORE the fetch cutoff will show their first
    # observed row as 'Open' even though it's actually an Add/Reduce — this
    # is the documented imperfection per the analytical workstream's spec.
    rows = trades_csv.assign_lifecycle(rows)

    # Phase 3: enrich with Held Duration, Times Touched, Pending; compute
    # X-File-Complete signal for the response header.
    completeness = trades_csv.enrich_contract_state(rows)

    # Track Backed Player parse failures separately for visibility
    bp_failures = reject_reasons.pop("backed_player_parse_failure", 0)
    if reject_reasons:
        diag["reject_reasons"] = ",".join(f"{k}={v}" for k, v in reject_reasons.items())[:200]
    else:
        diag["reject_reasons"] = ""
    diag["backed_player_parse_failures"] = bp_failures

    if from_date and to_date:
        rows = trades_csv.filter_to_range_local(rows, local_tz, from_date, to_date)
    elif date:
        rows = trades_csv.filter_to_date_local(rows, local_tz, date)
    else:
        rows = trades_csv.filter_to_today_local(rows, local_tz)
    diag["rows_after_date_filter"] = len(rows)

    # Filename reflects the window
    if from_date and to_date:
        filename = f"trades-{from_date}_to_{to_date}.csv"
    elif date:
        filename = f"trades-{date}.csv"
    else:
        today_str = _dt.now(local_tz).strftime("%Y-%m-%d")
        filename = f"trades-{today_str}.csv"

    csv_bytes = trades_csv.rows_to_csv_bytes(rows)
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Row-Count": str(len(rows)),
            "X-Pages-Fetched": str(diag.get("pages_fetched", 0)),
            "X-Records-Seen": str(diag.get("total_records_seen", 0)),
            "X-Records-In-Window": str(diag.get("records_in_window", 0)),
            "X-Rows-After-Parse": str(diag.get("rows_after_parse", 0)),
            "X-Rows-After-Date-Filter": str(diag.get("rows_after_date_filter", 0)),
            "X-Cutoff-Utc": str(diag.get("cutoff_utc_iso", "")),
            "X-Api-Error": str(diag.get("api_error", "")),
            "X-Tz": str(diag.get("tz", "")),
            "X-Reject-Reasons": str(diag.get("reject_reasons", "")),
            "X-Backed-Player-Parse-Failures": str(diag.get("backed_player_parse_failures", 0)),
            "X-File-Complete": "true" if completeness.get("file_complete", True) else "false",
            "X-Pending-Contracts": str(completeness.get("n_pending_contracts", 0)),
            "X-Schema-Version": trades_csv.SCHEMA_VERSION,
        },
    )


# ---------------------------------------------------------------------------
# /trading — performance review page (v0.1)
#
# Answers "how am I doing today?" with three headline numbers: today's cash
# P&L, wins/losses, and total trade count. Same Polymarket activity pull as
# the CSV endpoint, summarized via trades_csv.summarize_rows().
#
# Auth: same bearer token as /reports/today.csv.
# Default: today in operator's TZ. Optional ?date=YYYY-MM-DD for any day.
# ---------------------------------------------------------------------------
@app.get("/trading")
async def trading_page(
    request: Request,
    tz: Optional[str] = Query(None, description="Timezone (e.g. America/New_York). Default: env CSV_DEFAULT_TZ."),
    date: Optional[str] = Query(None, description="Specific date YYYY-MM-DD (in tz). Default: today."),
    token: Optional[str] = Query(None, description="Auth token (alternative to Authorization header)"),
    authorization: Optional[str] = Header(None),
):
    """Render the trading performance page with today's P&L summary."""
    _check_csv_token(authorization, token)

    tz_str = tz or CSV_DEFAULT_TZ
    local_tz = trades_csv._resolve_local_tz(tz_str)

    key_id = os.environ.get("POLYMARKET_US_API_KEY_ID", "")
    secret_key = os.environ.get("POLYMARKET_US_API_SECRET_KEY", "")
    if not key_id or not secret_key:
        raise HTTPException(
            status_code=500,
            detail="POLYMARKET_US credentials not configured on server",
        )
    try:
        from polymarket_us import PolymarketUS  # type: ignore
    except ImportError:
        raise HTTPException(status_code=500, detail="polymarket-us SDK not installed")

    client = PolymarketUS(key_id=key_id, secret_key=secret_key)
    loop = asyncio.get_event_loop()

    # 2026-05-01 cross-day visibility fix:
    #
    # Problem: a contract opened on day N-1 and closed on day N renders on
    # day N's trading page with no cost / no P&L / no entry-price, because
    # `filter_to_date_local(rows, ..., display_date)` cuts the buy fills
    # (which are timestamped N-1) out of the row set before
    # `summarize_rows` aggregates per-contract.
    #
    # Fix: do TWO fetches.
    #
    #   Narrow fetch (display_date only) → headline aggregates: cash_pnl,
    #     n_buys, n_sells, n_settlements, return_on_capital. These are
    #     intentionally day-of-flow numbers — yesterday's buy outflow
    #     does NOT count toward today's cash P&L.
    #
    #   Wide fetch (display_date - 2 days through display_date) → per-
    #     contract aggregation. Captures opening fills from prior days so
    #     cost/entry/exit/profitability are complete for contracts that
    #     span dates.
    #
    # Then filter wide-summary's closed_contracts to those that CLOSED on
    # display_date, and merge: headline from narrow, closed_contracts from
    # wide-filtered.
    #
    # Lookback is 2 days. Operator-confirmed scope 2026-05-01: handles the
    # vast majority of cross-day cases. Can be extended if longer holds
    # surface.
    LOOKBACK_DAYS = 2

    # Cutoff for the activity fetch — beginning of the target day in operator's TZ
    if date:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td_inner
        try:
            target = _dt.strptime(date, "%Y-%m-%d").replace(tzinfo=local_tz)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date; use YYYY-MM-DD")
        narrow_cutoff_utc = target.astimezone(_tz.utc)
        wide_cutoff_utc = (target - _td_inner(days=LOOKBACK_DAYS)).astimezone(_tz.utc)
        narrow_result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz, narrow_cutoff_utc)
        )
        wide_result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz, wide_cutoff_utc)
        )
        display_date = date
    else:
        from datetime import datetime as _dt, timezone as _tz, timedelta as _td_inner
        narrow_result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz)
        )
        # For "today" (no date param), narrow uses today_start_utc (default in
        # fetch_today_activities). Wide uses today_start - LOOKBACK_DAYS.
        now_local = _dt.now(local_tz)
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        wide_cutoff_utc = (today_start_local - _td_inner(days=LOOKBACK_DAYS)).astimezone(_tz.utc)
        wide_result = await loop.run_in_executor(
            None, lambda: trades_csv.fetch_today_activities(client, local_tz, wide_cutoff_utc)
        )
        display_date = _dt.now(local_tz).strftime("%Y-%m-%d")

    narrow_activities, narrow_diag = narrow_result
    wide_activities, wide_diag = wide_result

    # Build narrow row set (display-date only) for headline aggregates
    narrow_rows = []
    for a in narrow_activities:
        row = trades_csv.parse_activity(a, local_tz)
        if row is not None:
            narrow_rows.append(row)
    narrow_rows = trades_csv.assign_lifecycle(narrow_rows)
    trades_csv.enrich_contract_state(narrow_rows)
    narrow_rows = trades_csv.filter_to_date_local(narrow_rows, local_tz, display_date)
    narrow_summary = trades_csv.summarize_rows(narrow_rows)

    # Build wide row set (display-date - LOOKBACK_DAYS through display-date)
    # for per-contract aggregation. Lifecycle assignment runs on the full
    # window so a contract's open + close events are joined together.
    wide_rows = []
    for a in wide_activities:
        row = trades_csv.parse_activity(a, local_tz)
        if row is not None:
            wide_rows.append(row)
    wide_rows = trades_csv.assign_lifecycle(wide_rows)
    trades_csv.enrich_contract_state(wide_rows)
    # IMPORTANT: do NOT filter wide_rows by date. We want the full window
    # in summarize_rows so per-contract cost/entry/exit are complete.
    wide_summary = trades_csv.summarize_rows(wide_rows)

    # Merge: take headline from narrow_summary, take closed_contracts from
    # wide_summary filtered to those that closed on display_date.
    #
    # Filter key: close_date_short is "MM/DD/YY" in operator's local TZ
    # (computed from last_event_local in summarize_rows), so we compare
    # against display_date formatted the same way.
    from datetime import datetime as _dt2
    display_date_obj = _dt2.strptime(display_date, "%Y-%m-%d").date()
    display_date_short = display_date_obj.strftime("%m/%d/%y")

    cross_day_contracts = [
        c for c in wide_summary.get("closed_contracts", [])
        if c.get("close_date_short") == display_date_short
    ]

    # Take the merged summary: headline from narrow, closed_contracts from
    # wide-filtered. Recompute headline aggregates that depend on
    # closed_contracts list (n_closed, win_rate, total_cost_closed,
    # return_on_capital) using the cross-day-correct contracts.
    summary = dict(narrow_summary)
    summary["closed_contracts"] = cross_day_contracts
    n_closed = len(cross_day_contracts)
    n_profitable = sum(1 for c in cross_day_contracts if c["profitable"])
    n_unprofitable = sum(
        1 for c in cross_day_contracts
        if not c["profitable"] and not c["broke_even"]
    )
    summary["n_closed"] = n_closed
    summary["n_profitable"] = n_profitable
    summary["n_unprofitable"] = n_unprofitable
    summary["win_rate"] = (n_profitable / n_closed) if n_closed > 0 else None

    total_cost_closed = round(sum(c["cost"] for c in cross_day_contracts), 2)
    summary["total_cost_closed"] = total_cost_closed
    if total_cost_closed > 0:
        summary["return_on_capital"] = round(
            summary["cash_pnl"] / total_cost_closed * 100
        )
    else:
        summary["return_on_capital"] = None

    # "As of" timestamp in operator's TZ.
    # v0.8.4: format aligned to operator standard HH:MM AM/PM TZ (drops
    # seconds, drops leading zero on hour). Single source of as-of for
    # the new collapsed footer line.
    from datetime import datetime as _dt, timedelta as _td
    as_of = _dt.now(local_tz).strftime("%-I:%M %p %Z")

    # v0.8.4 (PM-D6): build the Recent Trades feed — flat list of every
    # executed transaction (fill OR settlement) for display_date in
    # local_tz, sorted newest-first. This is a flat-from-rows derivation
    # rather than a walk over closed_contracts because we want fills
    # from STILL-OPEN positions too (operator wants to see today's buys
    # that haven't been sold yet). wide_rows already has every parsed
    # row; we filter to display_date and to actual fills/settlements.
    #
    # See docs/PM-D6-Recent-Trades-2026-05-06.md for the spec, including
    # the order-type data gap (Market vs Limit not currently exposed by
    # Polymarket activity API; v1 ships with "—" for fill rows).
    recent_trades = []
    for row in wide_rows:
        utc_dt = row.get("_utc_dt")
        if utc_dt is None:
            continue
        local_dt = utc_dt.astimezone(local_tz)
        if local_dt.strftime("%Y-%m-%d") != display_date:
            continue

        lifecycle = row.get("Lifecycle", "")
        side = row.get("Buy or Sell", "")
        is_settled = lifecycle == "Settled"

        # Map row → State / Condition
        if is_settled:
            cf = row.get("Cash Flow ($)", 0) or 0
            try:
                cf_val = float(cf)
            except (TypeError, ValueError):
                cf_val = 0.0
            condition = "Won" if cf_val > 0 else "Lost"
            condition_class = "won" if cf_val > 0 else "lost"
            state = ""
            state_class = ""
        elif side == "Buy":
            state, state_class = "Bought", "bought"
            condition, condition_class = "—", ""
        elif side == "Sell":
            state, state_class = "Sold", "sold"
            condition, condition_class = "—", ""
        else:
            continue  # not a fill or settlement; skip

        # Numeric coercions
        try:
            price_dollars = float(row.get("Fill Price ($)", 0) or 0)
        except (TypeError, ValueError):
            price_dollars = 0.0
        try:
            shares_int = int(row.get("Shares", 0) or 0)
        except (TypeError, ValueError):
            shares_int = 0
        try:
            amount_dollars = float(row.get("Cash Flow ($)", 0) or 0)
        except (TypeError, ValueError):
            amount_dollars = 0.0

        recent_trades.append({
            "player": row.get("Backed Player") or "—",
            "time_short": local_dt.strftime("%-I:%M %p"),
            "time_sort": utc_dt.timestamp(),
            "state": state,
            "state_class": state_class,
            "condition": condition,
            "condition_class": condition_class,
            "rate_dollars": price_dollars,
            "rate_cents": int(round(price_dollars * 100)),
            "qty": shares_int,
            "amount_dollars": amount_dollars,
            "amount_class": "positive" if amount_dollars > 0 else ("negative" if amount_dollars < 0 else ""),
        })

    # Newest at top
    recent_trades.sort(key=lambda r: r["time_sort"], reverse=True)

    # v0.3: date selector context
    # display_date is YYYY-MM-DD already from the route logic above.
    # Compute "Today" / "Yesterday" / explicit-date label, plus full
    # weekday/long format for the header subtitle.
    today_local = _dt.now(local_tz).date()
    try:
        display_date_obj = _dt.strptime(display_date, "%Y-%m-%d").date()
    except ValueError:
        display_date_obj = today_local

    if display_date_obj == today_local:
        display_date_label = "Today"
    elif display_date_obj == today_local - _td(days=1):
        display_date_label = "Yesterday"
    else:
        display_date_label = display_date_obj.strftime("%b %d, %Y")

    display_date_full = display_date_obj.strftime("%A, %B %d, %Y")
    display_date_iso = display_date_obj.strftime("%Y-%m-%d")
    yesterday_iso = (today_local - _td(days=1)).strftime("%Y-%m-%d")

    # Build the auth query string. Two forms:
    #   token_qs       — leading "?" form for "no other params" links
    #   token_qs_amp   — leading "&" form for "append to URL with ?date=..." links
    token_qs = ""
    token_qs_amp = ""
    if token:
        token_qs = f"?token={token}"
        token_qs_amp = f"&token={token}"

    return TEMPLATES.TemplateResponse(
        "trading.html",
        {
            "request": request,
            "summary": summary,
            "display_date": display_date,
            "display_date_label": display_date_label,
            "display_date_full": display_date_full,
            "display_date_iso": display_date_iso,
            "yesterday_iso": yesterday_iso,
            "as_of": as_of,
            "recent_trades": recent_trades,
            "token_qs": token_qs,
            "token_qs_amp": token_qs_amp,
            "tz_label": tz_str,
        },
    )
