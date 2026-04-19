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
    current_version: 8
    last_updated: 2026-04-19
    last_updated_by_session: H-010

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-ready
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). Research document v3 produced and accepted at H-010 (docs/clob_asset_cap_stress_test_research.md). Code turn deferred to H-011 pending operator rulings on Q4 (API credentials), Q5' (slug source), §12 (SDK vs hand-roll), and §6 meta.json survey authorization."
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
  last_handoff_id: H-010
  next_handoff_id: H-011
  sessions_count: 10
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
  decision_journal_entries_needed: []  # all resolved at H-009 and H-010
  raid_entries_by_severity:
    sev_8: 3   # R-008, R-009, I-012
    sev_7: 9   # R-010, I-003, I-004, I-005, I-006, I-007, I-008 (and 2 others)
    sev_6: 3   # I-009, I-010, I-011
    sev_5: 0
    sev_4_and_below: 3  # I-002 (severity 2), I-014 (severity 3), I-015 (severity 3)
    issues_open: 13   # 15 total issues; I-001 resolved H-005 and I-013 resolved H-009
    assumptions_unvalidated: 6  # A-001, A-002, A-003, A-004, A-006, A-008
  pending_operator_decisions:
    - id: POD-H010-Q4
      surfaced_session: H-010
      surfaced_in: "docs/clob_asset_cap_stress_test_research.md v2 §7 Q4, re-surfaced v3 §9"
      question: "API credential status for Polymarket US (polymarket.us/developer). Do credentials exist (a), not exist (b), or should a scoped stress-test key be generated (c)?"
      blocks: "All stress-test code — authentication is required for Markets WebSocket per docs/clob_asset_cap_stress_test_research.md v3 §4.2"
      status: open
    - id: POD-H010-Q5p
      surfaced_session: H-010
      surfaced_in: "docs/clob_asset_cap_stress_test_research.md v3 §7 Q5'"
      question: "Slug source for the stress test. Options: (a') api.polymarket.us — clean test, gateway bridge not verified. (b') gateway.polymarket.us slugs — tests gateway-to-api bridge simultaneously. (c') hybrid with single-slug probe first. Claude recommendation: (c')."
      blocks: "Slug-handling layer of stress-test code"
      status: open
    - id: POD-H010-§12
      surfaced_session: H-010
      surfaced_in: "docs/clob_asset_cap_stress_test_research.md v3 §12"
      question: "SDK vs hand-rolled WebSocket client for stress test. Options: (a) polymarket-us SDK, (b) hand-rolled, (c) hybrid. Claude recommendation: (a) for stress test, defer long-term decision. Connected to Q4 and Q5' — resolve together."
      blocks: "Structure of all stress-test code"
      status: open
    - id: POD-H010-§6-survey
      surfaced_session: H-010
      surfaced_in: "docs/clob_asset_cap_stress_test_research.md v1/v2/v3 §6"
      question: "Authorization to walk operator through the Render-shell meta.json survey that produces current slug-count baseline. Operator-executed via Render shell; Claude provides commands and reads output."
      blocks: "Concrete 'N' value for stress-test sweeps in §7 Q3"
      status: open
  phase_3_attempt_2_notes:
    - "Research-first discipline in force per D-016 commitment 2 and R-010 — no fabrication of URLs or module symbols"
    - "H-010: research document produced at docs/clob_asset_cap_stress_test_research.md, three versions this session (v1, v2, v2.1, v3). v3 accepted."
    - "Sports WS endpoint and subscription format research deferred to Phase 3 attempt 2 Sports WS deliverable; not in scope for the asset-cap stress test deliverable"
    - "H-010 established (cited in v3): Markets WebSocket endpoint = wss://api.polymarket.us/v1/ws/markets; auth = Ed25519 three-header (X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature); subscription unit = market slug; wire format = camelCase enum-string (confirmed via SDK README response-side evidence); per-subscription cap = 100 slugs; concurrent-connection and rate limits not documented"
    - "Storage-growth runway (~35 days from 2026-04-19 at 290 MB/day) is a Phase 3 attempt 2 design consideration — R-012"
    - "sportradar_game_id populates closer to match start, not at discovery — capture worker design implication"
    - "Four pending operator decisions block the code turn: POD-H010-Q4, POD-H010-Q5p, POD-H010-§12, POD-H010-§6-survey. See pending_operator_decisions."

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
  - "Polymarket US Markets WebSocket = wss://api.polymarket.us/v1/ws/markets (H-010, cited in docs/clob_asset_cap_stress_test_research.md v3 §4.1). Auth: three headers X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature; signature over timestamp+'GET'+path; Ed25519; 30-sec clock window."
  - "Polymarket US Markets WebSocket subscription unit: market slug. Cap: 100 slugs per subscription (H-010, v3 §4.4). Concurrent-connection and rate limits: not documented on docs.polymarket.us (H-010, v3 §4.5 — the empirical gap that justifies the stress test)."
  - "Polymarket US wire format for Markets WebSocket: camelCase with enum-string subscription types (e.g., requestId, subscriptionType='SUBSCRIPTION_TYPE_MARKET_DATA', marketSlugs). Resolved H-010 via SDK README response-side evidence; Overview page's snake_case prose is stale."
  - "api.polymarket.us shares a single slug namespace across REST (markets.retrieve_by_slug, markets.book) and WebSocket (subscribe slug list). Gateway-to-api slug identity still unverified at H-010 close — open as POD-H010-Q5p."
  - "Polymarket US Python SDK exists at github.com/Polymarket/polymarket-us-python (package polymarket-us, Python 3.10+). SDK-vs-hand-roll decision open as POD-H010-§12."

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
    current_version: 8
    committed_to_repo: pending  # v8 uploaded this session
    committed_session: H-010
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
    committed_to_repo: pending  # D-018 through D-022 added this session; uploaded
    committed_session: H-010
    pending_entries: []
  RAID_md:
    status: accepted
    committed_to_repo: pending  # I-015 and D-018–D-022 added this session; uploaded
    committed_session: H-010
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  clob_asset_cap_stress_test_research_md:
    status: accepted
    path: "docs/clob_asset_cap_stress_test_research.md"
    current_version: 3
    committed_to_repo: pending  # produced this session; uploaded
    committed_session: H-010
    note: "Phase 3 attempt 2 first-deliverable research doc per D-018 and D-019. v1 → v2 → v2.1 → v3 all produced this session."
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

