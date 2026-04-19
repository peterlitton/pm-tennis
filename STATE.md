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
    current_version: 10
    last_updated: 2026-04-19
    last_updated_by_session: H-012

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-ready
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). Research document v4 accepted at H-012 (v3 at H-010, additive §13 at H-012). All four H-010 PODs resolved: Q4 via D-023 (H-011, credentials at Render env vars); §12 via D-024 (H-012, SDK); Q5' via D-025 (H-012, hybrid probe-first); §6-survey via D-026 (H-012, executed, N baseline = 74). Code turn blocked only on code-turn-research tasks (byte-level Ed25519 via SDK, timestamp-unit cross-check) and on session-pacing — likely next session (H-013) starts the code turn."
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
  last_handoff_id: H-012
  next_handoff_id: H-013
  sessions_count: 12
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
  pending_operator_decisions: []  # All four H-010 PODs are now resolved: Q4 at H-011 (D-023); §12, Q5', §6-survey all at H-012 (D-024, D-025, D-026). Code turn is no longer blocked on operator decisions.
  resolved_operator_decisions_current_session:
    - id: POD-H010-§12
      resolved_session: H-012
      resolved_by_decision: D-024
      resolution_summary: "Option (a) — SDK. Stress test is built on the official Polymarket US Python SDK (polymarket-us, github.com/Polymarket/polymarket-us-python). Ships fastest; minimal Tripwire 1 exposure; one new dependency added to a new isolated Render service per D-020 / Q2=(b), not to pm-tennis-api. Does not commit the Phase 3 full-deliverable pool architecture — that is re-evaluated post-stress-test."
    - id: POD-H010-Q5p
      resolved_session: H-012
      resolved_by_decision: D-025
      resolution_summary: "Option (c') — hybrid probe-first. Stress test runs a one-slug probe (gateway-sourced slug → SDK subscribe → ~10-second observation → disconnect) as its first runtime action after authentication. Probe outcome determines main-sweep slug source: api-sourced (SDK markets.list()) by default; gateway-sourced optional if bridge confirmed. Ambiguous probe outcomes are surfaced in the addendum rather than silently resolved."
    - id: POD-H010-§6-survey
      resolved_session: H-012
      resolved_by_decision: D-026
      resolution_summary: "Authorized and executed in-session (Render shell, 2026-04-19T16:22:29Z). Three objectives met: on-disk schema confirmed (matches discovery.py TennisEventMeta dataclass; meta.json path is /data/matches/{event_id}/meta.json, correcting v3's casual /data/events/ reference); N baseline = 74 slugs across 74 active events (one moneyline per event, uniform distribution); probe-slug default = event 9392, aec-atp-digsin-meralk-2026-04-21 (traceability anchor only; code turn reselects fresh)."
    - id: POD-H010-Q4
      resolved_session: H-011
      resolved_by_decision: D-023
      resolution_summary: "Option (a) — credentials exist and are stored as Render env vars POLYMARKET_US_API_KEY_ID and POLYMARKET_US_API_SECRET_KEY on the pm-tennis-api service. Values never entered the chat transcript; no rotation required. (Preserved from H-011 STATE v9 for continuity; next STATE refresh may prune to current-session entries only per convention.)"
  phase_3_attempt_2_notes:
    - "Research-first discipline in force per D-016 commitment 2 and R-010 — no fabrication of URLs or module symbols"
    - "H-010: research document produced at docs/clob_asset_cap_stress_test_research.md, three versions this session (v1, v2, v2.1, v3). v3 accepted."
    - "H-011: POD-H010-Q4 resolved via D-023. Polymarket US API credentials stored at Render env vars POLYMARKET_US_API_KEY_ID and POLYMARKET_US_API_SECRET_KEY on pm-tennis-api. Values never entered chat. Polymarket usage instructions confirmed three-header auth scheme and disambiguated timestamp unit as milliseconds (unix_ms)."
    - "H-012: POD-H010-§12 resolved via D-024 — SDK (option a). Stress-test code uses polymarket-us SDK against wss://api.polymarket.us/v1/ws/markets; one new dep in isolated Render service per D-020/Q2=(b); does not commit Phase 3 full pool architecture."
    - "H-012: POD-H010-Q5' resolved via D-025 — hybrid probe-first (option c'). One-slug gateway-sourced probe as first runtime action after authentication; probe outcome determines main-sweep slug source."
    - "H-012: POD-H010-§6-survey resolved via D-026 — executed in-session. Meta.json on-disk schema confirmed; N baseline = 74 slugs across 74 events (up from ≈38 at H-009 due to ~36h of continuous Phase 2 discovery; _write_meta immutability is working as designed); probe-slug default recorded as event 9392 for traceability."
    - "H-012: Research doc bumped v3 → v4. §13 added (H-012 rulings + survey findings + probe-slug default + code-turn scoping summary). §§1–12 unchanged — v4 is additive; v3's text including §5's ≈38 estimate is preserved as accepted rather than revised. v4 scope decision logged in Handoff_H-012 §9 (operator-delegated)."
    - "H-012: Meta.json path correction surfaced during §6 survey — research-doc v3 casually referenced '/data/events/' in several places (§7 Q5' draft; D-025 commitment 1 text); actual path is /data/matches/{event_id}/meta.json. Not retroactively corrected in v3 text per the 'additive v4' scoping decision. v4 §13.2 and D-026 note the correction."
    - "Sports WS endpoint and subscription format research deferred to Phase 3 attempt 2 Sports WS deliverable; not in scope for the asset-cap stress test deliverable"
    - "H-010 established (cited in v3 and v4): Markets WebSocket endpoint = wss://api.polymarket.us/v1/ws/markets; auth = Ed25519 three-header (X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature); subscription unit = market slug; wire format = camelCase enum-string (confirmed via SDK README response-side evidence); per-subscription cap = 100 slugs; concurrent-connection and rate limits not documented"
    - "Storage-growth runway (~35 days from 2026-04-19 at 290 MB/day) is a Phase 3 attempt 2 design consideration — R-012"
    - "sportradar_game_id populates closer to match start, not at discovery — capture worker design implication"
    - "H-012 close: zero PODs remain blocking the code turn. Code turn (likely H-013) blocked only on code-turn-research tasks (byte-level Ed25519 via SDK per D-023/D-024 commitment 4a; timestamp-unit cross-check per D-023/D-024 commitment 4b). Both are research-in-session tasks, not operator decisions."
    - "H-011: Byte-level Ed25519 signing operation (exact input bytes, exact encoding) still not verified against authoritative source. Polymarket usage instructions paste in H-011 did not fully resolve. Surfaced in D-023; code-turn research task, not a POD. D-024 commitment 4 re-scopes this through the SDK: if SDK owns signing, collapses to trust-SDK; if user-code surface is exposed, that surface is cited at code-turn."

