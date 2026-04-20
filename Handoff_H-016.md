# PM-Tennis Session Handoff — H-016

**Session type:** Phase 3 attempt 2 — probe executed (H-015 deferred work completed + I-016 fixed + D-029 deployment-flow governance revision landed)
**Handoff ID:** H-016
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** Probe ran successfully. Classification=accepted. RAID I-016 resolved per D-028. §14 research-doc addendum written. Helper-snippet flip landed. D-029 deployment-procedure revision landed at session close (operator ruled 'PAT, no expiration'; Playbook §13 added; plan revision v4.1-candidate-4 queued). RAID I-017 added (sev 4, pre-existing TestVerifySportSlug failures). Seven-session clean-discipline streak maintained (H-010 → H-016, no tripwires, no OOP).

---

## 1. What this session accomplished

H-016 opened from H-015 + its H-014-Claude-style addendum. Session-open reading expanded per operator direction to include Build Plan v4 summary (via Orientation), STATE v13, Playbook §§1-5+9-12, RAID including I-016, and DJ D-016 through D-027. Retrospective fabrication check: git log confirmed H-015 commit bundle (402c05e + 274cd09), I-016 claims verified against on-disk code (discovery.py line 328, slug_selector lines 142-156 both match as described), and 38/38 stress-test tests pass against pinned deps in clean venv.

Four substantive workstreams landed this session:

1. **Helper-snippet flip** — operator-ruled "resolve shell errors" at session open. Created `src/stress_test/list_candidates.py` as a committed module invocable as `python -m src.stress_test.list_candidates`. Replaces the multi-line pasted snippet from RB-002 §5.1 that failed twice at H-015 due to bracketed-paste markers. 20 new unit tests. Includes a `--show-rejected` diagnostic mode (helpful for I-016 investigation). Updated RB-002 §5.1 and `src/stress_test/README.md` and `src/stress_test/__init__.py`. Landed in commit `d7b2bd2`.

2. **RAID I-016 investigation and fix per D-028** — operator-authorized Phase-2 touch after Claude proposed three fix candidates. Investigation read `/data/matches/9471/meta.json` directly in the pm-tennis-api Render Shell; confirmed the Polymarket gateway response has NO `eventDate` key; canonical date source is `startDate` as full ISO timestamp. Applied Fix C (both forward-going + backward-compatible): (a) `src/capture/discovery.py` line 328 now sources `event_date` from `startDate[:10]`; (b) `src/stress_test/slug_selector.py` `_passes_date_filter` falls back to `start_date_iso[:10]` when `event_date` is empty (handles ~116 historical meta.json files written H-007 through H-016); (c) test fixture in `tests/test_discovery.py` corrected to remove the false `eventDate` key that had been silently masking the bug; (d) 9 new tests added (3 regression in TestParseEvent + 6 fallback in test_stress_test_slug_selector). Subsidiary finding surfaced during investigation: `_check_duplicate_players` (discovery.py line 424) has been silently broken in production since Phase 2 deployed at H-007 — `event_date` short-circuit meant the duplicate-player flag never fired. Fix automatically restores function for new events going forward; historical files retain stale `duplicate_player_flag=False` and are not retroactively corrected. Documented in D-028 and I-016 status cell. Landed in commits `d7b2bd2` (code + RAID + manifest artifacts) and `83c0bf8` (DecisionJournal with D-028).

3. **Live probe execution per D-025 + D-027** — after Render auto-deployed the H-016 bundle, slug selection via the new committed module in pm-tennis-api Shell surfaced 5 eligible candidates (all WTA matches dated 2026-04-21, all pre-H-016 historical meta.json files accepted via the new `start_date_iso` fallback). Operator picked topmost: `aec-wta-paubad-julgra-2026-04-21` (event 9471, Paula Badosa vs Julia Grabher). Probe invoked in pm-tennis-stress-test Shell: `python -m src.stress_test.probe --probe --slug=aec-wta-paubad-julgra-2026-04-21 --event-id=9471`. Outcome: `classification: "accepted"`, `connected: true`, `subscribe_sent: true`, `first_message_latency_seconds: 1.15`, `message_count_by_event: {market_data: 1}`, `error_events: []`, `close_events: []`, `exception_type: ""`. Zero errors. First-message preview confirmed real market data (bid 0.02 × 16000, offer 0.98 × 16000, state MARKET_STATE_OPEN, request_id echo). D-025 branch selected per commitment language: "main sweeps may use either gateway-sourced or api-sourced slugs; default is api-sourced." The gateway-to-api slug bridge is confirmed working.

