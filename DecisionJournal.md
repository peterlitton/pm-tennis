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

*End of DecisionJournal.md — formal rebuild, H-003.*
*Next entry will be D-009 or a gate verdict, whichever comes first.*