# ---- Runbooks inventory ----
runbooks:
  RB-001:
    title: "GitHub + Render Setup"
    path: "runbooks/Runbook_GitHub_Render_Setup.md"
    produced_session: H-004
    status: complete

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
    current_version: 10
    committed_to_repo: pending  # v10 produced this session
    committed_session: H-012
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
    committed_to_repo: pending  # D-024, D-025, D-026 added this session
    committed_session: H-012
    pending_entries: []
  RAID_md:
    status: accepted
    committed_to_repo: true  # no changes this session; H-010 I-015 landed before H-011 open, no H-011 or H-012 changes
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  clob_asset_cap_stress_test_research_md:
    status: accepted
    path: "docs/clob_asset_cap_stress_test_research.md"
    current_version: 4
    committed_to_repo: pending  # v4 produced this session
    committed_session: H-012
    renamed_session: H-011
    note: "Phase 3 attempt 2 first-deliverable research doc per D-018 and D-019. v1 → v2 → v2.1 → v3 at H-010; v3 accepted at H-010 close. At H-011 the on-disk filename was corrected from CLOB-asset-cap-stress-test-research.md to the canonical clob_asset_cap_stress_test_research.md. At H-012 v4 added: §13 captures H-012 rulings D-024/D-025/D-026, §6 survey findings, and probe-slug default; §§1–12 unchanged from v3 (additive v4 scope decision, operator-delegated)."
  Handoff_H010_md:
    status: accepted
    path: "Handoff_H-010.md"
    committed_to_repo: true  # filename-drift fix at H-011: renamed from Handoff_H_010.md (underscore) to Handoff_H-010.md (hyphen) to match convention used H-004 through H-009
    committed_session: H-010
    renamed_session: H-011
  Handoff_H011_md:
    status: accepted
    path: "Handoff_H-011.md"
    committed_to_repo: true  # landed at commit 374e2e6 in the H-011 bundle
    committed_session: H-011
  Handoff_H012_md:
    status: accepted
    path: "Handoff_H-012.md"
    committed_to_repo: pending  # produced this session
    committed_session: H-012
  data_dictionary_md:
    status: not-started
    note: "Phase 3 deliverable"
  window_close_analysis_notebook:
    status: not-started
    note: "Phase 7 or post-Phase-7 deliverable"

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

