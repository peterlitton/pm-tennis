# PM-Tennis Session Handoff — H-015

**Session type:** Phase 3 attempt 2 — live probe attempt (blocked on calendar + I-016 finding)
**Handoff ID:** H-015
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** Cut held: probe + §14 addendum this session, main-sweeps deferred to H-016. Probe attempt blocked at Step 1 (slug selection) — `slug_selector.list_candidates()` returned empty. Two operator-authorized diagnostics revealed both an external block (no eligible matches in next ~24h, operator-confirmed) and a real Phase-2 data-extraction issue (`event_date` empty in meta.json). RAID I-016 filed (sev 6). DJ unchanged at 27 entries. No SDK calls, no live network traffic, no tripwires fired, no OOP events. H-016 picks up with I-016 investigation as first action, then probe retry.

---

## 1. What this session accomplished

H-015 opened from the H-014 handoff with no operator-direction discrepancies; STATE v12 was fully on disk along with the rest of the H-014 commit bundle (5 files, 5 commits, all SHAs verifiable in `git log`). The session-open self-audit ran cleanly; the retrospective fabrication check (38/38 stress-test tests in fresh venv against pinned deps) passed and confirmed H-014's load-bearing claim that the suite is not decaying.

Per operator direction at session open ("read please. the more information you have the more value you will add to the project"), H-015-Claude expanded the reading from H-014-Claude's recommended subset (probe.py, RB-002, README, research-doc §15) to include also Playbook §1-§7, DecisionJournal entries D-016 through D-027, RAID Issues + Decisions, SECRETS_POLICY §A.5-A.7, and research-doc §7 Q1-Q5'. The full reading completed before any substantive work.

Operator ruled the cut at session open: **probe + §14 addendum this session; main-sweeps deferred to H-016.** Consistent with H-014-Claude's default offer in the addendum notes; consistent with H-010 → H-014 pacing discipline.

### Work that landed

| Item | Status |
|------|--------|
| H-014 handoff accepted; full reading per operator direction | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + H-009 fabrication-check standing direction | ✅ Complete — handoff/STATE cross-reference clean; commit-bundle integrity confirmed (5 files, 5 commits, no v11/v12-style discrepancy) |
| Repo clone | ✅ `git clone https://github.com/peterlitton/pm-tennis.git` per standing authorization (six sessions of practice now) |
| Retrospective fabrication check | ✅ 38/38 tests pass in fresh venv against pinned deps; confirms H-014's claim |
| Cut-point ruling at session open | ✅ Operator ruled: probe + §14 addendum; main-sweeps to H-016 |
| Step 1 — slug selection in pm-tennis-api Shell | ⚠️ Blocked — `list_candidates()` returned empty after operator overcame two bracketed-paste failures with the helper snippet |
| Diagnostic A (operator-authorized) | ✅ Confirmed system healthy — 116 event dirs on disk, monotonic growth from H-012's 74 |
| Diagnostic B (operator-authorized, heredoc workaround) | ✅ Surfaced the I-016 finding — 10 most-recent meta.json files have empty `event_date` despite titles encoding the date |
| Step 2 — probe execution in pm-tennis-stress-test Shell | ❌ Not run — blocked by Step 1 |
| §14 addendum (probe outcome) | ❌ Not written — no probe ran. Per operator ruling, §14 stays reserved (not a placeholder) |
| RAID I-016 filed | ✅ Sev 6, with full root-cause description, H-016 action items, and workaround |
| RAID header bumped to H-015 close | ✅ Complete |
| STATE v12 → v13 | ✅ YAML validates clean; phase bumped to `phase-3-attempt-2-probe-blocked-on-calendar`; counters advanced; resolved_operator_decisions pruned per H-014 convention; +9 phase_3_attempt_2_notes; H-014 scaffolding flips pending→true with commit SHAs; STATE v13 + Handoff_H-015 + RAID-with-I-016 added as pending |
| Handoff_H-015 production | ✅ This document |

### Counters at session close

