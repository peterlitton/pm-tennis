# Working log — 2026-05-04 late evening — v0.6.13 PRICEDIAG-REST

**Status:** Diagnostic-only ship. Adds REST-side per-slug one-shot logger. No behavior change.
**Tarball:** `pm-dashboard-v0.6.13-pricediag-rest.tar.gz`
**Bug class:** Polymarket prices not summing to plausible band on the moneyline pair (sum < 95¢ where ~100-110¢ would be healthy).

## Discovery progression

### Initial trigger (earlier same evening)

During PM-D.3 design conversation, operator surfaced live Bai vs Lu match (event_key 12124183, WTA 125 Jiujiang qualifier). Dashboard showed Bai 70¢ + Lu 4¢ = 74¢. Order book screenshots from Polymarket app confirmed real market prices were Bai 69-70¢ / Lu 31-32¢ with healthy 1¢ spreads on both sides — well-functioning two-sided book. Dashboard reading some kind of stuck/stale value on Lu side.

### v0.6.12 PRICEDIAG-WS deployed

Tarball shipped earlier this session. Added two per-slug one-shot loggers in `polymarket_worker.py`:
- `[PRICEDIAG] market_data slug=X (one-shot) payload=...`
- `[PRICEDIAG] trade slug=X (one-shot) payload=...`

Operator deployed. Logs captured 60+ raw WS market_data payloads after deploy.

### What v0.6.12 logs taught us

1. **WS payloads contain only YES-side book data per slug.** Each WS market_data frame has `bids`, `offers`, `stats`, `lastPriceSample` for one slug — not paired Yes/No prices.

2. **Path A in `_extract_prices_from_market_data` never fires from WS.** Path A reads `marketSides[]` (the REST-style schema). None of the captured WS payloads contained `marketSides`. Path A was speculative when written; the empirical answer is "WS doesn't carry it."

3. **Path B is the only active path on WS frames.** It extracts best_bid/best_ask from bids/offers, applies a 5¢ spread guard, and writes ONLY `side_a_cents`. Side_b stays REST-owned by architecture.

4. **The 4¢ value's origin was NOT identified from WS payloads alone.** Lajovic/Choinski's WS payload (mid-evening reproduction of the bug) showed best_bid=9¢, best_ask=10¢, healthy 1¢ spread. Stats also showed `lowPx=4¢` — the session's daily low — which suggests a single bad print at 4¢ earlier in the day got "stuck" somewhere in the pipeline. But the WS payload itself doesn't tell us which stage of the pipeline locked onto 4¢.

5. **Pattern across affected matches:** all live, all Asian Challenger / qualifier tier, all featuring one-sided dynamics with one player far ahead. Most other live matches summed cleanly (typical sum 100-105¢). Three matches with the bug all summed below 100¢.

### What v0.6.12 did NOT settle

The initial hypothesis going into v0.6.12 was: "Path B's one-sided extraction is causing side_b to go stale, and the wrong 4¢ comes from REST." That hypothesis was an inference, not a finding.

After reading v0.6.12 logs we cannot confirm:
- Whether REST is actually returning the wrong value for side_b
- Whether the resolver merge logic is preserving stale state across updates
- Whether the side_a/side_b → p1/p2 mapping has a failure mode (e.g., 4¢ being correct for one side but rendered against the wrong player)
- Whether `lastPriceSample.shortPx` (visible in WS payloads but not currently extracted) is actually the No-side price we should be reading

To trace any of these requires data we don't have yet: the actual REST payload for an affected match. v0.6.13 captures that data.

### Operator-rejected approach: derive side_b from side_a

I (Claude) proposed deriving side_b as `100 - side_a_cents` to eliminate the failure class. Operator pushed back: real markets in volatile periods have spreads producing sum >100¢, sometimes 110-120¢. Forcing 100 by construction would erase the volatility signal that operator trades on. The proposal would have been a workaround, not a fix.

Operator direction: "I'm not going to start building work arounds or 'solutions' that aren't solutions." Diagnostic-first.

## What this ship does

Adds **per-slug one-shot REST events-payload logger** in `_extract_moneyline_with_prices`. Mirrors v0.6.12's WS logger pattern.

- Fires once per slug per process lifetime (memory bounded at active-slug count, typically <200)
- Logs the **full event JSON** (not just the market block) — captures `seriesSlug`, `startDate`, all per-event metadata that may explain stale price reads
- Tag: `[PRICEDIAG-REST]`
- Suppressed forever after first hit per slug

## Files changed

- `src/polymarket_worker.py`:
  - One new global: `_per_slug_rest_logged: dict[str, bool]`
  - One new log block in `_extract_moneyline_with_prices` after slug is validated
  - ~20 lines including comments
- `templates/dashboard.html` — footer v0.6.12 → v0.6.13
- `docs/parked-items.md` — Polymarket price extraction wrong-field bug entry rewritten to reflect actual findings (initial hypothesis flagged as guess, not finding; six hypotheses listed; diagnostic plan documented; closure criterion tightened)

## Files NOT changed

- `_extract_prices_from_market_data` — untouched
- `_extract_moneyline_with_prices` field reads — untouched (we still read `marketSides[1].quote.value` for side_b; we just additionally log the raw payload)
- Resolver merge logic — untouched
- Side mapping logic — untouched

## Test plan after deploy

1. Confirm v0.6.13 footer renders
2. Wait for next live match window with broken sums (any p1+p2 sum below 95¢)
3. Pull Render logs, grep for `[PRICEDIAG-REST]` to find that slug's REST payload
4. Pull `[PRICEDIAG]` lines (v0.6.12) for the same slug — match WS payload
5. Establish healthy-match baseline: pull a `[PRICEDIAG-REST]` for a known-good match (sum ~100), compare to the broken one
6. Trace fields: which REST field corresponds to the displayed wrong price? what does WS show for the same fields at the same time?
7. Audit the resolver path: `polymarket_worker._discovery_loop` → `slug_prices` updates → resolver → snapshot → frontend render. Identify the stage where the wrong value is locked in.

## Risk assessment

Zero behavior change. One extra dict lookup per discovery iteration per slug (constant time). One INFO log line per slug, suppressed forever after first hit. Module compiles cleanly under Python 3.12.

Diagnostic logger fires before the marketSides/sides validation — meaning we capture the payload even if the event would otherwise be skipped (multi-outcome, missing players, etc.). That's deliberate: a payload that would be skipped is exactly the kind we want visibility into.

## Open question — log volume

Each event in the REST payload is moderately large (markets, marketSides, players, prices, dates). At ~100 active slugs and one log per slug per process lifetime, we expect ~100 large INFO lines after each deploy. Render's log retention should handle this without issue. If log volume becomes a problem in subsequent ships, can switch to `log.debug` with INFO-level summary instead of full payload.

## Cross-references

- `log/working_log_entry_2026-05-04-pricediag.md` — v0.6.12 ship (initial diagnosis, now superseded by this entry)
- `docs/parked-items.md` → "Polymarket price extraction wrong-field bug" — full state of the investigation
- `src/polymarket_worker.py` — three diagnostic loggers now: `_per_slug_md_logged`, `_per_slug_trade_logged`, `_per_slug_rest_logged`
- Latency-validation Finding 3 (empirical-probe-first discipline) — the discipline this investigation follows. Original finding came out of a similar bug class: assumed schema differed from actual.
