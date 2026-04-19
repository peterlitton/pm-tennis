# PM-Tennis Session Handoff — H-012

**Session type:** Phase 3 attempt 2 — POD resolution + §6 survey execution, no code
**Handoff ID:** H-012
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** All four H-010 PODs resolved across H-011 + H-012. POD-H010-§12 ruled (D-024) = SDK. POD-H010-Q5′ ruled (D-025) = hybrid probe-first. POD-H010-§6-survey ruled and executed (D-026) = authorized and run in-session; N baseline = 74. Research document bumped v3 → v4 (additive §13). STATE v9 → v10. Zero PODs remain blocking the code turn. No tripwires fired. No out-of-protocol events.

---

## 1. What this session accomplished

H-012 opened from the H-011 handoff into the pre-loaded three-POD queue (Q5′, §12, §6-survey) plus the standing code turn. Per the H-011 addendum's pacing guidance and session-open cut-point discipline, the operator chose the "land all three rulings + run §6 survey + close" cut rather than stopping earlier or attempting the code turn. The session executed that cut cleanly.

| Item | Status |
|------|--------|
| H-011 handoff accepted | ✅ Complete |
| Session-open self-audit produced per Playbook §1.3 + H-009 fabrication-check standing direction | ✅ Complete |
| Full repo clone per H-011-addendum guidance (avoids URL-by-URL probe) | ✅ Complete (`git clone` into `/home/claude/pm-tennis`) |
| Governance fingerprint spot-check (STATE `governance` vs D-004–D-008) | ✅ All match |
| Repo-integrity spot-check (main.py SHA, H-011 bundle commit, filename-drift fixes, DJ count, RAID count, POD counts) | ✅ All match STATE v9 |
| Joint ruling on POD-H010-§12 + POD-H010-Q5′ | ✅ Operator ruled (§12)=(a) SDK, (Q5′)=(c′) hybrid probe-first |
| D-024 (POD-H010-§12 resolution) journaled | ✅ Prepended to DecisionJournal |
| D-025 (POD-H010-Q5′ resolution) journaled | ✅ Prepended to DecisionJournal |
| POD-H010-§6-survey authorized | ✅ Operator ruled (a): authorize + read discovery.py first |
| `discovery.py` re-read to verify on-disk `meta.json` schema before drafting commands | ✅ Confirmed `TennisEventMeta` dataclass shape; caught a v3 research-doc path error ("/data/events/" → actual `/data/matches/{event_id}/meta.json`) |
| §6 survey script drafted, reviewed, and executed by operator via Render shell | ✅ Executed 2026-04-19T16:22:29Z; single consolidated bash script, read-only |
| §6 survey findings captured | ✅ `meta.json` files on disk = 74; slug distribution uniform (1/event); N baseline = 74; probe-slug default = event 9392 |
| D-026 (POD-H010-§6-survey resolution + findings) journaled | ✅ Prepended to DecisionJournal |
| Research doc v3 → v4 (additive §13) | ✅ v4 scope ruled by Claude under operator-delegated authority ("Claude decides"); additive §13 added, §§1–12 unchanged |
| STATE v9 → v10 produced | ✅ YAML validates; in this bundle |
| Handoff H-012 produced | ✅ This document |

---

## 2. Decisions made this session

Full text of each entry in DecisionJournal.md. One-line summaries, newest first:

- **D-026** — POD-H010-§6-survey resolved: authorized and executed; meta.json on-disk schema confirmed against `discovery.py`; N baseline = 74 slugs across 74 active events (up from ≈38 at H-009 due to ~36h of continuous Phase 2 discovery); probe-slug default = event 9392, `aec-atp-digsin-meralk-2026-04-21` (traceability anchor only; code turn reselects fresh).
- **D-025** — POD-H010-Q5′ resolved: option (c′) hybrid probe-first. Stress test runs a one-slug gateway-sourced probe as its first runtime action; probe outcome determines main-sweep slug source. Ambiguity is surfaced, not silently resolved.
- **D-024** — POD-H010-§12 resolved: option (a) SDK. Stress-test code uses the `polymarket-us` Python SDK in a new isolated Render service per D-020/Q2=(b); pm-tennis-api `requirements.txt` not modified. Phase 3 full-deliverable pool architecture is re-evaluated post-stress-test.

