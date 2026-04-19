# PM-Tennis Project — STATE

This file is the cross-session state snapshot for the PM-Tennis project. It is read by Claude at the start of every session as part of the handoff-acceptance ritual, and updated by Claude at the end of every session as part of the handoff-production ritual. The operator commits the updated file to the repository after each session.

Per decision D-004 through D-008 and the governance model established in H-001 and H-002, STATE.md is the single source of truth for: current phase, commitment-file integrity, observation-window status, open items requiring attention, and the project's governance fingerprint (trigger phrases, carrier method, access model, audit setting).

**This file has two layers:**

1. **Structured data** (YAML front matter below). This is the machine-parseable source of truth. Any field referenced by tooling (GitHub Actions checks, healthcheck endpoints, admin-UI displays) reads from the YAML, not the prose. Field values are authoritative when they disagree with anything in the prose section.

2. **Prose commentary** (everything after the YAML). This is the human-readable narrative layer. It explains the current state, expands on what the fields mean in context, and records any observations that don't fit in a structured field. The prose is not source-of-truth — if you find a conflict between prose and YAML, the YAML wins and the prose is wrong and must be corrected.

**Update discipline:**
- Every session **must** begin with Claude reading this file.
- Every session **must** end with Claude producing an updated version of this file, even if the only changes are "last session ID" and "date."
- An unchanged STATE between two consecutive sessions is itself a red flag and should be called out in the session handoff if it occurs.
- STATE updates travel with the session handoff as a bundle; the operator commits both together.
- STATE is never edited by the operator directly. If the operator believes STATE is wrong, the procedure is to surface the issue to Claude at the next session-open, who then updates STATE as part of that session's closing ritual.

---

```yaml
# ============================================================================
# STRUCTURED DATA — authoritative source of truth
# ============================================================================

schema_version: 1  # bump if the schema of this YAML block changes

# ---- Project identity ----
project:
  name: PM-Tennis
  description: "Polymarket US in-play tennis moneyline instrument and trading system"
  plan_document:
    current_version: v4
    current_version_date: 2026-04-18
    location: "PM-Tennis_Build_Plan_v4.docx in repo root"
    pending_revisions:
      - id: v4.1-candidate
        sections: ["Section 5.6"]
        summary: "Remove data/baseline/ from Render disk storage layout — baseline files live in repo, not on disk. Tracked as RAID I-014."
      - id: v4.1-candidate-2
        sections: ["Section 5.4", "Section 11.3"]
        summary: "The '150-asset pool cap' is not a documented Polymarket US limit. Polymarket US Markets WebSocket documents one numeric cap: 100 slugs per subscription. Concurrent-connection and per-account caps are undocumented. §5.4 and §11.3 text to be revised to reflect the actual Polymarket US structure. Tracked as RAID I-015, established by H-010 research in docs/clob_asset_cap_stress_test_research.md v3 §4.4 and §11 point 1."
      - id: v4.1-candidate-3
        sections: ["discovery.py line 37 / line 120 code comments"]
        summary: "Line 37 and line 120 code comments in src/capture/discovery.py state that side.identifier is the 'asset/token ID for CLOB subscription.' Polymarket US Markets WebSocket's documented subscription unit is market_slug, not side.identifier. Comments are misleading against actual Polymarket US behavior. Cosmetic comment-level patch; no code-behavior change. Surfaced by H-010 research in docs/clob_asset_cap_stress_test_research.md v3 §11 point 3. Apply under Playbook §12 when next plan revision is cut, alongside I-014 and v4.1-candidate-2."
  state_document:
    current_version: 13
    last_updated: 2026-04-19
    last_updated_by_session: H-015

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-probe-blocked-on-calendar
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). H-015 attempted live-probe execution per RB-002 §5 two-shell workflow but probe was blocked: `slug_selector.list_candidates()` returned empty in the pm-tennis-api Shell. Diagnostic A confirmed Phase 2 discovery is healthy (116 event dirs on disk, up from 74 at H-012 — monotonic growth as expected). Diagnostic B revealed root cause: 10 most-recent meta.json files (event_ids 9440–9449) all have `event_date=\"\"` despite event titles encoding the date as text (e.g., 'Elmer Moeller vs. Hugo Gaston 2026-04-20'). Operator confirmed the surfaced events are future games and that no eligible matches exist in the next ~24h. Two findings: (a) calendar-empty for ~24h means probe genuinely had nothing to run against today; (b) `event_date` extraction in src/capture/discovery.py line 328 is reading a wrong-named gateway field — filed as RAID I-016 (severity 6). H-016 picks up: (1) investigate I-016 in src/capture/discovery.py and the gateway raw event payload to identify the correct date key (Phase-2-touching change requires explicit operator authorization separate from Phase 3 work package); (2) live probe execution per RB-002 §5 (either after I-016 is fixed, or via the title-date workaround documented in I-016 if the Phase-2 fix is not authorized in time, or by retry once calendar populates if neither blocks); (3) §14 addendum (probe outcome); (4) main sweeps deferred again to H-017."
  work_package_started_session: null  # starts next session
  last_gate_passed:
    name: "Phase 2 exit gate"
    phase: phase-2
    date: 2026-04-19
    handoff_with_verdict: H-007
  next_gate_expected:
    name: "Phase 3 exit gate"
    phase: phase-3
    triggers:
      - "48-hour unattended capture run with no data gaps"
      - "CLOB pool correctly handles stale connections (15-min recycle, 90-sec liveness)"
      - "Sports WS retirement handler correctly marks retired matches"
      - "Handicap capture logic produces 5-tick median and correctly flags stale handicaps"
      - "CLOB asset-cap stress test complete (deferred from Phase 1)"
      - "First-server identification recorded on first live Sports WS message"
  phase_3_attempt_counter: 2  # attempt 1 failed at H-008; see D-016

# ---- Session accounting ----
sessions:
  last_handoff_id: H-015
  next_handoff_id: H-016
  sessions_count: 15
  most_recent_session_date: 2026-04-19
  out_of_protocol_events_cumulative: 0
  out_of_protocol_events_since_last_gate: 0
  out_of_protocol_trigger_phrase: "out-of-protocol"
  missed_handoffs:
    - session: H-008
      reason: "Session went sideways attempting to correct fabricated Sports WS URL; operator deleted chat transcript"
      remediation: "H-009 reconstructed D-013 through D-015 from H-007 handoff source; D-016 records the failure; D-017 retroactively journals H-006 plan-revision decision. RAID I-013 resolved same session."

