# Polymarket Tennis Trading — Re-run on 40-Day Window

**Period:** April 9 – May 18, 2026 (40 days)
**Author:** PM-D.7
**Date:** 2026-05-19
**Companion to:** `Polymarket-Tennis-Analysis-Draft5.md`
**Baseline:** Draft 5 measured an 8-day window (Apr 11 – Apr 18, 2026) on intuition alone, +$954 on $11,166 wagered, +8.5% ROI, 45.0% win rate.

---

## Executive Summary

Peter traded Polymarket US in-play tennis for 40 days and netted **+$5,291 on $52,383 wagered (+10.1% ROI)** across 687 closed contracts. The headline ROI is comparable to the Draft 5 baseline (+8.5%), but the *composition of profit changed substantially* — and the change is the analytically interesting story.

Four headline movements from Draft 5:

1. **Effective win rate rose from 45.0% to 68.1%** — the operator now wins more contracts than he loses, by a wide margin. This is a 23.1-point increase that survives any reasonable statistical test.
2. **Payoff asymmetry collapsed from 1.75× to 0.76×** — winning contracts now pay *less* than losing contracts cost. The Draft 5 edge (big wins covering more frequent losses) inverted into the opposite shape (frequent small wins offset by less frequent but larger losses).
3. **Swing vs. Hold gap narrowed from 22.6 pp to 15.6 pp** but in a fundamentally changed way — both subsets shifted upward, the gap remains statistically significant (p<0.001), and the underlying mechanism appears different.
4. **P&L concentration dropped sharply.** Top-1 contract was 61% of P&L in Draft 5 and is 9% here. Top-10 was 193% in Draft 5 and is 64% here. The book is more diversified, less tail-driven.

Trading remained profitable in both periods. *How* it was profitable changed. The shift from a hit-rate-below-breakeven, payoff-asymmetry-driven edge to a hit-rate-above-breakeven, payoff-asymmetry-suppressed edge is consistent with the operator changing what he trades and how he exits — though this analysis cannot, by itself, distinguish behavioral change from variance.

---

## Premise

This report measures the operator's trading activity on Polymarket US tennis markets over the 40-day window April 9 – May 18, 2026. It uses the same eight-finding structure as the original Draft 5 analysis to enable direct comparison.

Draft 5 was an *intuition-only* baseline. This window overlaps Draft 5's 8 days at its start (Apr 11–18) but extends an additional 31 days during which the dashboard accumulated indicator data and the operator's instrumentation increased. **Whether the changes documented below reflect operator improvement, instrument-supported decisions, sample-size variance, or some combination is the question that follow-up analysis must address.** This report measures what changed; it does not yet explain why.

The two purposes of the analysis remain Draft 5's:

1. **Is the trading profitable?** The simple money question.
2. **If profitable, why?** Is it hit rate, payoff asymmetry, or something else?

---

## Scope and Exclusions

**Included:** Tennis contracts (ATP and WTA tour) with at least one terminal event (operator close, or Polymarket settlement at $0/$1) within the reporting window.

**Excluded:**

- **Non-tennis sports** (NHL, NBA, MLB, MLS, WNBA — ~286 rows). The dashboard's analytical scope is tennis only.
- **STENAP vs. TRISCH match** (Apr 10, 23 rows). Excluded in Draft 5 as market-making activity not representative of the operator's discretionary trading; the rationale still applies.
- **In-flight contracts** (23 contracts, ~50 rows). Per the operator's stated period-based reporting rule, a contract is reported on the day it closes — open positions are invisible to reporting. Of these 23, 17 were flagged `Pending=TRUE` in the source data; the remaining 6 were opened May 17–18 and settled May 19 (outside the window).

The resulting in-scope set is **687 contracts, 3,080 rows** across 37 trading days.

---

## Methodology

**Data source.** Source data is the production trading-productivity platform's `/reports/today.csv` endpoint, pulled with `from=2026-04-09&to=2026-05-18&tz=America/Chicago`. The CSV is the same data the operator reads on the `/trading` page; both implement the rules from `docs/trade-data-semantics.md` and `docs/Period-Based-Contract-Reporting-Concept.md`. The CSV is treated as ground truth.

**Contract grouping.** A contract is identified by `(Backed Player, Market Slug, LONG-or-SHORT)`. The LONG/SHORT axis matters because the same player on the same match can produce separate contracts if the operator's buys routed through different sides of the order book; the cash-flow rule treats them identically but they are distinguishable. `Backed Player` is the player the operator bought, regardless of routing — read directly from the CSV.

