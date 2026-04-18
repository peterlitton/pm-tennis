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
  description: "Polymarket US in-play tennis moneyline mispricing instrument and trading system"
  plan_document:
    current_version: v3
    current_version_date: 2026-04-17
    location: "project knowledge and GitHub repository"
    pending_revisions:
      - decision: D-002
        sections: ["Section 8 Phase 7", "Section 9", "Section 11"]
        summary: "Incorporate pilot-then-freeze protocol for signal_thresholds.json"
      - decision: D-003
        sections: ["Section 8 Phase 1", "Section 11.1"]
        summary: "Phase 1 Sports WS granularity check becomes explicit go/no-go gate"
  state_document:
    current_version: 4
    last_updated: 2026-04-18
    last_updated_by_session: H-004

# ---- Phase and work package ----
phase:
  current: pre-build
  current_work_package: "Phase 1 — Host preparation, verification, and Sackmann pipeline"
  work_package_started_session: H-004
  last_gate_passed:
    name: null
    phase: null
    date: null
    handoff_with_verdict: null
  next_gate_expected:
    name: "Phase 1 exit gate"
    phase: phase-1
    triggers:
      - "Host / PaaS ready and verified reachable to Polymarket endpoints"
      - "Sports WS point-level granularity verified (per D-003 this is a gate decision, not a silent downgrade)"
      - "Capture-pool asset-cap stress test complete"
      - "Sackmann pipeline built, P(S) tables committed, build_log.json committed"
      - "fees.json committed, breakeven.json derived and committed"
      - "JS/Python fair-price parity test vector committed"
      - "Tournament-to-format mapping table committed"

# ---- Session accounting ----
sessions:
  last_handoff_id: H-004
  next_handoff_id: H-005
  sessions_count: 4  # H-001 (kickoff), H-002 (scaffolding begin), H-003 (scaffolding complete), H-004 (infrastructure)
  most_recent_session_date: 2026-04-18
  out_of_protocol_events_cumulative: 0
  out_of_protocol_events_since_last_gate: 0
  out_of_protocol_trigger_phrase: "out-of-protocol"

# ---- Repository and deployment state ----
repo:
  host: GitHub
  url: "https://github.com/peterlitton/pm-tennis"
  visibility: public  # per D-005
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
    python_version_deployed: "3.14.3"
    python_version_target: "3.12"
    python_version_pinned: false  # flag: pin to 3.12 in Phase 1
    persistent_disk_mount: "/data"
    persistent_disk_size_gb: 10
    auto_deploy: true
    auto_deploy_branch: main
    health_check_path: "/healthcheck"
    exists: true
    status: live
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
    path: data/fees.json
    exists: false
    sha256: null
    last_modified_session: null
  breakeven_json:
    path: data/breakeven.json
    exists: false
    sha256: null
    last_modified_session: null
  sackmann_build_log:
    path: data/sackmann/build_log.json
    exists: false
    sha256: null
    last_modified_session: null

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

# ---- Open items requiring attention ----
open_items:
  tripwire_events_currently_open: 0
  python_version_pin_needed: true  # deploy used 3.14.3; plan specifies 3.12; fix in Phase 1
  raid_entries_by_severity:
    sev_8: 2   # R-001 (adverse selection), R-010 (statistical power)
    sev_7: 9   # R-002 through R-009, R-011
    sev_6: 3   # R-009 (monitoring), R-012, R-013
    sev_5: 2   # R-014, R-015
    sev_4_and_below: 0
    issues_open: 5   # I-001 through I-005
    assumptions_unvalidated: 4  # A-001 through A-004 (A-005 is monitoring)
  decision_journal_open_subquestions:
    - decision: D-002
      count: 4
      summary: "Pilot duration, calibration method, overfitting guardrails, no-tradeable-config branch"
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

