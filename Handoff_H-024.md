# PM-Tennis Session Handoff — H-024

**Session type:** Tier 1 transcription-and-interpretation session — §17 main-sweeps-outcome addendum memorializing H-023's two runs of live-gateway evidence against §16's committed harness. Operator-gated tiered scope per H-023 handoff §10.2 framing; Tier 1 authorized, drafted, reviewed, corrected, verified, landed. Tiers 2 and 3 explicitly not authorized this session.
**Handoff ID:** H-024
**Session start:** 2026-04-21
**Session end:** 2026-04-21
**Status:** Deliverable landed. §17 appended to `docs/clob_asset_cap_stress_test_research.md` following §14 precedent structure; byte-identical §§1–16 preservation verified via SHA-256 baseline check both pre-write and post-write (baseline `cef7245f427b4be412a38a32b35df6bf100409228c3638fa9e916a261104374f` over lines 1–1123 of the assembled file); document grew 1127 → 1296 lines (+169). Zero tripwires, zero OOP, zero DJ entries, zero code changes, zero test changes, zero RAID changes, zero commitment-file changes. If bundle merges cleanly, fifteen consecutive clean-discipline sessions (H-010 → H-024).

---

## 1. What this session accomplished

H-024 opened from H-023's close with operator authorization (standing) to clone the repo. Session-open reading covered Handoff_H-023 in full (427 lines, including §9 evidence trail E1–E10 and §10 tiered-scope framing), Letter from H-023-Claude in full, operator-attached H-025 scope pre-registration document, Orientation in full, Playbook §§1 / 2 / 4 / 13 in full, STATE v21 YAML header and scaffolding inventory, and the session-open self-audit block.

Per operator ruling on "Reading 1–6" authorization, pre-Tier-1 reading extended to: DJ entries D-033 / D-032 / D-025 / D-027 / D-019 in full; research-doc §16 in full with §16.11 freeze language pinned; `_resolve_m2` / `_resolve_cell_measurements` in sweeps.py for M2 `'independent'` semantic interpretation (deliberately held out of H-023 per hold-scope discipline; in-scope for H-024 Tier 1 per H-023 handoff §10.5 step 4); classify_cell step-6 reason-string text verbatim; CellSpec grid enumeration (lines 339–410 of sweeps.py) to map H-023's run 2 cell indices to connection/subscription counts.

Five substantive workstreams landed this session:

1. **Item 1 — Session-open self-audit.** Verified H-023 bundle on main: STATE v21, DJ at 33 entries, Handoff_H-023 present, research-doc at 1127 lines with §16 frozen (§§16.1–16.11). One minor internal inconsistency noted: `scaffolding_files.STATE_md.current_version: 19` (stale inner entry; v20 + v21 bumps had not propagated to the nested field). Authoritative `state_document.current_version` was always correct at 21. Not a blocker; corrected at H-024 close to 22 as part of the v22 bundle.

2. **Item 2 — POD-H017-D029-mechanism resolution-path check per D-030.** Not explicitly run this session at the mechanical `search_mcp_registry` level because H-025's operator-attached steering pre-registers the POD for formal closure at H-025 with three candidate resolutions named (A / B / C). The ritual check at H-024 carried only the semantic question: did anything change in registry composition since H-023 that would shift the candidate weighting? No signal surfaced. POD remains open, low urgency, pre-registered for H-025 closure.

3. **Item 3 — Pre-Tier-1 reading phase per operator authorization.** Five DJ entries read in full (D-033, D-032, D-025, D-027, D-019); research-doc §16 read in full as §17 precedent context; §16.11 freeze language pinned; `_resolve_m2` docstring read with emphasis on the caveat "we use a weaker observable — traffic distribution across connection slots" (sweeps.py lines 1932–1934). Reading established four framing-precision risks for §17 drafting: (i) D-033 orthogonal-not-revision; (ii) M2 observable-not-identity; (iii) markets.list empirical-not-bug; (iv) 30-second-window + single-match + two-run scope caveat on every quantitative claim. Operator added framing-precision risk (iv) explicitly during pre-draft exchange.

4. **Item 4 — §17 drafting + three-checks review + correction cycle.** §17 drafted to 171 lines (including leading `---\n\n` and trailing `\n---\n\n` separators) following §14 precedent structure across seven subsections (17.1 scope/why-written; 17.2 run inputs; 17.3 execution-and-outcomes; 17.4 classification/interpretation with four empirical findings plus 17.4.5 additional M-question status; 17.5 H-023 work summary; 17.6 six items deferred to H-025+; 17.7 what §17 does not change). Byte-identical §§1–16 baseline pinned via SHA-256 (`cef7245f...`) before draft; post-draft verification matched baseline. Operator ran three checks on the surfaced draft: stitch correctness at §16→§17 boundary; line-count accounting; framing-precision re-check on 17.4 subsections and 17.6 deferred items list. Stitch initially failed (missing blank line before `---`; root cause: `sed -n '1,1123p'` truncated one line before the original inter-section blank); corrected by re-truncating head at line 1124; baseline SHA still matched since line 1124 is not in §§1–16 content scope. Framing-precision re-check surfaced five gaps: §17.4.5 M1 bullet enumerated three mechanism candidates (window too short / anchor too quiet / attribution field not populated) — scope-in-detail on speculation; §17.4.5 D-033 exception-type-predictions bullet included a parenthetical enumerating trigger conditions — same pattern; §17.6 items 1/2/3 scoped redesign candidates, frame-extension sub-questions, and M1 re-sweep shape in detail — all three violating the deferred-items-shouldn't-scope-the-research-first-work principle. All five tightened. Re-verification after corrections: baseline SHA matched; stitch matched §15→§16 precedent; line-count delta clean at +169; framing-precision risks held on corrected draft. File copied to `/home/claude/pm-tennis/docs/clob_asset_cap_stress_test_research.md`; post-copy baseline re-check confirmed match.

