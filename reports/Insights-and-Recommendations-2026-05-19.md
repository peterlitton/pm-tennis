# Trading Insights and Dashboard Recommendations

**Author:** PM-D.7
**Date:** 2026-05-19
**Window analyzed:** April 9 – May 18, 2026 (40 days, 687 closed contracts, 37 trading days)

---

## How to read this document

This is a strategic synthesis of what the operator's 40 days of trading suggest about which entry strategies, exit strategies, and dashboard features deserve attention next.

**About the framing.** During this trial period the operator wagers arbitrary amounts to gather data and practice. Dollar amounts and ROI are therefore noisy and not the evaluation axis. What matters is the **shape of the trading**: entries, exits, hold durations, price movements, win-rate outcomes, and how the mix of these has evolved as the operator has become more familiar with the platform.

**About the operator's actions.** On Polymarket, the operator picks a player and buys at the current price. They can then exit by selling at a later market price, or hold until the match resolves at 100¢ (player won) or 0¢ (player lost). That is the entirety of the operator's interaction with the market. There is no other action available, and the analysis throughout this document is framed in those terms.

**About what "win" and "loss" mean here.** A contract is a win if the exit price ended higher than the entry price (whether the exit was a manual sell or a 100¢ resolution). A loss if the exit was lower. Win rate is the count of winning contracts divided by total closed contracts.

---

## The journey across 40 days

The window analyzed here is not steady state. Two things were happening at once:

**The operator was learning the platform.** Forty days ago the operator had been trading on Polymarket for only a few weeks and was developing patterns by feel — entry timing, when to sell, when to hold, which conditional orders to leave standing overnight. Over the window, this practical knowledge accumulated rapidly: identification of tradable oscillation bands during tiebreakers, the standing-conditional-order routine for async overnight trades, awareness of which structural setups produce reliable price moves.

**The dashboard was being built around the operator's trading.** At the start of the window, the operator's only tool was the Polymarket iPhone app — no second screen, no indicators, no real-time reporting on closed positions, no consolidated view of the day's trading activity. Over the 40 days, a comprehensive execution-support surface was constructed: live match data, score and server attribution, momentum and pre-match edge indicators, position visibility on open trades, a closed-contracts review page, automated trade attribution joining indicator state to outcomes.

The trading data covers both arcs simultaneously. Every observation below reflects the entanglement: the operator getting better at the platform, with progressively more support from the dashboard. Separating "operator improvement" from "dashboard contribution" cleanly is not possible from this window alone. What the data does show is the cumulative effect of both, and where the strongest patterns now sit.

---

## What the 40 days look like in aggregate

| | |
|---|---|
| Total closed contracts | 687 |
| Trading days | 37 |
| Wins | 468 |
| Losses | 219 |
| Overall win rate | 68.1% |
| Contracts managed actively (Swing) | 387 |
| Contracts held to match resolution (Hold) | 300 |
| Swing win rate | 74.9% |
| Hold win rate | 59.3% |

The Swing-versus-Hold gap — active management vs. passive resolution — is 15.6 percentage points and statistically significant at p < 0.001. This is the most reliable pattern in the dataset.

---

## Week-over-week pattern

The mix of strategies the operator deployed shifted visibly week by week:

| Week | n | Win rate | Swing share | Hold share | Swing win rate | Hold win rate |
|---|---|---|---|---|---|---|
| W15 | 50 | 56.0% | 56.0% | 44.0% | 75.0% | 31.8% |
| W16 | 90 | 57.8% | 48.9% | 51.1% | 75.0% | 41.3% |
| W17 | 54 | 63.0% | 64.8% | 35.2% | 71.4% | 47.4% |
| W18 | 115 | 79.1% | 57.4% | 42.6% | 89.4% | 65.3% |
| W19 | 156 | 66.0% | 44.9% | 55.1% | 68.6% | 64.0% |
| W20 | 181 | 75.1% | 63.5% | 36.5% | 73.0% | 78.8% |
| W21 | 41 | 58.5% | 70.7% | 29.3% | 69.0% | 33.3% |

