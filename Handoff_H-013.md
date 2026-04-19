# PM-Tennis Session Handoff — H-013

**Session type:** Phase 3 attempt 2 — code turn (SDK research + probe scaffolding + CLI tests)
**Handoff ID:** H-013
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** All three code-turn research tasks resolved against authoritative sources. Probe scaffolding + slug_selector + 38 unit tests written and passing. Render disk-sharing architecture validated against docs and found not to support the D-025 commitment 1 shared-disk pattern; D-027 journals the supersession and operator-ruled Option D (CLI-supplied slug). Render service was NOT stood up this session — operator's Option X cut deferred that and the doc-update work (RB-002 Steps 3/5, stress_test/README.md) to H-014.

---

## 1. What this session accomplished

H-013 opened from the H-012 handoff into the code turn. Operator accepted the smaller-cut recommendation at session open (SDK source research + auth + probe scaffolding this session; main sweeps + live execution deferred to H-014), then over the course of the session ruled on: in-session scope adjustments (stand up Render service this session — later reversed), Render disk architecture question (Option D), and D-025-supersession-vs-re-interpretation (Supersession).

### Work that landed

| Item | Status |
|------|--------|
| H-012 handoff accepted | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + H-009 fabrication-check standing direction | ✅ Complete (read-out in session transcript) |
| Repo clone | ✅ `git clone https://github.com/peterlitton/pm-tennis.git` per H-012 addendum standing guidance |
| Governance-fingerprint spot-check | ✅ STATE v10 fields match D-004 through D-016 intent |
| Research task 1: SDK Ed25519 signing-surface exposure (D-024 comm. 4a) | ✅ Resolved — "trust the SDK." Fully internal; no user-code signing surface. Backed by `pynacl` per pip dry-run. Authoritative citations: SDK README + `docs.polymarket.us/api-reference/authentication`. |
| Research task 2: timestamp-unit cross-check (D-024 comm. 4b) | ✅ Resolved — milliseconds, unambiguous. Authentication page table row now reads literally "X-PM-Timestamp: Current time in milliseconds." The earlier "30 seconds of server time" phrasing is still present but pinned by the unit table row. No contradiction. |
| Research task 3: SDK transitive deps (H-012 addendum quiet-uncertainty) | ✅ Resolved — 12 packages total. Direct: `httpx>=0.27.0`, `pynacl>=1.5.0`, `websockets>=12.0`. Transitives are standard (`httpcore`, `anyio`, `idna`, `certifi`, `h11`, `typing_extensions`, `cffi`, `pycparser`). Wheels available for Linux/x86_64 + CPython 3.12; no compile required. Verified by `pip install --dry-run --report` in a clean venv. |
| Probe scaffolding code | ✅ Written: `src/stress_test/{__init__.py, probe.py, slug_selector.py, requirements.txt, README.md}`. Every SDK symbol traced to the fetched README in-line in the probe.py header citations block. |
| Unit tests for slug_selector | ✅ 19 tests covering positive, negative, filter-by-status, filter-by-date, malformed JSON, empty states, multi-market edge case, and realistic H-012-survey-shape dict. |
| Unit tests for probe CLI | ✅ 19 tests covering argparse, config-error path, NO_CANDIDATE path, config-checked-before-slug precedence, main() dispatch, ProbeOutcome dataclass, classification-to-exit-code mapping, ProbeConfig observation-seconds clamping. |
| All tests passing | ✅ 38/38 after D-027 refactor. Zero mocking of the SDK — per H-012 addendum, SDK-mocking would hide the drift class that killed H-008. Network-touching path deferred to H-014 live smoke. |
| End-to-end smoke of self-check and all probe-mode exit paths | ✅ Verified locally via direct module invocation: self-check (no creds / no disk) clean; `--probe --slug=... ` with no creds exits `EXIT_CONFIG_ERROR`; `--probe` with no `--slug` and empty disk exits `EXIT_NO_CANDIDATE`; `--help` produces expected output. |
| Render disk-architecture validation | ✅ `render.com/docs/disks` fetched and authoritatively answers the question. Quote: "A persistent disk is accessible by only a single service instance, and only at runtime. This means: You can't access a service's disk from any other service." Closed Option A (shared/read-only attach) definitively. |
| D-025 commitment 1 → D-027 supersession | ✅ Journaled. D-025's footer updated per DJ conventions line 13. D-027 records the four-option consideration, Option D ruling, and full reasoning. |

