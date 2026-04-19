# PM-Tennis — Decision Journal

This document records every non-trivial decision made during the PM-Tennis project, with enough reasoning for future-Claude (and future-operator) to understand the *why* behind each choice. Per Section 1.5.4 of the build plan, Claude logs decisions at the moment they are made. Per the session-close ritual (Playbook §2), the operator's gate verdicts and out-of-protocol acknowledgements are also recorded here.

The Decision Journal is a project artifact, not a session summary. It accumulates across all sessions without deletion or revision. Its value is cumulative — a reader arriving late in the project can reconstruct the reasoning behind every choice without consulting session transcripts.

---

## Conventions

- **Sequential IDs.** Each decision has a unique sequential ID (D-001, D-002, ...). IDs are never reused, never skipped, and never reassigned.
- **Reverse chronological order.** Newest decisions appear at the top so that the most recent context is immediately visible at session open.
- **No in-place revision.** Decisions are not edited after the fact. If a decision is changed or overridden, a new entry is added referencing the prior ID. The prior entry receives a one-line note at the bottom: `SUPERSEDED BY D-xxx (date)`. The original reasoning is preserved in full.
- **Gate verdicts.** When the operator passes or fails a phase-exit gate, the verdict is logged here at the top of the session following the gate, before any new work begins. Format: `Gate verdict: [Phase N exit] — [PASS / FAIL / DEFER] — [date] — [brief rationale]`.
- **Out-of-protocol events.** Every out-of-protocol invocation is logged here, in addition to the session handoff's self-report section. Format is given in D-004.
- **Entry structure.** Each entry carries: date, session ID (handoff ID), type tag, the decision, what was considered, the reasoning, and the commitment the decision creates. Sub-questions that remain open are listed explicitly and resolved by a later entry or a sub-ruling.
- **Reconstructed entries.** An entry may be marked "Reconstructed" when it was journaled in a later session from handoff sources rather than at the moment of decision. Reconstructed entries carry both a decision date and a journaling date; their Source line names the authoritative material used.

---

## D-022 — Ruling 5: commit cadence for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Governance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (menu paste in H-010 session opening, Ruling 5).

**Decision:** Periodic commits within a deliverable are permitted; a handoff is required at session end. This matches the commit cadence used during Phase 2.

**Considered:**
- (a) One commit per deliverable; handoff required before each commit
- (b) One commit per deliverable; handoff required only at session end
- (c) Periodic commits within a deliverable are fine; handoff required at session end
- (d) Something else

**Reasoning (operator):** "Same cadence used for Phase 2 (which succeeded). The H-008 problem was the missing handoff, not the number of commits."

**Commitment:** Intra-deliverable commit pacing is a judgment call for the work being done. The hard requirement is Playbook §2 session-close and R-011 proactive-handoff discipline. The attempt-1 failure is addressed by the handoff rule, not by restricting commit frequency.

---

## D-021 — Ruling 4: testing posture for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Quality

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 4).

**Decision:** Each deliverable is tested with unit tests plus a lightweight live smoke test before it is considered complete.

**Considered:**
- (a) Unit tests only; live validation deferred to the Ruling 3 checkpoint
- (b) Unit tests plus a lightweight live smoke test on one match or one asset before the deliverable is considered complete
- (c) Live-first — thinnest working version against real data, validate by inspection, then add tests
- (d) Something else

**Reasoning (operator):** "Addresses the specific attempt-1 failure mode (tests passed, live operation failed) without reversing the testing pyramid."

**Commitment:** No Phase 3 attempt 2 deliverable is declared complete on unit-test evidence alone. A live smoke test is part of the completion bar. The live smoke test is narrower than the Ruling 3 checkpoint (one match / one asset / one connection is sufficient); the Ruling 3 checkpoint is the broader acceptance event.

---

## D-020 — Ruling 3: definition of done for the first deliverable

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Acceptance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 3, including the adjustment note for the asset-cap stress test).

**Decision:** The first deliverable of Phase 3 attempt 2 is accepted when (1) unit tests pass, (2) the operator has reviewed the code, and (3) a single live verification has run against the actual Polymarket US gateway. Because the first deliverable is the asset-cap stress test (D-018), the single-live-verification language is adjusted per the operator's menu note: **the stress test runs to completion against the actual gateway with the actual asset count we expect.** "Actual asset count we expect" is the asset count implied by current discovery volume under the subscription-unit interpretation established by the Phase 3 attempt 2 research document; it is not a pre-guessed number.