# ---- Cost tracking ----
costs:
  expected_monthly_usd:
    baseline: 35-50
    under_memory_pressure: 110
  actual_monthly_usd_estimate: 8.25  # Starter $7 + 10GB disk $1.25
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
    - component: "Domain (if custom)"
      expected_usd_range: "~1 (amortized)"
      status: deferred
    - component: "Polymarket US trading account balance"
      note: "operator-sized per Section 9 position-sizing commitment; not a platform cost"

# ---- Scaffolding files inventory ----
scaffolding_files:
  STATE_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: true
    committed_session: H-004
  Orientation_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: true
    committed_session: H-004
  Playbook_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: true
    committed_session: H-004
  SECRETS_POLICY_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: true
    committed_session: H-004
  DecisionJournal_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: true
    committed_session: H-004
  RAID_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: true
    committed_session: H-004
  PreCommitmentRegister_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: true
    committed_session: H-004
  data_dictionary_md:
    status: not-started
    produced_session: null
    note: "Created in Phase 3 or earlier per H-001"
  window_close_analysis_notebook:
    status: not-started
    note: "Built before observation opens, Phase 7 or post-Phase-7"

# ---- End of structured data ----
```

---

## Prose commentary

### Where the project is right now

Four sessions in. H-004 closed the last pre-Phase-1 infrastructure gap. The GitHub repository `peterlitton/pm-tennis` is live and public, all seven governance scaffolding files are committed for the first time, and the Render backend service `pm-tennis-api` is deployed and returning a live `/healthcheck` response. The operator verified the healthcheck both in a desktop browser and on the iPhone that will be used for trading.

Phase 1 technical work begins in H-005. The first task is a quick housekeeping item — pinning the Python version to 3.12 (Render defaulted to 3.14.3) — followed immediately by the Sackmann pipeline, which is the longest Phase 1 deliverable.

No tripwires have fired. No out-of-protocol events have occurred. The D-002 sub-questions remain open and non-blocking.

### What changed in H-004

**YAML changes from v3 to v4:**
- `state_document.current_version`: 3 → 4
- `state_document.last_updated_by_session`: H-003 → H-004
- `sessions.last_handoff_id`: H-003 → H-004
- `sessions.next_handoff_id`: H-004 → H-005
- `sessions.sessions_count`: 3 → 4
- `phase.current_work_package`: "GitHub + Render setup walkthrough" → "Phase 1 — Host preparation, verification, and Sackmann pipeline"
- `phase.work_package_started_session`: H-003 → H-004
- `repo.url`: null → `https://github.com/peterlitton/pm-tennis`
- `repo.exists`: false → true
- `deployment.backend.*`: all fields populated (service live)
- `deployment.backend.python_version_deployed`: "3.14.3" (new field — flags mismatch with plan's 3.12)
- `deployment.backend.python_version_pinned`: false (new field — action item for Phase 1)
- `open_items.python_version_pin_needed`: true (new field)
- `costs.actual_monthly_usd_estimate`: 0 → 8.25
- All `scaffolding_files.*.committed_to_repo`: false → true (with `committed_session: H-004`)
- `runbooks.RB-001`: new section added

### Why the Python version mismatch is a minor flag, not a RAID entry

Render defaulted to Python 3.14.3 rather than the plan's specified 3.12. For the placeholder `main.py` this has no consequence — `fastapi` and `uvicorn` work fine on 3.14. However the plan specifies 3.12 throughout, and the Sackmann pipeline and capture engine will be written and tested against 3.12. Pinning early is cleaner than allowing the deployed version to drift from the development target. This is handled by adding a `.python-version` file to the repo at the start of H-005, before any Phase 1 code is written. It is flagged in STATE rather than RAID because it requires one small action, not ongoing risk management.

### Unchanged from STATE v3

The YAML field dictionary, failure modes and recovery procedures, read/write protocol, non-coverage section, and artifact-interactions section in the prose commentary are unchanged from v3. These sections are schema-stable and do not require per-session updates.

---

*End of STATE.md — current document version: 4. Last updated: H-004.*