5. **Item 5 — Session-close bundle production.** STATE v22 produced with YAML validation confirmed (parser report: all 17 top-level keys present and valid; `state_document.current_version: 22`; `sessions.last_handoff_id: H-024`; `sessions.next_handoff_id: H-025`; `sessions.sessions_count: 24`). Handoff_H-024 this document. Letter from H-024-Claude to H-025-Claude with operator-attached H-025 scope steering carried verbatim-equivalent into §10 for H-025-Claude's session-open intake.

### Work that landed

| Item | Status |
|------|--------|
| H-023 handoff accepted; full reading | ✅ Complete |
| Letter from H-023-Claude read in full | ✅ Complete |
| Operator-attached H-025 scope steering reviewed for carry-forward | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + D-007 | ✅ Complete — one minor internal inconsistency flagged (stale `STATE_md.current_version: 19` inner field) |
| Pre-Tier-1 reading (D-033, D-032, D-025, D-027, D-019; §16 in full; `_resolve_m2`; §16.11 freeze) | ✅ Complete per operator authorization |
| Four framing-precision risks pinned before drafting | ✅ Complete |
| Byte-identical §§1–16 baseline pinned via SHA-256 | ✅ `cef7245f...` over lines 1–1123 |
| §17 drafted (171 lines, §14 precedent structure) | ✅ Complete |
| Three-checks review by operator (stitch / line-count / framing-precision) | ✅ Complete — six corrections applied (1 stitch + 5 framing-precision) |
| Correction cycle re-verification (baseline SHA, stitch, framing-precision) | ✅ All re-checks pass on corrected draft |
| §17 copied to repo `docs/` | ✅ Complete; post-copy baseline re-verified |
| STATE v22 produced with YAML validation | ✅ Parses cleanly; fields verified |
| Handoff_H-024 produced | ✅ This document |
| Letter from H-024-Claude to H-025-Claude produced | ✅ In bundle |
| H-025 scope pre-registration carried verbatim-equivalent in §10 | ✅ In this document |
| Tier 2 (DJ entries on H-022 §9 Observations 1+2) | ⏸ Explicitly not authorized this session; own-session per operator ruling |
| Tier 3 (disposition of H-022 §9 Observations 3–6) | ⏸ Explicitly not authorized this session; H-026+ |
| §16.9 step 1a+1b re-fetch | ⏸ Not performed — H-024 scope was transcription not code-touching; per H-023 handoff §10.4 the re-fetch is required "only if H-024 touches code" and operator signal was Tier 1 §17 only |

### Counters at session close

- OOP events cumulative: **0** (unchanged)
- Tripwires fired: **0** (unchanged)
- Tripwires fired in H-024: 0
- DJ entries: **33** (unchanged — zero added this session)
- RAID open issues: **13** (unchanged)
- RAID total issues: **17** (unchanged)
- Pending operator decisions: **1** (POD-H017-D029-mechanism; pre-registered for H-025 formal closure)
- Plan-text revision candidates: **4** (v4.1-candidate, -2, -3, -4; unchanged)
- Clean-discipline streak: **15 consecutive sessions** (H-010 → H-024) if close bundle lands cleanly

---

## 2. Decisions made this session

**Zero numbered DecisionJournal entries added this session.** DJ remains at 33.

Per the "execution of standing convention is not a decision" principle (H-019) and the "correction cycles within pre-authorized tier scope are not rule changes" extension (H-024): §17 transcription is execution of §16.8 acceptance-bar commitments (items 3 and 4: live smoke run executed → outcome JSON preserved → results interpreted in subsequent additive section); framing-precision corrections are draft-review iteration within pre-authorized Tier 1 scope; tier non-authorization is session-scope ruling per the pre-registered tier structure.

**Operator rulings / in-session rulings** (recorded for reference; none reached DJ-entry threshold):

