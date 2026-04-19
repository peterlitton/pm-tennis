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
    current_version: 11
    last_updated: 2026-04-19
    last_updated_by_session: H-013

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-probe-scaffolded
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). Research document v4 accepted at H-012. All four H-010 PODs resolved. H-013 landed: probe scaffolding (src/stress_test/) + 38 unit tests + three code-turn-research tasks resolved (SDK Ed25519 signing fully internal; timestamp unit confirmed milliseconds; SDK transitive deps = 12 packages, no compile required) + D-027 (probe-slug transport supersedes D-025 commitment 1 with operator-supplied --slug CLI arg; Render disks strictly single-service per authoritative docs). H-014 picks up with: (1) rewriting two stale artifacts committed at H-013 (src/stress_test/README.md + runbooks/Runbook_RB-002_Stress_Test_Service.md Steps 3 and 5), (2) Render stress-test service provisioning per corrected RB-002, (3) live probe execution per D-027 two-shell workflow, (4) main sweeps (§7 Q3=(c)), (5) research-doc §15 additive or v5."
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
  last_handoff_id: H-013
  next_handoff_id: H-014
  sessions_count: 13
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
  pending_operator_decisions: []  # All four H-010 PODs resolved through H-012. D-027 ruled in-session at H-013. No operator decisions blocking H-014.
  resolved_operator_decisions_current_session:
    # Pruned to current-session (H-013) entries only per the stricter reading of the convention flagged in Handoff_H-012 §8.
    # The H-013 rulings below are in-session operator rulings, not POD entries (H-013 had no PODs open at session start).
    - id: H-013-cut-point
      resolved_session: H-013
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Smaller cut for H-013: SDK research + auth + probe scaffolding this session; main sweeps + live execution deferred to H-014. Per H-012 addendum's code-turn pacing guidance."
    - id: H-013-code-location
      resolved_session: H-013
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Stress-test code lives at src/stress_test/ inside the main repo; deployed as a separate Render service per D-020/Q2=(b). Same repo, separate service — one git history, clean service teardown."
    - id: H-013-architecture-options
      resolved_session: H-013
      resolved_by_decision: D-027
      resolution_summary: "Option D after Render disk-sharing architecture research: operator picks slug via pm-tennis-api Shell, passes to probe as --slug CLI arg. Preserves D-024 commitment 1 and D-020/Q2=(b) isolation. Selected over three alternatives (add endpoint to pm-tennis-api; sync via object storage; fetch from gateway at probe time)."
    - id: H-013-supersession-vs-reinterpretation
      resolved_session: H-013
      resolved_by_decision: D-027
      resolution_summary: "D-027 is journaled as supersession of D-025 commitment 1 rather than re-interpretation. Operator selected the stricter discipline: supersession keeps D-025's original text intact in the historical record and forces the new reality into a named, dated, numbered DJ entry."
    - id: H-013-option-X-close
      resolved_session: H-013
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Option X session close: stop after code + tests land. Deferred to H-014: (a) src/stress_test/README.md update for D-027; (b) Runbook RB-002 Steps 3 and 5 rewrite for D-027; (c) Render stress-test service provisioning; (d) live probe execution; (e) main sweeps; (f) research-doc §15 or v5."
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
    status: "draft-stale-post-D-027 — Steps 3 and 5 need rewrite before H-014 deployment; flagged as H-014 first task per Handoff_H-013 §5"

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
    current_version: 11
    committed_to_repo: pending  # v11 produced this session
    committed_session: H-013
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
    committed_to_repo: pending  # D-027 added and D-025 footer modified this session
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
    committed_to_repo: true  # v4 landed in the H-012 commit
    committed_session: H-012
    renamed_session: H-011
    note: "v4 remains the current accepted version. D-027 ruling at H-013 is captured in the Decision Journal and Handoff_H-013 but NOT yet reflected in the research doc — H-014 ruling on §15-additive-vs-v5-bump."
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
    committed_to_repo: pending  # produced this session
    committed_session: H-013
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
    status: pending
    committed_session: H-013
    note: "Package init with version string 0.1.0-stress-test-h013"
  src_stress_test_slug_selector_py:
    path: "src/stress_test/slug_selector.py"
    status: pending
    committed_session: H-013
    tests: "tests/test_stress_test_slug_selector.py — 19 tests passing"
    note: "Reads /data/matches/*/meta.json and returns fresh ProbeCandidate. Schema verified against TennisEventMeta in src/capture/discovery.py lines 139-193."
  src_stress_test_probe_py:
    path: "src/stress_test/probe.py"
    status: pending
    committed_session: H-013
    tests: "tests/test_stress_test_probe_cli.py — 19 tests passing"
    note: "Stress-test entry point. Self-check mode (default, no network) + probe mode (--probe --slug=<SLUG>). D-027-compliant: --slug CLI arg is the production slug source. Module header carries explicit SDK-README citations."
  src_stress_test_requirements_txt:
    path: "src/stress_test/requirements.txt"
    status: pending
    committed_session: H-013
    note: "Isolated deps for pm-tennis-stress-test service. polymarket-us==0.1.2 + pytest==8.3.4. pm-tennis-api's /requirements.txt is NOT modified per D-024 commitment 1."
  src_stress_test_README_md:
    path: "src/stress_test/README.md"
    status: pending-stale
    committed_session: H-013
    note: "STALE as of D-027 ruling. Slug-selection and Running-on-Render sections still describe disk-based production path. H-014 first-task: update per D-027 before deployment. Stale sections flagged in Handoff_H-013 §5.1."
  tests_test_stress_test_slug_selector_py:
    path: "tests/test_stress_test_slug_selector.py"
    status: pending
    committed_session: H-013
    note: "19 tests; pure on-disk fixtures; no mocking. All passing."
  tests_test_stress_test_probe_cli_py:
    path: "tests/test_stress_test_probe_cli.py"
    status: pending
    committed_session: H-013
    note: "19 tests; argparse + run_probe early-return paths + main() dispatch + ProbeOutcome + classification mapping + ProbeConfig clamping. Zero SDK mocking per H-012 addendum. All passing."

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

