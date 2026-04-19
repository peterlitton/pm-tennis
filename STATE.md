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
  state_document:
    current_version: 7
    last_updated: 2026-04-19
    last_updated_by_session: H-009

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-ready
  current_work_package: "Phase 3 attempt 2 — scope and first deliverable to be determined at H-010 by operator direction"
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
  last_handoff_id: H-009
  next_handoff_id: H-010
  sessions_count: 9
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
  first_poll_events_discovered: 38
  meta_json_files_written: 38
  delta_stream_path: "/data/events/discovery_delta.jsonl"
  daily_raw_archive_path: "/data/events/2026-04-19.jsonl"
  daily_raw_archive_size_mb: 33.7  # at H-009 close, growing ~12 MB/hour
  daily_raw_archive_growth_estimate_mb_per_day: 290  # uncompressed
  poll_interval_seconds: 60
  gateway_base: "https://gateway.polymarket.us"
  participant_type_confirmed: "PARTICIPANT_TYPE_TEAM or PARTICIPANT_TYPE_PLAYER (extractor handles both; observed events at H-009 use TEAM)"
  participant_type_prior_claim_corrected: true  # H-007 claimed PLAYER exclusively; corrected at H-009 V2
  sportradar_game_id_at_discovery: "empty until match approaches live start (observed: 0/38 populated at H-009 when no live matches)"

# ---- Open items requiring attention ----
open_items:
  tripwire_events_currently_open: 0
  python_version_pin_needed: false  # resolved H-005
  decision_journal_entries_needed: []  # all resolved at H-009
  raid_entries_by_severity:
    sev_8: 3   # R-008, R-009, I-012
    sev_7: 9   # R-010, I-003, I-004, I-005, I-006, I-007, I-008 (and 2 others)
    sev_6: 3   # I-009, I-010, I-011
    sev_5: 0
    sev_4_and_below: 2  # I-002 (severity 2), I-014 (severity 3)
    issues_open: 11   # I-002, I-003, I-004, I-005, I-006, I-007, I-008, I-009, I-010, I-011, I-012, I-014 minus I-013 (resolved H-009) and I-001 (resolved H-005)
    assumptions_unvalidated: 6  # A-001, A-002, A-003, A-004, A-006, A-008
  pending_operator_decisions: []
  phase_3_attempt_2_notes:
    - "Research-first discipline in force per D-016 commitment 2 and R-010 — no fabrication of URLs or module symbols"
    - "Sports WS endpoint and subscription format must be researched from Polymarket US / Sportradar documentation before any code references them (A-008)"
    - "Scope and sequence of first deliverable to be determined by operator at H-010 session open"
    - "Storage-growth runway (~35 days from 2026-04-19 at 290 MB/day) is a Phase 3 attempt 2 design consideration — R-012"
    - "sportradar_game_id populates closer to match start, not at discovery — capture worker design implication"

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
  - "Polymarket US authenticated API: api.polymarket.us (not used — no order placement yet)"
  - "Sport slug tennis confirmed with leagues [wta, atp]"
  - "Participant type may be TEAM or PLAYER; extractor handles both (corrected H-009)"
  - "sportradar_game_id populates at Polymarket's discretion, typically close to match start; empty at pure pre-match discovery"
  - "Daily raw-poll archive (/data/events/YYYY-MM-DD.jsonl) grows ~290 MB/day uncompressed; Phase 4 adds compression"
  - "Phase 3 attempt 1 (H-008) failed via fabricated Sports WS URL + fabricated DiscoveryConfig symbol; reverted at H-009 per D-016"
  - "Phase 3 attempt 2 begins from c63f7c1d-equivalent repo state"

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
    current_version: 7
    committed_to_repo: pending  # uploaded this session
    committed_session: H-009
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
    committed_to_repo: pending  # updated at H-009 with D-009 through D-017; uploaded this session
    pending_entries: []
  RAID_md:
    status: accepted
    committed_to_repo: pending  # updated at H-009; uploaded this session
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
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

Phase 2 remains complete and operational. At H-008, a Phase 3 implementation attempt was made that authored five new capture modules, a rewritten `main.py`, tests, and a pytest.ini. The attempt failed in live operation due to two fabrications: an external Sports WS endpoint URL that was not researched from documentation, and an internal `DiscoveryConfig` symbol that was assumed to exist in `discovery.py` but did not. H-008 did not produce a handoff; the operator deleted its transcript. H-009 executed an Option A1 revert per D-016, restoring `main` to a state byte-equivalent to commit `c63f7c1d` (the last pre-Phase-3 commit). The revert was validated through seven checks (V1–V7) covering file contents, git history, build logs, runtime logs, environment variables, disk mount, and live service behaviour. All seven passed.

