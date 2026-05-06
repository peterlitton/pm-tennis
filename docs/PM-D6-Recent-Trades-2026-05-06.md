# PM-D.6 — Recent Trades section + Trading Performance page header refresh

**Status:** Specification locked, build instructions below
**Author:** PM-D.6 with operator (Peter)
**Date:** 2026-05-06
**Affects:** `/trading` page (templates/trading.html, src/main.py route, static/trading.css)
**Production version at design time:** Trading v0.5.1 → bumping to Trading v0.8.4

---

## Background

The `/trading` page (Trading v0.5.1) gives the operator a daily performance review: today's cash P&L card, three stat tiles (Closed / Return on capital / Activity), and a Closed Contracts table where each row expands to show fills.

What's missing: a **flat list of every executed transaction** for the day, in chronological order, that the operator can scan at a glance. The Closed Contracts table groups by contract — useful for understanding what completed but not for answering "what just happened?" The operator's stated need is to spot conditional (limit) orders that have filled while away from the dashboard, plus general "did I do what I think I did today?" review.

The Polymarket activity API and the existing trade-attribution pipeline already expose every fill as a row inside `raw_fills`. A Recent Trades section flattens those across contracts and sorts newest-first. No new data source is required for player, time, side, rate, qty, or amount. There IS one data gap (order type — Market vs Limit) flagged below.

This doc also captures the operator-driven header changes shipping in the same release: title rename, Live Tennis link, refresh button, and footer consolidation.

## What changes

### Change 1 — Header

| Element | Before | After |
|---|---|---|
| Title | "Trading" | "Trading Performance" |
| Live Tennis link | (none) | Quiet text link in header right cluster, opens `/` in new tab |
| Refresh button | (none) | Grey jelly-bean icon button (circular-arrow SVG), full page reload on click |

Live Tennis link styling matches the "Performance" link added to the live dashboard in v0.8.3 (`.header-link` class — tertiary text color, dotted underline, hover-lifts to primary text). On the trading page the analogous class is `.t-live-link`.

The refresh button uses `.t-refresh-btn` — `border-radius: 999px`, light-grey fill matching `--bg-row-header`, hover state darkens slightly. SVG is the standard refresh-arrow path (~13×13 px).

### Change 2 — Footer

| Before | After |
|---|---|
| `As of 1:33:10 pm` (separate line) + `Trading v0.5.1 · Refresh page for current data` (footer block) | Single line: `As of HH:MM AM/PM TZ · Trading v0.8.4` |

Specifically:

- "Refresh page for current data" copy removed (the new refresh button is the affordance)
- Time format aligned to `HH:MM AM/PM TZ` (operator standard — drops seconds)
- Version moved onto the same line as the timestamp
- Single horizontal rule above the line, centered text

### Change 3 — Recent trades section

A new `<div class="t-recent-section">` rendered after the Closed Contracts table.

**Per-row columns (operator-locked):**

| Column | Format | Source |
|---|---|---|
| Player | Player backed (single name string) | `c["backed_player"]` from the contract |
| Time | `HH:MM AM/PM` in operator's tz | derived from `raw_fill["utc_dt"]`, formatted via `local_tz` |
| State | `Bought` / `Sold` | `raw_fill["side"]` ("Buy" → "Bought", "Sell" → "Sold"); resolution rows go to Condition instead |
| Condition | `Market` / `Limit` / `Won` / `Lost` | See "Order-type data gap" below for Market/Limit; `Won`/`Lost` from `is_resolution=True` + `is_win` |
| Rate | `N¢` (e.g. `45¢`); $1.00 / $0.00 for settlements | `raw_fill["price"]` × 100, rounded |
| Qty | Integer share count | `raw_fill["shares"]` |
| Amount | `+$N.NN` green / `−$N.NN` red | `raw_fill["cash_flow"]`; sign drives color |

**Section behavior:**

- One row per executed transaction (every individual fill OR resolution event). No consolidation by player, contract, or match.
- Sort: newest at top.
- Date scope: the displayed date (today by default; respects `?date=YYYY-MM-DD`). A transaction is "for that day" if its local-tz timestamp falls on that calendar date, matching the existing `filter_to_date_local` semantics already used for headline aggregates.
- **Resting limit orders that have NOT filled are NOT shown.** Pending orders are excluded — only printed (filled) trades and settlement events appear.
- Section heading: "Recent trades" (lowercase t per the existing `.t-table-title` style), with hint text "today's executed transactions, newest first" right of the title.

