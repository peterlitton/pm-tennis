# PM-Tennis — RAID Log

This document is the living Risks, Assumptions, Issues, and Dependencies log for the PM-Tennis project. It is seeded from Section 11 (Open Issues), Section 12 (Risks and Mitigations), and the five review additions accepted in H-002. New entries are added as items emerge; existing entries are updated as status changes. Entries are never deleted — a closed entry is marked closed, not removed.

Per Section 1.5.4 of the build plan, Claude maintains this log as a living document, adding entries when new risks, assumptions, issues, or decisions emerge and updating entries when their status changes.

---

## Conventions

- **IDs.** Each entry has a type prefix and sequential number: `R-` for Risk, `A-` for Assumption, `I-` for Issue, `D-` for Dependency. IDs are never reused.
- **Severity (Risks and Issues only).** 1–10 scale matching Section 11's convention: 7–8 is critical (per-match or per-phase failure mode that must be engineered against), 5–6 is material (requires an explicit plan element), 1–4 is acknowledged and managed inline.
- **Status.** One of: `open`, `mitigated` (mitigation in place but risk not eliminated), `resolved` (issue fixed or assumption validated), `closed` (no longer applicable), `monitoring` (watching for changes).
- **Owner.** The phase or decision responsible for the mitigation or resolution.
- **Source.** Where the entry originated: plan section, session, or decision ID.

---

## Risks

Risks are uncertain future events that would negatively affect the project if they occur. A mitigated risk still has a residual probability of occurring; it is not the same as resolved.

---

### R-001 — Adverse selection on passive fills

**Severity:** 8
**Status:** Mitigated
**Owner:** Phase 6 (replay simulator)
**Source:** Section 11.1; H-002 review addition confirmed

**Description:** Counterparties that hit the resting bid during an undershoot may be disproportionately informed rather than retail. If fills cluster at moments where the model's fair estimate is wrong rather than the market's, the thesis is undermined regardless of nominal P&L — the operator is being filled by flow that knows something.

**Mitigation:** The Phase 6 replay simulator computes a post-fill signed price drift metric, net of fair-price movement, over 30 seconds following each simulated fill. This metric is the seventh pass condition in Section 9.3 (adverse-selection criterion). A significantly negative net drift fails the observation window regardless of all other metrics. The recent-taker-activity filter in Section 4.4 also guards at signal-qualification time by requiring aggressive taker flow to be present before a signal is treated as tradeable.

**Residual risk:** The taker-activity filter and the post-fill metric together reduce but do not eliminate adverse-selection risk. A sufficiently sophisticated informed actor could simulate retail flow patterns. Residual risk is accepted; the 30-second metric is the primary observable.

---

### R-002 — Sports WebSocket point-level granularity unavailable

**Severity:** 7
**Status:** Open — Phase 1 verification required
**Owner:** Phase 1 (host preparation and verification); D-003
**Source:** Section 11.1; D-003 (H-002)

**Description:** Point-level data is visible in the Polymarket US iPhone app during live matches, establishing that point-level state exists in Polymarket's infrastructure. What is unconfirmed is whether the public Sports WebSocket delivers it or whether the app uses a separate authenticated channel. If the public WS emits only game-boundary transitions, break-point and deuce transitions — the highest log-odds evidence states in the model — are unavailable. The thesis is weaker at game-level granularity, and whether it remains worth pursuing is a judgment call the operator must make, not an automatic downgrade.

**Mitigation:** Per D-003, Phase 1's granularity check is an explicit go/no-go gate. Claude captures 15+ minutes of a live ATP/WTA main-tour match and inspects `sports.jsonl` for per-point state transitions. If only game-boundary transitions are present, Claude stops, produces an assessment of which signal classes survive the coarsening, and the operator rules go / no-go / defer before Phase 2 begins. The ruling is logged to the DecisionJournal.

**Residual risk:** If the ruling is "go at game level," the signal model operates with lower leverage and the observation window may be less discriminating. This is a known and accepted residual risk under the go/game-level scenario.

---

### R-003 — Maker Rebates Program artifact mimics tradeable undershoot

