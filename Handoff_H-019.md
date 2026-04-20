# PM-Tennis Session Handoff — H-019

**Session type:** Research / governance — §16 main-sweeps-scope research-doc addendum per D-019 research-first-then-code sequencing; one-deliverable session by operator cut at open
**Handoff ID:** H-019
**Session start:** 2026-04-20
**Session end:** 2026-04-20
**Status:** Bundle produced — STATE v17, `docs/clob_asset_cap_stress_test_research.md` (v4 + §16 H-019 main-sweeps-scope addendum; complete replacement; §§1-15 byte-identical), Handoff_H-019. Ten consecutive clean-discipline sessions (H-010 → H-019). Zero tripwires, zero OOP. Zero DJ entries this session per operator direction. Mid-session `present_files` lesson held — one present_files call at the operator-requested review step, not mid-session. Main sweeps code deferred to H-020 per D-019 sequencing.

---

## 1. What this session accomplished

H-019 opened from H-018 with operator authorization to clone the repo (standing). Session-open reading covered Handoff_H-018 in full (281 lines including H-018-Claude's informal letter), Orientation, Playbook end-to-end (all 13 sections), STATE v16 YAML + prose, DecisionJournal all 31 entries (D-001 through D-031), RAID.md in full, SECRETS_POLICY §§A and B, research-doc §§7/13/14/15, probe.py header/citations [A]-[D]. Session-open self-audit passed against on-disk reality: H-018 bundle merged cleanly on `main`; DJ at 31 entries with D-031 at top; STATE v16; RAID I-017 Resolved; `tests/test_discovery.py` with two renamed `TestVerifySportSlug` methods (lines 566, 581) verified on disk. Zero discrepancies.

After initial scope proposal, operator requested brief-prep reading (items 1–4 per Claude's preparedness list): PM-Tennis_Build_Plan_v4.docx §5.4 and §11.3 (I-015 pending-revision context); probe.py lines 120–764 (sweeps-extension pattern); `src/stress_test/requirements.txt` (pin confirmation); Runbook RB-002 in full (two-shell workflow pattern). ~45 minutes of focused reading. Produced detailed preparedness report surfacing the load-bearing question for §16: whether multiple `subscribe()` calls on one `markets_ws` compose additively or replace.

Operator cut the session at open to **§16 research-doc addendum only**. Main sweeps code deferred to H-020 per D-019 research-first-then-code sequencing.

Three substantive workstreams landed this session:

1. **Item 1 — POD-H017-D029-mechanism resolution-path check per D-030.** `search_mcp_registry` returned GitLab, Contentsquare, Exa, Microsoft Learn, Lucid, Mem, Glean — no GitHub MCP connector. Unchanged from H-016/H-017/H-018. No path-change detected. No targeted DJ entry per D-030's "if material" clause — nothing material.

2. **Item 2 — SDK README re-fetch per standing instruction.** The instruction "re-fetch `github.com/Polymarket/polymarket-us-python` README at code-turn time, no exceptions" had sat in four consecutive handoffs (H-015 → H-018) without being exercised. H-019 is the session that finally ran it. Operator supplied a tightened step-4 framing for the post-fetch checkpoint: exit states are binary (exit state A = clean, §16 drafts; exit state B = any contradiction with research record surfaced, DJ entry lands and §16 defers; "at odds with the research record" catchall for unknown contradictions; when uncertain, default to B). Re-fetched [E] `github.com/Polymarket/polymarket-us-python` README, [F] `docs.polymarket.us/api-reference/websocket/markets`, [G] libraries.io PyPI metadata for `polymarket-us`. Findings: SDK unchanged (10 commits on GitHub matches H-013's recorded count; PyPI `polymarket-us==0.1.2` still latest, two releases total both 2026-01-22); every probe.py [A]-[D] citation still resolves; exception surface identical; Ed25519 signing remains fully internal; 100-slug-per-subscription cap directly confirmed on [F] ("You can subscribe to a maximum of 100 markets per subscription. Use multiple subscriptions if you need more"); two empirical gaps identified (M1 multi-same-type subscription composition; M2 multi-`client.ws.markets()` independence) framed as measurement questions for the sweeps harness, not contradictions with research record. Cross-checked 12 claims; all consistent. Operator ruled exit state A (clean) and authorized §16 drafting.

3. **Item 3 — §16 draft, operator review, amendments, accept.** Produced 345-line additive section per §13/§14/§15 precedent; §§1-15 preserved byte-identical (verified: 0 diff lines against v4 for lines 1-780). §16 organized into 11 subsections. Round 1 review surfaced two design choices for operator input: (1) 1+99 anchor-slug-plus-placeholder composition default vs pure-100-placeholder; (2) adding `degraded` classification vs keeping probe.py's four-way. Operator ruled: keep 1+99 default AND add dedicated 100P/0R M4 control cell to grid; keep `degraded` classification AND pin the degraded-vs-rejected-vs-accepted threshold explicitly (subscribe-success ratio: ≤0.5 rejected, (0.5, 1.0) exclusive degraded, 1.0 candidate for clean); plus small §16.11 explicit-naming fix. Three amendments applied in round 2: §16.5 M4 control cell + cell_id flag; §16.7 seven-step classification precedence list + special cases for single-subscribe and M4 control cells; §16.8 M4 control cell added to acceptance-bar live-smoke checklist. Small §16.11 first-bullet rewrite landed. Re-verified §§1-15 byte-identical (0 diff lines). Operator accepted.

Plus the usual close-bundle assembly: STATE v17 produced with full YAML validation; this handoff.

### Work that landed

| Item | Status |
|------|--------|
| H-018 handoff accepted; full reading | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + D-007 | ✅ Complete — zero discrepancies; H-018 bundle verified on `main` |
| Repo clone (standing authorization) | ✅ Complete |
| Orientation.md re-read | ✅ Complete |
| Playbook.md end-to-end (all §§1-13) | ✅ Complete |
| DecisionJournal all 31 entries (D-001 through D-031) | ✅ Complete |
| RAID.md in full | ✅ Complete |
| SECRETS_POLICY.md §§A + B | ✅ Complete — §A.6 discipline understood |
| Research-doc §§7, 13, 14, 15 | ✅ Complete |
| probe.py header block [A]-[D] | ✅ Complete at initial brief |
| Brief-prep reading per operator request (plan §5.4/§11.3, probe.py implementation, stress_test/requirements.txt, RB-002) | ✅ Complete — ~45 min focused reading |
| Item 1: POD-H017-D029-mechanism resolution-path check per D-030 | ✅ Complete — no path-change detected; POD remains open |
| Item 2: SDK README re-fetch + two supporting fetches | ✅ Complete — standing instruction finally exercised; exit state A ruled |
| Item 3 draft: §16 addendum (345 lines) | ✅ Complete |
| Item 3 review round 1: two design choices surfaced | ✅ Complete |
| Item 3 amendments (M4 control cell, classification threshold, §16.11 explicit) | ✅ Complete — §§1-15 re-verified byte-identical |
| Item 3 review round 2: accept | ✅ Complete |
| STATE v17 produced with YAML validation | ✅ Complete — YAML parses clean |
| Handoff_H-019 production | ✅ This document |
| Main sweeps code (`src/stress_test/sweeps.py`) | ⏳ Deferred to H-020 per operator cut at session open (D-019 research-first-then-code sequencing) |
| Optional DJ footer cleanup | ⏳ Skipped per operator direction — "§16 is the deliverable; give it your full attention" |

### Counters at session close

- OOP events cumulative: **0** (unchanged)
- Tripwires fired: **0** (unchanged)
- Tripwires fired in H-019: 0
- DJ entries: **31** (unchanged — zero added this session per operator direction)
- RAID open issues: **13** (unchanged)
- RAID total issues: **17** (unchanged)
- Pending operator decisions: **1** (POD-H017-D029-mechanism)
- Plan-text revision candidates: **4** (v4.1-candidate, -2, -3, -4; unchanged)
- Clean-discipline streak: **10 consecutive sessions** (H-010 → H-019)

---

## 2. Decisions made this session

**Zero numbered DecisionJournal entries added this session.**

Per operator direction, the SDK README re-fetch was execution of an already-committed standing instruction (not a decision), and §16 is research-doc production (not a rule change). Governance trail for the re-fetch lives in §16.1's fetch-record header and in this handoff's self-report. The 31-entry DJ remains unchanged from H-018 close.

**Operator rulings / in-session rulings (recorded in STATE `resolved_operator_decisions_current_session`; none reached DJ-entry threshold):**

- **H-019-session-cut-at-open** — operator cut session to §16 research-doc addendum only; main sweeps code deferred to H-020 per D-019 research-first-then-code sequencing. One-deliverable-per-session pattern preserved.
- **H-019-checkpoint-exit-state-A-clean** — operator ruled exit state A (clean) after Claude surfaced structured re-fetch findings at the mid-session checkpoint. Per operator's tightened step-4 framing, the checkpoint was binary: either §16 drafts or a DJ entry lands for a surfaced contradiction. Findings showed SDK unchanged, every probe.py citation still resolves, no research-record contradictions — exit state A authorized §16 drafting. Two empirical gaps (M1, M2) correctly framed as measurement questions for the harness, not as contradictions.
- **H-019-section-16-accept** — operator accepted §16 after two rounds of review. Round 1 ruled on two design choices (keep 1+99 default + add 100P/0R M4 control cell; keep `degraded` classification + pin subscribe-success-ratio threshold explicitly) plus small §16.11 explicit-naming fix. Round 2 verified three amendments landed cleanly and §§1-15 remained byte-identical. Operator accepted.

---

## 3. Pushback and clarification events this session

Worth naming for future-Claude visibility.

### 3.1 The "do you need more briefing" recommendation → operator approval

After Claude proposed "§16-only" as the session scope, Claude surfaced that items 1–4 of additional brief-prep reading (plan §5.4/§11.3, probe.py implementation, stress_test/requirements.txt, RB-002) would produce measurably better §16 quality — roughly 45 minutes before drafting. This wasn't a cut-the-scope move; it was a pre-draft surface of "here's what I haven't yet read that would strengthen the output." Operator approved explicitly. Proceeding with items 1–4 turned out to be load-bearing for §16 specifically:
- Plan §5.4/§11.3 gave §16 the exact language I-015 will eventually revise ("Pool size is bounded by the soft 150-asset cap (to be stress-tested in Phase 3)") so §16 is grounded in the plan text it's informing.
- probe.py's implementation (lines 120–764) gave §16 the precise pattern to extend — event-handler registration, `subscription_request_id` generation, ProbeOutcome dataclass, classification precedence — rather than inferring from STATE's architectural notes.
- The combination surfaced the single most load-bearing question for §16 (M1 — multi-same-type subscription composition semantics on one `markets_ws`) before drafting, so the re-fetch at item 2 had a specific thing to answer.

The pattern to internalize for future-Claude: when proposing a session cut, also surface any brief-prep gaps before declaring ready. The operator can decline the brief-prep, but the surfacing itself is the discipline. "Ready except for these specific unread pieces" is more honest than "ready."

### 3.2 The operator's tightened step-4 framing on exit states

Before the SDK re-fetch, Claude proposed a two-branch checkpoint: exit state A (clean, §16 drafts) or exit state B (contradiction surfaced, DJ entry + §16 defers). Operator tightened the framing explicitly:

1. **Enumerated items are not exhaustive; the catchall is load-bearing.** The named contradiction surfaces (SDK past 0.1.2, multi-subscription semantics different from §15, concurrent-connection cap not previously known, exception surface change, anything making §16 cite against different reality than probe.py did) are the known axes; the "anything else at odds with the research record" catchall is where unknown ones land. Don't let the enumeration tempt into deciding a finding is clean just because it doesn't match a named item. **When uncertain which exit state, it's B.** Err toward surfacing.

2. **If [E] has moved past 0.1.2, pin-harder-vs-upgrade is its own decision with its own entry, not a choice inside §16.** Version drift doesn't get absorbed into §16's prose; it's a governance event.

3. **No D-032 for the re-fetch itself.** The re-fetch is execution of an already-committed standing instruction, not a new decision. Governance trail for the re-fetch belongs in §16.1's fetch-record header and in this handoff's self-report. Save DJ entries for actual decisions.

The framing is worth preserving in operator voice because it's sharper than anything Claude would have written unprompted. The "when uncertain, default to B" clause specifically rewires the decision heuristic so that the lazy path (call it A) is not the default; the safe path (call it B) is. Record this pattern under "operator-supplied framing at decision time" alongside H-018's D-031 pre-H-004 framing.

### 3.3 The two design-choice rulings at §16 round 1

Claude surfaced two design choices as open rather than baking a choice into the draft:

1. **1+99 anchor-plus-placeholder composition vs pure-100-placeholder.** Claude proposed 1+99 with reasoning; operator kept 1+99 as default AND **added a dedicated 100P/0R M4 control cell** to the grid. This ruling is tighter than Claude's original proposal — the M4 control cell gives M4 a clean unconfounded measurement without requiring a separate invocation. One additional cell, ~30–60 seconds of sweep time, disambiguates the measurement. The insight the ruling encoded: the anchor slug is load-bearing in the main grid (protects M1 attribution against M4-failure-case traffic drops), but the M4 measurement itself benefits from an anchor-free baseline. Both patterns coexist in the grid.

2. **Adding `degraded` classification vs keeping probe.py's four-way.** Claude proposed `degraded`; operator kept `degraded` AND **required the threshold between `degraded` / `rejected` / `clean` be pinned explicitly.** Reasoning: "Without a threshold, H-020-Claude has to invent one, and that invention becomes a fabrication surface. Named measurement forces the code to address the threshold directly." Operator proposed the specific cutoff (subscribe-success ratio ≤ 0.5 → rejected; (0.5, 1.0) exclusive → degraded; 1.0 → candidate for clean), acknowledged other thresholds are defensible, and asked Claude to name whichever threshold is committed.

Both rulings illustrate a pattern: when Claude surfaces a design choice, the operator often tightens the ruling in a direction Claude did not propose. The surface-then-ruling flow works because each side's contribution is different — Claude produces the draft with decision points marked, operator produces the tightened commitments. Don't short-circuit this by pre-deciding; the quality of the ruling depends on the decision being actually open at surface time.

### 3.4 The "§16 is the deliverable, skip the footer cleanup" direction

Operator's pre-signal instruction explicitly dropped the DJ footer cleanup from §16's session if session time became contested. The footer has been stale since H-009 (says "updated at H-009 ... next entry will be D-018"); H-017-Claude, H-018-Claude, and H-019-Claude have all flagged it as a standing opportunity. Operator's direction: "§16 is the deliverable; give it your full attention. It's survived since H-009, it'll survive another session." Received and honored — §16 produced cleanly with full attention; footer cleanup explicitly did not happen this session. It survives for a future session.

---

## 4. Files created / modified this session

### Pending commit (session-close bundle for operator action)

| File | Action | Notes |
|------|--------|-------|
| `docs/clob_asset_cap_stress_test_research.md` | Modified (complete replacement) | v4 + §16 H-019 main-sweeps-scope addendum (lines 781-1127). §§1-15 preserved byte-identical (verified: 0 diff lines against v4 for lines 1-780). Total 1127 lines (was 782 at v4 open). §16 organized into 11 subsections. No v5 bump — additive-to-v4 convention per §13/§14/§15 precedent. Footer updated. |
| `STATE.md` | Modified (complete replacement, v16 → v17) | YAML validates clean. All H-019 counter bumps, scaffolding-files updates, prose rewrites landed. |
| `Handoff_H-019.md` | Created | This document. |

**Delivery path per D-030 interim flow:**

1. Operator navigates to `claude-staging` branch in GitHub web UI.
2. Drag-and-drop `docs/clob_asset_cap_stress_test_research.md` (replace existing — path must match).
3. Drag-and-drop `STATE.md` (replace existing).
4. Drag-and-drop `Handoff_H-019.md` (create new at repo root).
5. Review staging-vs-main diff: https://github.com/peterlitton/pm-tennis/compare/main...claude-staging
6. If satisfied, merge `claude-staging` → `main`. Render will auto-deploy `pm-tennis-api`; behavior unchanged because no code path on the service is affected (research-doc-only change).

### Files NOT modified this session

- `DecisionJournal.md` (zero DJ entries added per operator direction)
- `RAID.md` (no RAID changes — §16 populates research record, does not surface new risks or issues per §16.11's "does not change" discipline)
- Any commitment file (`fees.json`, `breakeven.json`, `data/sackmann/build_log.json`, `signal_thresholds.json` still doesn't exist)
- `src/capture/discovery.py` (no Phase 2 code touch; D-016 commitment 2 not triggered)
- `main.py` (untouched)
- `tests/test_discovery.py` (untouched since H-018)
- `requirements.txt` (untouched per D-024 commitment 1)
- `src/stress_test/*` (untouched — sweeps code deferred to H-020 per D-019 sequencing)
- `src/stress_test/requirements.txt` (read for brief-prep, not modified)
- `PM-Tennis_Build_Plan_v4.docx` (read for brief-prep, no plan revision this session)
- `PreCommitmentRegister.md`, `SECRETS_POLICY.md`, `Orientation.md`, `Playbook.md` (read for governance compliance, not modified)
- `runbooks/*` (RB-002 read for brief-prep, not modified)
- All previous handoffs (read; not modified)

---

## 5. Known-stale artifacts at session close

After operator completes the H-019 commit-bundle merge, no known-stale artifacts remain in the repo introduced by H-019.

If operator defers some bundle actions (e.g., merges STATE + Handoff but defers the research-doc, or vice versa), H-020 self-audit will surface the specific discrepancy between STATE's claims and on-disk repo state, and Claude proceeds per Playbook §1.5.4 (surface, await operator ruling).

**DecisionJournal footer remains stale** ("updated at H-009 session close ... next entry will be D-018"). Has been stale since H-009, predates H-017/H-018/H-019. Out of scope for this session per operator direction ("give §16 full attention"). Noted for a future cleanup pass. Same flag as H-017's, H-018's handoffs.

**Pre-existing environmental failure** (unchanged from H-018): `tests/test_stress_test_probe_cli.py::test_main_defaults_to_self_check` fails when run in the pm-tennis-api baseline venv because `polymarket_us` SDK lives in `src/stress_test/requirements.txt` (per D-024 dep-isolation). Not a defect; a consequence of the intentional dep-isolation. Future sessions running the full `tests/` suite in one venv should install both requirements files, or run the stress-test tests separately in the stress-test venv.

**Pre-existing `DeprecationWarning`** on `asyncio.get_event_loop()` in `TestVerifySportSlug.test_slug_found` (untouched since H-018's flag). Noted for future cleanup. Out of scope here.

---

## 6. Tripwire events this session

**Zero tripwires fired. Zero OOP invocations.** Ten consecutive sessions now (H-010 through H-019) without firing a tripwire or invoking OOP.

Specific discipline points that held:

- **Research-first discipline actually exercised.** The "re-fetch polymarket-us-python README at code-turn time" standing instruction had sat in four consecutive handoffs (H-015 → H-018) without being exercised; H-019 finally ran it. H-019 is the session that converted the standing instruction from aspirational to executed. Going forward, H-020+ inherit a different discipline shape: not "re-fetch before drafting §16" but "re-fetch at every code-turn session that touches the SDK surface, verify nothing has moved since the H-019 baseline."
- **Surface-before-committing on the design choices.** The two design choices at §16 round 1 (1+99 composition default, `degraded` classification) were surfaced as open rather than baked into the draft. Operator tightened both rulings in ways Claude did not propose — this is evidence the surfacing flow produces better outcomes than pre-deciding would have.
- **Byte-identical preservation verified, not assumed.** Every §16 edit cycle (initial draft, round 1 feedback, round 2 amendments) was followed by a `diff` check against the pre-H-019 v4 to confirm §§1-15 remained byte-identical. Zero diff lines for lines 1-780 at every checkpoint.
- **No present_files call mid-session.** The one present_files call this session was at the operator-requested review step ("present for my review"), which is the appropriate moment. H-017's lesson applied throughout the research and amendment work — files staged in `/mnt/user-data/outputs/` but not presented until operator asked to see them.
- **Exit-state discipline on the re-fetch checkpoint.** Operator's tightened framing made exit state B (contradiction → DJ entry + §16 defers) a real branch, not a soft-edge. Claude surfaced findings in the structured (fetch record / claim-by-claim / gap analysis / exit-state recommendation / operator-confirmation-question) format operator specified; operator ruled. Discipline was: don't draft §16 against a shaky interpretation.
- **No DJ fabrication.** Zero DJ entries added this session per operator direction — the re-fetch was execution, not decision; §16 is research-doc production, not a rule change. Claude did not reach for a D-032 to "document the re-fetch" when operator had explicitly ruled out that move.

---

## 7. STATE diff summary (v16 → v17)

Key fields that changed:

- `project.state_document.current_version`: 16 → 17
- `project.state_document.last_updated`: 2026-04-20 → 2026-04-20 (unchanged calendar date — H-019 ran same day as H-018)
- `project.state_document.last_updated_by_session`: H-018 → H-019
- `phase.current_work_package`: rewritten to reflect H-019 accomplishments (I through V) and H-020 pickups (a, b, c)
- `sessions.last_handoff_id`: H-018 → H-019
- `sessions.next_handoff_id`: H-019 → H-020
- `sessions.sessions_count`: 18 → 19
- `sessions.most_recent_session_date`: 2026-04-20 → 2026-04-20 (unchanged)
- `open_items.resolved_operator_decisions_current_session`: pruned H-018 entries per settled convention; 3 H-019 entries added (H-019-session-cut-at-open, H-019-checkpoint-exit-state-A-clean, H-019-section-16-accept)
- `open_items.phase_3_attempt_2_notes`: +8 entries for H-019 (session-open audit, brief-prep reading, item 1 POD check, item 2 SDK re-fetch, item 3 §16 draft, item 4 review round 1, item 5 amendments, H-019 close summary)
- `open_items.raid_entries_by_severity.*`: unchanged (no RAID changes this session)
- `open_items.pending_operator_decisions`: unchanged (1 entry — POD-H017-D029-mechanism, unchanged)
- `scaffolding_files.STATE_md`: v16 → v17/pending
- `scaffolding_files.DecisionJournal_md`: committed_to_repo changed to true (H-018 bundle merge assumption; zero DJ entries this session); pending_entries unchanged at []
- `scaffolding_files.RAID_md`: committed_to_repo changed to true (H-018 bundle merge assumption; no H-019 RAID changes)
- `scaffolding_files.Handoff_H018_md`: pending → true (landed on main via H-018 bundle merge; self-audit verified)
- `scaffolding_files.Handoff_H019_md`: **new entry**, pending
- `scaffolding_files.clob_asset_cap_stress_test_research_md`: committed_to_repo back to pending; committed_session H-016 → H-019; note updated for §16

Prose sections updated:
- "Where the project is right now" — refreshed for H-019 close; added §16 landed paragraph
- "What changed in H-018" → replaced with "What changed in H-019"
- "H-019 starting conditions" → replaced with "H-020 starting conditions"
- "Validation posture going forward" — refreshed for H-020's application surfaces (retrospective for H-019 artifacts; preventive for main-sweeps code-turn per §16.9; preventive for §16 itself — frozen at H-019; surface POD-H017-D029-mechanism)

---

## 8. Open questions requiring operator input

**Pending operator decisions at session close: 1.**

- **POD-H017-D029-mechanism** — opened by D-030 at H-017. Question: how should D-029's push mechanism actually work given Claude.ai's sandbox environment has no access to Render env vars? H-019 resolution-path check found no change (no GitHub MCP connector in Anthropic's registry, no other sandbox-accessible secret-injection mechanisms, no operator preference shift). Not urgent; project operates correctly under the D-030 interim flow. Surface at each session-open per D-030 Resolution path.

Items carried forward from prior sessions, not specific to H-019:

- Object storage provider for nightly backup — Phase 4 decision.
- Pilot-then-freeze protocol content — Phase 7 decision (D-011).
- Four plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, -2, -3, -4) — cut at next plan revision under Playbook §12.

Items H-020-Claude should raise at session open:

- **POD-H017-D029-mechanism resolution-path check** per D-030: brief check (no material change expected absent explicit operator signal). If any change is material, becomes its own targeted DJ entry. No urgency.
- **H-020 cut decision.** Operator names which deliverables are in scope. Default offer based on this handoff: main sweeps code (`src/stress_test/sweeps.py` + `tests/test_stress_test_sweeps.py`) implementing §16 as operator-reviewed, with live smoke run deferred to H-021. Alternate path: code + live smoke in the same session — possible but long; the live smoke run carries its own operator-attention demand (two-shell workflow extension), and the one-deliverable-per-session pattern suggests smoke run is more likely H-021.

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Clean. Read Handoff_H-018 in full (281 lines including H-018-Claude's informal letter). Read Orientation, Playbook end-to-end, STATE v16 YAML + prose in full, DecisionJournal all 31 entries, RAID in full, SECRETS_POLICY §§A and B, research-doc §§7/13/14/15, probe.py header block [A]-[D]. Performed the self-audit per Playbook §1.3 as a visible block at the start of the response; zero discrepancies found against on-disk reality (H-018 bundle commit verified; DJ at 31 entries with D-031 at top verified; STATE current_version: 16 verified at line 51; RAID I-017 Resolved verified; `tests/test_discovery.py` renamed methods verified at lines 566, 581; method names matching H-018's claim verified).

**Brief-prep recommendation and execution:** Surfaced items 1–4 (plan §5.4/§11.3, probe.py implementation, stress_test/requirements.txt, RB-002) as brief-prep gaps before declaring ready. Operator approved; ~45 min focused reading executed. Report surfaced the load-bearing question for §16 (M1 multi-same-type subscription composition semantics) before drafting.

**Pacing discipline:** Held across the session. Operator's cut at open (§16 only) was recommended by Claude and approved; Claude did not push to expand scope into code. Operator's "hold before starting — wait for signal" instruction was honored — no substantive work touched until explicit authorization at each stage.

**Surfacing-not-rationalizing exercised throughout:**
- Session-open: brief-prep gaps surfaced explicitly rather than declaring ready.
- Item 2 re-fetch: findings structured in the (fetch record / claim-by-claim / gaps / exit-state / operator-confirmation) format per operator's specified shape.
- Item 2 exit-state recommendation: both gaps (M1, M2) explicitly surfaced and framed as measurement questions; caveat included that "when uncertain which exit state, it's B" per operator's tightening.
- Item 3 round 1: two design choices surfaced as open (1+99 default, `degraded` classification) rather than baked into draft; operator tightened both in directions Claude did not propose.
- §16.11 explicit bullet about "§16 does not amend §§1-15": operator flagged it; Claude applied it. The framing "state it, don't infer it from byte-identical preservation" is preserved.

**Pushback exercised:** None directly against operator this session — operator's instructions were unambiguous throughout. The session's moments of pushback were Claude's own — recommending brief-prep items before drafting; recommending §16-only as the cut; surfacing design choices as open rather than pre-deciding.

**Pacing assessment:** Right-sized session. One deliverable (§16 addendum) of genuine research value; one standing-instruction-finally-exercised discipline win (the four-handoff polymarket-us-python README re-fetch standing instruction ran for the first time at H-019); one calibration (operator's tightened exit-state framing shifting the default from A to B when uncertain — worth internalizing for future-Claude on future research-first checkpoints). Landed with §16 as accepted, bundle producing, operator satisfied. Clean cut per operator's close ("Good work. Clean cut.").

**Out-of-protocol events:** 0 this session. Cumulative: 0.
**Tripwires fired:** 0. Ten consecutive sessions with zero tripwires.
**DJ entries added:** 0 (per operator direction — re-fetch is execution, §16 is production, neither reaches DJ-entry threshold). Total entries: 31 (unchanged).
**RAID changes:** none. Open issues 13, total 17 (unchanged).

**Quiet uncertainties carried into session close:**

- **M1 and M2 are named measurement questions in §16 but remain empirically unresolved.** The harness will answer them when H-020 implements sweeps code and H-021 (or later) runs the live smoke. If M2 resolves as "shared" (two `client.ws.markets()` calls on one client return the same object), the concurrent-connections axis of §7 Q3=(c) isn't testable via a single-client design; a secondary strategy (multiple clients) needs a DJ entry at code-turn time. Flag for H-020-Claude: don't presume M2 resolution independent; treat the first N=2-connections cell's observations as the resolution, and if secondary strategy is needed, DJ-entry-it before writing it.
- **Placeholder-slug synthesis details (§16.10).** §16 commits to format-matching synthesis but leaves the exact construction (past-dated vs far-future vs syntactically invalid) as a code-turn decision informed by M4 pilot observations. If placeholder rejection is hard (BadRequestError on the whole subscription), synthesis needs to be "farther from real" than if rejection is silent. H-020-Claude should synthesize a few candidate placeholder schemas and pilot one against a single subscribe before committing to 100-slug batches.
- **The §17 or further-additive slot.** §16 will be interpreted by a subsequent research-doc section written after the live smoke. §14 is the precedent. That section's shape (§17? §17-reserved-like-§14-was? different number?) is a minor judgment call for the session that writes it.
- **The 10-consecutive-clean-discipline streak has a growing weight.** Ten sessions is a real pattern. Worth noting without overclaiming: the discipline is holding because operator cuts cleanly, Claude surfaces before deciding, and the project's rituals are well-matched to the work. The streak is an artifact of the governance model working, not an independent thing to protect. If it breaks, it breaks; the discipline is what matters.

---

## 10. Next-action statement

**The next session's (H-020) first actions are:**

1. Accept handoff H-019.

2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-020 open the check applies in three modes:
   - **Retrospective for H-019 artifacts.** STATE v17, Handoff_H-019, research-doc §16 additive (1127 lines total; §§1-15 byte-identical to v4 pre-H-019). Spot-check that on-disk reality matches the bundle's claims. Specific checks: `wc -l docs/clob_asset_cap_stress_test_research.md` → 1127; `grep -c "^## 16\." docs/clob_asset_cap_stress_test_research.md` → 11 subsections (§16.1 through §16.11); §§1-15 byte-identical check via `diff <(sed -n "1,780p" docs/clob_asset_cap_stress_test_research.md) <(git show HEAD~N:docs/clob_asset_cap_stress_test_research.md)` against a pre-H-019 revision; `grep "current_version: 17" STATE.md` → match; DJ at 31 entries (unchanged).
   - **Preventive for main sweeps code turn.** Per §16.9 step 1, **re-fetch `github.com/Polymarket/polymarket-us-python` README at H-020 code-turn time.** H-019 established a clean baseline (10 commits, polymarket-us==0.1.2); H-020 verifies nothing has moved in the intervening hours/days. If [E] has moved materially (commit count changed, SDK version past 0.1.2, any surface change), do NOT write code against §16's commitments without first surfacing the delta. That is a governance-layer event and warrants a targeted DJ entry before code. Fetch record for H-020 goes in H-020's handoff, not in a revised §16 — §16 is frozen at H-019.
   - **Preventive for §16 itself.** §16 is frozen at H-019. H-020 does not amend §16. A H-020-side re-fetch that finds [E] changed is surfaced via handoff and DJ entry (if material), not by editing §16.

3. **Raise two session-open items explicitly** before substantive work:
   - **POD-H017-D029-mechanism resolution path check** per D-030. Brief check whether anything has changed. If material change, becomes a targeted DJ entry. If no change, note "POD-H017-D029-mechanism remains open; no path-change detected" and proceed.
   - **H-020 cut decision.** Operator names which deliverables are in scope. Default offer based on this handoff: main sweeps code only this session (`src/stress_test/sweeps.py` + `tests/test_stress_test_sweeps.py` + `src/stress_test/requirements.txt` and `src/stress_test/README.md` updates if needed), live smoke run deferred to H-021 per D-019 research-first-then-code sequencing and one-deliverable-per-session pattern. Alternate path: code + live smoke in the same session — possible but long.

4. **Main sweeps code implementation** when authorized. Per §16:
   - New module: `src/stress_test/sweeps.py` with CLI surface (`--sweep=subscriptions|connections|both`, `--observation-seconds=N`, `--slug-source=api|gateway`, `--seed-slug=SLUG` optional).
   - Default grid: 1/2/5/10 subscriptions per connection × 1/2/4 concurrent connections, 1 real anchor slug + 99 placeholder slugs per subscription.
   - Dedicated 100P/0R M4 control cell (single-subscription, single-connection, `cell_id="m4-control-100p-0r"`, `real_slug=""`).
   - Outcome record shapes per §16.6: `SweepCellOutcome`, `ConnectionObservation`, `SubscribeObservation`, `SweepRunOutcome`.
   - Five-way classification per §16.7: `clean`/`degraded`/`rejected`/`exception`/`ambiguous` with subscribe-success-ratio threshold pinned (≤0.5 rejected, (0.5, 1.0) exclusive degraded, 1.0 candidate for clean). Seven-step precedence list in §16.7.
   - Event-handler pattern mirrors probe.py lines 445–450 (register before connect/subscribe; same six events).
   - Exception catching mirrors probe.py lines 476–530 (documented SDK exceptions → rejected; transport → exception; catch-all → exception).
   - No debouncing (`responsesDebounced` explicitly false or omitted per §16.5).
   - No disk writes per §7 Q1=(a).
   - New test file: `tests/test_stress_test_sweeps.py`. Exercises non-network paths: grid generation, placeholder-slug synthesis, classification state machine (each precedence rule covered), outcome record serialization, config loading. Zero SDK mocking per H-012 addendum.

5. **Live smoke run per D-021** only if authorized in a subsequent turn or session. Expected shape extending RB-002's two-shell workflow: real-slug anchor fetch via `markets.list()` on `pm-tennis-stress-test` Shell (no longer requires `pm-tennis-api` Shell since `markets.list()` doesn't need disk access); sweeps invocation via `python -m src.stress_test.sweeps --sweep=both`; `SweepRunOutcome` JSON captured from stdout. Acceptance bar per §16.8 item 3 includes M4 control cell runs to completion.

6. **Session-close per Playbook §2** — STATE v18, Handoff_H-020, DJ entries for any new numbered decisions.

**Phase 3 attempt 2 starting state at H-020 session open:**

- Repo on `main` with the H-019 bundle merged (assuming operator completes the merge): STATE v17. DJ at 31 entries (unchanged, D-031 still at top). Handoff_H-019. `docs/clob_asset_cap_stress_test_research.md` at v4 + §16 additive (1127 lines). RAID unchanged. `tests/test_discovery.py` unchanged from H-018.
- Live `pm-tennis-api` service with I-016 fix deployed; behavior unchanged at H-019 (research-doc-only).
- Live `pm-tennis-stress-test` service; one successful probe in its history.
- One pending operator decision: POD-H017-D029-mechanism (low urgency).
- §16 populated and frozen; §17 or further-additive is the natural next slot for the main-sweeps-outcome addendum after live smoke.
- Four plan-text pending revisions in STATE (v4.1-candidate, -2, -3, -4).
- D-030 interim flow is the default deployment mechanism. `claude-staging` branch exists; merge gate is operator-only.
- **Ten consecutive sessions (H-010 through H-019) closed without firing a tripwire or invoking OOP.**
- Research-first discipline in force per D-016, D-019 — now with §16.9 as the standing re-fetch instruction for every session that touches the SDK surface.
- 'Always replace, never patch' file-delivery discipline in force per H-016 / D-029 §3.
- SECRETS_POLICY §A.6 in force.
- D-031 active. D-030 active. D-029 active but Commitment §2 suspended per D-030. D-028 active. D-027 active. D-025 commitment 1 superseded by D-027; 2/3/4 in force. D-024, D-023, D-020, D-019, D-018, D-016 in force.

---

*End of handoff H-019.*
