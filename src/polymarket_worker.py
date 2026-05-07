"""Polymarket Markets WebSocket worker.

Subscribes to moneyline markets on tennis events listed by Polymarket US's
gateway, captures live bid/ask/last-trade prices into an in-memory dict
keyed by market_slug.

Cross-feed mapping (Polymarket market_slug → API-Tennis event_key) lands
in Step 3.3. This module owns:
  - Gateway polling for live tennis events (`/v2/sports/tennis/events`)
  - Markets WS subscription to those events' moneyline market slugs
  - Price extraction from market_data payloads (best bid / best ask /
    last trade) into `slug_prices`
  - Event-id → (player_a_name, player_b_name, tournament_name, slug,
    asset_index) mapping in `slug_metadata` so the cross-feed step
    knows which slug is which player on which match

State_timestamps update happens here too: every successful market_data
frame stamps `state.source_timestamps["polymarket"]` so the frontend's
liveness counter cycles.

Architecture decisions (per project plan + operator session 3 brief):
  - One process, parallel asyncio task with api_tennis_worker, shared
    state.matches but distinct field ownership (api_tennis_worker owns
    score/serve/sets fields; this worker owns p1_price_cents and
    p2_price_cents, set in Step 3.3 once cross-feed maps slugs to
    event_keys).
  - Idle cleanly without API keys (mirror api_tennis_worker pattern).
  - Discovery polls every 15s by default (operator preference for
    real-time-ish discovery); Markets WS reconnects on closure.
  - Reference: github.com/peterlitton/latency-validation
    (sports_ws.py + discovery.py + analysis/normalize.py for
    empirical schema). Not vendored; reimplemented per project plan's
    asset-reuse-not-code-reuse boundary.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, Optional

import httpx

from . import state
from . import cross_feed
from . import player_metadata
from . import price_log
from . import polymarket_global_worker

log = logging.getLogger("polymarket_worker")

# ---- Config -------------------------------------------------------------

POLYMARKET_US_API_KEY_ID: str = os.environ.get("POLYMARKET_US_API_KEY_ID", "")
POLYMARKET_US_API_SECRET_KEY: str = os.environ.get(
    "POLYMARKET_US_API_SECRET_KEY", ""
)
GAMMA_BASE: str = os.environ.get(
    "GAMMA_BASE", "https://gateway.polymarket.us"
)
TENNIS_SPORT_SLUG: str = os.environ.get("TENNIS_SPORT_SLUG", "tennis")
GAMMA_POLL_INTERVAL_SECONDS: int = int(
    os.environ.get("GAMMA_POLL_INTERVAL_SECONDS", "15")
)
GAMMA_PAGE_LIMIT: int = int(os.environ.get("GAMMA_PAGE_LIMIT", "100"))
MARKETS_WS_SLUG_CAP: int = int(os.environ.get("MARKETS_WS_SLUG_CAP", "100"))
WS_RECONNECT_INITIAL_SECONDS: float = 1.0
WS_RECONNECT_MAX_SECONDS: float = 60.0
WS_RECONNECT_FACTOR: float = 2.0

# Watchdog (v0.6.11). When N consecutive WS connect attempts fail, the
# worker exits the process so Render's auto-restart picks it up. Threshold
# tunable via env var; default 5 keeps short transient outages (incident #2
# at 2026-05-03 23:45 UTC self-healed in ~32s after 4 failures) from
# triggering, while still catching the 30-min sticky-state case (incident
# #1 at 2026-05-03 17:30 UTC needed manual restart after ~225 attempts).
# Set to 0 to disable.
MARKETS_WS_RESTART_AFTER_N_FAILS: int = int(
    os.environ.get("MARKETS_WS_RESTART_AFTER_N_FAILS", "5")
)
# Step 3.9: how long after a WS price update do we suppress REST overwrite?
# Set to ~3x the discovery interval so even if WS frames arrive infrequently
# (only on actual price changes), the REST poll at 15s won't trample a 14s-old
# WS update. If WS goes silent for longer than this, REST resumes ownership.
WS_FRESHNESS_WINDOW_MS: int = int(os.environ.get("WS_FRESHNESS_WINDOW_MS", str(45_000)))
# Step 3.9: master switch for WS reactivation. Default OFF for safety —
# environments without polymarket-us SDK installed or without API keys
# fail open to REST-only behavior. Set to "1" to enable WS layering.
MARKETS_WS_ENABLED: bool = os.environ.get("MARKETS_WS_ENABLED", "0") == "1"
USER_AGENT: str = "pm-dashboard/1.0 (+https://pm-dashboard-o71w.onrender.com)"

# Step 9-A C1 (v2): cadence for /v1/portfolio/positions polling. 30s is a
# reasonable balance between fresh state (operator just placed a trade)
# and not hammering the API. P&L re-renders client-side from streaming
# prices on every tick, so per-position freshness only matters for
# detecting newly-opened or fully-closed positions.
POSITIONS_POLL_INTERVAL_SECONDS: int = int(
    os.environ.get("POSITIONS_POLL_INTERVAL_SECONDS", "30")
)


# PM-D.3/D.4 unfilled-orders feature.
# Cadence mirrors positions: 30s. Reasoning:
#   - Resting orders update at operator-action timescale (operator
#     places/modifies/cancels via Polymarket UI), not market-data
#     timescale. Faster cadence isn't earned by data-change frequency.
#   - 30s aligns with positions polling — simplifies operational model.
#   - Filled or cancelled orders fall off the SDK response naturally,
#     so 30s is the worst-case latency between Polymarket-side state
#     change and dashboard reflection.
ORDERS_POLL_INTERVAL_SECONDS: int = int(
    os.environ.get("ORDERS_POLL_INTERVAL_SECONDS", "30")
)


# 2026-05-02 — polymarket_us SDK 0.1.2 WS workaround.
#
# The SDK's BaseWebSocket.connect() in polymarket_us/websocket/base.py
# does:
#
#     await websockets.connect(url, additional_headers=headers)
#
# In `websockets` 13.1+ the top-level `websockets.connect` resolves to
# `legacy.client.Connect`, which accepts `extra_headers` (NOT
# `additional_headers`). The SDK was written against the modern
# `websockets.asyncio.client.connect` API where `additional_headers` is
# correct, but mistakenly calls the top-level dispatcher.
#
# Result at runtime: any markets WS connect attempt raises
# `TypeError: create_connection() got an unexpected keyword argument
# 'additional_headers'` and the worker's reconnect loop spins
# indefinitely on backoff.
#
# Repro confirmed: AsyncPolymarketUS().ws.markets().connect() — fails
# on websockets versions 13.1 → 16.0, with or without uvloop.
#
# Workaround: rebind `websockets.connect` to the modern asyncio client's
# connect, which DOES accept `additional_headers` and is the API the SDK
# clearly intended to use. Applied at module load so the SDK picks up
# the patched binding the first time it dereferences `websockets.connect`
# inside its WS connect path.
#
# Future-proofing: this patch is idempotent and a no-op if the SDK ever
# fixes its import (e.g., switches to `from websockets.asyncio.client
# import connect`). At that point this block can be deleted entirely.
#
# Tracking: SDK fix request to be filed; durable replacement is to
# write our own ~50-80 line WS client using
# `websockets.asyncio.client.connect` directly and bypass the SDK's WS
# wrapper. This monkey-patch is the interim quick-win.
def _apply_polymarket_us_ws_workaround() -> None:
    try:
        import websockets
        from websockets.asyncio.client import connect as asyncio_connect
    except ImportError:
        return
    # Only patch if the bug is actually present (top-level connect has
    # `extra_headers` instead of `additional_headers`).
    import inspect
    try:
        params = inspect.signature(websockets.connect).parameters
    except (ValueError, TypeError):
        return
    if "additional_headers" in params:
        return  # already correct, nothing to do
    if "extra_headers" not in params:
        return  # unfamiliar shape, don't patch — let the original error surface
    websockets.connect = asyncio_connect
    log.info(
        "polymarket_us SDK 0.1.2 WS workaround applied: "
        "rebound websockets.connect → websockets.asyncio.client.connect"
    )


_apply_polymarket_us_ws_workaround()


# Constant Polymarket tags moneyline (head-to-head winner) markets with.
# Confirmed empirically against gateway.polymarket.us/v2/sports/tennis/events
# on 2026-04-26: field is `marketType` (also redundantly `sportsMarketType`),
# value is `"moneyline"` (lowercase string). The latency-validation reference's
# `sportsMarketTypeV2: "SPORTS_MARKET_TYPE_MONEYLINE"` is stale — the API
# evolved between when that worker was written and now.
MONEYLINE_MARKET_TYPE = "moneyline"


# ---- Shared in-memory state owned by this worker -----------------------

# market_slug → latest captured prices (cents, integers 0-99)
# Each entry: {"bid_cents": int|None, "ask_cents": int|None,
#              "last_cents": int|None, "updated_ms": int}
slug_prices: dict[str, dict[str, Any]] = {}

# market_slug → metadata used by Step 3.3's cross-feed mapping
# Each entry: {
#   "polymarket_event_id": str,
#   "tournament_name": str,
#   "event_date": str,            # YYYY-MM-DD
#   "player_a_name": str,         # the participant whose side this slug bets on
#   "player_b_name": str,
#   "asset_index": int,           # 0 or 1 — which outcome of the moneyline
# }
slug_metadata: dict[str, dict[str, Any]] = {}

# Active set of slugs we want subscribed to. Updated on each discovery
# poll. Used by the WS supervisor to know what to subscribe to on
# (re)connect.
_active_slugs: set[str] = set()

# warn-once tracking, similar to api_tennis_worker
_warned: set[str] = set()
_raw_md_logged = False
_raw_trade_logged = False

# v0.6.12 PRICEDIAG: per-slug one-shot raw-payload loggers.
# When a price discrepancy on a specific market is suspected, the
# process-wide one-shot loggers above don't help — they fired on whatever
# the first frame after process start happened to be. These per-slug
# variants fire ONCE per (slug, payload-type) pair after process start,
# capturing the actual schema for any specific market on its next frame.
#
# Why both: market_data carries book-state (bids/offers/marketSides),
# trade carries execution-level. Extraction bugs can hide in either path,
# and the bug class we're chasing (Bai 70¢ + Lu 4¢ ≠ 100¢) could be
# wrong-field-from-market_data OR wrong-field-from-trade-event.
#
# Memory: bounded by active-slug count (typically <200), bool per slug.
# Render's process is single-instance; no concurrency concerns at this scale.
#
# Cleanup: these dicts grow only as new slugs appear. On WS reconnect, the
# global state is preserved; we don't re-log after a reconnect because the
# schema doesn't change between reconnects. Process restart resets.
_per_slug_md_logged: dict[str, bool] = {}
_per_slug_trade_logged: dict[str, bool] = {}

# v0.7.2 PRICEDIAG diagnostic dicts. One-shot-per-slug logs to keep
# log volume bounded. These exist to capture the path that's writing
# None into slug_prices for the K. Singh / Cordova-style flap.
_per_slug_rest_none_logged: dict[str, bool] = {}
_per_slug_path_b_side_a_skip_logged: dict[str, bool] = {}
_per_slug_path_b_side_b_skip_logged: dict[str, bool] = {}
_per_slug_merge_suppress_logged: dict[str, bool] = {}

# v0.6.13 PRICEDIAG: per-slug one-shot REST events-payload logger.
# Captures the raw event JSON the first time `_extract_moneyline_with_prices`
# sees each slug after process start. Mirrors the v0.6.12 WS loggers above.
#
# Why: v0.6.12 captured WS payloads only. WS payloads contain only the YES
# side's order book (no `marketSides` block in any of the 60+ payloads
# captured tonight). We do not yet have a captured REST events payload for
# matches showing the wrong-price bug (Bai/Lu sum=74¢, Wong/Yao=82¢,
# Lajovic/Choinski=95¢). Without REST captures we cannot identify whether
# the bug originates in REST extraction, the resolver merge path, or the
# REST endpoint itself.
#
# Memory bound: active-slug count, typically <200 entries. Bool per slug.
# Logs once per slug per process lifetime, suppressed forever after.
_per_slug_rest_logged: dict[str, bool] = {}


# v0.7.7 EXTRACTION DIAGNOSTIC (2026-05-05) — temporary instrument.
#
# Captures every WS market_data frame's candidate side-A and side-B prices
# from each available source, alongside what slug_prices currently holds
# (the value the dashboard renders). Goal: empirically determine which
# WS field, if used as the source for side B, would deliver sub-second
# updates without being silently rejected by the sum-band guard.
#
# Storage: per-slug ring buffer, 5000 frames per slug. At realistic ~3 fps
# on active markets this covers ~28 minutes — comfortable margin for the
# 15-minute capture the operator runs during diagnostic. Total memory
# bound: 5000 × 100 slugs × ~250 bytes per row ≈ 125 MB worst case;
# realistic usage is much lower since most slugs are not max-active.
#
# Lifecycle: starts capturing on process restart (v0.7.7 deploy). Stays
# on until a follow-up ship removes the route. No on/off switch — bounded
# memory means it can run continuously without operational concern.
#
# Endpoint: GET /api/extraction-diag exposes the buffers as JSON.
#
# Removal target: v0.7.8 or later, after the data analysis informs the
# real fix. See docs/investigations/asymmetric-stuck-side-bug-2026-05-05.md
# follow-up section for context.
from collections import deque

EXTRACTION_DIAG_BUFFER_SIZE = 5000
_extraction_diag_buffers: dict[str, "deque[dict[str, Any]]"] = {}


def _warn_once(key: str, payload: Any) -> None:
    if key in _warned:
        return
    _warned.add(key)
    log.warning(
        "Polymarket schema: %s; payload sample keys=%s",
        key,
        list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__,
    )


# ---- Price extraction (from latency-validation/analysis/normalize.py) ---


def _coerce_price_float(v: Any) -> Optional[float]:
    """Polymarket stringifies prices as '0.310' etc. Returns float in
    [0.0, 1.0] or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _extract_px(px_obj: Any) -> Optional[float]:
    """Pull numeric price out of {"value": "0.310", "currency": "USD"}."""
    if not isinstance(px_obj, dict):
        return None
    return _coerce_price_float(px_obj.get("value"))