# ---- Repository and deployment state ----
repo:
  host: GitHub
  url: "https://github.com/peterlitton/pm-tennis"
  visibility: public
  default_branch: main
  exists: true

deployment:
  backend:
    provider_category: "managed PaaS with deploy-from-git"
    provider_choice: Render
    service_name: "pm-tennis-api"
    service_url: "https://pm-tennis-api.onrender.com"
    region: "Oregon (US West)"
    instance_type: "Starter"
    python_version_deployed: "3.12.13"
    python_version_target: "3.12"
    python_version_pinned: true
    persistent_disk_mount: "/data"
    persistent_disk_size_gb: 10
    persistent_disk_used_mb_at_h009_close: 35  # approximate, from df -h /data
    auto_deploy: true
    auto_deploy_branch: main
    health_check_path: "/healthcheck"
    build_command: "pip install -r requirements.txt"
    start_command: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    exists: true
    status: live
    live_deploy_commit: 17f44eb1  # revert commit, 2026-04-19 03:17:11Z
    live_deploy_verified_session: H-009
    notes: >
      Discovery loop runs as asyncio background task inside this service (D-014).
      Reverted to Phase 2 state at H-009 per D-016 Option A1.
      Running main.py at commit c63f7c1d-equivalent content (version "0.1.0-phase2").
      38 active tennis events discovered; discovery loop polling every 60s.
  frontend:
    provider: Netlify
    site_url: null
    custom_domain: null
    exists: false
  stress_test:
    provider_category: "managed PaaS with deploy-from-git"
    provider_choice: Render
    service_name: "pm-tennis-stress-test"
    service_url: "https://pm-tennis-stress-test.onrender.com"
    region: "Oregon (US West)"
    instance_type: "Starter"
    python_version_deployed: "3.12"  # inherits Render's Python default for Python runtime; SDK pin is 0.1.2
    persistent_disk_attached: false  # D-027 — stress-test service intentionally has no disk
    auto_deploy: false  # explicit: Manual per RB-002 Step 1
    health_check_path: null  # disabled; service is a CLI that exits, not a long-running server
    build_command: "pip install -r src/stress_test/requirements.txt"
    start_command: "python -m src.stress_test.probe"  # runs self-check only; probe mode is manual invocation via Shell
    exists: true
    status: live  # self-check green; service restart-loops after each self-check exit, which is expected
    live_deploy_verified_session: H-014
    env_vars_set:
      - "POLYMARKET_US_API_KEY_ID"  # set via Render dashboard, value never in repo/chat (SECRETS_POLICY §A.6)
      - "POLYMARKET_US_API_SECRET_KEY"  # same
    notes: >
      Isolated stress-test service per D-024 commitment 1 and D-020/Q2=(b).
      pm-tennis-api's requirements.txt is NOT modified by this service's
      lifecycle. Provisioned at H-014 per rewritten RB-002 (D-027-correct).
      Probe execution deferred to H-015 per Option 2 cut at H-014 open.
      Teardown: delete service in Render dashboard after main-sweep work
      completes; code in src/stress_test/ remains in repo for audit.
  backup_storage:
    provider_category: "object storage with web-UI management"
    provider_choice: null
    exists: false

# ---- Commitment files ----
commitment_files:
  signal_thresholds_json:
    path: data/signal_thresholds.json
    exists: false
    sha256: null
    last_modified_session: null
  fees_json:
    path: fees.json
    exists: true
    sha256: null  # to be computed at Phase 7
    last_modified_session: H-005
  breakeven_json:
    path: breakeven.json
    exists: true
    sha256: null  # to be computed at Phase 7
    last_modified_session: H-005
  sackmann_build_log:
    path: data/sackmann/build_log.json
    exists: true
    sha256: null  # to be computed at Phase 7
    last_modified_session: H-005

# ---- Observation-active soft lock ----
soft_lock:
  observation_active_file_path: OBSERVATION_ACTIVE
  present: false
  created_session: null
  removed_session: null

# ---- Observation window state ----
observation_window:
  status: not-started
  pilot:
    status: not-started
    started_date: null
    ended_date: null
    pilot_protocol_document_exists: false
    pilot_protocol_document_path: null
    pilot_protocol_accepted_by_operator: false
  window:
    started_date: null
    target_calendar_cap_date: null
    target_signal_count: 250
    signals_captured: 0
    signals_qualifying: 0
    days_elapsed: 0
    projected_close_date: null
    closure_reason: null

# ---- Discovery state (Phase 2 output) ----
discovery:
  status: running
  sport_slug: tennis
  sport_slug_verified: true
  leagues_confirmed: ["wta", "atp"]
  first_poll_date: 2026-04-19
  first_poll_events_discovered: 38  # historical: first-poll count at H-007; preserved for provenance
  meta_json_files_written: 74  # H-012 §6 survey at 2026-04-19T16:22:29Z; up from 38 at H-009 due to ~36h of continuous discovery; _write_meta never overwrites per discovery.py line 371
  current_event_count: 74  # H-012 §6 survey snapshot; all 74 active_at_discovery=True ended_at_discovery=False at survey time
  current_slug_count: 74  # N baseline for stress-test sweeps per research-doc v4 §13.2; one moneyline per event, distribution uniform
  delta_stream_path: "/data/events/discovery_delta.jsonl"
  daily_raw_archive_path: "/data/events/2026-04-19.jsonl"
  daily_raw_archive_size_mb: 33.7  # at H-009 close, growing ~12 MB/hour
  daily_raw_archive_growth_estimate_mb_per_day: 290  # uncompressed
  poll_interval_seconds: 60
  gateway_base: "https://gateway.polymarket.us"
  participant_type_confirmed: "PARTICIPANT_TYPE_TEAM or PARTICIPANT_TYPE_PLAYER (extractor handles both; observed events at H-009 and H-012 use TEAM)"
  participant_type_prior_claim_corrected: true  # H-007 claimed PLAYER exclusively; corrected at H-009 V2 and re-confirmed at H-012 §6 survey
  sportradar_game_id_at_discovery: "empty until match approaches live start (observed: 0/38 at H-009; H-012 survey did not re-check this specifically)"

