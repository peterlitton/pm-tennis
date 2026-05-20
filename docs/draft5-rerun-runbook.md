# Draft 5 Re-run — Operations Guide

**Author:** PM-D.7
**Status:** Revised 2026-05-19 after the first re-run produced its report
**Audience:** The next Claude tasked with producing the periodic re-run of Draft 5
**Companion docs:** `Polymarket-Tennis-Analysis-Draft5.md`, `docs/trade-data-semantics.md`, `docs/Period-Based-Contract-Reporting-Concept.md`, `docs/analysis-2026-05-13-resolutions-readme.md`

---

## Objective

Produce a re-run of `Polymarket-Tennis-Analysis-Draft5.md` on the operator's current trade history. Tennis only. Same eight findings. Same report structure. New numbers.

The deliverable is a markdown report in the same shape as Draft 5: executive summary, premise, scope/exclusions, methodology, findings, honest limitations, what the data can support, where the opportunity lives, what the data cannot tell us.

The strategic purpose — measuring the dashboard's effect on operator performance against the original Draft 5 baseline — is documented elsewhere (the PM-D.6 handoff, the onboarding doc, the concept docs). This runbook is operations only.

---

## Reading order before you start

1. **`Polymarket-Tennis-Analysis-Draft5.md`** — the founding analysis. Cover to cover. Know its eight findings, its honest-limits framing, its tone. You're recreating *this document* with new numbers.
2. **`docs/trade-data-semantics.md`** — the data model. Most of the wrong turns previous sessions made were avoidable by reading this first.
3. **`docs/Period-Based-Contract-Reporting-Concept.md`** — the rule that "a contract is reported on the day it closes." Determines what counts as in-scope.
4. **This runbook** — the operations.

What you do **not** need to read:

- The Polymarket Activities API specs
- The `attribute_trades.py` source, the `/var/data/trade_log/*.jsonl` file format, or the `polymarket_worker.py` slug logic. These are part of the live dashboard's data pipeline. They are not the source for this analysis.
- `analysis/fetch_resolutions.py` and `analysis/open_only_positions.json`. These were a one-off when resolutions were thought to be unreachable. They're not the path. (After resolutions were verified to be in `/reports/today.csv`, these files become deletable cleanup.)

---

## The canonical data source

`/reports/today.csv` on the production dashboard. Single endpoint, single fetch, range-parameterized.

```
GET https://pm-dashboard-o71w.onrender.com/reports/today.csv
  ?from=YYYY-MM-DD
  &to=YYYY-MM-DD
  &tz=America/Chicago
  &token=<REPORTS_TOKEN>
```