- **H-024-tier-1-authorization** — Tier 1 (§17 research-doc addendum) authorized as H-024's primary deliverable with four framing-precision risks pinned and pre-Tier-1 reading scope approved.
- **H-024-section-17-format-ruling** — §17 follows §14 precedent (prose-with-citations), not verbatim sub-sections of H-023 handoff §9 (E1–E10 + synthesized items 1–7 are evidence §17 references, not structure §17 duplicates).
- **H-024-tier-1-correction-cycle-acceptance** — Five framing-precision gaps surfaced at three-checks review (M1 mechanism candidates; D-033 trigger conditions parenthetical; §17.6 items 1/2/3 scope-in-detail). All five tightened. Correction-cycle-pass rather than first-pass-pass, named honestly for forward propagation. Received-discipline addition for H-025+: post-draft pre-registered-pulls self-audit before surfacing for review.
- **H-024-tier-1-verdict** — Tier 1 passes. All three checks clear on corrected draft. File copied to repo; post-copy baseline re-verified. Proceed to session-close artifact production.
- **H-024-tier-2-non-authorization** — Tier 2 explicitly not authorized this session. Session closes on Tier 1 alone. Tier structure is operator-gated transitions; Tier 2 gets its own session.

---

## 3. Files in the session bundle

1. `docs/clob_asset_cap_stress_test_research.md` — v4 + §§13–16 additive → v4 + §§13–17 additive. §17 appended per §14 precedent structure. Byte-identical §§1–16 preserved (SHA-256 `cef7245f...` match both pre-write and post-write). Document grew 1127 → 1296 lines (+169). **Substantive content change this session.**

2. `STATE.md` — v21 → v22. Structured updates:
   - `sessions.last_handoff_id` → H-024
   - `sessions.next_handoff_id` → H-025
   - `sessions.sessions_count` → 24
   - `sessions.most_recent_session_date` → 2026-04-21 (unchanged — same calendar day)
   - `state_document.current_version` → 22
   - `state_document.last_updated` → 2026-04-21
   - `state_document.last_updated_by_session` → H-024
   - `scaffolding_files.STATE_md.current_version` → 22 (corrects stale inner field that read 19; authoritative outer field was always correct)
   - `scaffolding_files.STATE_md.committed_session` → H-024
   - `scaffolding_files.STATE_md.note` → refreshed for H-024 narrative
   - `scaffolding_files.Handoff_H023_md.committed_to_repo` → pending → true (assumed per H-024 session-open audit; operator verifies at commit)
   - `scaffolding_files.Handoff_H024_md` → new entry
   - `scaffolding_files.clob_asset_cap_stress_test_research_md.committed_session` → H-019 → H-024
   - `scaffolding_files.clob_asset_cap_stress_test_research_md.note` → refreshed for §17 landing
   - `open_items.resolved_operator_decisions_current_session` — pruned to H-024 entries only per the H-014-settled stricter-reading convention. H-023 entries removed; five H-024 rulings added (H-024-tier-1-authorization, H-024-section-17-format-ruling, H-024-tier-1-correction-cycle-acceptance, H-024-tier-1-verdict, H-024-tier-2-non-authorization).
   - `phase.phase_3_attempt_2_notes` → new H-024 entry appended.
   - `phase.current_work_package` → H-024 narrative appended to cumulative per-session trail.

   Prose: H-024 paragraph prepended; H-022 preservation header re-labeled "(as of H-022)" with correct transition note.

3. `Handoff_H-024.md` — this document.

4. `Letter_from_H-024-Claude.md` — informal letter to H-025-Claude, same genre as H-023-Claude → H-024.

**NOT in the bundle (by design):**
- No code changes. `src/stress_test/sweeps.py`, `tests/test_stress_test_sweeps.py`, `src/stress_test/probe.py`, all Phase 2 code — unchanged.
- No DecisionJournal.md changes. Zero new entries. DJ remains at 33.
- No RAID.md changes.
- No runbook changes.
- No commitment-file changes. `signal_thresholds.json` still does not exist; `fees.json` / `breakeven.json` / `data/sackmann/build_log.json` unchanged.
- No additional research-doc sections beyond §17.

---

## 4. Governance-check results this session

**Session-open self-audit (retrospective for H-023 artifacts):**
- STATE `current_version: 21` ✓
- STATE `last_updated_by_session: H-023` ✓
- DJ entry count: 33 ✓ (D-033 at top, D-032 second, D-031 third)
- `src/stress_test/sweeps.py` 2,422 lines ✓
- `tests/test_stress_test_sweeps.py` 1,330 lines ✓
- `docs/clob_asset_cap_stress_test_research.md` 1,127 lines ✓
- `Handoff_H023_md` in scaffolding_files inventory ✓
- **One minor internal inconsistency:** `scaffolding_files.STATE_md.current_version: 19` (stale nested field from v20 + v21 bumps that did not propagate to the nested scaffolding entry). Authoritative `state_document.current_version` was correctly at 21. Not a blocker; flagged to operator at session-open and corrected at session-close to 22 as part of the v22 bundle.

**Session-open self-audit (preventive per §16.9 step 1a+1b standing convention):**
- Not performed this session. Per H-023 handoff §10.4, §16.9 step 1a+1b re-fetch is required "only if H-024 touches code." Operator-authorized scope was Tier 1 §17 addendum (transcription, no code touch). Not required.

**Session-open self-audit (preventive for Render service state):**
- Not performed this session. §17 drafting is not live-execution; deploy state was not exercised. Per H-023 handoff §10.4, the Render deploy-state check is required "only if H-024 is a live-execution session."