**Severity:** 7
**Status:** Mitigated
**Owner:** Phase 4 (signal implementation); Section 4.4
**Source:** Section 11.1

**Description:** Market makers quoting quadratically toward mid under Polymarket US's Maker Rebates Program may reposition after a score event in a way that looks like a tradeable undershoot but is actually algorithmic repositioning toward the new mid. A buy placed during such a repositioning would fill only to see the price continue moving rather than reverting — the visible "valley" is the maker's quote-repositioning, not retail overshooting.

**Mitigation:** Section 4.4's recent-taker-activity filter requires at least one `last_trade_price` event within 30 seconds preceding any signal. This distinguishes genuine retail-driven overshoots (where aggressive flow is crossing the spread) from pure maker chasing (where no taker flow is present). The adverse-selection metric in Phase 6 (R-001 mitigation) provides a second backstop by detecting the pattern in the post-fill price drift.

**Residual risk:** The 30-second taker-activity window is a heuristic, not a guarantee. A maker repositioning coincident with unrelated taker flow would pass the filter. Residual risk is accepted as bounded by the 30-second window and the post-fill metric.

---

### R-004 — First-server identification error

**Severity:** 7 (catastrophic per-match, not per-project)
**Status:** Mitigated
**Owner:** Phase 3 (capture)
**Source:** Section 11.1

**Description:** If the instrument records the wrong player as first server, every subsequent state's `(server)` dimension is mirrored and every log-odds evidence delta is sign-flipped for that match. The fair-price model has no internal mechanism to detect this error — a match with persistent sign-flipped deltas looks like a match where the trailing player keeps improbably recovering, which could appear as systematic undershoots on the wrong player.

**Mitigation:** Phase 3 records the first-server identification explicitly in `meta.json` with a flag on first Sports message with `live==true`. Window-close analysis cross-checks accumulated evidence direction against final winner: persistent sign-flipped fair-price trajectories are a detectable pattern. Matches flagged as potentially mis-identified are quarantined from the primary criterion.

**Residual risk:** Cross-check is ex-post, meaning mirrored matches would be captured in full and influence the archive before detection. Quarantine is applied at analysis time, not capture time. Accepted.

---

### R-005 — Retirement and suspension handling failure

**Severity:** 7
**Status:** Mitigated
**Owner:** Phase 3 (capture); Section 4.5
**Source:** Section 11.1

**Description:** Mid-match retirements produce extreme price moves unrelated to score state. The Sackmann archive excludes retirements; a live match that ends in retirement would generate a signal from a price move the model cannot evaluate correctly, potentially producing a spurious qualifying signal or a catastrophic fill.

**Mitigation:** On Sports WS status transition to `"suspended"`, signal evaluation is disabled for that match immediately. On transition to `"finished"` or `"cancelled"` with a partial score, the match is marked retired in `final.json` and excluded from window-close signal evaluation. The model withdraws rather than attempting to model retirement probability.

**Residual risk:** A retirement that produces a Sports WS status transition with a delay could generate a brief window of false signals. The `suspended` status is the instrument's signal; if the WS lags the actual retirement, a fill is possible. Accepted as low-frequency and bounded in size by position-size limits.

---

### R-006 — CLOB WebSocket silent stall

**Severity:** 7
**Status:** Mitigated
**Owner:** Phase 3 (capture); Section 5.4
**Source:** Section 12.2