**Considered:**
- (a) Unit tests + operator code review + single live poll/connection against one real market
- (b) (a) plus a 1-hour unattended test
- (c) (a) plus a manual walkthrough of the admin UI surfaces
- (d) Something else

**Reasoning (operator):** "Unit-tests-only missed the H-008 failure; live verification on one real market catches it without requiring hours of unattended runtime."

**Commitment:** The Ruling 3 checkpoint is a per-deliverable acceptance event distinct from the Phase 3 exit gate. The Phase 3 exit gate (48-hour unattended run, pool stale-connection handling, Sports WS retirement handler, handicap median, asset-cap stress test, first-server identification) remains the eventual target; Ruling 3 is the interim bar each deliverable clears. The first-deliverable live verification is the stress test itself running to completion; there is no separate "single live connection" step layered on top.

---

## D-019 — Ruling 2: research-first form for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Governance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 2). Implements D-016 commitment 2 (research-first discipline for external APIs and cross-module symbols).

**Decision:** Research that concerns external endpoints or cross-module symbols is produced as a **standalone research document** first. Operator reviews the document. Code begins in a subsequent Claude turn only after the review.

**Considered:**
- (a) Standalone research document first, operator reviews, then code begins in a subsequent Claude turn
- (b) Research produced inline, operator spot-checks each citation, code begins immediately after each research block is accepted
- (c) Operator supplies the documentation links; Claude works strictly from supplied material and refuses to use anything else

**Reasoning (operator):** "Maximum distance from the H-008 fabrication pattern."

**Commitment:** The research-document-then-code sequencing applies for the duration of Phase 3 attempt 2 unless explicitly lifted. Each research document goes through operator review before the turn that begins the corresponding code. Hybrid — operator supplies links during a research turn — is compatible with (a) and does not constitute a switch to (c). A switch to (b) or (c) for a specific deliverable requires a new ruling and a new DecisionJournal entry.

---

## D-018 — Ruling 1: first deliverable of Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Scope / Sequencing

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 1).

**Decision:** The first deliverable of Phase 3 attempt 2 is the deferred CLOB asset-cap stress test from Phase 1 (RAID I-002). Other Phase 3 components (CLOB pool, Sports WS client, correlation layer, handicap updater) follow after the stress test resolves pool sizing.

**Considered:**
- (a) CLOB WebSocket pool
- (b) Sports WebSocket client
- (c) Correlation layer
- (d) Handicap updater
- (e) Deferred CLOB asset-cap stress test (I-002)
- (f) Something else

**Reasoning (operator):** "Resolving the sizing question first determines how the CLOB pool gets built and avoids redoing pool design later."

**Commitment:** The asset-cap stress test runs before the CLOB pool is built. The "soft 150-asset cap" referenced in plan §5.4 and §11.3 is verified empirically against the Polymarket US CLOB service before any long-lived pool code is written. The stress-test design is scoped by the Phase 3 attempt 2 research document (v1 produced this session; v2 pending §4 external research).

---

## D-017 — v3→v4 plan revision (retroactive journaling)

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Plan revision / Retroactive entry

**Source:** Reconstructed H-009 from Handoff_H-006.md §2. The decision was labeled "D-008" in H-006's handoff before the numbering conflict with the pre-existing D-008 (Section 1.5 forward references, H-002) was identified at the same session by D-012. D-012 resolved the numbering policy but did not retroactively assign a canonical ID to the plan-revision decision itself. D-017 closes that gap per Playbook §12.3 step 6, which requires a DecisionJournal entry for every plan revision.

**Decision:** Produce v4 of the PM-Tennis Build Plan; premise shift from mispricing-test to instrument-vs-intuition test.

**Motivating evidence:** Baseline analysis of 71 Polymarket US iPhone screenshots (502 cash events, 131 resolved tennis contracts excluding STENAP/TRISCH) showing operator ROI of +8.5% overall and +14.3% on swing trades, with effective swing win rate of 55.9% (vs 58.2% breakeven, p=0.697, statistically indistinguishable from breakeven). Analysis performed in an adjacent chat session on 2026-04-18.

**Chain of authorship:** Analysis adjacent → premise shift directed by operator → source artifacts (Premise Brief, Baseline Summary v2, Hypothesis Set v2, Injection Instruction v2) produced adjacent → v4 produced in H-006 under Playbook §12.

**Rationale for v4 rather than v3.x:** A premise-level shift requires one clean reading. Mixing v3's mispricing framing with v4 amendments would burden all downstream phases.