**Governance fingerprint:** Unchanged. OOP trigger phrase `"out-of-protocol"`, handoff carrier markdown files, public GitHub, secrets-in-env-vars, single authoring channel — all intact.

**SECRETS_POLICY §A.6 discipline:** Credential values did not enter the chat transcript at any point. No Shell work, no env-var references beyond naming. Discipline held.

**`present_files` discipline:** No mid-session `present_files` calls. One `present_files` call at session close (this bundle).

**Deployment discipline:** Not exercised — §17 is transcription, not live-execution. Per H-023 handoff §10.4 convention.

**Byte-identical §§1–16 preservation discipline:** New load-bearing discipline at H-024. SHA-256 baseline pinned pre-draft (`cef7245f427b4be412a38a32b35df6bf100409228c3638fa9e916a261104374f` over lines 1–1123 of the assembled file). Verified post-draft on scratch-assembled file; verified again post-copy-to-repo. Baseline matched all three times. One correction in the preservation chain: initial `sed -n '1,1123p'` truncation dropped the inter-section blank line (line 1124 of original) which made the §16→§17 stitch fail against §15→§16 precedent; corrected to `sed -n '1,1124p'`; baseline still matched since line 1124 is not in §§1–16 content scope.

---

## 5. Scaffolding-files inventory snapshot at H-024 close

Sessions' own files:
- Handoff_H-001 through Handoff_H-022 — accepted and committed to main (verified at prior self-audits).
- Handoff_H-023 — accepted; committed-to-main assumed per H-024 session-open audit. Operator verifies definitively at H-024 bundle commit.
- Handoff_H-024 — produced this session; pending commit.
- STATE.md — v22 produced this session; pending commit.
- Orientation.md, Playbook.md, PreCommitmentRegister.md, RAID.md, DecisionJournal.md, SECRETS_POLICY.md — unchanged.

Project deliverable files:
- `main.py` — unchanged (H-009 c63f7c1d-equivalent restore).
- `src/capture/discovery.py` — unchanged since H-016 (D-028 fix).
- `src/stress_test/sweeps.py` — unchanged since H-020 (2,422 lines). H-023 exercised its live-smoke path twice; H-024 read `_resolve_m2` / `_resolve_cell_measurements` for §17 semantic interpretation without modifying.
- `tests/test_stress_test_sweeps.py` — unchanged since H-020 (91 tests).
- `runbooks/Runbook_RB-002_Stress_Test_Service.md` — unchanged. §9 of H-022 surfaces proposed Step 4 caveat; Tier 2 (H-025+ scope) addresses if authorized.
- **`docs/clob_asset_cap_stress_test_research.md` — §17 appended this session.** Document now at 1296 lines (was 1127 at H-024 open). §§1–16 byte-identical preserved via SHA-256 baseline check.
- `docs/sports_ws_granularity_verification.md` — unchanged (H-005 I-001 resolution).
- `fees.json`, `breakeven.json`, `data/sackmann/build_log.json` — unchanged.

**What a future-Claude opening H-025 should find on GitHub main at session open (assuming operator completes the H-024 bundle merge):**
STATE v22. DJ at 33 entries (unchanged). Handoff_H-024. Letter_from_H-024-Claude. Research-doc at 1296 lines (v4 + §§13–17). All other files as listed above.

If operator defers some bundle actions, H-025 self-audit surfaces the specific discrepancy per Playbook §1.5.4 and seeks operator ruling.

---

## 6. Assumptions changed or added this session

**Zero assumption changes.** No additions, no removals, no status shifts. RAID unchanged at 13 open / 17 total.

---

## 7. Tripwires fired this session

**None.** Zero tripwires fired at H-024. Zero OOP invocations. Fifteen consecutive sessions (H-010 through H-024) closed without firing a tripwire or invoking OOP if the close bundle lands cleanly.

The closest moments to tripwires were:

1. **M1 mechanism speculation in initial §17.4.5 draft.** H-023-Claude's letter had explicitly flagged this as a predictable-risk pull. I pre-registered it as a framing-precision risk before drafting. It still landed in the initial draft. The operator's three-checks review caught it. This is the discipline layer operating correctly — but the catch happened at operator review, not at Claude self-check. Named in §9 self-report as the session's honest learning.

2. **Stitch correction at §16→§17 boundary.** Initial sed-truncation error produced a stitch mismatch against §15→§16 precedent. The three-checks review named stitch correctness as priority #1; I caught the error on the first `view` of the assembled file at boundary lines 1120–1130; fixed without operator intervention. Substantive-if-broken, cosmetic otherwise; fixed to match convention.

3. **The pull to collapse Tier 2 into Tier 1.** Briefly considered whether "§17 that also includes the two DJ entries as formalizations" could be a single consolidated deliverable. Named and rejected in-session before drafting: different files (research-doc vs DJ), different roles (empirical narrative vs rule-change ledger), mixing them conflates categories. Rejection preserved the governance-ledger separation as a structural principle, not just session pragmatics. Operator affirmed at Tier 1 verdict.