4. **§14 research-doc addendum written** — the H-014-reserved slot populated. 7 subsections: H-015 deferral rationale, probe input (including the `list_candidates` output), full probe outcome JSON verbatim, classification + D-025 branch selected with 6 supporting observations, H-016 work summary table, H-017 pickup, what §14 does not change. Landed in commit `e28e390`.

Governance workstream landed:

5. **D-029 deployment-procedure revision** — motivated by recurring H-014/H-015/H-016 failure modes in the drag-and-drop commit workflow (H-014 missed STATE v11, H-015 bracketed-paste failures, H-016 missing DJ + stale artifacts + Claude's own splice-file process deviation). After design discussion, operator ruled 'PAT, no expiration' at session close. Commitment: Claude pushes code/docs to the `claude-staging` branch using a non-expiring fine-grained GitHub PAT scoped to `peterlitton/pm-tennis`, stored as a Render environment variable; operator merges staging → main as the single human-in-the-loop gate. Playbook §13 (staging-push-and-merge ritual) added with 8 failure modes. Plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4 for the next plan-revision cadence. Implementation sequencing: operator generates PAT → stores in Render env var → creates claude-staging branch → reports back at H-017 open → Claude test-pushes before first real use. First real use: H-017 non-trivial commit.

   Note on the auth-mechanism decision path during the session: Claude initially recommended GitHub MCP connector, then retracted after verifying the MCP registry at operator's request (no GitHub connector in Anthropic registry at H-016). Operator initially ruled defer (Option A); after further clarification on PAT-vs-MCP tradeoffs and on no-expiration as an acceptable mode for this project's threat model, operator ruled 'PAT, no expiration.' D-029 landed with that authentication mechanism specified.

### Work that landed

| Item | Status |
|------|--------|
| H-015 handoff accepted; full reading per operator direction | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + H-009 fabrication-check standing direction | ✅ Complete — handoff/STATE cross-reference clean; H-015 commit-bundle integrity verified (402c05e + 274cd09); I-016 claims verified against on-disk code |
| Repo clone (standing authorization) | ✅ Complete |
| Retrospective fabrication check | ✅ 38/38 stress-test tests pass in fresh venv against pinned deps; confirms baseline integrity before H-016 changes |
| Helper-snippet convention flip (operator-ruled at session open) | ✅ Complete — `list_candidates.py` + 20 tests + RB-002/README updates; committed `d7b2bd2` |
| I-016 investigation (read live gateway payload) | ✅ Complete — event 9471 meta.json confirmed the bug shape |
| I-016 fix per D-028 (operator-authorized 'c with thorough documentation') | ✅ Complete — Fix C applied (discovery.py + slug_selector + tests + RAID update); committed `d7b2bd2` + `83c0bf8` |
| I-017 filed (pre-existing TestVerifySportSlug failures surfaced during H-016 test runs) | ✅ Filed in RAID (sev 4, H-017 disposition) |
| Live probe executed per RB-002 §5 + D-025 + D-027 | ✅ Classification=accepted; outcome JSON captured |
| §14 research-doc probe-outcome addendum | ✅ Written and committed `e28e390` |
| D-028 DecisionJournal entry (full text) | ✅ Committed `83c0bf8` |
| D-029 DecisionJournal entry (full text) | ✅ Landed (session close) |
| D-029 Playbook §13 ritual | ✅ Landed (session close) |
| D-029 plan §1.5.3/§1.5.4 revision | ✅ Queued as v4.1-candidate-4 in STATE pending_revisions |
| STATE v13 → v14 | ✅ YAML validates clean; phase bumped to `phase-3-attempt-2-probe-executed`; counters advanced; I-016 resolved / I-017 added; D-028 and D-029 referenced; POD-H016-deployment-flow opened and resolved within session; H-015 scaffolding flipped pending→true; v14 + Handoff_H-016 + DecisionJournal (D-029) + Playbook (§13) pending |
| Handoff_H-016 production | ✅ This document |

### Counters at session close

- OOP events cumulative: **0** (unchanged)
- Tripwires fired: **0** (unchanged)
- Tripwires fired in H-016: 0
- DJ entries: **29** (was 27 — D-028 and D-029 added)
- RAID open issues: **14** (was 14: I-016 closed, I-017 opened)
- RAID total issues: **17** (was 16; I-017 new)
- Pending operator decisions: **0** (POD-H016-deployment-flow resolved via D-029 landing)
- Plan-text revision candidates: **4** (v4.1-candidate, -2, -3, new -4 for D-029)

---

## 2. Decisions made this session

**Numbered DecisionJournal entries added this session:**

- **D-028 — RAID I-016 fix: source `event_date` from `startDate`, with `slug_selector` fallback for historical meta.json**
  - Phase 2 code modified with explicit operator authorization per D-016 commitment 2
  - Fix C applied (forward correctness + backward compatibility)
  - 9 new tests
  - Subsidiary finding on `_check_duplicate_players` silently broken since H-007 documented
  - Landed in commits `d7b2bd2` (code) + `83c0bf8` (DJ entry)

- **D-029 — Deployment procedure revision: Claude pushes to a staging branch; operator merges to `main`**
  - Operator ruling: 'PAT, no expiration' at session close
  - Authentication: non-expiring fine-grained GitHub PAT, scoped single-repo, read+write on Contents, stored as Render env var
  - Playbook §13 added (staging-push-and-merge ritual; 8 failure modes enumerated)
  - Plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4 for next plan-revision cadence
  - Implementation sequencing: operator generates PAT → stores in Render env var → creates claude-staging branch → reports back at H-017 open → Claude test-pushes before first real use

**Six operator rulings / in-session rulings (all recorded in STATE `resolved_operator_decisions_current_session`, none reached DJ-entry threshold on their own):**

- **H-016-helper-snippet-flip** — operator-ruled "resolve shell errors" at session open; flipped RB-002 §5.1 pasted snippet to committed module.
- **H-016-I-016-fix-authorization** — operator-authorized Fix C "c with thorough documentation"; culminated in D-028 (the authorization itself is an in-session ruling; the fix it authorized is D-028's commitment).
- **H-016-commit-as-one-bundle** — operator ruled "one commit" for the H-016 bundle.
- **H-016-commit-first-then-probe** — operator ruled to commit the bundle and run the probe in this session rather than defer to H-017.
- **H-016-publish-convention-flip** — in-session commitment (Claude-authored): "always replace, never patch" for file delivery going forward. Baked into D-029 draft as commitment 3.
- **H-016-deployment-flow-PAT-no-expiration** — operator ruled 'PAT, no expiration' at session close; D-029 landed as a formal DJ entry specifying the authentication mechanism.

---

## 3. Pushback and clarification events this session

Worth naming for future-Claude visibility.

### 3.1 The H-008-class danger surface was exercised cleanly

The live probe was explicitly flagged in the H-015 addendum as "the first net-new SDK surface ... the highest fabrication-risk surface since H-008." It ran end-to-end, classification=accepted, zero errors. Every SDK symbol in probe.py's [A]-[D] citation block resolved correctly against the live `polymarket-us==0.1.2` install on Render. The research-first discipline H-013-Claude established (every SDK symbol cited; self-check run before live-probe run) paid off — the fabrication risk was real but the discipline held.

### 3.2 Claude-authored process deviation surfaced by operator

Mid-session, Claude produced `D-028-entry-to-insert.md` as a splice-into-existing-file artifact rather than a complete replacement of `DecisionJournal.md`. This deviated from the established "Claude produces complete replacements; operator uploads" convention. Combined with the drag-and-drop workflow's silent-missing-file failure mode, the first H-016 commit (`d7b2bd2`) landed with the DJ absent and three stale reference artifacts present. Operator surfaced the deviation explicitly: "DJ was not in the bundle just the entry to insert (BAD execution choice—too much manual error risk. for every deploy in other sessions I've ALWAYS been instructed to replace)."

Claude acknowledged the error, produced the full replacement DecisionJournal.md for follow-up commit `83c0bf8`, and committed going forward to 'always replace, never patch' as a convention. This commitment is baked into the D-029 draft (commitment 3). No governance artifact beyond D-029 needed — the convention is self-enforcing if Claude doesn't produce patch artifacts.

### 3.3 Recommendation retracted when research contradicted it

When asked which authentication mechanism (PAT vs MCP connector) was simpler long-term, Claude initially recommended MCP with confidence. Operator asked Claude to confirm MCP was available; Claude then searched the MCP registry and found that the GitHub connector does not appear to be in the current Anthropic registry (GitLab is, GitHub isn't). Claude retracted the recommendation, surfaced the finding explicitly, and recalibrated the options. Operator initially ruled defer (Option A). After further discussion — operator surfaced that the project has had 24 sessions and 20+ deployments of accumulated manual-error cost and asked directly for the actual blocker — the decision was revisited. Operator then ruled 'PAT, no expiration' and D-029 landed. Later in the session, operator shared a screenshot of `github.com/mcp` showing an official GitHub MCP server, which on inspection was VS-Code-only and confirmed the Claude.ai web path is PAT-only anyway. H-008-class failure caught pre-commitment twice — once on the initial MCP-registry fabrication, once on the assumption that "MCP doesn't exist" without distinguishing Anthropic-registry vs broader MCP ecosystem.

### 3.4 Tool-use limit pauses occurred and were handled cleanly

Early in the session, Claude hit a tool-use limit during the initial reading-heavy phase, which caused a response pause with a "Continue" button. Operator initially interpreted this as a protocol issue ("I haven't done anything as I didn't want to confuse or interrupt you"). Claude clarified that tool-use limits are quota-based pauses that resume on any next operator message, not protocol blockers. Operator internalized the pattern ("so if you get a random 'continue' you'll understand I'm not stopping you or interrupting"). No lasting issue; worth noting for H-017-Claude that this quota behavior exists and is not a protocol event.

### 3.5 Commit-mechanism recalibration

Extended mid-session exchange on deployment procedures. Claude initially over-weighted the safety value of the current drag-and-drop workflow when operator proposed direct-push. Operator named concrete recurring failure modes (H-014 missed STATE v11, H-015 paste failures, H-016 missing DJ). Claude recalibrated its risk assessment, acknowledged the asymmetry in how it had been weighting costs, and drafted D-029 accordingly. Governance change was initially deferred for an auth-mechanism reason (§3.3); operator then pushed back on the deferral ("this project has covered 24 Claude sessions and 20+ deployments... what's the blocker for better automating?"), forcing Claude to distill the actual blocker down to one question. Deferral reversed; D-029 landed with 'PAT, no expiration.' The recalibration itself was worth naming because it surfaced the tendency to (a) under-count operator-side costs when assessing workflow changes, and (b) treat drafting as a substitute for framing a direct question.

---

## 4. Files created / modified this session

### Landed in repo (3 commits, H-016)

**Commit `d7b2bd2` — H-016 bundle:** 13 files changed including the 11 intended + 2 stale artifacts that slipped in via the upload.

| File | Action |
|------|--------|
| `src/capture/discovery.py` | Modified — Fix A for I-016 (line 328 event_date extraction) |
| `src/stress_test/__init__.py` | Modified — version bumped to `0.1.1-stress-test-h016`; list_candidates added to module docstring |
| `src/stress_test/README.md` | Modified — reflects helper-snippet flip + H-016 update notes |
| `src/stress_test/list_candidates.py` | **NEW** — committed module replacing RB-002 §5.1 pasted snippet |
| `src/stress_test/slug_selector.py` | Modified — Fix B for I-016 (`_passes_date_filter` start_date_iso fallback) |
| `tests/test_discovery.py` | Modified — fixture corrected + 3 new I-016 regression tests |
| `tests/test_stress_test_list_candidates.py` | **NEW** — 20 unit tests for the new module |
| `tests/test_stress_test_slug_selector.py` | Modified — 6 new I-016 fallback tests |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` | Modified — §5.1 rewrite to use new invocation; header H-016 stamp |
| `RAID.md` | Modified — I-016 marked Resolved; I-017 added |
| `CHECKSUMS.txt` | **INADVERTENTLY COMMITTED** — reference artifact; H-017 cleanup |
| `COMMIT_MANIFEST.md` | **INADVERTENTLY COMMITTED** — reference artifact; H-017 cleanup |
| `D-028-entry-to-insert.md` | **INADVERTENTLY COMMITTED** — stale splice file; should have been replaced with DecisionJournal.md; H-017 cleanup |

**Commit `83c0bf8` — follow-up to add missing DJ:** 1 file changed.

| File | Action |
|------|--------|
| `DecisionJournal.md` | Modified — D-028 inserted at top above D-027 |

**Commit `e28e390` — §14 research-doc addendum:** 1 file changed.

| File | Action |
|------|--------|
| `docs/clob_asset_cap_stress_test_research.md` | Modified — §14 H-016 probe-outcome addendum inserted between §13 and §15 |

### Pending commit (session-close bundle)

| File | Action | Notes |
|------|--------|-------|
| `STATE.md` | Modified (v13 → v14) | YAML validates clean; all phase/counter/scaffolding/prose updates applied including D-029 landing |
| `Handoff_H-016.md` | Created | This document |
| `DecisionJournal.md` | Modified | D-029 spliced above D-028 (reverse chronological); D-028 already committed at 83c0bf8 |
| `Playbook.md` | Modified | §13 (staging-push-and-merge ritual) added; table of rituals updated; footer updated |

### Draft artifacts from the D-029 design process (superseded by the landed versions above; local-only)

| File | Status |
|------|--------|
| `/mnt/user-data/outputs/governance-draft/D-029-draft.md` | Superseded by the D-029 entry now in DecisionJournal.md |
| `/mnt/user-data/outputs/governance-draft/Playbook_section_13_draft.md` | Superseded by the §13 now in Playbook.md |
| `/mnt/user-data/outputs/governance-draft/plan_v4.1-candidate-4_draft.md` | Informational; content captured in STATE pending_revisions |

**No modifications to:** any commitment file (`fees.json`, `breakeven.json`, `data/sackmann/build_log.json`, `signal_thresholds.json` still doesn't exist), `main.py` (untouched), `/requirements.txt` (repo root — untouched per D-024 commitment 1), `PM-Tennis_Build_Plan_v4.docx`, `PreCommitmentRegister.md`, `SECRETS_POLICY.md`, `Orientation.md`, `Playbook.md`, previous handoffs.

---

## 5. Known-stale artifacts at session close

Three files inadvertently committed at commit `d7b2bd2` that are not intended to be part of the project:

- `CHECKSUMS.txt` (repo root) — SHA-256 checksums of the commit bundle; reference artifact.
- `COMMIT_MANIFEST.md` (repo root) — operator-facing instructions for how to commit the bundle; reference artifact.
- `D-028-entry-to-insert.md` (repo root) — intermediate Claude-authored splice artifact that should have been replaced with `DecisionJournal.md`; the session's process-deviation artifact.

None of these affect the build, tests, deploys, or any commitment file. They are repository clutter. H-017 picks up cleanup as a minor item (can be bundled with any other H-017 commit).

---

## 6. Tripwire events this session

**Zero tripwires fired. Zero OOP invocations.** Seven consecutive sessions now (H-010 through H-016) without firing a tripwire or invoking OOP.

Three preventive-mode disciplines exercised without firing:

- **The H-008-class fabrication-risk surface was exercised against live API.** Every SDK symbol used in the live probe traced to a real symbol on the installed SDK. No fabrication class bugs in probe.py. The research-first discipline scaled to the live-network use case cleanly.

- **Phase-2-touch authorization gate honored.** Before modifying `src/capture/discovery.py` line 328, Claude surfaced three fix candidates (A, B, C) with explicit tradeoff language and waited for operator authorization. Operator ruled "c with thorough documentation"; only then did Claude modify Phase 2 code. D-016 commitment 2 held.

- **Claude-authored process deviation self-surfaced and corrected mid-session.** The splice-file artifact (`D-028-entry-to-insert.md`) was a deviation from established convention. Operator surfaced it; Claude acknowledged the error rather than rationalizing it, produced the full replacement, and committed to 'always replace' going forward. This is the research-first/surfacing-not-rationalizing discipline applied to process rather than code.

---

## 7. STATE diff summary (v13 → v14)

Key fields that changed:

- `project.state_document.current_version`: 13 → 14
- `project.state_document.last_updated_by_session`: H-015 → H-016
- `project.plan_document.pending_revisions`: +1 (new v4.1-candidate-4 for D-029 §1.5.3/§1.5.4 revision)
- `phase.current`: `phase-3-attempt-2-probe-blocked-on-calendar` → `phase-3-attempt-2-probe-executed`
- `phase.current_work_package`: rewritten to reflect H-016 completions + H-017 pickups
- `sessions.last_handoff_id`: H-015 → H-016
- `sessions.next_handoff_id`: H-016 → H-017
- `sessions.sessions_count`: 15 → 16
- `discovery.meta_json_files_written`: 74 → 126 (H-016 redeploy observation)
- `discovery.current_event_count`: 74 → 126
- `discovery.current_slug_count`: 74 → 126
- `open_items.raid_entries_by_severity.sev_6`: 4 → 3 (I-016 resolved)
- `open_items.raid_entries_by_severity.sev_4_and_below`: 3 → 4 (I-017 added)
- `open_items.raid_entries_by_severity.issues_open`: 14 → 14 (I-016 closed, I-017 opened — net zero)
- `open_items.pending_operator_decisions`: [] → [] (POD-H016-deployment-flow opened and resolved within this session)
- `open_items.resolved_operator_decisions_current_session`: pruned per settled convention and replaced with H-016's 6 in-session rulings (including H-016-deployment-flow-PAT-no-expiration)
- `open_items.phase_3_attempt_2_notes`: +10 entries for H-016
- `scaffolding_files.STATE_md`: v13 → v14/pending; note rewritten
- `scaffolding_files.Playbook_md`: committed_to_repo true → pending (D-029 §13 added this session)
- `scaffolding_files.DecisionJournal_md`: committed_to_repo true → pending (D-029 added at close; D-028 already committed at 83c0bf8)
- `scaffolding_files.RAID_md`: committed_to_repo pending → true (commit d7b2bd2); committed_session H-015 → H-016
- `scaffolding_files.clob_asset_cap_stress_test_research_md`: committed_session H-014 → H-016 (§14 added, commit e28e390)
- `scaffolding_files.Handoff_H015_md`: committed_to_repo pending → true (commit 274cd09)
- `scaffolding_files.Handoff_H016_md`: **new**, pending

Prose sections updated:
- "Where the project is right now" — fully refreshed for H-016 close
- "What changed in H-015" — removed; new "What changed in H-016" section added
- "H-015 starting conditions" → renamed/rewritten as "H-017 starting conditions"
- "Validation posture going forward" — refreshed for H-017's four application surfaces (retrospective for H-016 artifacts, preventive for main-sweeps, preventive for D-029, preventive for I-017)

---

## 8. Open questions requiring operator input

**No pending operator decisions at session close.** POD-H016-deployment-flow was created mid-session (D-029 deferral) and resolved before session close (operator ruled 'PAT, no expiration'; D-029 landed).

Items carried forward from prior sessions, not specific to H-016:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Four plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, -2, -3, -4) — cut at next plan revision under Playbook §12.

Items H-017-Claude should raise at session open:

- **D-029 operator-side setup confirmation.** Ask whether operator has: (a) generated the non-expiring PAT with correct scoping, (b) stored it as a Render env var (confirm the env var name), (c) created the `claude-staging` branch. If all three: Claude does a small test-push to staging to verify the flow end-to-end before first real use. If any are incomplete: Claude waits on the operator-side setup before proceeding with any other H-017 commit work.
- **Cleanup of 3 stale artifacts in repo root** (`CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, `D-028-entry-to-insert.md`). Small, uncontroversial. Can be the first real use of the staging-push flow (low-stakes first commit).
- **RAID I-017 disposition.** Two pre-existing TestVerifySportSlug failures. Either update tests to expect RuntimeError OR update code to raise SystemExit. Small single-file fix either way.

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Clean. Read H-015 handoff + addendum in full. Read STATE v13 (YAML + prose). Full reading per operator direction included Orientation, Playbook §§1-5+9-12, RAID including I-016, DJ D-016 through D-027, discovery.py extraction code + TennisEventMeta + _check_duplicate_players, slug_selector._passes_date_filter, probe.py header/citations, RB-002 in full. Skipped Build Plan v4 .docx read (flagged explicitly); Orientation §5-§6 provided sufficient structural content for H-016's scope. Skipped the 38-test fresh-venv re-run at open (H-015-Claude had already run it at H-015 open; no code had changed); did run it before making any code changes this session, and again after, against pinned deps — both passed. Self-audit produced as a visible block. Tool-use limit hit once during the reading-heavy phase; resumed cleanly on operator message.

**Cut-point discipline at session open:** Operator ruled "resolve shell errors" (→ helper-snippet flip authorized) and work proceeded. Throughout the session, scope expanded cleanly via operator rulings: commit-bundle approach; commit-then-probe-in-this-session; §14 addendum after probe; D-029 drafted; D-029 deferred and then un-deferred by operator direction; D-029 landed. No cut-violation events.

**Surfacing-not-rationalizing exercised:**
- When the first H-016 commit landed without DecisionJournal.md, operator surfaced the process deviation. Claude acknowledged rather than explaining-away, produced the full replacement, committed going forward to 'always replace' convention.
- When asked about MCP connector availability, Claude searched the registry rather than relying on memory; surfaced the finding that GitHub MCP is not in the Anthropic registry; retracted the initial recommendation. When operator pushed back on the subsequent deferral, Claude recalibrated and framed the one actual open question (PAT accept-or-not); operator ruled, D-029 landed. Later in the session, operator shared a screenshot showing `github.com/mcp` does have an official GitHub MCP server (VS-Code-only), confirming the Claude.ai path is PAT-only — second-order verification of the earlier finding, not a retraction of it.
- When the I-017 TestVerifySportSlug failures surfaced during H-016 test runs, Claude verified against the baseline (unmodified main) that the failures pre-existed, filed I-017 at the appropriate severity, and scoped them out of D-028 rather than extending D-028's scope to absorb them.

**Phase-2-touch authorization gate honored.** Before modifying `src/capture/discovery.py`, Claude surfaced three fix candidates (A/B/C) with explicit tradeoff language. Operator ruled "c with thorough documentation." Only then did Claude modify Phase 2 code. D-016 commitment 2 held intact.

**Retrospective fabrication check:** Executed against H-015 + H-014 + H-013 code. 38/38 tests pass in fresh venv against pinned deps at H-016 open; 79/79 tests pass in the scope of H-016 changes at session close (38 existing stress-test + 20 new list_candidates + 9 new discovery/slug_selector + 12 unchanged discovery TestParseEvent). 2 pre-existing failures in TestVerifySportSlug were NOT introduced by H-016 work; filed as I-017.

**Live probe discipline:** The H-008-class fabrication surface was finally exercised against live network. Every SDK symbol in probe.py's citation block traced to a real symbol on the installed SDK. Classification=accepted with no errors. The research-first discipline H-013-Claude established scaled correctly to the live-network case.

**Pacing assessment:** Long session. Substantial scope expansion from the H-015 conservative default (probe + §14 close) to the H-016 actual scope (helper-snippet flip + I-016 fix with Phase-2 touch + probe + §14 + D-028 + D-029 drafts). Each expansion was explicitly operator-ruled. No ruling under fatigue. Multiple tool-use pauses occurred and were handled cleanly. Lands longer than H-015, meaningfully productive, no corner-cutting surfaced.

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. Three preventive-mode disciplines without firing.
**DJ entries added:** 1 (D-028). Total entries in journal: 28.
**RAID changes:** I-016 marked Resolved; I-017 added (sev 4).

---

## 10. Next-action statement

**The next session's (H-017) first actions are:**

1. Accept handoff H-016.

2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-017 open the check applies in four modes:
   - **Retrospective for H-016 artifacts.** STATE v14, Handoff_H-016, DecisionJournal D-028, RAID I-016/I-017, `list_candidates.py`, the discovery.py/slug_selector.py fixes, the research-doc §14 addendum. Spot-check that claims about commit SHAs, line numbers, and test counts match on-disk reality. Key items to verify: d7b2bd2 contains the I-016 fix at discovery.py line 328 reading `startDate`; slug_selector has the `start_date_iso` fallback; the §14 JSON in the research-doc matches what the probe actually output.
   - **Preventive for main sweeps code-turn.** Main sweeps is the first net-new SDK surface beyond probe.py's [A]-[D] citation block. Fabrication-risk surface: `client.markets.list()` and multi-subscription semantics on `markets_ws`. **Re-fetch `github.com/Polymarket/polymarket-us-python` README at code-turn time.** No exceptions.
   - **Preventive for D-029 implementation (if authorized).** Re-verify MCP registry at H-017 open for GitHub connector (may have been added since H-016 search). Re-read current Playbook and plan text before editing — draft governance artifacts are starting points, not frozen.
   - **Preventive for I-017 disposition.** Read the actual `verify_sport_slug` function before deciding which side to fix; don't rely on I-017's description as the full picture.

3. **Raise three session-open items explicitly** before substantive work:
   - **D-029 operator-side setup confirmation.** At H-016 close, operator confirmed: (a) non-expiring fine-grained PAT generated scoped to `peterlitton/pm-tennis` with Contents read+write; (b) stored as `GITHUB_PAT` env var on the `pm-tennis-api` Render service; (c) `claude-staging` branch created from `main` at commit `66def97`. Claude verified the branch exists on remote at session close via git clone. **First H-017 action after self-audit is a small test push to `claude-staging`** — change one trivial file (e.g., a timestamp note in a scratch file, or the initial cleanup of stale artifacts). Operator reviews diff in GitHub web UI, merges if good. This is low-stakes exercising of the end-to-end mechanism before first real-work use.
   - **Stale-file cleanup:** delete `CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, `D-028-entry-to-insert.md` from repo root. This can double as the test push — a legit small useful change that exercises the staging-push mechanism.
   - **RAID I-017 disposition:** surface the two options (update tests vs update code) and seek operator ruling. Small single-file fix.

4. **Main sweeps per §7 Q3=(c).** Code-turn work. Shape: 1/2/5/10 subscriptions × 100 placeholder slugs × 1/2/4 concurrent connections. ~30 minutes runtime. Per §7 Q1=(a), no disk writes of received tick content. Per D-021 testing posture: unit tests + operator code review + smoke run constitute acceptance bar. Expected new module: `src/stress_test/sweeps.py` or equivalent. **Slug source per D-025 branch-selected at H-016: api-sourced via `client.markets.list()` as default, with gateway-sourced as fallback if needed.**

5. **§16 main-sweeps addendum to research-doc.** Written after main sweeps complete.

6. **Session-close per Playbook §2** — STATE v15, Handoff_H-017, DJ entries for any new numbered decisions (D-029 plausible if it lands; D-030 possible for other substantive rulings).

**Phase 3 attempt 2 starting state at H-017 session open:**

- Repo on `main` with full H-013+H-014+H-015+H-016 bundle. STATE v14. DJ at 28 entries (last D-028). Handoff_H-016. RAID with I-016 Resolved + I-017 new (14 open, 17 total). Research-doc with §14 populated. src/stress_test/list_candidates.py + all I-016 fix code committed.
- Three stale artifacts in repo root pending cleanup (harmless; repository clutter only).
- Live `pm-tennis-api` service with I-016 fix deployed. 126+ events at H-016 close (growing at ~1-2/hr). event_date correctly populated for newly-discovered events; historical events retain empty event_date handled transparently by slug_selector fallback.
- Live `pm-tennis-stress-test` service; self-check green; one successful probe in history.
- D-029 deployment workflow ready for first real use:
  - Non-expiring fine-grained GitHub PAT generated, scoped to `peterlitton/pm-tennis` Contents read+write (confirmed by operator at session close).
  - PAT stored as `GITHUB_PAT` env var on the `pm-tennis-api` Render service (confirmed by operator at session close).
  - `claude-staging` branch exists on remote at commit `66def97` (verified by Claude at session close via git clone).
  - Branch protection on `main`: operator did not confirm whether set up; H-017-Claude should ask at session open as housekeeping.
  - First H-017 substantive action after self-audit: a small test push to `claude-staging` to exercise the mechanism end-to-end before first real-work use.
- Zero pending operator decisions at session close.
- Four plan-text pending revisions in STATE (v4.1-candidate-4 conditional on D-029).
- Research-first discipline in force per D-016, D-019.
- 'Always replace, never patch' file-delivery discipline in force per H-016 operator surfacing + Claude commitment.
- SECRETS_POLICY §A.6 guard continues — H-016 exercised the credential path during the probe; credentials never entered chat (SDK handled all auth internally from env-var-named credentials per D-023).
- D-028 active. D-027 active. D-025 commitment 1 superseded; 2/3/4 in force. D-024, D-023, D-020, D-019, D-018, D-016 in force.
- Pruning convention for `resolved_operator_decisions_current_session`: stricter reading, settled.
- Seven consecutive sessions (H-010 through H-016) closed without firing a tripwire or invoking OOP.

---

*End of handoff H-016.*