**Commitment:** v4 is the active build plan. v3 is preserved in git history. `STATE.project.plan_document.current_version = v4`.

**Downstream consequences (from H-006):**
- D-009 (H3 hypothesis dropped) — scope implication of the revised research question.
- D-010 (conviction scoring + exit context ship together at Phase 5) — new instrument features introduced by v4.
- D-011 (pilot-then-freeze deferred to Phase 7) — reserved decision slot carried forward from v3.
- D-012 (decision numbering corrected) — resolves the conflict that motivated this retroactive entry.

**Retroactive-journaling note:** This entry is dated 2026-04-19 (journaling date) but records a decision made 2026-04-18 (decision date). The dual dating is intentional per Playbook §1.5.2's reconstruction discipline.

---

## D-016 — Phase 3 attempt 1 failed; revert main to pre-attempt state and begin Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-009
**Type:** Recovery / Governance

### What happened

Between H-007 session close and the beginning of H-009, a session occurred (labeled H-008 for handoff-sequence integrity, though no handoff was ever produced) in which Phase 3 capture components were authored, tested, committed to the repo on main, and deployed. The commits are visible in git history, timestamped 2026-04-19 02:11:12Z through 02:18:56Z:

- `677016c1` — src/capture/clob_pool.py (10.9 KB)
- `a10486b3` — src/capture/correlation.py (12.2 KB)
- `00282260` — src/capture/sports_ws.py (18.1 KB)
- `bab716ef` — src/capture/handicap.py (8.6 KB)
- `d319e09e` — main.py rewritten (12.0 KB) to wire all components
- `8bdc3859` — tests/test_capture_phase3.py (23.4 KB)
- `40973377` — pytest.ini (asyncio_mode=auto)

After deployment, the code began failing in live operation. Per operator's explanation at session H-009: *"Claude failed to read the documentation thoroughly and made up a placeholder URL for live Sports WS. Trying to correct it in that session just made it worse."* The session ended without producing a handoff document or an updated STATE.md. The operator subsequently deleted the session transcript.

### The fabrication pattern

During H-009 revert validation (V4 log scan), Render runtime logs surfaced a second fabrication from the failed session: `main.py` at `d319e09e` contained the import `from src.capture.discovery import DiscoveryLoop, DiscoveryConfig`. The `DiscoveryConfig` class does not exist in `discovery.py` (which was unchanged from H-007). Claude assumed a symbol existed in an unmodified file. The service crash-looped with `ImportError: cannot import name 'DiscoveryConfig' from 'src.capture.discovery'` from 03:10:11Z through 03:13:20Z (six documented ImportError events during the delete phase of the revert transaction).

Two fabrications in one failed session, of different kinds:
1. An external endpoint URL (Sports WS) fabricated rather than researched against documentation.
2. An internal module symbol (`DiscoveryConfig`) assumed to exist in an existing-but-unmodified file.

The common failure mode is: writing code that references names Claude never verified exist.

### What is recoverable and what is not

Recoverable: the code itself (present in git history), the commit timestamps and messages, the order of commits, the general shape of what was attempted, the ImportError evidence from Render logs.

Not recoverable: the exact fabricated Sports WS URL, what it was "corrected" to during the attempted fixes, the specific failure signatures beyond the ImportError, the reasoning at each decision point during the session, and any intermediate diagnostic output.

### Root causes (as stated and as observed)

Stated by operator: Claude fabricated an endpoint URL for the live Sports WebSocket rather than researching the actual endpoint from Sportradar or Polymarket US documentation. Attempting to correct the URL in-session without returning to documentation compounded the failure.

Observed during H-009 revert validation: also an internal-symbol fabrication (`DiscoveryConfig`). This is the same failure class as the URL fabrication — writing code that presumes a name exists without verifying it does.

Both are direct violations of build plan §1.5.4 ("Claude shall not silently adapt to unexpected findings") and of the research-first discipline that should govern any external-API integration work or cross-module coupling.

### Ruling by operator at H-009

1. **Option A1 adopted.** Revert main to its state at commit `c63f7c1d` (the last commit before the Phase 3 attempt, dated 2026-04-19 01:46:44Z, message "fix: discovery task catches all exceptions and retries"). Remove the five new Phase 3 files (clob_pool.py, sports_ws.py, correlation.py, handicap.py, test_capture_phase3.py) and pytest.ini; restore main.py to its c63f7c1d content. Approach executed through GitHub web UI, walked through with Claude step by step.