**State / Condition mapping (worked rules):**

| Underlying event | State | Condition |
|---|---|---|
| Buy fill (any order type) | Bought | Market or Limit (per order-type lookup; see gap below) |
| Sell fill (any order type) | Sold | Market or Limit (per order-type lookup) |
| Settlement at $1 (long) or $0 (short) | (last fill direction — typically "Bought") | `Won` (green) |
| Settlement at $0 (long) or $1 (short) | (last fill direction) | `Lost` (red) |

> Note on settlements: the State column is intentionally the operator's last action (Bought/Sold), not the resolution itself. The resolution dimension is captured in Condition (`Won`/`Lost`). This was an explicit operator decision — State should describe what the operator did; Condition describes the meta-status (how it filled / how it ended).

### Change 4 — Indicator legend / docs touch

The page does not currently include an indicator legend (only the live dashboard does), so no in-page legend update is needed. Docs to update:

- `docs/PM-Tennis-Pricing-Architecture-Handoff.md`: add a brief mention of the Recent Trades section in any Trading-page section (currently the doc is silent on `/trading`; minimum-effort note recommended).
- `docs/runbook.md` (if a project SOP touches the trading page rendering): note the section exists.
- This file (`docs/PM-D6-Recent-Trades-2026-05-06.md`): canonical spec.

## Order-type data gap (Market vs Limit)

**The current Polymarket activity API parsing in `trades_csv.py` does NOT capture order type.** The `raw_fill` dict has `side`, `shares`, `price`, `cash_flow`, etc., but no `order_type` field. The Polymarket trade payload includes a side (`ORDER_SIDE_BUY` / `ORDER_SIDE_SELL`) but does not surface market-vs-limit at the trade level in the data we currently parse.

**Resolution options:**

1. **Display blank / "—" for Condition on all non-settlement rows** — ship Recent Trades immediately without the Market/Limit distinction. Add the column wiring; populate when the data source is available.

2. **Cross-reference the open-orders log** — when a fill timestamp matches a previously-seen open limit order (by price + side + market), label it "Limit"; otherwise "Market". Requires plumbing the orders-history into the trades pipeline. Non-trivial.

3. **Inspect a different Polymarket endpoint** — the orders endpoint (`/v1/portfolio/orders`) may carry order-type metadata. Investigation needed; may be a one-line addition to the activity parse if order context is exposed there.

**Recommended for v1 ship: Option 1.** Render the Condition column with `—` for fill rows, `Won`/`Lost` for settlement rows. Operator gets the section now, with the most operationally important condition (settlements) immediately visible. Market/Limit becomes a follow-up once the data source is identified.

This is operator-decision territory — flag at build review time. The mockup uses sample Market/Limit values for visual completeness, but the v1 wire MUST default Condition to `—` for fill rows unless option 2 or 3 is implemented in the same ship.

## Implementation instructions

### Step 1 — Backend: extend the trading page route

In `src/main.py` `trading_page` route, after the existing `summary` is built, build a flat list of recent trades from `wide_rows` (the wide-fetch row set, which includes all fills for contracts touched in the lookback window):