Each of these is the discipline layer operating correctly — the governance caught potential drift, with the M1 catch happening at operator review rather than Claude self-check (the forward-learning point memorialized in §9).

---

## 8. Open questions requiring operator input

**Pending operator decisions at session close: 1.**

- **POD-H017-D029-mechanism** — opened by D-030 at H-017; pre-registered for formal closure at H-025 per operator-attached steering document (three candidate resolutions A/B/C named). Not urgent; project operates correctly under the D-030 interim flow. H-025 is the narrow single-deliverable cleanup session for this closure.

Items carried forward from prior sessions, not specific to H-024:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Four plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, -2, -3, -4) — cut at next plan revision under Playbook §12.

Items H-025-Claude should raise at session open:

- **POD-H017-D029-mechanism resolution**, per the operator-attached steering document carried in §10 of this handoff. The three candidates (A / B / C) are pre-registered; H-025-Claude surfaces them to operator with any weighting shift surfaced in the H-025 session-open reading.

---

## 9. Self-report and §9 Evidence for H-025

### 9.1 Self-report

**Tier 1 landed via correction-cycle-pass, not first-pass-pass.** §17 drafted with four framing-precision risks pinned pre-draft per operator-affirmed discipline. Three of four held in the initial draft (D-033 orthogonal-not-revision, M2 observable-not-identity, markets.list empirical-not-bug — each written with explicit caveats and verbatim quoted resolver-docstring material where the precision-point was load-bearing). The fourth risk (M1 mechanism speculation) landed in §17.4.5's M1 bullet in the initial draft — I enumerated three mechanism candidates (window too short / anchor too quiet / attribution field not populated) under "not resolved by §17" framing. Disclaiming "not resolved" did not remove the speculation; it embedded it. Operator's three-checks review caught this + four related scope-in-detail issues in §17.4.5 (D-033 trigger-conditions parenthetical) and §17.6 (items 1, 2, 3 all enumerated candidates / sub-questions / re-sweep specifications for deferred research-first work). All five tightened on self-audit against operator's named criteria; re-verification passed on all three checks.

**The meta-lesson for H-025+.** Pre-registration caught pulls 1 and 2 (D-033 orthogonal-not-revision; M2 observable-not-identity) at draft-time. Pull 4 (scope caveat) was pinned and held throughout. Pull 3 (M1 mechanism speculation) surfaced in draft exactly where H-023-Claude's letter had predicted and operator's framing-precision pin had flagged — but the catch happened at operator review, not at Claude pre-surface self-check. The pre-registration wasn't wrong; the gap was between drafting-complete and surfacing-for-review. The received-discipline addition for H-025+: **post-draft pre-registered-pulls self-audit** — after draft complete and before surfacing for review, re-read each pre-registered pull and verify against the draft ("did I do this?"). That step, if run here, would have caught the M1 enumeration on self-review rather than on operator review.

**Scope-discipline held on the tier transitions.** Tier 2 (two DJ entries on H-022 §9 Observations 1+2) was genuinely tempting — the formalization work is discrete, non-novel, and would have been easy to knock out in the remaining session bandwidth. The structural reason for holding (research-doc vs DJ files have different roles; mixing conflates categories) is load-bearing and was surfaced pre-draft, before the "bandwidth is available" argument could gather force. Operator's Tier 2 non-authorization ruling at verdict affirmed the structural principle.

**Shell-and-commit discipline held.** No Shell work this session (§17 is transcription; no live execution). No push attempts. File replacement in the repo directory used `cp` from scratch to destination per "always replace, never patch" convention (D-029 §3 / H-016). Post-copy baseline SHA re-verified.

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. Fifteen consecutive sessions with zero tripwires if close bundle lands cleanly.

**DJ entries added:** 0. Total entries: 33 (unchanged).
**RAID changes:** none. Open issues 13, total 17 (unchanged).

**Quiet uncertainties carried into session close:**

- **Whether the M1-mechanism-speculation catch at operator-review rather than self-review indicates a deeper gap in my self-check discipline.** The post-draft pre-registered-pulls self-audit memorialized as received discipline is the proposed corrective. Whether it's sufficient — vs. needing a broader post-draft self-review protocol covering more than just pre-registered pulls — is not resolved by H-024 alone; H-025+ practice will surface.
- **Whether `scaffolding_files.STATE_md.current_version: 19` was the only stale inner field at session-open audit.** The audit caught that one; I did not systematically re-audit every nested scaffolding-files field against their `committed_session` outer values. If there are other stale inner fields, they would surface at a future session's self-audit. Not a blocker, but worth naming.
- **Whether H-025's narrow-single-deliverable scope survives the session-open reading.** The operator's H-025 steering is specific (POD-H017-D029 closure; three candidates A/B/C; no substantive sweep work; no research-first on error_events or `_fetch_anchor_slug`). If something at H-025 session-open surfaces a reason to weight the candidates differently than A default, or a reason to bundle the closure with an adjacent mechanical change (e.g., SECRETS_POLICY §A.6 revision if B wins), H-025-Claude handles within the scope the steering specifies rather than expanding.