- OOP events cumulative: **0** (unchanged)
- Tripwires fired: **0** (unchanged)
- Tripwires fired in H-015: 0 (three preventive-mode disciplines without firing — see §6)
- DJ entries: **27** (unchanged — operator ruling: I-016 to RAID, not DJ)
- RAID open issues: **14** of 16 total (was 13 of 15; +I-016 filed at H-015)
- Pending operator decisions: **0**

---

## 2. Decisions made this session

No numbered DecisionJournal entries were added this session. Five operator rulings (one explicit at session open, four during the work) and one delegated-authority sub-ruling were made in-session; all are on method/convention rather than project-shape commitments, and per DJ conventions they don't reach the DJ-entry threshold. They are recorded in STATE's `resolved_operator_decisions_current_session` and expanded here for future-session visibility.

- **H-015-cut-point** — Operator ruled at session open: probe + §14 addendum this session; main-sweeps deferred to H-016. Consistent with H-014-Claude's default offer in the addendum notes. Critically, the cut held even after the probe was blocked — H-015 did NOT extend silently into "let me just investigate I-016 a little while we're here." Investigation goes to H-016 as its first action, with the I-016 finding documented as the handoff to that work.

- **H-015-section-14-stays-reserved** — In-session ruling: §14 of research doc remains reserved (option a), not a placeholder for the H-015 attempt (option b). Rationale operator ratified: §14 should mean "probe outcome from a probe that ran." H-015 attempt + calendar block + I-016 finding documented in Handoff_H-015 §3 and STATE v13 (correct location for session-specific events per the prose-vs-YAML discipline). H-016 writes §14 when an actual probe runs.

- **H-015-diagnostic-execution** — Operator authorized two diagnostics in the pm-tennis-api Shell to confirm the system-vs-calendar attribution after `list_candidates()` returned empty. Diagnostic A (count + list event dirs) returned 116 dirs, healthy growth. Diagnostic B (sample 10 meta.json files) — after a heredoc workaround for bracketed-paste — surfaced the I-016 finding.

- **H-015-RAID-vs-DJ-classification-of-I-016** — Operator ruling at session close: I-016 (empty event_date in meta.json) goes to RAID, not DJ. Explicit reasoning: the finding cannot be validated for some time (depends on Phase-2 raw payload inspection); RAID is the right home for an issue awaiting validation. DJ stays at 27 entries with no H-015 additions.

- **H-015-helper-snippet-friction-surface** — In-session note (no operator ruling required): first operator use of the H-014 sub-ruling pasted-snippet helper convention (RB-002 §5.1) produced two failed pastes due to bracketed-paste markers in the Render Shell. Diagnostic B initially failed for the same reason; heredoc workaround succeeded. Strong empirical evidence — stronger than H-014 had — that converting the helper to a committed `src/stress_test/list_candidates.py` file is worth doing at H-016. NOT flipped this session to honor the cut-point ruling. Surfaced for H-016 explicit consideration.

**One sub-ruling under delegated authority by H-015-Claude:** when operator said "for B please present script," I read it as "show the script content for the operator to run via heredoc workaround" rather than "commit a helper file to the repo," and explicitly surfaced the two readings before acting. Operator's subsequent action (running the heredoc successfully) confirmed reading 1 was correct. Documenting because delegated-authority calls are exactly what the H-014 helper-snippet flag was about — surface before acting, even when the smaller cut feels obvious.

---

## 3. Pushback and clarification events this session

Worth naming for future-Claude visibility.

### 3.1 Empty `list_candidates()` result not silently rationalized

When Step 1 returned empty, the easy path would have been to say "no eligible matches today, try tomorrow, close the session." Operator stated knowledge that "no active games for the next ~24hrs" appeared to confirm that read. **But the deeper diagnostic surfaced something the operator's calendar knowledge could not have known: empty `event_date` fields across all sampled meta.json files.** The H-008 fabrication-class failure mode is "writing code that references names Claude never verified exist"; the symmetrical research-first failure mode at the operations level is "accepting plausible-sounding explanations without verifying them against ground truth." Diagnostic A + B were a small extension of the cut to verify the explanation against ground truth before closing — and they paid off with a real, separate, previously-undetected Phase-2 data-quality issue.

