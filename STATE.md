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
    current_version: 12
    last_updated: 2026-04-19
    last_updated_by_session: H-014

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-service-provisioned
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). H-013 landed probe scaffolding (src/stress_test/) + 38 unit tests + three code-turn-research resolutions + D-027 (probe-slug transport supersedes D-025 commitment 1). H-014 landed: (1) stale-artifact corrections per D-027 (src/stress_test/README.md rewrite + runbooks/Runbook_RB-002_Stress_Test_Service.md full rewrite); (2) research-doc §15 additive capturing H-013 code-turn-research resolutions, D-027 supersession + evidence trail, probe scaffolding inventory, stale-artifact-corrected note, and H-015 forward look; (3) pm-tennis-stress-test Render service provisioned per D-027-correct RB-002 — self-check green (polymarket_us 0.1.2 imports OK, both credentials set, 0 probe candidates as expected under D-027). H-015 picks up with: (1) live probe execution per D-025/D-027 two-shell workflow (pm-tennis-api Shell lists candidates → pm-tennis-stress-test Shell runs probe with --slug --event-id → ProbeOutcome JSON pasted back); (2) probe-outcome §14 addendum to research doc; (3) main sweeps (§7 Q3=(c)) — new code module likely src/stress_test/sweeps.py; (4) main-sweeps §16 addendum."
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
  last_handoff_id: H-014
  next_handoff_id: H-015
  sessions_count: 14
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
    sev_6: 3   # I-009, I-010, I-011
    sev_5: 0
    sev_4_and_below: 3  # I-002 (severity 2), I-014 (severity 3), I-015 (severity 3)
    issues_open: 13   # 15 total issues; I-001 resolved H-005 and I-013 resolved H-009
    assumptions_unvalidated: 6  # A-001, A-002, A-003, A-004, A-006, A-008
  pending_operator_decisions: []  # H-013 ruled D-027 in-session; H-014 had no PODs to open. No operator decisions blocking H-015.
  resolved_operator_decisions_current_session:
    # Pruned to current-session (H-014) entries only per the stricter reading
    # of the convention flagged in Handoff_H-012 §8 — confirmed by operator
    # at H-014 open. History is preserved in DJ entries and prior handoffs
    # (H-013 rulings live in Handoff_H-013 §2 and §3); this field's name is
    # load-bearing and the stricter reading keeps it honest.
    - id: H-014-STATE-v11-remediation
      resolved_session: H-014
      resolved_by_decision: in-session remediation (not a DJ entry)
      resolution_summary: "STATE v11 was produced at H-013 close but was omitted from the H-013 commit bundle (operator error). H-014-Claude surfaced the discrepancy at session open rather than silently reconciling; operator uploaded the v11 file out-of-band; H-014 proceeded from the correct v11 baseline."
    - id: H-014-cut-point
      resolved_session: H-014
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Option 2 — rewrite the two known-stale artifacts per D-027, produce research-doc §15 additive, provision the Render service per corrected RB-002. Defer live probe execution + main sweeps code + addendum to H-015. Consistent with H-010/H-011/H-012/H-013 pacing discipline."
    - id: H-014-research-doc-additive-vs-bump
      resolved_session: H-014
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "§15 additive (not v5 bump) — consistent with the H-012 precedent that added §13 to v4 without a version bump. §14 is reserved for the H-015 probe-outcome addendum; §15 is intentionally out-of-order because the probe outcome is its own unit of analysis."
    - id: H-014-helper-snippet-convention
      resolved_session: H-014
      resolved_by_decision: in-session ruling under delegated authority (not a DJ entry)
      resolution_summary: "pm-tennis-api-Shell candidate-listing helper is a pasted one-line Python snippet (inlined in RB-002 §5.1), not a committed src/stress_test/list_candidates.py file. Rationale: avoids a new file requiring tests/docs/maintenance; Shell-pasted form is transparent. Flagged in Handoff_H-013 §10 item 3 as a deferred H-014 choice; Claude applied the smaller cut under delegated authority. Cheap to reverse at H-015 if operator prefers."
    - id: H-014-pruning-convention
      resolved_session: H-014
      resolved_by_decision: operator ruling mid-session (not a DJ entry)
      resolution_summary: "resolved_operator_decisions_current_session: stricter-reading pruning confirmed as the convention. Operator's reasoning: records are preserved elsewhere (DJ entries + committed handoffs). The H-013 call to prune was not a one-off; this is now the settled convention for future sessions."
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
    current_version: 12
    committed_to_repo: pending  # v12 produced this session
    committed_session: H-014
    note: "v11 was produced at H-013 close but omitted from the H-013 commit bundle (operator error); remediated by operator out-of-band at H-014 open (v11 file uploaded; H-014 worked from it as the correct baseline). v12 is the normal-session-close artifact."
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
    committed_to_repo: true  # no changes this session; last modified H-010 when I-015 landed
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  clob_asset_cap_stress_test_research_md:
    status: accepted
    path: "docs/clob_asset_cap_stress_test_research.md"
    current_version: 4
    committed_to_repo: pending  # §15 additive produced this session
    committed_session: H-014
    renamed_session: H-011
    note: "v4 remains the current version. §13 added at H-012 (H-012 rulings + survey); §15 additive added at H-014 (H-013 code-turn-research resolutions + D-027 supersession + scaffolding note + stale-artifact-corrected note + H-015 forward look). §14 is reserved for the H-015 probe-outcome addendum. v5 bump was considered and rejected in favor of §15 additive, following H-012 precedent."
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
    committed_to_repo: pending  # produced this session
    committed_session: H-014
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
    status: pending
    committed_session: H-014
    note: "Rewritten at H-014 per D-027: new 'Slug source' section; What-this-service-does updated; Authoritative-inheritance slug-schema bullet scoped to library use only; Running-locally updated with --slug example; Running-on-Render rewritten for two-shell workflow referencing RB-002; exit-code-11 description updated; Tests section updated to 38 tests (both files) and §15 addendum reference; status line reflects H-014 D-027 pass. No longer pending-stale."
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