Early weeks show the lower Hold win rates (31–47%) typical of a trader actively experimenting with positions held to resolution but not yet calibrated to which Hold setups work. From Week 18 onward, Hold win rates rise sharply and stay there (with the exception of partial Week 21 which is too small to read into). Swing win rates climb steadily across the first four weeks, plateau near 70–90%, and remain strong.

The contract count rises in the middle weeks and stays elevated — the operator was trading more actively, taking more entries, in a wider range of matches. Week 19 in particular shows the highest contract count (156) and the highest Hold share (55%). Week 20 is the volume peak (181 contracts) but with a sharp tilt back toward Swing and the highest Hold win rate of the window.

These shifts are partly the operator trying different patterns and seeing what works; partly the dashboard surfacing new information that changes which entries look attractive. Both arcs are present in this table.

---

## The insights, ordered by leverage for what to build next

### 1. The Swing-versus-Hold gap is the most actionable read from the data

Swings win more often than Holds across nearly every entry-price band:

**Swing performance by entry price** (operator-perspective):

| Entry price | n | Win rate | Median price move |
|---|---|---|---|
| 0–20¢ | 34 | 73.5% | +4.3¢ |
| 20–40¢ | 83 | 62.7% | +7.0¢ |
| 40–60¢ | 48 | 70.8% | +11.3¢ |
| 60–80¢ | 100 | 78.0% | +14.8¢ |
| 80–100¢ | 122 | 82.8% | +10.7¢ |

**Hold performance by entry price**:

| Entry price | n | Win rate | Median price move |
|---|---|---|---|
| 0–20¢ | 47 | 12.8% | −10.0¢ |
| 20–40¢ | 33 | 18.2% | −25.0¢ |
| 40–60¢ | 15 | 26.7% | −45.0¢ |
| 60–80¢ | 57 | 59.6% | +22.0¢ |
| 80–100¢ | 145 | 86.2% | +10.0¢ |

The Hold table is striking. When the operator picks a player priced below 60¢ and holds to resolution, the player most often loses and the contract goes to 0. Of the 95 Hold contracts entered below 60¢, only 16 won.

The Hold table also shows that high-entry-price Holds (80–100¢) work mechanically — picking a heavy favorite and waiting for the resolution wins about as often as the entry price implies. The upside per contract is small (the median win moves only +10¢) but the pattern is reliable.

**Recommendation: a Hold-window warning indicator for mid-and-lower-range entries.** When the operator is holding a position entered below 60¢ as the match approaches a hard-to-exit phase, surface a visual prompt: *"holds in this entry-price band have underperformed — consider exiting at current price."* The pattern is large enough and consistent enough across weeks to act on.

### 2. Low-price entries produce the largest price moves — but the structural-conviction question is open

The largest positive price moves in the dataset all come from low-entry-price contracts that resolved at 100¢:

| Entry | Exit | Move | Type | Player |
|---|---|---|---|---|
| 2¢ | 100¢ | +98¢ | Hold | Calvin Hemery |
| 3¢ | 100¢ | +97¢ | Hold | Kaylan Bigun |
| 3¢ | 100¢ | +97¢ | Hold | Niels Visker |
| 4¢ | 100¢ | +96¢ | Hold | August Holmgren |
| 9¢ | 100¢ | +91¢ | Hold | Sorana Cirstea |

These are matches where the operator picked a player whose contract was priced very low and that player ended up winning. The pattern: identify a structural-near-certainty setup (e.g., a player who is dominantly favored on most indicators but whose contract is somehow priced cheaply), buy in, hold to resolution.

The Hold-by-entry-price table also showed that *most* low-entry Holds lose. So this pattern is a sharp instrument: when correctly read, it produces +90¢ wins; when incorrectly read, it produces near-total losses. The question is what distinguishes a structural-near-certainty entry from a noisy underdog bet.