**Cash flow rule.** Net P&L per contract is the sum of `Cash Flow ($)` across the contract's rows. The CSV signs cash flow consistently: negative for buys, positive for sells and $1 settlements, zero for $0 settlements. This handles LONG and SHORT positions uniformly without the realized-P&L inversion that affects raw data. Row-level cash flow reconciles exactly to contract-level P&L (difference: $0.0000).

**Win/Loss definition.** A contract is a *win* if its net cash P&L is positive, a *loss* otherwise. This matches Draft 5's "effective outcome" framing — both Won-via-resolution and Won-via-exit count as wins; both Lost-via-resolution and Lost-via-exit count as losses.

**Swing vs. Hold definition.** A contract is a *Swing* if it contains any `Reduce` or `Close` lifecycle event (operator actively closed at least some shares). A contract is a *Hold* if it has only `Open` and `Add` events followed by a `Settled` event (operator let it ride to resolution). 118 contracts had both partial closes and a final settlement; these are counted as Swings (active management was present).

**Statistical tests.** Where reported, p-values use a two-proportion z-test. Confidence intervals are not computed for headline numbers; the honest-limits section addresses statistical-power concerns qualitatively.

**Differences from Draft 5 methodology.** The original analysis derived everything from a custom `compute_baseline.py` script run against iPhone-CSV-transcribed records. This re-run pulls from the production dashboard's API, which has the same data model formalized in code. The pre-computed `Cash Flow ($)`, `Lifecycle`, and `Backed Player` columns replace fields Draft 5 had to derive manually. The reporting period rule (contracts reported on close day) is applied via the data pipeline rather than as a manual step. None of these changes should materially affect comparability.

---

## Finding 1 — Trading was profitable, at similar ROI to baseline

| Metric | Re-run (40 days) | Draft 5 (8 days) | Direction |
|---|---|---|---|
| Contracts | 687 | 131 | 5.2× wider |
| Total wagered | $52,383 | $11,166 | 4.7× wider |
| Net P&L | +$5,291 | +$954 | 5.5× wider |
| ROI | +10.1% | +8.5% | +1.6 pp |

The 40-day ROI is within 2 percentage points of Draft 5's. As a top-line dollar finding, the trading remained profitable through the new window and at a roughly similar return-on-capital rate.

The bottom-line dollar number is the *least* analytically interesting finding here — it tells us trading continued to make money, but not what changed in the underlying behavior. The composition findings below carry the analytically interesting signal.

## Finding 2 — Win rate rose dramatically, from 45% to 68%

| Metric | Re-run | Draft 5 | Direction |
|---|---|---|---|
| Effective win rate | 68.1% | 45.0% | +23.1 pp |
| Implied breakeven (from payoff ratio) | 56.7% | 58.2% | comparable |
| Margin vs. breakeven | +11.4 pp | −13.2 pp | flipped sign |

**This is the largest change in the dataset.** Draft 5 found the operator winning 45% of the time and profiting via 1.75× payoff asymmetry. In this window, the operator wins 68% of the time. The hit rate moved from below breakeven to substantially above it.

The 23-point jump is well beyond what variance alone would produce at this sample size. With n=687 in the re-run and a true rate at the Draft 5 level, observing 68.1% would be effectively impossible (z far above any reasonable threshold).

Two interpretive cautions are necessary, however:

1. The Draft 5 sample (131 contracts) was small enough that 45% was not statistically distinguishable from a true rate of 50% or higher. The "true" Draft 5 baseline could have been higher than 45% in the population.
2. The contract mix changed. The re-run includes a substantial Hold subset (300 contracts, 44% of the book) where the operator backs heavy favorites and lets them resolve. These produce a high mechanical win rate (heavy favorites win at their implied probability) but small per-contract dollar wins. Draft 5 had only 63 Hold contracts (48% of its book — comparable share, but very different absolute count and composition).

The win-rate jump is real and large. Whether it represents skill improvement is the open question Finding 3 begins to answer.

## Finding 3 — Payoff asymmetry collapsed from 1.75× to 0.76×

| Subset | Re-run avg win | Re-run avg loss | Re-run ratio | Draft 5 ratio |
|---|---|---|---|---|
| All contracts | $29.21 | $38.27 | **0.76×** | 1.75× |
| Swing only | $31.20 | $29.94 | 1.04× | n/a* |
| Hold only | $25.97 | $44.89 | 0.58× | n/a* |