### 9.2 Evidence for H-025

**Research-doc state at H-024 close.** `docs/clob_asset_cap_stress_test_research.md` at 1296 lines (was 1127 at session open). §§1–16 byte-identical to v4 + §§13–16 additives as recorded pre-H-024; SHA-256 `cef7245f427b4be412a38a32b35df6bf100409228c3638fa9e916a261104374f` over lines 1–1123 of the post-§17 file. §17 runs lines ~1127–~1292 (with `---\n\n` separators at ~1125 and ~1294 flanking the new section).

**Framing-precision disposition in §17.** Four risks pinned; all held on the corrected draft: (1) D-033 orthogonal-not-revision — §17.4.3 explicitly rejects revision framing with "The finding is **not** that D-033's partition is incomplete for its scope... The finding is that error_events are a category D-033 did not scope to address"; (2) M2 observable-not-identity — §17.4.2 includes verbatim resolver-docstring quote ("we use a weaker observable — traffic distribution across connection slots") and summary sentence "consistent with independence at the observable level the harness measures"; (3) markets.list empirical-not-bug — §17.4.4 explicitly says "The SDK function-contract does not promise 'return active tennis markets'... The function delivered on that contract" and "This is a finding about what `_fetch_anchor_slug`'s default strategy needs to do, not a claim that `markets.list()` is broken"; (4) 30-second-window + single-match + two-run scope caveat — pinned at the end of §17.1 (load-bearing statement naming the scope bound) and reinforced throughout 17.3 message-count table and 17.4 findings.

**§17.6 deferred items on corrected draft (six items, precision-criteria-passing):** (1) `_fetch_anchor_slug` redesign — research-first per D-019; candidate set named as research-first scope, not enumerated; (2) D-033 frame extension — research-first per D-019; extension shape named as research-first scope, not pre-determined; (3) M1 resolution work — dependent on item 1 as prerequisite; experiment shape research-first scope; (4) error-event payload extraction — prerequisite to item 2; procedural description only; (5) any code changes — research-first sequencing per D-019; (6) Phase 3 exit gate work — §17 closes §16 acceptance bar only, not Phase 3.

**D-033 status after two runs:** The three exception-type additions (PermissionDeniedError, InternalServerError, WebSocketError) remained unexercised across both runs. Recorded in §17.4.5 as "neither evidence for nor against the partition — the sweep grid as designed does not naturally exercise the code paths that trigger these types." Partition correctness remains hypothesis-correct-by-construction; empirical confirmation or contradiction requires a future experiment outside §16's scope.

**M4 silent-filter disposition:** Two-sample replication of `silent_filter_inferred=true` across ~80 minutes. §17 records this as "directionally supportive of the silent-filter branch of M4 as a stable characterization for the placeholder format the harness generates" without generalizing beyond the two samples and the specific placeholder format.

**M2 `'independent'` disposition at N=2 AND N=4:** Both connections-axis-n2 (cell 6) and connections-axis-n4 (cell 7) resolved `m2_resolution = "independent"`. §17 records this as an observable-level claim at the traffic-distribution layer, with the resolver's own docstring caveat about SDK-identity-level preserved verbatim. The stronger claim (SDK has genuinely distinct object identity and underlying transport connections for concurrent `client.ws.markets()` calls) is not what the resolver tests and is not what §17 claims.

**Error-event scaling disposition:** 1/4/9 errors on cells 2/3/4 (subscriptions-axis at N=2/5/10) on one anchor slug in one 30s window in one run. Recorded as an observation, not a general law. Payload content held for H-025+ extraction if needed. Orthogonal category to D-033 per §17.4.3 framing.

---

## 10. Next-action statement and H-025 scope pre-registration

### 10.1 Framing — H-025 is pre-registered as narrow single-deliverable cleanup

H-025 is a reversion to the strict one-deliverable-per-session shape. H-024's tiered scope was a justified adaptation for transcription-plus-formalization work; H-025 goes back to narrow single-deliverable because the work is a single governance decision with real material weight (a DJ entry that formally closes a 7-session-open POD and establishes whichever path forward becomes permanent).

### 10.2 H-025 scope (carried verbatim-equivalent from operator-attached steering document)

**H-025 scope: narrow-scope cleanup session. One deliverable: POD-H017-D029 resolution.**

**Why this scope now.** POD-H017-D029 has been open since H-017. Every session since has opened with a resolution-path check per D-030, and every check has returned "no change" (no GitHub MCP connector in the registry). The check has become ritual rather than a path to resolution. D-030's interim flow (Claude pushes to claude-staging, operator merges to main) works operationally, but leaves D-029 in a superseded-by-interim-but-not-formally-superseded state indefinitely. Seven sessions of open-drift is long enough.

**H-025 is the right session for this because:**
- H-024 has cleared the H-022 §9 governance observation backlog at Tier 1 level (§17 landed). Tier 2 (DJ entries on H-022 §9 Observations 1+2) and Tier 3 (Observations 3–6) are preserved for H-026+ since H-025 is narrow-scope. POD-H017-D029 is the next-oldest governance debt and fits the cleanup-session shape.
- Substantive research-first next-work (_fetch_anchor_slug redesign, D-033 frame extension for error_events, M1 re-sweep planning) pushes to H-026+ regardless. Inserting H-025 as cleanup does not delay substantive progress.
- H-025's decision is operator-level, not experimental. It can land in one session without blocking on anything else.

