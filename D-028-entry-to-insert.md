## D-028 — RAID I-016 fix: source `event_date` from `startDate`, with `slug_selector` fallback for historical meta.json

**Date:** 2026-04-19
**Session:** H-016
**Type:** Bug fix / Phase 2 + Phase 3 / Operator-authorized

**Source:** Operator authorization at H-016 ("c with thorough documentation"), responding to Claude's three-option proposal for fixing RAID I-016 (empty `event_date` field in production meta.json). Investigation triggered by H-015's blocked probe attempt, completed at H-016 by reading a real raw gateway payload from event 9471 in the `pm-tennis-api` Render Shell.

**Decision:** Apply Fix C — both a forward-going extraction fix in `src/capture/discovery.py` AND a backward-compatible fallback in `src/stress_test/slug_selector.py`. Specifically:

1. **`src/capture/discovery.py` line 328** — change the `event_date` extraction from `event.get("eventDate")` (a key the gateway response does not include) to `str(event.get("startDate") or "").strip()[:10]`. Preserves the `event_date` field name on `TennisEventMeta` and its YYYY-MM-DD format; only the source key changes. Phase 2 code touched per explicit operator authorization separate from the Phase 3 attempt 2 work package (D-016 commitment 2).

2. **`src/stress_test/slug_selector.py` `_passes_date_filter`** — modify to read `event_date` first, then fall back to `start_date_iso[:10]` if `event_date` is empty or unparseable. The `start_date_iso` field has been correctly populated since Phase 2 deploy (it has always been sourced from `event.get("startDate")` on line 330 of discovery.py); the fallback makes ~116 historical meta.json files (written H-007 through H-016 with empty `event_date`) usable as probe candidates without mutating the immutable on-disk records.

3. **Test fixture correction at `tests/test_discovery.py`** — remove the `"eventDate": event_date` key from `make_raw_event()` (line 89 pre-fix). The fixture had been silently masking I-016: the production gateway has no `eventDate` key, but the test fixture provided one, so production code passed tests against a payload shape that did not match reality. The fix removes the false key and adds a fixture-level assertion in the new I-016 regression tests to guard against re-introduction.

**Considered (from H-016 in-session proposal):**