Phase 2 remains complete and operational. The service at `pm-tennis-api.onrender.com` continues to run the reverted Phase 2 `main.py` (SHA `ceeb5f29…`, 2,989 bytes, 87 lines). Discovery loop polls `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. No Phase 3 code exists on `main`.

H-010 executed Phase 3 attempt 2's research-first opening move per D-018 and D-019. The operator-ruled scope menu from H-010 produced five decisions (D-018 through D-022) covering first deliverable (asset-cap stress test), research form (standalone doc → review → code), definition of done, testing posture (unit + live smoke), and commit cadence. Four versions of the asset-cap stress test research document were produced this session: v1 (initial), v2 (§4 answered via Polymarket US docs fetch), v2.1 (§4.3 verbatim excerpt verification, §4.3.1 case-style inconsistency surfacing), v3 (SDK README read, §4.3.1 resolved, §4.7 partially resolved, §12 surfaced). v3 is accepted. No code has been written.

What the H-010 research established (all cited in `docs/clob_asset_cap_stress_test_research.md` v3, all from `docs.polymarket.us` per D-013): Markets WebSocket is `wss://api.polymarket.us/v1/ws/markets`. Authentication is Ed25519 with three handshake headers (X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature) signing `timestamp + "GET" + path`, 30-second clock window. Subscription unit is market slug, not the side.identifier that `discovery.py` line 37 comment suggests. Wire format is camelCase with enum-string subscription types; the Overview page's snake_case+integer example is stale. Per-subscription cap is 100 slugs. Concurrent-connection and rate limits are not documented — that is the empirical gap the stress test exists to characterize.

What the research did not establish: whether gateway-sourced slugs (what Phase 2 meta.json currently contains) are identical to api.polymarket.us-accepted slugs. The SDK read revealed this was a bridge question the SDK doesn't answer directly, and surfaced an alternative architecture (stress-test-from-api) that avoids the bridge entirely. This is open as POD-H010-Q5p.

Four pending operator decisions block the code turn: Q4 (API credential status), Q5p (slug source for the test), §12 (SDK vs hand-rolled WebSocket client), and §6 meta.json survey authorization. These are the first business of H-011.

Two plan-text patches accumulated this session beyond I-014: v4.1-candidate-2 (§5.4 / §11.3 revise the 150-asset-cap phrasing per I-015) and v4.1-candidate-3 (discovery.py line-37 / line-120 code comments correct the subscription-unit description per §11 point 3 of the research doc). All three are tracked in `pending_revisions` and will be bundled when the next plan revision is cut.

### What changed in H-010

DecisionJournal: D-018 through D-022 added at the top of file (Rulings 1–5 from the H-010 scope menu).

RAID: new issue I-015 (150-asset-cap inheritance finding, severity 3). Five new decisions in the RAID decisions table mirror the DecisionJournal additions.

STATE bumped from v7 to v8. Material changes: version and session counters advanced; three new pending_operator_decisions (Q4, Q5', §12, §6 survey); `phase_3_attempt_2_notes` extended with H-010 research progress; `scaffolding_files` bumped for the three H-009 bundle entries that actually landed (STATE/DecisionJournal/RAID `committed_to_repo: pending → true` against H-009) plus a new entry for the research document; `architecture_notes` extended with what H-010 established about the Polymarket US API surface; two new `pending_revisions` entries (v4.1-candidate-2 for I-015, v4.1-candidate-3 for the discovery.py comment).

### H-011 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with H-010 bundle landed (STATE v8, DecisionJournal with D-018–D-022, RAID with I-015 and D-018–D-022, research document v3, handoff H-010).
- Service running `main.py` at `0.1.0-phase2`, discovery loop healthy. 38 active tennis events.
- Zero Phase 3 code on `main`.
- Research-first discipline in force per D-016 and D-019.
- Four pending operator decisions listed in `pending_operator_decisions`: POD-H010-Q4, POD-H010-Q5p, POD-H010-§12, POD-H010-§6-survey. First business of H-011 is operator rulings on these.
- The Phase 3 exit criteria in `phase.next_gate_expected.triggers` remain unchanged.

### Validation posture going forward

Unchanged from H-009. At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode: code drafted in the session that names any external endpoint, URL, module path, class name, or function signature must trace to (a) operator-provided material, (b) an existing committed file, or (c) documentation fetched in this same session. H-010 exercised this discipline: every external claim in the research document is cited with URL and excerpt; no code was written. The self-audit for H-011 will include a specific check that code, when it is drafted, continues this discipline.

---

*End of STATE.md — current document version: 8. Last updated: H-010.*
