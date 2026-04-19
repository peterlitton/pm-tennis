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
        summary: "Remove data/baseline/ from Render disk storage layout — baseline files live in repo, not on disk"
  state_document:
    current_version: 6
    last_updated: 2026-04-19
    last_updated_by_session: H-007

# ---- Phase and work package ----
phase:
  current: phase-3-ready
  current_work_package: "Phase 3 — Capture (CLOB pool, Sports WS client, correlation, JSONL archive)"
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

# ---- Session accounting ----
sessions:
  last_handoff_id: H-007
  next_handoff_id: H-008
  sessions_count: 7
  most_recent_session_date: 2026-04-19
  out_of_protocol_events_cumulative: 0
  out_of_protocol_events_since_last_gate: 0
  out_of_protocol_trigger_phrase: "out-of-protocol"

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
    auto_deploy: true
    auto_deploy_branch: main
    health_check_path: "/healthcheck"
    build_command: "pip install -r requirements.txt"
    start_command: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    exists: true
    status: live
    notes: >
      Discovery loop runs as asyncio background task inside this service (D-014).
      Separate pm-tennis-discovery background worker was created and deleted this
      session — Render disk-per-service constraint makes shared disk impossible
      across services.
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
  first_poll_events_discovered: 38
  meta_json_files_written: 38
  delta_stream_path: "/data/events/discovery_delta.jsonl"
  poll_interval_seconds: 60
  gateway_base: "https://gateway.polymarket.us"
  participant_type_confirmed: "PARTICIPANT_TYPE_PLAYER"

# ---- Open items requiring attention ----
open_items:
  tripwire_events_currently_open: 0
  python_version_pin_needed: false  # resolved H-005
  decision_journal_entries_needed:
    - D-013  # Polymarket US gateway is correct API target
    - D-014  # Discovery runs inside API service
    - D-015  # Tennis sport slug confirmed as "tennis"
  raid_entries_by_severity:
    sev_8: 2   # R-001 (adverse selection), R-010 (statistical power)
    sev_7: 9   # R-002 through R-009, R-011
    sev_6: 3   # R-009 (monitoring), R-012, R-013
    sev_5: 2   # R-014, R-015
    sev_4_and_below: 0
    issues_open: 4   # I-001 resolved H-005; I-002 through I-005 open
    assumptions_unvalidated: 4  # A-001 through A-004
  pending_operator_decisions: []

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

# ---- Architectural notes (cross-session reference) ----
architecture_notes:
  - "Discovery loop runs as asyncio background task inside pm-tennis-api (D-014)"
  - "Render persistent disk is per-service — no cross-service disk sharing possible"
  - "Polymarket US public gateway: gateway.polymarket.us (no auth for reads)"
  - "Polymarket US authenticated API: api.polymarket.us (not used — no order placement)"
  - "Sport slug tennis confirmed with leagues [wta, atp]"
  - "PARTICIPANT_TYPE_PLAYER confirmed for tennis players"

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
    current_version: 6
    committed_to_repo: true
    committed_session: H-007
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
    committed_to_repo: true
    pending_entries: [D-013, D-014, D-015]
  RAID_md:
    status: accepted
    committed_to_repo: true
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  data_dictionary_md:
    status: not-started
    note: "Phase 3 deliverable"
  window_close_analysis_notebook:
    status: not-started
    note: "Phase 7 or post-Phase-7 deliverable"

# ---- Phase 2 source files ----
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
    committed_session: H-007
    notes: "Updated to include discovery background task on startup"

# ---- End of structured data ----
```

---

## Prose commentary

### Where the project is right now

Phase 2 complete. The discovery loop is running live on `pm-tennis-api`, polling `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. The first poll discovered 38 active tennis events and wrote 38 `meta.json` files to the Render persistent disk at `/data/matches/{event_id}/meta.json`. The discovery delta stream is live at `/data/events/discovery_delta.jsonl`.

Phase 3 begins next session. The two primary deliverables are the CLOB WebSocket pool and the Sports WebSocket client. These are the components that will capture live order-book ticks and score-state transitions respectively.

### What changed in H-007

**YAML changes from v5 to v6:**
- `state_document.current_version`: 5 → 6
- `state_document.last_updated`: 2026-04-18 → 2026-04-19
- `state_document.last_updated_by_session`: H-005 → H-007
- `sessions.last_handoff_id`: H-006 → H-007
- `sessions.next_handoff_id`: H-007 → H-008
- `sessions.sessions_count`: 6 → 7 (counting H-006 as session 6)
- `phase.current`: pre-build → phase-3-ready
- `phase.current_work_package`: Phase 1 → Phase 3
- `phase.last_gate_passed`: Phase 2 exit gate, date 2026-04-19
- `deployment.backend.build_command`: added (was missing, corrected to `pip install -r requirements.txt`)
- `deployment.backend.notes`: added D-014 architectural note
- `project.plan_document.current_version`: v3 → v4 (corrected — was stale from pre-H-006)
- `discovery.*`: new section added, all fields populated
- `open_items.decision_journal_entries_needed`: D-013, D-014, D-015
- `phase_2_files.*`: new section added
- `architecture_notes`: new section added

### Critical architectural decision recorded here (D-014)

The build plan described a "capture worker" as a separate Render background worker service. This session discovered empirically that Render persistent disks cannot be shared between services. A separate `pm-tennis-discovery` background worker was created, confirmed working (slug verified, first poll 200 OK), but crashed on disk write with `PermissionError: [Errno 13] Permission denied: '/data'` because the disk was only attached to `pm-tennis-api`.

Resolution: the discovery loop runs as an asyncio background task inside the FastAPI process. Both the HTTP server and the discovery loop share the same `/data` disk. This is the correct architecture for this deployment environment and is recorded as D-014.

### Render build command correction

The `pm-tennis-api` service had its build command hardcoded to `pip install fastapi uvicorn` — set manually during the initial Render setup in H-004. This meant `httpx`, `pandas`, `numpy`, `pyarrow`, `scipy`, and `requests` were never installed in the production environment despite being in `requirements.txt`. Corrected to `pip install -r requirements.txt` in service Settings during this session.

### Phase 3 readiness

The discovery delta stream is the input to Phase 3. The capture worker will tail `discovery_delta.jsonl` to know which event IDs to open CLOB WebSocket connections for. The `sportradar_game_id` field in each `meta.json` is the correlation key for the Sports WebSocket. Both are populated and on disk.

---

*End of STATE.md — current document version: 6. Last updated: H-007.*