The service at `pm-tennis-api.onrender.com` is running the reverted Phase 2 `main.py` at version `0.1.0-phase2`. The discovery loop polls `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. 38 active tennis events were discovered at the post-revert deploy (03:18:49Z, 2026-04-19); since then the set has been stable (`added=0 removed=0`) across observed poll cycles. 38 `meta.json` files exist on the persistent disk, unchanged since H-007. The discovery delta stream is being written to `/data/events/discovery_delta.jsonl`; raw poll snapshots are being appended to `/data/events/2026-04-19.jsonl`.

Phase 3 attempt 2 is the next work to do. It has not been scoped or sequenced in this session. H-009 deliberately produced no new Phase 3 code; its entire output is the revert transaction, documentation reconciliation, and session-close bundle.

### What changed in H-009

This session closed several governance gaps in one batch. The DecisionJournal was extended with nine new entries:

- D-009 through D-012 reconstructed from H-006 (H3 dropped; conviction + exit context ship together; pilot-then-freeze deferred; numbering corrected).
- D-013 through D-015 reconstructed from H-007 (Polymarket US gateway target; discovery-in-API architecture; tennis slug confirmed).
- D-016 records the Phase 3 attempt 1 failure, the Option A1 revert ruling, the tripwire classification, and the commitments for attempt 2.
- D-017 retroactively journals the H-006 v3→v4 plan revision decision, which had been informally referenced but never had its own canonical entry.

Each reconstructed entry carries both a decision date and a journaling date per Playbook §1.5.2.

RAID gained three new risks (R-010 fabrication, R-011 session-close discipline, R-012 storage growth runway), two new assumptions (A-008 research-first at Phase 3 attempt 2, A-009 participant-type corrected), and three new issues (I-012 attempt 1 failure, I-013 missed-handoff-at-H-008 — resolved same session — and I-014 the v4.1 plan-text patch).

STATE bumped from v6 to v7. Material changes:

- `state_document.current_version`: 6 → 7
- `state_document.last_updated_by_session`: H-007 → H-009
- `sessions.last_handoff_id`: H-007 → H-009
- `sessions.next_handoff_id`: H-008 → H-010
- `sessions.sessions_count`: 7 → 9 (counting H-008 as a session that occurred)
- `sessions.missed_handoffs`: new field, records H-008 absence and its remediation
- `phase.current`: phase-3-ready → phase-3-attempt-2-ready
- `phase.current_work_package`: restated to reference attempt 2
- `phase.phase_3_attempt_counter`: 2 (new field)
- `deployment.backend.live_deploy_commit`: 17f44eb1
- `deployment.backend.live_deploy_verified_session`: H-009
- `deployment.backend.persistent_disk_used_mb_at_h009_close`: 35
- `deployment.backend.notes`: updated to reference the revert
- `discovery.*`: several fields added or corrected (participant_type corrected; daily raw archive info added; sportradar_game_id observation added)
- `open_items.decision_journal_entries_needed`: emptied (all resolved)
- `open_items.phase_3_attempt_2_notes`: new field, gathers the scope-setting guidance for H-010
- `governance.research_first_discipline_for_external_apis`: true (new, per D-016)
- `architecture_notes`: several entries added for H-008 findings and H-009 corrections
- `phase_2_files.main_py`: updated with SHA, line count, restoration session

### The H-008 session — what we know and what we do not

H-008 occupied roughly the window 2026-04-19 02:11Z (first new-module commit on main) through 02:18Z (last new-module commit), plus some amount of in-session time before and after those commits. No handoff was produced; no STATE update happened; the chat transcript was deleted by the operator after the session went sideways.

Recoverable from the record: the code itself (present in git history on superseded commits 677016c1, a10486b3, 00282260, bab716ef, d319e09e, 8bdc3859, 40973377), the commit timestamps and messages, the order of commits, the ImportError evidence captured in Render logs at 03:10–03:13Z when the broken `main.py` was deployed against the reverted-in-progress filesystem, and the operator's stated root cause.

Not recoverable: the exact fabricated Sports WS URL, the URL(s) it was "corrected" to, the specific failure signatures beyond the ImportError, the reasoning chain at each in-session decision, and any intermediate diagnostic output.

D-016 names the failure pattern (fabrication of names without verification) and establishes the research-first discipline (R-010, A-008) to prevent it in attempt 2.

### Phase 3 attempt 2 starting conditions at H-010

When the next session opens, Claude will find:

- Repo on `main` at commit `17f44eb1` (or a newer scaffolding-files commit if this bundle lands before H-010 opens).
- Service running `main.py` at `0.1.0-phase2`, discovery loop healthy.
- Persistent disk with 38 `meta.json` files, discovery delta stream, daily raw-poll archive.
- Zero Phase 3 code on `main`.
- Research-first discipline in force.
- Scope and first-deliverable selection open for operator direction.

The Phase 3 exit criteria in STATE's `phase.next_gate_expected.triggers` remain as they were — attempt 2 aims at the same gate, not a different one.

### Validation posture going forward

At every session-open hereafter, the self-audit should include a specific check against the fabrication failure mode: if Claude has drafted code or is about to draft code that names any external endpoint, URL, module path, class name, or function signature that was not either (a) provided verbatim by the operator, (b) observed in an existing committed file, or (c) fetched from documentation in this same session, that is a tripwire requiring research or operator confirmation before proceeding.

---

*End of STATE.md — current document version: 7. Last updated: H-009.*