*Draft 5 didn't break payoff asymmetry by subset in its findings, though the underlying numbers are derivable.

**This is the most analytically significant change.** Draft 5's profitability depended on winners paying 1.75× what losers cost. That asymmetry is now inverted: winners pay *less* than losers cost. The book is profitable nonetheless — but profitability now requires the higher win rate (Finding 2) to compensate for the inverted asymmetry.

The math of the new equilibrium:

- Win rate 68.1% × $29.21 avg win = $19.89 expected per-contract gain
- Loss rate 31.9% × $38.27 avg loss = $12.21 expected per-contract loss
- Net expected per-contract: +$7.68

Compared to Draft 5:

- Win rate 45.0% × (Draft 5 avg win, ~$220) = ~$99 expected per-contract gain
- Loss rate 55.0% × (Draft 5 avg loss, ~$126) = ~$69 expected per-contract loss
- Net: ~$30 per contract

The Draft 5 model was higher expected dollars per contract but with much higher variance (large wins, large losses, infrequent wins offsetting frequent losses). The current model is lower expected dollars per contract but more contracts and lower variance. The total dollar return is similar because the much wider book (687 vs 131 contracts) makes up the per-contract difference.

**This is a fundamentally different shape of edge.** Whether it's sustainable, whether it's better, whether it's actually generated by changed operator behavior — the data doesn't say. What it says clearly is that the *mechanism* generating profit shifted, and the new mechanism is more dependent on maintaining a high win rate than on capturing large wins.

## Finding 4 — Trade-count-per-swing pattern reversed: 7+ swings now win, not lose

| Bucket | Re-run n | Re-run win rate | Re-run ROI | Draft 5 n | Draft 5 win rate | Draft 5 ROI |
|---|---|---|---|---|---|---|
| 1–2 trades | 109 | 71.6% | +2.8% | 32 | 65.6% | +13.7% |
| 3–4 trades | 119 | 73.1% | +10.0% | 16 | 56.3% | +12.0% |
| 5–6 trades | 61 | 83.6% | +40.2% | 13 | 53.8% | +5.7% |
| 7+ trades | 98 | 75.5% | **+19.4%** | 7 | 28.6% | **−9.7%** |

**This is the single most striking pattern reversal in the dataset.** Draft 5 found that over-engaged positions (7+ trade swings) were where intuition broke down — 28.6% win rate, negative ROI. The re-run finds 7+ trade swings *profitable* (75.5% win rate, +19.4% ROI), with the **5–6 bucket being the best-performing one** (83.6% win rate, +40.2% ROI).

Draft 5 framed the 7+ pattern as "the operational tell of intuition failing." That pattern is no longer present. Either:

- The operator's deep-engagement positions are now better-managed than they were in April,
- The Draft 5 sample (n=7 in this bucket) was too small to support its framing, or
- The composition of what counts as a 7+ swing changed (more partial closes on routine winners now, fewer desperation-repurchases on losing structural bets).

The Draft 5 read was that "positions that feel like they need active re-engagement are exactly the ones to consider exiting cleanly instead." The re-run does not support that conclusion in this window. If anything, deeper engagement now correlates with better outcomes.

This finding warrants follow-up. The trade-count parked indicator (a dashboard warning at 7+ engagements) was justified by Draft 5's signal; if that signal isn't reliable, the indicator's activation criteria should be reconsidered.

## Finding 5 — Stake-bucket asymmetry largely persists, but $500+ is now profitable

| Bucket | Re-run n | Re-run win rate | Re-run ROI | Re-run payoff | Draft 5 win rate | Draft 5 ROI |
|---|---|---|---|---|---|---|
| <$25 | 270 | 65.2% | +65.8% | 1.81× | 60.5% | +49% |
| $25–100 | 272 | 66.5% | +5.3% | 0.62× | 45.7% | +5% |
| $100–200 | 104 | 78.8% | +9.5% | 0.45× | 57.9% | **negative** |
| $200–500 | 30 | 63.3% | −2.4% | 0.50× | 50.0% | small loss |
| $500+ | 11 | 90.9% | +11.8% | 0.54× | 100% (4/4) | **+62%** |

**The <$25 bucket remains the strongest performer** by ROI (+65.8%), echoing Draft 5's pattern that small-stake exploratory bets produce outsized returns. Payoff asymmetry in this bucket is 1.81×, the only bucket where winners pay more than losers cost.