Phase 2 remains complete and operational. The service at `pm-tennis-api.onrender.com` continues to run the reverted Phase 2 `main.py` (SHA `ceeb5f29…`, 2,989 bytes, 87 lines). Discovery loop polls `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. No Phase 3 code exists on `main`. Discovery growth since H-009: 38 `meta.json` files written at H-009 → 74 at H-012 (confirmed via §6 survey executed in-session at 2026-04-19T16:22:29Z).

**All four H-010 PODs are resolved across H-011 and H-012.** POD-H010-Q4 (credentials) via D-023 at H-011. POD-H010-§12 (SDK vs hand-roll) via D-024 at H-012 — SDK. POD-H010-Q5′ (slug source) via D-025 at H-012 — hybrid probe-first. POD-H010-§6-survey (meta.json survey) via D-026 at H-012 — authorized and executed. No PODs remain blocking the code turn.

What the code turn (likely H-013) inherits, consolidated from research-doc v4 §13.5:
- Dependency: `polymarket-us` SDK in a new isolated Render service per D-020/Q2=(b); not added to pm-tennis-api.
- Credentials: `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` via `os.environ`; SDK consumes them.
- First runtime action: Q5′=(c′) one-slug gateway-sourced probe, ~10-second observation window, outcome recorded.
- Main sweeps: §7 Q3=(c) — per-subscription count sweep × concurrent-connection count sweep. Pure connection-level test, no disk writes of received content.
- Main-sweep slug source: probe-outcome-dependent (api-sourced default).
- Code-turn research tasks (not PODs): byte-level Ed25519 signing scoped through SDK (may collapse to "trust-SDK" if SDK owns signing internally); timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication`.
- N baseline: 74 slugs across 74 events as of 2026-04-19T16:22:29Z; slam-week projection ≈128 per v3 §5.
- Probe-slug default (traceability anchor, code turn reselects fresh): event 9392, `aec-atp-digsin-meralk-2026-04-21`.

What the H-010 research established (all cited in `docs/clob_asset_cap_stress_test_research.md` v3 and preserved in v4, all from `docs.polymarket.us` per D-013) remains valid: Markets WebSocket is `wss://api.polymarket.us/v1/ws/markets`. Authentication is Ed25519 with three handshake headers signing `timestamp + "GET" + path`, 30-second clock window. Subscription unit is market slug. Wire format is camelCase with enum-string subscription types. Per-subscription cap is 100 slugs. Concurrent-connection and rate limits are not documented — that is the empirical gap the stress test exists to characterize.

Three plan-text patches are queued in `pending_revisions` against the next plan revision: v4.1-candidate (Section 5.6 baseline-path correction per I-014), v4.1-candidate-2 (Section 5.4 / Section 11.3 "150-asset cap" revision per I-015), and v4.1-candidate-3 (discovery.py line-37 / line-120 code-comment correction per H-010 research doc §11 point 3). All three will be bundled when the next plan revision is cut.

### What changed in H-012