Phase 2 remains complete and operational. The service at `pm-tennis-api.onrender.com` continues to run the reverted Phase 2 `main.py` (SHA `ceeb5f29…`, 2,989 bytes, 87 lines). Discovery loop polls `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. No Phase 2 code was modified this session. Discovery archive continues to grow monotonically (`_write_meta` is immutable).

**Phase 3 attempt 2 has a live isolated service as of H-014.** `pm-tennis-stress-test` is provisioned on Render at `https://pm-tennis-stress-test.onrender.com`, Auto-Deploy Off, no persistent disk per D-027. Self-check verified: polymarket_us 0.1.2 imports cleanly, both credential env vars set, 0 probe candidates under D-027 (expected — confirms isolation). The service's start command is the default no-op self-check; the probe runs only on manual invocation via the two-shell workflow in RB-002 §5.

**Stale artifacts from H-013's Option X cut have been corrected.** Both `src/stress_test/README.md` (slug-selection sections, Running-on-Render, exit-code table) and `runbooks/Runbook_RB-002_Stress_Test_Service.md` (Step 3 "Skip — no disk attach," Step 5 two-shell workflow, fallback Options A/B/C removed) were rewritten per D-027 at H-014 open. Research-doc §15 additive captures the H-013 code-turn-research resolutions with full evidence trails, the D-027 supersession, the scaffolding inventory, and the H-014 stale-artifact corrections.

**All three H-013 code-turn-research tasks remain resolved against authoritative sources.** §15.1.1: SDK Ed25519 signing is fully internal (no user-code signing surface). §15.1.2: X-PM-Timestamp is milliseconds, unambiguous. §15.1.3: SDK transitive deps = 12 standard wheel-available packages for Linux/x86_64 + CPython 3.12. See `architecture_notes` YAML block for the citation trail.

**D-027 remains active.** D-025 commitment 1 is superseded; commitments 2/3/4 stand. D-024 commitment 1 (pm-tennis-api/requirements.txt untouched) is actively reinforced by D-027. D-020/Q2=(b) isolation is preserved and now concretely realized in a running service. The research-question intent of D-025 — probe a gateway-sourced slug against the api WebSocket — is preserved; only the slug-to-probe transport changed from shared-disk read to operator-supplied `--slug=SLUG` CLI argument.

**What the H-015 session inherits:**

- Repo with the full H-013 + H-014 bundle: STATE v12, DJ with D-027 and D-025 footer (unchanged at H-014), Handoff_H-014, rewritten README, rewritten RB-002, research-doc v4 with §15 additive.
- Live `pm-tennis-stress-test` service with credentials + no disk, ready for the two-shell probe workflow.
- Zero operator decisions blocking.
- §14 reserved in the research doc for the H-015 probe-outcome addendum.
- Zero net-new code this session (all H-013 code still in force; no new modules added).

### What changed in H-013

DecisionJournal: D-027 prepended (newest-first per convention). D-025's resolution footer updated with "SUPERSEDED IN PART BY D-027" note per DJ conventions line 13. D-025 original text preserved in full.

Research document: unchanged at H-013 (v4 remains accepted). D-027 ruling was captured in the DJ and Handoff_H-013; research-doc §15 additive produced at H-014 (see below).