def _to_cents(price: Optional[float]) -> Optional[int]:
    """Convert 0.0–1.0 float to 0–99 cent integer for display.

    Polymarket prices are probabilities in [0,1]. Display layer wants
    cents. Round-half-to-even via int(round(...)) so 0.315 → 32 not 31.
    Clamp to [0, 99] for safety; 100 would be displayed as 99 to keep
    column width predictable.
    """
    if price is None:
        return None
    cents = int(round(price * 100))
    if cents < 0:
        return 0
    if cents > 99:
        return 99
    return cents


def _extract_prices_from_market_data(
    market_data: dict[str, Any],
) -> dict[str, Optional[int]]:
    """Pull per-side prices from a WS marketData payload.

    SCHEMA NOTE (Step 3.9, partly speculative until first WS frame logged):
    The REST gateway moneyline schema is `marketSides[].quote.value` per side.
    We don't have an empirical WS market_data sample for moneylines yet —
    the latency-validation reference captured raw archives but didn't extract
    side identities, and the original Step 3.2 code path was never run against
    real WS frames after the architectural pivot.

    Speculative extraction strategy:
      1. Look for marketSides[].quote.value (matches REST schema; if WS
         mirrors REST, this works directly)
      2. Fall back to bid_cents/ask_cents/last_cents from bids/offers/stats
         (the original pre-Step-3.2 schema). These won't populate
         side_a_cents/side_b_cents, so the resolver won't see updated prices,
         but the entry is still written for diagnostic logging.

    The one-shot raw payload log (`_raw_md_logged` gate above) will reveal
    the actual WS schema on the first deployed frame. Operator review the
    log line and we patch this extractor in a follow-up if needed.

    Returns a partial dict with whichever fields we could extract. Caller
    is responsible for merging into existing slug_prices entry (preserves
    REST-written fields not present in WS payload).
    """
    out: dict[str, Optional[int]] = {}

    # --- Path A: marketSides per-side prices (matches REST schema) ---
    sides = market_data.get("marketSides")
    if isinstance(sides, list) and len(sides) == 2:
        def _quote_cents(side: Any) -> Optional[int]:
            if not isinstance(side, dict):
                return None
            q = side.get("quote")
            if not isinstance(q, dict):
                return None
            return _to_cents(_coerce_price_float(q.get("value")))

        side_a_cents = _quote_cents(sides[0])
        side_b_cents = _quote_cents(sides[1])
        if side_a_cents is not None or side_b_cents is not None:
            out["side_a_cents"] = side_a_cents
            out["side_b_cents"] = side_b_cents
            # Maintain legacy `last_cents` shape: side_a's price (matches
            # what the REST discovery loop writes today)
            out["last_cents"] = side_a_cents

    # --- Path B: bids/offers/stats (legacy CLOB-style schema) ---
    bids = market_data.get("bids") or []
    offers = market_data.get("offers") or []
    stats = market_data.get("stats") or {}

    best_bid = _extract_px(bids[0].get("px")) if bids and isinstance(bids[0], dict) else None
    best_ask = _extract_px(offers[0].get("px")) if offers and isinstance(offers[0], dict) else None
    last_trade = _extract_px(stats.get("lastTradePx")) if isinstance(stats, dict) else None

    if best_bid is not None:
        out["bid_cents"] = _to_cents(best_bid)
    if best_ask is not None:
        out["ask_cents"] = _to_cents(best_ask)
    # Only set last_cents from CLOB schema if Path A didn't set it.
    if "last_cents" not in out and last_trade is not None:
        out["last_cents"] = _to_cents(last_trade)

    # --- Path B side_a_cents (2026-05-03, data-driven) -----------------
    # 50-row diagnostic analysis (v0.6.6 [WS-DIAG] capture during live
    # ATP Challenger play) found: WS `ask` matches REST `side_a_cents`
    # with median 0 / mean 0.02 cent delta. Best of 4 candidates
    # evaluated (ask, mid, bid, lastTrade). lastTrade was second
    # (mean 1.81) but goes stale; ask is current-state.
    #
    # Tight-spread guard: spread > 5¢ correlated 100% with stale-market
    # REST corruption in the diagnostic (side_a+side_b=137-140¢ instead
    # of ~101¢ overround). Skip the WS write in those cases — REST's
    # 15s cadence still owns side_a in stale markets.
    #
    # v0.6.15: side_b_cents now also has a WS writer (below) via
    # `lastPriceSample.shortPx`. side_b is no longer REST-only.
    if (
        "side_a_cents" not in out  # Path A didn't already set it
        and best_ask is not None
        and best_bid is not None
    ):
        spread_cents = round((best_ask - best_bid) * 100)
        if 0 <= spread_cents <= 5:
            out["side_a_cents"] = _to_cents(best_ask)
            # Maintain legacy last_cents shape: side_a's price
            if "last_cents" not in out:
                out["last_cents"] = _to_cents(best_ask)
        else:
            # v0.7.2 PRICEDIAG: log when the spread guard rejects a
            # side_a write. If this fires for K. Singh's slug, then
            # we have empirical confirmation of part of the flap
            # hypothesis: WS can't refresh side_a, so the original
            # REST None (or stale value) persists — and the merge
            # gate's WS-fresh state suppresses REST refresh.
            slug_for_log = market_data.get("marketSlug", "?")
            if not _per_slug_path_b_side_a_skip_logged.get(slug_for_log):
                log.info(
                    "[PRICEDIAG-PATHB-SIDE-A-SKIP] spread guard reject: "
                    "slug=%s spread_cents=%d best_bid=%r best_ask=%r",
                    slug_for_log, spread_cents, best_bid, best_ask,
                )
                _per_slug_path_b_side_a_skip_logged[slug_for_log] = True

    # --- Path B side_b_cents (v0.7.8, 2026-05-05) ---------------------
    # Source: 1 - best_ask (the complement of the live order book's ask).
    #
    # Why this changed from v0.6.15 (lastPriceSample.shortPx):
    # `lastPriceSample` is a paired snapshot Polymarket only refreshes
    # ~once per minute (the `.ts` field on captured payloads is up to
    # 67 seconds older than `transactTime`). Reading shortPx therefore
    # delivers the right value but at minute-cadence — even though WS
    # frames arrive sub-second, the value doesn't change between
    # snapshots. Side B looked frozen while side A updated live.
    # Empirical confirmation: production WS payload dump 2026-05-05 16:34
    # (working_log_entry_2026-05-05-v0.7.8-realtime-side-b.md, evidence
    # log entry).
    #
    # 1 - best_ask updates per-frame. It's the live-book-derived
    # complement of side A's source. Both sides now refresh together
    # off the same WS frame's order book, sum guaranteed = 100¢ by
    # construction (modulo the cents rounding).
    #
    # Spread guard: same as side_a (≤ 5¢). When the order book is
    # wide-spread (stale market), neither side gets a WS write and
    # REST's 15s cadence refreshes both. This matches the side_a
    # behavior — symmetrical guards, symmetrical fallback.
    #
    # Removes the sum-band guard. The sum-band guard existed to catch
    # `lastPriceSample` corruption (one side at the settlement default
    # 0.50, the other at a real value). 1 - best_ask cannot have that
    # corruption — there's only one source.
    if (
        "side_b_cents" not in out  # Path A didn't already set it
        and best_ask is not None
        and best_bid is not None
    ):
        spread_cents = round((best_ask - best_bid) * 100)
        if 0 <= spread_cents <= 5:
            out["side_b_cents"] = _to_cents(1.0 - best_ask)

    return out


# ---- Gateway discovery --------------------------------------------------