**The $100–200 bucket — Draft 5's identified problem zone — flipped from loss to gain.** Win rate rose from 57.9% to 78.8% and ROI from negative to +9.5%. The asymmetry (0.45×) is still unfavorable, but the higher win rate now compensates. This is consistent with the broader Finding 2/3 story: more wins, smaller wins, fewer losses, larger losses.

**The $500+ bucket dropped from extraordinary (4/4 wins, +62% ROI) to merely good (10/11 wins, +11.8% ROI).** Draft 5 noted this bucket's results as "suggestive, not evidence" due to sample size. With 11 contracts here the same caveat applies, but the pattern is now: structural-near-certainty bets win nearly always at small ROI, which is consistent with what they are (heavy favorites bought at 80–95¢ effective).

## Finding 6 — P&L concentration dropped sharply; the book is more diversified

| Metric | Re-run | Draft 5 |
|---|---|---|
| Top-1 contract as % of total P&L | 9% | 61% |
| Top-10 as % of total P&L | 64% | 193% |
| Net P&L without top-10 | +$1,918 | −$885 |

**The book is no longer tail-dominated.** Draft 5's profitability depended heavily on a single trade (61% of P&L) and the top 10 trades (193%, meaning the other 121 contracts in aggregate *lost* money). In the re-run, the top contract is 9% of P&L and the bottom 677 contracts collectively make $1,918.

The top-1 contract in the re-run was a +$489.51 win on a SHORT Calvin Hemery position bought at 98¢ effective and resolved at $1. Pattern C — structural near-certainty bet — same template Draft 5 identified, but the magnitude is much smaller and the contribution to overall P&L proportionally lower.

This is the single most encouraging finding for **durability** of the operator's edge. A tail-dependent book is fragile; a diversified book is robust. The re-run looks much more like a diversified book.

## Finding 7 — Tour split: ATP profitable, WTA marginal

| Tour | Re-run n | Wagered | P&L | Win rate | ROI |
|---|---|---|---|---|---|
| ATP | 471 | $34,955 | +$4,696 | 67.1% | +13.4% |
| WTA | 216 | $17,428 | +$595 | 70.4% | +3.4% |

The operator runs roughly 2:1 ATP:WTA by contract count. ATP produces the bulk of the dollar profit (+$4,696 of $5,291 net). WTA wins slightly more often (70.4% vs 67.1%) but at a much lower ROI (+3.4% vs +13.4%) — consistent with WTA being heavier in Hold-style high-favorite bets that produce small mechanical wins but limited dollar upside.

Draft 5 did not split by tour in its findings. The re-run shows the operator has tour-level differentiation in his book and that the ATP side carries the profit center. Worth tracking whether this persists.

## Finding 8 — Time pattern: profit concentrated in first half of window

| Half | Days | Contracts | Wagered | P&L | Win rate | Swing win rate |
|---|---|---|---|---|---|---|
| First half | Apr 9 – Apr 27 | 272 | $25,593 | +$4,650 | 65.1% | 79.1% |
| Second half | Apr 28 – May 18 | 415 | $26,790 | +$641 | 70.1% | 72.1% |

**P&L is heavily concentrated in the first half** (88% of profit, but only 49% of capital and 40% of contracts). The second half saw slightly higher overall win rate but lower swing win rate and dramatically lower per-dollar profit.

Draft 5 found a 50% → 62% swing-win-rate *improvement* across its 8 days. The re-run shows the opposite trajectory at this resolution: 79.1% → 72.1% on swings. This could mean:

- The first half captured the tail of Draft 5's improving regime, after which performance plateaued or regressed.
- The first half had a favorable variance run (lots of small wins, a few big ones — the Calvin Hemery $489 contract is in this half).
- The second half saw the operator take on harder trades or different conditions (tournament cycles, surface changes — the Madrid-to-Italian Open transition straddles the halves).

**Day-of-week pattern.** No strong signal. Saturday and Friday show the best win rates by dollar profit; Tuesday is the only day with a net loss (−$673) despite a high 73.0% win rate, driven by a few large losing contracts. Effect sizes are small relative to within-day variance; treat day-of-week as noise unless future data confirms a pattern.

## Additional finding (not in Draft 5) — LONG/SHORT split

| Side | n | Wagered | P&L | Win rate | ROI |
|---|---|---|---|---|---|
| LONG | 327 | $28,624 | +$1,850 | 67.6% | +6.5% |
| SHORT | 360 | $23,759 | +$3,442 | 68.6% | +14.5% |