### 3.2 Bracketed-paste markers — two distinct multi-line-snippet failures

The H-014 sub-ruling pasted-snippet helper convention (RB-002 §5.1) failed twice on the same operator paste attempt due to bracketed-paste escape markers attaching `^[[200~` to the start of `PYTHONPATH=`. Bash interpreted the whole prefix as a non-existent filename. The simpler single-line invocation (operator was already at `/opt/render/project/src` so no `PYTHONPATH=` was needed) worked. Diagnostic B then failed the same way; a heredoc workaround succeeded. **Two distinct multi-line snippets, two distinct failures — same root cause.** This is meaningfully stronger evidence than H-014 had for converting to a committed helper file. H-014-Claude's flag at H-014 close — "if H-015 finds the pasted form awkward, the easy fix is to write `src/stress_test/list_candidates.py`" — is now empirically supported. H-015 honored the cut-point ruling and did not flip in-session; H-016-Claude should consider it explicitly at session open.

### 3.3 Cut held against extension temptation

When the probe was blocked, the natural temptation was to extend into "we're already in the file, let me just check the discovery.py extraction logic, write up the bug, maybe even prototype a fix." H-015-Claude declined the extension. The reasoning: (a) the cut-point ruling at session open was explicit and the close was clean; (b) Phase-2-touching changes require explicit operator authorization separate from the Phase 3 work package per D-016 / R-010; (c) H-016 is a better venue for the investigation because it can be that session's focused first action without the H-015 cognitive carryover. The discipline H-014-Claude flagged about pacing held: "Don't be the instance that breaks the streak by being optimistic about how much fits."

### 3.4 Surfacing-not-rationalizing applied to the operator's stated knowledge

When operator said "no active games for the next ~24hrs" and Diagnostic B then surfaced 10 events titled with "2026-04-20" dates and `active=True`, those two pieces of information looked inconsistent on first read. The temptation to rationalize ("operator must mean something different by 'active'") was resisted; the inconsistency was surfaced explicitly with three named possible reconciliations (operator right + extraction bug; extraction bug only; both). Operator's subsequent clarification ("they are future games") confirmed the reconciliation as both — operator's calendar knowledge was right AND the extraction is broken — and H-015 proceeded to file I-016 against the second issue without rewriting either piece of information silently.

---

## 4. Files created / modified this session

| File | Action | Notes |
|------|--------|-------|
| `RAID.md` | Modified | I-016 added to Issues table (sev 6, full root-cause description, H-016 action items including workaround). Header "Last updated" line bumped from H-010 to H-015 close 2026-04-19. Status: pending (session-close commit). |
| `STATE.md` | Modified (v12 → v13) | YAML: state_document v12→v13; session counters 14→15; phase.current bumped to `phase-3-attempt-2-probe-blocked-on-calendar`; phase.current_work_package rewritten; raid_entries_by_severity (sev_6 3→4, issues_open 13→14); pending_operator_decisions still []; resolved_operator_decisions_current_session pruned per H-014 convention and replaced with 5 H-015 entries; phase_3_attempt_2_notes +9 entries for H-015; scaffolding_files: H-014 entries flipped pending→true with commit SHAs (Handoff_H-014 → 087557d, README → 626a548, RB-002 → 9d47ef5, research-doc §15 → af5885e), STATE v12 entry updated to v13/pending, RAID entry flipped pending with H-015 note, new Handoff_H015 entry added pending. Prose: "Where the project is right now" refreshed; new "What changed in H-015" section added; "H-015 starting conditions" renamed to "H-016 starting conditions" and refreshed; "Validation posture going forward" refreshed for H-016's three application surfaces. Old v12 prose orphan deleted from below the v13 end-marker. YAML validates clean. Status: pending (session-close commit). |
| `Handoff_H-015.md` | Created | This document. Status: pending (session-close commit). |

**No modifications to:**