### Work that was deliberately deferred at session close per operator's Option X cut

| Item | Reason deferred | Where it picks up |
|------|-----------------|-------------------|
| `src/stress_test/README.md` rewrite for D-027 | Written before D-027 was final; contains stale references to disk-based slug selection. Correcting it rushed at session close raises drift risk. | H-014 first task |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` Steps 3 + 5 rewrite | Step 3 ("attach disk") and Step 5 ("how to execute probe") are incorrect under D-027. H-013 operator ruled Option X (stop here) rather than patch-then-deploy under tool-budget pressure. | H-014 first task |
| Render service provisioning | Originally scoped into H-013 after operator ruled "stand up service this session" mid-session; subsequently deferred when the disk-architecture discovery reopened the design. Not attempted this session. | H-014 after RB-002 is correct |
| Research-doc §15 additive (or v5) capturing D-027 | Additive content is the same as the D-027 DJ entry + Handoff §3 narrative; redundant to write three times, and H-014 is the right place once the doc-update decisions are made together. | H-014 |

No tripwires fired. Zero OOP events this session. Counters remain: OOP cumulative 0, tripwires fired 0.

---

## 2. Decisions made this session

Full text of each entry in DecisionJournal.md. One-line summaries, newest first:

- **D-027** — Probe-slug transport: operator-supplied CLI argument (`--slug=SLUG`) via Option D; supersedes D-025 commitment 1's shared-disk read after Render docs confirmed disks are strictly single-service. D-025 commitments 2/3/4 unaffected. Research-question intent preserved. Operator ruled Supersession over Re-interpretation at explicit Claude request.

- **D-025** (modified) — Footer appended: `SUPERSEDED IN PART BY D-027`. Original decision text preserved in full per DJ convention line 13.

In-session operator rulings not recorded as separate DJ entries (scoped as rulings on H-013 internal method, not new commitments):

- **Cut-point ruling** (session open): smaller cut for H-013 — SDK research + auth + probe scaffolding this session; defer main sweeps and live execution to H-014.
- **Code-location ruling**: `src/stress_test/` inside the main repo; separate Render service for deployment (not separate repo).
- **Session-scope ruling** (mid-session): "stand up the service this session" — subsequently superseded by the Option X cut after the disk-architecture discovery.
- **Architecture-options ruling**: Option D of the four options surfaced after the Render disk-sharing research.
- **Supersession-vs-re-interpretation ruling**: Supersession, for precedent-setting-discipline reasons.
- **Session-close cut (Option X)**: stop after code + tests land; defer doc updates and deployment to H-014.

Each in-session ruling was surfaced with explicit options and a named recommendation before the operator responded. None were silent.

---

## 3. Pushback and clarification events this session

Several worth naming for future-Claude visibility.

### 3.1 Cut-point proposal at session open

The H-012 addendum explicitly warned that H-013 is a code turn and that optimistic whole-queue ambition is the H-008 shape of risk. At session open, after completing the self-audit and orientation, Claude declined to proceed directly into coding and instead surfaced an explicit cut-point proposal with three ways forward. Operator ruled the smaller cut. This is the H-011/H-012 pacing discipline being applied in a code turn. Not a pushback against operator direction — a pre-action scoping step.

### 3.2 SDK env-var-name mismatch surfaced pre-code

The SDK README shows `POLYMARKET_KEY_ID` / `POLYMARKET_SECRET_KEY` in its example usage. D-023 committed `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY`. Before writing any code that reads env vars, Claude surfaced the mismatch explicitly to operator with the plan to use the D-023 committed names (since env-var names are application-chosen, not enforced by the SDK, and D-023 names are what's actually in the Render dashboard). Operator approved "proceed." This is exactly the fabrication-avoidance pattern: name a near-miss where sloppy matching of the README could have shipped code that fails with `KeyError` at startup.

### 3.3 Render disk-architecture surface before runbook execution

Claude wrote RB-002 Step 3 (attach disk read-only to stress-test service) optimistically, flagged in the Runbook text itself that the disk-sharing capability was unverified, and in the companion chat message explicitly recommended running a web_search before operator executed RB-002. Operator approved "1" (search first). Search returned authoritative docs confirming Render disks are strictly single-service. This prevented a mid-deploy operator interruption that would have landed Claude in the classic "corrupting a live procedure to salvage the session" H-008 failure shape. Research-first discipline applied exactly where it was meant to apply — externally against Render's published capability, before an operator action.

### 3.4 Supersession-vs-re-interpretation offered as explicit choice

After operator ruled Option D, Claude surfaced an ambiguity in how D-027 should be journaled: as re-interpretation of D-025 commitment 1 (claiming the new architecture preserves the original's intent) or as supersession (formally replacing part of it). Claude gave its preference (re-interpretation) alongside the operator-favorable counter-argument (supersession is more conservative; better discipline) and asked for an explicit ruling. Operator ruled Supersession. This is the D-025 "most conservative" Q5′ pattern from H-012 applied in the other direction — operator-language-precision-by-asking rather than by under-qualifying. The ruling creates a useful precedent for future sessions: when design reality forces a commitment change, the default is supersession (named in a new numbered entry), not silent re-reading.

### 3.5 Option X close — session-scope discipline

Approaching session close, Claude offered the operator two options: (X) stop after code+tests land and defer README/RB-002/deployment to H-014; (Y) continue into doc updates and deployment this session. Claude named the primary risk of Y (end-of-session errors compounding) and the cost of X (known-stale artifacts flagged for H-014). Operator ruled X. This is the H-011/H-012 pacing discipline extended to session close — when the primary deliverable is done and scope drift is the main remaining risk, stopping is the correct move.

---

## 4. Files created / modified this session

| File | Action | Notes |
|------|--------|-------|
| `src/stress_test/__init__.py` | Created | Package init; version string `0.1.0-stress-test-h013`. |
| `src/stress_test/slug_selector.py` | Created + one post-D-027 fix | Reads `/data/matches/*/meta.json`, picks fresh probe candidate. Schema verified against `src/capture/discovery.py` `TennisEventMeta`. `datetime.utcnow()` → `datetime.now(timezone.utc)` fix for Python 3.12 deprecation noise. |
| `src/stress_test/probe.py` | Created + D-027 refactor | Entry point with self-check (default) and probe (`--probe --slug=...`) modes. Every SDK symbol traced to the README in a module-header citations block. `ProbeOutcome` dataclass written as structured JSON on stdout; classification mapped to exit code. After D-027 ruling: `--slug` and `--event-id` CLI flags added; `run_probe` reshaped with CLI-slug precedence over slug_selector fallback; self-check step 4 reworded to reflect "0 disk candidates is expected on Render per D-027." |
| `src/stress_test/requirements.txt` | Created | `polymarket-us==0.1.2` + `pytest==8.3.4`. Exact pin per operator ruling. Comment block explains transitive footprint (12 packages, no compile required). |
| `src/stress_test/README.md` | Created | ⚠️ **Stale as of D-027.** Still references disk-based slug selection. Flagged for H-014 first-task update. |
| `tests/test_stress_test_slug_selector.py` | Created | 19 tests covering positive/negative/filter-by-status/filter-by-date/malformed-JSON/empty/multi-market/realistic-survey-shape paths. Pure on-disk fixtures; no mocking. |
| `tests/test_stress_test_probe_cli.py` | Created | 19 tests covering argparse/config-error/NO_CANDIDATE/precedence/main-dispatch/dataclass/mapping/clamping. Zero SDK mocking per H-012 addendum guidance. |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` | Created | ⚠️ **Stale as of D-027.** Steps 3 (disk attach) and 5 (probe execution) written pre-D-027 and are now incorrect. Flagged for H-014 first-task rewrite. |
| `DecisionJournal.md` | Modified | D-027 prepended per newest-first convention; D-025 footer appended with SUPERSEDED IN PART BY language per DJ conventions line 13. Total entries 26 → 27 (D-025's supersession note is not a new numbered entry, it's a footer). |
| `STATE.md` | Modified | Bumped v10 → v11. See §7 STATE diff below. YAML validates. |
| `Handoff_H-013.md` | Created | This document. |

**No modifications to:**

- `src/capture/discovery.py` — read-only inspection only, no edits. Phase 2 code remains as committed at `17f44eb1` pre-H-013.
- `main.py` — untouched. Still at SHA `ceeb5f29…`, 2,989 bytes, 87 lines, version string `0.1.0-phase2`.
- `/requirements.txt` (repo root) — untouched. D-024 commitment 1 reinforced by D-027 Option D.
- `RAID.md` — no entries added, resolved, or edited.
- `PreCommitmentRegister.md` — not touched.
- Any commitment file (`fees.json`, `breakeven.json`, `data/sackmann/build_log.json`). `signal_thresholds.json` still does not exist.
- `PM-Tennis_Build_Plan_v4.docx` — plan-text patches remain queued in STATE `pending_revisions`, not applied this session.
- `docs/clob_asset_cap_stress_test_research.md` — v4 preserved as accepted; v5 (or §15 additive) deferred to H-014.
- Previous handoffs (`Handoff_H-010.md` through `Handoff_H-012.md`) — preserved as-is.

**Operator's commit action at session close:** upload DecisionJournal.md, STATE.md (v11), Handoff_H-013.md, and the following new files — `src/stress_test/__init__.py`, `src/stress_test/probe.py`, `src/stress_test/slug_selector.py`, `src/stress_test/requirements.txt`, `src/stress_test/README.md`, `tests/test_stress_test_slug_selector.py`, `tests/test_stress_test_probe_cli.py`, `runbooks/Runbook_RB-002_Stress_Test_Service.md`.

---

## 5. Known-stale artifacts committed this session

Per the Option X cut, two artifacts are landing with content known to be stale as of D-027. Both are flagged with the same first-task-of-H-014 treatment. Committing them is the right tradeoff under Option X because:

- The files are new (not pre-existing committed content that is drifting silently).
- Stale sections are narrowly scoped (Steps 3 and 5 in RB-002; a few paragraphs in README).
- The rest of each file is correct and useful as-is.
- H-013 closes with the stale content clearly named; H-014 opens with the update as a named next-action rather than a discovery.

The alternative — not committing these files this session and re-authoring them at H-014 — would have the side effect of the code landing without its documentation, which is worse.

### 5.1 `src/stress_test/README.md` stale content

- References `slug_selector.select_probe_slug()` as the production probe slug source. Under D-027 it is **not** the production path on the Render stress-test service; it is a local-development and pm-tennis-api-Shell-helper utility only.
- The "Running on Render" section describes the probe's slug selection as automatic. Under D-027 it requires explicit `--slug=SLUG` on the Shell invocation.
- Exit-code table still says `EXIT_NO_CANDIDATE` means "slug_selector returned []." Under D-027 it means "no `--slug` provided and slug_selector fallback also returned [] (expected on Render)."

### 5.2 `runbooks/Runbook_RB-002_Stress_Test_Service.md` stale content

- Step 3 ("Attach the persistent disk — read-only") is entirely superseded. The attach operation is not supported on Render (authoritative docs quoted above). Replacement: "Skip — no disk attached to stress-test service. Slug workflow is pm-tennis-api-Shell-assisted per Step 5."
- Step 5 ("How H-014 will execute the probe") describes the probe selecting its own slug from disk. Replacement: two-shell workflow — (a) operator runs a short Python snippet in `pm-tennis-api` Shell listing eligible candidates from `/data/matches/`; (b) operator copies the chosen slug + event_id; (c) operator switches to `pm-tennis-stress-test` Shell; (d) operator runs `python -m src.stress_test.probe --probe --slug=<SLUG> --event-id=<EID>`; (e) operator copies the outcome JSON back to chat.
- The fallback options A/B/C in Step 3 ("if Render doesn't support shared disks") are now inert — they proposed contingencies for a question that is definitively answered. Keeping them as a historical note is optional; cleaner to delete.

H-014 should rewrite both documents before touching deployment. Update order: `README.md` first (short, simpler), then `RB-002` (longer, has the procedural workflow), then deploy.

---

## 6. Tripwire events this session

Zero tripwires fired. Zero OOP invocations. Session ran entirely within protocol.

Three moments exercised research-first discipline preventively without firing:

- **SDK env-var-name mismatch** (§3.2): near-miss where mechanical matching of the SDK README's example would have produced code that fails with `KeyError` at startup because the committed env-var names are different. Caught pre-code by explicit comparison of README and D-023.
- **Render disk-architecture discovery** (§3.3): the whole Option-D ruling exists because Claude fetched Render's docs before an operator procedure rather than assuming the capability. The fetch returned authoritative contradictory-to-plan information. The response was to stop, surface, and ruling-solicit rather than adapt silently. This is the H-008 failure inverted.
- **SDK source-vs-README scope check**: the H-012 addendum warned specifically not to invent SDK method signatures beyond what the README shows. Claude fetched the README verbatim (one tool call), read the full method surface, and every SDK symbol in `probe.py` is cited against a specific line in the README. The `pip install --dry-run` check for transitive deps was a belt-and-suspenders confirmation that the installable package matches the README's promises.

The fabrication-failure-mode check was preventive-mode effective: `grep -r "polymarket_us\|polymarket-us" src/stress_test/` surfaces only imports and references consistent with the cited README and pip-verified package. Every name traces.

---

## 7. STATE diff summary (v10 → v11)

Key fields that changed:

- `project.state_document.current_version`: 10 → 11
- `project.state_document.last_updated_by_session`: H-012 → H-013
- `sessions.last_handoff_id`: H-012 → H-013
- `sessions.next_handoff_id`: H-013 → H-014
- `sessions.sessions_count`: 12 → 13
- `sessions.most_recent_session_date`: 2026-04-19 (unchanged — same calendar day as H-012, but session count reflects H-013 is distinct)
- `phase.current_work_package`: rewritten to reflect probe scaffolding complete, code-turn-research tasks resolved, D-027 architecture fixed, H-014 picks up with doc updates + deployment + main sweeps
- `open_items.pending_operator_decisions`: still empty (D-027 was ruled in-session; no open PODs carry into H-014)
- `open_items.resolved_operator_decisions_current_session`: rewritten with H-013 entries (cut-point, code-location, architecture-options, supersession, Option X close). H-012's preserved Q4 entry plus the three H-012 resolutions pruned per the stricter "current session only" reading (per Handoff_H-012 §8 flagged convention question; Claude making the call under delegated authority in the absence of an explicit operator ruling, documented here so it's visible)
- `open_items.phase_3_attempt_2_notes`: +several entries covering D-027, Render disk-architecture finding, probe scaffolding complete, known-stale artifacts flagged
- `scaffolding_files`: new entries for `src/stress_test/*` files, test files, Runbook RB-002; existing entries for `DecisionJournal_md`, `STATE_md`, `Handoff_H013_md` updated to pending-commit
- `runbooks`: RB-002 added (produced H-013, status: **draft — stale as of D-027, rewrite first-task H-014**)
- `architecture_notes`: +3 entries (Render disks strictly single-service; D-027 Option D; SDK Ed25519 signing is fully internal confirmed at H-013)
- `phase_3_files`: new section tracking the stress-test files separately from Phase 2's capture files

---

## 8. Open questions requiring operator input

**Zero pending operator decisions blocking H-014's start.** `pending_operator_decisions` is empty.

Governance-convention question re-raised from H-012 §8 for a future ruling, not urgent:

- **`resolved_operator_decisions_current_session` pruning policy.** H-012 preserved H-011's Q4 entry alongside the three H-012 resolutions with an explicit note flagging the ambiguity. H-013 pruned to current-session-only entries per the stricter reading — documented in §7 above so the call is visible. If operator wants the cumulative-across-recent-sessions reading instead, H-014 can revert the prune. Flagging for operator awareness again; not urgent.

Carried forward from prior sessions, not specific to H-013:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Three plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, v4.1-candidate-2, v4.1-candidate-3) — cut at next plan revision under Playbook §12.

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Clean. Read H-012 handoff in full (including §9 self-report and especially the H-012 addendum on code-turn pacing, SDK-source-not-just-README discipline, Ed25519 scope-through-SDK, timestamp-unit cross-check, probe slug freshness, /data/events vs /data/matches path correction, D-020 isolated-service discipline, delegated-authority conservatism, H-011 Q4 convention preservation flag, counters-to-watch). Cloned repo per H-012 addendum guidance in one shot. Produced self-audit and orientation from verified repo state. All spot-checks passed.

**Cut-point surfacing at session open:** Consistent with H-011/H-012 pacing discipline and H-012 addendum's specific warning about code turns. Proposed the smaller cut (research + auth + probe scaffolding this session) with explicit rationale and alternatives. Operator ruled the recommended cut.

**Research-first discipline at code-turn boundaries:** Three specific instances (§3.2, §3.3, §6) where the discipline was exercised preventively. The Render-docs fetch before operator ran RB-002 is the clearest case — it turned a hypothetical optimism ("shared disks might work") into authoritative knowledge ("they don't") before operator spent real time in the Render dashboard. Named in the transcript, acted on with a ruling request, logged here.

**D-027 supersession framing:** When D-025 commitment 1 became unimplementable, Claude surfaced Option A (violates D-024), Option B (violates D-020), Option C (literally-conflicts-with-D-025), Option D (preserves all commitments with operator-in-the-loop). Recommended D. Operator approved. Then, on the "re-interpretation vs supersession" question, Claude's own preference was re-interpretation but Claude recognized the precedent-setting concern and named it explicitly before asking the operator to rule. Operator ruled Supersession. The meta-discipline preserved: Claude does not use operator-delegated authority to soften committed language silently; when architecture reality forces a commitment to change, the change gets a numbered DJ entry.

**Code structure discipline:** Every SDK symbol referenced in `probe.py` is cited against a specific README section in the module-header comment block. `slug_selector.py` schema fields are cited against specific lines in `src/capture/discovery.py`. Import paths resolved successfully in a clean venv (`pip install polymarket-us==0.1.2`) before any non-trivial code was written against them. Test coverage is pure-fixture for slug_selector and pure-argparse/dataclass for probe CLI — zero SDK mocking, because the H-012 addendum and H-008 post-mortem agree that SDK mocks are the exact test pattern that hides fabrication.

**Session-close discipline (Option X):** Called the cut when primary work was done and remaining work carried real risk of end-of-session errors. Named the tradeoff honestly: code is in, tests are green, doc artifacts are known-stale-and-flagged, deployment is deferred. Better than rushing through README/RB-002/deployment with four more rulings-under-fatigue.

**Known quiet-uncertainty I carried into session close:** The `pruning convention` call in §7. H-012 §8 flagged this as a future-ruling question; no ruling has been given; Claude applied the stricter reading (current-session-only) at H-013 close and documented it for H-014 review. This is exactly the kind of call the H-012 addendum talked about — making the smaller conservative cut with visible audit trail rather than letting ambiguity sit or silently expanding it.

**Pacing assessment:** Session was moderate-to-long, about the same density as H-012. Substantive middle (three research-task resolutions, code scaffolding, 38 unit tests), one unexpected architecture-discovery beat (Render disks), one ruling sequence (Option D → Supersession), one session-close cut (Option X). Did not land deployment. Decision to defer deployment under Option X was correct — disk-architecture ruling happened mid-session, which means doc updates would have been under pressure, and shipping un-updated docs to production procedures is the H-008 attractive trap.

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. Three preventive-mode exercises of research-first discipline without firing.
**DJ entries added:** 1 numbered (D-027) + 1 footer modification (D-025). Total entries in journal: 27.

---

## 10. Next-action statement

**The next session's (H-014) first actions are:**

1. Accept handoff H-013.

2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-014 open the check is **active** — inspect `src/stress_test/` code committed by H-013 and verify: every SDK symbol traces to the Polymarket US Python SDK README (cited in `probe.py` header); every internal import (`from src.stress_test import slug_selector`, `from src.capture...` — actually `slug_selector` reads discovery.py schema only, does NOT import it, because schema-read-only via JSON is safer than coupling) resolves to actually-existing files; every env-var name (`POLYMARKET_US_API_KEY_ID`, `POLYMARKET_US_API_SECRET_KEY`) matches D-023. The D-027 path means the production probe invocation reads neither `/data/` nor `slug_selector`; confirm that. The fabrication-failure-mode check is preventive + retrospective here — preventive for any new code H-014 writes, retrospective for the code H-013 committed.

3. **Correct the known-stale artifacts** flagged in Handoff §5 before any deployment step:
   - Rewrite `src/stress_test/README.md` sections about slug selection, "Running on Render," and exit-code table per D-027.
   - Rewrite `runbooks/Runbook_RB-002_Stress_Test_Service.md` Steps 3 and 5 per D-027. Step 3 becomes "Skip — no disk attach for stress-test service." Step 5 becomes the two-shell workflow (list candidates in pm-tennis-api Shell; run probe in pm-tennis-stress-test Shell with `--slug=<SLUG> --event-id=<EID>`).
   - Consider whether a small helper script lives in `src/stress_test/list_candidates.py` for use in the pm-tennis-api Shell, or whether a single-line Python command pasted into the Shell is sufficient. Operator ruling or Claude-under-delegated-authority at H-014 open.

4. **Research-doc bump.** Decide §15 additive (cheap, preserves v4 accepted text) vs v5 bump. Recommendation is §15 additive given H-012 precedent, but if H-014 has other research-doc revisions coalescing, v5 makes sense. Content: D-027 summary, Render disk-architecture finding, probe-scaffolding-landed note, code-turn-research-tasks-resolved summary, forward reference to H-014 main sweeps.

5. **Render service provisioning** per updated RB-002. Create `pm-tennis-stress-test` service, add env vars, run self-check, verify self-check output matches expectations. No disk attach. Service start command: `python -m src.stress_test.probe` (self-check only; probe mode is manually invoked). Follow-up optional: change start command to `sh -c "python -m src.stress_test.probe && sleep 86400"` to avoid restart churn in logs, as discussed in original RB-002 Step 4's alternative.

6. **Live probe execution** per D-025 + D-027 + D-026:
   - In `pm-tennis-api` Shell, list eligible candidates from `/data/matches/*/meta.json` (freshly — the D-026 default slug 9392 is two days stale by now and may have ended).
   - Select freshest active not-ended not-live candidate.
   - In `pm-tennis-stress-test` Shell: `python -m src.stress_test.probe --probe --slug=<SLUG> --event-id=<EID>`.
   - Copy the `ProbeOutcome` JSON from stdout back to chat.
   - Claude logs outcome, classifies probe result, and decides (or surfaces to operator) the main-sweep slug source per D-025 hybrid-probe-first logic.

7. **Main sweeps** per §7 Q3=(c) — both per-subscription-count sweep and concurrent-connection-count sweep. Shape: 1/2/5/10 subs × 100 placeholder slugs × 1/2/4 concurrent connections. ~30 minutes. Code for sweeps is NOT yet written — this is H-014 code-turn work. Expected new module `src/stress_test/sweeps.py` or equivalent. Per Q1=(a), no disk writes of tick content; per D-021 testing posture, unit tests + operator code review + smoke run constitute the acceptance bar.

8. **Addendum/addendums to research doc** — write after main sweeps. Captures probe outcome + main-sweep data + any code-turn-research findings not already in D-027 or v4/v5.

9. **Session-close per Playbook §2** — DJ entries for any new decisions, STATE v12, Handoff_H-014.

**Phase 3 attempt 2 starting state at H-014 session open:**

- Repo on `main` with H-013 bundle landed: STATE v11, DecisionJournal with D-027 + D-025 footer, Handoff_H-013, `src/stress_test/` package, `tests/test_stress_test_*.py`, draft `runbooks/Runbook_RB-002_Stress_Test_Service.md`.
- Service at `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`. Discovery loop healthy. 74+ active tennis events on disk at H-013 open (exact count as of H-014 open will be higher by ~24h of continuous discovery).
- Zero production Phase 3 code on `main` in `src/capture/` (Phase 2 files preserved, Phase 3 probe code is in `src/stress_test/` — intentionally isolated per D-020 and D-024 commitment 1).
- Zero Render services deployed for Phase 3 — isolated stress-test service is provisioned at step 5 of the H-014 plan, not present at H-014 open.
- Polymarket US credentials at Render env vars `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` on **`pm-tennis-api`** service (D-023). At H-014 step 5 the same credential values get entered via the Render dashboard into the new `pm-tennis-stress-test` service's env vars. Values never in repo, never in chat transcript.
- Research document `docs/clob_asset_cap_stress_test_research.md` at v4, operator-accepted. v5-or-§15-additive decision at H-014 step 4.
- **Zero pending operator decisions in STATE `open_items.pending_operator_decisions`.**
- Three plan-text pending revisions in STATE unchanged from H-012.
- Research-first discipline in force per D-016 and D-019 and reinforced by H-013 evidence trail.
- SECRETS_POLICY §A.6 guard operating — H-013 did not exercise it (credential values never entered chat), discipline holds.
- D-027 active; D-025 commitment 1 superseded; remaining D-025 commitments in force.

---

*End of handoff H-013.*
