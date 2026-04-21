# PM-Tennis Project — Playbook

This document is the procedures book for the PM-Tennis project. It contains the rituals that govern how work happens: how sessions open and close, how gates are adjudicated, how tripwires are handled, how the out-of-protocol mechanism is invoked, how commitment files are modified (or not) during observation, how the observation window opens and closes, and all the smaller procedures that the project needs to run consistently across sessions.

The Playbook is paired with **Orientation.md**, which describes the project's structure, files, and governance model at an onboarding level. Orientation is "what this project is and how it's organized." Playbook is "what you do, step by step, in each situation." A new reader reads Orientation first; a reader in the middle of a specific situation reaches for Playbook.

## How to use this document

Every ritual in this document has the same structure, for scannability and to make omissions visible:

1. **Name and scope** — what the ritual governs, and when it applies.
2. **Preconditions** — what must be true before the ritual can be performed.
3. **Procedure** — numbered steps, in order. Each step names who does it (Claude or operator) and what the output is.
4. **Postconditions** — what must be true after the ritual is complete. If any postcondition is not met, the ritual did not complete successfully.
5. **Failure modes** — specific ways this ritual can fail mid-procedure, and what to do in each case.
6. **Logging requirements** — what gets written where, and in what artifacts.

Some rituals have short entries in some sections (e.g., "preconditions: none" for rituals that apply unconditionally, or "failure modes: none specific to this ritual beyond the general ones" when the ritual is simple). The structure is preserved anyway, so that the reader sees the same five sections in every entry and can tell at a glance whether a section was intentionally short or accidentally omitted.

**Cross-references.** Rituals reference each other. The session-close ritual references the STATE update ritual; the gate-UAT ritual references the session-close ritual; the observation-window open ritual references the commitment-file freeze ritual. Rather than duplicating procedures, each ritual is written once and referenced as `[Playbook §N]` where N is the section number.

