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
      - id: v4.1-candidate-4
        sections: ["Section 1.5.3", "Section 1.5.4"]
        summary: "Plan §1.5.3 and §1.5.4 revision candidate to reflect D-029 — Claude pushes to `claude-staging` branch, operator merges to `main`. D-029 landed at H-016 as a DJ entry (operator ruled 'PAT, no expiration'). Revised text: §1.5.3 'The operator shall: [...] review and merge Claude's pushes to the claude-staging branch at the operator's cadence, per Playbook §13; [...]'; §1.5.4 addition 'Claude pushes code and documentation changes to the claude-staging branch using a non-expiring GitHub PAT stored as a Render env var. Claude does not merge to main, does not force-push, does not push to any branch other than claude-staging.' Apply under Playbook §12 at next plan-revision cadence alongside -1, -2, -3."
  state_document:
    current_version: 14
    last_updated: 2026-04-19
    last_updated_by_session: H-016

# ---- Phase and work package ----
phase:
  current: phase-3-attempt-2-probe-executed
  current_work_package: "Phase 3 attempt 2 — asset-cap stress test (D-018). H-016 completed: (1) helper-snippet flip landed (`src/stress_test/list_candidates.py` + 20 tests; RB-002 §5.1 and README updated) in commit d7b2bd2; (2) RAID I-016 investigated against a live gateway payload (event 9471 meta.json read in pm-tennis-api Shell) and fixed per D-028 — discovery.py line 328 now sources event_date from startDate[:10], and slug_selector._passes_date_filter falls back to start_date_iso[:10] for ~116 historical meta.json files; committed in d7b2bd2 (code + RAID) and 83c0bf8 (D-028); (3) live probe executed in pm-tennis-stress-test Shell against gateway-sourced slug `aec-wta-paubad-julgra-2026-04-21` (event 9471) — classification accepted, first_message_latency_seconds=1.15, one market_data message received, D-025 hybrid-probe-first question resolved: gateway-to-api slug bridge is confirmed working; main sweeps may use either slug source with api-sourced as default; (4) §14 probe-outcome addendum written into docs/clob_asset_cap_stress_test_research.md in commit e28e390. H-017 picks up: (a) main sweeps per §7 Q3=(c) (1/2/5/10 subscriptions × 100 placeholder slugs × 1/2/4 concurrent connections); (b) placeholder-slug generation strategy decision informed by probe evidence; (c) §16 main-sweeps addendum; (d) RAID I-017 disposition (two pre-existing TestVerifySportSlug failures); (e) stale-file cleanup (3 artifacts inadvertently committed at H-016); (f) D-029 deployment-procedure revision (drafts produced this session; deferred pending operator ruling on auth mechanism)."
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
  last_handoff_id: H-016
  next_handoff_id: H-017
  sessions_count: 16
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
  meta_json_files_written: 126  # H-016 post-redeploy observation at 2026-04-19T22:18:18Z; up from 116 at H-015. Events 9301-9471. Events 9301 through ~9466-9471 were discovered pre-H-016-fix (all have empty event_date — the I-016 symptom; slug_selector now handles via start_date_iso fallback per D-028). Events discovered after commit d7b2bd2 deploy will have correct event_date.
  current_event_count: 126  # H-016 probe-time snapshot
  current_slug_count: 126  # one moneyline per event, distribution uniform per H-012 D-026 survey
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
    sev_6: 3   # I-009, I-010, I-011 (I-016 resolved H-016 per D-028)
    sev_5: 0
    sev_4_and_below: 4  # I-002 (severity 2), I-014 (severity 3), I-015 (severity 3), I-017 (severity 4, added H-016)
    issues_open: 14   # 17 total issues; I-001 resolved H-005, I-013 resolved H-009, I-016 resolved H-016; I-017 added H-016
    assumptions_unvalidated: 6  # A-001, A-002, A-003, A-004, A-006, A-008
  pending_operator_decisions: []  # POD-H016-deployment-flow resolved at session close via D-029 — operator ruled 'PAT, no expiration.' D-029 landed as a DJ entry; Playbook §13 added.
  resolved_operator_decisions_current_session:
    # Pruned to current-session (H-016) entries only per the H-014-settled
    # stricter-reading convention. H-015 entries are preserved in
    # Handoff_H-015 §2/§3 and STATE v13's prose; this field reflects only
    # the current session's in-session rulings.
    - id: H-016-helper-snippet-flip
      resolved_session: H-016
      resolved_by_decision: in-session ruling (not a DJ entry)
      resolution_summary: "Operator ruled 'resolve shell errors' at session open — affirmative on the helper-snippet flip. New committed module `src/stress_test/list_candidates.py` replaces the pasted snippet in RB-002 §5.1 that failed twice at H-015. 20 new tests. No Phase-2 touch."
    - id: H-016-I-016-fix-authorization
      resolved_session: H-016
      resolved_by_decision: operator ruling mid-session (culminated in DJ entry D-028)
      resolution_summary: "Operator authorized Fix C — both discovery.py event_date extraction AND slug_selector fallback — with 'thorough documentation.' Fix applied via D-028 (full DJ entry). Phase-2 code touched per D-016 commitment 2 with explicit authorization. Commits: d7b2bd2 (code), 83c0bf8 (D-028)."
    - id: H-016-commit-as-one-bundle
      resolved_session: H-016
      resolved_by_decision: operator ruling (not a DJ entry)
      resolution_summary: "Operator ruled 'one commit' for the H-016 bundle (helper-snippet flip + I-016 fix). Landed as commit d7b2bd2. In practice, the DJ (D-028) was omitted from that first commit and added in follow-up commit 83c0bf8; the stale artifacts `CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, and `D-028-entry-to-insert.md` were inadvertently committed and remain in the repo until an H-017 cleanup commit."
    - id: H-016-commit-first-then-probe
      resolved_session: H-016
      resolved_by_decision: operator ruling (not a DJ entry)
      resolution_summary: "Operator ruled 'Commit the bundle and then run the probe in this session' — expanding H-016 scope beyond the H-015 handoff's conservative suggestion. Execution: commit bundle → wait for Render redeploy → slug selection → probe → §14 addendum."
    - id: H-016-publish-convention-flip
      resolved_session: H-016
      resolved_by_decision: in-session note (Claude-authored commitment; not a DJ entry)
      resolution_summary: "Mid-session, Claude produced `D-028-entry-to-insert.md` as a splice-into-existing-file artifact rather than a full replacement of DecisionJournal.md. Operator surfaced this as a process deviation: 'for every deploy in other sessions I've ALWAYS been instructed to replace.' Claude acknowledged the error and committed going forward to the 'always replace, never patch' convention. Logged as commitment for future sessions; baked into D-029 as commitment 3."
    - id: H-016-deployment-flow-PAT-no-expiration
      resolved_session: H-016
      resolved_by_decision: operator ruling at session close (formalized as DJ entry D-029)
      resolution_summary: "Operator ruled 'PAT, no expiration' at session close. D-029 landed as a DJ entry naming a non-expiring fine-grained GitHub PAT scoped to peterlitton/pm-tennis repository, stored as a Render env var. Playbook §13 (staging-push-and-merge ritual) added. Plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4 in pending_revisions. Implementation sequencing: operator generates PAT → stores in Render env var → creates claude-staging branch → reports back at H-017 open. Claude does a test push to staging at H-017 before first real use."
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
    - "H-016 open: full reading completed per handoff + operator direction (Handoff_H-015 + addendum, STATE v13, Orientation, Playbook §§1-5 + §§9-12, RAID including I-016, DJ D-016 through D-027, discovery.py extraction + TennisEventMeta + _check_duplicate_players, slug_selector._passes_date_filter, probe.py header/citations, RB-002 in full). Retrospective fabrication check: git log confirmed H-015 commit bundle integrity (402c05e + 274cd09); I-016 claims against discovery.py line 328 and slug_selector lines 142-156 verified against on-disk code; 38/38 baseline stress-test tests pass against pinned deps in clean venv."
    - "H-016 helper-snippet flip: per operator ruling 'resolve shell errors' at session open, flipped RB-002 §5.1 pasted snippet to committed module src/stress_test/list_candidates.py. 20 new unit tests added. RB-002 §5.1 and src/stress_test/README.md updated to reference the new invocation. No Phase-2 touch. Landed in commit d7b2bd2."
    - "H-016 I-016 investigation: operator-executed in pm-tennis-api Render Shell. Read /data/matches/9471/meta.json (event 9471 = WTA Paula Badosa vs Julia Grabher 2026-04-21). Confirmed: gateway response has NO eventDate key; canonical date source is startDate as full ISO timestamp (2026-04-21T08:00:00Z); start_date_iso is populated correctly; event_date is empty. H-015-Claude's inferential hypothesis confirmed. ~116 historical meta.json files all have same shape (empty event_date + populated start_date_iso)."
    - "H-016 I-016 fix per D-028 (Fix C, operator-authorized 'c with thorough documentation'): (a) discovery.py line 328 changed from event.get('eventDate') to event.get('startDate')[:10] with comprehensive comment citing D-028 + I-016; (b) slug_selector._passes_date_filter modified to fall back to start_date_iso[:10] when event_date empty/malformed (handles the ~116 historical meta.json files); (c) test fixture in tests/test_discovery.py corrected to remove false eventDate key (was silently masking the bug); (d) 9 new tests added (3 regression in TestParseEvent + 6 fallback in test_stress_test_slug_selector); (e) subsidiary finding: _check_duplicate_players silently broken in production since H-007 due to empty event_date short-circuit on line 424 — restored automatically by the fix going forward, historical files not backfilled. Landed in commits d7b2bd2 (code + RAID + manifest artifacts) and 83c0bf8 (DecisionJournal with D-028)."
    - "H-016 subsidiary RAID find: I-017 added (sev 4) for two pre-existing TestVerifySportSlug test failures — baseline tests expected SystemExit but production code raises RuntimeError. Existed on main at H-016 open; not introduced by H-016 work. Out of scope for D-028; H-017 disposition."
    - "H-016 live probe execution per D-025 + D-027: pm-tennis-api auto-deployed after commit; 126 active tennis events at probe time (up from 116 at H-015). Slug selected via python -m src.stress_test.list_candidates: event_id 9471, slug aec-wta-paubad-julgra-2026-04-21. Probe invoked in pm-tennis-stress-test Shell: python -m src.stress_test.probe --probe --slug=aec-wta-paubad-julgra-2026-04-21 --event-id=9471. Outcome: classification=accepted, connected=true, subscribe_sent=true, first_message_latency_seconds=1.15, message_count_by_event={market_data:1}, error_events=[], close_events=[], exception_type=''. D-025 hybrid-probe-first branch: main sweeps may use either gateway-sourced or api-sourced slugs with api-sourced as default."
    - "H-016 §14 addendum: full probe-outcome writeup added to docs/clob_asset_cap_stress_test_research.md as §14 (reserved slot populated). 7 subsections: H-015 deferral rationale, probe input, probe outcome JSON verbatim, classification + D-025 branch selected, H-016 work summary, H-017 pickup, what §14 does not change. Landed in commit e28e390."
    - "H-016 commit-flow deviations: (a) first H-016 commit d7b2bd2 omitted DecisionJournal.md (operator error) and included 3 stale artifacts (COMMIT_MANIFEST.md, CHECKSUMS.txt, D-028-entry-to-insert.md); (b) follow-up commit 83c0bf8 added the DJ; (c) stale artifacts remain in repo pending H-017 cleanup. Claude's Process error: produced D-028-entry-to-insert.md as splice-into-existing-file instead of complete DJ replacement — deviation from established 'always replace' convention. Operator surfaced this explicitly; Claude committed to 'always replace, never patch' convention going forward; baked into D-029 draft as commitment 3."
    - "H-016 D-029 deployment-procedure revision landed. Operator ruled 'PAT, no expiration' at session close. Commitment: Claude pushes code/docs to `claude-staging` branch using a non-expiring fine-grained GitHub PAT scoped to peterlitton/pm-tennis, stored as a Render env var; operator merges staging to main as the single human-in-the-loop gate. Playbook §13 (staging-push-and-merge ritual) added with 8 failure modes. Plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4. Implementation sequencing: operator generates PAT with no expiration → stores in Render env var → creates claude-staging branch → reports back at H-017 open → Claude test-pushes before first real use. First real use: H-017 non-trivial commit."
    - "H-016 close: DJ at 29 entries (D-028 and D-029 added). RAID: 14 open issues (I-016 closed, I-017 opened). Phase 3 attempt 2 stress-test probe COMPLETE per D-025 commitments 1-4. Main sweeps remain for H-017. Governance: D-029 landed (staging-push-and-merge workflow). Three stale files need cleanup at H-017 (separate from D-029)."

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
    current_version: 14
    committed_to_repo: pending  # v14 produced this session
    committed_session: H-016
    note: "v14 reflects H-016 work: helper-snippet flip (d7b2bd2), RAID I-016 investigated and fixed per D-028 (d7b2bd2 + 83c0bf8), live probe executed with classification=accepted, §14 probe-outcome addendum written (e28e390), I-017 added (sev 4, TestVerifySportSlug drift), D-029 deployment-flow revision landed at session close (operator ruled 'PAT, no expiration'; Playbook §13 added; v4.1-candidate-4 queued). 29 DJ entries at close."
  Orientation_md:
    status: accepted
    committed_to_repo: true
  Playbook_md:
    status: accepted
    committed_to_repo: pending  # §13 staging-push-and-merge ritual added this session per D-029
    committed_session: H-016
    note: "§13 (staging-push-and-merge ritual) added at H-016 per D-029. §§1-12 unchanged. Table of rituals updated. Footer updated. Preserves all §§1-12 original content verbatim."
  SECRETS_POLICY_md:
    status: accepted
    committed_to_repo: true
  DecisionJournal_md:
    status: accepted
    committed_to_repo: pending  # D-029 added this session; D-028 landed earlier this session in commit 83c0bf8
    committed_session: H-016
    pending_entries: []
  RAID_md:
    status: accepted
    committed_to_repo: true  # updated at H-016: I-016 resolved per D-028, I-017 added
    committed_session: H-016
    note: "H-016: I-016 marked Resolved with reference to D-028; I-017 added (sev 4, two pre-existing TestVerifySportSlug failures surfaced during H-016 testing); header 'Last updated' bumped to H-016 close; footer changelog updated. Landed in commit d7b2bd2."
  PreCommitmentRegister_md:
    status: accepted
    committed_to_repo: true
  clob_asset_cap_stress_test_research_md:
    status: accepted
    path: "docs/clob_asset_cap_stress_test_research.md"
    current_version: 4
    committed_to_repo: true  # §14 H-016 addendum landed in e28e390
    committed_session: H-016
    renamed_session: H-011
    note: "v4 remains the current version. §13 added at H-012 (H-012 rulings + survey); §15 additive added at H-014 (H-013 code-turn-research resolutions + D-027 supersession + scaffolding note + stale-artifact-corrected note + H-015 forward look); §14 added at H-016 as the probe-outcome addendum (reserved slot populated). §14 content: the D-025 hybrid-probe-first probe ran and was classified accepted; gateway-to-api slug bridge confirmed working. Document now complete through §15; no sections reserved. v5 bump was not needed — additive-to-v4 convention preserved."
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
    committed_to_repo: true  # landed in H-015 commit 274cd09
    committed_session: H-015
  Handoff_H016_md:
    status: accepted
    path: "Handoff_H-016.md"
    committed_to_repo: pending  # produced this session
    committed_session: H-016
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

