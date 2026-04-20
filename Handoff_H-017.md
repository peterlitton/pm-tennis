# PM-Tennis Session Handoff — H-017

**Session type:** Governance — D-030 landed (D-029 first-use validation surfaced an architectural gap; interim flow formalized); mid-session process recovery; cut to Path A close
**Handoff ID:** H-017
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** D-030 produced and operator-approved; STATE v15 produced; bundle queued for operator merge to claude-staging including three stale-artifact deletions. POD-H017-D029-mechanism opened. Mid-session present_files error caught by operator and corrected via comprehensive governance re-read; eight-session clean-discipline streak maintained (H-010 → H-017, no tripwires fired, no OOP). Path A cut at session close: I-017 disposition and main sweeps deferred to H-018.

---

## 1. What this session accomplished

H-017 opened from H-016 with operator authorization to clone the repo. Session-open reading covered Handoff_H-016 in full, Orientation, STATE v14, Playbook §§1, 2, 4, 13, RAID Issues table, DJ entries D-029 and D-030-area, and the H-016 handoff structure. Self-audit produced as a visible block.

Five substantive workstreams landed this session:

1. **Self-audit recovered a missing artifact.** Handoff_H-016.md was not in the H-016 session-close commit (`66def97` contained DecisionJournal.md, Playbook.md, STATE.md only). H-017 self-audit surfaced the gap before substantive work; operator committed the handoff to main as `e6c4deb` during H-017. Per Playbook §10, this is a permitted operator action (committing a Claude-produced file). Discrepancy resolved without Claude code or doc action.

2. **D-029 first-use validation surfaced an architectural gap.** D-029 Commitment §2 specifies that Claude authenticates to GitHub via a PAT stored as a Render environment variable. This presumes a working environment that can read Render env vars (a Python process running on the Render service). Claude.ai's sandbox environment cannot read Render env vars; the PAT-on-Render-env-var pattern as drafted in D-029 §2 is therefore not directly usable from Claude's actual working environment. Surfaced before any commit attempt.

3. **Render side of D-029 verified.** Operator validated `pm-tennis-api` Render configuration: Auto-Deploy = "On commit", Branch = `main`. Pushes to `claude-staging` are ignored by auto-deploy; the merge-gate safety property D-029 was primarily designed to create is structurally available.