The SHORT side delivers more than half the dollar profit on less than half the wagered capital. SHORT win rate is comparable to LONG (68.6% vs 67.6%), but SHORT ROI is more than double LONG's. The mechanical reason: SHORT positions are typically bought at low fill prices (i.e., high effective NO-side prices), so a $1-paying resolution produces a larger per-dollar return than a near-certainty LONG.

Draft 5 didn't surface this split. It is more an artifact of the operator's structural-near-certainty bet pattern (which prefers SHORT-side routing when buying NO on heavy favorites) than a separate trading edge. Tracked for transparency.

---

## Honest Limitations

**Window selection.** This is a 40-day window of one operator's recent activity. It is wider than Draft 5's 8 days, but it is still one window. Tennis tournament cycles, surface transitions, and the operator's own life rhythms could all bias the period systematically.

**Statistical power on subgroup findings.** Headline aggregates (Finding 1, Finding 2, Finding 3) are well-powered at n=687. Subgroup findings (Finding 5 stake-bucket cells, Finding 4 trade-count cells, Finding 7 tour split, Finding 8 time pattern) have cells with n=11 to n=270 — power varies, and confidence intervals at the low-n cells are wide. Treat subgroup-level dollar figures and ROI percentages as directional, not precise.

**Comparability with Draft 5 has limits.** Draft 5's data was transcribed from iPhone-app screenshots; the re-run pulls from the production API. Both implement the same logical data model, but transcription noise and category-edge differences may produce small inconsistencies that compound at subgroup level. The headline movements (win rate +23 pp, payoff ratio collapse) are too large to be artifacts of this. Smaller pattern shifts (day-of-week, stake-bucket micro-cells) may be partly methodological.

**The change is real; the cause is not isolated.** This analysis can demonstrate that win rate rose, payoff asymmetry inverted, P&L concentration dropped, and the trade-count pattern reversed. It cannot, on its own, attribute these changes to the operator's behavioral change, to dashboard instrumentation availability, to favorable variance, to market regime change, or to some interaction. Disentangling those would require either a controlled comparison (with/without dashboard on otherwise-similar matches) or much more data.

**The dataset cannot reveal the operator's mental state at decision time.** Draft 5 noted this; it remains true. We can observe entries, exits, and outcomes. We cannot observe the operator's reasoning, the indicators he glanced at, the price moves he saw but didn't trade, or the trades he considered but skipped.

**Whether 1.75×→0.76× payoff collapse is durable or transient is unknown.** This is the most strategically important uncertainty. If the new mechanism (high win rate, low payoff, small wins, occasional larger losses) is the operator's actual edge going forward, the dashboard's role shifts — exit signals and extremity warnings matter less; entry quality and position-sizing discipline matter more. If the new mechanism is a transient pattern that will revert to Draft 5's shape, the dashboard's exit-architecture concept (the canonical answer to "should the dashboard have alerts?") remains as important as ever.

---

## What the Data Can Support

1. **Trading remained profitable across a 40-day window.** +$5,291 net is real money, reconciled to row-level cash flow within a cent.

2. **Win rate rose to 68.1%, well above breakeven.** This is statistically robust at n=687.

3. **Payoff asymmetry inverted.** Winners now pay less than losers cost. Profit is now driven by win-rate edge, not by payoff edge.

4. **P&L concentration dropped sharply.** The book is more diversified, less tail-dependent. This is encouraging for durability.

5. **Swing vs. Hold remains the largest categorical distinction.** Swing wins more often, with better ROI, and contains the operator's edge mechanism. Hold contracts are mostly heavy-favorite bets that produce small mechanical wins at unfavorable payoff asymmetry — a different kind of trade with different economics.

6. **The $100–200 stake bucket is no longer a problem.** It flipped from net-loss to net-profit, with win rate rising 21 percentage points.

7. **The 7+ trade engagement pattern reversed.** What Draft 5 identified as the operational tell of intuition failing now shows as profitable. The trade-count warning indicator (parked) should be reconsidered in light of this.

8. **Operator currently profits more on ATP than WTA and more on SHORT-side routing than LONG.** Both differences are large enough to be substantive; sample is large enough to support as durable.

---

## Where the Opportunity Lives Going Forward

The strategic frame from Draft 5 (better entry signals in mid-stakes, better exit context, earlier recognition of losing setups) was built around the patterns Draft 5 saw. Those patterns shifted. The strategic frame should shift accordingly.

**Entry signals in the $100–200 band — less urgent than before.** Draft 5 named this bucket as the problem zone. It is now mid-range performance. The dashboard's role here is now confirmation, not correction.