**Phase 3 attempt 2 probe scaffolding landed at H-013.** `src/stress_test/` package now contains probe.py (entry point with self-check + probe modes), slug_selector.py (local-dev/helper utility), requirements.txt (isolated deps — `polymarket-us==0.1.2` + `pytest==8.3.4`), __init__.py, and a README. 38 unit tests across two test files, all passing. Zero SDK mocking per H-012 addendum guidance — network-touching path is exercised at H-014 against the live gateway.

**All three H-013 code-turn research tasks resolved against authoritative sources.** SDK Ed25519 signing surface is fully internal (collapses to "trust the SDK"); timestamp unit is milliseconds, unambiguous; SDK transitive deps are 12 standard packages with wheels for Linux/x86_64 + CPython 3.12. See `architecture_notes` YAML block for the specific citations.

**D-027 ruled at H-013** after Claude fetched `render.com/docs/disks` during probe-scaffolding work and discovered that Render persistent disks are strictly single-service — the shared-disk architecture D-025 commitment 1 assumed is not supported. Operator ruled Option D: probe slug is supplied via `--slug=SLUG` CLI argument; operator selects from `/data/matches/` via `pm-tennis-api` Shell. D-025 commitment 1 is superseded (per explicit operator ruling choosing supersession over re-interpretation); commitments 2, 3, 4 are unaffected. D-024 commitment 1 (pm-tennis-api/requirements.txt untouched) and D-020/Q2=(b) (isolated Render service) are preserved exactly.

**What the H-014 session inherits:**

- Repo with the H-013 bundle: STATE v11, DJ with D-027 and D-025 footer, Handoff_H-013, `src/stress_test/` package, test files, draft RB-002.
- Two known-stale artifacts committed under the Option X cut: `src/stress_test/README.md` (slug-selection sections) and `runbooks/Runbook_RB-002_Stress_Test_Service.md` (Steps 3 and 5). Both flagged in Handoff_H-013 §5 with specific rewrite guidance. H-014 first task.
- Zero operator decisions blocking.
- Research-doc `docs/clob_asset_cap_stress_test_research.md` at v4. H-014 ruling on §15-additive vs v5.
- Credentials at Render env vars on pm-tennis-api service. H-014 step 5 reuses the same values via the stress-test service's own env-var block.
- Zero Phase 3 production code on `main` in `src/capture/` (Phase 2 preserved). Phase 3 probe code is in `src/stress_test/` — isolated by path per D-024 commitment 1 and D-020/Q2=(b).

### What changed in H-013

DecisionJournal: D-027 prepended (newest-first per convention). D-025's resolution footer updated with "SUPERSEDED IN PART BY D-027" note per DJ conventions line 13. D-025 original text preserved in full.

