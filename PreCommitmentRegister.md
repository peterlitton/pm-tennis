# PM-Tennis — Pre-Commitment Register

This document is the human-readable record of every value, threshold, formula, and parameter that the project commits to before the observation window opens. Its machine-readable counterparts are the four commitment files: `data/fees.json`, `data/breakeven.json`, `data/signal_thresholds.json`, and `data/sackmann/build_log.json`. Those files are the authoritative source for the running system; this register records the reasoning behind each committed value, who decided it, and in which session.

The register exists because a Bayesian pre-commitment discipline requires not just that values are frozen before observation, but that the reasoning for each value is on record before the window opens. A value without recorded reasoning is indistinguishable from a value chosen after seeing data. The reasoning here is the evidence that the commitment was made in good faith before observation began.

---

## How this register works

**Population cadence.** Entries are added as commitments are made, primarily during Phase 1 and the pilot phase. The register is not complete at the end of H-003 — it is a template. Each section below contains the entry structure and any pre-seeded values that can be stated before Phase 1 begins. The remaining values are populated during Phase 1 work and the pilot protocol.

**Status lifecycle.** Each entry carries a status:

- `draft` — value is proposed but not yet final; may change before freeze
- `frozen` — value is locked; recorded in the corresponding commitment file with its SHA-256 checksum in STATE.md; cannot be changed during an active observation window
- `superseded` — entry was frozen and then legitimately changed (only possible between windows, not during); a new entry replaces it and this entry records the reason for the change

**Freeze event.** All entries in the Signal Thresholds and Breakeven sections are frozen at the pilot-complete / observation-window-open event (Playbook §7). The Fees section entries are frozen at Phase 1 exit. The Sackmann Build Parameters section entries are frozen when `build_log.json` is committed at Phase 1 exit. A frozen entry may not be edited during an active observation window — this applies to both Claude and the operator, and is enforced by the `OBSERVATION_ACTIVE` soft lock and the nightly SHA-256 checksum (Section 5.8 of the build plan).

**Supersession procedure.** If a committed value must change between observation windows (e.g., a Polymarket US fee-schedule change), the procedure is: (1) close the current window per Playbook §8; (2) add a new entry with the updated value and the reason for the change; (3) mark the prior entry `superseded` with a reference to the new entry; (4) re-derive any entries that depend on the changed value; (5) freeze all affected entries before opening a new window. No entry is deleted.

**Relationship to commitment files.** When an entry is frozen, the value is written to the corresponding JSON file. The register and the JSON file must agree. If they disagree, the JSON file is authoritative for the running system, and the register entry must be corrected and the discrepancy logged to the DecisionJournal.

---

## Section 1 — Fee Parameters

**Corresponding file:** `data/fees.json`
**Freeze event:** Phase 1 exit gate
**Source:** Polymarket US published fee schedule; Section 2.2 of the build plan

These values are read from Polymarket US's published schedule at Phase 1 and committed verbatim. They are not derived or calibrated — they are facts about the exchange. A fee-schedule change from the exchange supersedes these entries and ends the current observation window per Section 9.6.

---

### PCR-F-001 — Taker fee coefficient (Θ_taker)

**Status:** `draft` — to be verified and frozen at Phase 1 exit
**Value:** 0.05
**Formula:** Fee = Θ × C × p × (1 − p), where C = contracts, p = price
**Source:** Polymarket US published schedule, effective April 3 2026; Section 2.2
**Session committed:** *(populate when frozen)*
**SHA-256 of fees.json at freeze:** *(populate when frozen)*
**Notes:** Peaks at $1.25 per 100 contracts when p = $0.50. Symmetric around midpoint; approaches zero at price extremes. Charged to the aggressor side of each trade.

---

### PCR-F-002 — Maker rebate coefficient (Θ_maker)

**Status:** `draft` — to be verified and frozen at Phase 1 exit
**Value:** 0.0125
**Formula:** Same as taker; credited to the resting side of each trade
**Source:** Polymarket US published schedule, effective April 3 2026; Section 2.2
**Session committed:** *(populate when frozen)*
**SHA-256 of fees.json at freeze:** *(populate when frozen)*
**Notes:** 25% of the taker fee. Earned on both legs when entry and exit are passive posts. The strategy's passive-only execution means both legs earn this rebate except on sell-at-market exits.