```python
# After summary is built, before TemplateResponse:
recent_trades = []
for c in wide_summary.get("closed_contracts", []) + wide_summary.get("open_contracts", []):
    backed_player = c.get("backed_player") or "—"
    is_short = c.get("direction") == "SHORT"
    for fill in c.get("raw_fills", []):
        # fill date must match display_date in local tz
        fill_local = fill["utc_dt"].astimezone(local_tz) if fill.get("utc_dt") else None
        if fill_local is None or fill_local.strftime("%Y-%m-%d") != display_date:
            continue

        # Map side → State (Bought/Sold/—)
        if fill["is_resolution"]:
            # Resolution row: State carries the most recent non-resolution
            # action's side; Condition carries Won/Lost. For v1 simplicity,
            # display State as blank on settlement rows (operator can infer
            # from prior rows). Alternative: walk back the raw_fills to
            # find the last non-resolution side. Keeping simple for v1.
            state = ""
            condition = "Won" if fill["is_win"] else "Lost"
        elif fill["side"] == "Buy":
            state = "Bought"
            condition = "—"  # Order-type data gap; see PM-D6.
        elif fill["side"] == "Sell":
            state = "Sold"
            condition = "—"
        else:
            continue

        recent_trades.append({
            "player": backed_player,
            "time_short": fill_local.strftime("%-I:%M %p"),
            "time_sort": fill["utc_dt"].timestamp() if fill.get("utc_dt") else 0,
            "state": state,
            "state_class": state.lower(),
            "condition": condition,
            "condition_class": condition.lower() if condition in ("Won", "Lost") else "",
            "rate_cents": int(round(fill["price"] * 100)),
            "rate_dollars": fill["price"],
            "qty": int(round(fill["shares"])),
            "amount_dollars": fill["cash_flow"],
            "amount_class": "positive" if fill["cash_flow"] > 0 else ("negative" if fill["cash_flow"] < 0 else ""),
        })

# Sort newest-first
recent_trades.sort(key=lambda r: r["time_sort"], reverse=True)
```

Pass `recent_trades` into the template context.

**Note on data source:** `wide_summary` already carries the per-contract `raw_fills` lists (built in `_aggregate_contracts`). The flatten + filter + sort is pure derivation; no new API calls.

**Note on `open_contracts`:** if the existing `summarize_rows` doesn't expose a separate `open_contracts` key (current code only emits `closed_contracts`), the iteration above will need to walk `wide_summary["all_contracts"]` (or whatever holds in-progress positions). Verify at build time. The fallback is to iterate every row in `wide_rows` directly and skip duplicate fills via a `(utc_dt, side, price, shares)` tuple set.

### Step 2 — Backend: rate display for settlements

A settlement fill has `price` of 1.0 (full payoff) or 0.0 (wipeout). The spec says rate column shows "$1.00" / "$0.00" for these (matching the existing convention in the closed-contracts Entry → Exit column). Trivial branch in the template — see Step 3.

### Step 3 — Frontend: template changes

In `templates/trading.html`:

**Header changes:**

```diff
   <div class="t-header">
     <div>
-      <span class="t-title">Trading</span>
+      <span class="t-title">Trading Performance</span>
       <div class="t-date-selector">
         …
       </div>
     </div>
+    <div class="t-header-right">
+      <a href="/" class="t-live-link" target="_blank" rel="noopener">Live Tennis</a>
+      <button class="t-refresh-btn" type="button" title="Refresh"
+              onclick="window.location.reload()">
+        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor"
+             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
+          <path d="M14 8a6 6 0 1 1-1.76-4.24"/>
+          <polyline points="14 2 14 6 10 6"/>
+        </svg>
+      </button>
+    </div>
   </div>
```

**Recent trades section (new, after closed contracts):**

```html
{% if recent_trades %}
<div class="t-recent-section">
  <div class="t-table-title">
    Recent trades
    <span class="t-table-hint">today's executed transactions, newest first</span>
  </div>
  <div class="t-table">
    <div class="t-recent-table-grid t-recent-head">
      <div class="t-recent-th">Player</div>
      <div class="t-recent-th">Time</div>
      <div class="t-recent-th">State</div>
      <div class="t-recent-th">Condition</div>
      <div class="t-recent-th t-recent-th-rate">Rate</div>
      <div class="t-recent-th t-recent-th-qty">Qty</div>
      <div class="t-recent-th t-recent-th-amount">Amount</div>
    </div>
    {% for t in recent_trades %}
    <div class="t-recent-table-grid t-recent-row">
      <div class="t-recent-player">{{ t.player }}</div>
      <div class="t-recent-time">{{ t.time_short }}</div>
      <div class="t-recent-state {{ t.state_class }}">{{ t.state }}</div>
      <div class="t-recent-condition {{ t.condition_class }}">{{ t.condition }}</div>
      <div class="t-recent-rate">
        {% if t.rate_dollars >= 1.0 %}${{ '%.2f'|format(t.rate_dollars) }}
        {% elif t.rate_dollars == 0.0 %}$0.00
        {% else %}{{ t.rate_cents }}¢{% endif %}
      </div>
      <div class="t-recent-qty">{{ t.qty }}</div>
      <div class="t-recent-amount {{ t.amount_class }}">
        {% if t.amount_dollars > 0 %}+${{ '%.2f'|format(t.amount_dollars) }}
        {% elif t.amount_dollars < 0 %}−${{ '%.2f'|format(-t.amount_dollars) }}
        {% else %}$0.00{% endif %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}
```