STATE: bumped v10 → v11. Material changes: session counters advanced; `phase.current` bumped from `phase-3-attempt-2-ready` to `phase-3-attempt-2-probe-scaffolded`; `phase.current_work_package` rewritten to reflect H-013 completion and H-014 pickup; `resolved_operator_decisions_current_session` pruned to H-013 entries only per the stricter reading (Claude-under-delegated-authority ruling at H-013); `phase_3_attempt_2_notes` + several entries covering D-027, code-turn-research resolutions, scaffolding completion, known-stale artifacts; `architecture_notes` +5 entries on Render disks/D-027/SDK signing/timestamp unit/transitive deps; `runbooks` inventory added RB-002 with stale-flag; new `phase_3_attempt_2_files` section tracked the stress-test package and test files.

Code + tests: `src/stress_test/` package created with 5 files; `tests/test_stress_test_slug_selector.py` (19 tests) and `tests/test_stress_test_probe_cli.py` (19 tests) created. All 38 tests passing. Draft runbook RB-002 created but carried two known-stale sections (Steps 3 and 5) flagged for H-014 rewrite.

### What changed in H-014

**STATE v11 remediation at session open.** STATE v11 was produced at H-013 close but was omitted from the H-013 commit bundle (operator error). H-014-Claude surfaced the discrepancy at self-audit time rather than silently reconciling; operator supplied the v11 file out-of-band; H-014 proceeded from the correct v11 baseline without any silent reconciliation.

**Stale-artifact corrections.** Both `src/stress_test/README.md` and `runbooks/Runbook_RB-002_Stress_Test_Service.md` were rewritten per D-027 at H-014 open, before any deployment work. README: "What this service does" revised; new "Slug source — D-027 supersedes D-025 commitment 1" section added; Authoritative-inheritance slug-schema bullet scoped to library use only; Running-locally updated with `--slug` examples; Running-on-Render rewritten to describe the two-shell workflow and reference RB-002; exit-code-11 row revised to reflect D-027 meaning; status line updated. RB-002: full rewrite. Step 3 replaced with "Skip — no disk attach" + rationale. Step 5 rewritten as the two-shell workflow (pm-tennis-api Shell lists candidates via pasted Python snippet → pm-tennis-stress-test Shell runs probe with `--slug` + `--event-id` → operator pastes `ProbeOutcome` JSON back). Step 1 "load-bearing region" language removed. Fallback Options A/B/C from stale Step 3 removed as inert under D-027.

**Research-doc §15 additive.** Added to v4 without a version bump, per the H-012 precedent for §13. Content: §15.1 H-013 code-turn-research resolutions (three sub-items, each with authoritative citations); §15.2 D-027 supersession with the render.com/docs/disks verbatim quote and the four-option rationale; §15.3 probe-scaffolding landed inventory + end-to-end smoke results; §15.4 known-stale artifacts corrected at H-014; §15.5 what H-015 picks up; §15.6 what §15 does not change. §14 reserved for the H-015 probe-outcome addendum (intentionally out-of-order — probe outcome is its own unit of analysis and no live probe ran at H-014).

**Retrospective fabrication check at session open.** 38 unit tests re-run in a fresh venv against the pinned deps — all passing. Every SDK symbol in `probe.py` resolves against installed `polymarket-us==0.1.2`. Env var names match D-023. `slug_selector` schema matches `TennisEventMeta`. No fabrication. End-to-end smoke of the four CLI paths (self-check, probe/no-creds/config-error, probe/no-slug/no-candidate, `--help`) re-verified — all match H-013's claims and the probe.py code.

**pm-tennis-stress-test Render service provisioned.** Following the D-027-correct RB-002, operator created the service with Auto-Deploy Off, no persistent disk, the two required env vars. Build succeeded with 16 packages (all wheel-only, no compile). Self-check output verified line-by-line against RB-002 Step 4's expected block: polymarket_us 0.1.2 import ok, SDK surfaces importable, both credentials set, 0 probe candidates (the D-027 isolation signal), self-check complete. Exit-after-selfcheck restart-loop is expected and cosmetic; the sleep-loop alternative is documented in RB-002 Step 4 if the churn becomes noise. Service URL: `https://pm-tennis-stress-test.onrender.com`. No HTTP surface is served.