# ---- Open items requiring attention ----
open_items:
  tripwire_events_currently_open: 0
  python_version_pin_needed: false  # resolved H-005
  decision_journal_entries_needed: []  # all resolved at H-009 and H-010
  raid_entries_by_severity:
    sev_8: 3   # R-008, R-009, I-012
    sev_7: 9   # R-010, I-003, I-004, I-005, I-006, I-007, I-008 (and 2 others)
    sev_6: 4   # I-009, I-010, I-011, I-016 (new H-015)
    sev_5: 0
    sev_4_and_below: 3  # I-002 (severity 2), I-014 (severity 3), I-015 (severity 3)
    issues_open: 14   # 16 total issues; I-001 resolved H-005 and I-013 resolved H-009; I-016 added H-015
    assumptions_unvalidated: 6  # A-001, A-002, A-003, A-004, A-006, A-008
  pending_operator_decisions: []  # H-015 had no PODs reach DJ-entry threshold; all rulings were on method/convention. No operator decisions blocking H-016.
  resolved_operator_decisions_current_session:
    # Pruned to current-session (H-015) entries only per the H-014-settled
    # stricter-reading convention. H-014 entries are preserved in
    # Handoff_H-014 §2/§3 and STATE v12's prose; this field reflects only
    # the current session's in-session rulings.
    - id: H-015-cut-point
      resolved_session: H-015
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Probe + §14 addendum this session; main-sweeps deferred to H-016. Consistent with H-014-Claude's default offer in the addendum notes; consistent with H-010/H-011/H-012/H-013/H-014 pacing discipline. Cut held even after probe blocked — session did not extend silently into investigation work; surfaced finding as RAID I-016 and closed cleanly."
    - id: H-015-section-14-stays-reserved
      resolved_session: H-015
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "§14 of research doc remains reserved (option a) rather than receiving a placeholder for the H-015 attempt (option b). Rationale: §14 should mean 'probe outcome from a probe that ran.' H-015 attempt + calendar block + I-016 finding documented in Handoff_H-015 §3 and STATE v13 (correct location for session-specific events per the prose-vs-YAML discipline). H-016 writes §14 when an actual probe runs."
    - id: H-015-diagnostic-execution
      resolved_session: H-015
      resolved_by_decision: operator ruling mid-session (not a DJ entry)
      resolution_summary: "Operator authorized Diagnostic A (count + list event dirs) and Diagnostic B (sample meta.json metadata) in pm-tennis-api Shell to confirm the system-vs-calendar attribution for the empty list_candidates() result. Diagnostic A: 116 dirs, healthy growth from H-012's 74. Diagnostic B (after heredoc workaround for bracketed-paste): 10 events, all active=True ended=False live=False, all event_date='', titles include 2026-04-20 dates. Surfaced I-016 finding."
    - id: H-015-RAID-vs-DJ-classification-of-I-016
      resolved_session: H-015
      resolved_by_decision: operator ruling at session close (not a DJ entry)
      resolution_summary: "I-016 (empty event_date in meta.json) goes to RAID; not a DJ entry. Operator ruling: the finding cannot be validated for some time (depends on Phase-2 raw payload inspection), so RAID is the right home; DJ stays at 27 entries with no H-015 additions. Consistent with the pruning convention's spirit — DJ for project-shape commitments, RAID for risks/issues, STATE for session-method rulings."
    - id: H-015-helper-snippet-friction-surface
      resolved_session: H-015
      resolved_by_decision: in-session note (not a DJ entry; not requiring operator ruling)
      resolution_summary: "First operator use of the H-014 sub-ruling pasted-snippet helper convention (RB-002 §5.1) produced two failed pastes due to bracketed-paste markers in the Render Shell environment. Diagnostic B also failed for same reason; heredoc workaround succeeded. Stronger evidence than H-014 had for converting to a committed src/stress_test/list_candidates.py helper file. Surfaced for H-016 explicit consideration; not flipped in H-015 to honor the cut."
  phase_3_attempt_2_notes:
    - "Research-first discipline in force per D-016 commitment 2 and R-010 — no fabrication of URLs or module symbols. H-013 exercised it three times in preventive mode without firing a tripwire."
    - "H-010: research document produced at docs/clob_asset_cap_stress_test_research.md, three versions this session (v1, v2, v2.1, v3). v3 accepted."
    - "H-011: POD-H010-Q4 resolved via D-023. Polymarket US API credentials stored at Render env vars POLYMARKET_US_API_KEY_ID and POLYMARKET_US_API_SECRET_KEY on pm-tennis-api. Values never entered chat. Polymarket usage instructions confirmed three-header auth scheme and disambiguated timestamp unit as milliseconds (unix_ms)."
    - "H-012: POD-H010-§12 resolved via D-024 — SDK (option a). H-012: POD-H010-Q5' resolved via D-025 — hybrid probe-first (option c'). H-012: POD-H010-§6-survey resolved via D-026 — executed in-session; N baseline = 74 slugs across 74 events."
    - "H-012: Research doc bumped v3 → v4 (additive §13). Meta.json path correction surfaced: actual path is /data/matches/{event_id}/meta.json, not /data/events/ as some v3 prose read."
    - "H-012 close: zero PODs remain blocking the code turn. Code turn (H-013) blocked only on code-turn-research tasks (byte-level Ed25519 via SDK per D-023/D-024 commitment 4a; timestamp-unit cross-check per D-023/D-024 commitment 4b). Both research-in-session tasks, not operator decisions."
    - "H-013: Code-turn-research task 1 (Ed25519 signing surface) RESOLVED — fully internal to SDK; backed by pynacl. No user-code signing. Citations: SDK README + docs.polymarket.us/api-reference/authentication."
    - "H-013: Code-turn-research task 2 (timestamp unit) RESOLVED — milliseconds, unambiguous. Authentication page now has explicit 'Current time in milliseconds' in the header table row."
    - "H-013: Code-turn-research task 3 (SDK transitive deps; H-012 addendum quiet-uncertainty) RESOLVED — 12 packages total: httpx/pynacl/websockets direct, standard transitives; wheels available for Linux/x86_64 + CPython 3.12; no compile required on Render. Verified via pip install --dry-run in clean venv."
    - "H-013: D-027 ruled — probe-slug transport via operator-supplied --slug CLI arg (Option D). Supersedes D-025 commitment 1 because Render disks are strictly single-service per authoritative docs: 'A persistent disk is accessible by only a single service instance ... You can't access a service's disk from any other service' (render.com/docs/disks fetched H-013). D-025 commitments 2/3/4 unaffected."
    - "H-013: Probe scaffolding landed at src/stress_test/ (__init__.py, probe.py, slug_selector.py, requirements.txt, README.md). 38 unit tests across tests/test_stress_test_slug_selector.py (19) and tests/test_stress_test_probe_cli.py (19). All passing. Zero SDK mocking per H-012 addendum guidance — network-touching path is exercised at H-014 live smoke."
    - "H-013: Known-stale artifacts committed this session under Option X cut: src/stress_test/README.md (slug-selection sections) and runbooks/Runbook_RB-002_Stress_Test_Service.md (Steps 3 + 5). H-014 first-task: update both before deployment."
    - "H-013: Render stress-test service NOT stood up this session. Originally scoped into H-013 after mid-session operator ruling; deferred under Option X after D-027 was ruled and artifact-update work was still pending. H-014 provisions the service."
    - "H-013 close: zero PODs. Code-turn-research tasks resolved. Two known-stale artifacts flagged. Deployment + main sweeps remain for H-014."
    - "H-014: STATE v11 produced at H-013 close was omitted from the H-013 commit bundle (operator error). H-014-Claude surfaced the discrepancy at session open before any substantive work; operator uploaded v11 file out-of-band; H-014 proceeded from the correct v11 baseline without silent reconciliation."
    - "H-014: Two known-stale artifacts from H-013's Option X cut rewritten per D-027 — src/stress_test/README.md and runbooks/Runbook_RB-002_Stress_Test_Service.md. README: new 'Slug source' section, Running-on-Render rewritten for two-shell workflow, exit-code-11 description corrected, Tests section updated to 38/19. RB-002: full rewrite; Step 3 now 'Skip — no disk attach'; Step 5 rewritten as two-shell workflow (pm-tennis-api Shell lists candidates via pasted snippet → pm-tennis-stress-test Shell runs probe --slug --event-id); fallback Options A/B/C from stale Step 3 removed (inert under D-027)."
    - "H-014: Research-doc §15 additive written — three H-013 code-turn-research resolutions fully cited with evidence trail (Ed25519 fully internal; timestamp ms-unambiguous; SDK deps 12 wheel-only packages); D-027 supersession + Render disks single-service authoritative citation; probe-scaffolding inventory; stale-artifact corrections named; H-015 forward look. §14 reserved for H-015 probe-outcome addendum (intentional out-of-order). v4 remains current version; §15-additive-vs-v5-bump ruling chose additive per H-012 precedent."
    - "H-014: pm-tennis-stress-test Render service provisioned per D-027-correct RB-002. Build succeeded (16 packages wheel-only, no compile). Self-check green: [ok] polymarket_us 0.1.2 import, [ok] SDK surfaces importable, [ok] both credential env vars set, [info] 0 probe candidates (expected under D-027 — confirms isolation). Exit-after-selfcheck restart-loop behavior as expected; operator did not switch to the sleep-after-selfcheck alternative. Service URL: https://pm-tennis-stress-test.onrender.com. Auto-Deploy: Off. No persistent disk attached."
    - "H-014: Retrospective fabrication check at session open against H-013 code — 38/38 tests pass under pinned deps in fresh venv; every SDK symbol in probe.py resolves against installed polymarket-us==0.1.2; env var names match D-023; slug_selector schema matches TennisEventMeta dataclass. No fabrication. Live self-check on Render (noted above) provides additional retrospective confirmation — the code that worked locally boots and imports cleanly on the target platform too."
    - "H-014: One sub-ruling under delegated authority — pm-tennis-api-Shell candidate-listing helper is a pasted Python snippet (inlined in RB-002 §5.1), not a committed list_candidates.py file. Avoids a new file requiring tests/docs/maintenance; pasted form is transparent. Reversible at H-015 if operator prefers."
    - "H-014 close: zero PODs. Service provisioned + healthy. Rewritten artifacts verified. §15 additive in place. H-015 opens with live-probe execution + main-sweeps code as the core work."
    - "H-015 open: full reading completed (Handoff_H-014, STATE v12, Orientation, Playbook §1-§7, DecisionJournal D-016 through D-027, RAID Issues + Decisions, SECRETS_POLICY §A.5-A.7, RB-002, README, probe.py full 765 lines including classification logic, research-doc §7 Q1-Q5' and §15 full additive). Per-operator-direction full reading at session open. Retrospective fabrication check: 38/38 tests pass in fresh venv against pinned deps (polymarket-us==0.1.2 + pytest==8.3.4). H-014 commit-bundle integrity confirmed: 5-file bundle landed (STATE v11+v12, Handoff_H-014, README rewrite, RB-002 rewrite, research-doc §15 additive); no v11/v12-style discrepancies."
    - "H-015 cut at session open: probe + §14 addendum this session; main-sweeps deferred to H-016. Consistent with H-014-Claude default offer in addendum notes."
    - "H-015 probe attempt blocked on calendar. Step 1 (slug selection in pm-tennis-api Shell): operator pasted helper snippet from RB-002 §5.1 — first attempt and a retry both corrupted by bracketed-paste markers (^[[200~ prefix attached to PYTHONPATH= token, bash interpreted as filename, errored). Simpler invocation without PYTHONPATH= prefix worked (operator was already at /opt/render/project/src). list_candidates() returned empty result."
    - "H-015 Diagnostic A (operator-authorized, pm-tennis-api Shell): `ls /data/matches/ | wc -l` = 116 directories, up from 74 at H-012. Discovery is healthy and growing monotonically as expected (_write_meta is immutable per discovery.py)."
    - "H-015 Diagnostic B (operator-authorized, pm-tennis-api Shell): heredoc workaround used after first attempt failed bracketed-paste markers same way. 10 most-recent meta.json files (event_ids 9440-9449) inspected. All 10 show active=True ended=False live=False. Titles include 2026-04-20 dates (e.g., 'Elmer Moeller vs. Hugo Gaston 2026-04-20'). All 10 show event_date='' (empty string). Operator confirmed these are future games and that no eligible matches exist in the next ~24h."
    - "H-015 finding: empty event_date is a real Phase-2 data-extraction issue, separate from the calendar block. Root cause likely at src/capture/discovery.py line 328: `event_date=str(event.get('eventDate') or '').strip()` — Polymarket gateway responses likely don't have a top-level `eventDate` key. slug_selector._passes_date_filter (lines 142-156) correctly rejects empty event_date as defensive behavior. Filed as RAID I-016 (severity 6). Per operator ruling at H-015 close: RAID, not DJ — finding cannot be validated for some time."
    - "H-015: Helper-snippet bracketed-paste friction — second observed instance this session (helper snippet + Diagnostic B both failed; heredoc workaround succeeded for Diagnostic B). Stronger evidence than H-014 for converting the H-014 sub-ruling pasted-snippet helper to a committed src/stress_test/list_candidates.py file. Surfaced for H-016 explicit consideration; not flipped in H-015 to honor the cut."
    - "H-015 close: zero PODs. Probe blocked on calendar + I-016. RAID I-016 filed (sev 6). DJ unchanged (27 entries). H-016 opens with: (1) investigate I-016 in src/capture/discovery.py and gateway raw event payload — Phase-2-touching change requires explicit operator authorization; (2) probe retry (after I-016 fix, or via title-date workaround per I-016, or once calendar populates); (3) §14 addendum (probe outcome); (4) main sweeps deferred to H-017."