No out-of-protocol events. OOP counters remain at 0 cumulative, 0 since last gate. No tripwires fired.

---

## 3. Pushback and clarification events this session

No pushbacks declining operator requests. Two clarification moments worth naming for future-Claude visibility:

**3.1 "Most conservative" Q5′ phrasing (mid-session).** Operator's first Q5′ answer was "whichever is the most conservative." Claude surfaced that "conservative" admitted of two readings — (a′) under a minimize-test-risk reading, (c′) under a research-first-maximalism reading — and declined to pick between them, asking the operator to clarify. Operator clarified as (c′). Logged in D-025 "Reasoning" section because the dual-reading ambiguity is a small but generalizable lesson about operator-language precision when competing risk vectors are in play. Not a pushback; a clarification that prevented Claude from silently picking a reading.

**3.2 v4 research-doc scope (delegated back to Claude).** Operator ruled "v4 — signal a new major" for the research-doc version bump. Claude surfaced that a major bump could imply either additive-only or additive-plus-revisions-to-§5/§7, and asked the operator to scope. Operator responded "Claude decides." Claude ruled additive-only and logged the reasoning in-session before writing the doc. Reasoning preserved here for audit:

- Scope discipline: H-010 and H-011 both named queue-overload as a pattern to avoid; the session already had D-024/D-025 logged, the §6 survey run, and D-026 + STATE + Handoff still to land.
- §5's ≈38 estimate is not wrong — it's labeled as-of-H-009 and the v4 §13 cross-references the updated N=74 explicitly. Drift through revision would be worse than additive accumulation.
- v4 as additive-only still resolves three formerly-open v3 questions (schema-on-disk, actual N, probe-slug selection) — the version bump is defensible without §5/§7 edits.
- Asymmetric cost: adding §5/§7 revisions later is cheap; quiet drift of operator-accepted v3 text is hard to catch.

Both are consistent with the H-011 addendum's pattern of making the smaller, safer cut and letting the operator expand scope later if desired.

---

## 4. The §6 survey — script and execution

Per operator direction: "Combine into one script, single output paste." Script reproduced here verbatim for audit; see D-026 for findings:

```bash
echo "=============================================="
echo "PM-TENNIS §6 META.JSON SURVEY — H-012"
echo "Run date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "=============================================="
echo ""

echo "--- SECTION 1: Directory exists and meta.json count ---"
if [ -d /data/matches ]; then
  echo "Event directories (first 20):"
  ls /data/matches/ 2>/dev/null | head -20
  echo ""
  echo "Total meta.json files on disk:"
  find /data/matches -name meta.json -type f 2>/dev/null | wc -l
else
  echo "ERROR: /data/matches does not exist — schema assumption wrong, stop here"
fi
echo ""

echo "--- SECTION 2: One sample meta.json (first 80 lines) ---"
SAMPLE=$(find /data/matches -name meta.json -type f 2>/dev/null | head -1)
if [ -n "$SAMPLE" ]; then
  echo "FILE: $SAMPLE"
  head -80 "$SAMPLE"
else
  echo "No meta.json found — SECTION 1 probably failed"
fi
echo ""

echo "--- SECTION 3: Total market slug count across all events ---"
find /data/matches -name meta.json -type f 2>/dev/null -exec python3 -c "
import sys, json
try:
    d = json.load(open(sys.argv[1]))
    print(len(d.get('moneyline_markets', [])))
except Exception as e:
    print(f'ERROR:{sys.argv[1]}:{e}', file=sys.stderr)
    print(0)
" {} \; 2>/dev/null | awk '{s+=$1} END {print "Total slugs:", s, "  (Events processed:", NR, ")"}'
echo ""

echo "--- SECTION 4: Distribution of moneyline markets per event ---"
echo "Format: COUNT OF EVENTS | MONEYLINE MARKETS PER EVENT"
find /data/matches -name meta.json -type f 2>/dev/null -exec python3 -c "
import sys, json
try:
    d = json.load(open(sys.argv[1]))
    print(len(d.get('moneyline_markets', [])))
except Exception:
    pass
" {} \; 2>/dev/null | sort | uniq -c
echo ""

echo "--- SECTION 5: Per-event status flags + sample slugs (first 40) ---"
find /data/matches -name meta.json -type f 2>/dev/null -exec python3 -c "
import sys, json
try:
    d = json.load(open(sys.argv[1]))
    eid = d.get('event_id', '?')[:12]
    active = d.get('active_at_discovery', False)
    ended = d.get('ended_at_discovery', False)
    live = d.get('live_at_discovery', False)
    discovered = d.get('discovered_at', '')[:19]
    slugs = [m.get('market_slug', '?') for m in d.get('moneyline_markets', [])]
    slug_preview = slugs[0][:50] if slugs else '<no slugs>'
    print(f'{eid:12}  active={active!s:5}  ended={ended!s:5}  live={live!s:5}  disc={discovered}  slug0={slug_preview}')
except Exception as e:
    print(f'ERROR reading {sys.argv[1]}: {e}')
" {} \; 2>/dev/null | head -40
echo ""

echo "=============================================="
echo "END OF §6 SURVEY"
echo "=============================================="
```