**Three candidate resolutions for H-025 to choose among.** H-025-Claude opens with these three named. Operator rules which one; H-025 drafts the DJ entry accordingly.

**Candidate A — Promote D-030 interim flow to permanent.**
Formally supersede D-029 Commitment §2 (GitHub PAT stored as Render env var) with D-030's drag-and-drop-to-staging flow as the permanent mechanism. Acknowledge that the GitHub-MCP-connector resolution path per D-030 has not surfaced in ~7 sessions and is not projected to. Close POD-H017-D029 by accepting the interim flow as the end state.

*What this means operationally:* no change. Current workflow continues. But the governance ledger is clean — no orphan POD, no "interim solution" framing, D-030 becomes the formal answer.

*What this costs:* commits the project to operator-merge-to-main discipline indefinitely. If Anthropic later adds a GitHub MCP connector, revisiting would require a new DJ entry.

**Candidate B — Per-session PAT paste with SECRETS_POLICY §A.6 revision.**
Operator pastes a GitHub PAT into the session at the point Claude needs to push. Requires a SECRETS_POLICY §A.6 revision DJ entry because current policy is "credential values never enter chat." This is a meaningful policy change, not a mechanical substitution.

*What this means operationally:* Claude can push directly to main (or claude-staging) when needed, reducing operator-merge overhead per session by some amount.

*What this costs:* weakens SECRETS_POLICY §A.6 for a specific credential type. PAT scoping would need to be tight (repo-specific, short expiration, revokable). Requires operator comfort with per-session PAT exposure in chat transcript, which the project has avoided so far by design.

**Candidate C — Explicit defer-until-condition.**
Leave POD-H017-D029 open but formalize the deferral with a specific triggering condition rather than open-ended. E.g., "Defer resolution until (i) GitHub MCP connector appears in Anthropic registry, OR (ii) operator-merge overhead becomes a named friction point, OR (iii) H-050 regardless — whichever comes first." The resolution-path check in subsequent sessions becomes trigger-check rather than ritual.

*What this means operationally:* no immediate change. But the ritual resolution-path check gains a clear end condition.

*What this costs:* leaves the POD formally open while acknowledging it's not actively working toward resolution. Cleaner than current drift but less clean than A or B.

**H-025-Claude's job, concretely:**

1. Open session per standard. Accept H-024 handoff; session-open self-audit.
2. Raise POD-H017-D029 resolution as H-025's deliverable (pre-registered here).
3. Read D-029 in full, D-030 in full, and the POD's accumulated resolution-path-check history across H-017 → H-024 to ensure any latent reason to favor A, B, or C hasn't surfaced.
4. Surface the three candidates to operator with updated reasoning if any context has shifted.
5. Operator rules which candidate. Draft DJ entry:
   - Cites D-029, D-030, POD-H017-D029's open history (sessions, resolution-path-check pattern)
   - States the ruling clearly
   - Documents any formal supersession (if A: supersede D-029 Commitment §2; if B: revise SECRETS_POLICY §A.6; if C: formalize the deferral trigger conditions)
   - Updates STATE.md as needed (POD closes; D-029 status changes if A; SECRETS_POLICY references update if B)
6. Operator reviews DJ entry + STATE changes; H-025-Claude revises if needed.
7. Session close per standard.

**Scope discipline for H-025.**

H-025 does NOT do:
- Any substantive sweep work
- Any research-first turns on `_fetch_anchor_slug` or D-033 frame extension
- Any code changes
- Any M1/M2/M3/M5 follow-up work
- Bundle Candidate A with B or C (operator picks one; if hybrid is warranted, H-025-Claude surfaces that before drafting, but the default is single-candidate)