# ---- Runbooks inventory ----
runbooks:
  RB-001:
    title: "GitHub + Render Setup"
    path: "runbooks/Runbook_GitHub_Render_Setup.md"
    produced_session: H-004
    status: complete
  RB-002:
    title: "Stand up the pm-tennis-stress-test Render service"
    path: "runbooks/Runbook_RB-002_Stress_Test_Service.md"
    produced_session: H-013
    rewritten_session: H-014  # per D-027 supersession — Step 3 "skip no disk" + Step 5 two-shell workflow
    status: "active — D-027-correct as of H-014; service provisioned and self-check verified"

# ---- Governance fingerprint ----
governance:
  out_of_protocol_trigger_phrase: "out-of-protocol"
  out_of_protocol_overrides_observation_lock: false
  handoff_carrier_method: "markdown files"
  repo_access_model: "public GitHub repository"
  repo_secrets_policy: "no secrets in repo ever; secrets live in platform env vars"
  session_open_self_audit_enabled: true
  section_1_5_forward_references_accepted: true
  single_authoring_channel: "Claude authors; operator reviews and commits"
  state_file_authoring: "Claude reads and updates; operator commits"
  state_file_update_cadence: "every session, mandatory"
  research_first_discipline_for_external_apis: true  # new H-009, per D-016 commitment 2 and R-010