2. **Tripwire classification:**
   - **Tripwire 1** (integrity discrepancy between STATE/handoff and repo): real, caused by missed session-close ritual at H-008. No governance breach in the commits themselves; STATE v6 and handoff H-007 are stale because H-008 never produced its handoff.
   - **Tripwire 2** (out-of-session commits per Playbook §10): false positive, withdrawn. Commits were legitimate in-session outputs of H-008.
   - **Tripwire 3** (DecisionJournal gap D-009 through D-015): real, predates H-008, independent of the failure. Addressed in H-009 via reconstruction from handoff sources (D-009 through D-012 from H-006; D-013 through D-015 from H-007), each entry flagged as reconstructed per Playbook §1.5.2.

3. **Commit-message variance note.** The five delete commits in the revert transaction were committed with GitHub's default `"Delete <filename>"` messages (plus a free-form `"Claude fuck up"` tag added by the operator) rather than the structured `"revert: remove failed Phase 3 <file> (N/7)"` format Claude had drafted. The `main.py` restore commit (`17f44eb1`) used the structured format. The seven-commit revert transaction remains unambiguously identifiable in the git log by timestamp cluster (03:08:45Z–03:17:11Z) and by the "(7/7)" tag on the main.py restore. No action needed; noted for future-Claude reading the log.

### Revert validation outcomes (H-009)

Seven validation checks were performed after the revert commits landed:

- **V1** — 38 `meta.json` files present on persistent disk. ✓
- **V2** — `meta.json` well-formed, contains expected fields and `PENDING_PHASE3` stubs. ✓ (with two documentation notes: participant type observed is `PARTICIPANT_TYPE_TEAM` not `PARTICIPANT_TYPE_PLAYER` as H-007 claimed; `sportradar_game_id` empty across all 38 events, consistent with no-live-matches context.)
- **V3** — discovery delta stream being written, daily raw-poll archive being written. ✓ (with one informational note: raw-poll archive grows ~290 MB/day uncompressed, which has runway implications before Phase 4 compression arrives.)
- **V4** — No ERROR / WARN / Traceback in Render logs after the 03:18:49Z revert deploy. ✓
- **V5** — Build log confirms `pip install -r requirements.txt` installed full dependency set (fastapi, uvicorn, pandas, numpy, pyarrow, requests, scipy, httpx). ✓
- **V6** — Environment variables minimal and expected (ENVIRONMENT, LOG_LEVEL, PM_TENNIS_TOKEN). No failed-attempt leftovers. ✓
- **V7** — `/data` mounted as real persistent volume (`/dev/nvme2n1`, 9.8 GB, ~35 MB used). ✓

### Commitments created by this decision

1. **Phase 3 attempt 2 begins from c63f7c1d-equivalent repo state.** No code from the failed attempt carries forward into attempt 2. Phase 3 design choices do not inherit from attempt 1.

2. **Research-first discipline for all external APIs and cross-module references.** Before any code is written for Phase 3 attempt 2 that (a) calls an external endpoint, or (b) imports a symbol from a module that is not being concurrently modified, Claude produces a short research summary citing the actual documentation source (for endpoints) or the actual module definition (for symbols). Fabrication of URLs, endpoint shapes, message formats, authentication schemes, module names, class names, or function signatures is a tripwire. This applies at minimum to the Sports WebSocket endpoint (the specific URL failure point), the CLOB WebSocket subscription format, correlation metadata shape, and any symbol imported from `src.capture.discovery` or other pre-existing modules.

3. **Session-close ritual discipline.** The missed handoff at H-008 is the proximate cause of the governance debris H-009 cleaned up. Future sessions that end before Claude can produce a handoff voluntarily apply Playbook §2.5.2: Claude proactively offers to produce the handoff when the session seems near close, rather than waiting for explicit close request. If a session ends abruptly mid-task, the next session treats the prior session's missed handoff as a Failure-mode-1.5.2 lost-handoff event and reconstructs per §9.3.

4. **H-009 produces no new Phase 3 code.** Its entire output is the revert transaction, the DecisionJournal reconstruction (D-009 through D-015) plus this entry (D-016) plus the retroactive plan-revision entry (D-017), STATE v7, RAID updates, and handoff H-009. Phase 3 attempt 2 begins in H-010 or later.

### What this session does not decide

This entry does not prescribe the technical approach for Phase 3 attempt 2. Sub-deliverable sequencing, module structure, testing strategy, first deliverable — all remain open for operator direction at the start of the next Phase 3 session.