Script executed on `pm-tennis-api` Render shell at 2026-04-19T16:22:29Z. Output pasted back in-session. Key numeric findings: 74 `meta.json` files on disk; total market slug count = 74; distribution 74×1 (uniform); first 40 status rows all `active=True ended=False live=False`; discovery timestamps ranging from 2026-04-19T01:47:35Z (earliest on disk) to 2026-04-19T14:04:52Z (most recent). Sample `meta.json` structure matched `TennisEventMeta` dataclass in `src/capture/discovery.py` lines 139–193 exactly.

**Schema-verification catch before execution:** Before running the script, Claude re-read `src/capture/discovery.py` (at operator direction) and discovered that the v3 research-doc text casually referenced "/data/events/" as the meta.json location. The actual path per `_meta_path()` (discovery.py line 356) is `/data/matches/{event_id}/meta.json`; `/data/events/` is the raw-poll-snapshot JSONL directory. Commands were drafted against the verified path, not the v3 prose. Survey executed cleanly on the correct path. Recorded in D-026 as a subsidiary finding.

---

## 4a. Self-audit findings and resolutions

Session-open self-audit (Playbook §1.3 step 4 + H-009 fabrication-check standing direction) produced no discrepancies. Spot-checks:

- **Handoff ID match:** received H-011, STATE `sessions.next_handoff_id` = H-012 → receiving H-011 at H-012 open is correct. ✅
- **`main.py` SHA:** `ceeb5f290f7f7b2da7ce96131f2431fa2acdcfdecba1e91c8d3a04f6eab5a473`, 2,989 bytes, 87 lines. Matches STATE v9 exactly. ✅
- **H-011 bundle landed:** commit `374e2e6` (2026-04-19 11:00:20 -0500) touches DecisionJournal.md (+40 lines for D-023), STATE.md (v8→v9), Handoff_H-011.md (new). Matches H-011's "files modified" claim. ✅
- **Filename-drift fixes landed:** both renames from H-011 are in git log as `3c63e46` and `3ee4150`. ✅
- **DecisionJournal count:** 23 entries before this session — consistent with H-011's D-023 addition. ✅
- **RAID count walk (not grep-shortcut, per H-011 self-correction lesson):** 15 issues total (I-001 through I-015), 2 resolved (I-001 H-005, I-013 H-009), 13 open. Matches STATE `issues_open: 13`. ✅
- **POD state:** three PODs open per STATE — POD-H010-Q5′, -§12, -§6-survey. POD-H010-Q4 present under `resolved_operator_decisions_current_session` per H-011 convention. ✅
- **Governance fingerprint:** all seven STATE `governance` fields match their corresponding DecisionJournal authorities (D-004, D-005, D-006, D-007, D-008, D-016). ✅
- **Fabrication-failure-mode check:** grep for `POLYMARKET|api_key|secret_key` across `src/` and `main.py` returns zero references to Polymarket credentials anywhere in repo code. The four existing `os.environ` calls are all Phase 2 config (sport slug, poll interval, data root, environment label). Consistent with STATE's claim that zero Phase 3 code exists on main. Preventive rather than corrective at session open. ✅
- **`src/capture/` clean post-revert:** only `__init__.py` and `discovery.py` present; no stray Phase 3 attempt 1 files. ✅