- (A) **Fix discovery.py only.** Smallest change. Forward-going correctness; historical 116+ meta.json files remain unusable (they're immutable per `_write_meta`).
- (B) **Workaround in slug_selector only, no Phase-2 touch.** Historical files immediately usable; bug in discovery.py persists; any future consumer of meta.json's `event_date` field still sees empty values.
- (C) **Both.** Forward correctness AND backward compatibility. Two file changes; touches Phase 2.

Selected: (C). Operator ruling.

**Rationale (operator-approved):**

1. **The investigation produced ground truth.** A live read of `/data/matches/9471/meta.json` in the pm-tennis-api Render Shell at H-016 confirmed the I-016 hypothesis: `event_date=""`, `start_date_iso="2026-04-21T08:00:00Z"`, `start_time="2026-04-21T08:00:00Z"`, `end_date_iso="2026-04-21T23:59:00Z"`. Three of the four date-ish fields are populated; only `event_date` is empty. The Polymarket gateway payload uses `startDate`, not `eventDate`. This is not inferred — it is read.

2. **Surface-area minimization.** Fix A is one line. Fix B is one function rewrite with comprehensive docstring. The total code change is small (under 100 lines including comments), and its blast radius is bounded: discovery.py extracts the same field name in the same format from a different source; slug_selector falls back through a field that has always been populated. No cross-module signature changes, no schema changes to meta.json.

3. **Backward compatibility is real value.** ~116 meta.json files exist on disk at H-016 (up from 74 at H-012 and 38 at H-009). Phase 2 discovery has been writing one file per discovered event since H-007. All of them have empty `event_date`. Without Fix B, every one of those files would never reach probe-eligibility — they would be filtered out forever. The probe could only run against events discovered AFTER the H-016 fix lands, which would needlessly delay the Phase 3 work by however long it takes for fresh eligible matches to come into the discovery window. With Fix B, the existing archive is immediately usable.

4. **The doc-coupling rule applies.** Per Orientation §8, code changes whose behavior is described in project documentation require the documentation to be updated in the same commit. The slug_selector module docstring (top of file, item 1 in the design-constraints list) named `event_date` as a required field. The function docstring of `_passes_date_filter` described "Require event_date to be today or future" with no mention of fallback. Both are updated to reflect the new behavior.

5. **Test fixture honesty.** The pre-fix fixture in `tests/test_discovery.py` line 89 included `"eventDate": event_date`, simulating a gateway response shape that does not exist in reality. This is the same failure mode H-008 surfaced (writing code against names Claude never verified exist), expressed in test-fixture form. The fix corrects the fixture and adds a regression test that asserts `"eventDate" not in raw` before parsing — guarding against any future re-introduction of the same masking bug.

**Subsidiary finding surfaced during investigation (worth recording, not a separate decision):**

Production behavior of `_check_duplicate_players` (discovery.py line 416) has been silently broken since Phase 2 deployed at H-007. The function short-circuits to `return False` on line 424 when `new_meta.event_date` is empty. Because every meta.json from H-007 through H-016 had empty `event_date`, the duplicate-player detection has never fired in production — the `duplicate_player_flag` field has been unconditionally `False` across all 116+ records.

The H-016 fix automatically restores this functionality going forward: meta.json files written from H-016 onward will have correct `event_date`, so `_check_duplicate_players` will work as designed for new events. The historical 116+ files remain affected (their `duplicate_player_flag` stays at the never-checked default) but cannot be retroactively corrected without re-writing immutable on-disk records, which is out of scope.

This is a side-benefit of the fix, not its motivation. No separate code change is needed; flagging here for completeness so the duplicate-player metric can be interpreted correctly during any future analysis (e.g., "duplicate_player_flag is reliable for events with discovered_at >= H-016 timestamp; treat as missing for earlier records").

**Commitment:**

1. `src/capture/discovery.py` line 328 reads `event_date` from `startDate[:10]`. This is the canonical source going forward. Any future change to the date-extraction logic that does not match this pattern requires a new DJ entry.

2. `src/stress_test/slug_selector.py` `_passes_date_filter` falls back to `start_date_iso[:10]` when `event_date` is empty or malformed. This fallback is permanent — even after all historical meta.json files have aged out of relevance (events past their match date), removing the fallback would be a behavior change that requires its own DJ entry. The cost of keeping it is essentially zero (one extra dict lookup); the value is defense-in-depth against any future similar regression.

3. Test fixture in `tests/test_discovery.py` `make_raw_event()` does NOT include an `eventDate` key. Three new tests (`test_i016_event_date_sourced_from_startDate`, `test_i016_event_date_empty_when_startDate_missing`, `test_i016_event_date_ignores_legacy_eventDate_key`) pin the new behavior and explicitly guard against fixture-level masking re-introduction.

4. Six new tests in `tests/test_stress_test_slug_selector.py` (the `test_i016_fallback_*` group) cover the fallback path: empty event_date + future start_date_iso passes; empty event_date + past start_date_iso rejected; both empty rejected; malformed event_date falls through to fallback; populated event_date wins over divergent start_date_iso; non-string fallback rejected gracefully.

5. RAID I-016 is marked Resolved at H-016, with reference to this entry. The RAID Issues table is updated in the H-016 commit bundle.

6. Three plan-text revisions queued in STATE `pending_revisions` are NOT modified by this entry; they remain Phase 2 / cross-section corrections to be cut in a future plan revision under Playbook §12.

**Effect on other decisions:**

- **D-016 commitment 2** (research-first discipline): satisfied. The fix was driven by a live read of the actual gateway payload, not by inference from documentation. Every claim about the gateway shape in this entry traces to the operator-pasted output of `cat /data/matches/9471/meta.json` at H-016.
- **D-016 commitment 1** (Phase 2 attempt 2 begins from c63f7c1d-equivalent state): unchanged. This entry modifies one line of Phase 2 code under explicit operator authorization, which is the supported escape hatch. The c63f7c1d baseline remains the reference point for the Phase 3 attempt 2 work package.
- **D-027 commitment 1** (probe-slug supplied via CLI `--slug` argument): unchanged. This fix makes the slug-selection path more reliable but does not change the transport mechanism.
- **D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026**: unchanged.

**What this entry does not decide:**

- It does not authorize a backfill of historical meta.json files. The 116+ existing files remain as written; the fallback in slug_selector handles their consumption.
- It does not modify the `start_time` field's behavior in discovery.py (the dataclass docstring on line 160 says "HH:MM or empty" but the actual gateway returns a full ISO timestamp; `start_time` is currently a duplicate of `start_date_iso` in production). This is a separate schema-doc-vs-reality drift surfaced incidentally during H-016 investigation; it does not affect probe selection or any downstream consumer in current scope. Logged for a future minor cleanup, not for this commit.
- It does not change any commitment file (`fees.json`, `breakeven.json`, `signal_thresholds.json`, `data/sackmann/build_log.json`). None are in the path of this fix.

**Evidence trail:**

- Live raw read at H-016 from pm-tennis-api Render Shell:
  - `ls -t /data/matches/ | head -5` → top 5 event_ids: 9471, 9469, 9470, 9466, 9467.
  - `cat /data/matches/9471/meta.json` → revealed `event_date=""`, `start_date_iso="2026-04-21T08:00:00Z"`, `start_time="2026-04-21T08:00:00Z"`, `end_date_iso="2026-04-21T23:59:00Z"`.
- Code reads at H-016:
  - `src/capture/discovery.py` lines 328–331 (extraction code)
  - `src/capture/discovery.py` lines 139–193 (TennisEventMeta dataclass)
  - `src/capture/discovery.py` lines 416–435 (_check_duplicate_players, surfaced subsidiary finding)
  - `src/stress_test/slug_selector.py` lines 142–156 (_passes_date_filter pre-fix)
  - `tests/test_discovery.py` line 89 (fixture with false eventDate key)
- Test runs against pinned deps in clean venv (polymarket-us==0.1.2, pytest==8.3.4, Python 3.12.13):
  - Baseline (unmodified main branch at commit 274cd09): 38/38 stress-test tests pass; 47/49 discovery tests pass with 2 pre-existing failures in `TestVerifySportSlug` unrelated to I-016.
  - Post-fix: 79/79 tests pass in the scope of H-016 changes (15 in TestParseEvent including 3 new I-016 regression tests; 4 in TestCheckDuplicatePlayers; 25 in slug_selector including 6 new I-016 fallback tests; 19 in probe_cli unchanged; 20 in list_candidates from earlier H-016 work). The 2 pre-existing TestVerifySportSlug failures are unaffected by this fix and remain out of scope.

**Subsidiary finding to surface for separate disposition:**

Two pre-existing test failures in `TestVerifySportSlug` (`test_network_failure_raises_system_exit`, `test_empty_sports_list_raises_system_exit`) exist on the baseline `main` branch at H-016 open and persist through the H-016 fix. Both expect `SystemExit` but the production code raises `RuntimeError`. This is unrelated to I-016 — the affected code path is `verify_sport_slug` startup behavior, not `_parse_event` extraction. Worth a separate RAID entry or DJ entry at next session, but explicitly out of scope for D-028.

---