---

## D-015 — Tennis sport slug confirmed as "tennis"

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Technical verification / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The Polymarket US gateway uses sport slug `"tennis"` with leagues `["wta", "atp"]`. The default value in `TENNIS_SPORT_SLUG` is correct and requires no override.

**Confirmed by:** Live gateway response at startup during H-007, logged at INFO level. Re-confirmed during the 03:18:49Z revert deploy startup in H-009: `✓ MATCH — sport slug='tennis' name='Tennis' leagues=['wta', 'atp']`.

**Commitment:** Discovery module's tennis-slug default stands. No override file needed.

---

## D-014 — Discovery loop runs inside pm-tennis-api, not as a separate service

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Architecture / Deviation from plan / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The discovery background task runs as an asyncio task inside the FastAPI process on pm-tennis-api, not as a separate Render background worker service.

**Rationale:** Render persistent disks are per-service and cannot be shared between services. Running discovery inside the API service ensures both read and write access to the same `/data` disk. A separate background worker service was created and deleted during H-007 after this constraint was discovered empirically.

**Consequence:** pm-tennis-api serves two roles: HTTP API (Phase 4 will expand this) and continuous discovery worker. Represents an architectural deviation from the build plan's implied service separation, justified by the disk-sharing constraint.

**Commitment:** Capture worker and API share a process. Phase 3 attempt 2 and later phases inherit this architecture.

---

## D-013 — Polymarket US gateway is the correct API target

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Technical / Scope / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The discovery module polls `gateway.polymarket.us` (Polymarket US public API), not `gamma-api.polymarket.com` (offshore Polymarket). These are separate products with separate API structures.

**Rationale:** Build plan Section 1.2 is explicit that the offshore Polymarket product is out of scope. The Polymarket US public gateway requires no authentication for read operations.

**Endpoints confirmed:**
- `GET /v2/sports` — enumerate sports, verify tennis slug
- `GET /v2/sports/{slug}/events` — paginated event discovery

**Commitment:** All Polymarket endpoints used by this project come from `gateway.polymarket.us` (read) and, when trading actions are eventually needed, from `api.polymarket.us`. Offshore URLs are out of scope permanently.

---

## D-012 — Decision numbering corrected

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Governance / Bookkeeping / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The Injection Instruction's references to "D-002 pilot-then-freeze" and "D-003 Sports WS gate" were build-plan internal labels, not canonical RAID/STATE decision IDs. Canonical numbering (D-001 through D-007 per STATE.md) is authoritative. The v3→v4 revision and related decisions are assigned D-008 through D-011 in H-006 (with D-017 later retroactively journaling the plan-revision decision itself).

**Reasoning:** Prevents ambiguity between in-document cross-references and canonical DecisionJournal IDs.

**Commitment:** All future DecisionJournal IDs derive from this journal, not from plan-internal references.

---

## D-011 — Pilot-then-freeze protocol deferred to Phase 7

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Pre-commitment / Scheduling / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The pilot-then-freeze protocol for `signal_thresholds.json` is a Phase 7 decision. v4 notes it as a placeholder. Full specification and formal ID assignment at Phase 7.

**Reasoning:** Operator comfortable with deferral; no content yet to commit. The pilot protocol is itself a pre-commitment artifact and must be written before any pilot data is inspected.

**Commitment:** Phase 7's exit gate adds a requirement for a pilot protocol document. This entry reserves the decision slot.

---

## D-010 — Conviction scoring and exit context ship together at Phase 5

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Scope / Scheduling / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** Build plan Sections 4.6 (Conviction Scoring) and 4.7 (Exit Context) are parallel instrument features, both shipping at Phase 5. No staged rollout.

**Reasoning:** Both derived from the same fair-price computation; they serve the same operator-decision moment.

**Commitment:** Phase 5 deliverables include both features simultaneously. Neither may ship without the other.

---

## D-009 — H3 hypothesis dropped

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Scope / Research question / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The hold-strategy rehabilitation hypothesis (H3) is permanently dropped from v4 and all future plan documents.

**Reasoning:** Operator direction. Not to be raised again.

**Commitment:** v4 tests H1 and H2 only. H3 is not a candidate for reinstatement.

---

## D-008 — Section 1.5 forward references are aspirational; scaffolding realizes them

**Date:** 2026-04-18
**Session:** H-002
**Type:** Governance confirmation