---

### PCR-F-003 — Promotional taker rebate

**Status:** `draft` — to be verified and frozen at Phase 1 exit
**Value:** 50% taker rebate applied weekly
**Expiry:** Through April 30 2026
**Source:** Polymarket US promotion, current as of plan writing; Section 2.2
**Session committed:** *(populate when frozen)*
**SHA-256 of fees.json at freeze:** *(populate when frozen)*
**Notes:** Effectively halves taker fees during the promotional window. If the promotion expires or is extended before Phase 1 freeze, this entry is updated to reflect the actual schedule at freeze time. If it expires during the observation window, this entry is superseded and the window ends per Section 9.6.

---

## Section 2 — Sackmann Build Parameters

**Corresponding file:** `data/sackmann/build_log.json`
**Freeze event:** Phase 1 exit gate (when P(S) tables are committed)
**Source:** Phase 1 Sackmann pipeline work; Section 4.2 of the build plan

These entries record how the P(S) lookup tables were built — which archive versions were used, what data was included and excluded, and the resulting match counts and date coverage. They are facts about the build, not calibrated values, but they are pre-committed so that any future re-build of the tables is detectable as a change.

---

### PCR-S-001 — P_S_best_of_3 men's build parameters

**Status:** `draft` — to be populated and frozen at Phase 1 exit
**Source archives:** `tennis_pointbypoint` (ATP main + Challenger main)
**Expected match count:** ~35,000 (per Section 4.2; actual recorded in build_log.json)
**Actual match count:** *(populate at Phase 1)*
**Date coverage:** *(populate at Phase 1 — record actual cutoff from Sackmann GitHub)*
**Matches excluded:** *(populate at Phase 1 — document validation exclusions)*
**Bayesian shrinkage threshold:** n < 200 empirical observations → blend with Barnett-Clarke baseline; n = 0 → use Barnett-Clarke only
**Session committed:** *(populate when frozen)*
**SHA-256 of build_log.json at freeze:** *(populate when frozen)*

---

### PCR-S-002 — P_S_best_of_3 women's build parameters