**Footer collapse:**

```diff
-  <div class="t-asof">As of {{ as_of }}</div>
-
-  <div class="t-footer">
-    <span>Trading v0.5.1</span>
-    <span>·</span>
-    <span>Refresh page for current data</span>
-  </div>
+  <div class="t-footer-line">
+    As of {{ as_of }}
+    <span class="sep">·</span>
+    Trading v0.8.4
+  </div>
```

The `as_of` variable in the route uses `%I:%M:%S %p %Z` today; change to `%-I:%M %p %Z` for the new format (drops seconds, drops leading zero on hour).

### Step 4 — Frontend: CSS additions

In `static/trading.css`, add (after the existing footer rules):

```css
/* v0.8.4: header right-side cluster — Live Tennis link + refresh button */
.t-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.t-live-link {
  font-size: 13px;
  color: var(--text-tertiary);
  text-decoration: none;
  border-bottom: 1px dotted var(--text-tertiary);
  padding-bottom: 1px;
}
.t-live-link:hover {
  color: var(--text-primary);
  border-bottom-color: var(--text-primary);
}
.t-refresh-btn {
  background: var(--bg-row-header);
  border: 0.5px solid var(--border-tertiary);
  border-radius: 999px;
  cursor: pointer;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  color: var(--text-secondary);
  transition: background 100ms ease, color 100ms ease;
}
.t-refresh-btn:hover {
  background: #ebebe6;
  color: var(--text-primary);
}
.t-refresh-btn svg { width: 13px; height: 13px; }

/* v0.8.4: Recent trades section — flat per-fill row list */
.t-recent-section { margin-bottom: 16px; }
.t-recent-table-grid {
  display: grid;
  grid-template-columns: minmax(0,1.4fr) 70px 65px 70px 50px 50px 80px;
  gap: 8px;
  padding: 10px 12px;
  align-items: center;
}
.t-recent-head {
  background: var(--bg-row-header);
  border-bottom: 0.5px solid var(--border-tertiary);
}
.t-recent-row {
  border-bottom: 0.5px solid var(--border-tertiary);
  font-size: 13px;
}
.t-recent-row:last-child { border-bottom: none; }
.t-recent-th {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.t-recent-th-rate, .t-recent-th-qty, .t-recent-th-amount { text-align: right; }
.t-recent-player { font-weight: 500; }
.t-recent-time { color: var(--text-secondary); font-size: 12px; }
.t-recent-state { color: var(--text-secondary); }
.t-recent-state.bought { color: var(--text-primary); }
.t-recent-state.sold { color: var(--text-primary); }
.t-recent-condition { color: var(--text-secondary); font-size: 12px; }
.t-recent-condition.won { color: var(--text-positive); font-weight: 500; }
.t-recent-condition.lost { color: var(--text-negative); font-weight: 500; }
.t-recent-rate, .t-recent-qty, .t-recent-amount {
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.t-recent-amount.positive { color: var(--text-positive); font-weight: 500; }
.t-recent-amount.negative { color: var(--text-negative); font-weight: 500; }

/* v0.8.4: footer collapsed to single line */
.t-footer-line {
  text-align: center;
  font-size: 12px;
  color: var(--text-tertiary);
  padding-top: 12px;
  border-top: 0.5px solid var(--border-tertiary);
}
.t-footer-line .sep { margin: 0 6px; color: var(--text-tertiary); }
```

The pre-existing `.t-asof` and `.t-footer` rules can stay defined (harmless if unused) or be removed.

### Step 5 — Mobile

Existing `@media (max-width: 640px)` block needs an addition for the new grid:

```css
@media (max-width: 640px) {
  /* …existing rules… */

  /* Recent trades grid — narrow Player col, drop Condition or Time
     on smallest widths. v0.8.4 first pass keeps all columns; will
     iterate if operator surfaces a mobile-readability issue. */
  .t-recent-table-grid {
    grid-template-columns: minmax(0,1fr) 60px 55px 60px 45px 40px 70px;
    gap: 4px;
    padding: 8px 10px;
    font-size: 12px;
  }
  .t-recent-player { font-size: 12px; }
}
```