**Decision:** Section 1.5 of the build plan references project assets (DecisionJournal, RAID log, STATE.md, PreCommitmentRegister, OBSERVATION_ACTIVE lock, runbooks) that did not exist at the time Section 1.5 was written. The operator confirmed this is acceptable as an aspirational governance posture. The scaffolding work in H-002 and H-003 makes those references concrete.

**Considered:** (a) Treat Section 1.5's references as binding from day one and block progress until all referenced artifacts exist; (b) treat them as aspirational and build the artifacts to match them as scaffolding progresses. Option (a) is circular — the artifacts cannot exist until they are built, and the governance model cannot govern their construction if it does not exist. Option (b) is the only workable path.

**Reasoning:** Section 1.5 was written to lock in the governance model before the assets existed. Writing the governance posture first and building the artifacts to match it is the correct sequencing — the alternative (build assets first, write governance after) risks the assets diverging from the intended model. The posture is acknowledged explicitly so that neither party is confused when Section 1.5 names an asset that is still being built.

**Commitment:** The scaffolding files produced in H-002 and H-003 must faithfully implement Section 1.5's described behavior. If a scaffolding file diverges from Section 1.5, the divergence is surfaced and either the file or Section 1.5 is corrected — silent divergence is not acceptable.

---

## D-007 — Session-open self-audit block is included

**Date:** 2026-04-18
**Session:** H-002
**Type:** Protocol

**Decision:** On handoff acceptance at the start of every session, Claude produces a visible self-audit block documenting: the handoff ID received, what repo files (or uploaded files) were checked against the handoff's claimed modifications, commitment-file checksums compared against the handoff's record (once those files exist), any inconsistencies found, and an explicit orientation statement (current phase, current work package, next action).

**Considered:** (a) Self-audit block on every session-open, produced by Claude and visible in the chat; (b) operator-only audits via unprompted spot-checks with no claim-side audit from Claude. Option (b) relies entirely on operator vigilance and is unverifiable without something to check against. Option (a) adds a visible surface on every session that can itself be checked against the handoff and the repo state — it is auditable.

**Reasoning:** The operator noted in H-001 that drift is a real risk and that Claude's prior pattern of skipping process is a known failure mode. Making the audit visible at session start raises the cost of drift to Claude (a missing or sparse self-audit is itself a red flag the operator can catch on review) and gives the operator a consistent artifact to spot-check. Spot-checks still happen on top of this; the self-audit is not a substitute.

**Commitment:** Every session handoff acceptance includes a self-audit block. The block must list at minimum: handoff ID received, files checked, any inconsistencies found, and the orientation statement. A missing or perfunctory self-audit is a protocol violation that must be flagged in that session's handoff self-report.

---

## D-006 — Handoff carrier is markdown files

**Date:** 2026-04-18
**Session:** H-002
**Type:** Process

**Decision:** Handoff documents are transported between sessions as markdown files. Claude produces a `Handoff_H-NNN.md` at session end. The operator saves or downloads it and pastes or uploads it at the start of the next session.

**Considered:** (a) Markdown files produced by Claude; (b) copy-paste into a personal note system; (c) auto-sync via a third-party tool. Option (c) adds an external dependency and a new failure surface. Option (b) is workable but degrades when the operator changes note systems or copy-pastes incorrectly. Option (a) keeps the handoff as a self-contained file that can be committed to the repo once the repo exists, reviewed as a document, and re-uploaded cleanly.

**Reasoning:** Markdown is the existing project documentation format. A single consistent format removes the conversion step and keeps handoffs compatible with the repo and the rest of the project artifacts. Handoff files in the repo also serve as a complete session audit trail.

**Commitment:** Claude produces `Handoff_H-NNN.md` at session end. Operator preserves it and provides it at the next session start. A lost handoff is an operator responsibility and cannot be reconstructed by Claude — though prior session transcripts may allow the operator to reconstruct one manually.

---

## D-005 — Repo access model is a public GitHub repository

**Date:** 2026-04-18
**Session:** H-002
**Type:** Infrastructure / Security

**Decision:** The project's Git repository is a public GitHub repository. Claude accesses repo contents via the public GitHub URL when the operator provides it, or via operator-uploaded file batches when files are being actively worked on. No read-only tokens or per-session credential sharing is required.

**Considered:** (a) Public repo; (b) private repo with a read-only personal access token shared per session; (c) operator re-uploads key files at the start of each session. Option (c) is high-friction and error-prone — the operator must remember which files are current. Option (b) adds credential management per session and is the kind of friction that causes protocol drift. Option (a) is the lowest-friction model but imposes a hard constraint on what may be committed.