Phase 2 remains complete and operational — with a material fix landed this session. The service at `pm-tennis-api.onrender.com` continues to run the Phase 2 `main.py` unchanged (SHA `ceeb5f29…`, 2,989 bytes, 87 lines), but `src/capture/discovery.py` line 328 was modified at H-016 per D-028 to fix RAID I-016 (empty `event_date` extraction). Discovery loop continues polling `gateway.polymarket.us/v2/sports/tennis/events` every 60 seconds. At the post-H-016-deploy observation (2026-04-19T22:18Z), 126 active events were in discovery (up from 116 at H-015 and 74 at H-012). `_write_meta` immutability holds — historical meta.json files written with empty `event_date` remain on disk; slug_selector's fallback (also landed at H-016) handles them transparently via the populated `start_date_iso` field.

**Phase 3 attempt 2 stress-test service remains live.** `pm-tennis-stress-test` at `https://pm-tennis-stress-test.onrender.com` verified at H-014, self-check green, H-016 executed the first live probe against it successfully.

**The D-025 hybrid-probe-first research question is answered: gateway-to-api slug bridge confirmed working.** H-016 ran the probe end-to-end with gateway-sourced slug `aec-wta-paubad-julgra-2026-04-21` (event 9471, WTA). Classification: `accepted`. First message latency 1.15 seconds. One `market_data` message received in the 10-second window. Zero errors, zero close events, no exceptions. Per D-025 commitment language, main sweeps (H-017 scope) may use either gateway-sourced or api-sourced slugs with api-sourced as the default (cleanest; via SDK's `client.markets.list()`).

**RAID I-016 resolved via D-028.** The investigation read a live gateway payload from `/data/matches/9471/meta.json` in the pm-tennis-api Shell, confirming that the gateway response has NO `eventDate` key — the canonical date source is `startDate` (full ISO timestamp). Fix C applied (both `discovery.py` forward-going fix AND `slug_selector.py` backward-compatible fallback). 9 new tests added. Subsidiary finding: `_check_duplicate_players` has been silently broken in production since H-007 (always returned `False` due to the empty-event_date short-circuit); restored automatically going forward by the fix, historical 116+ files retain stale `duplicate_player_flag=False`.

**RAID I-017 added (sev 4).** Two pre-existing test failures in `TestVerifySportSlug` surfaced during H-016 testing: both expect `SystemExit` but production code raises `RuntimeError`. Not introduced by H-016 work; existed on main at session open. Out of scope for D-028; H-017 disposition.

**D-029 deployment-procedure revision landed at H-016 close.** Multiple recurring failure modes in the current drag-and-drop commit workflow motivated the design (H-014 missed STATE v11, H-015 bracketed-paste failures, H-016 missing DJ + stale artifacts + Claude's splice-file process deviation). Operator ruled "PAT, no expiration" at session close. Commitment: Claude pushes code and documentation to the `claude-staging` branch using a non-expiring fine-grained GitHub PAT scoped to the repository, stored as a Render environment variable; operator merges staging → main as the single human-in-the-loop gate. Playbook §13 (the staging-push-and-merge ritual, 8 failure modes enumerated) was added. Plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4 for next plan-revision cadence per Playbook §12. **Implementation:** operator generates PAT → stores in Render env var → creates claude-staging branch → reports back at H-017 open → Claude test-pushes before first real use.

**D-027 remains active.** D-025 commitment 1 is superseded; commitments 2/3/4 stand. D-024 commitment 1 (pm-tennis-api/requirements.txt untouched) is actively reinforced. D-020/Q2=(b) isolation is preserved. D-028 is new at H-016 (Phase-2 fix + slug_selector fallback). D-029 is new at H-016 (deployment-procedure revision; staging-push-and-merge workflow).

**What the H-017 session inherits:**

- Repo with the full H-013 + H-014 + H-015 + H-016 bundle: STATE v14 (this doc), DJ at 29 entries (D-028 + D-029 added), Handoff_H-016, RAID with I-016 resolved + I-017 new (14 open issues, 17 total), Playbook with §13 added.
- Three stale artifacts in repo root from the H-016 commit that need cleanup: `CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, `D-028-entry-to-insert.md`.
- Live `pm-tennis-api` service with I-016 fix deployed; 126+ events at H-016 close; event_date now correctly populated for newly-discovered events.
- Live `pm-tennis-stress-test` service; self-check green; one live probe successfully executed and classified accepted.
- D-029 deployment-procedure revision LANDED: operator-ruled 'PAT, no expiration'. Awaiting operator-side setup (generate PAT → store in Render env var → create claude-staging branch → report at H-017 open). First real staging-push use at H-017 non-trivial commit.
- §14 of research-doc populated; §16 is the next natural slot for main-sweeps addendum.
- Four plan-text revisions queued in STATE `pending_revisions`: v4.1-candidate (Section 5.6 baseline path), -2 (Section 5.4 and §11.3 asset-cap language), -3 (discovery.py comments), -4 (§1.5.3/§1.5.4 for D-029).
- Zero pending operator decisions.
- Seven consecutive sessions (H-010 through H-016) closed without firing a tripwire or invoking OOP.

### What changed in H-016

**Phase 3 attempt 2 stress-test probe COMPLETE.** The first Polymarket US API Markets WebSocket live-network call in the project's history executed cleanly. D-025 hybrid-probe-first question answered. Main sweeps remain for H-017; the probe itself is done.

**RAID I-016 resolved.** D-028 landed with Fix C — forward-going fix to discovery.py AND backward-compatible fallback in slug_selector. 9 new tests. Phase-2 code modified with explicit operator authorization per D-016 commitment 2. Subsidiary finding: `_check_duplicate_players` was silently broken in production since H-007; automatic restoration for new events going forward.

**Helper-snippet flip landed.** `src/stress_test/list_candidates.py` as a committed module replaces the multi-line pasted snippet from RB-002 §5.1 that failed twice at H-015. 20 new unit tests. Includes `--show-rejected` diagnostic mode that would have surfaced I-016 more directly had it existed at H-015.

**§14 probe-outcome addendum written to research-doc.** The reserved slot is populated; research-doc is now complete through §15 with no reserved sections.

**DJ +2: D-028 and D-029 added.** Counter now 29. D-028 is the RAID I-016 fix with thorough documentation per operator direction. D-029 is the deployment-procedure revision with operator ruling 'PAT, no expiration' — Playbook §13 added, plan §1.5.3/§1.5.4 revision queued as v4.1-candidate-4. RAID I-017 added (sev 4, pre-existing TestVerifySportSlug failures out of D-028 scope).

**STATE bumped v13 → v14.** Material changes: `phase.current` bumped from `phase-3-attempt-2-probe-blocked-on-calendar` to `phase-3-attempt-2-probe-executed`; `phase.current_work_package` rewritten to reflect H-016 completions and H-017 pickups; sessions_count 15→16; raid_entries_by_severity reshuffled (sev_6 4→3, sev_4_and_below 3→4, issues_open 14→14 with one close + one open); pending_operator_decisions empty (POD-H016-deployment-flow resolved via D-029 landing); resolved_operator_decisions_current_session pruned per settled convention and replaced with H-016's 6 in-session rulings; phase_3_attempt_2_notes +10 entries; pending_revisions +1 (v4.1-candidate-4 for D-029); scaffolding_files: H-015 entries flipped pending→true with commit SHAs, DecisionJournal and RAID and research-doc marked committed_session=H-016, Playbook flipped to pending (D-029 §13 addition), STATE v14 + Handoff_H-016 added as pending; discovery counts refreshed (74→126).

**Tripwires: none fired.** Zero OOP events. Seven consecutive sessions (H-010 through H-016) with clean discipline.

**Process finding — Claude-authored deviation surfaced mid-session:** Claude produced `D-028-entry-to-insert.md` as a splice-into-existing-file artifact rather than a full replacement of DecisionJournal.md, deviating from the established "Claude produces complete replacements; operator uploads" convention. Combined with the drag-and-drop workflow's silent-missing-file failure mode (operator upload missed the spliced DJ, included 3 stale reference artifacts), this produced a partially-wrong first H-016 commit (d7b2bd2) that required a follow-up commit (83c0bf8) to remediate. Operator surfaced the process deviation explicitly. Claude committed to 'always replace, never patch' convention going forward and baked it into the D-029 draft (commitment 3). No governance artifact change needed beyond D-029 itself; the drafts capture the failure mode and its remediation.

### H-017 starting conditions

When the next session opens, Claude will find:

- Repo on `main` with the full H-016 bundle: STATE v14, DJ at 28 entries (last D-028), Handoff_H-016, RAID with I-016 resolved + I-017 new, research-doc with §14 populated, `src/stress_test/list_candidates.py` module, 9 new tests for I-016 regression + fallback, 20 new tests for list_candidates.
- Three stale artifacts in repo root needing cleanup: `CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, `D-028-entry-to-insert.md`.
- `pm-tennis-api` service running with I-016 fix deployed; 126+ events discovered; event_date correctly populated for new events.
- `pm-tennis-stress-test` service live with credentials; one successful probe in its history.
- One pending operator decision: POD-H016-deployment-flow (D-029 authentication mechanism choice).
- §16 as the natural next section of research-doc for main-sweeps addendum.
- Four plan-text pending revisions in STATE (v4.1-candidate-4 conditional on D-029).
- Research-first discipline in force per D-016, D-019.
- Pruning convention for `resolved_operator_decisions_current_session`: stricter reading, settled.
- Drag-and-drop commit workflow with 'always replace, never patch' discipline in force until D-029 lands.

### Validation posture going forward

At every session-open hereafter, the self-audit includes a specific check against the fabrication failure mode. At H-017 open, the check has four application surfaces:

- **Retrospective for H-016 artifacts.** STATE v14, Handoff_H-016, DecisionJournal D-028, RAID I-016/I-017 updates, `list_candidates.py`, the discovery.py/slug_selector.py fixes, the research-doc §14 addendum. Spot-check that claims about commit SHAs, line numbers, and test counts match on-disk reality. H-016 artifacts are unusually rich; focus on the highest-leverage items (the discovery.py line 328 fix, the D-028 entry text, the §14 probe outcome verbatim JSON).

- **Preventive for main sweeps code-turn.** Main sweeps (§7 Q3=(c), the H-017 scope) is the first net-new SDK surface beyond probe.py's citation block [A]-[D]. Fabrication-risk surface: `client.markets.list()` and multi-subscription semantics on `markets_ws`. Re-fetch `github.com/Polymarket/polymarket-us-python` README at code-turn time per H-014-Claude and H-015-Claude emphatic notes. No exceptions.

- **Preventive for D-029 implementation.** If the authentication mechanism is resolved at H-017 open and D-029 implementation begins, re-verify the MCP registry for GitHub (may have been added since H-016 search) and re-read the current Playbook/plan text before editing. The draft governance artifacts are starting points, not commit-ready files — they should be refined against the current state of the governance documents at H-017 open, not treated as frozen.

- **Preventive for I-017 disposition.** Small code fix either side (update tests to expect RuntimeError, OR update code to raise SystemExit). Read the actual verify_sport_slug function at H-017 before deciding which side to fix; don't rely on I-017's description as the full picture.

Values of `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` must never enter the chat transcript — they are set via Render dashboard only. H-016 exercised the credential path during the probe; discipline held (credentials never entered chat, all auth done via the SDK's internal handling of env-var-named credentials per D-023).

---

*End of STATE.md — current document version: 14. Last updated: H-016.*