## Acceptance criteria

1. Page title reads "Trading Performance" (not "Trading").
2. Header right cluster contains a Live Tennis text link and a refresh icon button.
3. Live Tennis link opens `/` in a new tab; styled as quiet text link (tertiary, dotted underline; lifts on hover).
4. Refresh button is grey, pill-shaped, with a circular-arrow icon. Click triggers `window.location.reload()`.
5. Footer is one line: `As of HH:MM AM/PM TZ · Trading v0.8.4` — no "Refresh page for current data" copy.
6. As-of time format is `HH:MM AM/PM TZ` (no seconds, no leading zero on hour).
7. New "Recent trades" section appears below "Closed contracts".
8. Recent trades shows one row per executed transaction. No consolidation.
9. Sort order: newest at top.
10. Date scope: the page's currently-displayed date (today by default; respects `?date=` param).
11. Resting limit orders that have NOT filled do NOT appear.
12. State column shows `Bought` / `Sold` for fill rows; blank for settlement rows.
13. Condition column shows `Won` (green) / `Lost` (red) on settlement rows; `—` on fill rows (until order-type gap is closed — see "Order-type data gap" above).
14. Rate column shows cents (e.g., `45¢`) for fill rows; `$1.00` / `$0.00` on settlement rows.
15. Qty is integer.
16. Amount is signed dollars: green on positive (cash in), red on negative (cash out).
17. Empty section: if zero recent trades for the date, the section is suppressed (matches existing pattern of hiding empty Closed Contracts).
18. Mobile (≤640px): all columns still visible at smaller font; readable without horizontal scroll on a 360px-wide screen.
19. No regression on existing closed-contracts table behavior, P&L card, stats row, or date selector.

## Rollback

The changes touch:
- `templates/trading.html` (header, footer, new section)
- `static/trading.css` (new rules; no removal of existing rules)
- `src/main.py` (trading_page route — `recent_trades` derivation + `as_of` format change)

Independent rollback per change:

- **Title only:** revert `.t-title` text.
- **Live Tennis link / refresh button:** remove `.t-header-right` block from template; CSS rules can stay unreferenced.
- **Recent trades:** remove `{% if recent_trades %}…{% endif %}` block from template and `recent_trades` derivation from main.py. CSS rules harmless.
- **Footer collapse:** restore `.t-asof` div + `.t-footer` block; revert `as_of` format string.
- **Whole bundle:** redeploy the prior tarball.

No backend logic changes beyond `trading_page` derivation + as-of format. No schema, no worker logic, no data file format changes.

## Open questions

1. **Order-type data source.** The Market/Limit Condition column needs a data source. v1 ships with `—` for fill rows. Resolution requires either: (a) parse a different Polymarket endpoint that exposes order_type, or (b) cross-reference the orders-history log to label fills that match a previously-resting limit. **Operator decision needed before order-type wiring ships.**

2. **Long-day pagination.** Days with many fills (50+ rows) make the section tall. v1 renders all rows; if operator surfaces a "too long" issue, paginate at 30 rows with "show all" toggle.

3. **Cross-day visibility for limit-order fills.** A limit order placed yesterday that fills today appears on today's Recent trades correctly (matches existing cross-day lookback semantics). No extra work; flagged for awareness.

4. **Recent trades on yesterday/custom-date views.** The section follows the date selector — viewing "Yesterday" shows yesterday's recent trades. Confirmed correct by the `display_date` filter in the derivation.

## Cross-references

- **PM-D5-Now-Price-From-Opposing-Side.md** — sister design doc for the prior shipment (v0.8.3).
- **PM-D3-trading-diary-feature-2026-05-04.md** — designed-but-not-built feature; the diary's trade-level capture would attach annotations to these same Recent Trades rows.
- **trades_csv.py `_combine_fills()` and `_aggregate_contracts()`** — existing infrastructure that builds the `raw_fills` list this section iterates.
- **Trading v0.5.1** — prior shipment; this is v0.8.4 (version aligned with the live dashboard's current numbering).