- `src/stress_test/probe.py` — read-only inspection (full 765 lines, especially classification logic in `_run_probe_async` lines 360-584). H-013 code unchanged.
- `src/stress_test/slug_selector.py` — read-only inspection (lines 142-156 `_passes_date_filter`; lines 159-176 `_candidate_from_meta`). H-013 code unchanged. Confirms the empty-event_date rejection is correct defensive behavior.
- `src/stress_test/README.md` — read-only inspection. H-014 rewrite unchanged.
- `runbooks/Runbook_RB-002_Stress_Test_Service.md` — read-only inspection. H-014 rewrite unchanged.
- `docs/clob_asset_cap_stress_test_research.md` — read-only inspection (§7 Q1-Q5', §15 full additive). §14 remains reserved per H-015 ruling.
- `src/capture/discovery.py` — read-only inspection of line 328 only (`event_date=str(event.get("eventDate") or "").strip()`) and line 159 (TennisEventMeta dataclass field). Phase 2 code preserved per D-016. **No fix attempted in H-015**; investigation + fix proposal goes to H-016 as its first action.
- `main.py` — untouched. Still at SHA `ceeb5f29...`, 2,989 bytes, 87 lines, version `0.1.0-phase2`.
- `/requirements.txt` (repo root) — untouched. D-024 commitment 1 holds.
- `DecisionJournal.md` — no entries added per operator ruling. Counter remains at 27.
- `PreCommitmentRegister.md` — not touched.
- Any commitment file. `signal_thresholds.json` still does not exist.
- `PM-Tennis_Build_Plan_v4.docx` — plan-text patches remain queued in STATE `pending_revisions` (unchanged from H-014).
- Previous handoffs (`Handoff_H-010.md` through `Handoff_H-014.md`) — preserved as-is.

**Operator's commit action at session close:** upload STATE.md (v13), Handoff_H-015.md, RAID.md (with I-016). Three files total.

---

## 5. Known-stale artifacts at session close

**None.** I-016 documents the empty `event_date` finding but does not flag the artifact as stale — `discovery.py` line 328's behavior is captured accurately in I-016's description. The fix (or workaround) is H-016's work; the issue is filed correctly.

---

## 6. Tripwire events this session

Zero tripwires fired. Zero OOP invocations. Session ran entirely within protocol.

Three moments exercised research-first / pacing discipline preventively without firing tripwires:

- **The H-008 fabrication-class danger zone was kept saved for H-016 by honoring the cut-point even after the probe was blocked.** No extension into "let me just investigate I-016 a little while we're here." This is the discipline H-014-Claude flagged: "Don't be the instance that breaks the streak by being optimistic about how much fits."

- **Diagnostic B was not silently re-attempted after the bracketed-paste failure.** Surfaced the friction explicitly, named two reconciliation paths (Path 1 retry with workaround, Path 2 declare A sufficient), and sought operator ruling rather than picking. Operator chose the heredoc workaround.

- **The empty-list result was not silently rationalized.** Two diagnostics were proposed and operator-authorized rather than accepting the plausible-sounding "calendar empty, fine, move on" explanation at face value. Diagnostic B revealed the I-016 finding that the operator's calendar knowledge could not have surfaced.

---

## 7. STATE diff summary (v12 → v13)

Key fields that changed:

- `project.state_document.current_version`: 12 → 13
- `project.state_document.last_updated_by_session`: H-014 → H-015
- `phase.current`: `phase-3-attempt-2-service-provisioned` → `phase-3-attempt-2-probe-blocked-on-calendar`
- `phase.current_work_package`: rewritten to reflect H-015 attempt + outcome and H-016 pickup
- `sessions.last_handoff_id`: H-014 → H-015
- `sessions.next_handoff_id`: H-015 → H-016
- `sessions.sessions_count`: 14 → 15
- `open_items.raid_entries_by_severity.sev_6`: 3 → 4
- `open_items.raid_entries_by_severity.issues_open`: 13 → 14
- `open_items.pending_operator_decisions`: still `[]`
- `open_items.resolved_operator_decisions_current_session`: **pruned** per H-014 settled convention (H-014 entries removed); replaced with 5 H-015 entries (cut-point, section-14-stays-reserved, diagnostic-execution, RAID-vs-DJ-classification-of-I-016, helper-snippet-friction-surface)
- `open_items.phase_3_attempt_2_notes`: +9 entries for H-015
- `scaffolding_files.STATE_md`: v12 → v13/pending; note rewritten
- `scaffolding_files.RAID_md`: committed_to_repo true → pending; note added
- `scaffolding_files.clob_asset_cap_stress_test_research_md`: committed_to_repo pending → true (commit af5885e)
- `scaffolding_files.Handoff_H014_md`: committed_to_repo pending → true (commit 087557d)
- `scaffolding_files.Handoff_H015_md`: **new**, pending
- `phase_3_attempt_2_files.src_stress_test_README_md`: status pending → committed (commit 626a548)

Prose sections updated:
- "Where the project is right now" — refreshed for H-015 close; probe-blocked + I-016 + helper-snippet-friction surfaced.
- "What changed in H-014" — preserved as historical; new "What changed in H-015" section added.
- "H-015 starting conditions" → renamed "H-016 starting conditions" and refreshed.
- "Validation posture going forward" — refreshed with H-016's three application surfaces (I-016 investigation, probe retry, retrospective for H-015 artifacts).
- Orphan v12 prose blocks below the new v13 end-marker were deleted.

---

## 8. Open questions requiring operator input

**Zero pending operator decisions blocking H-016's start.** `pending_operator_decisions` is empty.

Items carried forward from prior sessions, not specific to H-015:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Three plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, v4.1-candidate-2, v4.1-candidate-3) — cut at next plan revision under Playbook §12.