# ---- Architectural notes (cross-session reference) ----
architecture_notes:
  - "Discovery loop runs as asyncio background task inside pm-tennis-api (D-014)"
  - "Render persistent disk is per-service — no cross-service disk sharing possible"
  - "Polymarket US public gateway: gateway.polymarket.us (no auth for reads)"
  - "Polymarket US authenticated API: api.polymarket.us (REST + WebSocket; used by the Polymarket US Python SDK; confirmed Ed25519 auth per H-010 research)"
  - "Sport slug tennis confirmed with leagues [wta, atp]"
  - "Participant type may be TEAM or PLAYER; extractor handles both (corrected H-009)"
  - "sportradar_game_id populates at Polymarket's discretion, typically close to match start; empty at pure pre-match discovery"
  - "Daily raw-poll archive (/data/events/YYYY-MM-DD.jsonl) grows ~290 MB/day uncompressed; Phase 4 adds compression"
  - "Phase 3 attempt 1 (H-008) failed via fabricated Sports WS URL + fabricated DiscoveryConfig symbol; reverted at H-009 per D-016"
  - "Phase 3 attempt 2 begins from c63f7c1d-equivalent repo state"
  - "Polymarket US Markets WebSocket = wss://api.polymarket.us/v1/ws/markets (H-010, cited in docs/clob_asset_cap_stress_test_research.md v3/v4 §4.1). Auth: three headers X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature; signature over timestamp+'GET'+path; Ed25519; 30-sec clock window."
  - "Polymarket US Markets WebSocket subscription unit: market slug. Cap: 100 slugs per subscription (H-010, v3/v4 §4.4). Concurrent-connection and rate limits: not documented on docs.polymarket.us (H-010, v3/v4 §4.5 — the empirical gap that justifies the stress test)."
  - "Polymarket US wire format for Markets WebSocket: camelCase with enum-string subscription types (e.g., requestId, subscriptionType='SUBSCRIPTION_TYPE_MARKET_DATA', marketSlugs). Resolved H-010 via SDK README response-side evidence; Overview page's snake_case prose is stale."
  - "api.polymarket.us shares a single slug namespace across REST (markets.retrieve_by_slug, markets.book) and WebSocket (subscribe slug list). Gateway-to-api slug identity resolved at H-012 via D-025 ruling: hybrid probe-first (option c') — one gateway-sourced slug probed against /v1/ws/markets at code-turn time resolves the bridge question definitively before main stress-test sweeps."
  - "Polymarket US Python SDK exists at github.com/Polymarket/polymarket-us-python (package polymarket-us, Python 3.10+). SDK is committed for the stress test per H-012 D-024 ruling (option a); Phase 3 full-deliverable pool architecture is re-evaluated post-stress-test."
  - "Polymarket US Markets WebSocket timestamp header (X-PM-Timestamp) is in milliseconds per Polymarket-supplied usage instructions (H-011, D-023). Prior research-doc §4.2 cited '30 seconds of server time' language from the authentication page but did not fully pin the unit. Millisecond unit is canonical for code; authentication page will be re-fetched at code-turn time to cross-check per D-023/D-024 commitment 4b."
  - "Polymarket US API credentials stored at Render env vars POLYMARKET_US_API_KEY_ID and POLYMARKET_US_API_SECRET_KEY on pm-tennis-api service (H-011, D-023). Values never in repo, never in chat transcript. Code reads by name via os.environ. SDK authentication flow consumes these per D-024 commitment 3."
  - "Meta.json per-match files live at /data/matches/{event_id}/meta.json on the Render persistent disk. /data/events/ is the raw-poll-snapshot JSONL directory (discovery.py _events_snapshot_dir()), not the meta directory. Confirmed by H-012 §6 survey and discovery.py _meta_path() (src/capture/discovery.py line 356). Research-doc v3 used casual '/data/events/' references; v4 §13.2 and D-026 note the correction."
  - "Stress-test N baseline = 74 market slugs across 74 active tennis events (H-012 §6 survey at 2026-04-19T16:22:29Z; research-doc v4 §13.2). One moneyline per event, uniform distribution. Growth trajectory: 38 at H-009 → 74 at H-012 (~36h of continuous immutable Phase 2 discovery). Slam-week projection from v3 §5: ≈128 at peak (above the 100-slug per-subscription cap only marginally, requires 2 subscriptions)."
  - "Stress-test probe-slug default at H-012: event 9392, aec-atp-digsin-meralk-2026-04-21 (research-doc v4 §13.4). Traceability anchor only; code turn reselects fresh from /data/matches/*/meta.json because survey snapshot ages by hours-to-days before code-turn execution."
  - "Render persistent disks are STRICTLY single-service — confirmed H-013 via authoritative fetch of render.com/docs/disks: 'A persistent disk is accessible by only a single service instance ... You can't access a service's disk from any other service.' Read-only shared mounts are not supported. This rules out the D-025 commitment 1 shared-disk pattern."
  - "D-027 (H-013) supersedes D-025 commitment 1: probe slug is supplied to the probe via --slug CLI argument (operator picks from pm-tennis-api Shell listing /data/matches/). D-025 commitments 2/3/4 unaffected. Preserves D-024 commitment 1 (pm-tennis-api/requirements.txt untouched) and D-020/Q2=(b) isolation."
  - "SDK Ed25519 signing operation is FULLY INTERNAL to the polymarket-us SDK (confirmed H-013 via SDK README + docs.polymarket.us/api-reference/authentication). No user-facing signing surface. D-024 commitment 4(a) collapses to 'trust-the-SDK.' PyNaCl is the SDK's internal Ed25519 backend."
  - "Timestamp unit for X-PM-Timestamp is MILLISECONDS, unambiguous (confirmed H-013 via authentication-page header table row: 'X-PM-Timestamp: Current time in milliseconds'). D-023 subsidiary finding 1 is now fully verified against the authoritative source."
  - "polymarket-us==0.1.2 transitive dependency tree = 12 packages: httpx/pynacl/websockets direct, plus httpcore/anyio/idna/certifi/h11/typing_extensions/cffi/pycparser. Wheels available for Linux/x86_64 + CPython 3.12; no compile required on Render. Verified H-013 via pip install --dry-run --report in clean venv."
  - "pm-tennis-stress-test Render service is live as of H-014. Isolated per D-020/Q2=(b) and D-024 commitment 1. URL: https://pm-tennis-stress-test.onrender.com (no HTTP surface served — the URL exists because Render assigns one to every web service). Auto-Deploy: Off. No persistent disk. Start command runs self-check only; probe execution is manual via the two-shell workflow in RB-002 §5. Self-check verified at provisioning time — polymarket_us 0.1.2 imports cleanly, both credential env vars set, 0 probe candidates under D-027 (expected). Service restart-loops after each self-check exit; cosmetically acceptable, alternative sleep-loop start command available in RB-002 Step 4 if restart churn becomes noise during main sweeps."