Research document: unchanged this session (v4 remains accepted). D-027 ruling is captured in the DJ and Handoff_H-013; research-doc v5 or §15 additive is an H-014 ruling.

STATE: bumped v10 → v11. Material changes: session counters advanced (sessions_count 12→13, last_handoff_id H-012→H-013, next_handoff_id H-013→H-014); `phase.current` bumped from `phase-3-attempt-2-ready` to `phase-3-attempt-2-probe-scaffolded`; `phase.current_work_package` rewritten to reflect H-013 completion and H-014 pickup; `pending_operator_decisions` still empty (D-027 ruled in-session, not a carried-forward POD); `resolved_operator_decisions_current_session` pruned to H-013 entries only per the stricter reading of the H-012-flagged convention question (Claude-under-delegated-authority ruling, documented for visibility in Handoff_H-013 §7 and §9); `phase_3_attempt_2_notes` +several entries covering D-027, code-turn-research resolutions, scaffolding completion, known-stale artifacts; `architecture_notes` +5 entries on Render disks/D-027/SDK signing/timestamp unit/transitive deps; `runbooks` inventory adds RB-002 with stale-flag; `scaffolding_files` updated (v11/Handoff_H013/DecisionJournal pending-commit; previous session's pending-commits marked committed=true); new `phase_3_attempt_2_files` section tracks the stress-test package and test files.

RAID: no changes this session. No issues added or resolved. No new risks or assumptions.

Code + tests: `src/stress_test/` package created with 5 files; `tests/test_stress_test_slug_selector.py` (19 tests) and `tests/test_stress_test_probe_cli.py` (19 tests) created. All 38 tests passing. Draft runbook RB-002 created but carries two known-stale sections (Steps 3 and 5) flagged for H-014 rewrite.

Three moments of preventive research-first discipline without firing tripwires: SDK env-var-name mismatch caught pre-code; Render disk-architecture validated before operator procedure; SDK method surface cited against README line-by-line in probe.py header.

No tripwires fired. No out-of-protocol events. OOP counters remain at 0 cumulative, 0 since last gate.

### H-014 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with the H-013 bundle landed (STATE v11, DecisionJournal with D-027 and D-025 footer, Handoff_H-013, `src/stress_test/` package, tests, draft RB-002).
- Service at `pm-tennis-api.onrender.com` running `main.py` at `0.1.0-phase2`, discovery loop healthy. 74+ active tennis events on disk (count will be higher than H-013 snapshot by ~24h of continuous discovery).
- Zero production Phase 3 code on `main` in `src/capture/` (Phase 2 preserved, Phase 3 probe code is in `src/stress_test/` — intentionally isolated).
- Zero Render services deployed for Phase 3 — isolated stress-test service is provisioned at H-014 step 5, not at H-014 open.
- Polymarket US credentials at Render env vars `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` on **pm-tennis-api** service (D-023). H-014 step 5 enters the same values into the new pm-tennis-stress-test service's env vars via the Render dashboard. Values never in repo, never in chat transcript.
- Research document at v4. §15-additive-vs-v5 is an H-014 ruling.
- **Two known-stale artifacts flagged for first-task H-014 rewrite:** `src/stress_test/README.md` and `runbooks/Runbook_RB-002_Stress_Test_Service.md` Steps 3 and 5. Specific rewrite guidance in Handoff_H-013 §5.
- **Zero pending operator decisions.**
- D-027 active; D-025 commitment 1 superseded; remaining D-025 commitments in force.
- Research-first discipline in force per D-016 and D-019, reinforced by H-013 evidence trail.

### Validation posture going forward

At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode. At H-014 open this is both preventive (for new code H-014 writes: main sweeps, any helper utilities) and retrospective (the `src/stress_test/` code committed at H-013 should be spot-checked — every SDK symbol traces to the cited README lines in the probe.py module header; every env-var name matches D-023; the `src/stress_test` package does not import from `src.capture` — it reads discovery.py's on-disk schema as JSON via slug_selector, avoiding the cross-module import coupling that contributed to the H-008 `DiscoveryConfig` fabrication).

At code-turn time in H-014 (main sweeps), the fabrication check applies fully: every SDK symbol referenced in new sweep code must trace to the Polymarket US Python SDK README OR to an explicit in-session source fetch. Values of `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` must never enter the chat transcript.

---

*End of STATE.md — current document version: 11. Last updated: H-013.*