Items H-016-Claude should raise at session open:

- **Helper-snippet convention flip.** Two empirical multi-line-paste failures this session (helper snippet + Diagnostic B) provide stronger evidence than H-014 had for converting the H-014 sub-ruling pasted snippet to a committed `src/stress_test/list_candidates.py` file invocable as `python -m src.stress_test.list_candidates`. The benefit: removes the multi-line-paste failure mode entirely; tests are easy to write; aligns with the rest of the package's pattern. The cost: a small new file. H-016-Claude should explicitly raise this at session open and seek operator ruling before investigating I-016, because if the flip is approved it can be bundled with the I-016 work.

- **I-016 fix authorization.** I-016 names `src/capture/discovery.py` line 328 as the likely root cause. Phase 2 code is preserved per D-016 — any actual fix to `discovery.py` is a Phase-2-touching change requiring explicit operator authorization separate from the Phase 3 attempt 2 work package. H-016-Claude should investigate and propose, then seek operator ruling on whether to fix in `discovery.py` (clean fix) or to apply the title-date workaround in `slug_selector` only (no Phase-2 touch, but the underlying meta.json file remains incorrect for any other consumer of `event_date`).

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Clean. Read H-014 handoff + addendum notes in full. Read STATE v12 (YAML + prose). Cross-referenced H-014 commit-bundle integrity against `git log` (5 commits, 5 artifacts, all SHAs verifiable). No discrepancies surfaced. Self-audit produced as a visible block at the start of the response.

**Reading expansion under operator direction:** Operator directed full reading at session open ("read please. the more information you have the more value you will add to the project"). H-015-Claude expanded from H-014-Claude's recommended subset (probe.py, RB-002, README, research-doc §15) to include also Playbook §1-§7, DecisionJournal D-016 through D-027, RAID Issues + Decisions, SECRETS_POLICY §A.5-A.7, and research-doc §7 Q1-Q5'. The full reading completed before any substantive work. Reading-completion announcement was a structured block enumerating what was read in load-bearing order.

**Cut-point discipline at session open:** Honored H-014-Claude's default offer (probe + §14, defer main-sweeps). Operator ruled the cut explicitly. Cut held throughout the session even when the probe was blocked — the temptation to extend into "let me just investigate I-016 while we're here" was named explicitly and declined. Investigation goes to H-016 as its focused first action.

**Retrospective fabrication check:** Executed at session open against H-013 + H-014 code. 38/38 tests pass in fresh venv against pinned deps. Sixth consecutive session of clean discipline (H-010 → H-015).