# ---- Cost tracking ----
costs:
  expected_monthly_usd:
    baseline: 35-50
    under_memory_pressure: 110
  actual_monthly_usd_estimate: 8.25
  cost_components:
    - component: "Render backend (Starter instance)"
      expected_usd_range: "7"
      status: active
    - component: "Render persistent disk (10 GB)"
      expected_usd_range: "1.25"
      status: active
    - component: "Netlify frontend"
      expected_usd_range: "0 to low single digits"
      status: not-yet-active
    - component: "GitHub repo"
      expected_usd_range: "0"
      status: active
    - component: "Object storage for nightly backup"
      expected_usd_range: "~5"
      status: not-yet-active

# ---- Scaffolding files inventory ----
scaffolding_files:
  STATE_md:
    status: accepted
    current_version: 13
    committed_to_repo: pending  # v13 produced this session
    committed_session: H-015
    note: "v13 reflects H-015 probe attempt + block, RAID I-016 finding filing, and pruning of resolved_operator_decisions to H-015 entries only per the H-014-settled convention."
  Orientation_md:
    status: accepted
    committed_to_repo: true
  Playbook_md:
    status: accepted
    committed_to_repo: true
  SECRETS_POLICY_md:
    status: accepted
    committed_to_repo: true
  DecisionJournal_md:
    status: accepted
    committed_to_repo: true  # D-027 + D-025 footer landed in H-013 commit b208144; no changes this session
    committed_session: H-013
    pending_entries: []
  RAID_md:
    status: accepted
    committed_to_repo: pending  # I-016 added this session; sev_6 count and issues_open count both bumped
    committed_session: H-015
    note: "H-015 added I-016 (empty event_date in meta.json — sev 6) per operator ruling. Header 'Last updated' line bumped to H-015 close 2026-04-19."
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  clob_asset_cap_stress_test_research_md:
    status: accepted
    path: "docs/clob_asset_cap_stress_test_research.md"
    current_version: 4
    committed_to_repo: true  # §15 additive committed in H-014 commit af5885e
    committed_session: H-014
    renamed_session: H-011
    note: "v4 remains the current version. §13 added at H-012 (H-012 rulings + survey); §15 additive added at H-014 (H-013 code-turn-research resolutions + D-027 supersession + scaffolding note + stale-artifact-corrected note + H-015 forward look). §14 is reserved for the H-016 probe-outcome addendum (originally reserved for H-015 but probe blocked on calendar + I-016). v5 bump was considered at H-014 and rejected in favor of §15 additive, following H-012 precedent. No changes at H-015."
  Handoff_H010_md:
    status: accepted
    path: "Handoff_H-010.md"
    committed_to_repo: true
    committed_session: H-010
    renamed_session: H-011
  Handoff_H011_md:
    status: accepted
    path: "Handoff_H-011.md"
    committed_to_repo: true
    committed_session: H-011
  Handoff_H012_md:
    status: accepted
    path: "Handoff_H-012.md"
    committed_to_repo: true  # landed in the H-012 commit
    committed_session: H-012
  Handoff_H013_md:
    status: accepted
    path: "Handoff_H-013.md"
    committed_to_repo: true  # landed in H-013 commit b208144
    committed_session: H-013
  Handoff_H014_md:
    status: accepted
    path: "Handoff_H-014.md"
    committed_to_repo: true  # landed in H-014 commit 087557d
    committed_session: H-014
  Handoff_H015_md:
    status: accepted
    path: "Handoff_H-015.md"
    committed_to_repo: pending  # produced this session
    committed_session: H-015
  data_dictionary_md:
    status: not-started
    note: "Phase 3 deliverable"
  window_close_analysis_notebook:
    status: not-started
    note: "Phase 7 or post-Phase-7 deliverable"

