# PM-D.5 — "now" price on the OPEN row: source from opposing side

**Status:** Specification locked, build pending
**Author:** PM-D.5 with operator (Peter)
**Date:** 2026-05-06
**Affects:** OPEN sub-row rendering on the production dashboard
**Related:** v0.8.0 cutover (Polymarket Global midpoint feed) — see `docs/PM-Tennis-Pricing-Architecture-Handoff.md`

---

## Background

The dashboard's OPEN sub-row format is:

```
OPEN  200 sh @ 45¢ → now 52¢   +$14.00   +15.6%   38m
```

The value rendered after `now` is the displayed current price of the player the operator holds a position on. From the original spec onward, this value has never been calculated correctly. The operator noticed at original spec time but did not push back; the issue stayed unresolved through every version since. Today's task is to fix the calculation.

## The fix

The `now` price for the player the operator holds shall be derived from the OPPOSING player's displayed market price:

```
now_price_for_held_player = 1 − displayed_market_price_of_opposing_player
```

Worked in cents:

```
now_cents = 100 − opposing_side_displayed_cents
```

### Why this rule (operator's reasoning)

The operator validates the dashboard against the iPhone Polymarket app. The iPhone shows one number per player. When the operator holds Player A and exits, the price they realize is bound by what the market is willing to pay on the opposing token (Player B). Sourcing `now` for Player A from `(1 − Player B's displayed price)` gives the operator a single number that correctly reflects "what would I get if I exited right now," tied directly to the same opposing-side number the iPhone shows.

This is the operator-locked rule. It supersedes any prior calculation. Do not re-derive it.

### Examples

```
Operator holds Sinner. Opposing player Alcaraz displays 38¢.
  Sinner's now = 100 − 38 = 62¢

Operator holds Swiatek. Opposing player Sabalenka displays 55¢.
  Swiatek's now = 100 − 55 = 45¢

Operator holds Djokovic. Opposing player Medvedev displays 22¢.
  Djokovic's now = 100 − 22 = 78¢
```

## Implementation instructions

If you are handed this cold, follow these steps in order. Do not skip steps. Do not reinterpret the rule.

### Step 1 — Locate the rendering call site

File: `static/dashboard.js`. Function: `positionSubRow`. Approximately line 442. The call site that invokes it from `renderRow` passes `m.p1_price_cents` or `m.p2_price_cents` as the `currentPriceCents` argument:

```javascript
const p1Pos = positionSubRow(m.p1_position, m.p1.name, m.p1_price_cents);
const p2Pos = positionSubRow(m.p2_position, m.p2.name, m.p2_price_cents);
```

This is the wrong source. The argument needs to come from the OPPOSING side. The fix is at the call site, not inside `positionSubRow` — `positionSubRow` itself is just rendering whatever `currentPriceCents` it is handed, and that contract should not change.

### Step 2 — Change the source side at the call site

The rule is symmetric:

- For Player 1's OPEN row, pass `derive_now_cents(m.p2_price_cents)`
- For Player 2's OPEN row, pass `derive_now_cents(m.p1_price_cents)`

Where:

```javascript
function deriveNowCents(opposingCents) {
  if (opposingCents == null) return null;
  return 100 - opposingCents;
}
```

The `null` guard is required: when one side has no displayed price (rare, transient on the Polymarket Global feed when only one token's book has populated), the OPEN row should fall back to rendering `—` rather than `100¢`. The downstream `pricePillHtml` already handles `null` correctly.

Final form at the call site:

```javascript
const p1NowCents = deriveNowCents(m.p2_price_cents);
const p2NowCents = deriveNowCents(m.p1_price_cents);
const p1Pos = positionSubRow(m.p1_position, m.p1.name, p1NowCents);
const p2Pos = positionSubRow(m.p2_position, m.p2.name, p2NowCents);
```

### Step 3 — Do NOT change the price source feeding the match-row prices

The match-row's price columns (the per-side prices shown next to each player's name on the live match line) continue to display `m.p1_price_cents` and `m.p2_price_cents` directly. Those are the values the operator validates against the iPhone for general "what's the market saying" reading, and they should remain as they are. ONLY the `now` price on the OPEN sub-row is derived from the opposing side. Confirm this distinction with the operator before deviating.

### Step 4 — Update P&L computation in lockstep

`positionSubRow` computes `pnlCents = cashValue - cost` from server-side fields, NOT from `currentPriceCents`. Verify by reading the function: `cashValue` comes from `position.cash_value_cents`, which is computed server-side in `polymarket_worker._resolver_iteration` from the position record. The displayed `now` price is purely visual.

This means: changing the displayed `now` price as described does NOT change the displayed P&L. The P&L will still reflect the server's mark-to-market using whatever the server computes. **If the operator expects the P&L to also use the `1 − opposing` rule, that is a separate change at the resolver level (server-side) and must be discussed with the operator before implementing.** Do not assume.

### Step 5 — Smoke test the four cases

After deploy, eyeball these four cases on the production dashboard against the iPhone:

1. Match where the operator holds Player 1, both prices populated. P1's `now` should equal 100 minus P2's match-row price.
2. Match where the operator holds Player 2, both prices populated. P2's `now` should equal 100 minus P1's match-row price.
3. Match where the operator holds positions on BOTH sides (rare but possible: hedged or accidental). Both OPEN rows render with the cross-derivation; sums of the two `now` prices should be 100 ± rounding.
4. Match where one side's price is briefly `null` (one-sided book). The OPEN row for the player whose `now` derives from the missing side should render `—`, not crash, not show `100¢`.

### Step 6 — Document the rule in code

Add a comment block above the `deriveNowCents` definition that captures the rule in operator's language. Suggested wording:

```javascript
// The "now" price on the OPEN row is derived from the OPPOSING player's
// displayed market price: now_for_held_player = 1 − opposing_displayed.
// This matches the price the operator would realize on exit, since
// exiting a long position on Player A means selling at whatever the
// market is paying on Player B's token. Operator-locked rule, validated
// against iPhone Polymarket app. See PM-D5-Now-Price-From-Opposing-Side.md.
```

The comment is the contract. If a future developer is tempted to "fix" this back to a same-side source, the comment must be enough to stop them.

## What this does NOT change

- Match-row per-side prices (still source-side display)
- P&L dollar amount (still server-computed from positions data)
- P&L percent (derived from dollar P&L)
- Time-held display
- COND row prices (resting limit orders display their own target price, not a derived `now`)
- Entry price on the OPEN row (still `cost / shares` from the position record)
- The shape of `state.matches[*].p{1,2}_price_cents` — no schema change

## What this DOES change

- One field on one sub-row in the dashboard frontend.

## Acceptance criteria

1. OPEN row's `now` value, for any match where the operator has an open position, equals `100 − opposing_match_row_price` to the cent.
2. When opposing price is null, OPEN row shows `—` for `now`.
3. Match-row per-side prices are unchanged.
4. P&L numbers on the OPEN row are unchanged from before this fix (still server-computed, still mark-to-market via the existing path).
5. No console errors, no layout shift, no row breaking.
6. Comment block from Step 6 is present in `static/dashboard.js`.

## Rollback

The change is one call site in `static/dashboard.js` plus one helper function. Rollback is reverting the file. No backend changes, no schema changes, no migrations.