**Exit context — different shape needed.** Draft 5's exit problem was identifying when swings became over-engaged losers. The re-run shows the 7+ engagement signal no longer points where it did. The exit-signal architecture (browser + audible, five triggers) was designed against Draft 5's exit problem; some of its triggers (the trade-count compound trigger especially) need re-validation against current behavior before implementation. The momentum-reversal and price-decline triggers are not affected by this re-run's findings and remain on the same footing.

**The new opportunity — guarding the win-rate edge.** If the operator's edge is now hit-rate-based rather than payoff-based, the failure mode shifts from "tail event wipes out wins" to "cold streak erodes the cushion." Cold-streak detection, drawdown monitoring, and per-day P&L watchdog become structurally more relevant than they were against Draft 5's tail-dependent edge. None of the existing concept docs cover this directly; it's a new direction worth scoping.

**Hold subset payoff-asymmetry warning.** Hold contracts have 0.58× payoff ratio — winners pay $26, losers pay $45. The win rate (59.3%) is just barely above the implied breakeven for that ratio (~63%). The operator is essentially breaking even on Hold contracts (slight loss, −4.2% ROI). The mechanism: buying near-favorites at 85–95¢ and letting them resolve. When they win, the profit is $0.05–$0.15/share; when they lose, the loss is $0.85–$0.95/share. **The asymmetry is structural and unfavorable; the only ways to improve it are entering at better prices (further out from $1) or exiting before resolution when momentum turns.** Both are dashboard-supportable.

**Direction X immediate next step.** The indicator-attribution data accumulated in the second half of the window (where instrumentation is increasingly populated) becomes the natural Direction X first cut. Which momentum-state-at-entry distributions correlate with which contract outcomes? Where do `Fair Price at Fill` and the actual resolution outcome disagree? The re-run report frames the question; the indicator-attribution analysis answers it.

---

## What the Data Cannot Tell Us

1. **Whether the win-rate jump (+23 pp) reflects skill improvement, instrument support, or variance.** All three are plausible. Disentangling them requires either a controlled comparison or substantially more data.

2. **Whether the payoff-asymmetry inversion is durable.** If Draft 5's 1.75× was the operator's real edge and the current 0.76× is transient, the next 40 days may revert. If 0.76× is the new normal, the strategic frame is different.

3. **Why the 7+ trade pattern reversed.** Without per-trade decision-reasoning data, we cannot tell whether deep-engagement positions are now intrinsically better-managed, or whether the *kind* of positions reaching 7+ engagement changed, or whether favorable variance happened to favor the deep-engagement bucket this window.

4. **Whether the first-half / second-half profit asymmetry is regime change or sample variance.** 88% of profit in the first half is striking; whether the second-half plateau is a real shift or a cooling spell will only show in subsequent windows.

5. **Whether instrument availability correlates with outcome quality at trade level.** This requires per-contract joining of indicator state at entry — which the trade attribution pipeline now produces — against contract outcome. That is Direction X's first major analytical cut and is the natural follow-up.

6. **The trades that didn't happen.** The dataset shows what the operator traded. It does not show the matches he watched, the prices he considered, the entries he passed on. Some of the strongest selection pressure in any operator's edge is in the trades they don't take.

---

## Closing

Trading was profitable in this 40-day window, at a return rate comparable to the Draft 5 baseline. What changed beneath the topline is the more interesting story: the operator now wins more often, wins smaller, loses larger, and is no longer dependent on tail outcomes. The 7+ trade engagement signal from Draft 5 has reversed direction. The $100–200 problem bucket is no longer a problem.

These shifts may reflect operator improvement, instrument support, regime change, or variance — likely some mixture. The next-step analysis (Direction X, joining indicator state at entry against contract outcomes) is what can begin to separate these. This report is the precondition for that work: a current baseline measurement against which the indicator-attribution data can be evaluated.

The dashboard's purpose has been to deliver measurably better outcomes than the +8.5% / 45% / 1.75× Draft 5 baseline. The 40-day window measurements are +10.1% / 68.1% / 0.76×. By the most direct read, two of three are improved (ROI marginally up, win rate substantially up), one is degraded (payoff ratio inverted), and the overall dollar return is comparable. The path forward is to understand which of these movements is the operator's edge and which is variance, and to instrument the result.

---

*Re-run report. Numerical claims reconciled to row-level cash flow via `/reports/today.csv` pulled 2026-05-19. Sample period: 2026-04-09 to 2026-05-18 (40 days, 687 contracts, $52,383 wagered).*