Low-entry Swings, by contrast, win 73.5% of the time with positive median moves. They don't capture the +98¢ outliers (the operator sells out before resolution), but they win much more reliably.

**Recommendation: a structural-conviction tag for low-price entries.** Combine the player's pre-match prior, current score state, server attribution, recent point momentum, and ranking differential into a single confidence read. When the operator is about to enter at a low price and the structural-conviction is high, surface a "Hold candidate" tag. When it's low or mixed, surface "Swing candidate." This is buy-side decision support the operator has explicitly asked for, and the data shows it is needed: low-price entries currently win when actively managed and lose when passively held, so helping the operator distinguish which mode to apply is the right intervention.

### 3. Trade-count behavior splits into two distinct patterns

Looking at contracts with many touches (5+ buys and sells on the same contract):

| Touches | n | Win rate | Median move |
|---|---|---|---|
| 1–2 | 109 | 71.6% | +11¢ |
| 3–4 | 119 | 73.1% | +10¢ |
| 5–6 | 61 | 83.6% | +15¢ |
| 7+ | 98 | 75.5% | +7¢ |

5–6 touches is the highest-win-rate bucket. 7+ touches still wins three times in four. Multi-touch contracts are a substantial fraction of the operator's profit pattern, not a failure mode.

But these counts conceal two different behaviors:

- **The oscillation pattern.** The operator identifies a price range that's swinging within a tradable band (typically during tiebreakers or in late-set tension situations) and trades the band repeatedly: buy at the low side, sell at the high side, re-enter on the next dip, exit again, etc. This produces high touch counts and high win rates.
- **The chasing pattern.** A contract goes against the operator, they re-enter at successively worse entry prices trying to recover, and the position deepens into a losing situation. This also produces high touch counts, but with a falling per-touch entry price and a poor outcome.

The current data doesn't cleanly separate these because the touch count alone doesn't carry the per-touch direction. Both patterns coexist in the 7+ bucket; the aggregate looks healthy, but the underlying mix matters.

**Recommendation: a context-aware trade-count indicator, not a raw-count warning.** A warning that fires on touch count alone is too coarse — it would warn on the operator's oscillation-trading edge as readily as on chasing. The right signal compares per-touch entry prices: if successive entries on the same contract are at progressively *higher* prices (operator chasing a losing position to higher entry costs), warn. If successive entries are oscillating within a band, treat it as a tradable pattern and stay silent.

### 4. The momentum indicator is hand-tuned and currently unvalidated

The momentum indicator (MI) was constructed with these parameters:

- Window: last 12 individual points
- Point weights: 1 (own-serve point won), 2 (return point won), 3 (hold a game while serving), 5 (break opponent's serve)
- Linear time decay across the window
- Three-state classification (none / contested / leader) with thresholds 2/2

These numbers — 12 points, weights of 1/2/3/5, thresholds of 2/2 — were design choices. They reflect a sensible structure (recent points matter more than older points, breaks matter more than holds) but the specific values have never been validated against actual trade outcomes.

The trade attribution pipeline now captures `momentum_at_entry` on every fill that happens during a live match. For every closed Swing in the most recent weeks, the momentum state at entry is recorded and the contract outcome is known.

The data exists to test:

- Does momentum-at-entry predict outcomes? (i.e., does entering when the player has positive momentum lead to better outcomes than entering when they have negative momentum?)
- Is the relationship monotonic? Or is mean-reversion the better play (entering against momentum)?
- Are the 2/2 thresholds the right cutoffs?
- Are the point weights right? Does breaks-weighted-5 actually carry 5× the predictive value of own-serve-points-weighted-1?

**Recommendation: validate the MI empirically as the activation step of indicator-data analysis.** This is the highest-leverage foundational work the dashboard can do right now. Output: an empirically-tuned MI with weights and thresholds based on what the data says, not on what felt right when first designed. The MI is one input to the operator's reading of a match alongside score state, server, current price, player record — none of which is wholly dispositive on its own. The dashboard's job is to make it a sharper input than guesswork made it, and that requires validation.

### 5. The pre-match edge badge sits on current data but its calibration is untested

The edge badge computes `edge = pre_pct − price_cents`, where `pre_pct` comes from a surface-aware Elo blend using Tennis Abstract data refreshed during the window (May 1 snapshot).

Data freshness is not the issue. The open question is whether the model's *calibration* matches reality — whether a player the model says has 75% probability actually wins 75% of the time, whether a +20¢ edge actually predicts the player is undervalued by 20¢, etc.

The same trade attribution pipeline captures `edge_badge_at_entry` and `fair_price_at_entry`. The closed contracts in this window provide actual outcomes. The validation cut is straightforward:

- For contracts where the operator entered at a high positive edge (model says player is significantly undervalued by the market), do those contracts win more often than chance?
- Is the edge magnitude monotonic with win rate? (A +30¢ edge should predict more wins than a +10¢ edge.)
- Is the relationship symmetric? (Are −20¢ edges as informative about expected losses as +20¢ edges are about expected wins?)

**Recommendation: validate the edge-badge calibration empirically, immediately after MI validation.** Same approach, same data pipeline, same output: an empirical calibration curve that either confirms the edge badge as-is or surfaces specific bands where it under- or over-fires. If miscalibrated in a specific band, the rendering can be adjusted (e.g., suppress the badge in the bands where it doesn't predict) without rebuilding the underlying model.

### 6. The operator has asked for buy/sell signals — the building blocks now exist

The operator has stated they want **"Market has underpriced…"** and **"Market has overreacted…"** signals on the dashboard.

The building blocks are mostly in place:

| Building block | Status |
|---|---|
| Live price | Live (Gateway + Sports WS) |
| Live score state | Live (API-Tennis WS) |
| Server attribution | Live (API-Tennis WS) |
| In-game point state | Live (Gateway score field) |
| Pre-match edge badge | Live (data current, calibration pending — Insight 5) |
| Momentum indicator | Live (current parameters unvalidated — Insight 4) |
| Trade attribution | Live (joining indicator state to outcomes) |
| Rate of price change | Not currently computed |
| Rate of score events | Not currently computed |

Two distinct signal types worth scoping:

**Reactive signals — "the market just moved without a justifying event."** Compute rolling 30–60 second windows of price change and score-event count. If price moves more than a threshold in the window without a corresponding score event (no break, no set point, no medical timeout, no game change), the price move is reactive to something other than match state — either noise, news, or thin liquidity. The empirical question: do these moments revert?

The data to answer this exists in the state recorder. Pre-launch validation: in the past 30 days, find moments where price moved >10¢ in 60s without a same-window score event, and check what happened in the next 5 minutes. If reversion is the modal outcome, the signal is shippable.

**Proactive signals — "the model says this player is undervalued."** This depends on Insight 5 landing — the edge badge needs empirical validation before a signal built on it can be trusted. After that, the signal is: when current price is below the validated fair-price band AND momentum is positive AND no recent break-against, surface a "potential undervaluation" tag.

Both signals should ship soft initially — visual tags on the dashboard row, not audible alerts. The exit-signal architecture concept already covers the alert-tier escalation pattern; entry signals should follow the same pattern.

**Recommendation: start with the reactive overreaction signal in a near-term build.** Sequence:

1. Add rate-of-price-change and rate-of-score-events to the state recorder.
2. Backtest using the data already collected.
3. If reversion is consistent, ship the visual tag.
4. Iterate thresholds based on subsequent attributed trades.

The proactive undervaluation signal is the natural follow-up after the edge-badge calibration work (Insight 5).

### 7. The Hold subset has structurally limited upside and the data shows it

Even when Holds win, the price move on high-entry-price Holds is small. A Hold entered at 85¢ that wins moves +15¢. A Hold entered at 90¢ that wins moves +10¢. The mechanical upside on Holds at high entry prices is capped by the distance to 100¢.

Meanwhile, Holds at high entry prices that *lose* (the favorite unexpectedly drops the match) move −85¢ or worse — to 0. The few losers in the 80–95¢ Hold band can swamp many small winners.

This is structural, not skill-based. The math of buying at 90¢ to win 10¢ when right and lose 90¢ when wrong is fundamentally unfavorable unless the player wins more than 90% of the time. The 80–95¢ Hold subset wins at 86% in this window — close to the structural break-even, but not above it.

**Recommendation: a Hold-asymmetry warning on entries above ~80¢.** When the operator has entered at a high price and is trending toward a held-to-resolution position (no recent sell activity as the match progresses), surface: *"high-entry Holds carry asymmetric downside — consider partial exit at current price."* The pattern is mechanical and the data supports it directly.

### 8. Hold duration is informative and not currently surfaced

Each contract has a hold-duration field on its terminal row. The distribution shows:

- Median hold duration on closed contracts: ~1.5 hours (a typical match length)
- Roughly 10% of contracts hold under 15 minutes (rapid tiebreaker trading or quick exits)
- Roughly 5% hold for >24 hours (positions opened the night before for next-day matches, then held to resolution)

Hold duration cross-cut with outcome quality is unexplored in this analysis but is a strong candidate for analytical attention. Are quick Swings (under 15 minutes) the highest-win-rate subset? Do overnight Holds (entered the night before, held through match resolution) underperform compared to in-match Swings on the same matches? The data exists to answer these.

**Recommendation: include hold-duration as an axis in the next round of indicator-data analysis.** Partition the contract set by duration buckets (sub-15-min, 15–60-min, 1–3h, 3–24h, >24h) and look at win rate, price-move distribution, and entry-price profile per bucket. If a clear pattern emerges, the dashboard could surface a time-of-position indicator — "you've held this position 45 minutes, which is past the median for Swings in this entry-price band."

This is exploratory — no specific feature is recommended yet, just the analytical step that would inform one.

### 9. Headline-on-the-day reporting and trade visibility have value beyond what the current /trading page captures

The current trading review page surfaces today's closed contracts, today's cumulative P&L, today's win rate, and a recent-trades feed. It's a substantial improvement over the iPhone-only starting state, which had no consolidated review at all.

What the page doesn't yet surface that the data could support:

- **Per-strategy summaries.** A morning-after read on which patterns the operator was running — what fraction of yesterday's trades were sub-15-min swings, what fraction were Holds, how did each subset perform. The operator is experimenting; the platform should help them see what they actually did, not just the aggregate result.
- **Held-position visibility on completed-but-not-yet-acted-on opportunities.** When a held position approaches a structural exit point (per Insights 1, 7, or 8), the morning review is where that surfaces — not just live during the match.
- **Pattern-level performance attribution over a custom window.** Right now the page is single-day. A weekly view, an "all-time" view (within the dashboard's history), a custom-range view — these scaffold the operator's ability to detect their own pattern shifts.

These aren't urgent vs. the validation work (Insights 4 and 5) but they are the natural evolution of the trading-review surface. The infrastructure (the `/reports/today.csv` endpoint with `from`/`to` range params) already supports the data; what's needed is the UI surface to consume it.

**Recommendation: a weekly and custom-range view on the /trading page, plus per-strategy summaries.** Low-to-medium effort, no upstream data work required, immediate value for the morning-review workflow.

### 10. The operator's evolving strategy is itself a moving target, and the dashboard's contribution needs a way to be measured

Looking at the week-over-week table, the operator's behavior changes meaningfully week to week — different strategy mixes, different volume, different Hold/Swing balance. Some of this change is the operator iterating on their own; some is the dashboard surfacing new information that shifts which entries look attractive.

This is healthy — the operator is supposed to be experimenting. But it complicates measurement: if both the operator's behavior and the dashboard's feature set are moving simultaneously, attributing a win-rate change to one versus the other is difficult.

Two practices that would make measurement cleaner going forward:

- **Hold the operator's strategy approach stable for a defined period after each dashboard feature ships.** When a new feature is intended to influence operator decisions, the post-ship window is most informative when the operator's other patterns aren't simultaneously changing. The operator's experimentation is valuable; bounded periods of stability after a ship would let the data speak more cleanly about the feature.
- **Define what success looks like before each ship.** For features intended to influence decisions (like the Hold-warning of Insight 1 or the structural-conviction tag of Insight 2), define beforehand: what win-rate or entry-pattern change should this feature produce, how will we observe it, what minimum number of contracts is needed to detect a real signal. This makes the dashboard's contribution visible and avoids the "did the feature help or did the operator's strategy shift in the same week" ambiguity.

This is operational hygiene rather than a feature, but it determines whether the next 40 days produce evidence about what works, or more uncategorized noise.

---

## Recommendations ranked by leverage

| Rank | Recommendation | Effort | Data support |
|---|---|---|---|
| 1 | Validate the MI empirically (Insight 4) — foundational | Medium | Trade attribution data is ready |
| 2 | Validate the edge-badge calibration (Insight 5) | Medium | Same pipeline as #1 |
| 3 | Hold-warning indicator for mid-range entries (Insight 1) | Low | Strong; 95-contract sample with 17% win rate |
| 4 | Structural-conviction tag for low-price entries (Insight 2) | Medium | Strong; pattern is clear in the data |
| 5 | Hold-asymmetry warning on high-entry-price positions (Insight 7) | Low | Strong; math is mechanical |
| 6 | Context-aware trade-count indicator (Insight 3) | Low–Medium | Strong; chasing-vs-oscillation distinction is the key |
| 7 | Weekly/custom-range view on /trading page (Insight 9) | Low | Operator workflow benefit; no upstream data work needed |
| 8 | Reactive overreaction signal (Insight 6) | Medium | Backtestable from existing data |
| 9 | Proactive undervaluation signal (Insight 6) | Medium | Depends on #2 |
| 10 | Hold-duration analytical cut (Insight 8) | Low (analysis only) | Unexplored |
| — | Feature-attributed measurement plan (Insight 10) | Process | Operational |

Recommendations 1 and 2 are gates for several others. Recommendations 3, 5, 6, and 7 can ship in the near term on the data already in hand. Recommendations 4 and 8 are larger builds. Recommendations 9 and 10 are analytical work that informs the next round.

---

## What this synthesis claims and doesn't

**Does claim:**
- The patterns described are present in the data and reconciled to source.
- The recommended dashboard improvements are specific, scoped, and grounded in observed evidence.
- The operator is on a productive learning curve, and the dashboard's available tools have grown substantially over the window.

**Does not claim:**
- That the patterns are stable. Forty days is a meaningful window but still a single sample period. Some patterns may shift in the next 40 days as the operator continues to experiment and as new dashboard features land.
- That fixing the MI or edge badge in isolation will produce measurable trading improvement. They are necessary infrastructure for higher-quality signals; whether the signals built on top help depends on signal design and operator workflow.
- That the operator's experimentation should be reduced. The mix changes are how the operator learns the platform; the dashboard's job is to support that learning, not constrain it. The measurement-plan recommendation is about making the dashboard's contribution visible, not about freezing strategy choices.

---

*Synthesis. Numerical claims reconcile to `/reports/today.csv` pulled 2026-05-19 for the period 2026-04-09 → 2026-05-18. All in-flight contracts excluded per period-based reporting rule; non-tennis and the STENAP/TRISCH market excluded per analysis scope.*