# ---- Phase 3 attempt 2 source files (stress-test package, H-013) ----
phase_3_attempt_2_files:
  src_stress_test_init_py:
    path: "src/stress_test/__init__.py"
    status: committed
    committed_session: H-013
    note: "Package init with version string 0.1.0-stress-test-h013. No changes at H-014."
  src_stress_test_slug_selector_py:
    path: "src/stress_test/slug_selector.py"
    status: committed
    committed_session: H-013
    tests: "tests/test_stress_test_slug_selector.py — 19 tests passing"
    note: "Reads /data/matches/*/meta.json and returns fresh ProbeCandidate. Schema verified against TennisEventMeta in src/capture/discovery.py lines 139-193. Under D-027 this module is a library used by local-dev and by the pm-tennis-api-Shell helper snippet in RB-002 §5.1; it is NOT called in the production probe code path on the isolated stress-test service. No changes at H-014."
  src_stress_test_probe_py:
    path: "src/stress_test/probe.py"
    status: committed
    committed_session: H-013
    tests: "tests/test_stress_test_probe_cli.py — 19 tests passing"
    note: "Stress-test entry point. Self-check mode (default, no network) + probe mode (--probe --slug=<SLUG> [--event-id=<EID>]). D-027-compliant: --slug CLI arg is the production slug source. Module header carries explicit SDK-README citations [A]-[D]. No changes at H-014; live-verified via self-check on Render."
  src_stress_test_requirements_txt:
    path: "src/stress_test/requirements.txt"
    status: committed
    committed_session: H-013
    note: "Isolated deps for pm-tennis-stress-test service. polymarket-us==0.1.2 + pytest==8.3.4. pm-tennis-api's /requirements.txt is NOT modified per D-024 commitment 1. Verified at H-014 via Render build: installs cleanly (16 packages, all wheels, no compile)."
  src_stress_test_README_md:
    path: "src/stress_test/README.md"
    status: committed
    committed_session: H-014
    note: "Rewritten at H-014 per D-027: new 'Slug source' section; What-this-service-does updated; Authoritative-inheritance slug-schema bullet scoped to library use only; Running-locally updated with --slug example; Running-on-Render rewritten for two-shell workflow referencing RB-002; exit-code-11 description updated; Tests section updated to 38 tests (both files) and §15 addendum reference; status line reflects H-014 D-027 pass. Landed in H-014 commit 626a548."
  tests_test_stress_test_slug_selector_py:
    path: "tests/test_stress_test_slug_selector.py"
    status: committed
    committed_session: H-013
    note: "19 tests; pure on-disk fixtures; no mocking. All passing at H-013; re-verified passing at H-014 open in fresh venv against pinned deps."
  tests_test_stress_test_probe_cli_py:
    path: "tests/test_stress_test_probe_cli.py"
    status: committed
    committed_session: H-013
    note: "19 tests; argparse + run_probe early-return paths + main() dispatch + ProbeOutcome + classification mapping + ProbeConfig clamping. Zero SDK mocking per H-012 addendum. All passing at H-013; re-verified passing at H-014 open in fresh venv against pinned deps."

# ---- Phase 2 source files (current state on main) ----
phase_2_files:
  src_capture_discovery_py:
    path: "src/capture/discovery.py"
    status: committed
    committed_session: H-007
    tests: "tests/test_discovery.py — 46 tests passing"
  src_init_py:
    path: "src/__init__.py"
    status: committed
    committed_session: H-007
  src_capture_init_py:
    path: "src/capture/__init__.py"
    status: committed
    committed_session: H-007
  main_py:
    path: "main.py"
    status: committed
    committed_session: H-009  # restored to c63f7c1d content at H-009 revert
    size_bytes: 2989
    line_count: 87
    version_string: "0.1.0-phase2"
    sha256: ceeb5f290f7f7b2da7ce96131f2431fa2acdcfdecba1e91c8d3a04f6eab5a473
    notes: "Phase 2 discovery loop inside FastAPI process. Restored at H-009 per D-016 Option A1."

# ---- End of structured data ----
```

---

## Prose commentary

### Where the project is right now

Phase 2 remains complete and operational. The service at `pm-tennis-api.onrender.com` continues to run the reverted Phase 2 `main.py` (SHA `ceeb5f29…`, 2,989 bytes, 87 lines). Discovery loop polls `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. No Phase 2 code was modified this session. Discovery archive continues to grow monotonically — H-015 Diagnostic A confirmed 116 event directories on disk, up from 74 at H-012 (~24h growth). `_write_meta` immutability holds.

**Phase 3 attempt 2 stress-test service remains live as of H-014.** `pm-tennis-stress-test` at `https://pm-tennis-stress-test.onrender.com` continues to self-check green per H-014's verified provisioning. No code changes this session; no SDK calls made; no live probe executed.

**H-015 attempted live probe execution per RB-002 §5 two-shell workflow but probe was blocked.** Step 1 (slug selection in pm-tennis-api Shell) returned an empty `list_candidates()` result. Two diagnostics were operator-authorized: Diagnostic A (`ls /data/matches/`) confirmed the system is healthy with 116 event directories, monotonic growth from H-012's 74. Diagnostic B (sample of 10 most-recent meta.json files, after a heredoc workaround for bracketed-paste markers) revealed two co-occurring conditions: (a) operator-confirmed: no eligible matches in the next ~24h regardless (the surfaced events are future games dated 2026-04-20+); and (b) all 10 meta.json files have empty `event_date` fields despite the date being encoded in the title text. The probe was blocked today by (a); but (b) is a separate Phase-2 data-extraction issue that would block a probe retry tomorrow if not investigated, and is filed as RAID I-016.

**RAID I-016 (sev 6) filed at H-015 close.** Likely root cause: `src/capture/discovery.py` line 328 uses `event.get("eventDate")` to extract the date, but Polymarket gateway responses appear to use a different key name. `slug_selector._passes_date_filter` correctly rejects empty `event_date` as defensive behavior — the issue is upstream extraction, not selector logic. H-016's first action is to investigate the gateway raw event payload (a one-time read from `/data/events/2026-04-19.jsonl` or equivalent) and identify the correct key. **Phase 2 code is preserved per D-016**; any actual fix to `discovery.py` is a Phase-2-touching change requiring explicit operator authorization separate from the Phase 3 work package. A workaround for the probe-retry path that bypasses `discovery.py` (parsing the date from event titles in `slug_selector` only) is documented in I-016.

**The H-014 sub-ruling pasted-snippet helper convention surfaced friction in production use.** Two of the three multi-line snippet pastes operator attempted in the pm-tennis-api Render Shell this session were corrupted by bracketed-paste escape markers (`^[[200~ ... ~`), making bash interpret the whole expression as a non-existent filename. The simpler single-line invocation (without `PYTHONPATH=` prefix, since operator was already at the right cwd) and the heredoc-wrapped Diagnostic B both worked. This is meaningful empirical data that the H-014 sub-ruling — chosen at H-014 under delegated authority on the basis that "Shell-pasted form is transparent and self-documenting" — has a real cost in this Shell environment. H-015 did not flip the convention to honor the cut-point ruling. **Strong recommendation surfaced for H-016 explicit consideration:** convert to a committed `src/stress_test/list_candidates.py` helper file invokable as `python -m src.stress_test.list_candidates`, removing the multi-line-paste failure mode entirely.