DecisionJournal: D-024, D-025, D-026 added at the top (newest-first per convention). D-024 resolves POD-H010-§12 (SDK). D-025 resolves POD-H010-Q5′ (hybrid probe-first). D-026 resolves POD-H010-§6-survey (authorized and executed; N=74; probe-slug default = 9392).

Research document bumped v3 → v4. §13 added capturing H-012 rulings, §6 survey findings, probe-slug default, and consolidated code-turn scoping summary. §§1–12 unchanged from v3. v4 scope is additive only per operator-delegated scoping decision.

STATE bumped v9 → v10. Material changes: session counters advanced (sessions_count 11→12, last_handoff_id H-011→H-012, next_handoff_id H-012→H-013); `pending_operator_decisions` drained to empty (all four H-010 PODs now resolved); `resolved_operator_decisions_current_session` rewritten to list the three H-012 resolutions plus H-011's Q4 (Q4 preserved with explicit note pending operator ruling on convention); `phase_3_attempt_2_notes` extended with six H-012 entries; `architecture_notes` extended with Q5′/§12/§6-survey resolutions, meta.json path correction, N=74 baseline, and probe-slug default; `discovery` block updated (meta_json_files_written 38→74, new `current_event_count` and `current_slug_count` fields at 74); scaffolding_files inventory updated (H-011 now committed=true, v10/D-024-D-026/research-doc-v4/Handoff_H-012 all pending, research-doc current_version 3→4).

RAID: no changes this session. No issues added or resolved; no new risks; no new assumptions. The H-010 PODs were tracked in STATE `open_items.pending_operator_decisions`, not in RAID, so POD resolution does not affect RAID content.

§6 survey executed as a single consolidated bash script on the Render shell for pm-tennis-api at 2026-04-19T16:22:29Z. Read-only; no disk mutation. Script content reproduced in Handoff_H-012 §4. Survey output pasted back in-session. Findings recorded in research-doc v4 §13.2 and D-026.

No tripwires fired. No out-of-protocol events. OOP counters remain at 0 cumulative, 0 since last gate.

One scoping decision made under operator-delegated authority (v4 scope = additive only) — logged in Handoff_H-012 §9 self-report; reasoning preserved for future-Claude. One minor convention question surfaced for future ruling (pruning previous-session resolutions from `resolved_operator_decisions_current_session`) — not urgent.

### H-013 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with H-012 bundle landed (STATE v10, DecisionJournal with D-024/D-025/D-026, research-doc v4, Handoff_H-012).
- Service running `main.py` at `0.1.0-phase2`, discovery loop healthy. 74 active tennis events on disk at H-012 close (up from 38 at H-009; still growing as discovery runs).
- Zero Phase 3 code on `main`.
- Polymarket US credentials at Render env vars `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` (D-023). Code reads via `os.environ`; values never in repo.
- Research-first discipline in force per D-016 and D-019.
- **Zero pending operator decisions blocking the code turn.** `pending_operator_decisions` is empty.
- Code turn is the next substantive work. Two code-turn research tasks run alongside it: byte-level Ed25519 (may collapse to trust-SDK) and timestamp-unit cross-check. Neither is a POD.
- Phase 3 exit criteria in `phase.next_gate_expected.triggers` remain unchanged.

### Validation posture going forward

Unchanged from H-010 and H-011. At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode: code drafted in the session that names any external endpoint, URL, module path, class name, or function signature must trace to (a) operator-provided material, (b) an existing committed file, or (c) documentation fetched in this same session. H-012 did not draft code, but the §6 survey demonstrated the discipline in a different form: commands were drafted against the *verified* on-disk schema (derived from reading `src/capture/discovery.py` first) rather than the *implied* schema from research-doc §6 prose. This caught a "/data/events/" vs "/data/matches/" path error before the operator executed the commands.

At code-turn time (H-013), the fabrication check applies fully: every SDK symbol referenced in stress-test code must trace to the Polymarket US Python SDK README (the H-010 v3 source) or to fresh SDK-source fetches at that moment. Values of `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` must never enter the chat transcript — they are read via `os.environ` only.

---

*End of STATE.md — current document version: 10. Last updated: H-012.*