**Reasoning:** A public repo forces secrets discipline that is desirable regardless — no credentials, API keys, Polymarket account identifiers, or personal data may ever land in the repo. Environment variables in the hosting platforms' web UIs (Render, Netlify) hold all secrets; the code that reads them by name is public but does not contain the values. The project's subject matter (a personal trading instrument built around a public exchange's public feeds) is not itself sensitive. The strategy specifics are, but the plan already commits to transparency of the commitment files.

**Commitment:** No secrets in the repo, ever. `SECRETS_POLICY.md` (produced H-002) specifies what counts as a secret, where secrets live, and what the audit procedure is. Any commit that would introduce a secret is a tripwire event refused by Claude and flagged for operator review.

---

## D-004 — Out-of-protocol trigger phrase is "out-of-protocol"

**Date:** 2026-04-18
**Session:** H-002
**Type:** Governance

**Decision:** When the operator begins a request with the literal phrase "out-of-protocol", the usual full protocol is suspended for that specific task. The phrase must appear at the start of the request to be recognized as a governance signal.

**Considered:** Candidate phrases: "out-of-protocol", "quick fix", "OOP", or operator's choice of any phrase. "OOP" is brief but less mnemonic and could appear incidentally in technical context. "Quick fix" describes the situation type rather than the governance signal, making it ambiguous when the operator says it in passing conversation. "Out-of-protocol" names what it does, is unambiguous, and is unlikely to appear by accident in any other project context.

**Reasoning:** The phrase needs to be: (1) distinctive enough that it cannot appear by accident, (2) explicit about what it signals, and (3) consistent across sessions so Claude can reliably detect it without ambiguity. "Out-of-protocol" meets all three criteria. The cost of false negatives (operator forgets the phrase) is a mild friction. The cost of false positives (Claude incorrectly suspends protocol) is drift, which is the more dangerous failure mode, so the bar for detection is set high.

**Commitment:** Every out-of-protocol invocation is logged in two places: (1) the session handoff's Claude self-report section, and (2) a new entry in this DecisionJournal citing the OOP phrase, the request made, the work performed, and any rules that were suspended. The `OBSERVATION_ACTIVE` soft lock is unconditional and is **not** overridable by "out-of-protocol" — if an OOP request would modify a commitment file during an active observation window, Claude refuses and surfaces the Section 9.6 rule regardless of OOP invocation.

---

## D-003 — Sports WebSocket granularity is a go/no-go gate, not a silent downgrade

**Date:** 2026-04-18
**Session:** H-002
**Type:** Technical / Decision criterion

**Decision:** Phase 1's Sports WebSocket granularity verification is an explicit go/no-go gate surfaced to the operator. If point-level data is confirmed on the public Sports WebSocket, the project proceeds as planned. If only game-boundary transitions are emitted, Claude stops, produces an assessment of which signal classes survive the game-level coarsening, and the operator rules go / no-go / defer before Phase 2 begins. The operator's ruling is logged to the DecisionJournal before Phase 2 starts.

**Considered:** The plan as originally written (Section 11.1, severity 7) treated the game-level fallback as "weaker thesis but still viable" and allowed silent continuation. Claude's review pushed back: break-point and deuce transitions carry the highest log-odds evidence in the model, and these are exactly the transitions lost if granularity is game-level only. The thesis's most leveraged signal class is therefore the one most likely to be unavailable under the fallback.

**Reasoning:** A silent downgrade risks the observation window being run on an instrument that cannot observe the states the thesis most depends on. The operator cannot evaluate that tradeoff if Claude handles it silently. Making it an explicit gate preserves the operator's ability to decide whether a game-level instrument is worth building and running, or whether the project should pause or redirect.

**Commitment:** Phase 1's acceptance criteria must include this gate explicitly. The plan document's Section 8 Phase 1 and Section 11.1 are queued for update under the doc-code coupling rule (tracked in STATE's `pending_revisions` block). The update is applied when the plan text is next revised.

---

## D-002 — Signal-threshold derivation uses a pilot-then-freeze protocol

**Date:** 2026-04-18
**Session:** H-002
**Type:** Decision criterion / Pre-commitment

**Decision:** Between Phase 7 completion and the opening of the observation window, a pilot phase calibrates the values in `signal_thresholds.json` against archive data accumulated by the instrument. At pilot end, thresholds are frozen, `OBSERVATION_ACTIVE` is engaged, and the 250-signal / 60-day window clock starts. Pilot data is excluded from the window.

**Considered:** (a) Keep the plan's committed guesses (X=0.08 etc.) and acknowledge the weakness; (b) pilot-then-freeze; (c) skip pre-committed thresholds entirely and run the window as a threshold-sweep exploration. Option (a) weakens the Bayesian pre-commitment discipline — the window protects against in-window tuning but not against the plan being wrong at the start in a way that makes the window uninformative. Option (c) sacrifices falsification discipline entirely. Option (b) preserves both: the pilot calibrates, the freeze preserves pre-commitment, the pilot-data exclusion keeps the window independent.

**Reasoning:** The plan's Section 9 pre-commitment model depends on thresholds that are grounded in data, not arbitrary. Arbitrary starting thresholds create a real risk that an otherwise-valid thesis fails the window due to miscalibrated thresholds — or passes due to thresholds that happened to work on the pilot data. The pilot-then-freeze protocol separates calibration from evaluation, which is the same principle that separates training from test in predictive modeling.

**Open sub-questions (not decided in H-002; to be resolved before the pilot begins, i.e., before Phase 7 exit gate):**
1. **Pilot duration** — calendar time (e.g., 14 days), data volume (e.g., first 500 qualifying events), or both with a bound?
2. **Calibration method** — grid search over thresholds risks overfitting to pilot noise; alternatives include cross-validated search, a coarse pre-specified discrete grid with committed resolutions, or expert-judgement calibration against summary statistics only.
3. **Overfitting guardrails** — how to ensure pilot thresholds generalize to the window. Candidates: hold out part of the pilot data, pre-commit to a small set of candidate threshold tuples and select only among them.
4. **No-tradeable-configuration branch** — if the pilot reveals no threshold tuple that passes the breakeven bar under reasonable assumptions, the project pauses rather than proceeding with uncalibrated thresholds.

**Commitment:** Phase 7's exit gate adds a requirement: a pilot protocol document must exist and be accepted by the operator before the pilot begins. The pilot protocol is itself a pre-commitment artifact — it must be written and committed before any pilot data is inspected, to prevent it from being tuned to pilot data. Plan Sections 8 (Phase 7), 9, and 11 are queued for update (tracked in STATE).

---

## D-001 — Development environment, roles, and governance model

**Date:** 2026-04-18
**Session:** H-001
**Type:** Foundational / Governance

**Decision:** Project is built end-to-end by Claude across discrete chat sessions, under direction of a single non-technical operator who uses no terminals, SSH, or command-line tools. Deployment uses a managed PaaS (Render) for backend, Netlify for frontend, GitHub for the repository. Governance operates on four layers: session protocol (handoff/accept ritual), gate-blocking language in acceptance criteria, named tripwires, and operator spot-checks. The session model requires a handoff produced at session end and accepted at session start; thin handoffs trigger stop-and-surface, not best-effort reconstruction. Claude's obligations are defined by the "shall" and "shall not" rules in Section 1.5.4. The observation-active soft lock via the `OBSERVATION_ACTIVE` file protects commitment files during windows unconditionally.

**Considered:** The plan's original assumption was a conventional developer-operator setup with a Hetzner VPS and SSH access. That assumption was replaced once the actual operator profile (non-technical, no terminal access) was established. PaaS options considered: Render, Railway, Fly.io. Fly.io was excluded because its setup uses a CLI, which conflicts with the no-terminal constraint. Railway and Render are both compatible; Render was chosen for its Netlify-like UI experience and predictable pricing.

**Reasoning:** A plan built for a developer-operator who doesn't exist creates silent failures when a non-technical operator tries to execute it. Section 1.5 was written at length to make the actual environment explicit before any code is written. The governance structure (four-layer model, tripwires, handoff protocol) was specified up front because prior multi-session AI-assisted projects have shown that protocol discipline degrades without explicit structure — naming the rules and naming the failure modes is the first line of defense.

**Commitment:** All downstream sections of the plan are interpreted under Section 1.5. Acceptance criteria requiring terminal access are not acceptable; every phase is responsible for building the web-UI surfaces that expose its diagnostics. Section 1.5.6 lists the specific downstream sections requiring reconciliation and assigns Claude responsibility for applying the reconciliation during the relevant phases.

---

*End of DecisionJournal.md — updated at H-009 session close.*
*Next entry will be D-018 or a gate verdict, whichever comes first.*