**Status:** `draft` — to be populated and frozen at Phase 1 exit
**Source archives:** `tennis_pointbypoint` (WTA main) + `tennis_slam_pointbypoint` (women's Slam matches)
**Expected match count:** ~12,500 (per Section 4.2; actual recorded in build_log.json)
**Actual match count:** *(populate at Phase 1)*
**Date coverage:** *(populate at Phase 1)*
**Matches excluded:** *(populate at Phase 1)*
**Bayesian shrinkage threshold:** Same as PCR-S-001
**Session committed:** *(populate when frozen)*
**SHA-256 of build_log.json at freeze:** *(populate when frozen)*

---

### PCR-S-003 — P_S_best_of_5 men's build parameters

**Status:** `draft` — to be populated and frozen at Phase 1 exit
**Source archives:** `tennis_slam_pointbypoint` (men's Slam matches)
**Expected match count:** ~2,500 (per Section 4.2; actual recorded in build_log.json)
**Actual match count:** *(populate at Phase 1)*
**Date coverage:** *(populate at Phase 1)*
**Matches excluded:** *(populate at Phase 1)*
**Bayesian shrinkage threshold:** Same as PCR-S-001
**Session committed:** *(populate when frozen)*
**SHA-256 of build_log.json at freeze:** *(populate when frozen)*

---

### PCR-S-004 — Tour-wide serve-hold rate (Barnett-Clarke fallback input)

**Status:** `draft` — to be populated and frozen at Phase 1 exit
**Description:** Tour-wide average serve-hold rate computed once from each archive during Phase 1 pipeline. Used as the sole per-tour input to the Barnett-Clarke closed-form fallback for rare states (PCR-S-001/002/003 shrinkage).
**Men's best-of-3 value:** *(populate at Phase 1)*
**Women's best-of-3 value:** *(populate at Phase 1)*
**Men's best-of-5 value:** *(populate at Phase 1)*
**Session committed:** *(populate when frozen)*

---

### PCR-S-005 — Format routing table

**Status:** `draft` — seed values below; finalized and frozen at Phase 1 exit
**Description:** The static mapping that determines `best_of` for each event, and the set of excluded tournament formats (super-tiebreak deciders, no-ad scoring).

**Slam tournament set (men's main draw → best-of-5):**
- australian-open
- roland-garros
- french-open
- wimbledon
- us-open

**All other in-scope matches → best-of-3**

**Excluded formats (flagged at discovery, excluded from signal evaluation):**
- Super-tiebreak deciders (first-to-10 as deciding set)
- No-ad scoring
- *(any additional formats identified during Phase 1 are added here before freeze)*

**Session committed:** *(populate when frozen)*
**Notes:** The seed values above are taken from Section 4.2.3 of the build plan. Phase 1 verifies them against current Polymarket US taxonomy before freeze.

---

## Section 3 — Breakeven Derivation

**Corresponding file:** `data/breakeven.json`
**Freeze event:** Phase 1 exit gate
**Source:** Derived from Section 2 fee parameters; Section 8 Phase 1 of the build plan

The breakeven win rate is the minimum fraction of filled round-trips that must be profitable for expected P&L per trade to be zero or better. It is derived from the fee structure and the assumed price characteristics of the trades, not calibrated against market data. The derivation is committed at Phase 1 and enters the Section 9.3 primary criterion directly as the threshold the Bayesian posterior must exceed.

---

### PCR-B-001 — Assumed average entry price (for breakeven derivation)

**Status:** `draft` — to be set and frozen at Phase 1 exit
**Value:** *(populate at Phase 1 — set based on the fair-price range targeted by signal thresholds)*
**Reasoning:** *(populate at Phase 1)*
**Session committed:** *(populate when frozen)*
**Notes:** This is an input to the breakeven derivation, not a trading target. It represents the price at which a typical qualifying signal fires, given the handicap range [0.10, 0.90] and the undershoot-ratio trigger. A reasonable starting estimate is the midpoint of the handicap range (~0.50), but the actual value should be informed by the fair-price distribution observed during Phase 3 capture and the pilot.

---

### PCR-B-002 — Assumed average exit price (for breakeven derivation)

**Status:** `draft` — to be set and frozen at Phase 1 exit
**Value:** *(populate at Phase 1)*
**Reasoning:** *(populate at Phase 1)*
**Session committed:** *(populate when frozen)*
**Notes:** Exit target is fair-price-at-fill × 0.98 (PCR-T-008 exit cushion), snapped to nearest valid tick. The average exit price in the derivation approximates what this exit target looks like across the expected price range.

---

### PCR-B-003 — Assumed average spread at entry (for breakeven derivation)

**Status:** `draft` — to be set and frozen at Phase 1 exit
**Value:** *(populate at Phase 1 — informed by Phase 3 capture observations)*
**Reasoning:** *(populate at Phase 1)*
**Session committed:** *(populate when frozen)*

---

### PCR-B-004 — Breakeven win rate: passive entry + passive exit

**Status:** `draft` — to be derived and frozen at Phase 1 exit
**Value:** *(populate at Phase 1)*
**Derivation:** Both legs fill as resting orders. Entry earns maker rebate (Θ_maker × C × p_entry × (1 − p_entry)). Exit earns maker rebate (Θ_maker × C × p_exit × (1 − p_exit)). Net fee = rebates credited on both legs. Solve for win rate W such that W × (p_exit − p_entry) − (1 − W) × (p_entry − 0) + net_rebates = 0.
**Worksheet:** Committed to `breakeven.json` at Phase 1 exit; narrative derivation recorded here.
**Session committed:** *(populate when frozen)*
**SHA-256 of breakeven.json at freeze:** *(populate when frozen)*

---

### PCR-B-005 — Breakeven win rate: passive entry + sell-at-market exit

**Status:** `draft` — to be derived and frozen at Phase 1 exit
**Value:** *(populate at Phase 1)*
**Derivation:** Entry fills as resting order (maker rebate on entry). Exit crosses spread (taker fee on exit, no promotional rebate applies to exit leg if promotional window has ended). Solve for win rate W such that W × (p_exit − p_entry) − (1 − W) × (p_entry − 0) + entry_rebate − exit_taker_fee = 0.
**Worksheet:** Committed to `breakeven.json` at Phase 1 exit.
**Session committed:** *(populate when frozen)*
**SHA-256 of breakeven.json at freeze:** *(populate when frozen)*
**Notes:** This scenario applies when the passive exit fails within the 10-minute timeout and sell-at-market is used. The Section 9.3 primary criterion uses the blended breakeven across the expected mix of passive and sell-at-market exits. PCR-B-006 records the assumed mix.

---

### PCR-B-006 — Assumed exit-path mix (passive vs. sell-at-market)

**Status:** `draft` — to be set and frozen at Phase 1 exit (or pilot exit if pilot data informs it)
**Value:** *(populate — e.g., 70% passive exit, 30% sell-at-market)*
**Reasoning:** *(populate)*
**Session committed:** *(populate when frozen)*
**Notes:** The blended breakeven used in Section 9.3 = (passive_fraction × PCR-B-004) + (sam_fraction × PCR-B-005). This mix is set before observation; it is not adjusted to fit observed exit patterns during the window.

---

## Section 4 — Signal Thresholds

**Corresponding file:** `data/signal_thresholds.json`
**Freeze event:** Pilot-complete / observation-window-open event (Playbook §7); per D-002, thresholds are calibrated during the pilot and frozen at pilot end
**Source:** Section 4.4 and Section 9.2 of the build plan; pilot calibration per D-002

The values below are the plan's seed values from Section 9.2. They are starting points for the pilot calibration, not the frozen values. During the pilot phase, the pilot protocol document (a Phase 7 exit gate requirement per D-002) specifies how these values are calibrated against pilot data and frozen. The freeze happens at pilot end, before any observation-window data is collected.

All entries in this section are `draft` until the pilot-complete event.

---

### PCR-T-001 — Undershoot trigger ratio (X)

**Status:** `draft`
**Seed value:** 0.08 (8% of fair price)
**Definition:** Signal fires when (fair_price − observed_ask) / fair_price ≥ X
**Pilot calibration note:** The pilot protocol will specify whether X is grid-searched or set by expert judgment against pilot summary statistics. The calibrated value replaces the seed value here at pilot-complete.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-002 — Handicap range filter

**Status:** `draft`
**Seed value:** [0.10, 0.90] — both YES contracts must have pre-match median mid within this range
**Reasoning:** Outside this range the probability curve is too flat for log-odds evidence to produce reliable fair-price estimates; the book is typically too thin to trade.
**Pilot calibration note:** May be narrowed based on pilot fill-rate observations at extreme handicap values. Cannot be widened past [0.10, 0.90].
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-003 — Live price range filter

**Status:** `draft`
**Seed value:** [0.05, 0.95]
**Reasoning:** Same logic as PCR-T-002 applied to the live ask price at signal time.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-004 — Spread cap

**Status:** `draft`
**Seed value:** $0.04
**Definition:** Signal disqualified if current spread (ask − bid) on the YES contract exceeds this value.
**Reasoning:** A wider spread indicates a thin book where passive fill at the ask is unreliable and slippage on exit is elevated.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-005 — Minimum resting size at ask

**Status:** `draft`
**Seed value:** $50 notional
**Definition:** Signal disqualified if resting size at the current best ask is below this value.
**Reasoning:** Thin top-of-book exposes the passive order to being left behind when the quote steps away before filling.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-006 — Just-pulled-size filter

**Status:** `draft`
**Seed value:** Skip signal evaluation for 10 seconds if resting size at ask dropped by >50% in the prior 3 seconds.
**Reasoning:** A rapid size withdrawal indicates maker quote-pulling, which precedes adverse price moves. Waiting 10 seconds allows the book to restabilize before evaluating the signal.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-007 — Recent taker activity filter

**Status:** `draft`
**Seed value:** At least one `last_trade_price` event within the prior 30 seconds
**Reasoning:** Distinguishes genuine retail-driven overshoots from Maker Rebates Program repositioning. See R-003 and Section 4.4 of the build plan.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-008 — Score-event recency window

**Status:** `draft`
**Seed value:** 60 seconds (clock paused during Sports WS suspension status)
**Definition:** Signal disqualified if time since the most recent Sports WS score event exceeds this window.
**Reasoning:** Undershoots persisting beyond this window are more likely real repricing than transient mispricing.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-009 — Exit target

**Status:** `draft`
**Seed value:** fair_price_at_fill × 0.98, snapped to nearest valid tick at or below
**Definition:** The price at which the passive sell order is placed after a filled entry. The 0.98 cushion leaves a small margin below fair to improve passive exit fill probability.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-010 — Maximum time in position

**Status:** `draft`
**Seed value:** 10 minutes; exit via sell-at-market if passive sell unfilled at timeout
**Reasoning:** Bounds maximum exposure duration. A position held beyond 10 minutes is unlikely to exit passively within a score-event repricing window.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

### PCR-T-011 — Position size

**Status:** `draft`
**Seed value:** $25 notional per entry, fixed across all signals
**Reasoning:** Fixed sizing removes position-size as a variable in the observation-window analysis. $25 is small enough to be absorbed by typical Challenger liquidity and large enough to yield P&L that is meaningful relative to fees.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*
**Notes:** Position sizing for any scaled operation after a pass verdict is a separate commitment, not derived from this entry.

---

### PCR-T-012 — Concurrency caps

**Status:** `draft`
**Seed value:** Max 1 open position per match; max 3 open positions system-wide
**Reasoning:** Per-match cap prevents averaging into a losing position. System-wide cap limits total capital at risk and prevents the dashboard from becoming unmanageable during busy tournament days.
**Frozen value:** *(populate at pilot-complete)*
**Session committed:** *(populate when frozen)*

---

## Section 5 — Observation Window Terms

**Corresponding file:** None (these terms are recorded in this register and in STATE.md; they are not committed to a JSON file)
**Freeze event:** Pilot-complete / observation-window-open event (Playbook §7)
**Source:** Section 9 of the build plan

---

### PCR-W-001 — Window close triggers

**Status:** `draft` (seed from Section 9.1; not calibrated, adopted from plan)
**Value:** Window closes when either 250 qualifying signals are recorded OR 60 calendar days elapse, whichever comes first.
**Frozen value:** *(populate at pilot-complete — confirm or adjust)*
**Session committed:** *(populate when frozen)*

---

### PCR-W-002 — Primary criterion pass threshold

**Status:** `draft`
**Value:** Bayesian posterior probability that true win rate exceeds `breakeven.json` value ≥ 0.80 → pass; ≤ 0.40 → fail; between 0.40 and 0.80 → ambiguous (extend or follow-up window).
**Prior:** Uniform Beta(1,1) on true win rate.
**Frozen value:** *(populate at pilot-complete — confirm or adjust)*
**Session committed:** *(populate when frozen)*

---

### PCR-W-003 — Additional pass conditions (Section 9.3)

**Status:** `draft`
**Values:**
- Qualifying signal count during window: ≥ 150 (ideally 250)
- Simulated entry fill rate: ≥ 40% within 5 minutes (back-of-queue assumption)
- Simulated exit fill rate (among filled entries): ≥ 60% within 10 minutes
- Positive-day count: ≥ 60% of observation days with net positive simulated P&L
- Mean P&L per filled round-trip (net of fees, inclusive of zero-outcome unfilled entries): positive
- Adverse-selection metric: mean signed post-fill price drift (net of fair-price movement, 30-second window) not significantly negative at 95% confidence
**Frozen value:** *(populate at pilot-complete — confirm or adjust each condition)*
**Session committed:** *(populate when frozen)*

---

### PCR-W-004 — Secondary criterion conditions (Section 9.4)

**Status:** `draft`
**Values:**
- Actual intents logged during active windows: ≥ 30
- Actual fill rate on placed entries: ≥ 30%
- Realized P&L: positive after fees
- Manual-log reconciliation discrepancy rate: ≤ 10%
**Frozen value:** *(populate at pilot-complete — confirm or adjust)*
**Session committed:** *(populate when frozen)*

---

### PCR-W-005 — Coverage window commitment

**Status:** `draft` — operator commits specific daily hours before window opens
**Value:** *(operator specifies daily active hours at pilot-complete; recorded here at freeze)*
**Session committed:** *(populate when frozen)*
**Notes:** Only signals during logged active windows count toward the secondary criterion. Primary criterion uses all signals regardless of coverage.

---

*End of PreCommitmentRegister.md — v1 template, H-003.*
*All entries marked `draft` are to be populated and frozen at their respective freeze events.*
*Do not populate frozen values speculatively — only at the actual freeze event, with the session ID recorded.*