No discrepancies found. The H-011 bundle is clean and STATE v9 is internally consistent with repo state.

---

## 5. Tripwire events this session

Zero tripwires fired. No OOP invocations. Session ran entirely within protocol.

Two moments exercised the research-first discipline (R-010) in preventive mode without firing a tripwire:

- The Q5′ "most conservative" clarification (§3.1) — declining to pick a reading when operator language is genuinely ambiguous is the same discipline Tripwire 1 enforces for external documentation.
- The §6-survey schema-verification (§4 and D-026 subsidiary finding) — drafting commands against `discovery.py`-verified on-disk schema rather than research-doc prose caught a real path error before execution. This is the H-011-addendum "check second sources" lesson applied to in-session work.

Neither event rose to tripwire level; both are noted for future-Claude awareness of what the discipline looks like operating.

---

## 6. Files created / modified this session

| File | Action | Notes |
|------|--------|-------|
| `DecisionJournal.md` | Modified | D-024, D-025, D-026 prepended above D-023 per newest-at-top convention. Total entries 23 → 26. |
| `STATE.md` | Modified | Bumped v9 → v10. YAML validated via `yaml.safe_load`. See §7 STATE diff below. |
| `docs/clob_asset_cap_stress_test_research.md` | Modified | Bumped v3 → v4. Header: title, author line, version history, status. Additive §13 appended. §§1–12 unchanged from v3. 441 → 523 lines. |
| `Handoff_H-012.md` | Created | This document. |

**No modifications to:**
- `main.py` — still at SHA `ceeb5f290f7f7b2da7ce96131f2431fa2acdcfdecba1e91c8d3a04f6eab5a473`, 2,989 bytes, 87 lines.
- `src/capture/discovery.py` — unchanged (still carrying v4.1-candidate-3 comment patch queued in STATE `pending_revisions`). Re-read this session for schema verification; no edits.
- `RAID.md` — no issues added, resolved, or edited.
- `PreCommitmentRegister.md` — not touched.
- Any commitment file (`fees.json`, `breakeven.json`, `data/sackmann/build_log.json`). `signal_thresholds.json` still does not exist.
- `PM-Tennis_Build_Plan_v4.docx` — plan-text patches remain queued in STATE `pending_revisions`, not applied this session.
- Any test file.
- Any other `src/` file.
- `Handoff_H-010.md`, `Handoff_H-011.md` — previous handoffs, preserved as-is.

**Operator's commit action at session close:** upload DecisionJournal.md, STATE.md (v10), docs/clob_asset_cap_stress_test_research.md (v4), and Handoff_H-012.md. These four files are in this session's bundle.

---

## 7. STATE diff summary (v9 → v10)

Key fields that changed:

- `project.state_document.current_version`: 9 → 10
- `project.state_document.last_updated_by_session`: H-011 → H-012
- `phase.current_work_package`: rewritten to reflect all four H-010 PODs resolved, code turn blocked only on code-turn-research tasks (not PODs)
- `sessions.last_handoff_id`: H-011 → H-012
- `sessions.next_handoff_id`: H-012 → H-013
- `sessions.sessions_count`: 11 → 12
- `discovery.meta_json_files_written`: 38 → 74 (with inline comment tying to the §6 survey at 2026-04-19T16:22:29Z and to `_write_meta` immutability)
- `discovery.current_event_count`: new field, 74
- `discovery.current_slug_count`: new field, 74 (the N baseline for stress-test sweeps)
- `discovery.participant_type_confirmed`: updated to name H-012 re-confirmation
- `discovery.sportradar_game_id_at_discovery`: updated to note H-012 survey did not re-check this specifically
- `open_items.pending_operator_decisions`: drained from 3 entries to empty list (`[]`). All four H-010 PODs now resolved.
- `open_items.resolved_operator_decisions_current_session`: rewritten from 1 entry (H-011's Q4) to 4 entries (three H-012 resolutions + H-011's Q4 preserved with a note pending operator ruling on the prune-previous convention; see §9 self-report)
- `open_items.phase_3_attempt_2_notes`: +6 entries (four H-012 notes on rulings + survey + v4 + path-correction + code-turn blockers update); existing H-011 Ed25519 note kept and extended with D-024 commitment-4 scoping
- `architecture_notes`: +3 new entries (meta.json path correction, N=74 baseline with growth trajectory, probe-slug default); 3 existing entries updated to reflect H-012 resolutions (Q5′, §12, and Ed25519 scoped through SDK per D-024)
- `scaffolding_files.STATE_md`: current_version 9→10; committed_to_repo pending; committed_session H-012
- `scaffolding_files.DecisionJournal_md`: committed_to_repo pending (D-024, D-025, D-026 added); committed_session H-012
- `scaffolding_files.RAID_md`: committed_to_repo still true (no H-011 or H-012 changes)
- `scaffolding_files.clob_asset_cap_stress_test_research_md`: current_version 3→4; committed_to_repo pending; committed_session H-012; note extended with v4 description
- `scaffolding_files.Handoff_H011_md`: committed_to_repo pending → true (landed at commit 374e2e6)
- `scaffolding_files.Handoff_H012_md`: new entry, this document
- Prose commentary: "Where the project is right now" refreshed to reflect all-PODs-resolved state and consolidate the code-turn inheritance; "What changed in H-011" replaced with "What changed in H-012"; "H-012 starting conditions" replaced with "H-013 starting conditions"; "Validation posture going forward" extended with H-012 evidence

---

## 8. Open questions requiring operator input

**Zero pending operator decisions blocking the code turn.** `pending_operator_decisions` is empty in STATE v10.