**Description:** A documented issue (Polymarket GitHub issue #26, December 2025, unresolved at plan writing) causes the CLOB WebSocket to stop delivering messages after approximately 20 minutes while ping/pong continues to succeed. A stalled connection appears healthy at the transport layer but is producing no data.

**Mitigation:** Proactive 15-minute recycle on every connection regardless of observed health, staggered across the pool so at most one connection recycles at a time. Application-level liveness probe: if any connection receives no messages for 90 seconds during hours when at least one match is live, force-reconnect. Pool structure means a single stall affects at most one-quarter of coverage during the recycle window.

**Residual risk:** A stall that begins immediately after a recycle could persist for up to 90 seconds before the liveness probe triggers. Coverage gap of up to 90 seconds per affected connection is accepted.

---

### R-007 — Two-client sync and manual-log race condition

**Severity:** 7
**Status:** Mitigated
**Owner:** Phase 5 (dashboard); Section 7.2
**Source:** Section 11.1

**Description:** The dashboard and the Polymarket US iPhone app are independent clients. The dashboard cannot observe what was placed, filled, or cancelled on the phone. Manual-log race conditions — where a trade action happens before (or after) the corresponding envelope is logged — affect the window-close secondary criterion directly. A missed intent log makes a fill appear without a triggering signal; a delayed fill log makes the timing analysis incorrect.

**Mitigation:** Section 7's three disciplines: (1) intent envelope logged before acting on the app; (2) price, size, and app-displayed fields recorded at every action moment; (3) daily reconciliation against the Polymarket US app's trade history, with discrepancies logged to `reconciliation.jsonl`. A reconciliation-discrepancy-rate cap (≤10%) is a secondary-criterion condition.

**Residual risk:** Operator discipline determines the fidelity of the manual log. Fatigue-driven logging gaps are a real risk in a 60-day window. The secondary criterion is bounded to active-window signals specifically to limit the blast radius of fatigue-related gaps.

---

### R-008 — Operator fatigue and coverage bias

**Severity:** 7
**Status:** Mitigated
**Owner:** Phase 5 (dashboard); Section 7.3
**Source:** Section 11.1; H-002 review addition

**Description:** A 60-day observation window involving active monitoring of live tennis is an endurance test. Low-attention periods produce missed signals, and a fatigued operator who is present but not actively engaged may log intent without adequate signal verification, biasing the secondary criterion in both directions.

**Mitigation:** Section 7.3's pre-committed daily coverage windows, logged via the dashboard's availability toggle to `operator_availability.jsonl`. Only signals during active windows count toward the secondary criterion. The primary criterion (replay-simulator view) is computed across all signals regardless of operator coverage, making it independent of fatigue.

**Residual risk:** The boundary between "active" and "passive" is self-reported. An operator who logs "active" but is distracted introduces noise. Accepted; the reconciliation-discrepancy check provides a partial backstop.

---

### R-009 — Polymarket US API changes

**Severity:** 6
**Status:** Monitoring
**Owner:** All phases; ongoing
**Source:** Section 12.1

**Description:** Endpoint shapes change, new authentication is required, rate limits tighten, tennis taxonomy is restructured, or the published fee schedule is revised. Any of these would degrade or break the instrument with no warning.

**Mitigation:** The envelope stores raw messages; `meta.json` preserves full discovery payloads. A fee-schedule change ends the current observation window (Section 9.6) and requires re-derivation of `breakeven.json` before a new window starts. Quarterly taxonomy review catches structural shifts. Rate-limit response headers are logged and surfaced in the healthcheck.

**Residual risk:** A change between quarterly reviews could go undetected for weeks. Monitoring.

---

### R-010 — Statistical power at small sample

**Severity:** 8
**Status:** Mitigated
**Owner:** Section 9 (observation window design)
**Source:** Section 11.1; H-002 review addition

**Description:** At n=100 signals with a 55% observed win rate, the 95% confidence interval on the true win rate is approximately 45%–65% — wide enough to make a "pass" decision indistinguishable from a coin flip. A false-pass decision at small sample could drive the project into scaled operation on a non-edge.

**Mitigation:** The observation window runs to n=250 signals or 60 calendar days, whichever comes first. The pass criterion is a Bayesian posterior probability that the true win rate exceeds the `breakeven.json` value at ≥80% confidence — not a fixed point-estimate threshold. Ambiguous zones (posterior 40%–80%) extend to the calendar cap or require a follow-up window rather than forcing a decision.

**Residual risk:** Even at n=250, a 55% win rate yields a posterior interval that is informative but not tight. The ≥80% posterior threshold is calibrated to accept this uncertainty and rule pass only when the signal is sufficiently strong. Residual uncertainty is a property of the sample size and is accepted as the cost of a time-bounded observation window.

---

### R-011 — Sackmann archive pooling across tours

**Severity:** 7
**Status:** Mitigated (post-build refinement planned)
**Owner:** Phase 1 (Sackmann pipeline); post-build
**Source:** Section 11.1

**Description:** Pooling Slam, ATP main, and Challenger data into a single P(S) table for men's best-of-3 assumes distributional equivalence across tours that is not directly tested. Serve dominance, return competitiveness, and behavioral patterns at specific score states may differ materially between tour levels.

**Mitigation:** Log-odds additivity partially mitigates this: what matters is the relative probability change between states (the delta), not the absolute level. The common prior embedded in both P(S_before) and P(S_after) cancels in the subtraction. Post-build refinement compares deltas at representative high-leverage states across tour-specific P(S) tables once the live archive has accumulated sufficient matches per tour. If deltas differ by more than 15% at high-leverage states, tour-specific lookups are introduced.

**Residual risk:** The 15%-delta threshold is a judgment call, not a statistically derived threshold. Accepted as the best available standard given the sample-size constraints of tour-specific archives.

---

### R-012 — Pilot threshold derivation overfitting

**Severity:** 6
**Status:** Open — sub-questions unresolved; D-002 open items
**Owner:** D-002; pilot protocol document (due before Phase 7 exit)
**Source:** H-002 review addition; D-002

**Description:** The pilot-then-freeze protocol (D-002) calibrates `signal_thresholds.json` against pilot archive data. Calibration against a finite pilot sample risks overfitting — thresholds optimized to the pilot may fail to generalize to the observation window, producing a false-pass or false-fail result that is an artifact of the calibration method rather than the underlying thesis.

**Mitigation:** Overfitting guardrails are a D-002 open sub-question. Candidates: hold out part of the pilot data, pre-commit to a small set of candidate threshold tuples and select only among them, use coarse discrete grid with pre-committed resolutions. The pilot protocol document must be written and committed before any pilot data is inspected; calibration against already-seen data is explicitly prohibited.

**Residual risk:** Depends entirely on the guardrail method chosen. Status will update when D-002 sub-questions are resolved.

---

### R-013 — Queue-position assumption in replay simulator

**Severity:** 6
**Status:** Mitigated (conservatively)
**Owner:** Phase 6 (replay simulator)
**Source:** H-002 review addition

**Description:** The replay simulator places hypothetical orders at back-of-queue by default — behind all resting size at the order price as of the book state at placement time. Real fill probability may be higher (if the operator is fast and arrives near the front) or lower (if the book is thin and moves away). The back-of-queue assumption is a deliberate conservative bias: it understates simulated fill rates relative to actual performance, which means a pass under back-of-queue assumption is more credible than a pass under front-of-queue.

**Mitigation:** Conservative default is the mitigation. The assumption is stated explicitly in the simulator and in the Phase 6 acceptance criteria. Window-close analysis notes the queue-position assumption prominently in the decision memo so that any scale decision accounts for it.

**Residual risk:** Actual queue position is unknowable from the archive. The conservative assumption may understates true edge, but this direction of error is preferred over overstating it.

---

### R-014 — Secondary-criterion statistical power

**Severity:** 5
**Status:** Mitigated (design constraint accepted)
**Owner:** Section 9.4 (secondary criterion)
**Source:** H-002 review addition

**Description:** The secondary criterion requires at least 30 actual intents logged during active windows. At n=30, a 55% actual fill-and-profit rate has a very wide confidence interval. The secondary criterion is therefore weak as a standalone decision input — it is a sanity check on the operator's ability to capture signals with iPhone execution, not an independent falsification test.

**Mitigation:** The secondary criterion is explicitly not a primary decision input (Section 9.5 decision matrix). It can fail the window in the "primary pass / secondary fail" scenario (mispricing is real but iPhone execution cannot capture it), but it cannot independently pass the window. The lower bar (n=30, positive P&L, ≤10% unreconciled) is set to be achievable under realistic coverage, not to provide statistical precision.

**Residual risk:** The "primary pass / secondary fail" scenario ends the project without an automation path being opened — the decision matrix is explicit about this. The operator accepts that outcome as a possible result.

---

### R-015 — Host downtime during observation

**Severity:** 5
**Status:** Mitigated
**Owner:** Phase 7 (monitoring)
**Source:** Section 12.5

**Description:** Backend service (Render PaaS) downtime, maintenance windows, or platform incidents during the observation window create gaps in the archive. A gap during an active match loses tick data that cannot be recovered.

**Mitigation:** Render's deploy-from-git with automatic restart on failure. Phase 7's monitoring watchdog alerts on healthcheck failure. The archive's gap pattern (snapshot-after-gap sequence) makes gaps detectable at analysis time. Signals during detected gap windows are excluded from the primary criterion or flagged for manual review.

**Residual risk:** Render's SLA and historical uptime are not in the plan's scope to specify. A prolonged outage could truncate the observation window. Accepted as low-frequency at Render's reliability tier.

---

## Assumptions

Assumptions are things the project treats as true without direct verification. Each should be validated at the phase that first relies on it.

---

### A-001 — Polymarket US tennis market liquidity is sufficient for passive fills

**Status:** Unvalidated — Phase 1 observation
**Owner:** Phase 1 and 3
**Source:** Section 3.1 (implicit)

**Description:** The signal model assumes that ATP main-tour, WTA main-tour, Challenger, and Slam moneyline markets consistently maintain resting size at or near the ask sufficient for a $25 passive buy to fill within the signal's validity window. If Challenger markets are too thin, the instrument captures signals that are theoretically valid but practically unfillable.

**Validation plan:** During Phase 1 and early Phase 3 live capture, observe spread width, resting size at ask, and frequency of `last_trade_price` events across tour levels. The spread cap (≤$0.04) and minimum size-at-ask ($50) in `signal_thresholds.json` filter out thin-book signals; the pilot phase validates whether the filter leaves meaningful signal frequency.

---

### A-002 — Sackmann P(S) deltas transport from archive to live markets

**Status:** Unvalidated — observation window provides primary test
**Owner:** Phase 1 (Sackmann pipeline); observation window
**Source:** Section 3.1; Section 4.2

**Description:** The fair-price model assumes that the statistical impact of score-state transitions observed in the Sackmann archives (covering historical matches) is representative of the impact in live Polymarket US markets. Tennis scoring mechanics are identical across history; behavioral and structural dynamics may differ.

**Validation plan:** The observation window is the primary test: if the Bayesian posterior on win rate exceeds breakeven at ≥80% confidence, the assumption is supported. The archive-level cross-check of P(S) deltas across tour levels (R-011 mitigation) provides a secondary structural check.

---

### A-003 — Pre-match Polymarket US consensus price is a reliable strength signal

**Status:** Unvalidated — observable at Phase 3 capture
**Owner:** Section 4.1; Phase 3
**Source:** Section 4.1

**Description:** The fair-price model anchors on the pre-match Polymarket US YES median mid as the best available estimate of player relative strength. This assumption holds if the pre-match market is set by professional makers with time to price. It may fail if pre-match books are thin, set by retail flow, or stale.

**Validation plan:** The handicap sanity check (sum of medians within [0.98, 1.02], no crossed book) and the 30-minute max-age constraint filter out the most obvious failures. Matches with `shallow_handicap` or `stale` flags are excluded from signal evaluation. Residual assumption: a non-stale, non-shallow handicap is a reliable strength signal.

---

### A-004 — Render PaaS provides sufficient compute and disk for continuous capture

**Status:** Unvalidated — Phase 1 setup
**Owner:** Phase 1
**Source:** Section 1.5.1; Section 1.5.6

**Description:** The managed PaaS (Render) replacing the original Hetzner VPS provides at least: continuous background worker availability, sufficient disk for 16+ months of gzipped JSONL, and adequate compute to maintain two-to-four CLOB WebSocket connections plus a Sports WebSocket without message queuing lag under peak-tournament load.

**Validation plan:** Phase 1 stress test: subscribe to 200 asset IDs in a pool of connections and confirm message throughput is not degraded. Monitor queue depth and write latency during Phase 3 under live load. If Render's starter tier is insufficient, a tier upgrade (estimated USD 110/month) is the fallback.

---

### A-005 — Polymarket US fee schedule remains stable through the observation window

**Status:** Monitoring
**Owner:** Ongoing; Section 9.6
**Source:** Section 2.2

**Description:** The `fees.json` fee schedule (Θ_taker=0.05, Θ_maker=0.0125, 50% promotional taker rebate through April 30 2026) is treated as stable for the duration of the project. A fee change alters `breakeven.json` and ends the current observation window.

**Validation plan:** Monitor Polymarket US announcements. The nightly commitment-file checksum (Section 5.8) makes any unintended modification to `fees.json` immediately detectable. A legitimate fee change is handled per Section 9.6: window ends, `breakeven.json` re-derived, new window opens.

---

## Issues

Issues are problems that currently exist and require resolution. Unlike risks, they are not uncertain future events — they are known now. An issue without a resolution plan is a blocking item.

---

### I-001 — Sports WS point-level granularity is unconfirmed

**Severity:** 7
**Status:** Open — Phase 1 verification required
**Owner:** Phase 1; D-003
**Source:** Section 11.1; D-003

**Description:** The highest-leverage signal states (break points, deuces) depend on point-level score granularity in the Sports WebSocket. This has not been verified against live capture. The instrument cannot be designed with confidence in its signal leverage until this is resolved.

**Resolution plan:** Phase 1 live capture test per D-003. Gate decision surfaced to operator before Phase 2. Issue closes when the operator issues a go/no-go/defer ruling and it is logged to the DecisionJournal.

---

### I-002 — GitHub repository does not exist

**Severity:** 5
**Status:** Open — Phase 1 setup
**Owner:** Phase 1
**Source:** STATE.md (`repo.exists: false`)

**Description:** No Git repository exists for the project. Scaffolding files (STATE.md, Playbook.md, SECRETS_POLICY.md, DecisionJournal.md, RAID.md, and the files being produced in H-003) cannot be committed or version-controlled until the repo is created.

**Resolution plan:** GitHub + Render setup walkthrough, the next work package after H-003 scaffolding is complete. Operator creates the repo via the GitHub web UI following a step-by-step runbook Claude produces. Issue closes when `repo.url` is populated in STATE.md and at least one commit exists.

---

### I-003 — Plan document pending revisions (D-002, D-003)

**Severity:** 3
**Status:** Open — tracked in STATE
**Owner:** Future plan-revision session; Playbook §12
**Source:** STATE.md `pending_revisions`; H-002

**Description:** Two decisions (D-002 and D-003) require updates to the v3 build plan document. D-002 affects Sections 8 Phase 7, 9, and 11. D-003 affects Sections 8 Phase 1 and 11.1. The plan and the governance artifacts are currently inconsistent; the governance artifacts govern where they disagree.

**Resolution plan:** A dedicated plan-revision session per Playbook §12. Non-blocking for scaffolding and Phase 1 code work; the STATE pending_revisions list makes the debt visible. Issue closes when the plan document is updated and the pending_revisions list in STATE is cleared for D-002 and D-003.

---

### I-004 — Commitment files do not exist

**Severity:** 4 (pre-Phase 1; not blocking scaffolding)
**Status:** Open — Phase 1 deliverable
**Owner:** Phase 1
**Source:** STATE.md `commitment_files`

**Description:** `fees.json`, `breakeven.json`, `signal_thresholds.json`, and `data/sackmann/build_log.json` do not exist. The nightly checksum health check, the observation-active lock mechanism, and the signal-evaluation logic all depend on these files.

**Resolution plan:** Produced as Phase 1 deliverables per the plan's Phase 1 acceptance criteria. Issue closes when all four files exist, their SHA-256 checksums are recorded in STATE.md, and the Phase 1 exit gate is passed.

---

### I-005 — DecisionJournal D-002 sub-questions unresolved

**Severity:** 3 (not blocking until Phase 7 exit)
**Status:** Open — to be resolved before Phase 7 exit gate
**Owner:** D-002; operator ruling required
**Source:** D-002; H-002 Section 4

**Description:** Four sub-questions on the pilot protocol remain open: pilot duration, calibration method, overfitting guardrails, and the no-tradeable-configuration branch. These are not blocking for Phases 1–6 but must be resolved before the Phase 7 exit gate, because the pilot protocol document is a Phase 7 exit gate requirement.

**Resolution plan:** Operator rules on each sub-question at or before the Phase 7 exit gate. Claude then produces the pilot protocol document as a pre-commitment artifact before any pilot data is collected. Issue closes when the pilot protocol document is accepted and committed.

---

## Dependencies

Dependencies are external conditions the project relies on that are outside the project's direct control.

---

### DEP-001 — Polymarket US public API availability

**Status:** Active
**Owner:** Ongoing; Section 12.1
**Source:** Section 5.2

**Description:** The project depends on continued availability of three Polymarket US public endpoints: the Gamma REST API, the CLOB WebSocket, and the Sports WebSocket. Authentication, rate limits, endpoint URLs, and schema may change without notice.

**Management:** Envelope stores raw messages to absorb schema changes without re-parsing. Rate-limit response headers are logged. Quarterly taxonomy review. Fee-schedule changes trigger window-close per Section 9.6.

---

### DEP-002 — Sackmann tennis archives (Creative Commons)

**Status:** Active
**Owner:** Phase 1
**Source:** Section 4.2

**Description:** The project depends on Jeff Sackmann's `tennis_slam_pointbypoint` and `tennis_pointbypoint` GitHub archives, licensed CC BY-NC-SA 4.0. The P(S) lookup tables are built from these archives at Phase 1 and are static thereafter. Future archive updates are available but the project does not depend on receiving them.

**Management:** Archives are cloned at Phase 1 and the actual data cutoff is recorded in `build_log.json`. Post-build refinement re-calibrates against the instrument's own live archive once sufficient matches accumulate, reducing forward dependence on the Sackmann archive.

---

### DEP-003 — Render PaaS service continuity

**Status:** Active
**Owner:** Phase 1 setup; ongoing
**Source:** Section 1.5.1

**Description:** The backend capture worker, API, and scheduled jobs run on Render. A Render platform incident, pricing change, or policy change could interrupt the project.

**Management:** Phase 7 monitoring and watchdog alert on service degradation. Archive is backed up nightly to a separate object storage provider, providing a restoration path if the Render service must be migrated.

---

### DEP-004 — GitHub repository accessibility

**Status:** Pre-active (repo does not exist yet)
**Owner:** Phase 1
**Source:** D-005

**Description:** The public GitHub repository is the source of truth for all project code and documentation, and the trigger for Netlify and Render automatic deploys. GitHub service outages or account issues would block deploys.

**Management:** Operator maintains the GitHub account with a payment method on file (free tier is sufficient). Code committed to the repo is also present in the Render and Netlify deploy environments, so a short GitHub outage does not interrupt the running service — only new deploys.

---

### DEP-005 — Netlify frontend hosting

**Status:** Pre-active (site not yet created)
**Owner:** Phase 5
**Source:** Section 6.4

**Description:** The live dashboard runs on Netlify. A Netlify outage or account issue would make the dashboard unavailable during the observation window.

**Management:** The dashboard is a read-only display and trade-logging surface; a Netlify outage during observation does not stop the capture service. The operator can log trades manually and reconcile at end-of-day per Section 7.2. A Netlify outage extending beyond one day during active observation is a material disruption and would need manual fallback logging.

---

### DEP-006 — Polymarket US funded account and iPhone app

**Status:** Active
**Owner:** Operator; ongoing
**Source:** Section 2.3; Section 1.5.3

**Description:** All trade execution depends on the operator's funded Polymarket US account and the iPhone app. Account suspension, funding shortfall, or app unavailability would stop trading during the observation window.

**Management:** Operator is responsible for maintaining a funded account per Section 1.5.3. Account credentials are never shared with Claude. The project has no recovery path for account suspension — this is an operator responsibility.

---

*End of RAID.md — v1, H-003.*
*Add new entries at the top of the relevant section with the next sequential ID.*
*Update `Status` fields in place; add a one-line `Update (date):` note below the field when status changes.*
