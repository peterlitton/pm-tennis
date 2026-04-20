# PM-Tennis Session Handoff — H-020

**Session type:** Code turn — §16 main-sweeps-scope implementation; operator-cut at open to sweeps code only, live smoke deferred to H-021
**Handoff ID:** H-020
**Session start:** 2026-04-20
**Session end:** 2026-04-20
**Status:** Bundle produced — STATE v18, `src/stress_test/sweeps.py` (2,422 lines), `tests/test_stress_test_sweeps.py` (1,330 lines, 91 tests), DecisionJournal.md (two new entries D-032 and D-033 at top), Handoff_H-020. Eleven consecutive clean-discipline sessions (H-010 → H-020). Zero tripwires, zero OOP. Two DJ entries this session. Shape A session-close per operator ruling — ship sweeps code and tests, defer live smoke to H-021. §16.8 items 1+2 met; items 3+4 explicitly deferred. §16.9 standing-convention addendum landed as Handoff §4 (not §16 prose per §16.11).

---

## 1. What this session accomplished

H-020 opened from H-019 with operator authorization (standing) to clone the repo. Session-open reading covered Handoff_H-019 in full (324 lines including H-019-Claude's informal letter), Orientation, Playbook end-to-end (all 13 sections), STATE v17 YAML + prose, DecisionJournal all 31 entries extant at session open (D-001 through D-031), RAID.md in full, research-doc §§13/14/15/16 in full (§16 is the design source of truth for this code turn), probe.py 764 lines (reference pattern), slug_selector.py 283 lines, `tests/test_stress_test_probe_cli.py` and `tests/test_stress_test_slug_selector.py` for fixture pattern. Session-open self-audit passed against on-disk reality: H-019 bundle merged cleanly on `main` (commits `ee85985` and `1117781`); DJ at 31 entries with D-031 at top; STATE v17; research-doc at 1127 lines with §16 complete (§§16.1-16.11); claude-staging branch present on remote. Zero discrepancies.

Operator cut the session at open to **sweeps code + tests only**. Live smoke run deferred to H-021 per §16.8 items 3+4 and the one-deliverable-per-session pattern.

H-019-Claude's informal letter named three pause-checkpoints for the code turn — after scaffolding, after classification state machine, after outcome record serialization. This session adopted the letter's discipline with one operator-approved modification: checkpoints 2 and 3 were reorganized to (2) outcome records + classification, (3) self-check + async + CLI + per-cell M-resolvers + aggregate summaries. Three checkpoints ran in order. Each surfaced before proceeding.

Seven substantive workstreams landed this session:

1. **Item 1 — POD-H017-D029-mechanism resolution-path check per D-030.** No GitHub MCP connector in this session's tool surface. Unchanged from H-016/H-017/H-018/H-019 findings. No path-change detected. No targeted DJ entry per D-030's "if material" clause.

2. **Item 2 — §16.9 step 1 SDK re-fetch per R-010 / D-016 commitment 2.** Re-fetched [E] `github.com/Polymarket/polymarket-us-python` — 10 commits on main unchanged from H-019 baseline; 5 stars; MIT. Re-fetched [F] `docs.polymarket.us/api-reference/websocket/markets` — 100-slug subscription cap language verbatim identical. Re-fetched [G] `libraries.io/pypi/polymarket-us` — 0.1.2 still latest (2 releases total, both 2026-01-22). Three verification surfaces Claude named for the re-fetch: (a) `client.markets.list()` exists with optional params dict returning `{'markets': [...]}` — inner element shape NOT pinned in README, flagged for defensive handling in code; (b) multi-subscribe example on `markets_ws` still shows different-type composition only, M1 remains empirical per §16.4 framing (no change); (c) exception surface has six documented types in README's Error Handling example (unchanged from [A] citation). Operator ruled exit state A (clean) on the re-fetch; §16 drafting commitments stand unchanged. *Note: at checkpoint 3 SDK introspection, the installed module was discovered to export 12 exception classes vs README's 6 — see §2.2 (D-033) for the gap and resolution.*

3. **Item 3 — Sweeps code production (three-checkpoint discipline per H-019-Claude letter).** Checkpoint 1 (module scaffolding — header with citations [E]/[F]/[G]/[H], exit codes, wire-format constants, `SweepConfig` + `load_sweep_config`, `CellSpec` dataclass + `build_default_grid` producing 8 cells with M4 control first, placeholder-slug synthesis, `build_slug_list_for_subscription`) approved with three flag rulings: placeholder format `aec-ph-<hex>-<hex>-2099-12-31`, exit codes at 4/5/6/12 preserving probe's 1/2/3 unused in sweeps namespace, 30s default observation window. Checkpoint 2 (outcome records per §16.6 + classification state machine per §16.7) surfaced the §16.7 clean-(iii) Meaning-vs-Rule column ambiguity during mechanical transcription → **D-032** landed (Reading B: anchor-specific clean-(iii)). Checkpoint 3 (self-check + async execution + CLI + per-cell M-resolvers + aggregate summaries) surfaced the SDK exception-surface gap during introspection of installed `polymarket-us==0.1.2` → **D-033** landed (12 exception classes in module's `__all__` vs 6 in README's Error Handling example; frozenset assignments revised). Final `sweeps.py` state: 2,422 lines; 6 classes (`SweepConfig`, `CellSpec`, `SubscribeObservation`, `ConnectionObservation`, `SweepCellOutcome`, `SweepRunOutcome`); 31 sync functions + 3 async functions. No changes outside scope: `pm-tennis-api/requirements.txt` unmodified (D-024 commitment 1), no Phase 2 code touched (D-016 commitment 2), `slug_selector` not called in sweeps production path (D-027).

4. **Item 4 — D-032 drafted, reviewed, landed.** Claude surfaced the §16.7 clean row Meaning-vs-Rule column disagreement at checkpoint 2 pause. Three readings considered (A Rule-column literal, B Meaning-column literal, C both-hold-with-veto). Claude recommended B. Operator ruled Reading B — §16.5's anchor rationale is for M1-attributable traffic via §14.3 `marketSlug` echo; heartbeat is connection-level and not subscription-attributable. Entry drafted, reviewed verbatim by operator, accepted as written. Fix applied: `_cell_has_any_traffic` renamed to `_cell_has_anchor_slug_traffic_qualifying`; step 5 default-cell branch uses anchor-specific predicate; M4 control cell's relaxed-clean caveat preserved unchanged. Regression test (`test_d032_anchor_zero_traffic_regression`) pins Reading B with a docstring citing D-032 by number.

5. **Item 5 — D-033 drafted, reviewed, landed.** Claude ran `pip install -r src/stress_test/requirements.txt` at checkpoint 3 to verify self-check + CLI paths against a real SDK. SDK introspection surfaced 12 exception classes in `polymarket_us.__all__` where [E]'s README Error Handling example illustrates 6. Complete hierarchy walked and documented (PolymarketUSError ← Exception; APIStatusError base for six 4xx/5xx leaves; APIConnectionError base for APITimeoutError; WebSocketError on its own branch). Four alternatives considered (stay-with-six, expand-by-isinstance, defer-WebSocketError, InternalServerError-as-rejected). Selected named-expansion middle path per HTTP-semantic partition (4xx client-refusal vs 5xx server-infrastructure + network + WS-layer). Framed as exit-state-B material under "when uncertain, default to B" — the gap between research record and installed surface was not caught at H-019 or H-020 §16.9 step 1 re-fetch because the re-fetch was README-only. Operator accepted D-033 as written. Commit: `DOCUMENTED_REJECTED_EXCEPTION_TYPES` expanded to 5 (adding `PermissionDeniedError`); `DOCUMENTED_TRANSPORT_EXCEPTION_TYPES` expanded to 5 (adding `InternalServerError` and `WebSocketError`); module header [I] citation added for installed-module `__all__` as authoritative public surface. 13 per-type regression tests + frozenset membership pin = 14 standing D-033 tests.

6. **Item 6 — §16.9 standing-convention addendum established via this handoff (no §16 edit).** D-033's surfacing established that README-text re-fetch per §16.9 step 1 as originally written is insufficient. Future §16 code-turn sessions perform both README re-fetch AND installed-module introspection. Single exit-state rule covers both layers. Convention-level guidance; not §16 prose per §16.11. Full wording in §4 of this handoff.

7. **Item 7 — Test file production.** `tests/test_stress_test_sweeps.py` landed at 1,330 lines with 91 tests, all passing (0.39s). Mechanical transcription of the checkpoint-2 and checkpoint-3 sanity checks into a standing pytest regression suite, plus edge-case coverage for CLI/config/grid/placeholder/classification/aggregation surfaces. Non-network-only per D-021. SDK imported only for exception-class construction in D-033 per-type regression tests; no SDK method called. D-032 and D-033 regression tests have docstrings citing DJ entry by number per H-018's D-031-inline-citation precedent. Full-repo pytest: 204 passed (91 new + 113 existing), zero regressions.

Plus the usual close-bundle assembly: STATE v18 produced with full YAML validation; this handoff.

### Work that landed

| Item | Status |
|------|--------|
| H-019 handoff accepted; full reading | ✅ Complete |
| Session-open self-audit per Playbook §1.3 + D-007 | ✅ Complete — zero discrepancies; H-019 bundle verified on `main` |
| Repo clone (standing authorization) | ✅ Complete |
| Orientation.md re-read | ✅ Complete |
| Playbook.md end-to-end (all §§1-13) | ✅ Complete |
| DecisionJournal all 31 entries at session open (D-001 through D-031) | ✅ Complete |
| RAID.md in full | ✅ Complete |
| Research-doc §§13, 14, 15, 16 in full | ✅ Complete |
| probe.py full 764 lines (reference pattern) | ✅ Complete |
| slug_selector.py 283 lines | ✅ Complete |
| Fixture-pattern test files (probe_cli, slug_selector) | ✅ Complete |
| Item 1: POD-H017-D029-mechanism resolution-path check per D-030 | ✅ Complete — no path-change detected; POD remains open |
| Item 2: §16.9 step 1 SDK re-fetch ([E] + [F] + [G]) | ✅ Complete — exit state A ruled on README layer |
| Item 3 checkpoint 1: scaffolding (543 → 543 lines) | ✅ Complete — three flag rulings approved |
| Item 3 checkpoint 2: outcome records + classification (543 → 920 lines) | ✅ Complete — D-032 surfaced, ruled, landed |
| Item 3 checkpoint 3: self-check + async + CLI + M-resolvers + aggregates (920 → 2,422 lines) | ✅ Complete — D-033 surfaced, ruled, landed |
| Item 4: D-032 drafted + reviewed verbatim + landed | ✅ Complete — Reading B, anchor-specific clean-(iii) |
| Item 5: D-033 drafted + reviewed verbatim + landed | ✅ Complete — frozensets expanded to 5+5 |
| Item 6: §16.9 standing-convention addendum (this handoff §4) | ✅ Complete |
| Item 7: tests/test_stress_test_sweeps.py (1,330 lines, 91 tests) | ✅ Complete — all passing, 204 full-repo |
| STATE v18 produced with YAML validation | ✅ Complete — YAML parses clean |
| Handoff_H-020.md produced | ✅ Complete (this document) |

---

## 2. Decisions made this session

### 2.1 D-032 — §16.7 clean-(iii) reading: anchor-specific per Meaning column (Reading B)

Surfaced at checkpoint 2 pause during mechanical transcription of the classification state machine. §16.7's `clean` row has a Meaning column (*"message traffic received on the anchor slug(s) within the observation window"*) and a Rule column (*"at least one `market_data` or `trade` or `heartbeat` received across the cell"*) that disagree on clean-(iii) for default cells. Under Reading A (Rule column literal), the §16.7 `degraded` row's anchor-zero-traffic anomaly becomes operationally unreachable — a heartbeat-only + zero-anchor-traffic cell would satisfy clean-(iii) at step 5 and step 6 never fires.

Operator ruled **Reading B**: clean-(iii) is anchor-slug-specific per the Meaning column. Rule column's "across the cell" phrasing is imprecise transcription. §16.5's 1+99 anchor rationale is to produce attributable traffic for M1 measurement via the §14.3 `marketSlug` echo; heartbeat is connection-level and not subscription-attributable. A cell with heartbeats but zero anchor `market_data` / `trade` is meaningfully degraded.

§16 prose not edited; §16 remains frozen per §16.11. D-032 is the standing clarification reference. M4 control cell's relaxed-clean caveat (no traffic required) preserved unchanged. Regression test (`test_d032_anchor_zero_traffic_regression`) pins Reading B with a docstring citing D-032 by number; if the assignment is ever reverted, the test fails with direct traceability.

Full DJ entry: `DecisionJournal.md` D-032 (second entry from top).

### 2.2 D-033 — `polymarket-us==0.1.2` full exception surface: frozenset assignments revised

Surfaced at checkpoint 3 hard pause during SDK introspection. Claude ran `pip install -r src/stress_test/requirements.txt` to verify self-check + CLI paths; introspection of the installed module revealed `polymarket_us.__all__` exports 12 exception classes where [E]'s README Error Handling import example illustrates only 6. Complete hierarchy walked:

```
PolymarketUSError (root)
├── APIError
│   ├── APIConnectionError                [README] → transport
│   │   └── APITimeoutError               [README] → transport
│   └── APIStatusError (HTTP 4xx/5xx base)
│       ├── BadRequestError (400)         [README] → rejected
│       ├── AuthenticationError (401)     [README] → rejected
│       ├── PermissionDeniedError (403)             → rejected
│       ├── NotFoundError (404)           [README] → rejected
│       ├── RateLimitError (429)          [README] → rejected
│       └── InternalServerError (500+)              → transport
└── WebSocketError                                  → transport
```

Framed as exit-state-B material under "when uncertain, default to B" — the gap between §16.1's "SDK unchanged" research-record claim and the installed module's surface was not caught at H-020 §16.9 step 1 re-fetch because the re-fetch was README-only. §16.9 step 1 was performed correctly per its letter; the gap is in what §16.9 asks for, not how the re-fetch was performed.

Four alternatives considered (stay-with-six, expand-by-isinstance, defer-WebSocketError, InternalServerError-as-rejected). Operator ruled the **named-expansion middle path** per HTTP-semantic partition:

- **`DOCUMENTED_REJECTED_EXCEPTION_TYPES` → 5 types** (4xx client-refusal): `AuthenticationError`, `BadRequestError`, `NotFoundError`, `PermissionDeniedError` (D-033 addition), `RateLimitError`.
- **`DOCUMENTED_TRANSPORT_EXCEPTION_TYPES` → 5 types** (5xx server-infrastructure + network + WS-layer): `APIConnectionError`, `APITimeoutError`, `TimeoutError` (asyncio qualname), `InternalServerError` (D-033 addition), `WebSocketError` (D-033 addition).
- **Base classes** (`APIError`, `APIStatusError`, `PolymarketUSError`) — not in either frozenset; catch-all routes to `exception` defensively.

§16 prose not edited; §16 remains frozen per §16.11. D-033 is the standing clarification reference for the frozenset assignments. Module header [I] citation added alongside [E] to name the installed-module `__all__` as the authoritative public-surface source. 13 per-type regression tests + 1 frozenset membership pin = 14 standing D-033 tests, each with a docstring citing D-033 by number and each constructing the minimal exception instance the classifier would see in live execution (using `httpx.Response` stubs for `APIStatusError` subclass constructors).

Full DJ entry: `DecisionJournal.md` D-033 (top entry).

---

## 3. Pushback and clarification events this session

**3.1 Checkpoint 1 pause — three design flags surfaced for operator rulings.** At the end of checkpoint 1 scaffolding, Claude surfaced three items for explicit operator ruling before deepening: (a) placeholder-slug format `aec-ph-<hex>-<hex>-2099-12-31` — could be revised to different strategies (syntactically-invalid slugs, past-dated "expired" slugs); (b) sweep-specific exit codes 4/5/6/12 preserving probe's 1/2/3 — could be merged into a different scheme; (c) default observation window 30s — §16.10 named 30-60s range as undecided. Operator ruled all three approved as-proposed; not DJ-entry thresholds (code-turn mechanics, not rule changes).

**3.2 Checkpoint 2 pause — §16.7 Reading B surfaced for operator ruling.** See §2.1.

**3.3 Operator message duplicate-paste events (two separate occurrences).** Two operator messages during the session were duplicates of earlier messages (wrong-draft pasted). Both caught cleanly by Claude before further execution — first at the re-authorization after checkpoint 1 ruling; second later mid-session. In each case, Claude stopped, named three possible interpretations (duplicate paste / re-authorization / implicit approval), and held for clarification. Operator's intent on both was duplicate paste; no re-execution required. This is a governance-layer observation, not a DJ-entry threshold — the discipline of "pause and surface when uncertain" honored in both cases.

**3.4 Checkpoint 3 hard pause — SDK exception surface surfaced.** See §2.2. Operator explicitly framed this as the discipline boundary: "This is checkpoint-worthy and belongs at a hard pause, not absorbed into checkpoint 3." Claude held the rest of checkpoint 3 work (tests file write + session close) pending D-033 resolution.

**3.5 D-032 and D-033 entry-text paste-before-ruling.** Both D-032 and D-033 were pasted in full (verbatim DJ-entry text) before operator ruled on them. Discipline: operator ruled on the artifact, not a gloss. Same pattern for both entries — operator pre-ruled substance, then requested verbatim text, then accepted as written.

**3.6 Shape A / Shape B session-close framing.** At session-close surface, Claude presented two possible shapes (A ship-tests-scaffolded-live-smoke-deferred vs B defer-close-unified-H-020+H-021-closure) with tradeoffs. Operator ruled Shape A — preserves one-deliverable-per-session pattern. Shape B would have eroded the discipline load-bearing since H-013/H-014.

**3.7 Two small refinements at close-surface ruling.** Operator approved STATE v18 entries and Handoff TOC with two small refinements: (a) item 1's "DJ all 31 entries D-001 through D-031" tightened to "31 entries extant at session open (... DJ grew to 33 with D-032 and D-033 landing this session)" for count-at-open/count-at-close clarity; (b) §11 next-action item 7 adds single-line hint about the most-likely-close shape for H-021-Claude's session-open reading ("Shape A-equivalent — H-021 produces SweepRunOutcome capture and analysis; §17 interpretation and plan-revision work defers to H-022 unless operator extends H-021's scope"). Both applied.

---

## 4. §16.9 standing-convention addendum (proposed H-020; landed as standing convention via this handoff — no edit to §16 prose per §16.11)

**Session-close discipline for §16 code turns is extended: the §16.9 step 1 re-fetch check covers both layers that can drift independently.**

**Step 1a — README re-fetch.** Re-fetch [E]/[F]/[G] per §16.9 as originally written. Compare against the H-019 baseline (commit count, page content, PyPI version).

**Step 1b — Installed-module introspection.** `pip install -r src/stress_test/requirements.txt` (idempotent) and introspect the installed package: read `polymarket_us.__all__`, walk the exception hierarchy, read docstrings on exception classes, check for surfaces the README illustrates but does not enumerate exhaustively. Compare against the set of SDK surfaces the code under development will invoke.

**Single exit-state rule covers both layers:** If either layer surfaces a gap against the research record, default to exit state B per H-019's tightening.

**Rationale.** README-documented and module-exported surfaces can diverge without either being wrong. A README example is illustrative, not exhaustive; a module's `__all__` is the authoritative public-API declaration. H-020 surfaced this at checkpoint 3 when SDK introspection found 12 exception classes where the README's Error Handling section illustrates 6 (see D-033). The §16.9 check-as-originally-written was satisfied at H-020 §16.9 step 1 re-fetch time; the installed-module gap only appeared during checkpoint 3 code writing. Making step 1b standing convention moves the check earlier — before code that depends on the surface gets shipped.

**Precedent.** This is the H-013 / §15.1.3 discipline ("install the pinned version and exercise every surface used in-code against the installed package") applied to §16 code turns. H-013 established it for the initial probe implementation; it was not carried forward explicitly to §16.9. D-033 and this addendum close that gap.

**Scope of the addendum.** Convention-level guidance for future code-turn sessions. Does not edit §16 prose (§16 remains frozen at H-019 per §16.11). A future research-doc addendum (§17 or later) may formalize the convention in prose if useful; this handoff memorializes it as standing practice pending that. Where H-021 and subsequent sessions cite the convention, they cite D-033 and this handoff §4.

---

## 5. Files created / modified this session

**Created:**
- `src/stress_test/sweeps.py` (2,422 lines) — the main-sweeps harness implementing §16. Six classes, 31 sync functions, 3 async functions. Module header carries citations [E]/[F]/[G]/[H]/[I] with full provenance for every load-bearing symbol. No imports of `slug_selector` (D-027 compliance). No touches to Phase 2 code (D-016 commitment 2).
- `tests/test_stress_test_sweeps.py` (1,330 lines) — 91 tests across 10 sections. Non-network-only per D-021. SDK imported only for exception-class construction in D-033 per-type regression tests. D-032 and D-033 tests have docstrings citing DJ entries by number.

**Modified:**
- `DecisionJournal.md` — two new entries at top: D-033 (SDK exception-surface), D-032 (§16.7 Reading B). DJ counter 31 → 33.
- `STATE.md` — v17 → v18. Field bumps: `state_document.current_version`, `state_document.last_updated_by_session`, `sessions.last_handoff_id`, `sessions.next_handoff_id`, `sessions.sessions_count`. `phase.current_work_package` single-line string extended with H-020 accomplishment summary. `open_items.resolved_operator_decisions_current_session` pruned to H-020 entries only (per H-014-settled stricter-reading convention) with four new entries (checkpoint 1 approval, checkpoint 2 + D-032, checkpoint 3 + D-033, session-close shape A). `open_items.phase_3_attempt_2_notes` appended with nine H-020 entries.

**Unchanged (explicitly verified):**
- `pm-tennis-api/requirements.txt` — D-024 commitment 1 honored.
- `src/stress_test/requirements.txt` — no dependency changes; SDK pin at `polymarket-us==0.1.2` unchanged.
- `src/stress_test/probe.py`, `src/stress_test/slug_selector.py`, `src/stress_test/list_candidates.py` — no edits.
- `tests/test_discovery.py`, `tests/test_stress_test_probe_cli.py`, `tests/test_stress_test_slug_selector.py` — no edits.
- `src/capture/` and everything else under Phase 2 — D-016 commitment 2 honored.
- `docs/clob_asset_cap_stress_test_research.md` — §16 remains frozen per §16.11; D-032 and D-033 are standing clarifications, not edits.
- `RAID.md` — no RAID-item changes this session.
- `runbooks/Runbook_RB-002_Stress_Test_Service.md` — no runbook changes this session (H-021 may add a sweeps invocation section).
- All other repo files.

---

## 6. Known-stale artifacts at session close

None.

H-017 had three known-stale artifacts pending deletion (CHECKSUMS.txt, COMMIT_MANIFEST.md, D-028-entry-to-insert.md); all deleted by operator during H-017 merge. H-018 through H-020 added none. The repo is clean of known-stale artifacts at H-020 close.

---

## 7. Tripwire events this session

None fired.

- **R-010 preventive-fabrication tripwire:** Honored throughout. Re-fetch at §16.9 step 1 time (before any new code) established clean baseline; checkpoint-3 SDK introspection added a second defensive layer that surfaced the README-vs-module gap before any code depended on the incomplete surface. See §4 for the standing-convention addendum addressing that gap class going forward.
- **D-016 commitment 2 (no Phase 2 touch):** Honored. Zero edits to `src/capture/`, `main.py`, or any Phase 2 module.
- **D-024 commitment 1 (pm-tennis-api/requirements.txt immutable):** Honored. File unchanged.
- **Mid-session `present_files` lesson (H-017 precedent):** Held. Zero `present_files` calls during session work; this bundle is the first and only `present_files` at session close per discipline.

---

## 8. STATE diff summary (v17 → v18)

**YAML field changes:**
- `project.state_document.current_version`: 17 → **18**
- `project.state_document.last_updated_by_session`: H-019 → **H-020**
- `sessions.last_handoff_id`: H-019 → **H-020**
- `sessions.next_handoff_id`: H-020 → **H-021**
- `sessions.sessions_count`: 19 → **20**
- `phase.current_work_package`: existing H-019 narrative preserved; appended full H-020 accomplishment summary (sweeps code production via three-checkpoint discipline; D-032 §16.7 Reading B; D-033 SDK exception-surface frozenset revision; §16.9 standing-convention addendum via Handoff §4; test file 91 tests 204 total; Shape A close; H-021 pickup).
- `open_items.resolved_operator_decisions_current_session`: pruned from H-019's 3 entries to H-020's 4 entries per H-014-settled stricter-reading convention. Entries: checkpoint-1-scaffolding-approved, checkpoint-2-and-D-032, checkpoint-3-and-D-033, session-close-shape-A.
- `open_items.phase_3_attempt_2_notes`: appended 9 new H-020 entries (open self-audit; item 1 POD-H017-D029 check; item 2 §16.9 step 1 re-fetch; item 3 sweeps code; item 4 D-032; item 5 D-033; item 6 §16.9 addendum; item 7 test file; close).

**DJ counter:** 31 → **33**

**RAID counter:** unchanged (13 open / 17 total). Zero RAID changes this session.

**Clean-discipline streak:** **11 consecutive sessions** (H-010 → H-020).

---

## 9. Open questions requiring operator input

**None blocking.**

Two low-urgency items remain open from prior sessions:

- **POD-H017-D029-mechanism.** How should D-029's push mechanism work given Claude.ai's sandbox has no access to Render env vars? Interim flow per D-030 operating correctly. Checked this session per D-030 Resolution path; no path-change detected (no GitHub MCP connector); no targeted DJ entry per "if material" clause.
- **I-015 (v4.1-candidate-2 plan revision).** The "150-asset pool cap" is not a documented Polymarket US limit. Plan §5.4 and §11.3 text revision deferred. Sweeps produce the data v4.1-candidate-2 will eventually reference; they don't cut the plan revision. H-021 live-smoke data + subsequent analysis feeds this.

**Potentially surfacing at H-021:**

- If live-smoke execution surfaces any of `PermissionDeniedError` / `InternalServerError` / `WebSocketError` and the observed classification contradicts D-033's frozenset assignment, a follow-up DJ entry at H-021 revises the assignment with the live-smoke evidence. The D-033 per-type regression tests fail with direct traceability if any assignment is reverted.
- If M1 resolves "replace" (not "compose") in live smoke, §16.4's framing needs a targeted §17 interpretation entry.
- If M2 resolves "shared" (not "independent"), the per-connection sweeps design in v4.1-candidate-2 needs revision.

---

## 10. Claude self-report

**Research-first discipline honored throughout.** Two DJ entries this session; both emerged from mechanical transcription finding internal ambiguities (D-032 at §16.7 text) or installed-surface gaps (D-033 at SDK introspection) rather than from Claude deciding to revise §16. §16 remained frozen per §16.11 across both entries. The D-032 / D-033 framing as "standing clarification without superseding §16" is the shape research-first discipline produces at code-turn time.

**Pause-and-surface discipline honored at every checkpoint.** Three checkpoints ran (1, 2, 3); each paused for operator ruling before proceeding. Checkpoint 1 pause surfaced three design flags. Checkpoint 2 pause surfaced D-032. Checkpoint 3 pause surfaced D-033 (and the checkpoint was hard-paused mid-work when the finding was checkpoint-worthy, not absorbed into the larger checkpoint surface). The "if you find yourself interpreting §16 at this checkpoint rather than transcribing it, pause and surface" direction from the operator at the start of checkpoint 2 was exercised exactly once, correctly, for D-032.

**Fabrication tripwire not fired.** R-010 preventive discipline held. The §16.9 step 1 re-fetch at session start established clean baseline; checkpoint-3 SDK introspection added a second defensive layer that surfaced the README-vs-module gap proactively. The gap was surfaced-then-resolved at H-020, not absorbed-as-fabrication-through-catch-all.

**Testing discipline honored.** 91 new tests; all non-network; no SDK mocking; D-032 and D-033 regression tests use actual SDK classes (via `httpx.Response` stubs for `APIStatusError` constructors) and carry docstrings citing DJ entries by number. Full-repo pytest at close: 204 passed, zero regressions. The tests mirror the H-020 sanity-check suite's coverage plus edge-case additions; no test that didn't correspond to a sanity check or a named coverage area.

**Mid-session `present_files` lesson from H-017 still held.** Zero `present_files` calls during session work. This bundle is the first and only `present_files` at session close per discipline.

**Two duplicate-paste events handled cleanly.** Both caught before execution; operator's intent surfaced via naming three interpretations and holding for signal. Neither required re-execution. This is governance-layer housekeeping, not a DJ-entry threshold.

**Session-close shape honest.** Shape A selected explicitly — sweeps code and tests ship, live smoke defers. §16.8 items 1+2 met; items 3+4 explicitly deferred. The "don't claim acceptance on items not yet met" discipline is the right frame for a code-turn that didn't touch the live gateway.

**What H-021-Claude should know from H-020-Claude (informally):** The sweeps harness is the first pm-tennis code that fans out to multiple concurrent WS connections against the live gateway. `_run_cell_async` is structurally defensive (exceptions captured to outcome, not raised; per-subscribe exception isolation; per-connection close in a finally-equivalent pattern), but the connections-axis N=4 cell is unprecedented in the project's live-network exercise history (probe.py was 1 connection × 1 subscription × 1 slug at H-013). The classifier's step-7 `ambiguous` fallthrough exists precisely for observations the rules don't capture. If the first live run surfaces anything that doesn't cleanly classify, pause and surface. Also: the `_fetch_anchor_slug` defensive shape handler tries `marketSlug`, `market_slug`, `slug` field names in order on dict-element and attribute-access fallback; if the live `markets.list()` return shape doesn't match any of the three, the handler returns `None` and the harness exits `EXIT_NO_ANCHOR_SLUG` (12). Surface that to operator before retrying with `--seed-slug` — it's observational data about the SDK's return shape that feeds a potential §17 entry. Finally: D-033's three frozenset additions (`PermissionDeniedError`, `InternalServerError`, `WebSocketError`) are predictions, not observations. Live smoke is the observation. If any of the three fires and the observed classification contradicts D-033's assignment, the DJ revises with live evidence. The per-type regression tests will fail with direct traceability if any assignment is reverted — use that as the sanity check on the revision.

— H-020-Claude

---

## 11. Next-action statement

H-021's scope carried forward:

1. **Session-open reading + self-audit** per Playbook §1.3 + D-007. Confirm H-020 bundle merged cleanly on `main`: STATE v18, DJ at 33 entries (D-033 at top, D-032 below), `src/stress_test/sweeps.py` at 2,422 lines, `tests/test_stress_test_sweeps.py` at 1,330 lines with 91 tests passing, Handoff_H-020 on disk. Full-repo pytest should show 204 passing (91 new sweeps + 113 existing).

2. **POD-H017-D029-mechanism resolution-path check per D-030.** `search_mcp_registry` for GitHub MCP connector availability. If unchanged from H-016–H-020 findings (no connector), no targeted DJ entry per "if material" clause.

3. **§16.9 step 1 + step 1b re-fetch per the H-020 handoff addendum.** Standing convention now: two layers.
    - **Step 1a (README re-fetch):** Re-fetch [E] `github.com/Polymarket/polymarket-us-python`, [F] `docs.polymarket.us/api-reference/websocket/markets`, [G] `libraries.io/pypi/polymarket-us`. Baseline at H-020: 10 commits on main; polymarket-us==0.1.2 latest; 100-slug cap language verbatim.
    - **Step 1b (installed-module introspection):** `pip install -r src/stress_test/requirements.txt` (idempotent). Introspect `polymarket_us.__all__`, walk the exception hierarchy, read docstrings on exception classes. Baseline at H-020: 12 exception classes, complete hierarchy rooted at `PolymarketUSError ← Exception` with six leaves under `APIStatusError` (see D-033 for the tree).
    - **Single exit-state rule covers both layers:** If either layer surfaces a gap against the research record, default to exit state B per H-019's tightening.

4. **Live smoke run on pm-tennis-stress-test Render service.** Per RB-002 two-shell workflow. Environment requires `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` env vars set on Render (D-023 canonical names). Invocation:
    ```
    python -m src.stress_test.sweeps --sweep=both --log-level=INFO
    ```
    §16.5 commits to the 8-cell grid execution order: M4 control cell (100P/0R) first per H-020 ruling, then subscriptions-axis (N=1, 2, 5, 10), then connections-axis (N=1, 2, 4). Expected total runtime ~4 minutes of observation time plus connect/subscribe/close overhead — well inside §16.5's ~30-minute envelope. Capture stdout (SweepRunOutcome JSON) to disk; redirect stderr to a log file.

5. **SweepRunOutcome analysis + D-033 frozenset assignment verification.** Compare observed exception behavior against D-033 predictions, particularly the three additions:
    - `PermissionDeniedError` — if fired on M4 control cell's subscribe, should classify as `rejected` per D-033. M4 control cell's placeholder slugs are candidates for 403 if the server treats them as unauthorized-slug-access.
    - `InternalServerError` — if fired, should classify as `exception` (transport). 5xx on a sweep critical path indicates server-infrastructure failure, not client refusal.
    - `WebSocketError` — most likely to fire at the WS-layer on the connections-axis (N=4) cell if the SDK wraps a transport error. Should classify as `exception` (transport).
    If any observed behavior contradicts D-033's frozenset assignments, a follow-up DJ entry at H-021 revises the assignment with the live-smoke evidence.

6. **§16.8 acceptance bar items 3+4 formal acceptance.** Item 3 (live smoke run against actual gateway) and item 4 (SweepRunOutcome JSON capture from live smoke). H-020 met items 1 (unit tests pass — 91 + 113 = 204) and 2 (code reviewable — all surfaced at H-020 checkpoints). §16.8 full-bar acceptance is H-021's deliverable.

7. **H-021 session close.** Whichever §17 addendum or v4.1-candidate-2 plan-revision feeder work the sweeps data enables. At operator discretion — not pre-committed here. If M1 resolves "replace" (not "compose"), §16.4's framing for the multi-same-type subscription question needs a targeted §17 interpretation entry. If M2 resolves "shared" (not "independent"), the per-connection sweeps design in v4.1-candidate-2 needs revision. These are §17-or-later decisions, not H-021 scope unless operator extends. Most-likely close shape, pre-committed to nothing: Shape A-equivalent — H-021 produces SweepRunOutcome capture and analysis; §17 interpretation and plan-revision work defers to H-022 unless operator extends H-021's scope.

**What H-021 does NOT do:** expand sweep scope, add grid cells, revise §16, modify probe.py, touch Phase 2 code. Pure live-smoke-execution session.

**Standing reminders for H-021-Claude:**

- Re-fetch at code-turn time is the standing R-010 / D-016 commitment, now extended to cover both README and installed-module layers per this handoff's §4.
- Mid-session `present_files` lesson (H-017 precedent) still held through H-020. No `present_files` call during session work; all files bundled for close only.
- D-027 (operator-supplied slug) — H-021 does not pass `--seed-slug` initially. Let `_fetch_anchor_slug` call `client.markets.list()` and exercise the defensive shape handler. If the handler fails to resolve a slug (returns `None`), the harness exits `EXIT_NO_ANCHOR_SLUG` (12) and the session reports that finding to the operator before retrying with `--seed-slug`.
- D-029 (claude-staging; operator merges). H-021 pushes bundle to claude-staging; operator merges per Playbook §13.
- D-030 (interim drag-and-drop flow) — if claude-staging push encounters a blocker, fall back to drag-and-drop per Playbook §13.5.7.

**If H-021-Claude opens and finds the H-020 bundle NOT merged:** full self-audit per Playbook §1.3; surface to operator before proceeding.

— H-020-Claude