**D-027 remains active.** D-025 commitment 1 is superseded; commitments 2/3/4 stand. D-024 commitment 1 (pm-tennis-api/requirements.txt untouched) is actively reinforced. D-020/Q2=(b) isolation is preserved.

**What the H-016 session inherits:**

- Repo with the full H-013 + H-014 + H-015 bundle: STATE v13, DJ unchanged at 27 entries (no H-015 additions per operator ruling), Handoff_H-015, RAID with new I-016 entry (sev 6, total open issues 14).
- Live `pm-tennis-stress-test` service with credentials + no disk; self-check verified at H-014 and not regressed at H-015 (no code changes touching the service this session).
- Live `pm-tennis-api` service with 116 event dirs on disk and growing.
- Empty `event_date` finding (I-016) waiting for investigation as H-016 first action.
- Helper-snippet convention flip waiting for H-016 explicit consideration.
- §14 of research doc still reserved for the probe-outcome addendum (now an H-016 deliverable).
- Three plan-text revisions queued in STATE `pending_revisions` (unchanged).
- Zero pending operator decisions.
- Six consecutive sessions (H-010 through H-015) closed without firing a tripwire or invoking OOP.

### What changed in H-015

**Probe attempt blocked, surfaced cleanly.** Two-shell workflow attempted per RB-002 §5; Step 1 (slug selection) returned empty. Operator-confirmed calendar block + I-016 finding. No probe ever executed. No SDK calls made. No `pm-tennis-stress-test` Shell invoked. The H-014-Claude addendum-flagged "highest fabrication-risk surface since H-008" was not exercised this session — saved for H-016.

**RAID I-016 filed.** Empty `event_date` field in meta.json. Sev 6 (material; not critical because the discovery service itself is operational and the bug is in a derived field). Per operator ruling at session close: RAID, not DJ — finding cannot be validated for some time and the right home is the issue log.

**STATE bumped v12 → v13.** Material changes: session counters advanced (sessions_count 14→15, last_handoff_id H-014→H-015, next_handoff_id H-015→H-016); `phase.current` bumped from `phase-3-attempt-2-service-provisioned` to `phase-3-attempt-2-probe-blocked-on-calendar`; `phase.current_work_package` rewritten to reflect H-015 attempt and outcome; `raid_entries_by_severity.sev_6` 3→4 and `issues_open` 13→14; `resolved_operator_decisions_current_session` pruned per H-014 settled convention and replaced with H-015's 5 in-session rulings; `phase_3_attempt_2_notes` +9 entries for H-015; `scaffolding_files`: H-014 entries (Handoff_H-014, README, RB-002, research-doc) flipped pending→true with commit SHAs; STATE v13 + Handoff_H-015 + RAID v15 added as pending. Prose sections refreshed.

**DecisionJournal: no changes this session.** H-015 had no PODs open and none of its in-session rulings reached DJ-entry threshold (all were on method/convention, not project-shape commitments). Counter stays at 27. RAID I-016 went to RAID per operator ruling, not DJ.

**Tripwires: none fired.** Three preventive-mode disciplines exercised without firing: (1) the H-008 fabrication-class danger zone was kept saved for H-016 by honoring the cut-point even after the probe was blocked (no extension into "let me just investigate I-016 a little while we're here"); (2) Diagnostic B was not silently re-attempted after bracketed-paste failure — surfaced the friction and offered the operator a heredoc workaround with explicit reasoning; (3) the I-016 finding was surfaced sharply rather than silently rationalizing the empty-list as "calendar empty, fine, move on" — diagnostic B revealed something the operator could not have known from calendar knowledge alone.

**OOP events: 0 this session.** Counters remain at 0 cumulative, 0 since last gate.

**One sub-ruling under delegated authority (H-015-Claude):** when operator said "for B please present script," I read it as "show the script content for the operator to run via heredoc workaround" rather than "commit a helper file to the repo," and explicitly surfaced the two readings before acting. Operator's subsequent action (running the heredoc) confirmed reading 1 was correct. Documenting because delegated-authority calls are exactly what the H-014 helper-snippet flag was about — surface before acting, even if the smaller cut feels obvious.

### H-016 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with the full H-013 + H-014 + H-015 bundle: STATE v13, DecisionJournal unchanged at 27 entries (last entry D-027), Handoff_H-015, RAID with I-016 newly filed (sev 6, total open 14).
- Discovery service `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`, healthy. Event count 116+ at H-015 close (continues to grow at ~1-2 events/hour during normal hours).
- Stress-test service `pm-tennis-stress-test.onrender.com` live, Auto-Deploy Off, no persistent disk, both credential env vars set, self-check expected to remain green (no code changes this session).
- I-016 (empty event_date) waiting for investigation as the first action.
- The pasted-snippet helper convention from H-014 is still in force per RB-002 §5.1; H-015's empirical friction data is documented for H-016 to consider flipping to a committed file.
- Zero pending operator decisions.
- Three plan-text pending revisions in STATE unchanged (v4.1-candidate, -2, -3).
- Research-first discipline in force per D-016, D-019.
- Pruning convention for `resolved_operator_decisions_current_session`: stricter reading, settled.

### Validation posture going forward

At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode. At H-016 open, the check has three application surfaces:

- **Preventive for I-016 investigation.** Reading `discovery.py` line 328 and a sample raw gateway event payload is a read-only research task — fabrication risk is low because the operator-authorized read returns ground truth. The risk is more in *interpretation*: identifying the "right" key name from gateway payload structure should be cited from the actual payload byte-content, not from memory or from documentation that may not match payload shape. If the proposed key name doesn't trace to the operator-pasted payload, surface that gap rather than guess.

- **Preventive for the probe retry (live network code against real external API).** This is the H-008 risk class that H-015 saved for H-016. Every SDK symbol used must trace to the SDK README or a fresh re-fetch; the H-013 citation block in `probe.py` covers the current symbol set, but if main-sweeps gets pulled forward at H-016, fresh `markets.list()` and multi-subscription semantics work needs a SDK README re-fetch at code-turn time.

- **Retrospective for H-015 artifacts.** STATE v13, Handoff_H-015, RAID I-016. Spot-check that the I-016 description's claims about `discovery.py` line 328 and `slug_selector._passes_date_filter` lines 142-156 actually match the on-disk code (both were verified at H-015 close before filing).

Values of `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` must never enter the chat transcript — they are set via Render dashboard only. H-015 did not exercise the credential path (no probe ran); discipline holds vacuously.

---

*End of STATE.md — current document version: 13. Last updated: H-015.*