If during H-025 a related governance question surfaces (e.g., operator-merge overhead has indeed become a named friction point since H-017, which would inform Candidate B's appeal), H-025-Claude surfaces to operator but does not expand scope. H-026+ handles related follow-up.

If the POD resolution surfaces a material revision to the project's handoff/bundle workflow (e.g., Candidate B requires Playbook §13.5.7 revision), that revision is in-scope for H-025 because it's mechanically coupled to the DJ entry. Anything else is H-026+ scope.

**H-026+ then picks up:**

After H-025 lands:
- `_fetch_anchor_slug` redesign (research-first; multi-session arc)
- D-033 frame extension for error_events category
- M1 resolution re-sweep against cleanly-designed anchor source
- Any code changes per D-019 research-first discipline
- Plan revision batch under Playbook §12 (v4.1 incorporating the four queued candidates) — this is probably H-026 or H-027 depending on H-025's outcome

**Bundle expectations at H-025 close.**

- STATE v22 → v23 (v22 comes out of H-024 — this handoff)
- Handoff_H-025
- Letter from H-025-Claude to H-026-Claude
- DecisionJournal.md updated: one new entry formalizing the resolution (call it D-034)
- Possibly SECRETS_POLICY.md updated (if Candidate B)
- No code changes
- No test changes
- No research-doc changes
- Streak at 16 consecutive sessions if clean (H-010 → H-025)

### 10.3 H-025-Claude's first actions

1. Accept handoff H-024.
2. Perform session-open self-audit per Playbook §1.3 and D-007. Self-audit includes:
   - Retrospective for H-024 artifacts: STATE v22 on-disk, Handoff_H-024 on-disk, `docs/clob_asset_cap_stress_test_research.md` at 1296 lines with §17 appended, scaffolding inventory, DJ unchanged at 33.
   - Verify byte-identical §§1–16 of research-doc still matches SHA-256 baseline `cef7245f427b4be412a38a32b35df6bf100409228c3638fa9e916a261104374f` over lines 1–1123 (this is a standing preservation check now that §17 has landed).
   - POD-H017-D029 check as H-025's deliverable opening, not as ritual.
   - No preventive re-fetch required unless H-025 cut involves code (it does not per §10.2).
3. Raise POD-H017-D029 resolution as H-025's single deliverable. Read D-029 in full, D-030 in full, and the POD's open-history.
4. Surface three candidates (A / B / C) with any context shift surfaced in session-open reading.
5. Operator rules. Draft DJ entry D-034. STATE updates as needed. Possibly SECRETS_POLICY update if Candidate B.
6. Session close with bundle: STATE v23; Handoff_H-025; Letter from H-025-Claude; DJ +1 (D-034); possibly SECRETS_POLICY updated.

### 10.4 If H-025 opens and H-024 bundle is NOT merged

Full self-audit per Playbook §1.3; surface specific discrepancy per §1.5.4; seek operator ruling before proceeding. H-024's STATE claims v22 pending; if STATE on main is still v21, H-025-Claude proceeds per Playbook §1.5.4.

### 10.5 Received-discipline carried forward to H-025+

Per operator ruling at H-024 Tier 1 verdict, one concrete addition to the received-discipline stack:

- **Post-draft pre-registered-pulls self-audit.** After any drafting work completes and before surfacing for operator review, Claude re-reads each pre-registered pull (each named framing-precision risk, each named scope-creep vector, each named pull from the prior Claude's letter) and verifies against the draft: "did I do this?" For each pull, the answer is either (a) "no, held" — continue; (b) "yes, landed" — correct before surfacing. This step caught nothing at H-024 because H-024 did not run it; the M1 mechanism enumeration instead surfaced at operator three-checks review. The discipline memorialized here is prospective: H-025-Claude and beyond run the post-draft self-audit before surfacing.

---

## 11. Phase 3 attempt 2 state at H-025 session open

- Repo on `main` with the H-024 bundle merged (assuming operator completes merge): STATE v22, DJ at 33 entries (unchanged), Handoff_H-024, Letter_from_H-024-Claude, `docs/clob_asset_cap_stress_test_research.md` at 1296 lines with §17 appended.
- `src/stress_test/sweeps.py` at 2,422 lines (unchanged from H-020).
- `tests/test_stress_test_sweeps.py` at 1,330 lines, 91 tests (unchanged).
- `docs/clob_asset_cap_stress_test_research.md` at 1296 lines. §§1–16 byte-identical preserved from v4 + §§13–16 additives (SHA-256 `cef7245f...` over lines 1–1123). §17 appended at H-024 per §14 precedent structure. §17 frozen at H-024; future sessions do not amend it.
- RAID unchanged (13 open / 17 total).
- `pm-tennis-api` service running; discovery loop active.
- `pm-tennis-stress-test` service: known-good runtime state (H-022 baseline; H-023 exercised live-network path twice without triggering new deploy; H-024 made no deploy-affecting change).
- `/tmp/sweep_h021.*` and `/tmp/sweep_h023_run2.*` artifacts may persist on `pm-tennis-stress-test` Shell at H-025 open; if extraction needed for error-event payload analysis at H-025+, check presence first.
- One pending operator decision: POD-H017-D029-mechanism — pre-registered for H-025 formal closure per §10.
- Four plan-text pending revisions in STATE (v4.1-candidate, -2, -3, -4). Unchanged.
- D-030 interim flow is the default deployment mechanism. Drag-and-drop-to-staging discipline in force.
- "Always replace, never patch" file-delivery discipline per H-016 / D-029 §3.
- SECRETS_POLICY §A.6 in force — credential values never enter chat.
- D-033 active and scoped correctly; error_events remain an orthogonal category per §17.4.3 framing; frame extension work is H-025+ scope per §17.6 item 2.
- D-032, D-031, D-030, D-029 (Commitment §2 suspended per D-030; H-025 formalizes the status), D-028, D-027, D-025 commitments 2/3/4 in force (1 superseded by D-027), D-024, D-023, D-020, D-019, D-018, D-016 all in force.
- **Fifteen consecutive sessions (H-010 through H-024) closed without firing a tripwire or invoking OOP** if H-024 bundle lands cleanly.

---

*End of handoff H-024.*