**STATE bumped v11 → v12.** Material changes: session counters advanced (sessions_count 13→14, last_handoff_id H-013→H-014, next_handoff_id H-014→H-015); `phase.current` bumped from `phase-3-attempt-2-probe-scaffolded` to `phase-3-attempt-2-service-provisioned`; `phase.current_work_package` rewritten to reflect H-014 completion and H-015 pickup; new `deployment.stress_test` block added; `resolved_operator_decisions_current_session` pruned per confirmed stricter convention and replaced with H-014's in-session rulings (STATE-v11-remediation, cut-point, additive-vs-bump, helper-snippet, pruning-convention); `phase_3_attempt_2_notes` +8 entries for H-014; `runbooks.RB-002.status` flipped from stale-draft to active; `architecture_notes` +1 entry on the provisioned service; `scaffolding_files` flipped H-013 pendings to true and added pending H-014 artifacts (v12, Handoff_H-014, rewritten README, rewritten RB-002, §15 additive); `phase_3_attempt_2_files` status flips (pending → committed for H-013 files; pending-stale → pending for README post-rewrite).

DecisionJournal: no changes this session. H-014 had no PODs open and none of its in-session rulings reached DJ-entry threshold (all were on method/convention, not project-shape commitments). Counter stays at 27.

RAID: no changes this session. No issues added or resolved; no new risks; no new assumptions.

Tripwires: none fired. Three preventive-mode exercises of research-first discipline without firing — the "I think I know the Render repo path" moment (verified via web_search before RB-002 committed the path in Step 5.1); the retrospective fabrication check against H-013 code (preventive in-session check before trusting the committed scaffolding); the STATE-v11 missing-from-commit discrepancy (surfaced rather than silently reconciled).

OOP events: 0 this session. Counters remain at 0 cumulative, 0 since last gate.

One sub-ruling made under operator-delegated authority — the pm-tennis-api-Shell candidate-listing helper is a pasted Python snippet (inlined in RB-002 §5.1), not a committed `src/stress_test/list_candidates.py` file. Reasoning documented in research-doc §15.4 and Handoff_H-014 §3; reversible at H-015 if operator prefers.

### H-015 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with the full H-013 + H-014 bundle landed: STATE v12, DJ (D-027 + D-025 footer, unchanged at H-014), Handoff_H-014, `src/stress_test/` package (with D-027-correct README), tests, RB-002 rewritten D-027-correct, research-doc v4 with §13 + §15 additives (§14 reserved).
- Discovery service `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`, healthy. Event count continues to grow monotonically since H-012 survey (74 → higher by ~48h).
- Stress-test service `pm-tennis-stress-test.onrender.com` live, Auto-Deploy Off, no disk attached, both credential env vars set, self-check verified healthy. Exit-after-selfcheck restart-loop running; no action required from H-015 unless the loop becomes noisy.
- Zero production Phase 3 code on `main` in `src/capture/` (Phase 2 preserved). Phase 3 probe code is in `src/stress_test/` — isolated by path per D-024 commitment 1 and D-020/Q2=(b).
- **Zero pending operator decisions.**
- Research doc at v4 with §13 + §15 additives; §14 reserved for H-015 probe-outcome addendum.
- D-027 active; D-025 commitment 1 superseded; D-025 commitments 2/3/4, D-024, D-023, D-020 all in force.
- Research-first discipline in force per D-016 and D-019.
- Pruning convention for `resolved_operator_decisions_current_session`: stricter reading, settled as of H-014.

### Validation posture going forward

At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode. At H-015 open, the check has two application surfaces:

- **Preventive for new H-015 code.** Main sweeps will likely require a new module (e.g., `src/stress_test/sweeps.py`) that uses SDK methods beyond the probe's current surface (`client.markets.list()` for api-sourced slugs, `markets_ws` semantics for multiple concurrent subscriptions). Every SDK symbol in sweep code must trace to the Polymarket US Python SDK README — per D-024 commitment 2 — or to a fresh SDK-source fetch at code-turn time, with the citation committed inline in the module header. Placeholder slug generation for the 100-slug-per-subscription stress must be implemented without assuming slugs-that-don't-exist will be rejected gracefully — the probe outcome at H-015 will inform whether ungraceful rejection risks the service's stability.

- **Retrospective for H-014 artifacts.** Three documents were rewritten or added this session: the README, RB-002, and research-doc §15. Each should pass a spot-check: every factual claim in the README and RB-002 traces to the probe.py code or to the D-027 DJ entry; every citation in §15 traces to the named URL + fetch-session; no fabricated file paths (the `/opt/render/project/src/` path in RB-002 §5.1 was verified at H-014 via web_search before commit).

Values of `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` must never enter the chat transcript — they are set via Render dashboard only. Live verified at H-014: both env vars show as `[ok] ... set` in the self-check output without any value disclosure.

---

*End of STATE.md — current document version: 12. Last updated: H-014.*