async def _gamma_get_events(
    client: httpx.AsyncClient,
) -> list[dict[str, Any]]:
    """Page through /v2/sports/{slug}/events and return all events."""
    all_events: list[dict[str, Any]] = []
    offset = 0
    while True:
        try:
            resp = await client.get(
                f"/v2/sports/{TENNIS_SPORT_SLUG}/events",
                params={"limit": GAMMA_PAGE_LIMIT, "offset": offset},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("Gamma poll failed at offset=%d: %s", offset, exc)
            break
        data = resp.json()
        page = data.get("events") if isinstance(data, dict) else None
        page = page or []
        all_events.extend(page)
        if len(page) < GAMMA_PAGE_LIMIT:
            break
        offset += GAMMA_PAGE_LIMIT
    return all_events


def _extract_moneyline_with_prices(
    event: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """For one Gamma event, pull out everything we need for cross-feed
    + price display in one pass.

    Returns a single dict per event (one moneyline market per event in
    the empirical schema), or None if extraction fails.

    EMPIRICAL SCHEMA (Step 3.2-fix, validated against
    gateway.polymarket.us/v2/sports/tennis/events on 2026-04-26):

        event:
          id: "10013"                            (str)
          title: "Dalibor Svrcina vs. Andrea Guerrieri 2026-04-26"
          startDate: "2026-04-26T13:05:00Z"
          seriesSlug: "atp-2026" | "wta-2026" | …  (proxy for league)
          live: True/False
          markets: [...]                          (one moneyline)
            market:
              slug: "aec-atp-dalsvr-andgue-2026-04-26"
              marketType: "moneyline"             (NOT sportsMarketTypeV2)
              sportsMarketType: "moneyline"
              active: True, closed: False
              marketSides: [side, side]
                side:
                  description: "Dalibor Svrcina"   (player name)
                  long: True/False                 (which side is favored to win?)
                  team:
                    name: "Dalibor Svrcina"
                    league: "atp" | "wta" | …
                  price: "0.610"                  (per-side ASK; not what we display)
                  quote: {value: "0.610", currency: "USD"}  (the displayed last price)

    Notes for cross-feed:
      - No tournament/event-name field. seriesSlug is too coarse
        ("atp-2026"). Cross-feed must rely on date + last-name only.
      - Player names come from marketSides[].description (or .team.name —
        identical in samples). Build player_a / player_b from the two
        sides. If `long==True`, that side is the "yes" side of the
        market in Polymarket terms; we store a-side / b-side in
        marketSides[] order (which is consistent across polls).

    Skips events without an active moneyline market or without exactly
    two market sides.
    """
    event_id = str(event.get("id") or "")
    if not event_id:
        return None

    start_iso = event.get("startDate") or ""
    event_date = start_iso[:10] if isinstance(start_iso, str) else ""

    series_slug = event.get("seriesSlug") or ""  # "atp-2026" / "wta-2026"
    league = ""
    if isinstance(series_slug, str) and "-" in series_slug:
        league = series_slug.split("-", 1)[0]  # "atp" / "wta"

    markets = event.get("markets") or []
    for m in markets:
        if not isinstance(m, dict):
            continue
        # Accept either marketType or sportsMarketType — both observed
        # to carry "moneyline" on every sample we've seen, but defensive
        # against future schema reshuffles.
        mt = m.get("marketType") or m.get("sportsMarketType")
        if mt != MONEYLINE_MARKET_TYPE:
            continue
        if not m.get("active") or m.get("closed"):
            continue
        slug = m.get("slug")
        if not isinstance(slug, str) or not slug:
            continue

        # v0.6.13 PRICEDIAG: per-slug one-shot raw REST event log.
        # Captures the full event JSON exactly once for each slug seen,
        # so when a market shows wrong rendered prices (sum < 95¢ or
        # similar impossible state) we have the actual REST payload to
        # cross-reference against the v0.6.12 WS payload. Logs the full
        # event (not just the market) to capture seriesSlug, startDate,
        # and any per-event metadata that may explain stale price reads.
        if not _per_slug_rest_logged.get(slug):
            log.info(
                "[PRICEDIAG-REST] event slug=%s (one-shot) event=%s",
                slug,
                event,
            )
            _per_slug_rest_logged[slug] = True

        sides = m.get("marketSides") or []
        if len(sides) != 2:
            continue
        side_a, side_b = sides[0], sides[1]
        if not isinstance(side_a, dict) or not isinstance(side_b, dict):
            continue

        # Player names: prefer description (matches the displayed name
        # in Polymarket UI), fall back to team.name (identical in samples).
        def _player_from_side(side: dict[str, Any]) -> str:
            desc = side.get("description")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
            team = side.get("team") or {}
            tn = team.get("name")
            if isinstance(tn, str) and tn.strip():
                return tn.strip()
            return ""

        player_a = _player_from_side(side_a)
        player_b = _player_from_side(side_b)
        if not player_a or not player_b:
            continue

        # Prices from `quote.value`. Interpret each side's quote as
        # that side's price (sums to ~100¢). The bare `price` field is
        # observed to differ from `quote.value` (e.g. one is ask, the
        # other is mid/last) — quote.value matches Polymarket's UI.
        #
        # v0.7.2 PRICEDIAG-NONE: per-slug one-shot log when this returns
        # None. Hypothesis under test: K. Singh / Cordova-style flaps
        # are caused by initial REST extraction returning None for one
        # side (malformed quote.value), which then locks in via the
        # WS-fresh merge gate. If that's the cause, this log will show
        # the malformed quote payload for the affected slugs.
        def _quote_cents(side: dict[str, Any]) -> Optional[int]:
            q = side.get("quote")
            if not isinstance(q, dict):
                return None
            val = _coerce_price_float(q.get("value"))
            return _to_cents(val)

        cents_a = _quote_cents(side_a)
        cents_b = _quote_cents(side_b)

        # PRICEDIAG-NONE: one-shot per slug when REST extraction returns
        # None for either side. This is the smoking gun for the flap
        # hypothesis — the None must enter slug_prices somewhere; if
        # this fires for K. Singh's slug, REST is the source.
        if (cents_a is None or cents_b is None) and not _per_slug_rest_none_logged.get(slug):
            log.info(
                "[PRICEDIAG-NONE] REST extraction returned None: "
                "slug=%s cents_a=%r cents_b=%r side_a_quote=%r side_b_quote=%r",
                slug, cents_a, cents_b,
                side_a.get("quote"), side_b.get("quote"),
            )
            _per_slug_rest_none_logged[slug] = True

        return {
            "polymarket_event_id": event_id,
            "market_slug": slug,
            "event_date": event_date,
            "league": league,
            "player_a_name": player_a,
            "player_b_name": player_b,
            "side_a_cents": cents_a,
            "side_b_cents": cents_b,
        }

    return None


async def _discovery_loop() -> None:
    """Poll Gamma every GAMMA_POLL_INTERVAL_SECONDS.

    REST-DIRECT MODE (Step 3.2-fix architectural pivot):
    Empirical finding from live test 2026-04-26: the gateway response
    contains per-side prices directly (`marketSides[].quote.value`),
    so we get prices from the same poll that does discovery. We do
    NOT need a separate WebSocket connection for prices — the
    latency-validation reference does that for sub-second tick capture
    used by its analysis layer, but PM-Dashboard's display purpose is
    served fine by 15s REST cadence. WS code is retained but not run;
    available for future per-side-tick refinement if needed.

    Each iteration:
      1. Pull all tennis events from gateway.
      2. For each event, extract moneyline + prices into a single
         flat record.
      3. Update slug_metadata (used by resolver) and slug_prices
         (also used by resolver) atomically.
      4. Update state.source_timestamps.polymarket so the liveness
         counter cycles.
    """
    log.info(
        "Polymarket discovery starting: slug=%r interval=%ds (REST-direct mode)",
        TENNIS_SPORT_SLUG,
        GAMMA_POLL_INTERVAL_SECONDS,
    )
    async with httpx.AsyncClient(
        base_url=GAMMA_BASE,
        timeout=httpx.Timeout(20.0, connect=10.0),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    ) as client:
        while True:
            try:
                events = await _gamma_get_events(client)
            except Exception as exc:
                log.warning("Discovery loop iteration failed: %s", exc)
                events = []

            new_metadata: dict[str, dict[str, Any]] = {}
            new_prices: dict[str, dict[str, Any]] = {}
            for ev in events:
                rec = _extract_moneyline_with_prices(ev)
                if rec is None:
                    continue
                slug = rec["market_slug"]
                new_metadata[slug] = {
                    "polymarket_event_id": rec["polymarket_event_id"],
                    "tournament_name": "",  # Polymarket gateway doesn't expose this
                    "league": rec["league"],
                    "event_date": rec["event_date"],
                    "player_a_name": rec["player_a_name"],
                    "player_b_name": rec["player_b_name"],
                    "asset_index": 0,  # legacy field; unused in REST-direct mode
                }
                new_prices[slug] = {
                    # Per-side prices live directly here now, not derived
                    # from bid/ask. The `bid_cents`/`ask_cents` keys are
                    # kept None for shape-compatibility with anything
                    # that reads slug_prices, but the resolver reads
                    # `side_a_cents` / `side_b_cents` directly.
                    "bid_cents": None,
                    "ask_cents": None,
                    "last_cents": rec["side_a_cents"],  # legacy compat: side A only
                    "side_a_cents": rec["side_a_cents"],
                    "side_b_cents": rec["side_b_cents"],
                    "updated_ms": int(time.time() * 1000),
                }

            new_slugs = set(new_metadata.keys())
            added = new_slugs - _active_slugs
            removed = _active_slugs - new_slugs

            _active_slugs.clear()
            _active_slugs.update(new_slugs)
            slug_metadata.clear()
            slug_metadata.update(new_metadata)

            # Step 3.9: WS-aware price merge.
            # Discovery loop owns: slug existence, metadata, INITIAL prices for
            #   newly-appearing slugs, and FALLBACK prices when WS hasn't
            #   updated a slug in a while (covers cases where WS is down,
            #   misconfigured, or simply hasn't received a frame yet).
            # WS market_data handler owns: ongoing updates to side_a_cents
            #   AND side_b_cents for already-known slugs. As of v0.6.15,
            #   Path B writes both sides — side_a from best_ask and
            #   side_b from lastPriceSample.shortPx with sum-band sanity.
            #
            # Arc of changes recorded for the next reader:
            #   v0.6.7  — WS Path B started writing side_a only. side_b
            #             was assumed to be REST-refreshed at 15s.
            #   v0.6.14 — Discovered the merge gate's WS-fresh branch
            #             never let REST refresh side_b once WS was active.
            #             Fixed by refreshing side_b from REST every cycle
            #             in the WS-fresh branch. Operationally correct
            #             but kept side_b on a 15s cadence.
            #   v0.6.15 — WS Path B now writes side_b from
            #             lastPriceSample.shortPx. Merge gate returns to
            #             its pre-v0.6.7 shape: WS-fresh branch preserves
            #             BOTH side prices. REST is fallback when WS is
            #             silent. Both sides update sub-second.
            #
            # Root cause + fix arc documented in:
            # docs/investigations/price-extraction-bug.md.
            #
            # Field ownership is enforced by: only overwriting REST-derived
            # prices when the existing entry has no recent WS timestamp.
            # WS_FRESHNESS_WINDOW_MS controls how long a WS update
            # suppresses the next REST overwrite — if set too tight, REST
            # will trample WS between updates; if set too loose, a stale
            # WS price persists past the slug becoming inactive.
            # 2026-05-05 (v0.7.6): per-side WS freshness gate.
            # Each side has its own WS clock (ws_a_updated_ms /
            # ws_b_updated_ms). REST refresh is allowed independently
            # for each side: if WS hasn't refreshed side A within the
            # window, REST overwrites side A even if WS is currently
            # writing side B (and vice versa). Pre-v0.7.6 used a single
            # ws_updated_ms clock that suppressed both sides whenever
            # WS wrote either one; this produced the asymmetric-stuck-
            # side bug observed 2026-05-05 (Dellien/De Jong, where
            # Path B's sum-band guard rejected side_b on every WS frame
            # but Path A or Path B side_a kept stamping freshness,
            # locking side_b at a stale value while side_a updated).
            # See docs/investigations/asymmetric-stuck-side-bug-2026-05-05.md.
            #
            # Backward-compat: ws_updated_ms is still maintained as
            # max(ws_a_updated_ms, ws_b_updated_ms) by the WS handler.
            # The merge-gate logs (PRICEDIAG-MERGE-SUPPRESS) now report
            # both clocks so a stuck side is identifiable in logs.
            now_ms_int = int(time.time() * 1000)
            ws_freshness_cutoff_ms = now_ms_int - WS_FRESHNESS_WINDOW_MS
            merged_prices: dict[str, dict[str, Any]] = {}
            for slug, rest_prices in new_prices.items():
                existing = slug_prices.get(slug)
                if existing is None:
                    # First sighting — REST writes the initial price baseline
                    merged_prices[slug] = rest_prices
                    continue

                # Per-side WS freshness. Read both clocks; fall back to
                # the legacy ws_updated_ms for the brief migration window
                # where existing entries may not have per-side clocks
                # (this becomes dead code once the worker has run for
                # WS_FRESHNESS_WINDOW_MS after v0.7.6 deploy).
                legacy_ws_ms = existing.get("ws_updated_ms") or 0
                ws_a_ms = existing.get("ws_a_updated_ms") or legacy_ws_ms
                ws_b_ms = existing.get("ws_b_updated_ms") or legacy_ws_ms
                a_fresh = ws_a_ms >= ws_freshness_cutoff_ms
                b_fresh = ws_b_ms >= ws_freshness_cutoff_ms

                merged = dict(existing)
                # bid/ask are always REST-owned bookkeeping
                merged["bid_cents"] = rest_prices["bid_cents"]
                merged["ask_cents"] = rest_prices["ask_cents"]
                # Side A: if WS-fresh, keep existing; else accept REST
                if not a_fresh:
                    merged["side_a_cents"] = rest_prices.get("side_a_cents")
                # Side B: if WS-fresh, keep existing; else accept REST
                if not b_fresh:
                    merged["side_b_cents"] = rest_prices.get("side_b_cents")
                # last_cents tracks side_a (legacy contract): if side A
                # was just refreshed from REST, refresh last_cents too.
                if not a_fresh:
                    merged["last_cents"] = rest_prices.get("last_cents")
                # Don't update updated_ms from REST — let it reflect
                # the most recent ANY-source touch (the WS handler
                # already maintains it; if WS is silent for a long
                # time, this slug's entry decays naturally on next
                # REST cycle).
                merged_prices[slug] = merged

                # v0.7.2 PRICEDIAG (refined v0.7.6): log when WS-fresh
                # state is suppressing a REST refresh AND the existing
                # entry has None on the side that's being suppressed.
                # Per-side ages now logged so a stuck side is visible.
                a_suppressed_with_none = (
                    a_fresh and existing.get("side_a_cents") is None
                )
                b_suppressed_with_none = (
                    b_fresh and existing.get("side_b_cents") is None
                )
                if (
                    (a_suppressed_with_none or b_suppressed_with_none)
                    and not _per_slug_merge_suppress_logged.get(slug)
                ):
                    log.info(
                        "[PRICEDIAG-MERGE-SUPPRESS] WS-fresh suppress "
                        "with None side: slug=%s "
                        "existing_side_a=%r existing_side_b=%r "
                        "rest_side_a=%r rest_side_b=%r "
                        "ws_a_age_ms=%d ws_b_age_ms=%d",
                        slug,
                        existing.get("side_a_cents"),
                        existing.get("side_b_cents"),
                        rest_prices.get("side_a_cents"),
                        rest_prices.get("side_b_cents"),
                        now_ms_int - ws_a_ms,
                        now_ms_int - ws_b_ms,
                    )
                    _per_slug_merge_suppress_logged[slug] = True

            # Drop entries for slugs that have left the active set
            slug_prices.clear()
            slug_prices.update(merged_prices)

            if events:
                state.source_timestamps["polymarket"] = int(time.time() * 1000)

            if added or removed or len(new_slugs) > 0:
                log.info(
                    "Discovery delta: active=%d added=%d removed=%d events=%d",
                    len(_active_slugs),
                    len(added),
                    len(removed),
                    len(events),
                )

            await asyncio.sleep(GAMMA_POLL_INTERVAL_SECONDS)


# ---- Markets WS supervisor (SDK-backed) ------------------------------------

# Step 3.9: WS reactivated. The 15s REST lag was creating active friction with
# the dashboard's primary purpose — every glance required reconciling dashboard
# price against PM app price, which contaminated trust in the dashboard as a
# primary surface (a failure mode the original WS-vs-REST decision criteria
# didn't anticipate). See working log entry 2026-04-26 PM "Step 3.9 — WS
# reactivation" for the full reassessment.
#
# Architecture: WS layers ON TOP OF REST, doesn't replace it.
#   - Discovery loop (REST, 15s) owns slug existence, metadata, and INITIAL
#     prices for newly-appearing slugs.
#   - WS handlers own ongoing per-side price updates for already-known slugs.
#   - Field ownership enforced via ws_updated_ms timestamp: discovery loop
#     only overwrites side_a_cents/side_b_cents when WS hasn't touched the
#     slug within WS_FRESHNESS_WINDOW_MS (default 45s).
#
# Master switch: MARKETS_WS_ENABLED env var. Default off for safety; set to
# "1" to activate. When off, behavior is identical to pre-Step-3.9 REST-only.


def _extract_slug(payload: dict[str, Any]) -> Optional[str]:
    """Pull market_slug out of a market_data / market_data_lite / trade
    payload. Empirical schema from latency-validation/sports_ws.py."""
    for container in ("marketData", "marketDataLite", "trade"):
        inner = payload.get(container)
        if isinstance(inner, dict):
            slug = inner.get("marketSlug") or inner.get("market_slug")
            if isinstance(slug, str) and slug:
                return slug
    return None


def _capture_extraction_diag(
    slug: str,
    market_data: dict[str, Any],
    existing_slug_prices: Optional[dict[str, Any]],
) -> None:
    """v0.7.7 EXTRACTION DIAGNOSTIC — capture per-frame candidate side prices.

    For every WS market_data frame, record what each candidate WS field
    contained alongside what slug_prices currently holds (the value the
    dashboard renders). The buffer is then exposed via /api/extraction-diag
    so an off-process script can render per-player tables comparing all
    candidate sources to the rendered output over time.

    No side effects on the worker's price-update logic — this is read-only
    against `market_data`. Bounded by `EXTRACTION_DIAG_BUFFER_SIZE` per slug.
    """
    try:
        # Side A candidates
        sides = market_data.get("marketSides")
        a_market_sides: Optional[int] = None
        b_market_sides: Optional[int] = None
        if isinstance(sides, list) and len(sides) == 2:
            for idx, key in ((0, "a_market_sides"), (1, "b_market_sides")):
                side = sides[idx]
                if isinstance(side, dict):
                    q = side.get("quote")
                    if isinstance(q, dict):
                        cents = _to_cents(_coerce_price_float(q.get("value")))
                        if key == "a_market_sides":
                            a_market_sides = cents
                        else:
                            b_market_sides = cents

        bids = market_data.get("bids") or []
        offers = market_data.get("offers") or []
        stats = market_data.get("stats") or {}

        best_bid = _extract_px(bids[0].get("px")) if bids and isinstance(bids[0], dict) else None
        best_ask = _extract_px(offers[0].get("px")) if offers and isinstance(offers[0], dict) else None
        last_trade = _extract_px(stats.get("lastTradePx")) if isinstance(stats, dict) else None
        current_px = _extract_px(stats.get("currentPx")) if isinstance(stats, dict) else None

        last_sample = stats.get("lastPriceSample") if isinstance(stats, dict) else None
        long_px: Optional[float] = None
        short_px: Optional[float] = None
        if isinstance(last_sample, dict):
            long_px = _extract_px(last_sample.get("longPx"))
            short_px = _extract_px(last_sample.get("shortPx"))

        def _inv_cents(v: Optional[float]) -> Optional[int]:
            if v is None:
                return None
            return _to_cents(1.0 - v)

        a_best_ask = _to_cents(best_ask)
        a_current = _to_cents(current_px)
        a_last_trade = _to_cents(last_trade)
        a_long = _to_cents(long_px)

        b_inv_best_ask = _inv_cents(best_ask)
        b_inv_current = _inv_cents(current_px)
        b_inv_last_trade = _inv_cents(last_trade)
        b_short = _to_cents(short_px)
        b_inv_long = _inv_cents(long_px)

        # Currently-rendered values (what the dashboard shows for this slug)
        rendered_a = None
        rendered_b = None
        if isinstance(existing_slug_prices, dict):
            rendered_a = existing_slug_prices.get("side_a_cents")
            rendered_b = existing_slug_prices.get("side_b_cents")

        frame_ts = None
        for k in ("transactTime", "timestamp", "ts"):
            v = market_data.get(k)
            if isinstance(v, (str, int)):
                frame_ts = v
                break

        row = {
            "ts_ms": int(time.time() * 1000),
            "frame_ts": frame_ts,
            # side A candidates
            "a_marketSides": a_market_sides,
            "a_best_ask": a_best_ask,
            "a_currentPx": a_current,
            "a_lastTradePx": a_last_trade,
            "a_longPx": a_long,
            # side B candidates
            "b_marketSides": b_market_sides,
            "b_inv_best_ask": b_inv_best_ask,
            "b_inv_currentPx": b_inv_current,
            "b_inv_lastTradePx": b_inv_last_trade,
            "b_shortPx": b_short,
            "b_inv_longPx": b_inv_long,
            # rendered
            "rendered_a": rendered_a,
            "rendered_b": rendered_b,
        }

        buf = _extraction_diag_buffers.get(slug)
        if buf is None:
            buf = deque(maxlen=EXTRACTION_DIAG_BUFFER_SIZE)
            _extraction_diag_buffers[slug] = buf
        buf.append(row)
    except Exception as exc:  # noqa: BLE001 — diagnostic must never break worker
        log.debug("extraction-diag capture skipped slug=%s err=%s", slug, exc)


def _handle_market_data(payload: dict[str, Any]) -> None:
    """One market_data event → update slug_prices + source_timestamps.

    Step 3.9 architecture:
      Merges WS-derived price fields into the existing slug_prices entry
      rather than replacing the whole dict. Discovery loop owns metadata
      and slug existence; WS owns ongoing price updates for already-known
      slugs. We stamp `ws_updated_ms` so the discovery loop's REST-poll
      merge can know whether to defer to WS-fresh prices.

    If the slug is unknown (not in slug_prices yet because discovery
    hasn't seen it), we ignore the WS update — the cross-feed resolver
    needs metadata to use the price, so writing prices for an unmapped
    slug is wasted. Discovery will pick it up within 15s.
    """
    global _raw_md_logged
    if not _raw_md_logged:
        # Operationally critical schema dump on first frame, so any
        # divergence from the speculative Step 3.9 extractor is visible.
        log.info("Polymarket raw market_data sample (one-shot): %s", payload)
        _raw_md_logged = True

    md = payload.get("marketData")
    if not isinstance(md, dict):
        _warn_once("market_data: no marketData container", payload)
        return
    slug = md.get("marketSlug") or md.get("market_slug")
    if not isinstance(slug, str) or not slug:
        _warn_once("market_data: no marketSlug", md)
        return

    # v0.6.12 PRICEDIAG: per-slug one-shot raw payload log.
    # Logs the full payload exactly once for each slug seen, so when a
    # specific market shows wrong prices (Bai 70¢ + Lu 4¢ ≠ 100¢ tell)
    # we can read the actual payload for that slug from Render logs and
    # see which field contains the wrong value.
    if not _per_slug_md_logged.get(slug):
        log.info(
            "[PRICEDIAG] market_data slug=%s (one-shot) payload=%s",
            slug,
            payload,
        )
        _per_slug_md_logged[slug] = True

    # If we've never seen this slug, defer to discovery loop. Writing prices
    # without metadata produces orphan entries the resolver can't use.
    existing = slug_prices.get(slug)
    if existing is None:
        return

    # v0.7.7 EXTRACTION DIAGNOSTIC: capture per-frame candidate prices for
    # off-process analysis. No side effects on price-update logic.
    _capture_extraction_diag(slug, md, existing)

    new_fields = _extract_prices_from_market_data(md)
    if not new_fields:
        return

    # 2026-05-02 unfreeze fix (refined 2026-05-05 v0.7.6):
    # Only claim WS freshness (which suppresses REST overwrites of
    # side_a_cents/side_b_cents in the discovery merge) for the side
    # WS actually wrote. Path B has independent writers for each side
    # (best_ask + spread guard for side_a; lastPriceSample.shortPx +
    # sum-band guard for side_b). When one writer's guard rejects but
    # the other accepts, only the accepted side gets a fresh timestamp.
    # The other side's clock stays at its previous value, so the merge
    # gate allows REST to refresh it.
    #
    # Pre-v0.7.6 used a single `ws_updated_ms` stamp that was set if
    # EITHER side wrote. That suppressed REST refresh for both sides
    # whenever WS wrote either one — which produced the asymmetric-
    # stuck-side bug observed 2026-05-05 (Dellien/De Jong, where
    # Path B's sum-band guard was rejecting side_b but Path A or
    # Path B side_a kept stamping freshness, locking side_b at a
    # stale value while side_a updated sub-second). See
    # docs/investigations/asymmetric-stuck-side-bug-2026-05-05.md.
    #
    # Backward-compat: ws_updated_ms is still maintained as
    # max(ws_a_updated_ms, ws_b_updated_ms) so any reader of the legacy
    # field gets the most-recent-any-side semantics.
    wrote_side_a = "side_a_cents" in new_fields
    wrote_side_b = "side_b_cents" in new_fields

    now_ms = int(time.time() * 1000)
    merged = dict(existing)
    merged.update(new_fields)
    merged["updated_ms"] = now_ms
    if wrote_side_a:
        merged["ws_a_updated_ms"] = now_ms
    if wrote_side_b:
        merged["ws_b_updated_ms"] = now_ms
    # Legacy field: most-recent-any-side. Maintained for any reader
    # that hasn't migrated to per-side clocks.
    if wrote_side_a or wrote_side_b:
        merged["ws_updated_ms"] = now_ms
    slug_prices[slug] = merged
    state.source_timestamps["polymarket"] = now_ms


def _handle_trade(payload: dict[str, Any]) -> None:
    """One trade event → update last_cents + source_timestamps.

    Trades arrive less frequently than market_data (per latency-validation
    cadence study), but they're a useful signal for the liveness counter
    and the last-trade price display.

    Step 3.9: ignore trades for unknown slugs (same as market_data) and
    stamp ws_updated_ms.
    """
    global _raw_trade_logged
    if not _raw_trade_logged:
        log.info("Polymarket raw trade sample (one-shot): %s", payload)
        _raw_trade_logged = True

    trade = payload.get("trade")
    if not isinstance(trade, dict):
        _warn_once("trade: no trade container", payload)
        return
    slug = trade.get("marketSlug") or trade.get("market_slug")
    if not isinstance(slug, str) or not slug:
        _warn_once("trade: no marketSlug", trade)
        return

    # v0.6.12 PRICEDIAG: per-slug one-shot raw trade-payload log.
    # Same diagnostic mechanism as market_data above. Trade events
    # carry maker/taker side info (per latency-validation Finding 2)
    # and may surface in this bug if the price-stuck issue is on the
    # trade-event path rather than the market_data path.
    if not _per_slug_trade_logged.get(slug):
        log.info(
            "[PRICEDIAG] trade slug=%s (one-shot) payload=%s",
            slug,
            payload,
        )
        _per_slug_trade_logged[slug] = True

    existing = slug_prices.get(slug)
    if existing is None:
        return

    last_cents = _to_cents(_extract_px(trade.get("px")))
    if last_cents is None:
        return
    # 2026-05-02 unfreeze fix: same rationale as _handle_market_data above.
    # Trade handler only writes last_cents — never side_a_cents/side_b_cents —
    # so it must NOT stamp ws_updated_ms (which would suppress REST
    # overwrites of the side prices and freeze them). last_cents and
    # updated_ms still update normally.
    now_ms = int(time.time() * 1000)
    merged = dict(existing)
    merged["last_cents"] = last_cents
    merged["updated_ms"] = now_ms
    slug_prices[slug] = merged
    state.source_timestamps["polymarket"] = now_ms


def _batch_slugs(slugs: list[str], cap: int) -> list[list[str]]:
    return [slugs[i : i + cap] for i in range(0, len(slugs), cap)]


async def _markets_ws_loop() -> None:
    """Supervisor: connect MarketsWS, subscribe to active slugs, consume.

    On (re)connect, reads current _active_slugs (populated by discovery
    loop), batches into <=100-slug chunks, opens one WS per batch, and
    subscribes both market_data and trades.

    Backoff on connection loss; reset on successful connect.
    """
    # DIAG-1 (PM-D.2 2026-05-03): confirm task entry. If absent in production
    # logs, the task is being created by gather but never dispatched.
    log.info("DIAG _markets_ws_loop: ENTERED function body")

    if not POLYMARKET_US_API_KEY_ID or not POLYMARKET_US_API_SECRET_KEY:
        log.error(
            "Polymarket worker: POLYMARKET_US_API_KEY_ID and/or "
            "POLYMARKET_US_API_SECRET_KEY not set; worker idle."
        )
        # Still wait — discovery loop runs independently and will surface
        # any gateway issues; this branch just means no live prices.
        while True:
            await asyncio.sleep(60)

    # DIAG-2 (PM-D.2 2026-05-03): confirm we passed the keys check.
    log.info("DIAG _markets_ws_loop: keys present, attempting lazy import")

    # Lazy import — only required when keys present, keeps DEMO_MODE
    # boots fast and tolerates SDK absence in dev.
    try:
        from polymarket_us import (
            APIConnectionError,
            APITimeoutError,
            AsyncPolymarketUS,
            AuthenticationError,
            PolymarketUSError,
            WebSocketError,
        )
    except ImportError as exc:
        log.error(
            "polymarket-us SDK not installed (%s); worker cannot start. "
            "Add 'polymarket-us==0.1.2' to requirements.txt.",
            exc,
        )
        while True:
            await asyncio.sleep(60)
    except BaseException as exc:
        # DIAG-3 (PM-D.2 2026-05-03): catch ANY non-ImportError exception
        # so we surface the actual exception type. Most likely candidates:
        # SystemExit raised inside polymarket_us, RuntimeError from eager
        # init, AttributeError from a transitive 3.14 break.
        log.exception(
            "DIAG _markets_ws_loop: unexpected non-ImportError during lazy import: %r",
            exc,
        )
        raise

    # DIAG-4 (PM-D.2 2026-05-03): import succeeded, about to enter while loop.
    log.info("DIAG _markets_ws_loop: lazy import succeeded, entering main loop")

    backoff = WS_RECONNECT_INITIAL_SECONDS

    # Watchdog state (v0.6.11):
    #   consecutive_failures — count of failed connect attempts since
    #     the last successful connect. Resets to 0 on success.
    #   outage_started_ms     — timestamp (epoch ms) of the first failure
    #     in the current outage. None when not in an outage. Used to
    #     compute duration for the [WS-RECOVERED] log line.
    #   last_failure_class    — exception class name from the most recent
    #     failure. Captured for the [WS-RECOVERED] summary.
    consecutive_failures: int = 0
    outage_started_ms: Optional[int] = None
    last_failure_class: Optional[str] = None

    while True:
        slugs = sorted(_active_slugs)
        if not slugs:
            log.info("Markets WS: no active slugs; idle 30s")
            await asyncio.sleep(30)
            continue

        client: Any = None
        ws_list: list[Any] = []
        closed_event = asyncio.Event()

        try:
            client = AsyncPolymarketUS(
                key_id=POLYMARKET_US_API_KEY_ID,
                secret_key=POLYMARKET_US_API_SECRET_KEY,
            )

            batches = _batch_slugs(slugs, MARKETS_WS_SLUG_CAP)
            log.info(
                "Markets WS: opening %d connection(s) for %d slug(s)",
                len(batches),
                len(slugs),
            )

            for batch_idx, batch in enumerate(batches):
                ws = client.ws.markets()

                def _on_md(msg: dict[str, Any]) -> None:
                    try:
                        _handle_market_data(msg)
                    except Exception:
                        log.exception("market_data handler crashed")

                def _on_trade(msg: dict[str, Any]) -> None:
                    try:
                        _handle_trade(msg)
                    except Exception:
                        log.exception("trade handler crashed")

                def _on_close(*args: Any, **kwargs: Any) -> None:
                    log.info("Markets WS close (batch %d)", batch_idx)
                    closed_event.set()

                def _on_error(err: Any) -> None:
                    log.warning("Markets WS error event (batch %d): %s", batch_idx, err)

                ws.on("market_data", _on_md)
                ws.on("trade", _on_trade)
                ws.on("close", _on_close)
                ws.on("error", _on_error)

                await ws.connect()
                backoff = WS_RECONNECT_INITIAL_SECONDS

                md_req = f"md-{uuid.uuid4().hex[:12]}"
                tr_req = f"tr-{uuid.uuid4().hex[:12]}"
                await ws.subscribe_market_data(md_req, batch)
                await ws.subscribe_trades(tr_req, batch)
                ws_list.append(ws)

            log.info("Markets WS: all %d batches subscribed", len(batches))

            # Watchdog: emit [WS-RECOVERED] when this cycle followed a
            # failure run. Captures outage duration + failure count so
            # post-hoc log review can audit the recovery without needing
            # to read the failed-connect tracebacks. Reset counters on
            # success regardless.
            if consecutive_failures > 0:
                duration_ms = (
                    int(time.time() * 1000) - outage_started_ms
                    if outage_started_ms is not None
                    else 0
                )
                log.info(
                    "[WS-RECOVERED] markets WS reconnected after %d failed attempt(s); "
                    "outage_ms=%d last_failure=%s",
                    consecutive_failures,
                    duration_ms,
                    last_failure_class or "unknown",
                )
            consecutive_failures = 0
            outage_started_ms = None
            last_failure_class = None

            await closed_event.wait()
            log.info("Markets WS: close signal, tearing down")

        except AuthenticationError as exc:
            log.error("Markets WS auth failed: %s", exc)
            backoff = max(backoff, 30.0)
            consecutive_failures += 1
            if outage_started_ms is None:
                outage_started_ms = int(time.time() * 1000)
            last_failure_class = type(exc).__name__
        except (APIConnectionError, APITimeoutError, WebSocketError, PolymarketUSError) as exc:
            log.warning("Markets WS connection issue: %s", exc)
            consecutive_failures += 1
            if outage_started_ms is None:
                outage_started_ms = int(time.time() * 1000)
            last_failure_class = type(exc).__name__
        except Exception as exc:
            log.exception("Markets WS unexpected error: %s", exc)
            consecutive_failures += 1
            if outage_started_ms is None:
                outage_started_ms = int(time.time() * 1000)
            last_failure_class = type(exc).__name__
        finally:
            for ws in ws_list:
                try:
                    await ws.close()
                except Exception:
                    pass
            if client is not None:
                try:
                    await client.close()
                except Exception:
                    pass

        # Watchdog auto-restart trigger (v0.6.11). When N consecutive
        # failures accumulate, exit the process so Render's auto-restart
        # picks it up. Threshold tunable via MARKETS_WS_RESTART_AFTER_N_FAILS;
        # 0 disables. The duration captured in outage_ms gives operators
        # forensic context in pre-restart logs.
        if (
            MARKETS_WS_RESTART_AFTER_N_FAILS > 0
            and consecutive_failures >= MARKETS_WS_RESTART_AFTER_N_FAILS
        ):
            duration_ms = (
                int(time.time() * 1000) - outage_started_ms
                if outage_started_ms is not None
                else 0
            )
            log.error(
                "[WS-WATCHDOG] markets WS exceeded %d consecutive failures "
                "(outage_ms=%d, last_failure=%s); exiting process for auto-restart",
                MARKETS_WS_RESTART_AFTER_N_FAILS,
                duration_ms,
                last_failure_class or "unknown",
            )
            # Flush logs synchronously; os._exit bypasses normal shutdown.
            for handler in logging.getLogger().handlers:
                try:
                    handler.flush()
                except Exception:
                    pass
            os._exit(1)

        log.info("Markets WS reconnecting in %.1fs", backoff)
        await asyncio.sleep(backoff)
        backoff = min(backoff * WS_RECONNECT_FACTOR, WS_RECONNECT_MAX_SECONDS)


# ---- Cross-feed resolver loop ------------------------------------------

# Cadence for the cross-feed resolution sweep. Cheap operation
# (in-memory match), so we can run it more often than discovery.
RESOLVER_INTERVAL_SECONDS: float = 2.0

# Cents-conversion: bid+ask midpoint when both present, else whichever
# side has liquidity, else last_trade. Returns None if everything is None.
def _display_cents(prices: dict) -> Optional[int]:
    """Pick the displayable cent value from a slug_prices entry.

    Priority: midpoint(bid, ask) > bid > ask > last_trade > None.
    The midpoint is the most stable for display; falling back to
    one-sided liquidity covers thin markets; last_trade is a sanity
    fallback if no bids or offers are open.
    """
    bid = prices.get("bid_cents")
    ask = prices.get("ask_cents")
    if bid is not None and ask is not None:
        # Round to nearest int; tie behavior matches int(round(...))'s
        # half-even, which is fine for display.
        return int(round((bid + ask) / 2))
    if bid is not None:
        return bid
    if ask is not None:
        return ask
    return prices.get("last_cents")


# Track which polymarket_event_ids we've already warned about so we don't
# spam the log every resolver pass.
_unmapped_warned: set[str] = set()


async def _resolver_loop() -> None:
    """Periodic sweep: walk slug_metadata × state.matches, write prices.

    Every RESOLVER_INTERVAL_SECONDS:
      1. Reload overrides from disk (cheap, file is small; picks up
         operator edits without redeploy).
      2. Project state.matches into ApiTennisMatchView dicts for the
         resolver. Includes only live matches — Polymarket markets for
         finished/upcoming-only matches won't have meaningful prices
         anyway.
      3. Group slug_metadata by polymarket_event_id (each event has 2
         slugs in our store, one per side).
      4. For each polymarket event, resolve to api_tennis_event_key.
      5. On hit: read the latest prices for both slugs, write into
         state.matches[event_key].p1_price_cents / p2_price_cents per
         the asset_index → side mapping.
      6. On miss: warn-once with polymarket_event_id + names so operator
         can add an override entry.

    Side ordering: API-Tennis player order (first/second) matches the
    fuzzy match's name order. Polymarket event participants[] order
    matches Polymarket's marketSides[] order, captured in the
    asset_index field at discovery time. Both feeds typically use the
    same alphabetical ordering, but we don't depend on that — we map
    by token overlap on each side.
    """
    log.info(
        "Cross-feed resolver starting: cadence=%.1fs, overrides=%s",
        RESOLVER_INTERVAL_SECONDS,
        cross_feed.DEFAULT_OVERRIDES_PATH.name,
    )
    while True:
        try:
            await _resolver_iteration()
        except Exception:
            log.exception("Cross-feed resolver iteration crashed")
        await asyncio.sleep(RESOLVER_INTERVAL_SECONDS)


async def _resolver_iteration() -> None:
    """One pass of the resolver loop. Factored out for testability."""
    overrides = cross_feed.load_overrides()

    # Project live API-Tennis matches into the cross_feed view.
    api_matches: dict[str, cross_feed.ApiTennisMatchView] = {}
    for ek, m in state.matches.items():
        if m.status != "live":
            continue
        # Step F: pass p1_player_key/p2_player_key into the view so the
        # resolver can take the player_key path when both sides are
        # populated. Step A's worker extraction populates these on
        # state.Player; Polymarket-only shadow Players (which have no
        # event in this dict because the loop filters status=="live")
        # don't reach here, so player_key absence is rare in practice.
        api_matches[ek] = cross_feed.ApiTennisMatchView(
            p1_name=m.p1.name,
            p2_name=m.p2.name,
            tournament=m.venue,
            event_date=_today_iso(),  # API-Tennis state doesn't carry per-match date; assume today
            p1_player_key=m.p1.player_key,
            p2_player_key=m.p2.player_key,
        )

    # 2026-05-02: removed early-return when api_matches is empty.
    # The new Polymarket-only upcoming-match path (below) needs to run
    # even when there are no live API-Tennis matches — e.g. quiet
    # weekends where the entire slate is upcoming.

    # Group slug_metadata by polymarket_event_id. Each event normally
    # has exactly 2 slug entries (asset_index 0 and 1) but we built
    # discovery to only register asset_index 0, so each event has
    # 1 slug in our store.
    by_event: dict[str, list[tuple[str, dict]]] = {}
    for slug, meta in slug_metadata.items():
        ev_id = str(meta.get("polymarket_event_id") or "")
        if not ev_id:
            continue
        by_event.setdefault(ev_id, []).append((slug, meta))

    for ev_id, entries in by_event.items():
        # Use the first entry's metadata for resolution (event-level
        # fields are identical across all entries for the same event).
        slug, meta = entries[0]
        event_key_int = cross_feed.resolve_event_key(
            polymarket_event_id=ev_id,
            polymarket_player_a=meta.get("player_a_name", ""),
            polymarket_player_b=meta.get("player_b_name", ""),
            polymarket_tournament=meta.get("tournament_name", ""),
            polymarket_date=meta.get("event_date", ""),
            api_tennis_matches=api_matches,
            overrides=overrides,
        )

        if event_key_int is None:
            # Suppress noise: most Polymarket events the resolver can't
            # match are upcoming matches dated tomorrow+. API-Tennis
            # state only carries today's live matches, so by definition
            # tomorrow's Polymarket events have no API-Tennis counterpart.
            # Logging each one creates 50+ INFO lines per discovery cycle
            # for nothing actionable. Only warn when the date is today
            # or earlier — those are the "real" coverage gaps where an
            # operator override might help.
            if _is_future_date(meta.get("event_date", "")):
                continue
            if ev_id not in _unmapped_warned:
                _unmapped_warned.add(ev_id)
                log.info(
                    "cross_feed: unmapped polymarket_event_id=%s "
                    "(%s vs %s @ %s, %s). Add an override entry to "
                    "cross_feed_overrides.yaml if needed.",
                    ev_id,
                    meta.get("player_a_name", "?"),
                    meta.get("player_b_name", "?"),
                    meta.get("tournament_name", "?"),
                    meta.get("event_date", "?"),
                )
            continue

        ek_str = str(event_key_int)
        match = state.matches.get(ek_str)
        if match is None:
            continue

        # Side mapping: which Polymarket side (a or b) corresponds to
        # API-Tennis player 1 vs player 2? Use name-token overlap.
        # Polymarket discovery extracted player_a / player_b from
        # marketSides[0] / marketSides[1]; their prices live in
        # slug_prices[slug]['side_a_cents'] / 'side_b_cents'.
        #
        # v0.8.0 cutover (2026-05-06): prices now sourced from the
        # Polymarket Global worker (real-time per-token midpoints from
        # the public CLOB WebSocket) instead of this module's
        # Polymarket US WS feed. The Global worker keys its slug_prices
        # dict by the same US slug, so this lookup is a drop-in swap.
        # Falls back to the old US-derived slug_prices if Global has
        # not yet resolved this slug to its Global counterpart (e.g.,
        # a US match with no Polymarket Global market — the
        # global_status field will be 'no_global_market'). The fallback
        # preserves whatever the old code did and guards against
        # losing visibility for matches the Global feed can't see.
        prices = polymarket_global_worker.slug_prices.get(slug)
        if prices and prices.get("global_status") == "resolved":
            cents_a = prices.get("side_a_cents")
            cents_b = prices.get("side_b_cents")
        else:
            # Fallback to the old US worker's slug_prices for this slug.
            prices = slug_prices.get(slug)
            if not prices:
                continue
            cents_a = prices.get("side_a_cents")
            cents_b = prices.get("side_b_cents")

        pm_a_tokens = cross_feed.name_tokens(meta.get("player_a_name", ""))
        pm_b_tokens = cross_feed.name_tokens(meta.get("player_b_name", ""))
        ap1_tokens = cross_feed.name_tokens(match.p1.name)
        ap2_tokens = cross_feed.name_tokens(match.p2.name)
        # Last-tokens (surname proxies) for safe-attribution overlap.
        # See cross_feed.safe_attribution_overlap and
        # docs/investigations/position-fanout-bug-2026-05-05.md.
        ap1_last = cross_feed.name_last_token(match.p1.name)
        ap2_last = cross_feed.name_last_token(match.p2.name)

        # Overlap matrix: which API-Tennis player matches which Polymarket side?
        a1 = len(pm_a_tokens & ap1_tokens)
        a2 = len(pm_a_tokens & ap2_tokens)
        b1 = len(pm_b_tokens & ap1_tokens)
        b2 = len(pm_b_tokens & ap2_tokens)

        # Pick the assignment that maximizes total overlap. Two
        # candidates: A→1/B→2 or A→2/B→1. Take the higher score.
        # Step 3.8: capture old values before assignment for the
        # price_log emitter. Logged only if either side changed.
        old_p1 = match.p1_price_cents
        old_p2 = match.p2_price_cents
        if (a1 + b2) >= (a2 + b1):
            # Polymarket side A → API-Tennis player 1
            match.p1_price_cents = cents_a
            match.p2_price_cents = cents_b
        else:
            # Polymarket side A → API-Tennis player 2 (sides flipped)
            match.p1_price_cents = cents_b
            match.p2_price_cents = cents_a
        price_log.log_price_change(
            event_key=match.event_key,
            p1_name=match.p1.name,
            p2_name=match.p2.name,
            old_p1=old_p1,
            old_p2=old_p2,
            new_p1=match.p1_price_cents,
            new_p2=match.p2_price_cents,
        )

        # Step 9-A C1 (v2): assign open positions to sides via player-name
        # token overlap. We re-use ap1_tokens / ap2_tokens computed above.
        # Reset both sides each cycle so closed positions (no longer in
        # state.open_positions) clear naturally.
        #
        # 2026-05-05 (v0.7.5): switched from raw `overlap > 0` to
        # cross_feed.safe_attribution_overlap which requires either a
        # surname (last-token) match OR 2+ tokens of overlap. Holding
        # fix for the position-fanout bug — see
        # docs/investigations/position-fanout-bug-2026-05-05.md.
        match.p1_position = None
        match.p2_position = None
        for pos in state.open_positions:
            outcome_name = pos.get("outcome", "")
            if not outcome_name:
                continue
            outcome_tokens = cross_feed.name_tokens(outcome_name)
            if not outcome_tokens:
                continue
            outcome_last = cross_feed.name_last_token(outcome_name)
            overlap_p1, overlap_p2 = cross_feed.safe_attribution_overlap(
                outcome_tokens, ap1_tokens, ap2_tokens,
                outcome_last, ap1_last, ap2_last,
            )
            if overlap_p1 == 0 and overlap_p2 == 0:
                continue
            # Pick the side with stronger overlap. Tie → P1 (deterministic).
            target_side = 1 if overlap_p1 >= overlap_p2 else 2
            position_obj = state.Position(
                net_shares=pos["net_shares"],
                cost_cents=pos["cost_cents"],
                cash_value_cents=pos["cash_value_cents"],
                realized_cents=pos["realized_cents"],
                update_time=pos.get("update_time"),
            )
            if target_side == 1:
                match.p1_position = position_obj
            else:
                match.p2_position = position_obj

        # PM-D.3/D.4 unfilled-orders feature — attach resting orders.
        # Same name-overlap join as positions. Reset both lists each
        # cycle so cancelled/filled orders (no longer in
        # state.open_orders) clear naturally. Sort closest-to-fill at
        # top so the operator's eye lands on what's most likely to
        # execute next.
        #
        # 2026-05-05 (v0.7.5): same safe-overlap rule as positions —
        # see comment block above.
        match.p1_orders = []
        match.p2_orders = []
        for order in state.open_orders:
            outcome_name = order.get("outcome", "")
            if not outcome_name:
                continue
            outcome_tokens = cross_feed.name_tokens(outcome_name)
            if not outcome_tokens:
                continue
            outcome_last = cross_feed.name_last_token(outcome_name)
            overlap_p1, overlap_p2 = cross_feed.safe_attribution_overlap(
                outcome_tokens, ap1_tokens, ap2_tokens,
                outcome_last, ap1_last, ap2_last,
            )
            if overlap_p1 == 0 and overlap_p2 == 0:
                continue
            target_side = 1 if overlap_p1 >= overlap_p2 else 2
            if target_side == 1:
                match.p1_orders.append(order)
            else:
                match.p2_orders.append(order)
        # Sort each side closest-to-fill at top.
        match.p1_orders = _sort_orders_closest_to_fill(
            match.p1_orders,
            slug_prices.get(slug, {}).get(
                "side_a_cents" if a1 >= b1 else "side_b_cents"
            ),
        )
        match.p2_orders = _sort_orders_closest_to_fill(
            match.p2_orders,
            slug_prices.get(slug, {}).get(
                "side_a_cents" if a2 >= b2 else "side_b_cents"
            ),
        )

    # ---- Polymarket-only upcoming match creation (2026-05-02) ----------
    #
    # The loop above renders matches whose Polymarket events resolved to a
    # live API-Tennis match (cross-feed worked). On a quiet slate those
    # may be 0. Polymarket lists matches days ahead with prices and player
    # names; the dashboard should show those as upcoming even when no
    # API-Tennis fixture has matched yet.
    #
    # Strategy: second pass over `by_event`. For events not yet rendered
    # via the live-match path, create a Match record keyed by `pm:{ev_id}`
    # so it doesn't collide with API-Tennis numeric event_keys. Status
    # is "upcoming". When (later) the same match goes live and an
    # API-Tennis event_key arrives, the existing path will create a
    # separate `state.matches[<numeric>]` entry and the resolver will pop
    # the `pm:{ev_id}` shadow on next iteration (handled below).
    #
    # Window: matches starting within 24h. Operator-stated requirement.
    # Anything further out is filtered to keep the dashboard focused.
    #
    # Logging: every creation and every transition to live emits a tagged
    # `[PMONLY]` line for post-deploy audit. Set is per-process; restart
    # rebuilds the audit trail from scratch.

    # Build the set of API-Tennis player-token sets for events already
    # rendered live, so we can pop pm:{ev_id} shadows when their match
    # has gone live via the cross-feed path.
    live_player_tokens: list[tuple[set, set]] = []
    for ek, m in state.matches.items():
        if m.status == "live":
            live_player_tokens.append(
                (cross_feed.name_tokens(m.p1.name), cross_feed.name_tokens(m.p2.name))
            )

    for ev_id, entries in by_event.items():
        slug, meta = entries[0]
        prices = slug_prices.get(slug)
        if not prices:
            continue

        ev_date = meta.get("event_date", "")
        if not _is_within_24h(ev_date):
            continue

        pm_p1_name = (meta.get("player_a_name", "") or "").strip()
        pm_p2_name = (meta.get("player_b_name", "") or "").strip()
        if not pm_p1_name or not pm_p2_name:
            continue

        pm_p1_tokens = cross_feed.name_tokens(pm_p1_name)
        pm_p2_tokens = cross_feed.name_tokens(pm_p2_name)
        # Last-tokens for safe-attribution overlap on the shadow path.
        # See cross_feed.safe_attribution_overlap and
        # docs/investigations/position-fanout-bug-2026-05-05.md.
        pm_p1_last = cross_feed.name_last_token(pm_p1_name)
        pm_p2_last = cross_feed.name_last_token(pm_p2_name)

        # If this event already shows up as a live match (cross-feed
        # resolved it earlier in this iteration or in a past iteration),
        # don't shadow it with a pm:{ev_id} entry. Pop any pre-existing
        # shadow so we don't double-render.
        shadow_key = f"pm:{ev_id}"
        already_live = False
        for at1, at2 in live_player_tokens:
            # If the Polymarket players match the live API-Tennis players
            # by name token overlap, this event is already rendered live.
            if (
                (len(pm_p1_tokens & at1) > 0 and len(pm_p2_tokens & at2) > 0)
                or
                (len(pm_p1_tokens & at2) > 0 and len(pm_p2_tokens & at1) > 0)
            ):
                already_live = True
                break
        if already_live:
            if shadow_key in state.matches:
                log.info(
                    "[PMONLY] transition: ev_id=%s shadow=%s → live match found, "
                    "popping shadow (%s vs %s)",
                    ev_id, shadow_key, pm_p1_name, pm_p2_name,
                )
                state.matches.pop(shadow_key, None)
            continue

        cents_a = prices.get("side_a_cents")
        cents_b = prices.get("side_b_cents")

        # Sackmann lookups for rank + pre-match probability.
        # Tour inferred from slug prefix or league field.
        league = (meta.get("league") or "").lower()
        tour_label = "ATP" if league == "atp" else "WTA" if league == "wta" else "Ch."
        sackmann_tour = league if league in ("atp", "wta") else None
        p1_rank: Optional[int] = None
        p2_rank: Optional[int] = None
        p1_pre_pct: Optional[int] = None
        p2_pre_pct: Optional[int] = None
        if sackmann_tour:
            try:
                from . import sackmann
                p1_rank = sackmann.lookup_ranking(pm_p1_name, sackmann_tour)
                p2_rank = sackmann.lookup_ranking(pm_p2_name, sackmann_tour)
                prob = sackmann.match_probability(pm_p1_name, pm_p2_name, sackmann_tour, surface=None)
                if prob is not None:
                    p1_pre_pct = int(round(prob[0]))
                    p2_pre_pct = int(round(prob[1]))
            except Exception:
                # Sackmann lookups should never crash the resolver. Log
                # and continue with None ranks/pcts.
                log.exception("[PMONLY] sackmann lookup failed for ev_id=%s", ev_id)

        existing = state.matches.get(shadow_key)
        # v0.8.5 (PM-D7): start_time IS available — Polymarket's startDate
        # carries a full ISO timestamp; preserved as start_date_iso through
        # slug_metadata (changes 1 and 2 in polymarket_global_worker.py).
        # The prior code's "Polymarket doesn't expose match-start time"
        # comment was incorrect — the upstream code was truncating the
        # timestamp at ingestion. With this fix, pm: shadow matches sort
        # correctly alongside API-Tennis-keyed matches in
        # state.snapshot()'s chronological sort.
        # See docs/PM-D7-Start-Time-Bug-Fix-2026-05-06.md.
        pm_start_time = meta.get("start_date_iso") or None

        if existing is None:
            # Bootstrap player_key + country from player_metadata.
            # Steps B+E: name lookup against the bundled CSV. Returns
            # full record if name is known to the metadata; None if
            # player isn't in the CSV (brand new, hasn't appeared in
            # API-Tennis standings yet) — degraded to player_key=None,
            # country_iso3=None for that match. Self-corrects on next
            # metadata refresh.
            p1_meta = player_metadata.lookup_by_name(pm_p1_name)
            p2_meta = player_metadata.lookup_by_name(pm_p2_name)
            p1_player_key = p1_meta["player_key"] if p1_meta else None
            p2_player_key = p2_meta["player_key"] if p2_meta else None
            p1_country = p1_meta["country_iso3"] if p1_meta else None
            p2_country = p2_meta["country_iso3"] if p2_meta else None

            # Create new Polymarket-only Match record
            new_match = state.Match(
                event_key=shadow_key,
                tour=tour_label,
                venue=meta.get("tournament_name", "") or "",
                round="",
                status="upcoming",
                start_time=pm_start_time,
                p1=state.Player(name=pm_p1_name, country_iso3=p1_country, player_key=p1_player_key),
                p2=state.Player(name=pm_p2_name, country_iso3=p2_country, player_key=p2_player_key),
                p1_price_cents=cents_a,
                p2_price_cents=cents_b,
                p1_rank=p1_rank,
                p2_rank=p2_rank,
                p1_pre_pct=p1_pre_pct,
                p2_pre_pct=p2_pre_pct,
            )
            state.matches[shadow_key] = new_match
            log.info(
                "[PMONLY] created: ev_id=%s key=%s %s (%s, key=%s, %s) vs %s (%s, key=%s, %s) "
                "prices=(%s,%s) ranks=(%s,%s) date=%s",
                ev_id, shadow_key,
                pm_p1_name, tour_label, p1_player_key, p1_country,
                pm_p2_name, tour_label, p2_player_key, p2_country,
                cents_a, cents_b, p1_rank, p2_rank, ev_date,
            )
        else:
            # Update prices on existing shadow. Don't overwrite unrelated
            # fields (e.g. positions added by the position-attach path).
            old_p1_price = existing.p1_price_cents
            old_p2_price = existing.p2_price_cents
            existing.p1_price_cents = cents_a
            existing.p2_price_cents = cents_b
            existing.p1_rank = p1_rank
            existing.p2_rank = p2_rank
            existing.p1_pre_pct = p1_pre_pct
            existing.p2_pre_pct = p2_pre_pct
            # v0.8.5 (PM-D7): refresh start_time on existing shadows so
            # an in-place upgrade from None to the correct timestamp
            # happens cleanly without a worker restart.
            existing.start_time = pm_start_time
            if old_p1_price != cents_a or old_p2_price != cents_b:
                log.info(
                    "[PMONLY] price-update: ev_id=%s key=%s "
                    "p1: %s→%s p2: %s→%s",
                    ev_id, shadow_key, old_p1_price, cents_a, old_p2_price, cents_b,
                )

        # Position attach for shadow matches — same logic as live path.
        # 2026-05-05 (v0.7.5): safe-overlap rule applied here too —
        # see docs/investigations/position-fanout-bug-2026-05-05.md.
        match = state.matches[shadow_key]
        match.p1_position = None
        match.p2_position = None
        for pos in state.open_positions:
            outcome_name = pos.get("outcome", "")
            if not outcome_name:
                continue
            outcome_tokens = cross_feed.name_tokens(outcome_name)
            if not outcome_tokens:
                continue
            outcome_last = cross_feed.name_last_token(outcome_name)
            overlap_p1, overlap_p2 = cross_feed.safe_attribution_overlap(
                outcome_tokens, pm_p1_tokens, pm_p2_tokens,
                outcome_last, pm_p1_last, pm_p2_last,
            )
            if overlap_p1 == 0 and overlap_p2 == 0:
                continue
            target_side = 1 if overlap_p1 >= overlap_p2 else 2
            position_obj = state.Position(
                net_shares=pos["net_shares"],
                cost_cents=pos["cost_cents"],
                cash_value_cents=pos["cash_value_cents"],
                realized_cents=pos["realized_cents"],
                update_time=pos.get("update_time"),
            )
            if target_side == 1:
                match.p1_position = position_obj
            else:
                match.p2_position = position_obj

        # PM-D.3/D.4 unfilled-orders feature — attach resting orders
        # for shadow matches. Same logic as live path; in the PMONLY
        # path side a maps to p1 and side b to p2 (discovery assigns
        # pm_p1_name from marketSides[0]).
        # 2026-05-05 (v0.7.5): safe-overlap rule applied here too —
        # see docs/investigations/position-fanout-bug-2026-05-05.md.
        match.p1_orders = []
        match.p2_orders = []
        for order in state.open_orders:
            outcome_name = order.get("outcome", "")
            if not outcome_name:
                continue
            outcome_tokens = cross_feed.name_tokens(outcome_name)
            if not outcome_tokens:
                continue
            outcome_last = cross_feed.name_last_token(outcome_name)
            overlap_p1, overlap_p2 = cross_feed.safe_attribution_overlap(
                outcome_tokens, pm_p1_tokens, pm_p2_tokens,
                outcome_last, pm_p1_last, pm_p2_last,
            )
            if overlap_p1 == 0 and overlap_p2 == 0:
                continue
            target_side = 1 if overlap_p1 >= overlap_p2 else 2
            if target_side == 1:
                match.p1_orders.append(order)
            else:
                match.p2_orders.append(order)
        # Sort each side closest-to-fill at top.
        match.p1_orders = _sort_orders_closest_to_fill(match.p1_orders, cents_a)
        match.p2_orders = _sort_orders_closest_to_fill(match.p2_orders, cents_b)


def _is_within_24h(iso_date: str) -> bool:
    """Return True if iso_date (YYYY-MM-DD) is today, tomorrow, or in
    the past (delayed). Used to scope Polymarket-only upcoming match
    rendering to the operator's 24h trade-planning window.

    A 'today or tomorrow' check is a coarse proxy for '<= 24h from now'
    since Polymarket's per-event payload only carries calendar date,
    not start time. Operator's stated requirement is a 24h window;
    today+tomorrow gives them the planning horizon they want, with
    Sunday's late matches included on Saturday evenings, etc.
    """
    if not isinstance(iso_date, str) or not iso_date:
        return False
    from datetime import datetime, timezone, timedelta
    try:
        d = datetime.strptime(iso_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return False
    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)
    return d <= tomorrow


def _today_iso() -> str:
    """Return today's date as YYYY-MM-DD UTC. Used for API-Tennis match
    date inference until/unless we wire per-match date through state."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _is_future_date(iso_date: str) -> bool:
    """Return True if iso_date (YYYY-MM-DD) is strictly after today UTC.

    Tolerant of garbage input — returns False on parse failure so a
    malformed date doesn't suppress a real warning.
    """
    if not isinstance(iso_date, str) or not iso_date:
        return False
    from datetime import datetime, timezone
    try:
        d = datetime.strptime(iso_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return False
    return d > datetime.now(timezone.utc).date()


# ---- Public entry point ------------------------------------------------


async def _positions_loop() -> None:
    """Periodic poll of operator's open positions from Polymarket.

    Step 9-A C1 (v2). Cadence POSITIONS_POLL_INTERVAL_SECONDS. Fetches
    via `client.portfolio.positions()` (SDK wraps GET
    /v1/portfolio/positions), paginates until eof, and writes flattened
    entries into `state.open_positions` (a flat list, not a dict).

    The resolver loop iterates `state.open_positions` on every cycle
    and joins each position to its match by player-name token overlap
    (same strategy prices use). We do NOT key by slug because the slug
    returned by the positions API is a per-side slug that doesn't
    reliably match what discovery registers — discovery registers only
    asset_index 0 slugs for each event.

    On auth failure or transient error: log and continue. Loop never
    raises.
    """
    if not POLYMARKET_US_API_KEY_ID or not POLYMARKET_US_API_SECRET_KEY:
        log.info("positions loop: no API keys, skipping")
        return

    try:
        from polymarket_us import AsyncPolymarketUS, PolymarketUSError
    except ImportError as exc:
        log.error("positions loop: SDK not installed (%s); idle", exc)
        return

    log.info(
        "positions loop starting: cadence=%ds",
        POSITIONS_POLL_INTERVAL_SECONDS,
    )

    backoff = 1.0
    while True:
        try:
            await _positions_iteration_with_client(AsyncPolymarketUS, PolymarketUSError)
            backoff = 1.0  # reset on success
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("positions iteration crashed; backing off %.1fs", backoff)
            await asyncio.sleep(min(backoff, 60.0))
            backoff = min(backoff * 2.0, 60.0)
            continue
        await asyncio.sleep(POSITIONS_POLL_INTERVAL_SECONDS)


async def _positions_iteration_with_client(
    AsyncPolymarketUS: Any,
    PolymarketUSError: type,
) -> None:
    """One pass: fetch all pages, replace state.open_positions atomically."""
    client = AsyncPolymarketUS(
        key_id=POLYMARKET_US_API_KEY_ID,
        secret_key=POLYMARKET_US_API_SECRET_KEY,
    )
    try:
        new_positions: list[dict] = []
        cursor: Optional[str] = None
        page_count = 0
        max_pages = 20  # safety cap; operator typically has <50 positions

        while page_count < max_pages:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            try:
                resp = await client.portfolio.positions(params)
            except PolymarketUSError as exc:
                log.warning("positions API error: %s", exc)
                return

            positions_obj = resp.get("positions") or {}
            for slug_key, pos in positions_obj.items():
                # Skip fully-closed positions (Polymarket sometimes returns
                # these with netPosition=0 instead of dropping them).
                net = _to_int(pos.get("netPosition"))
                if net is None or net == 0:
                    continue

                cost_cents = _amount_to_cents(pos.get("cost"))
                cash_cents = _amount_to_cents(pos.get("cashValue"))
                realized_cents = _amount_to_cents(pos.get("realized"))
                if cost_cents is None or cash_cents is None or realized_cents is None:
                    continue

                meta = pos.get("marketMetadata") or {}
                outcome = meta.get("outcome", "")
                event_slug = meta.get("eventSlug")
                title = meta.get("title")

                # outcome is the player name (e.g. "Carlos Alcaraz") —
                # the join key the resolver uses.
                if not outcome:
                    log.warning(
                        "positions: skipping position with no outcome name "
                        "(slug=%s, title=%s)", slug_key, title
                    )
                    continue

                new_positions.append({
                    "outcome": outcome,
                    "net_shares": net,
                    "cost_cents": cost_cents,
                    "cash_value_cents": cash_cents,
                    "realized_cents": realized_cents,
                    "update_time": pos.get("updateTime"),
                    "event_slug": event_slug,
                    "title": title,
                })

            page_count += 1
            if resp.get("eof"):
                break
            cursor = resp.get("nextCursor")
            if not cursor:
                break

        # Replace global atomically (single assignment, no concurrent writers)
        state.open_positions = new_positions

        log.info(
            "positions: %d open position(s) loaded across %d page(s)",
            len(new_positions),
            page_count,
        )
    finally:
        # SDK may or may not need close; defensive
        close = getattr(client, "close", None)
        if callable(close):
            try:
                result = close()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass


# PM-D.3/D.4 unfilled-orders feature.
#
# Resting limit orders the operator has placed on Polymarket and that
# have not yet fully filled. Polled every ORDERS_POLL_INTERVAL_SECONDS
# (30s default), normalized to a flat list, joined to matches by the
# resolver via player-name overlap (same strategy as positions).
#
# The SDK's client.orders.list() wraps GET /v1/orders/open. Returns
# GetOpenOrdersResponse = {"orders": list[Order]}. Each Order carries
# id, marketSlug, side, type, price, quantity, cumQuantity,
# leavesQuantity, state, intent, marketMetadata, insertTime.
#
# We filter to ORDER_TYPE_LIMIT only — market orders aren't "resting"
# by definition; they execute on submit and appear in the trades feed,
# not the open-orders feed. Filtering belt-and-suspenders.
async def _orders_loop() -> None:
    """Periodic poll of operator's open resting orders from Polymarket.

    Cadence ORDERS_POLL_INTERVAL_SECONDS. Fetches via client.orders.list()
    (SDK wraps GET /v1/orders/open), paginates until eof, and writes
    flattened entries into state.open_orders (a flat list, not a dict).

    The resolver loop iterates state.open_orders on every cycle and
    joins each order to its match by player-name token overlap.

    On auth failure or transient error: log and continue. Loop never
    raises (mirrors _positions_loop pattern).
    """
    if not POLYMARKET_US_API_KEY_ID or not POLYMARKET_US_API_SECRET_KEY:
        log.info("orders loop: no API keys, skipping")
        return

    try:
        from polymarket_us import AsyncPolymarketUS, PolymarketUSError
    except ImportError as exc:
        log.error("orders loop: SDK not installed (%s); idle", exc)
        return

    log.info(
        "orders loop starting: cadence=%ds",
        ORDERS_POLL_INTERVAL_SECONDS,
    )

    backoff = 1.0
    while True:
        try:
            await _orders_iteration_with_client(AsyncPolymarketUS, PolymarketUSError)
            backoff = 1.0  # reset on success
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("orders iteration crashed; backing off %.1fs", backoff)
            await asyncio.sleep(min(backoff, 60.0))
            backoff = min(backoff * 2.0, 60.0)
            continue
        await asyncio.sleep(ORDERS_POLL_INTERVAL_SECONDS)


async def _orders_iteration_with_client(
    AsyncPolymarketUS: Any,
    PolymarketUSError: type,
) -> None:
    """One pass: fetch all pages, replace state.open_orders atomically."""
    client = AsyncPolymarketUS(
        key_id=POLYMARKET_US_API_KEY_ID,
        secret_key=POLYMARKET_US_API_SECRET_KEY,
    )
    try:
        new_orders: list[dict] = []
        cursor: Optional[str] = None
        page_count = 0
        max_pages = 20  # safety cap; operator typically has <50 resting orders

        while page_count < max_pages:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["cursor"] = cursor
            try:
                resp = await client.orders.list(params)
            except PolymarketUSError as exc:
                log.warning("orders API error: %s", exc)
                return

            orders_list = resp.get("orders") or []
            for order in orders_list:
                # Filter: only LIMIT orders are "resting." Market orders
                # execute on submit and don't sit in the open-orders feed
                # in the steady state, but defensive filter regardless.
                otype = order.get("type", "")
                if "LIMIT" not in str(otype).upper():
                    continue

                raw_price_cents = _amount_to_cents(order.get("price"))
                quantity = _to_int(order.get("quantity"))
                cum_qty = _to_int(order.get("cumQuantity")) or 0
                leaves_qty = _to_int(order.get("leavesQuantity"))

                if raw_price_cents is None or quantity is None:
                    log.warning(
                        "orders: skipping order with bad price/qty (id=%s, "
                        "price=%r, quantity=%r)",
                        order.get("id"), order.get("price"), order.get("quantity"),
                    )
                    continue

                # Defensive: if leavesQuantity is missing, derive from
                # quantity - cumQuantity. Should never happen with the
                # current SDK shape but harmless.
                if leaves_qty is None:
                    leaves_qty = max(quantity - cum_qty, 0)

                # Skip orders with no leaves — they're effectively done.
                # The SDK should drop these naturally but defensive.
                if leaves_qty <= 0:
                    continue

                # v0.7.3: read intent and apply operator-perspective transform
                # per docs/trade-data-semantics.md.
                #
                # Operator-perspective rules (from the doc, gospel):
                # 1. The operator never places SELL orders. The iPhone app
                #    only offers "Buy [Player]" — there is no SHORT operation
                #    available to retail users. The `side` field returned by
                #    the SDK is the order-book ROUTING side (which token leg
                #    matched), NOT an operator-facing buy/sell. Display every
                #    operator-placed limit order as a BUY.
                # 2. The `price` field returned by the SDK is the raw routed-
                #    side price. Operator-perspective price (what the iPhone
                #    receipt shows) requires:
                #       LONG  → price as-is
                #       SHORT → 100 − price (complement)
                # 3. The `outcome` field is the operator-bought player on
                #    every order, both LONG and SHORT. Already correct
                #    (already used as the resolver join key).
                #
                # Empirically verified by Marrero Curbelo order on 2026-05-04:
                #   API: side=SELL, price=19¢, intent=ORDER_INTENT_BUY_SHORT,
                #        outcome="Ivan Marrero"
                #   Receipt: "You bought Ivan Marrero, $80.81 cost, 81% odds"
                #   Operator-odds = 100 − 19 = 81% ✓
                #
                # We capture both raw and operator-perspective fields. The
                # frontend renders operator-perspective; raw is preserved for
                # diagnostic and recorder purposes.
                raw_side = str(order.get("side", "")).upper()
                intent = str(order.get("intent", "")).upper()

                # Side normalization for the raw field (diagnostic only).
                if "BUY" in raw_side:
                    raw_side_norm = "BUY"
                elif "SELL" in raw_side:
                    raw_side_norm = "SELL"
                else:
                    log.warning(
                        "orders: skipping order with unknown side (id=%s, "
                        "side=%r)", order.get("id"), order.get("side"),
                    )
                    continue

                # Direction (LONG vs SHORT) from intent. The intent values
                # for resting limit orders are ORDER_INTENT_BUY_LONG and
                # ORDER_INTENT_BUY_SHORT (operator never opens via SELL).
                # Defensive: also handle SELL_* in case the SDK exposes
                # closing-leg orders here in some future shape.
                if "SHORT" in intent:
                    direction = "SHORT"
                elif "LONG" in intent:
                    direction = "LONG"
                else:
                    # Unknown intent — fall back to LONG (no transform). Log
                    # so we notice unfamiliar intent values from the SDK.
                    log.warning(
                        "orders: unknown intent on order id=%s intent=%r — "
                        "treating as LONG (no price complement)",
                        order.get("id"), order.get("intent"),
                    )
                    direction = "LONG"

                # Operator-perspective side: always BUY. The iPhone app only
                # offers buys for retail users, so a resting limit is always
                # a buy from the operator's perspective regardless of routing.
                # We keep the field in the dict for frontend stability but
                # the renderer should treat the COND row as a buy regardless.
                side_norm = "BUY"

                # Operator-perspective price: complement on SHORT, as-is on LONG.
                if direction == "SHORT":
                    price_cents = 100 - raw_price_cents
                else:
                    price_cents = raw_price_cents

                meta = order.get("marketMetadata") or {}
                outcome = meta.get("outcome", "")
                event_slug = meta.get("eventSlug")

                # outcome is the player name — the join key the resolver uses.
                if not outcome:
                    log.warning(
                        "orders: skipping order with no outcome name "
                        "(id=%s)", order.get("id"),
                    )
                    continue

                new_orders.append({
                    "id": order.get("id", ""),
                    "outcome": outcome,
                    # Operator-perspective fields (rendered by frontend):
                    "side": side_norm,        # always "BUY" per op-perspective
                    "price_cents": price_cents,  # complemented if SHORT
                    # Raw routed-side fields (kept for diagnostic/recorder):
                    "raw_side": raw_side_norm,
                    "raw_price_cents": raw_price_cents,
                    "intent": intent,
                    "direction": direction,
                    # Quantities and metadata (unchanged):
                    "quantity": quantity,
                    "cum_quantity": cum_qty,
                    "leaves_quantity": leaves_qty,
                    "state": str(order.get("state", "")),
                    "insert_time": order.get("insertTime"),
                    "event_slug": event_slug,
                })

            page_count += 1
            if resp.get("eof"):
                break
            cursor = resp.get("nextCursor")
            if not cursor:
                break

        # Replace global atomically (single assignment, no concurrent writers)
        state.open_orders = new_orders

        log.info(
            "orders: %d open order(s) loaded across %d page(s)",
            len(new_orders),
            page_count,
        )
    finally:
        # SDK may or may not need close; defensive (mirrors positions pattern)
        close = getattr(client, "close", None)
        if callable(close):
            try:
                result = close()
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass


def _sort_orders_closest_to_fill(
    orders: list[dict],
    current_price_cents: Optional[int],
) -> list[dict]:
    """Sort resting orders by closest-to-fill (operator-perspective).

    v0.7.3: every operator-placed limit order is a BUY from the operator's
    perspective (per docs/trade-data-semantics.md — the iPhone app only
    offers buys). The sort is therefore one-dimensional: smallest
    distance from current price down to the target wins.

    A buy-limit fills when the market price drops to or below the target.
    Distance to fill = current − target. Operators commonly stack
    multiple buy-limits at descending price targets; the one with the
    target closest to current bubbles up.

    Negative distances mean the target sits ABOVE current price — the
    order would have executed already if placed marketable, so it
    sitting open implies the bid hasn't been hit yet (large size, or
    sub-tick rounding). We still sort by distance ascending; a slightly
    above-current target will be near zero distance and rank near the
    top, which is correct.

    current_price_cents may be None (price unavailable for that side);
    fall back to highest-target-first (orders most likely to fill if
    market is currently elevated above target).
    """
    if not orders:
        return orders

    if current_price_cents is None:
        # Fallback: highest target first. With every order a BUY,
        # the higher-priced bids fill first as price decays.
        return sorted(orders, key=lambda o: -o.get("price_cents", 0))

    def distance(o: dict) -> int:
        # All operator orders are BUYs (op-perspective). Distance to
        # fill is how far current price is above the target.
        target = o.get("price_cents", 0)
        return current_price_cents - target

    return sorted(orders, key=distance)


def _to_int(v: Any) -> Optional[int]:
    """Convert string/int to int. Polymarket returns netPosition as a string."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v.strip())
        except ValueError:
            try:
                return int(float(v.strip()))
            except (ValueError, TypeError):
                return None
    return None


def _amount_to_cents(amt: Any) -> Optional[int]:
    """Convert Polymarket's Amount {value: str, currency: 'USD'} to int cents.

    Values like {"value": "44.50", "currency": "USD"} → 4450 cents.
    """
    if not isinstance(amt, dict):
        return None
    val = amt.get("value")
    if val is None:
        return None
    try:
        dollars = float(str(val).strip())
        return int(round(dollars * 100))
    except (ValueError, TypeError):
        return None


async def run() -> None:
    """Top-level entry. Runs discovery + resolver + (optionally) WS in parallel.

    Step 3.9 architecture:
      Discovery loop: polls Gamma REST every 15s. Owns slug existence,
        metadata, and INITIAL prices on first slug appearance. Falls
        back to writing REST prices when WS hasn't updated a slug
        within WS_FRESHNESS_WINDOW_MS.
      WS supervisor (when MARKETS_WS_ENABLED=1): subscribes to active
        slugs as they appear in discovery, consumes market_data and
        trade events, merges per-side prices into existing slug_prices
        entries.
      Resolver: reads slug_prices to populate Match.p1_price_cents /
        Match.p2_price_cents on every cycle.

    Cancellable; clean shutdown propagates through child tasks.
    Mirrors api_tennis_worker.run() shape so main.py's lifespan can
    treat both workers identically.
    """
    log.info(
        "polymarket_worker starting (mode=%s, ws_freshness=%dms)",
        "REST+WS" if MARKETS_WS_ENABLED else "REST-only",
        WS_FRESHNESS_WINDOW_MS,
    )
    tasks: list[asyncio.Task] = [
        asyncio.create_task(_discovery_loop(), name="pm_discovery"),
        asyncio.create_task(_resolver_loop(), name="pm_resolver"),
    ]
    if POLYMARKET_US_API_KEY_ID and POLYMARKET_US_API_SECRET_KEY:
        tasks.append(asyncio.create_task(_positions_loop(), name="pm_positions"))
        tasks.append(asyncio.create_task(_orders_loop(), name="pm_orders"))
    if MARKETS_WS_ENABLED:
        tasks.append(asyncio.create_task(_markets_ws_loop(), name="pm_markets_ws"))
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        raise