- `from` / `to` are inclusive, in the timezone you specify.
- `tz` should be `America/Chicago` (the operator's location). All date-based filtering happens in this timezone.
- `token` comes from the operator. It's the same token used for the `/trading` UI. Do not hardcode it. Ask, paste, throw away after the session.
- A 40-day window returns ~1 MB / ~3,500 rows in ~15 seconds. No need to chunk.

The CSV is the same data the `/trading` page renders. The page is the human-readable view; the CSV is the machine-readable one. **Treat the CSV as ground truth for cash flow, contract grouping, and resolution outcomes.** The pre-computed columns (`Backed Player`, `Cash Flow ($)`, `Lifecycle`, `Held Duration (hours)`, `Times Touched`, `Pending`) already implement the rules from `trade-data-semantics.md` and `Period-Based-Contract-Reporting-Concept.md`. Don't redo them.

### Fields you actually need

From the ~30 columns in the CSV, the analysis lives in these:

| Field | Use |
|---|---|
| `Transact Time (Local)` | Date/time bucketing; the `from`/`to` filter is already applied |
| `Tour` | `ATP` / `WTA` for tennis; filter to these |
| `Market Slug` | Contract grouping (with Backed Player + LONG/SHORT) |
| `Backed Player` | Operator's bought player. Use this, not `Outcome (Player)` |
| `Intent` | The eight row types — see the trap list below |
| `Lifecycle` | `Open` / `Add` / `Reduce` / `Close` / `Settled` — the canonical state-change marker |
| `Fill Price (cents)` | Entry/exit prices for stake-bucket and price-extremity analyses |
| `Shares` | Server-computed share count, correct for both LONG and SHORT |
| `Cost ($)` | Capital deployed on this row |
| `Cash Flow ($)` | Signed cash flow: negative for buys, positive for sells and $1 settlements, zero for $0 settlements. **Sum this across a contract for true cash P&L.** |
| `Held Duration (hours)` | Pre-computed on terminal rows |
| `Times Touched` | Pre-computed; the buy+sell count Draft 5 used for "trade count per swing" |
| `Pending` | `TRUE` for rows belonging to genuinely-still-open contracts; exclude these |

The `Momentum at Fill`, `Edge Badge at Fill`, and `Fair Price at Fill` columns are Direction X indicator fields. They're not part of Draft 5 (which had none of those). They're empty for older records and populated for newer ones. Available for Direction X work; out of scope for this re-run unless the operator asks.

---

## The procedure

### 1. Confirm the window with the operator

Default for the periodic re-run is rolling 40 days through yesterday, matching the original Draft 5's "8 days ending yesterday" framing. The operator may specify a different window (a particular tournament, a comparison period, etc.). Don't pick a window without confirming.

### 2. Get the auth token

The operator will paste it. Don't store it. Use it for the fetch and discard.

### 3. Fetch the CSV

One `curl` to `/reports/today.csv` with the range. Save to `/home/claude/draft5-rerun/`.

If the fetch fails: check the token first, then check the date format (must be `YYYY-MM-DD`), then check whether you used `from` and `to` (not `from_date` / `to_date` — the route accepts both via alias but the URL is `from`/`to`).

### 4. Apply scope filters in order

The order matters because each filter narrows the set the next filter inspects.

1. **Tour filter.** Keep rows where `Tour ∈ {ATP, WTA}`. The CSV includes other sports (NHL, NBA, MLB, MLS, etc.) — exclude them. A 40-day window typically has ~10% non-tennis rows.
2. **STENAP-TRISCH exclusion.** Remove all rows where `Market Slug` contains `stenap-trisch`. This is the Draft 5 market-making match — Peter has explicitly excluded it from every analysis since. Verify with the operator if you suspect a similar market-making session exists in your window.
3. **In-flight contracts.** Per the period-based reporting rule, contracts without a terminal event in the report window are invisible to reporting. Two filter conditions are both needed:
   - **a.** Remove all rows belonging to contracts with `Pending=TRUE` on any of their rows.
   - **b.** Remove all rows belonging to contracts with no `Lifecycle ∈ {Close, Settled}` event anywhere in the window. The `Pending` flag reflects activity completeness against the fetch cutoff, *not* against your report window — a contract opened May 17 in a window ending May 18 may settle May 19 and not be flagged Pending. You still need to exclude it from this report; it'll close in a future window's report.
   Expect ~20–30 contracts excluded by these two conditions combined in a 40-day window.
4. **Other operator-specified exclusions.** Ask before running. Past sessions have had to handle ad-hoc exclusions (specific tournaments, specific players being tested by the operator, etc.).

### 5. Group into contracts

A contract is `(Backed Player, Market Slug, LONG-or-SHORT)`. The LONG/SHORT axis matters — the same player on the same match can produce two separate contracts on different sides of the book. Read LONG/SHORT from the `Intent` suffix (`_LONG` or `_SHORT`).

For each contract, aggregate:

- **Buys** (`Lifecycle ∈ {Open, Add}`): rows, total cost (sum of `Cost ($)`)
- **Sells** (`Lifecycle ∈ {Reduce, Close}`): rows, total proceeds (sum of `Cost ($)` — note: for sells, `Cost ($)` is the proceeds amount, sign reflected in `Cash Flow ($)`)
- **Settlement** (`Lifecycle = Settled`): present or not; if present, `Intent` carries `WIN` or `LOSS`
- **Cash P&L** = sum of `Cash Flow ($)` across all rows of the contract. **Always use this; never sum `realized_pnl_dollars` from the underlying trade log, which is unreliable for SHORT.**
- **Win/Loss** = sign of cash P&L (positive → win, non-positive → loss). Note this differs from Draft 5's framing slightly: Draft 5 had explicit Won-via-exit and Lost-via-exit categories. In this dataset those are equivalent to "swing closed with positive cash P&L" and "swing closed with negative cash P&L" respectively.
- **Category:** *Swing* if the contract has any sell or partial close (`Lifecycle ∈ {Reduce, Close}` present); *Hold* if the contract has only `Open`/`Add` rows followed by `Settled`. The partial-close-then-Settled pattern is common (~118 contracts in the 40-day run had both `Close`/`Reduce` and `Settled`) — Draft 5 counted these as swings since active management was present, and this re-run follows the same rule.

### 6. Compute the eight findings

In Draft 5's order. The fields you need are listed; the methodology is in Draft 5's own Methodology section.

1. **Overall** — count, total wagered, net P&L, ROI, win rate, payoff-asymmetry ratio (mean winning P&L ÷ mean |losing P&L|).
2. **Swing vs. Hold** — same metrics, partitioned by category. The 22.6-point swing/hold win-rate gap was Draft 5's strongest signal; this is the headline comparison.
3. **Payoff asymmetry** — Draft 5's 1.75× figure. Mean winning contract P&L ÷ mean losing contract P&L.
4. **Trade-count per swing** — `Times Touched` distribution on swing contracts. Draft 5 found 7+ trade swings produced 28.6% win rate / −9.7% ROI. Report the win rate and ROI at each trade-count bucket (1–2, 3–4, 5–6, 7+).
5. **Stake-bucket analysis** — partition contracts by total wagered into Draft 5's buckets: <$25, $25–100, $100–200, $200–500, $500+. Report win rate, ROI, payoff asymmetry per bucket. The $100–200 bucket was the problem zone.
6. **Top-1 concentration** — contribution of the top single contract to total P&L. Also top-10. Draft 5 had top-1 at 61% and top-10 at 193% (meaning the other 121 contracts lost money in aggregate).
7. **Tour split** — ATP vs WTA. Same metrics on each.
8. **Time pattern** — day-of-week, time-of-day, or cumulative-time pattern. Draft 5 found 50% → 62% swing win-rate improvement across the 8-day window. Report whatever time-axis signal is present at this window's resolution.

### 7. Cross-check before writing the report

- **Cash-flow reconciliation:** sum of `Cash Flow ($)` across all in-scope rows should equal the net P&L you compute by aggregating contracts. If they differ by more than a few cents, something's wrong (most likely a Pending contract slipped through).
- **No `realized_pnl_dollars`-derived numbers.** If you find yourself using that field, you're using the wrong source.
- **Contract count parity.** Distinct contract count should roughly match `Lifecycle in {Close, Settled}` row count (each contract has exactly one terminal event, modulo the partial-close-then-settle cases).
- **Spot-check 3–5 contracts manually** against the trading-page UI. Pick a winning swing, a losing swing, a held-and-won, a held-and-lost. Verify the entry/exit/P&L/share-count match. If they don't, stop and figure out why before writing the report.

### 8. Write the report

Match Draft 5's structure and tone:

- **Executive Summary** — 4–6 sentences. Total contracts, period, net P&L, ROI, headline win rate, the one or two most important findings.
- **Premise** — why this analysis exists. Reference Draft 5 as the baseline.
- **Scope and Exclusions** — list what's included and excluded, with rationale. Always document STENAP-TRISCH exclusion. Always note non-tennis exclusion. Document any operator-specified exclusions.
- **Methodology** — data source (`/reports/today.csv`), categorization rules, cash-flow rule (always `Cash Flow ($)`, never `realized_pnl_dollars`), unresolved-contract handling (excluded per period-based reporting rule). Note that resolutions are integrated rows in the CSV, not a separate lookup.
- **Findings** — the eight, in order, with numbers and Draft-5-style interpretation.
- **Honest Limitations** — sample size, statistical-power caveats, things the data cannot prove. Draft 5's honest-limits framing is the template. Copy its tone.
- **What the Data Can Support** — actionable, durable claims.
- **Where the Opportunity Lives Going Forward** — the strategic read. Reference the concept docs (Data-Driven-Indicators, Exit-Signal-Architecture) where relevant.
- **What the Data Cannot Tell Us** — explicit list of open questions.
- **Side-by-side comparison with Draft 5.** Which patterns held (same direction, similar magnitude)? Which moved (same direction, different magnitude)? Which inverted? This is the most strategically interesting section and should be its own subsection at minimum, possibly its own section.

Save the report at `/home/claude/draft5-rerun/Polymarket-Tennis-Analysis-Re-run-YYYY-MM-DD.md`. Present it to the operator via `present_files`. Do not commit it to the repo — the operator will decide where it lives.

### 9. Cleanup

Per the operator's standing rule: trade data on a public path is real exposure. After the analysis is delivered, remind the operator to:

- Delete `static/tennis_part_aa`, `static/tennis_part_ab`, and any other `static/tennis_*` files from the operator zip directory if they exist (leftovers from prior runs).
- Discard the auth token if it was shared in chat.

If `analysis/fetch_resolutions.py` and `analysis/open_only_positions.json` are still in the repo: those were the May 13 one-off that was made obsolete by the CSV approach. They can be removed in a follow-up commit (the resolutions readme already says this).

---

## Things to know

### LONG and SHORT are routing, not bets

`Backed Player` is the operator's bought player, on every row, regardless of `Intent` suffix. The LONG/SHORT axis reflects which side of the order book the buy was routed through, not which player the operator backed. From the operator's perspective both are equivalent — same player, same exposure, just different fills. The CSV's `Cash Flow ($)` already handles both correctly; you do not need to special-case SHORT for cash-flow math.

### Resolutions are rows in the CSV

A held-to-resolution contract has a `Lifecycle = Settled` row with `Cash Flow ($)` equal to either +shares (win) or 0 (loss). Per operator rule, match resolution IS a trade — the CSV operationalizes this rule. There is no separate "resolution lookup" step. If you find yourself wanting to look up match outcomes externally to determine win/loss, you've reached for the wrong source — the answer is in the CSV.

### Pending vs. Settled

`Pending=TRUE` rows belong to contracts that have *not* reached a terminal event in the fetched window. These are the genuinely-still-open contracts. Exclude them from reporting per the period-based reporting rule.

`Lifecycle=Settled` rows are the terminal events for held-to-resolution contracts. They are *not* pending. Include them in reporting.

### Cash flow is signed; don't fight it

`Cash Flow ($)` is negative for buys (money out) and positive for sells and winning settlements (money in). Don't apply your own sign convention. Don't sum costs and proceeds separately and subtract — just sum cash flow.

### `realized_pnl_dollars` is unreliable

This field appears in the underlying trade log (`/var/data/trade_log/`) but is not exposed in the CSV. If you encounter it elsewhere: do not use it. It is computed under Polymarket's internal convention and does not match cash flows for SHORT positions. The doc `docs/trade-data-semantics.md` is explicit on this.

### The trap I fell into and you should not

I started by pulling raw fills from `/var/data/trade_log/*.jsonl` via a static-file export and tried to reconstruct the analysis from scratch. I rebuilt share derivation. I rebuilt LONG/SHORT cost reconciliation. I tried to derive contract outcomes from sibling swings and from external match-result data. None of it was necessary. The trading productivity platform (`/trading` and its backing `/reports/today.csv`) already does all of this correctly, has done so since v0.8.4, and is the canonical source.

**If you find yourself thinking "I need to derive X" or "I need to look up Y externally" — stop. The CSV probably has it.** Check the field list above first.

### Time the operator's UI runs in

The operator is in Chicago (CDT during this period, UTC−5). Always pass `tz=America/Chicago`. Day boundaries are in operator-local time. Don't bucket trades by UTC date — a 9 PM Chicago trade is the same operator-day as a 3 PM Chicago trade, even though they're on different UTC dates.

### Don't write a Python script unless you need to

The whole pipeline — fetch, filter, group, compute, write — fits in ~150 lines of Python and can be run interactively in `bash_tool`. If you spec out a reusable script, fine, but the analysis output (the markdown report) is the deliverable, not the code. Don't gold-plate the pipeline.

The first re-run (PM-D.7, 2026-05-19) was run ad-hoc, no script committed. If you find you're writing the same code patterns the third time, that's the moment to formalize a script under `analysis/`.

### Lessons from the first run

The first run (PM-D.7, 2026-05-19, 40-day window) surfaced a few practical things worth carrying forward:

- **Reconciliation should be exact, not approximate.** Sum of contract-level cash P&L should equal sum of row-level `Cash Flow ($)` to the cent. The first run reconciled to $0.0000. If yours differs by more than rounding, a contract slipped past the filter.
- **The Pending flag is necessary but not sufficient** (see filter step 3 above). The original spec for this runbook treated `Pending=TRUE` as the complete in-flight signal; the first run revealed 6 additional contracts that opened late in the window and settled after the cutoff but were not flagged Pending. Filter step 3b catches them.
- **Findings can move large and fast.** The first run found win rate moved +23 pp and payoff asymmetry inverted (1.75× → 0.76×) over 5× more contracts. The instinct may be to question the methodology when results diverge sharply from baseline; in this case the methodology was right and the operator's trading really did change shape. Trust the reconciliation; report the divergence honestly.
- **Some Draft 5 findings reversed direction.** The 7+ trade engagement signal that Draft 5 called the "operational tell of intuition failing" now correlates with *winning*, not losing. The trade-count warning indicator (parked) was justified by Draft 5's signal; if the re-run finds the signal absent or reversed, surface that explicitly — it changes the activation criteria for any indicator built on it.
- **Don't infer causation.** The re-run can show what changed; it cannot tell you why (operator improvement, instrument support, regime change, variance — likely a mixture). Be explicit about this in the report's honest-limitations section.

---

## Quick reference

| Thing | Value |
|---|---|
| Data endpoint | `https://pm-dashboard-o71w.onrender.com/reports/today.csv` |
| Auth | `?token=<REPORTS_TOKEN>` (ask operator; do not store) |
| Required params | `from=YYYY-MM-DD`, `to=YYYY-MM-DD`, `tz=America/Chicago` |
| Default window | Rolling 40 days through yesterday (confirm with operator) |
| Working directory | `/home/claude/draft5-rerun/` |
| Report output | `/home/claude/draft5-rerun/Polymarket-Tennis-Analysis-Re-run-YYYY-MM-DD.md` |
| Founding doc | `Polymarket-Tennis-Analysis-Draft5.md` (repo root) |
| Data-model doc | `docs/trade-data-semantics.md` |
| Reporting-rule doc | `docs/Period-Based-Contract-Reporting-Concept.md` |
| Filters (in order) | Tour∈{ATP,WTA}; exclude `stenap-trisch`; exclude contracts with `Pending=TRUE`; exclude contracts with no `Lifecycle∈{Close,Settled}` in window |
| Contract key | `(Backed Player, Market Slug, LONG-or-SHORT)` |
| Cash P&L | Sum of `Cash Flow ($)` across contract rows |
| Win/Loss | Sign of cash P&L |
| Swing vs Hold | Swing = has any `Lifecycle ∈ {Reduce, Close}`; Hold = only `Open`/`Add` + `Settled` |
| Never use | `realized_pnl_dollars` (unreliable for SHORT) |
| Never reach for | Raw `/var/data/trade_log/*.jsonl`, `fetch_resolutions.py`, external match-result lookups |
| Always confirm with operator | Reporting window, ad-hoc exclusions beyond STENAP-TRISCH |

---

*PM-D.7, 2026-05-19. Drafted before the first re-run; revised same-day after the first run produced its report.*