**Surfacing-not-rationalizing applied to operator's stated knowledge:** When Diagnostic B surfaced apparent inconsistency between operator's "no active games for ~24h" and 10 events titled with 2026-04-20 dates and active=True, three named reconciliations were surfaced explicitly with operator-input requested rather than picking the plausible-sounding one. Operator's clarification ("they are future games") confirmed the both-explanations-true reading and H-015 proceeded to file I-016 against the data-quality side without silently rewriting either piece.

**Bracketed-paste friction handled in research-first mode:** When the helper snippet failed twice with `^[[200~` markers, H-015-Claude diagnosed the cause from the actual paste output (bracketed-paste markers attached to PYTHONPATH=) rather than guessing at "maybe try sudo" or other speculative fixes. Proposed a simpler invocation that worked. When Diagnostic B failed the same way, proposed a heredoc workaround with explicit reasoning rather than suggesting operator type the multi-line snippet manually. The friction surfaced an empirical case for H-016 to consider flipping the H-014 sub-ruling helper-convention.

**Delegated-authority discipline:** When operator said "for B please present script," read it as the smaller cut (show script content via heredoc) rather than scope expansion (commit a helper file). Surfaced both readings before acting; operator's subsequent action confirmed the smaller cut was correct. Recording explicitly because delegated-authority calls are exactly what H-014-Claude's helper-snippet flag was about — surface, don't assume.

**Session-close discipline:** STATE v13 produced with YAML validation passing (all material fields verified including counters, phase, RAID counts, pruning, scaffolding flips). Full handoff per Playbook §2.3 step 6. Pruning convention applied per H-014 settled convention. Old v12 prose orphan cleanly deleted from below the v13 end-marker.

**Known quiet-uncertainties carried into session close:** None. The H-015-helper-snippet-friction is explicitly surfaced for H-016 explicit consideration. The I-016 root-cause attribution to `discovery.py` line 328 was verified by reading the actual code (and by reading `slug_selector._passes_date_filter` lines 142-156 to confirm the rejection is correct defensive behavior, not selector bug). The H-015-cut-held-against-extension-temptation is documented in §3.3.

**Pacing assessment:** Short-to-moderate session. Substantive middle was modest in lines-of-output but high in cognitive load (full reading expansion + diagnostic-driven investigation + cut-discipline against extension temptation + RAID entry filing). No ruling under fatigue. Lands shorter than H-014, longer than the minimum-viable form a probe-blocked session could have produced — the I-016 finding adds real value to H-016's start.

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. Three preventive-mode disciplines without firing.
**DJ entries added:** 0 (operator ruling: I-016 to RAID, not DJ). Total entries in journal: 27.
**RAID changes:** +1 (I-016 added, sev 6).

---

## 10. Next-action statement

**The next session's (H-016) first actions are:**

1. Accept handoff H-015.

2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-016 open the check applies in three modes:
   - **Retrospective for H-015 artifacts.** Spot-check that I-016's claims about `discovery.py` line 328 and `slug_selector._passes_date_filter` lines 142-156 actually match the on-disk code. STATE v13 + Handoff_H-015 + RAID I-016 should pass the check without surprise.
   - **Preventive for I-016 investigation.** The investigation requires reading `discovery.py` extraction code and a sample raw gateway event payload. Read-only operations; fabrication risk is in *interpretation* — identifying the "right" key name for the date should be cited from the actual operator-pasted payload byte-content, not from memory or documentation that may not match payload shape.
   - **Preventive for any code that does land.** If H-016 produces a fix to `discovery.py` (after operator authorization), the change is Phase-2-touching and must follow doc-code-coupling per Orientation §8 (any plan-text references to event_date behavior get checked).

3. **Raise the helper-snippet convention flip explicitly at session open.** Two empirical paste failures this session (helper snippet + Diagnostic B) are stronger evidence than H-014 had. Surface to operator: convert pasted snippet to committed `src/stress_test/list_candidates.py` invocable as `python -m src.stress_test.list_candidates`? Seek operator ruling before any other H-016 work — if approved, the new file can be bundled with the I-016 fix.