**Authority.** The Playbook is authoritative for procedures. If a procedure here conflicts with a procedure described elsewhere (in the plan's Section 1.5, in a handoff, in a chat transcript), the Playbook wins, and the conflict is surfaced for resolution. Changing a procedure requires a DecisionJournal entry and a new Playbook version.

---

## Table of rituals

1. [Session-open ritual](#1-session-open-ritual)
2. [Session-close ritual](#2-session-close-ritual)
3. [Gate-UAT ritual](#3-gate-uat-ritual)
4. [Tripwire-handling ritual](#4-tripwire-handling-ritual)
5. [Out-of-protocol invocation ritual](#5-out-of-protocol-invocation-ritual)
6. [Commitment-file modification ritual](#6-commitment-file-modification-ritual)
7. [Observation-window open ritual](#7-observation-window-open-ritual)
8. [Observation-window close ritual](#8-observation-window-close-ritual)
9. [Thin-handoff handling ritual](#9-thin-handoff-handling-ritual)
10. [Out-of-session commit ritual](#10-out-of-session-commit-ritual)
11. [Pending-operator-decision escalation ritual](#11-pending-operator-decision-escalation-ritual)
12. [Plan-document revision ritual](#12-plan-document-revision-ritual)
13. [Staging-push-and-merge ritual](#13-staging-push-and-merge-ritual)

---

## 1. Session-open ritual

### 1.1 Name and scope

The session-open ritual governs the opening of every Claude chat session on this project. It applies to every session without exception, including short check-in sessions, sessions opened to ask a single question, sessions that will end in a gate-UAT, and sessions following an out-of-protocol request. A session that begins substantive work without completing this ritual is in protocol violation.

### 1.2 Preconditions

- A prior session exists, or the project is in its very first session (H-001, which had no predecessor and therefore no handoff to accept).
- The operator has provided the prior session's handoff document in the opening message (pasted or uploaded as a markdown file), or — if this is the very first session — has stated explicitly that no handoff exists and the session is the project kickoff.
- STATE.md exists, or — if this is the very first session or STATE has been lost — Failure mode 1.5.2 applies.

### 1.3 Procedure

1. **Operator:** pastes the prior session's handoff into the opening message (or uploads it as a file), and states either "please accept the handoff and confirm orientation" or equivalent explicit request. Ambiguous openings ("hey, let's pick up where we left off") require Claude to ask for the handoff explicitly rather than assuming.

2. **Claude:** reads the handoff in full. Not just the next-action statement — every section, including files-modified, asset-status, open-questions, self-report, and next-action. Thin-handoff handling (§9) triggers here if applicable.

3. **Claude:** reads STATE.md in full — YAML block first, then prose commentary. Cross-references STATE against the handoff's claims. Any file the handoff claims was produced or modified should appear in STATE's scaffolding-files inventory with appropriate status. Any commitment-file SHA claim in the handoff should match STATE's YAML.

4. **Claude:** performs the self-audit and writes it as a visible block at the start of the response. The self-audit contains, at minimum:
   - Handoff ID received.
   - Expected handoff ID per STATE's `sessions.next_handoff_id`, and whether they match.
   - Scaffolding-files inventory spot-check (any mismatch between handoff claims and STATE listing).
   - Commitment-file SHA spot-check (once commitment files exist; trivially passing during pre-build).
   - Governance fingerprint spot-check (STATE's `governance` fields vs. DecisionJournal entries for D-004 through D-008; once DecisionJournal exists formally).
   - Any discrepancies found, with a proposed resolution or a request for operator direction.
   - Open-items summary: tripwire events currently open, RAID counts by severity, DecisionJournal open sub-questions, pending operator decisions.

5. **Claude:** confirms orientation as a short explicit statement immediately after the self-audit block. The orientation statement contains:
   - Current phase.
   - Current work package.
   - Last gate passed (or "none yet" if pre-gate).
   - Next gate expected.
   - The next-action from the handoff.
   - Any blockers to that next action (unresolved tripwires, pending operator decisions, open sub-questions that the next action depends on).

6. **Claude:** updates `sessions.next_handoff_id` in STATE to reflect the session now in progress, and `sessions.sessions_count` by incrementing by one. This update is staged; it becomes material at session close (§2). The update happens now so that any mid-session STATE edit (rare but possible) carries the correct handoff ID.

7. **Claude:** checks whether any blockers from step 5 prevent substantive work. If yes, Claude surfaces them to the operator and waits. If no, Claude awaits the operator's first substantive instruction.

8. **Operator:** provides the first substantive instruction, which may be the next-action from the handoff, a revised instruction that overrides the handoff, or an out-of-protocol invocation (§5).

### 1.4 Postconditions

- A self-audit block has been produced and is visible at the start of the session response.
- An orientation statement has been produced.
- STATE's `sessions.next_handoff_id` and `sessions.sessions_count` reflect the current session.
- Any discrepancies between handoff and STATE have either been resolved or surfaced and acknowledged as deferred to a later point in the session.
- No substantive work has begun yet.

### 1.5 Failure modes

**1.5.1 No handoff provided.** The operator opens the session without pasting a handoff. Claude asks for it rather than proceeding. If the operator states the handoff was lost and cannot be retrieved, Failure mode 1.5.2 applies.

**1.5.2 Prior handoff lost or STATE missing at session-open.** The handoff is not available and cannot be retrieved from operator's storage, and / or STATE.md is not available. Claude does not attempt to reconstruct either from chat transcripts or best-effort memory. Procedure: surface the loss to the operator, ask what evidence is available (older handoffs, repo state, operator memory, chat transcript excerpts the operator can paste in), and produce a rebuild of the missing artifact with every reconstructed field explicitly flagged as reconstructed. The rebuild is logged to DecisionJournal as a forced-reconstruction event. The session's work is gated on the operator accepting the rebuild.

**1.5.3 Handoff ID does not match STATE's expected next ID.** Handoff claims to be H-NNN; STATE's `sessions.next_handoff_id` is H-MMM. Per §9 (thin-handoff handling) and the STATE failure mode 2, Claude stops, surfaces both values, asks the operator to confirm which is authentic and correctly numbered.

**1.5.4 Self-audit surfaces a discrepancy Claude cannot resolve.** A commitment-file SHA mismatch, a governance fingerprint disagreement, a files-modified claim that doesn't match STATE. Claude surfaces the specific discrepancy with enough detail for the operator to rule on it. Substantive work does not proceed until the operator rules.

**1.5.5 First session of the project (H-001).** No handoff exists. The ritual is modified: steps 1–3 are skipped (no prior handoff, STATE does not yet exist), step 4's self-audit is replaced by a statement that this is the project kickoff, step 5's orientation is replaced by an outline of the session's intended scope. STATE.md is produced at the end of the first session as part of §2, not before.

### 1.6 Logging requirements

- Self-audit block: visible in the session transcript at session start. Not separately persisted — it is part of the session's narrative.
- Any discrepancy resolved during the ritual: logged to DecisionJournal as a short entry naming the discrepancy and the resolution.
- Any discrepancy deferred: logged as a pending operator decision in STATE's `open_items.pending_operator_decisions`.
- STATE updates from step 6: reflected in the session-close STATE update (§2).

---

## 2. Session-close ritual

### 2.1 Name and scope

The session-close ritual governs the ending of every Claude chat session on this project. It applies to every session. A session that ends without completing this ritual leaves the project in an inconsistent state and is a protocol violation.

### 2.2 Preconditions

- The session has produced at least some output (even if that output was only the session-open ritual and a blocked-on-operator stop).
- The operator has indicated that the session is closing (explicitly: "let's wrap up," "please produce the handoff," "we're done for this session," or equivalent).
- STATE.md exists and is loaded in Claude's working context.

### 2.3 Procedure

1. **Claude:** enumerates every field in STATE that changed during the session, and every prose subsection in STATE that needs a narrative update. Produces this enumeration as a visible list at the start of the session-close output, so the operator can review before the update is applied.

2. **Claude:** updates the YAML block in STATE to reflect every enumerated field. Fields not enumerated are left alone. New list entries (e.g., a new entry in `pending_operator_decisions`) are appended rather than reordered. Comments in the YAML are preserved.

3. **Claude:** updates the prose commentary in STATE where narrative context has shifted. At minimum, the "Where the project is right now" subsection is always refreshed. Other subsections are updated selectively — the YAML field dictionary changes only on schema changes; the failure-modes section changes only when a new failure mode is named.

4. **Claude:** bumps `state_document.current_version` by one, sets `state_document.last_updated` to the session's closing date, and sets `state_document.last_updated_by_session` to the current handoff ID.

5. **Claude:** validates that the YAML block parses cleanly. If a YAML parser is available in the session, run it; otherwise inspect visually for common issues (unquoted strings that could be misinterpreted, indentation, list formatting). A parse failure at this step is a blocker — the session does not close until STATE is valid.

6. **Claude:** produces the session-close handoff document per the contents specified in Section 1.5.2 of the build plan:
   - Sequential handoff identifier (H-NNN).
   - Session's start and end timestamps.
   - Current work package and phase-checkpoint status.
   - Every file created, modified, or deleted during the session, with paths.
   - Every project asset touched.
   - Summary of decisions made during the session, with reasoning.
   - Open questions requiring operator input.
   - Flagged issues or tripwires that fired during the session.
   - Claude self-report paragraph noting anything skipped, rationalized, or uncertain.
   - Explicit next-action statement for the session that follows.
   - STATE diff summary: a short bullet list of what changed in STATE from the prior version to the new one.

7. **Claude:** bundles the updated STATE and the handoff together in the closing output, both visible as downloadable markdown files.

8. **Claude:** confirms to the operator that the session is closing, names the next-action for the following session, and reminds the operator that their tasks are: (a) save the handoff, (b) commit both files to the repo (once the repo exists), (c) bring the handoff into the next session's opening.

9. **Operator:** saves the handoff and STATE. If the repo exists, commits both files. This step is outside Claude's visibility — Claude cannot verify the operator performed it, but the protocol assumes they did.

### 2.4 Postconditions

- STATE has been updated, its YAML validates, its document version is bumped by one.
- A handoff document exists with all required contents.
- The STATE diff summary is included in the handoff.
- Both files are visible in the session's closing output for the operator to save.
- The next-action for the following session is explicitly stated.

### 2.5 Failure modes

**2.5.1 YAML parse failure.** STATE's YAML does not parse cleanly at step 5. Claude does not close the session with broken STATE. Procedure: stop, show the parse error, fix the YAML, re-validate. If the operator has indicated they need to end the session urgently, Claude produces a handoff that explicitly notes "STATE update blocked on YAML fix," does not bump the document version, and leaves the prior STATE as current. The next session opens with a mandatory STATE-repair work package before any other work.

**2.5.2 Session ended abruptly without closing ritual.** The operator disconnects or ends the session without requesting a handoff. Claude cannot force a close. The next session's opening will discover the missing handoff and apply Failure mode 1.5.2. Mitigation: if Claude senses the session may be ending (operator says "I need to go" or similar), Claude proactively offers to produce the handoff before the operator disconnects, rather than waiting for an explicit close request.

**2.5.3 Session produced no substantive output.** A session that was interrupted before substantive work could begin. Procedure: close with a minimal handoff noting what happened, STATE update that reflects only the session-counter increment and the date, and a next-action that is the same as the prior session's (picking up where it was interrupted). The session counter still increments; every session consumes a handoff ID.

**2.5.4 Operator requests skipping the handoff.** Operator says "no handoff needed this time" or similar. This is a protocol violation that would corrupt session continuity. Claude declines, explains the rule from Section 1.5.4, and produces the handoff anyway. If the operator insists, this is treated as an out-of-protocol invocation (§5), and the OOP log records that the handoff was skipped — but the handoff is still produced, because the OOP mechanism suspends restrictions on Claude, not the existence of the protocol itself.

### 2.6 Logging requirements

- Handoff document: produced, visible in the session's closing output, saved by operator.
- Updated STATE: produced, visible in the session's closing output, saved by operator.
- Any new DecisionJournal entries from this session: already written in real-time during the session; referenced in the handoff's decisions summary.
- Any RAID entries added, closed, or updated: already written in real-time; RAID counts in STATE reflect the session-end state.
- The session's out-of-protocol event count (if any): reflected in STATE's `sessions.out_of_protocol_events_cumulative` and `out_of_protocol_events_since_last_gate`.

---

## 3. Gate-UAT ritual

### 3.1 Name and scope

The gate-UAT ritual governs the transition from one phase to the next. Each of the seven build phases has an exit gate, and the observation window has two gates (pilot exit and window close). This ritual covers the exit gate for any phase. It is the mechanism by which the operator's verdict — binding — is recorded and the project advances.

### 3.2 Preconditions

- The current phase's work is complete per the phase's acceptance criteria in Section 8 of the build plan.
- Claude has produced, during the session, enough evidence to support the operator's verdict: screenshots from the admin UI, copy-paste text output, pass/fail matrices, and so on. Per Section 1.5.1, none of this evidence may be terminal-only; all must be accessible through web UIs, visual surfaces, or generated text the operator can see.
- The operator has indicated readiness to adjudicate the gate.

### 3.3 Procedure

1. **Claude:** produces a structured UAT evidence block containing:
   - Phase name and number.
   - The phase's exit-criteria list from Section 8 of the plan.
   - For each criterion: the specific evidence that the criterion is met (screenshot reference, text output excerpt, pass/fail assertion with justification).
   - A pass/fail matrix: a table mapping each criterion to a pass, fail, or N/A verdict.
   - A summary: overall recommendation based on the matrix.
   - Any criterion on which Claude has doubt, flagged explicitly — doubts are not hidden.

2. **Claude:** does not self-certify the gate. The evidence block is a proposal to the operator, not a verdict. Claude's summary may say "recommend pass" but the verdict is the operator's alone.

3. **Operator:** reviews the evidence block. The operator's review may include requesting additional evidence, running spot-checks against the admin UI or the repo, asking Claude to clarify specific points, or — if satisfied — delivering a verdict.

4. **Operator:** delivers the verdict explicitly. Three verdicts are possible:
   - **Pass** — all criteria are met, the gate closes, the phase is complete.
   - **Fail with reason** — one or more criteria are not met; the reason is named; the phase remains open and Claude has work to do before a re-adjudication.
   - **Defer** — the operator needs more time or more evidence before ruling; the gate stays open; a follow-up gate session is scheduled.

5. **Claude:** records the verdict in STATE's `phase.last_gate_passed` (on pass) and in the DecisionJournal (on any verdict, with reasoning). On pass, STATE's `phase.current` advances and `phase.next_gate_expected` is repopulated with the following phase's exit criteria.

6. **Claude:** if the verdict was pass and this gate marked the end of Phase 7, triggers the ritual for entering the pilot phase (which is a sub-ritual of the observation-window open ritual, §7, but scoped to pilot rather than window).

7. **Claude:** if the verdict was fail, logs the failed criteria and the operator's reason in STATE's `open_items.pending_operator_decisions` or as a new RAID entry, depending on whether the remediation is scope-bounded (decision) or risk-bounded (RAID).

8. **Claude:** continues the session per the operator's direction, or closes the session per §2 if the operator is done.

### 3.4 Postconditions

- The verdict is recorded in STATE and DecisionJournal.
- On pass: phase has advanced; next_gate_expected is repopulated.
- On fail: the failed criteria are tracked as open items.
- On defer: the gate's state is "pending"; no STATE or phase advancement occurs; a next session is required before a verdict can be delivered.
- The evidence block remains in the session's transcript for reference.

### 3.5 Failure modes

**3.5.1 Claude tempted to self-certify.** Claude produces the evidence block and then writes "gate passed" without waiting for operator verdict. This is a severe protocol violation and a tripwire. Procedure: Claude does not proceed; Claude produces the evidence block, stops, waits for verdict.

**3.5.2 Evidence block requires terminal-only verification.** A phase criterion as written requires tailing a log file or running a CLI command. Per Section 1.5.5, this is a tripwire. Procedure: Claude surfaces the rule, refuses to proceed, and reworks the criterion into a web-UI equivalent as part of the phase's unfinished work. The gate cannot be adjudicated until all criteria have web-UI equivalents.

**3.5.3 Operator delivers a vague verdict.** "Looks good, let's move on" is not a verdict. Procedure: Claude asks for an explicit pass / fail / defer, so that the DecisionJournal entry is unambiguous. If the operator is clearly saying pass but wasn't explicit, Claude writes "pass" in the journal but notes the phrasing.

**3.5.4 Operator passes the gate with one criterion visibly unmet.** Evidence shows criterion C failed, but operator says pass anyway with a note like "we'll come back to C later." Procedure: Claude records the pass verdict but explicitly tracks the unmet criterion as a RAID entry or pending-operator-decision. The pass is not silently rewritten; the debt is visible. If the operator pushes for the unmet criterion to be forgotten, Claude surfaces this as an out-of-protocol request.

### 3.6 Logging requirements

- UAT evidence block: visible in the session transcript; referenced in the handoff by session ID (the transcript is the reference, not a persisted artifact).
- Verdict: logged to DecisionJournal with reasoning ("Phase N passed on date; criteria evidence summarized in handoff H-NNN").
- STATE updates: `phase.last_gate_passed`, `phase.current`, `phase.next_gate_expected`, and `sessions.out_of_protocol_events_since_last_gate` reset to zero.
- Handoff for the session: treated as a gate handoff (per Section 1.5.2), which additionally contains the evidence block and pass/fail matrix.

---

## 4. Tripwire-handling ritual

### 4.1 Name and scope

The tripwire-handling ritual governs what happens when a tripwire event fires. The tripwires are enumerated in Section 1.5.5 of the plan and in the STATE failure modes; the ritual here is the behavioral procedure applied when one fires. Tripwires are hard stops, not soft advisories — the ritual exists because a tripwire fired means the project is in a situation where continuing without operator input is a governance violation.

### 4.2 Preconditions

- A condition has been detected that matches one of the enumerated tripwires: (a) modification of a commitment file during active observation, (b) attempting to skip or proceed past a phase-exit gate without operator verdict, (c) session began without the handoff-acceptance ritual, (d) test failure that Claude is tempted to resolve by weakening the test, (e) acceptance criterion that requires terminal access, (f) operator request that would fire one of the above.

### 4.3 Procedure

1. **Claude:** immediately stops whatever work was in progress. No further substantive action on the current task.

2. **Claude:** surfaces the tripwire to the operator as a visible block. The block contains:
   - Which tripwire fired (by name, from the enumerated list).
   - What specifically caused it to fire (the request, the condition, the detected discrepancy).
   - The rule from Section 1.5.5 or the relevant governance document that names this as a tripwire.
   - What Claude is not doing as a result (e.g., "I am not modifying fees.json; I am not closing the gate; I am not proceeding to the next phase").
   - A request for operator direction.

3. **Operator:** rules. Options are:
   - **Withdraw the request** — the tripwire was fired by a request that the operator now retracts. Claude returns to prior work (or closes the session if there was no prior work).
   - **Override explicitly** — the operator acknowledges the tripwire and explicitly directs Claude to proceed anyway. This is an out-of-protocol invocation (§5) and must use the OOP trigger phrase. The override is logged both as a tripwire event and as an OOP event.
   - **Reclassify** — the operator argues the condition does not actually match the tripwire. Claude re-evaluates and either agrees (proceeds normally, logs the false-positive) or disagrees (stays stopped, escalates).
   - **Defer** — the operator needs more time to decide. Session is paused on this tripwire; other work may proceed only if explicitly unblocked.

4. **Claude:** logs the tripwire event to DecisionJournal with: what fired, what the operator ruled, the reasoning, and any OOP invocation that resulted.

5. **Claude:** updates STATE. `open_items.tripwire_events_currently_open` increments by one if the tripwire is deferred or reclassified-as-open, or stays at zero if the tripwire was withdrawn or resolved. If override, the count does not increment (it's resolved-via-override) but the OOP counters do.

6. **Claude:** proceeds or stops per the operator's ruling.

### 4.4 Postconditions

- The tripwire has been logged to DecisionJournal.
- STATE's tripwire and OOP counters reflect the event.
- Work has either resumed per operator ruling, paused on deferral, or closed out.

### 4.5 Failure modes

**4.5.1 Claude rationalizes the tripwire rather than firing it.** The most dangerous failure mode. Claude detects the condition but decides it doesn't "really" apply, or decides to proceed quietly. This is exactly the drift pattern the governance layer exists to prevent. Procedure: the protocol says fire-first-decide-second. If there is any ambiguity about whether a condition is a tripwire, the default is to fire and let the operator reclassify (option 3 in §4.3). The cost of a false-positive tripwire (brief pause, operator clarifies) is much lower than a false-negative (silent drift).

**4.5.2 Multiple tripwires fire at once.** A single event matches two or more tripwires. Procedure: surface all of them in the same block, each separately named; operator rules on each separately, or on all of them with a single ruling that covers all.

**4.5.3 Operator overrides without using the OOP phrase.** Operator says "just do it" without the OOP phrase. Procedure: Claude asks the operator to use the OOP trigger phrase explicitly, because the governance model requires the override to be in the log as an OOP event. If the operator refuses, Claude does not proceed (the OOP mechanism exists specifically for this situation; skipping it undermines the mechanism).

**4.5.4 Tripwire fires but operator is absent.** The operator is not actively in the session; a condition has fired (e.g., during an exchange where Claude is working through a long task). Procedure: Claude stops, produces the tripwire surface, and waits. No substantive work continues until the operator responds. This may cause the session to sit idle; that is acceptable.

### 4.6 Logging requirements

- DecisionJournal: entry for every tripwire event, regardless of resolution. At minimum: trigger, context, ruling, OOP if applicable.
- STATE: tripwire counter and OOP counters updated per §4.3 step 5.
- Session handoff: flagged-issues section lists every tripwire event in the session, even if resolved quickly. The self-report paragraph notes any tripwire where Claude believes there was tension or ambiguity.

---

## 5. Out-of-protocol invocation ritual

### 5.1 Name and scope

The out-of-protocol (OOP) mechanism allows the operator to suspend the usual full protocol for a specific task. OOP is the escape hatch; it exists so that the governance layer is not so rigid that it prevents legitimate quick-fix work. This ritual covers OOP invocation, the scope of what OOP suspends, and the logging that makes OOP visible even when permitted.

Per D-004, the trigger phrase is the literal string "out-of-protocol" at the start of a request.

### 5.2 Preconditions

- The operator wants to request something that would, under normal protocol, trigger a tripwire, skip a ritual step, or bypass a gate.
- The operator has decided the request is nevertheless warranted.
- The request is not one that would violate the observation-active soft lock, which is unconditional.

### 5.3 Procedure

1. **Operator:** begins the request with the literal phrase "out-of-protocol." Example: "Out-of-protocol: please edit STATE.md directly to fix the typo in the costs section."

2. **Claude:** detects the OOP phrase. Before acting on the request:
   - Identifies what the OOP invocation suspends: which tripwire(s), which ritual step(s), which governance rule(s).
   - Checks that the request does not touch the observation-active soft lock. If the request would modify a commitment file during active observation, OOP does not apply; Claude refuses regardless, citing the unconditional nature of the lock per D-004 and Section 9.6.
   - Confirms to the operator that the OOP invocation is understood and what specifically is being suspended.

3. **Claude:** performs the requested work. During OOP, Claude's normal obligations around surface-first, gate-blocking, etc. are suspended for the specific task — but the logging obligations are not, and the observation-active lock is not.

4. **Claude:** logs the OOP event:
   - DecisionJournal entry with the full request, what was suspended, what was done, and any judgment calls made during the work.
   - STATE's `sessions.out_of_protocol_events_cumulative` increments by one.
   - STATE's `sessions.out_of_protocol_events_since_last_gate` increments by one.
   - Session handoff's self-report section notes the OOP event.

5. **Claude:** returns to normal protocol for any work that follows the OOP task. OOP applies to the specific task, not to the rest of the session.

### 5.4 Postconditions

- The requested work has been performed.
- The OOP event is logged in three places: DecisionJournal, STATE counters, session handoff self-report.
- Normal protocol is in effect for any work that follows.

### 5.5 Failure modes

**5.5.1 OOP phrase not used but operator clearly wants OOP behavior.** Operator says "just skip the ritual this once" or similar without the trigger phrase. Procedure: Claude asks the operator to use the trigger phrase explicitly. If the operator refuses, Claude does not proceed; the OOP mechanism exists precisely so that overrides are visible in logs.

**5.5.2 OOP used to request a commitment-file change during active observation.** The trigger phrase does not override the lock. Claude refuses, cites Section 9.6, and explains that the only way to change commitment files during observation is to close the window first.

**5.5.3 OOP used to skip session-open or session-close ritual.** OOP can suspend specific steps within these rituals (e.g., "skip the self-audit this time because we're doing a quick follow-up"), but not the rituals themselves. The session-open and session-close rituals must always occur; OOP can scope down what they contain, not eliminate them. If the operator requests elimination, Claude produces the minimum-viable version and logs the OOP as suspending specific steps.

**5.5.4 OOP events accumulating rapidly.** If OOP counters grow quickly (many events per session, or many events since last gate), this is itself a signal that the protocol is under pressure — either the protocol is miscalibrated or the project is in a rushed mode. Claude notes this observation in the session handoff's self-report when the trailing-session OOP rate exceeds a threshold the operator can tune (initial default: 3 OOP events in a single session, or 5 since the last gate).

### 5.6 Logging requirements

- DecisionJournal: full entry per OOP event.
- STATE: counter increments per §5.3 step 4.
- Session handoff: self-report section names the OOP events with one-line summaries.
- The OOP trigger phrase itself is recorded in STATE's `governance` fingerprint, which makes it spot-checkable.

---

## 6. Commitment-file modification ritual

### 6.1 Name and scope

The commitment-file modification ritual governs any change to the four protected files: `signal_thresholds.json`, `fees.json`, `breakeven.json`, and `sackmann/build_log.json`. These files are pre-commitments; their integrity is what makes the observation window produce a decision rather than a moving target. The ritual is most strict during active observation, but applies whenever any of the four files is created, modified, or deleted.

### 6.2 Preconditions

- A proposed change to one of the four commitment files exists.
- The observation-active soft lock status is known (STATE's `soft_lock.present`, verified against the repo's `OBSERVATION_ACTIVE` file).
- The current phase is known.

### 6.3 Procedure

1. **Claude:** verifies the current `soft_lock.present` status by both (a) reading STATE's YAML and (b) checking for the `OBSERVATION_ACTIVE` file in the repo. If the two disagree, STATE failure mode 3 applies and this ritual does not proceed.

2. **Claude:** if `soft_lock.present` is true (observation active), refuses the change. This is unconditional and not overridable by OOP. The refusal cites Section 9.6 of the plan and D-004's explicit clause that OOP does not override the lock. If the operator genuinely needs the change, the procedure is: close the current observation window first (§8), then the change becomes permissible but ends the window. The operator must explicitly acknowledge this.

3. **Claude:** if `soft_lock.present` is false, proceeds with the change. The procedure continues:
   - Writes the new file content.
   - Computes the new SHA-256 of the file.
   - Updates the corresponding entry in STATE's `commitment_files` section: `sha256` to the new value, `last_modified_session` to the current handoff ID, and `exists` to true if the file did not previously exist.
   - Writes a DecisionJournal entry describing the change, the motivation, and the reasoning. Commitment-file changes are always journaled, even in pre-build.

4. **Claude:** if this is the first time the file is being created (during Phase 1), includes in the DecisionJournal entry the derivation that produced the values. For `fees.json`, the Polymarket US fee schedule references. For `breakeven.json`, the derivation from `fees.json` plus assumptions. For `signal_thresholds.json`, the pilot-derived values (per D-002). For `sackmann/build_log.json`, the pipeline configuration and archive coverage.

5. **Claude:** if this is a revision to an existing file, includes in the DecisionJournal entry the prior value, the new value, the reason for the change, and whether any downstream artifacts (dashboard, replay simulator, breakeven derivation) are affected and need corresponding updates. Under the doc-code coupling rule, downstream updates travel with this change.

6. **Operator:** commits the updated file to the repo. The updated STATE goes with it as part of the session-close bundle.

### 6.4 Postconditions

- The commitment file reflects the new content.
- STATE's `commitment_files` section reflects the new SHA and the modifying session.
- DecisionJournal contains a new entry with the change's derivation and reasoning.
- If downstream artifacts were affected, they were updated in the same session.

### 6.5 Failure modes

**6.5.1 Soft lock disagreement.** STATE says `present: false` but the repo has `OBSERVATION_ACTIVE`, or vice versa. STATE failure mode 3 applies. Change does not proceed.

**6.5.2 Change requested during active observation.** Per §6.3 step 2, refused unconditionally. The operator's options are (a) withdraw the change, (b) close the window first (§8), or (c) defer the change until the current window closes naturally.

**6.5.3 Change would invalidate breakeven.json.** A change to `fees.json` mechanically invalidates `breakeven.json` because breakeven is derived from fees. Procedure: the change must be bundled with a re-derivation of breakeven; single-file changes to fees alone are rejected.

**6.5.4 Change made without DecisionJournal entry.** This is a doc-code coupling violation and a tripwire. The change is not considered complete until the journal entry exists.

**6.5.5 SHA in STATE does not match the file on disk after the change.** Bookkeeping error. Procedure: recompute the SHA from the file on disk and update STATE to match. The file is authoritative over STATE in this specific case because the file is what will be read by downstream systems; STATE is the record of what the file's SHA is.

### 6.6 Logging requirements

- DecisionJournal: mandatory entry per §6.3 steps 4 and 5.
- STATE `commitment_files` section: updated per §6.3 step 3.
- Session handoff: files-modified list includes the commitment file; decisions summary includes the journal entry reference.
- If the change was refused due to active observation: the refusal is logged to DecisionJournal with the operator's request and Claude's refusal reasoning.

---

## 7. Observation-window open ritual

### 7.1 Name and scope

The observation-window open ritual governs the transition from pilot-complete to window-active. Per D-002, a pilot phase precedes the observation window; pilot data is excluded from the window; thresholds are frozen at pilot end; and the 250-signal / 60-day clock starts. The ritual covers the mechanics of that transition.

A parallel sub-ritual covers the transition from Phase 7 exit to pilot open; it is a shortened version of this ritual and is described in §7.5.

### 7.2 Preconditions

- Phase 7 has passed its exit gate per §3.
- The pilot phase has completed.
- A pilot analysis has been produced and operator-reviewed, showing whether pilot-derived threshold values exist that meet the project's tradeability criteria (D-002's no-tradeable-configuration branch).
- `signal_thresholds.json` either exists with pilot-derived values or is being created as part of this ritual.
- `fees.json` and `breakeven.json` exist and are current.
- The operator has given an explicit go-live signal.

### 7.3 Procedure

1. **Operator:** delivers the go-live signal. This is an explicit statement: "we are opening the observation window now" or equivalent unambiguous phrasing.

2. **Claude:** verifies the preconditions. All four must hold. If any does not, Claude surfaces the gap and the ritual does not proceed.

3. **Claude:** finalizes `signal_thresholds.json` with the pilot-derived values, if not already finalized. The file is created or updated per §6 (commitment-file modification ritual), with the pilot-derivation reasoning in the DecisionJournal entry.

4. **Claude:** re-verifies that `fees.json` and `breakeven.json` are current as of this moment. If `fees.json` needs an update (e.g., a Polymarket US fee-schedule change occurred during pilot), that update happens now per §6, and `breakeven.json` is re-derived in the same session.

5. **Claude:** creates the `OBSERVATION_ACTIVE` file in the repo. The file's content is a short block: window start date, target calendar cap date (start + 60 days), target signal count (250), pilot end date, and the SHAs of the four commitment files at the moment of lock engagement.

6. **Claude:** updates STATE:
   - `soft_lock.present` = true.
   - `soft_lock.created_session` = current handoff ID.
   - `observation_window.status` = "active".
   - `observation_window.window.started_date` = today.
   - `observation_window.window.target_calendar_cap_date` = today + 60 days.
   - `observation_window.window.projected_close_date` = the calendar cap initially (updated as signals accumulate).
   - `phase.current` = "observation-active".

7. **Claude:** writes a DecisionJournal entry recording the window open: the pilot analysis summary, the finalized threshold values with derivation, the go-live confirmation from the operator, the commitment-file SHAs at lock engagement.

8. **Claude:** confirms to the operator that the window is open, names the observation-end conditions (250 signals or 60 days, whichever first), and reminds the operator of their Section 7 obligations (manual trade logging, daily reconciliation, coverage window commitments, operator-availability toggle usage).

### 7.4 Postconditions

- `OBSERVATION_ACTIVE` file exists in the repo with the correct content.
- STATE reflects window-active status with correct dates and SHAs.
- DecisionJournal contains a full window-open entry.
- The operator has acknowledged that the window is live.
- The commitment-file soft lock is engaged and will refuse any further modification to the four files until window close (§8).

### 7.5 Pilot-open sub-ritual

The Phase 7 → pilot transition is a shortened version of this ritual. It applies when Phase 7's exit gate has passed and the operator has approved a pilot protocol document (per D-002). The differences from the full window-open ritual:

- No `OBSERVATION_ACTIVE` lock is engaged (that engages only at pilot-complete / window-open).
- `observation_window.status` is set to "pilot" rather than "active".
- `observation_window.pilot.started_date` is populated.
- Threshold values are not yet frozen; the pilot's purpose is to calibrate them.
- Data captured during the pilot is excluded from the eventual window analysis.

Otherwise the ritual structure is identical: verify preconditions, update STATE, log to DecisionJournal, confirm to operator.

### 7.6 Failure modes

**7.6.1 Pilot analysis shows no tradeable configuration.** Per D-002's open sub-question 4, this is a real possibility. The window does not open. The project pauses for operator decision: abort, redesign thresholds (which effectively means redesigning the thesis), or extend pilot. Each path is logged to DecisionJournal.

**7.6.2 Commitment files are not current.** `fees.json` is stale (fee schedule changed during pilot), or `breakeven.json` was not re-derived after a `fees.json` change. Per §6.5.3, these must be reconciled before the window opens.

**7.6.3 Operator gives a partial go-live signal.** Something like "I think we're ready." Per §3.5.3, Claude asks for an explicit signal before proceeding.

**7.6.4 STATE and repo soft-lock state are already inconsistent.** At step 2 Claude checks preconditions and finds `OBSERVATION_ACTIVE` already exists (even though STATE says `present: false`), or STATE says `present: true` but no `OBSERVATION_ACTIVE` file exists. STATE failure mode 3 applies; ritual does not proceed until resolved.

**7.6.5 Pilot itself did not actually end.** The operator says go-live but the pilot analysis is not complete. Claude surfaces this and the ritual does not proceed; pilot-end is a precondition to window-open.

### 7.7 Logging requirements

- DecisionJournal: full window-open entry per §7.3 step 7.
- STATE: extensive update per §7.3 step 6.
- Repo: `OBSERVATION_ACTIVE` file created.
- Session handoff for the window-open session: treated as a gate handoff, with the pilot-analysis summary and the window-open evidence as primary content.

---

## 8. Observation-window close ritual

### 8.1 Name and scope

The observation-window close ritual governs the transition from window-active to window-closed. A window closes for one of five reasons: (a) target signal count reached, (b) calendar cap reached, (c) operator explicitly aborts, (d) a commitment file change becomes necessary mid-window (per Section 9.6 of the plan, this ends the window), (e) a catastrophic system failure renders the window invalid. The ritual covers the mechanics of closure and the transition to window-close analysis.

### 8.2 Preconditions

- The observation window is active: STATE's `soft_lock.present` is true, `observation_window.status` is "active", `OBSERVATION_ACTIVE` exists in the repo.
- A closure condition has been detected or is being declared by the operator.

### 8.3 Procedure

1. **Claude:** identifies the closure condition: signal-count reached (check against `observation_window.window.target_signal_count`), calendar cap reached (check against `target_calendar_cap_date`), operator abort (explicit statement), commitment-file change event (per Section 9.6), or catastrophic failure.

2. **Claude:** surfaces the closure condition to the operator for confirmation. For signal-count and calendar-cap closures, this is effectively notifying — the condition is mechanical and the confirmation is pro forma. For operator-abort or commitment-file-change, the operator's explicit statement is itself the condition. For catastrophic-failure, the operator must confirm that the failure invalidates the window.

3. **Claude:** captures the final window state: signal counts, days elapsed, any pending operator decisions, the SHAs of the commitment files at closure (they should match the SHAs at lock engagement unless a commitment-file change triggered the closure).

4. **Claude:** triggers the window-close analysis. This is a separate workstream, not part of the closure ritual itself, but the ritual kicks it off by creating an `analysis_window_N/` folder structure and populating it with the raw data references, the replay-simulator configuration at lock time, and the analysis notebook template. The analysis itself may take multiple sessions; the ritual only starts it.

5. **Claude:** removes the `OBSERVATION_ACTIVE` file from the repo. Updates STATE:
   - `soft_lock.present` = false.
   - `soft_lock.removed_session` = current handoff ID.
   - `observation_window.status` = "closed".
   - `observation_window.window.closure_reason` = one of the enum values.
   - `phase.current` = "observation-closed".

6. **Claude:** writes a DecisionJournal entry recording the closure: reason, final signal count, days elapsed, whether the closure was mechanical (count/cap) or triggered (abort/change/failure), and the analysis workstream that has been kicked off.

7. **Claude:** confirms to the operator that the window is closed and the soft lock is released. Notes that the commitment files are now unlocked and editable, and that any pending changes (e.g., a fee-schedule update that was queued during the window) can now be applied.

### 8.4 Postconditions

- `OBSERVATION_ACTIVE` file removed.
- STATE reflects window-closed status with correct closure reason.
- DecisionJournal contains a full closure entry.
- The window-close analysis workstream has been initiated.
- The operator knows the window is closed and what happens next.

### 8.5 Failure modes

**8.5.1 Signal count exceeded target without closure.** The count reached 250 several sessions ago but the closure was missed. Procedure: close the window retroactively, set `closure_reason` = "signal_count_reached", note the lag in the DecisionJournal, and treat any signals captured after the threshold as excluded from the analysis (they are outside the pre-committed window even though they were captured during active status). This is a governance incident and is escalated to the operator.

**8.5.2 Operator abort without reason.** Operator says "close the window" without stating why. Procedure: Claude asks for the reason, because the DecisionJournal entry needs it and the window-close analysis's interpretation depends on it (an abort due to external factors is different from an abort due to dissatisfaction with interim results, which is different from an abort due to a discovered flaw in the setup).

**8.5.3 Closure during an open position.** The operator has a live trade on the Polymarket US account at the moment closure is triggered. Procedure: closure of the window does not force exit of the live trade; the operator continues to manage the trade normally. But the closure timestamp is the analysis boundary; any fills after that timestamp are excluded from window-analysis metrics even if they resulted from entries placed during active status.

**8.5.4 Closure during commitment-file change.** A fee-schedule update forces closure mid-session. The closure ritual runs, then the commitment-file update ritual runs (§6). Both in the same session. The DecisionJournal has two entries: one for the closure, one for the fee update. The window's `closure_reason` is "commitment_file_change".

### 8.6 Logging requirements

- DecisionJournal: full closure entry per §8.3 step 6.
- STATE: updates per §8.3 step 5.
- Repo: `OBSERVATION_ACTIVE` removed.
- Session handoff: treated as a gate handoff, with closure evidence and final window metrics as primary content.
- The window-close analysis workstream creates its own artifacts (analysis notebook, decision memo) in later sessions.

---

## 9. Thin-handoff handling ritual

### 9.1 Name and scope

A thin handoff is one that lacks required elements per Section 1.5.2 of the plan: missing handoff ID, missing next-action statement, ambiguous next-action, inconsistent with repo state, missing files-modified list, missing decisions summary, and so on. This ritual governs what happens when Claude detects a thin handoff at session open.

### 9.2 Preconditions

- Session-open ritual (§1) is in progress, at the step where Claude reads the handoff.
- The handoff is present (not absent — that is §1.5.1) but is missing or malformed in one or more required elements.

### 9.3 Procedure

1. **Claude:** identifies specifically what makes the handoff thin. Produces a list of the missing or ambiguous elements with direct quotes (or explicit "this section is absent") where applicable.

2. **Claude:** does not attempt best-effort reconstruction. Per Section 1.5.2, silent reconstruction is exactly the failure mode this ritual exists to prevent.

3. **Claude:** surfaces the thinness to the operator:
   - What is missing or ambiguous.
   - What the impact is (e.g., "without a clear next-action, I don't know what to start with").
   - What information would resolve it.
   - A request for operator direction.

4. **Operator:** resolves. Options:
   - **Clarify from memory** — operator provides the missing context directly. Claude proceeds with the clarified context and logs the gap to DecisionJournal.
   - **Consult prior session's transcript** — operator checks the prior chat and pastes in the relevant section. Claude proceeds.
   - **Authorize proceeding with documented assumptions** — operator accepts that some context is lost and allows Claude to proceed with explicit assumption-tagging. Every assumption is named and logged. This is a soft OOP-like step but is not an OOP invocation — it is operator-authorized reconstruction with visibility.
   - **Rebuild the handoff** — operator and Claude together reconstruct the handoff for the prior session, to the extent possible, and use the rebuilt version as the session-opening artifact.

5. **Claude:** logs the thin-handoff event and the resolution to DecisionJournal.

6. **Claude:** proceeds with the session-open ritual from the point at which the thinness was detected, using the resolution from step 4.

### 9.4 Postconditions

- The thinness has been surfaced, resolved, and logged.
- The session-open ritual completes.
- Any assumptions made during resolution are explicitly flagged in STATE's `open_items.pending_operator_decisions` or in DecisionJournal, so they are visible to future sessions.

### 9.5 Failure modes

**9.5.1 Operator dismisses the thinness.** "It's fine, just proceed." Claude asks the operator to pick one of the four options in §9.3 step 4. If the operator refuses to specify, Claude treats it as option (c) — authorize proceeding with documented assumptions — and logs assumptions accordingly. Claude does not silently proceed.

**9.5.2 Handoff is so thin as to be unusable.** Multiple required elements missing; next-action is unclear; files-modified list is absent. Procedure: treat this as a lost-handoff event (§1.5.2) rather than a thin-handoff event, and apply the recovery procedure from there.

**9.5.3 Handoff is inconsistent with STATE.** Handoff says file X was modified; STATE shows no modification to X. Handoff claims SHA Y for commitment file Z; STATE says SHA W. These are not thinness failures; they are integrity failures. Apply the relevant STATE failure mode (§1.5.4 of the STATE document) rather than thin-handoff handling.

### 9.6 Logging requirements

- DecisionJournal: entry per thin-handoff event, with the specific thinness, the resolution, and any assumptions made.
- STATE: `open_items.pending_operator_decisions` may gain an entry if assumptions were made that need later resolution.
- Session handoff: the new session-close handoff mentions the thin-handoff event in its self-report section.

---

## 10. Out-of-session commit ritual

### 10.1 Name and scope

An out-of-session commit is a commit to the repository made at a time when no Claude session is active — typically, the operator making an edit directly between sessions. This ritual exists primarily to name what is and is not permitted, because the single-authoring-channel rule (per Section 1.5.3 of the plan) forbids operator-authored changes to code or documentation.

### 10.2 Preconditions

- The operator is considering making a commit or direct edit to the repository, outside a Claude session.

### 10.3 Procedure

1. **Operator:** recognizes that the single-authoring-channel rule applies. The rule: Claude writes code and documentation; operator reviews and commits but does not author.

2. **Operator:** evaluates which of the following the proposed action falls into:
   - **Permitted:** committing a file that Claude produced in a session (this is the normal flow). Removing an unused file Claude produced and then identified as unneeded (with Claude's concurrence from that session). Renaming a file per Claude's explicit session-end instruction. Purely mechanical actions the operator would do inside the GitHub web UI (creating a branch, merging a pull request that Claude prepared).
   - **Not permitted:** editing any file's content. Creating a new file the operator authored. Modifying a commitment file. Modifying STATE. Modifying any file during an active observation window, even one that would otherwise be permissible to edit, without first opening a session (the lock is unconditional, but edits during observation that don't touch commitment files are still safer to do in-session).

3. **Operator:** if the action is permitted, performs it and notes it for inclusion in the next session's opening (so Claude can update STATE if needed to reflect it).

4. **Operator:** if the action is not permitted, opens a Claude session to make the change in session. Even a short session with a minimal scope is better than an operator-authored edit.

5. **Claude:** at the next session's opening, receives the operator's note about any out-of-session mechanical actions, verifies they were within the permitted set, and updates STATE if needed.

### 10.4 Postconditions

- Any out-of-session action was within the permitted set.
- If not within the permitted set, the operator opened a session to make the change.
- STATE reflects any mechanical actions taken out-of-session.

### 10.5 Failure modes

**10.5.1 Operator edits a file out of session.** Discovered at next session-open when the file's SHA disagrees with STATE's record (for commitment files) or when Claude notices the divergence during work. Procedure: surface the discrepancy, log it to DecisionJournal as a protocol deviation, either accept the operator's edit (update STATE, note the deviation, move on) or revert it and redo the change in-session. The operator's decision is logged. Repeated occurrences warrant a discussion of whether the protocol needs adjustment.

**10.5.2 Operator commits a file they authored thinking it was minor.** Same handling as 10.5.1. A "minor" author-edit is still an author-edit.

**10.5.3 Operator performs an action that seems permitted but has downstream effects.** For example, merging a pull request that Claude didn't fully review. Procedure: at next session, Claude reviews the merged changes, verifies they match what was expected, updates STATE if needed. If there's a surprise, it becomes a DecisionJournal entry and possibly a RAID entry.

### 10.6 Logging requirements

- Out-of-session actions are logged at the next session-open, by Claude, in the session's DecisionJournal entry (if the action was noteworthy) or in a short STATE update (if the action was purely mechanical, like a branch creation).
- Deviations from the permitted set are logged to DecisionJournal as protocol deviations.

---

## 11. Pending-operator-decision escalation ritual

### 11.1 Name and scope

A pending operator decision is something Claude has surfaced for the operator to rule on, which has not yet been resolved. These accumulate in STATE's `open_items.pending_operator_decisions`. This ritual governs how they are tracked, surfaced at each session-open, and escalated when they persist.

### 11.2 Preconditions

- Claude has encountered a situation requiring operator ruling that the operator has not resolved in the current session.
- The situation does not resolve itself (it is not a question Claude can later answer through more work alone).

### 11.3 Procedure

1. **Claude:** when a decision is needed and the operator is not immediately available to rule, Claude creates a pending-operator-decision entry in STATE. The entry contains: a short id (sequential: POD-001, POD-002, etc.), a one-line summary, the session in which it was raised, and a note about what the decision blocks (the specific work that cannot proceed without it).

2. **Claude:** at every subsequent session-open, the self-audit block lists all open pending decisions. Decisions are not silently forgotten.

3. **Operator:** at any session, may choose to rule on any pending decision. Ruling is explicit: "Resolve POD-003: [the ruling]." Claude records the ruling in DecisionJournal (as a full entry, because the ruling is itself a decision) and removes the entry from `pending_operator_decisions`.

4. **Claude:** if a pending decision has been open for five or more sessions without progress, escalates it in the self-audit block: "POD-003 has been open for 5 sessions; is this still relevant? Does it need a ruling, or should it be withdrawn?" The operator responds by ruling, withdrawing (some decisions become moot as circumstances change), or explicitly re-deferring with a target session for resolution.

5. **Claude:** if a pending decision blocks the current work, Claude cannot proceed past the blocked point. The session may still do other work; the blocked work waits.

### 11.4 Postconditions

- Pending decisions are tracked in STATE and visible at every session-open.
- Rulings are logged to DecisionJournal with full reasoning.
- Blocked work remains visibly blocked until resolution.

### 11.5 Failure modes

**11.5.1 Pending decision list grows indefinitely.** If many decisions accumulate without resolution, the project is functionally stalled on operator input. Procedure: Claude surfaces this pattern in the session handoff's self-report when the count crosses a threshold (initial default: 3 pending decisions simultaneously open). This is a calibration signal to the operator that attention is needed.

**11.5.2 Operator resolves a decision informally.** Operator mentions a decision in passing without saying "Resolve POD-N". Claude asks for explicit resolution, so the DecisionJournal entry is unambiguous and the STATE update is correct.

**11.5.3 Claude surfaces a decision and then proceeds as if it were resolved.** The exact drift pattern the governance layer exists to prevent. Procedure: if Claude surfaces a decision, Claude stops on the blocked work and waits. Proceeding despite unresolved pending decisions is a tripwire (§4).

### 11.6 Logging requirements

- STATE `open_items.pending_operator_decisions`: add on creation, remove on resolution.
- DecisionJournal: full entry on resolution, including the original question, the ruling, the reasoning.
- Session handoff: self-audit block lists all open pending decisions at session-open; self-report notes any new pending decisions created this session.

---

## 12. Plan-document revision ritual

### 12.1 Name and scope

The plan document (`PM-Tennis_Build_Plan_vN.docx` at the current version) is the authoritative project specification. Decisions made in sessions sometimes require changes to the plan's text. Per the doc-code coupling rule (Section 1.5.4), these changes are not optional — a decision that commits the project to a different behavior than the plan describes must either update the plan or be explicitly deferred with tracking. This ritual governs plan revisions.

### 12.2 Preconditions

- A decision has been made (in a prior session or the current one) that affects the plan's text.
- STATE's `project.plan_document.pending_revisions` lists one or more outstanding items.
- The operator has indicated readiness to revise the plan, or the work being done in the current session forces a plan sync.

### 12.3 Procedure

1. **Claude:** consults STATE's `pending_revisions` list. Each entry names a decision and the sections of the plan affected.

2. **Claude:** produces a revised plan document. The revision:
   - Applies every pending change.
   - Bumps the version number (v3 → v4, or v4 → v5, etc.) and the version date.
   - Adds a change log at the front of the plan (or updates an existing change log) listing the version history and what changed in each version.
   - For each changed section, preserves the surrounding context and only modifies the specific passages affected by the decisions.
   - Does not introduce changes that are not listed in `pending_revisions` — the ritual is for sync, not for freeform editing.

3. **Operator:** reviews the revised plan, reads the change log, and spot-checks changed sections against the DecisionJournal entries they implement.

4. **Operator:** accepts or rejects. Acceptance is explicit. Rejection comes with specific feedback on what needs to change.

5. **Claude:** on acceptance, updates STATE:
   - `project.plan_document.current_version` = new version.
   - `project.plan_document.current_version_date` = today.
   - `project.plan_document.pending_revisions` = empty (all items applied) or reduced list (if some items were deferred).

6. **Claude:** writes a DecisionJournal entry for the revision: which items were applied, which (if any) were deferred and why.

7. **Operator:** commits the new plan version to the repo, replacing the prior version. The prior version is preserved in git history.

### 12.4 Postconditions

- The plan document is at a new version.
- `pending_revisions` is empty, or has a reduced list if deferrals happened.
- STATE reflects the new version.
- DecisionJournal has a revision entry.
- The prior version is still accessible via git.

### 12.5 Failure modes

**12.5.1 Revision is requested during an active observation window and touches the commitment discipline.** The plan's Sections 9 and 11 describe the observation window's rules. Changing them mid-window would effectively change the commitment. Procedure: refuse the revision during active observation for the affected sections; allow revisions to unaffected sections (e.g., an operational note about a runbook). This parallels the commitment-file lock: plan-text changes that alter pre-commitments are also locked during observation.

**12.5.2 Pending revisions accumulate without being applied.** Similar to §11.5.1 but for plan drift. If `pending_revisions` grows to more than 3 items without a plan sync, Claude flags this in the session handoff's self-report. Plan drift is a governance issue because new decisions accumulate against an increasingly out-of-date spec.

**12.5.3 Revision introduces inconsistency with governance artifacts.** A revised plan section contradicts the current STATE, DecisionJournal, or Playbook. Procedure: at revision time, Claude checks the proposed new text against all governance artifacts and surfaces any inconsistency before the operator is asked to accept. Resolution is usually that one of the artifacts is also out of date and needs a parallel update in the same session.

**12.5.4 Freeform edit requested.** The operator asks for changes to the plan that are not in `pending_revisions`. Procedure: Claude clarifies whether this is a new decision (in which case a DecisionJournal entry is needed first, then the plan change follows) or a mechanical correction (typos, formatting). Mechanical corrections can be bundled with a revision but are logged as such. Substantive changes without a decision trail are refused.

### 12.6 Logging requirements

- DecisionJournal: revision entry per §12.3 step 6.
- STATE: updates per §12.3 step 5.
- Session handoff: files-modified list includes the plan document; decisions summary includes the revision entry reference.
- The plan's own change log: updated at the front of the document, listing every revision.

## 13. Staging-push-and-merge ritual

### 13.1 Name and scope

The staging-push-and-merge ritual governs how Claude's code and documentation changes reach the repository. Per D-029, Claude pushes changes to a dedicated `claude-staging` branch during sessions; operator merges staging to `main` as the single human-in-the-loop gate. This ritual applies to every code or documentation change produced during a session — multi-file bundles, single-file fixes, STATE updates, handoffs, everything.

This ritual supersedes the prior workflow in which operator manually uploaded Claude-produced files via GitHub's web-UI drag-and-drop interface. The prior workflow's documented failure modes (H-014 missed-file-in-bundle, H-015 multi-line-paste failures, H-016 missing DJ plus stale artifacts committed) motivated the revision.

### 13.2 Preconditions

- The `claude-staging` branch exists in the `peterlitton/pm-tennis` repository, branched from `main` (initially) or kept in sync with `main` at session open.
- The project's permanent deploy mechanism per D-034 is in force. Per D-023 / SECRETS_POLICY §A.6, secret values never appear in the chat transcript.
- The operator has ruled on session cut/scope for the current session per the session-open ritual (§1).

### 13.3 Procedure

1. **Claude:** during session work, accumulates changes locally (in-session scratchpad) until a logical unit of work is complete — e.g., a fix + its tests, a handoff + its STATE update, a research-doc addendum. Prepares the bundle as logical units with descriptive framing identifying the H-NNN session, the scope, and any referenced DJ/RAID items. Per D-034, Claude does not push directly; Claude presents the completed bundle for operator upload to `claude-staging` per step 3.

2. **Claude:** before bundle presentation, runs the minimum validation set:
   - **Tests in clean venv against pinned deps.** The standard test-pass evidence.
   - **Path-correctness list.** Every file in the bundle, the path it is intended for, an assertion that the path matches the intended location.
   - **Schema/coupling check.** If a commitment file is touched, the SHA change is named. If doc-code coupling applies (per Orientation §8), the paired documentation update is named.
   - **Stale-artifact check.** Any working artifacts Claude produced during the session that are NOT intended for the repo (manifests, checksums, draft files, etc.) are explicitly excluded from the bundle.

3. **Claude:** presents the bundle to the operator via `present_files` (or equivalent download surface) per D-034. **Operator:** uploads the bundle files to the `claude-staging` branch via the GitHub web UI drag-and-drop interface. Upload targets the `peterlitton/pm-tennis` repository at the `claude-staging` refspec; no uploads to `main`; no uploads to any other branch.

4. **Claude:** produces a bundle-summary visible to the operator in chat at session close, containing at minimum:
   - List of files in the bundle (path + action: added / modified / deleted)
   - Brief description of each file's scope / the logical unit it represents
   - Test-run summary (pass count, fail count, any pre-existing failures listed as such)
   - Validation steps completed (path check, schema check, stale-artifact check)
   - Explicit upload-and-merge-request language: "Ready for your review and merge when you are."

5. **Operator:** reviews the staging branch's diff via GitHub's web UI (compare view or PR view). Review depth is operator's choice per the spot-check discipline in Orientation §8 (Layer 4 — operator spot-checks); minimum viable review is the file list and the bundle-summary framing from step 4.

6. **Operator:** one of three rulings:
   - **Merge.** Operator merges staging → main via GitHub's merge UI. This is the gate. Render auto-deploys `pm-tennis-api` from main.
   - **Request changes.** Operator names what needs to change. Claude addresses and re-produces the bundle (same ritual from step 2). No limit on iteration cycles.
   - **Defer merge.** Operator chooses not to merge this session — perhaps the session produced partial work that should not reach main yet. Staging branch retains the work; next session picks up either by extending staging further or by operator merging first and Claude starting fresh.

7. **Claude:** logs the bundle to the session handoff's files-modified list. If the session closes with changes on staging that operator has not merged, handoff explicitly names this state.

8. **Claude:** if operator merges during the session, the post-merge state is noted in the handoff. STATE's scaffolding-files inventory reflects the merged state (committed_to_repo: true with the merge commit SHA).

### 13.4 Postconditions

- All session work exists as commits on `claude-staging`.
- Push-summary visible in session transcript for each push.
- Operator has explicitly merged, requested changes, or deferred.
- Session handoff names the final state of staging (merged / pending merge / changes requested).
- No orphaned or stale artifacts on main as a result of the session.

### 13.5 Failure modes

**13.5.1 Claude pushes to a branch other than `claude-staging`.** Procedure: this is a tripwire per Playbook §4. Claude stops, surfaces the misdirection, and waits for operator direction. The errant branch is not merged; operator deletes or ignores it.

**13.5.2 Claude pushes a file to the wrong path.** The path-correctness check at step 2 is designed to catch this before push. If it escapes (path check wrong, or Claude's internal map drifted from repo reality), operator catches it at diff review. Procedure: Claude pushes a corrective commit to staging moving the file to the correct path; operator reviews and merges when satisfied.

**13.5.3 Claude pushes stale artifacts (manifests, checksums, working files) intended for the bundle-assembly process but not for the repo.** The stale-artifact check at step 2 is designed to catch this. If it escapes, operator catches it at diff review. Procedure: Claude pushes a corrective commit to staging removing the stale artifacts; operator merges when satisfied. This is the specific failure mode H-016 produced under the old workflow.

**13.5.4 Authentication fails mid-session.** Claude's push is rejected by GitHub (PAT revoked, expired, or scoped wrong; or MCP connector deauthorized). Procedure: Claude surfaces the failure to operator. Operator rotates/re-auths the credential per SECRETS_POLICY §A.6. Claude retries the push. No change leaks to main — the push simply fails.

**13.5.5 Operator merges a push that had a pre-existing test failure.** Pre-existing failures (failures that exist on main before Claude's changes and persist through Claude's changes — see RAID I-017 for an example) should be named in the push summary and treated as informational, not gating. Procedure: push summary explicitly lists pre-existing failures with "not introduced by this push" annotation; operator merges with that context. If a new failure (introduced by this push) is present, Claude does not request merge — Claude either fixes or surfaces for operator ruling before push.

**13.5.6 Claude attempts to push during an active observation window.** If the push would modify a commitment file (`signal_thresholds.json`, `fees.json`, `breakeven.json`, `data/sackmann/build_log.json`), Claude refuses at the behavior layer — same as the pre-D-029 rule. The commit mechanism does not change the lock's scope. Non-commitment-file pushes during observation are allowed (operator-attention dependency, not a file-level lock).

**13.5.7 Drag-and-drop-to-staging as the project's permanent deploy mechanism (per D-034).** Per D-034 (H-025), the drag-and-drop-to-staging flow is the project's permanent deploy discipline, not a transitional failure mode. Procedure: Claude produces complete-replacement files in the sandbox working environment; Claude presents the bundle to the operator via `present_files` (or equivalent download surface) at session close; operator drags and drops files onto the `claude-staging` branch in the GitHub web UI; operator reviews the staging-vs-main diff; operator merges `claude-staging` → `main` as the human-in-the-loop gate. This procedure is the active default — §13's other subsections describe push-side disciplines (Claude pushes, validation, etc.) that remain the authoring-side commitments under D-029's preserved sections, executed as evidence-in-chat rather than as direct pushes. If Anthropic ships a GitHub MCP connector, a sandbox secret-injection mechanism becomes available, or a different architecture is preferred, migration is a new DJ entry superseding D-034 at that time; this subsection remains authoritative until that entry lands.

**13.5.8 Operator wants Claude to bypass the merge gate.** OOP does not suspend the merge gate. Procedure: Claude refuses per Playbook §5.5.2's class of refusal (OOP cannot override unconditional governance). If operator genuinely needs a push direct to main, the procedure is to open a separate session, close the current work to staging, and handle the direct-to-main situation in a targeted future session — not to relax the gate mid-session.

### 13.6 Logging requirements

- Each push: push-summary in session transcript. Files-changed list in session handoff.
- Merge events: logged in STATE's scaffolding-files inventory (committed_session and commit SHA). No separate DJ entry required for routine merges.
- Iterations (Claude push → operator request changes → Claude re-push): named in session handoff's self-report. Multiple iterations per session are fine; they are the ritual working as intended.
- Failures (13.5.1 through 13.5.8): logged to DecisionJournal per the failure mode's severity.
- Deferred merges (work left on staging at session close): handoff §10 next-action statement explicitly names "operator to merge staging" as a next-action item.

---


---

*End of Playbook.md — original sections §§1–12 at session H-002; §13 added at H-016 per D-029.*