4. **D-030 landed.** Names the gap precisely (D-029 §2 only, not D-029's substantive commitments). Adopts the drag-and-drop-to-staging interim flow per Playbook §13.5.7 as the default for H-017 and all subsequent sessions until D-029's authentication mechanism is fixed by a future DJ entry. Operator ruled Option β-i (default, no per-session re-ratification). D-029 itself preserved unchanged. POD-H017-D029-mechanism opened (low urgency; project operates correctly under the interim flow). The decision text was reviewed by operator before the file was produced; the file was produced after operator approval ("proposal agreed").

5. **Stale-artifact cleanup queued for operator action.** Three artifacts inadvertently committed at H-016 (`CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, `D-028-entry-to-insert.md`) verified safe to delete. None are referenced by code, tests, or documentation. `D-028-entry-to-insert.md` content is fully preserved in DecisionJournal D-028 (committed at `83c0bf8` since H-016). Bundled with the D-030 commit for operator action on claude-staging.

Process workstream landed:

6. **Mid-session process error caught and corrected.** Mid-session, Claude called `present_files` on draft `DecisionJournal.md` and `STATE.md` as a draft-availability gesture. Operator correctly read this as a discipline signal — files presented for upload imply session-output ready, but the session was not closed and substantive scope (I-017, main sweeps) was incomplete. Operator surfaced the error explicitly: "shouldn't those files be rendered at the end of the session?" Claude acknowledged the error rather than rationalizing, then asked whether to do a more thorough governance re-read; operator authorized. Claude completed comprehensive re-read of governance corpus before further work. Detailed in §3.1 below.

### Work that landed

| Item | Status |
|------|--------|
| H-016 handoff accepted; full reading | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + D-007 | ✅ Complete — Handoff_H-016 missing-from-main discrepancy surfaced; operator committed at e6c4deb |
| Repo clone (standing authorization) | ✅ Complete |
| D-029 first-use validation | ✅ Complete — gap surfaced before any commit attempt |
| Render side of D-029 verified by operator | ✅ Complete — Auto-Deploy='On commit', Branch='main' |
| D-030 draft text produced | ✅ Complete — operator-reviewed inline before file production |
| D-030 inserted at top of DecisionJournal.md (replacement file) | ✅ Complete — pending operator merge |
| STATE.md v15 produced with all v14→v15 updates | ✅ Complete — YAML validates; pending operator merge |
| POD-H017-D029-mechanism opened in STATE | ✅ Complete |
| Three stale-artifact deletions verified safe | ✅ Complete — operator action on claude-staging |
| Mid-session present_files error surfaced and acknowledged | ✅ Complete — corrective re-read authorized and completed |
| Comprehensive governance re-read | ✅ Complete — full Playbook (§§3, 6, 7, 8, 9, 10, 11, 12 unread at session open); full SECRETS_POLICY; RAID Risks/Assumptions/Decisions; DJ D-016 through D-027; PCR introduction |
| Handoff_H-017 production | ✅ This document |
| RAID I-017 disposition | ⏳ Deferred to H-018 (Path A cut) |
| Main sweeps per §7 Q3=(c) | ⏳ Deferred to H-018 (Path A cut) |
| §16 research-doc addendum | ⏳ Deferred to H-018 (Path A cut) |

### Counters at session close

- OOP events cumulative: **0** (unchanged)
- Tripwires fired: **0** (unchanged)
- Tripwires fired in H-017: 0
- DJ entries: **30** (was 29; D-030 added)
- RAID open issues: **14** (unchanged)
- RAID total issues: **17** (unchanged)
- Pending operator decisions: **1** (POD-H017-D029-mechanism)
- Plan-text revision candidates: **4** (v4.1-candidate, -2, -3, -4)

---

## 2. Decisions made this session

**Numbered DecisionJournal entries added this session:**

- **D-030 — D-029 authentication mechanism: architectural gap at first-use; interim flow adopted per Playbook §13.5.7**
  - Operator ruling: Option β (new DJ entry) + β-i (default, no per-session re-ratification)
  - D-029 preserved unchanged; D-030 records the gap in D-029 Commitment §2 and adopts the interim drag-and-drop-to-staging flow
  - POD-H017-D029-mechanism opened to track the resolution question
  - Verified D-030's claims against SECRETS_POLICY §A.6 and Playbook §5.5.4 before lock-in — both supported the option-(c) rejection

**Three operator rulings / in-session rulings (recorded in STATE `resolved_operator_decisions_current_session`, only D-030's reached DJ-entry threshold on its own):**

- **H-017-D029-mechanism-gap-interim-flow** — operator ruled Option β + β-i mid-session; culminated in DJ entry D-030.
- **H-017-render-side-verification-method** — informal in-session exchange validating Render Auto-Deploy config; operator opened dashboard and reported back. Not a DJ-entry threshold; logged as evidence in D-030 Finding 2.
- **H-017-Path-A-cut-at-session-close** — operator approved Path A (close after D-030 + cleanup queue, defer I-017 and main sweeps to H-018). Not a DJ-entry threshold; logged as operational direction.

---

## 3. Pushback and clarification events this session

Worth naming for future-Claude visibility.

### 3.1 The mid-session present_files error and its recovery

The single most important process event this session. Mid-session, after operator approved the D-030 draft text and Claude produced the replacement DecisionJournal.md and STATE.md drafts, Claude called `present_files` on both files. Claude's framing was that the call made the files downloadable for whenever operator was ready to upload, not that it was an upload-now request. The operator correctly read it as a session-output-ready signal that didn't match the session state.

Operator's exact framing: "why are you presenting Dj and State now?" — followed by escalation as Claude tried to clarify: "shouldn't those files be rendered at the end of the session?" — and finally a direct discipline signal: "You're scaring me. I don't think you have a good grasp of the procedures. do you want to do a more thorough review of all of the governing docs?"

Claude's response was to acknowledge the error rather than rationalize it, propose a comprehensive re-read, and stop substantive work pending operator authorization. Operator authorized. Claude completed the read covering the unread Playbook sections (§§3, 6, 7, 8, 9, 10, 11, 12), full SECRETS_POLICY, RAID Risks/Assumptions/Decisions, DJ D-016 through D-027 carefully, and PCR introduction.

The error class is "inferring rituals from snippets rather than reading them end-to-end." Specifically, Claude had read Playbook §1 and §2 at session open but only via the table-of-rituals view and partial section reads; Playbook §2 (session-close) is unambiguous about close producing a bundle (handoff + STATE + any modified files together). Calling `present_files` on session output mid-session is not a defined ritual action; it's only meaningful at close. Reading §2 end-to-end during the recovery made this immediately clear.

What this means for future-Claude reading this handoff:

- The session-close ritual produces a bundle. Files do not get presented one-by-one as they're authored.
- "Drafts in `/mnt/user-data/outputs/`" is a sandbox concept; it is not a session-output state. Files become session output only at close, when bundled with the handoff.
- If you find yourself reaching for `present_files` outside session close, stop. That's the signal.

The recovery worked as intended: operator surfaced the error, Claude acknowledged without rationalizing, Claude self-proposed the corrective action (comprehensive re-read), operator authorized. The eight-session clean-discipline streak is intact because no tripwire fired and no OOP was invoked — but this is the closest the project has come in those eight sessions to a discipline drift.

### 3.2 D-029 first-use validation surfaced before any commit attempt

When operator confirmed the staging branch existed and asked Claude to push, Claude's first response was to surface the architectural gap rather than attempt the push and discover the failure. The PAT-to-sandbox gap was named precisely (D-029 §2 presumes Render-env-var access; Claude.ai sandbox doesn't have it), three resolution paths were enumerated (Path A: paste PAT into chat = SECRETS_POLICY violation; Path B: secret-injection mechanism = doesn't exist; Path C: operator-pushes-from-local = effectively the drag-and-drop flow), and Playbook §13.5.7 was identified as the existing-governance fallback. This is the research-first / surfacing-not-rationalizing discipline applied to governance rather than code.

When operator said "you push to Git staging with my approval," Claude pushed back rather than accept the implicit instruction. The pushback was specifically about the unresolved how-the-PAT-reaches-git question; Claude asked operator to specify which of three options they meant, with explicit OOP framing for the SECRETS_POLICY-violating option. Operator's response shifted the conversation to the orthogonal Render-side validation question, which Claude answered cleanly.

### 3.3 Operator's "are you suggesting the session is done?" prompt

Mid-recovery, after Claude proposed treating the present_files call as premature and moving on to substantive work, operator asked "are you suggesting the session is done?" This was exactly the right prompt — Claude's previous message had ambiguous phrasing that could have read either as "the session continues with substantive work" (intended) or "the session is wrapping up" (possible misreading). Claude clarified the intended meaning with an explicit step-by-step plan for continuing.

### 3.4 Operator's "what files?" prompt about the present_files outputs

Even later in the recovery, operator asked Claude to specify which files the present_files call had made available. This surfaced that Claude had been speaking imprecisely — "the files exist in `/mnt/user-data/outputs/`" was not informative without naming them. Claude corrected: DecisionJournal.md (full replacement, 1053 lines, with D-030) and STATE.md (full replacement, ~660 lines, v15). Claude also corrected its earlier "from my side" phrasing ("the D-030 work is done from my side") which had overstated completion — drafting was done; upload/deletion/merge were not.

These small precision pushbacks are worth recording because they're the same class of attention as the original present_files error. Operator was reading Claude's language carefully and pulling on threads where the language was ambiguous. Future-Claude should match that precision when communicating.

---

## 4. Files created / modified this session

### Pending commit (session-close bundle for operator action)

| File | Action | Notes |
|------|--------|-------|
| `DecisionJournal.md` | Modified (replacement) | D-030 inserted at top above D-029. D-029 preserved verbatim. 30 entries total, 1053 lines. |
| `STATE.md` | Modified (replacement, v14 → v15) | YAML validates clean; all material fields verified. ~660 lines. |
| `Handoff_H-017.md` | Created | This document. |
| `CHECKSUMS.txt` | DELETE | Stale H-016 artifact; not referenced by any code/tests/docs. |
| `COMMIT_MANIFEST.md` | DELETE | Stale H-016 artifact; not referenced by any code/tests/docs. |
| `D-028-entry-to-insert.md` | DELETE | Stale H-016 artifact; content fully preserved in DecisionJournal D-028 since `83c0bf8`. |

### Operator action sequence on `claude-staging`

Per Playbook §13.5.7 interim flow per D-030 (the file deliveries are operator drag-and-drop; the deletions are GitHub web-UI trash-icon operations):

1. Switch to `claude-staging` branch in GitHub web UI.
2. Drag-and-drop `DecisionJournal.md` (replace existing).
3. Drag-and-drop `STATE.md` (replace existing).
4. Drag-and-drop `Handoff_H-017.md` (create new).
5. Navigate to `CHECKSUMS.txt` → trash icon → commit deletion.
6. Navigate to `COMMIT_MANIFEST.md` → trash icon → commit deletion.
7. Navigate to `D-028-entry-to-insert.md` → trash icon → commit deletion.
8. Review staging-vs-main diff: `https://github.com/peterlitton/pm-tennis/compare/main...claude-staging`.
9. If satisfied, merge `claude-staging` → `main`.

### Operator-side commits during this session (not Claude-authored)

- **`e6c4deb`** — operator added `Handoff_H-016.md` to main during H-017 self-audit. Permitted §10 action (committing a Claude-produced file from H-016 close that was missed in `66def97`). 332 lines.

### Files NOT modified this session

- Any commitment file (`fees.json`, `breakeven.json`, `data/sackmann/build_log.json`, `signal_thresholds.json` still doesn't exist)
- `main.py` (untouched)
- `requirements.txt` (untouched per D-024 commitment 1)
- `PM-Tennis_Build_Plan_v4.docx` (no plan revision this session)
- `PreCommitmentRegister.md`, `SECRETS_POLICY.md`, `Orientation.md`, `Playbook.md`, `RAID.md` (read for governance compliance, not modified)
- All previous handoffs (read; not modified)
- `src/capture/discovery.py` (Phase 2 code untouched per D-016)
- `src/stress_test/*` (Phase 3 attempt 2 code untouched this session — main sweeps deferred)
- `tests/*` (no tests added or modified)
- `docs/clob_asset_cap_stress_test_research.md` (unchanged — §16 deferred to H-018)
- `runbooks/*` (unchanged)

---

## 5. Known-stale artifacts at session close

After operator completes the H-017 commit-bundle merge, no known-stale artifacts remain in the repo from H-016 or H-017.

If operator defers some bundle actions (e.g., merges files but skips deletions, or defers entire bundle to a later session), STATE v15's claims about stale-artifact deletion will not match repo state at H-018 open. H-018 self-audit will surface the discrepancy and seek operator ruling per Playbook §1.5.4 before proceeding.

The DecisionJournal footer is stale ("updated at H-009 session close ... next entry will be D-018") — this footer predates D-016 and has been stale since H-009; not introduced by H-017. Out of scope for this session; flagged for a future cleanup pass.

---

## 6. Tripwire events this session

**Zero tripwires fired. Zero OOP invocations.** Eight consecutive sessions now (H-010 through H-017) without firing a tripwire or invoking OOP.

The mid-session `present_files` error (§3.1) was a Claude process error caught by operator and corrected within the session. It did not match any of the enumerated tripwires in Playbook §4.2 — it was not a commitment-file modification during observation, not a gate skip, not a missed handoff-acceptance ritual, not a test-weakening, not a terminal-only acceptance criterion, and not a request that would fire those. It was a category of error not captured by the existing tripwire taxonomy: "Claude infers a ritual from snippets rather than reading it end-to-end, then performs an action consistent with the inferred ritual but not the actual ritual." Worth flagging for future taxonomy consideration; no DJ entry needed for the event itself because the recovery was clean.

---

## 7. STATE diff summary (v14 → v15)

Key fields that changed:

- `project.state_document.current_version`: 14 → 15
- `project.state_document.last_updated_by_session`: H-016 → H-017
- `phase.current_work_package`: rewritten to reflect H-017 accomplishments (α through ε) and H-018 pickups
- `sessions.last_handoff_id`: H-016 → H-017
- `sessions.next_handoff_id`: H-017 → H-018
- `sessions.sessions_count`: 16 → 17
- `open_items.pending_operator_decisions`: [] → 1 entry (POD-H017-D029-mechanism)
- `open_items.resolved_operator_decisions_current_session`: pruned per settled convention; 1 H-017 entry (H-017-D029-mechanism-gap-interim-flow)
- `open_items.phase_3_attempt_2_notes`: +6 entries for H-017
- `scaffolding_files.STATE_md`: v14 → v15/pending; note rewritten
- `scaffolding_files.Playbook_md`: pending → true (H-016's §13 landed at commit 66def97)
- `scaffolding_files.DecisionJournal_md`: still pending (D-030 added this session); note updated
- `scaffolding_files.Handoff_H016_md`: pending → true (operator commit e6c4deb during H-017)
- `scaffolding_files.Handoff_H017_md`: **new**, pending

Prose sections updated:
- "Where the project is right now" — fully refreshed for H-017 close
- "What changed in H-016" — replaced with "What changed in H-017" section
- "H-017 starting conditions" → renamed/rewritten as "H-018 starting conditions"
- "Validation posture going forward" — refreshed for H-018's application surfaces (retrospective for H-017 artifacts; preventive for main-sweeps code-turn; preventive for I-017 disposition; surface POD-H017-D029-mechanism per D-030 Resolution path)

---

## 8. Open questions requiring operator input

**Pending operator decisions at session close: 1.**

- **POD-H017-D029-mechanism** — opened by D-030. Question: how should D-029's push mechanism actually work given Claude.ai's sandbox environment has no access to Render env vars? Not urgent; project operates correctly under the D-030 interim flow. Surface at each session-open per D-030 Resolution path.

Items carried forward from prior sessions, not specific to H-017:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Four plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, -2, -3, -4) — cut at next plan revision under Playbook §12.

Items H-018-Claude should raise at session open:

- **POD-H017-D029-mechanism resolution path check** per D-030: brief check whether GitHub MCP connector has appeared in Anthropic's registry; whether other sandbox-accessible secret-injection mechanisms have become available; whether operator preference has shifted. If any change is material, becomes its own targeted DJ entry. No urgency.
- **RAID I-017 disposition** (carried over from H-016 → H-017 → H-018). Two pre-existing TestVerifySportSlug failures; sev 4. Read `verify_sport_slug` in `src/capture/discovery.py` first, then surface the two options (update tests vs. update code) with a recommendation. Per H-016 standing instruction: don't rely on I-017's description as the full picture.

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Mostly clean but with one structural weakness. Read Handoff_H-016 in full. Read STATE v14 (YAML + prose). Cross-referenced repo state against handoff claims (verified H-016 commit bundle on main; surfaced that Handoff_H-016.md was not in any commit). Self-audit produced as a visible block at the start of the response. **Reading at session open was incomplete, however, and this caused the mid-session error.** Claude read the Playbook table of rituals and §1, §2, §4, §13 only — not §§3, 5, 6, 7, 8, 9, 10, 11, 12. The Playbook §2 (session-close) reading was particularly partial. The mid-session present_files error was the consequence of working from inferred ritual shape rather than complete ritual text.

**Cut-point discipline at session open:** No explicit cut taken at session open; Claude proceeded into the D-029 first-use validation as the natural first step of the H-016 next-action statement. In retrospect this was reasonable — D-029's first-use was the H-016 handoff's literal first item ("D-029 operator-side setup confirmation") — but it bypassed an opportunity to discuss session scope explicitly with operator. Path A cut was not taken until late in the session, after the present_files recovery.

**Pushback discipline:** Held throughout the session, including the difficult moments. When operator said "you push to Git staging with my approval," Claude pushed back rather than accept the implicit instruction (§3.2). When operator framed the present_files event as a "major red flag," Claude acknowledged the diagnosis rather than defending the action (§3.1). The discipline that held this together was specifically: surface uncertainty rather than rationalize it, name what's not known, ask before doing.

**Surfacing-not-rationalizing exercised throughout:**
- D-029 first-use validation surfaced the architectural gap before any push attempt rather than after a failed push.
- Three resolution paths for the PAT-to-sandbox gap were enumerated with explicit governance citations rather than picking a plausible-sounding one.
- When operator's "you push to Git staging with my approval" left the how-the-PAT-reaches-git question unresolved, Claude asked rather than assumed.
- When the present_files error was caught, Claude acknowledged the error class ("inferring rituals from snippets") rather than minimizing it.
- D-030 draft text was reviewed by operator before file production, with two specific carve-outs ("scope and carve-outs" + "what this decision does not decide") flagged proactively.

**Comprehensive re-read after the present_files event:** The single most valuable thing this session did. Surfaced specific recalibrations:
- §10 (out-of-session commit) explicitly permits operator commits of Claude-produced files; the e6c4deb commit was a permitted action, not an irregular event.
- §11.5.3 names "Claude surfaces a decision and proceeds as if resolved" as a tripwire — a discipline pattern Claude should hold tighter going forward.
- D-018 through D-022 (H-010 rulings) define the Phase 3 attempt 2 acceptance bar precisely: unit tests + operator code review + live verification (D-020); no acceptance on unit-tests alone (D-021); research-first form = research doc → operator review → code in subsequent turn (D-019).
- For main sweeps in H-018: per D-019, the §16 research-doc addendum is produced first, operator reviews it, then code in a subsequent turn. The H-016 handoff's "re-fetch SDK README at code-turn time, no exceptions" instruction is the active enforcement of D-016 commitment 2 / R-010.

**Pacing assessment:** Long session. Approximately three deliverables of value: D-030 (governance), the recovery from present_files (process), and the comprehensive re-read (knowledge). The Path A cut at close was the right call — after a long session with a process recovery, pushing into main sweeps (the highest-fabrication-risk surface in the project) would have been bad pacing. Lands longer than H-016 in time but with similar substantive density.

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. The present_files event was a Claude error caught and corrected, not a tripwire firing — the existing tripwire taxonomy doesn't capture "Claude infers a ritual from snippets" as a defined tripwire.
**DJ entries added:** 1 (D-030). Total entries in journal: 30.
**RAID changes:** None. I-017 still open (carried forward).

**Quiet uncertainties carried into session close:** The DecisionJournal footer is stale (says "updated at H-009 ... next entry will be D-018") — has been stale since H-009; out of scope for this session but worth flagging for a future cleanup. The H-018 inheritance description in STATE is contingent on operator completing the bundle merge; if operator defers, H-018 self-audit will surface the discrepancy.

---

## 10. Next-action statement

**The next session's (H-018) first actions are:**

1. Accept handoff H-017.

2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-018 open the check applies in four modes:
   - **Retrospective for H-017 artifacts.** STATE v15, Handoff_H-017, DecisionJournal D-030, and the three deletions on `claude-staging` (or main, if merged). Spot-check that claims about commit SHAs, the D-030 entry text, the POD entry, and stale-artifact deletion match on-disk reality. If operator deferred any part of the bundle merge, the self-audit will surface the specific discrepancy.
   - **Preventive for main sweeps code-turn.** Main sweeps (§7 Q3=(c), the H-018 scope) is the first net-new SDK surface beyond probe.py's [A]-[D] citation block. Fabrication-risk surface: `client.markets.list()` and multi-subscription semantics on `markets_ws`. **Re-fetch `github.com/Polymarket/polymarket-us-python` README at code-turn time. No exceptions.** This instruction is now in its third consecutive handoff (H-015, H-016, H-017); H-018-Claude is the first to actually execute it.
   - **Preventive for I-017 disposition.** Read `verify_sport_slug` in `src/capture/discovery.py` before recommending which side to fix; don't rely on I-017's description as the full picture.
   - **Preventive for §16 research-doc addendum.** Per D-019, the addendum is research-first — it's produced first, operator reviews, then code follows in a subsequent turn. Don't conflate the addendum with the code.

3. **Raise three session-open items explicitly** before substantive work:
   - **POD-H017-D029-mechanism resolution path check** per D-030. Brief check whether anything has changed (GitHub MCP connector availability; sandbox-accessible secret-injection mechanisms; operator preferences). If material change, becomes a targeted DJ entry. If no change, note "POD-H017-D029-mechanism remains open; no path-change detected" and proceed.
   - **RAID I-017 disposition.** Read `verify_sport_slug`, surface the two options (update tests to expect RuntimeError vs. update code to raise SystemExit) with a recommendation. Small single-file fix either way; one of the H-018 deliverables.
   - **H-018 cut decision.** Operator names which deliverables are in scope. Default offer based on this handoff: I-017 fix + main sweeps research (research-doc §16 addendum) + operator review of §16 + main sweeps code in a subsequent turn after review. This is potentially a long session; cut conservatively if needed.

4. **Main sweeps per §7 Q3=(c)** when authorized. Shape: 1/2/5/10 subscriptions × 100 placeholder slugs × 1/2/4 concurrent connections. ~30 minutes runtime per configuration. Per §7 Q1=(a): no disk writes of received tick content. Per D-021 testing posture: unit tests + operator code review + live smoke run constitute acceptance bar. Expected new module: `src/stress_test/sweeps.py` or equivalent. Slug source per D-025 branch-selected at H-016: api-sourced via `client.markets.list()` as default, with gateway-sourced as fallback if needed. **D-019 research-first sequencing:** §16 addendum → operator review → code turn. Do not conflate.

5. **§16 research-doc addendum** to `docs/clob_asset_cap_stress_test_research.md`. Written before the main-sweeps code turn, not after.

6. **Session-close per Playbook §2** — STATE v16, Handoff_H-018, DJ entries for any new numbered decisions.

**Phase 3 attempt 2 starting state at H-018 session open:**

- Repo on `main` with the H-017 bundle merged (assuming operator completes the merge): STATE v15. DJ at 30 entries (last D-030). Handoff_H-017. Three stale H-016 artifacts deleted from repo root.
- Live `pm-tennis-api` service with I-016 fix deployed.
- Live `pm-tennis-stress-test` service; one successful probe in its history.
- One pending operator decision: POD-H017-D029-mechanism (low urgency).
- §14 of research-doc populated; §16 is the next slot.
- Four plan-text pending revisions in STATE (v4.1-candidate, -2, -3, -4).
- D-030 interim flow is the default deployment mechanism. `claude-staging` branch exists; merge gate is operator-only.
- Eight consecutive sessions (H-010 through H-017) closed without firing a tripwire or invoking OOP.
- Research-first discipline in force per D-016, D-019.
- 'Always replace, never patch' file-delivery discipline in force per H-016.
- SECRETS_POLICY §A.6 in force.
- D-028 active. D-027 active. D-025 commitment 1 superseded by D-027; 2/3/4 in force. D-024, D-023, D-020, D-019, D-018, D-016 in force. D-029 active but Commitment §2 suspended pending POD-H017-D029-mechanism resolution per D-030. D-030 active.

---

*End of handoff H-017.*