Code-turn research tasks remain (per D-023, D-024 commitment 4). These are not PODs — they are research-in-session tasks the code turn runs alongside its own work:
- Byte-level Ed25519 signing operation: scoped through the SDK per D-024 commitment 4(a). If the SDK owns signing internally, this collapses to "trust the SDK." If any signing surface is exposed to user code, that surface is cited at code-turn time.
- Timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication`: runs regardless of SDK use to verify the "30 seconds of server time" language aligns with the millisecond unit Polymarket's usage instructions specified (D-023 subsidiary finding 1).

Minor governance-convention question surfaced for future ruling, not urgent:
- **`resolved_operator_decisions_current_session` pruning policy.** H-011 convention was to show only current-session resolutions there. At H-012 I preserved the H-011 Q4 resolution alongside the three H-012 ones with an explicit note rather than pruning silently. If the convention should be strict "current session only," next session can prune Q4 on the H-012→H-013 STATE bump; if the intent is "cumulative across recent sessions," the current H-012 STATE is correct. Flagging for operator awareness; default to operator's preference.

Carried forward from prior sessions, not specific to H-012:
- Object storage provider for nightly backup — Phase 4 decision
- Pilot-then-freeze protocol content — Phase 7 decision (D-011)
- Three plan-text revisions queued in STATE `pending_revisions` (v4.1-candidate, v4.1-candidate-2, v4.1-candidate-3) — cut at next plan revision under Playbook §12

---

## 9. Claude self-report

Per Playbook §2.

**Session-open behavior:** Clean. Read the H-011 handoff in full (including §9 self-report and the H-011 addendum on "checking second sources"). Cloned the full repo in one shot per H-011-addendum guidance — avoided URL-by-URL probing and produced the session-open self-audit from verified repo state. All nine spot-checks in the self-audit passed. Fabrication-failure-mode check was preventive (no Phase 3 code yet, so grep returned clean — but the check establishes the discipline for the code turn to come).

**Ruling-language explicit-resolution beat:** When the operator ruled on Q5′ and §12 with short phrasing ("recommendation approved"; "(c′) hybrid probe-first"), Claude surfaced the Playbook §11.3 step 3 explicit-resolution convention and asked whether the operator wanted to restate in the canonical "Resolve POD-N: [ruling]" form. Operator provided the canonical language. Logged here because the alternative — silently treating the short phrasing as explicit resolution — would have worked operationally but would have left the DecisionJournal-entry language slightly indirect. Surfacing the beat rather than skipping it is the §11.5.2 discipline.

**"Most conservative" Q5′ clarification:** Operator's first Q5′ answer admitted two readings under different risk-vectors; Claude declined to pick and asked the operator to clarify. Operator clarified as (c′). This is exactly the research-first discipline pointed at operator-language ambiguity rather than at external documentation — the H-010 pattern of "v2 under-qualified" applied in reverse (don't over-resolve operator language either). D-025 "Reasoning" records the dual-reading explicitly so future-Claude can see the disambiguation.

**Scoping decision under operator-delegated authority (v4 scope):** Operator's response to "v4 scope?" was "Claude decides." Claude ruled additive-only and logged the full reasoning in-session *before* writing the doc. This is a notable session event because it's the only substantive in-session decision where Claude exercised delegated authority. The four-bullet reasoning (scope discipline, non-wrongness of v3 §5, defensibility of v4 bump without revisions, asymmetric cost of drift) is preserved in §3.2 above for audit. The decision was conservative — it preserves operator-accepted v3 text intact rather than editing it under a delegated mandate. If you disagree with the ruling, it's easily reversed in a future session by adding the §5/§7 revisions.

**§6 survey execution:** Script was drafted against `discovery.py`-verified schema, not research-doc §6 prose. Caught the "/data/events/" → "/data/matches/" path error before command execution. This is the H-011-addendum "check second sources" lesson — research-doc §6 was the first source, `discovery.py` was the second source, and they disagreed on the path. Second source won. Execution was clean (single operator paste of script, single paste-back of output). Findings were read carefully before being written into D-026 and v4 §13. No fabrication; no drift from observed data.

**Meta.json file-count growth observation:** The jump from 38 to 74 between H-009 and H-012 surfaced naturally during survey reading. Claude's first reaction was to verify it was explainable (Phase 2 running immutably for ~36 hours) rather than to treat it as a discrepancy. This is the correct posture — the survey's job is to report current state, not to reconcile with stale counters. STATE v10 preserves the historical `first_poll_events_discovered: 38` as provenance and adds new `current_event_count` and `current_slug_count` fields for the live count. Neither the old nor the new value is "wrong"; they're measurements at different times.

**Research doc v4 scope question surfaced proactively:** The operator ruled "v4 — signal a new major" without an explicit scope. Rather than silently pick, Claude asked the additive-vs-full scope question — the third sub-question of this session. The operator delegated the decision. The §3.2 reasoning is recorded so the delegation's exercise is visible.

**`resolved_operator_decisions_current_session` preservation:** I preserved the H-011 Q4 entry rather than pruning it to the strict "current-session-only" reading of the H-011 convention, and flagged the preservation explicitly in the YAML comment and in §8 of this handoff. The alternative (silent prune) would have been procedurally cleaner but would have erased visible trail of the full four-POD resolution arc at a moment when that arc is worth seeing at a glance. This is a convention question worth a cheap ruling in a future session; not urgent.

**Pacing decision:** H-010 resolved nothing but produced a four-version research document. H-011 resolved one POD (Q4) and stopped. H-012 resolved three PODs + ran the survey + produced v4 and took the session toward close. This is a faster cut than H-011, but the work is materially less dense per ruling (three operator-recommended resolutions approved quickly, one research-doc version bump, one survey execution). The session is substantive but not overloaded. The code turn stays deferred to H-013 — which is the correct place for it per the H-011 addendum's scope-discipline framing ("don't try to win the whole queue in one session").

**Session duration:** Moderate-to-long. Long opening (retrieval gap handling via full repo clone; self-audit from verified repo state; reading all governing documents). Substantive middle (three rulings, research doc v4, §6 survey execution, one in-session ruling under delegated authority). Long close (D-024, D-025, D-026, STATE v10 with extensive updates, this handoff). Operator attention cost was meaningful but produced four concrete artifacts (three DJ entries + research doc v4) and one empirical dataset (survey output).

**Out-of-protocol events:** 0 this session. Cumulative: 0.

**Tripwires fired:** 0. Two preventive-mode exercises of research-first discipline (§3.1 and §4 schema-verification) without firing.

---

## 10. Next-action statement

**The next session's (H-013) first actions are:**

1. Accept handoff H-012.
2. Perform the session-open self-audit per Playbook §1.3 and D-007. Self-audit must include the fabrication-failure-mode check per H-009 standing direction. At H-013 open, the check becomes *active* rather than *preventive*: if stress-test code has been drafted (in-session or between sessions), every SDK symbol, every endpoint string, every module path, every class name, every function signature must trace to (a) the Polymarket US Python SDK README fetched at H-010, (b) fresh SDK-source fetches at H-013 code-turn time, (c) operator-provided material, or (d) an existing committed file. The check additionally verifies `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` are referenced by name only via `os.environ`, never by value.
3. **Code turn — the stress test.** Per D-024 (SDK), D-025 (probe-first), D-026 (N=74 baseline, probe-slug default for traceability), research-doc v4 §13.5 (consolidated code-turn scoping), and D-020 / Q2=(b) (isolated Render service). The deliverable:
   - A new isolated Render service, separate from `pm-tennis-api`. Stress-test code lives here; gets torn down after.
   - Reads credentials via `os.environ["POLYMARKET_US_API_KEY_ID"]` and `os.environ["POLYMARKET_US_API_SECRET_KEY"]`.
   - First runtime action after authentication: one-slug probe (D-025 commitment 1) — fresh slug selection by reading `/data/matches/*/meta.json` at runtime (not the H-012 default).
   - Probe outcome recorded; main-sweep slug source determined by outcome.
   - Main sweeps: §7 Q3=(c) — per-subscription count (1/2/5/10 subs × 100 slugs, placeholders above real N=74) × concurrent-connection count (1/2/4). Pure connection-level test per §7 Q1=(a); no disk writes of received content.
   - Code-turn research tasks (alongside code): byte-level Ed25519 signing scoped through SDK per D-024 commitment 4(a); timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication` per D-024 commitment 4(b).
   - Per-deliverable acceptance bar per D-020: unit tests + operator code review + stress test runs to completion against actual gateway with actual asset count. The "actual asset count" is now concretely 74 per D-026.
4. Stress-test results addendum appended to research doc as §14 (or equivalent). Probe outcome + main-sweep data + any code-turn-research findings.

**Phase 3 attempt 2 starting state at H-013 session open:**

- Repo on `main` with H-012 bundle landed (STATE v10, DecisionJournal with D-024/D-025/D-026, research-doc v4, Handoff_H-012).
- Service at `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`. Discovery loop healthy. 74+ active tennis events on disk at H-012 close (still growing).
- Zero Phase 3 code on `main`.
- Polymarket US credentials at Render env vars `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` (D-023). Values never in repo, never in chat transcript.
- Research document `docs/clob_asset_cap_stress_test_research.md` at v4, operator-accepted.
- **Zero pending operator decisions in STATE `open_items.pending_operator_decisions`.**
- Three plan-text pending revisions in STATE: v4.1-candidate (I-014), v4.1-candidate-2 (I-015), v4.1-candidate-3 (discovery.py comment). Not changed this session.
- Research-first discipline in force per D-016 and D-019.
- SECRETS_POLICY §A.6 guard operating — H-012 did not exercise it (no credential-value handling), but the D-024 commitments preserve the discipline for the code turn.

---

*End of handoff H-012.*