4. **I-016 investigation as the first substantive action.** In pm-tennis-api Shell (operator-executed): inspect a sample raw gateway event payload from `/data/events/2026-04-19.jsonl` (or current day's file) to identify what key name(s) the date lives under in the actual payload. Likely candidates: `startDate`, `startTime`, derived from a nested participant/market structure, or absent entirely (date encoded only in the slug or title). Reading is read-only; no commit-blocking risk. After identifying the correct key, propose the fix to operator and seek explicit authorization before modifying `discovery.py` (per D-016 Phase 2 preservation).

5. **Probe retry per RB-002 §5.** Once I-016 is fixed (or the workaround applied in `slug_selector` only, depending on operator ruling), retry the two-shell workflow. Per the helper-snippet ruling at #3 above, the slug-selection step may use either the pasted snippet (if the convention is held) or `python -m src.stress_test.list_candidates` (if flipped). Calendar permitting (eligible matches must exist for the next ~24h), the probe runs and returns a `ProbeOutcome` JSON. Per D-025 commitment 4: if `classification == "ambiguous"`, do NOT silently resolve.

6. **§14 addendum (probe outcome).** Written after live probe result is in hand. Content: probe input (slug, event_id, candidate-count, timestamp), probe output (full ProbeOutcome JSON reproduced), classification, classification_reason, interpretation, and the main-sweep-slug-source decision D-025 branch selected.

7. **Main-sweeps remains queued for H-017.** Do NOT pull main-sweeps forward to H-016 unless I-016 + probe retry close cleanly with significant time remaining and operator explicitly approves the extension. Per H-014 + H-015 pacing discipline, main-sweeps deserves its own session — first net-new SDK surfaces beyond probe.py's current citation block (`client.markets.list()`, multi-subscription semantics), and the SDK README must be re-fetched at code-turn time per H-014-Claude's emphatic note.

8. **Session-close per Playbook §2** — STATE v14, Handoff_H-016, DJ entries for any new numbered decisions (a new D-028 is plausible if the I-016 fix authorization or the helper-snippet convention flip reach DJ-entry threshold; depends on operator ruling).

**Phase 3 attempt 2 starting state at H-016 session open:**

- Repo on `main` with H-013 + H-014 + H-015 bundles landed: STATE v13, DecisionJournal at 27 entries (last D-027), Handoff_H-015, RAID with I-016 newly filed (14 open issues, 16 total).
- Discovery service `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`, healthy. Event count 116+ at H-015 close; will continue to grow.
- Stress-test service `pm-tennis-stress-test.onrender.com` live; self-check expected green (no code changes touching the service this session).
- Zero Phase 3 production code on `main` in `src/capture/` (Phase 2 preserved). Phase 3 probe code in `src/stress_test/` — isolated per D-020 / D-024 commitment 1.
- I-016 (empty event_date) waiting for investigation as the first substantive action; Phase-2 fix authorization is the gating decision.
- Helper-snippet convention flip waiting for explicit consideration at H-016 open.
- §14 of research doc still reserved for the probe-outcome addendum.
- **Zero pending operator decisions in STATE `open_items.pending_operator_decisions`.**
- Three plan-text pending revisions in STATE unchanged.
- Research-first discipline in force per D-016, D-019, reinforced by H-015's evidence trail (cut-held-against-extension; surfacing-not-rationalizing on operator stated knowledge; bracketed-paste-friction handled by diagnosis + workaround).
- SECRETS_POLICY §A.6 guard operating — H-015 did not exercise it (no probe ran; no credential paths touched); discipline holds vacuously.
- D-027 active; D-025 commitment 1 superseded; D-025 commitments 2/3/4, D-024, D-023, D-020, D-018, D-019 in force.
- Pruning convention for `resolved_operator_decisions_current_session`: stricter reading, settled.
- Six consecutive sessions (H-010 through H-015) closed without firing a tripwire or invoking OOP.

---

*End of handoff H-015.*
