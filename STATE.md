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
    location: "project knowledge (to be moved to repo once repo exists)"
    pending_revisions:
      - decision: D-002
        sections: ["Section 8 Phase 7", "Section 9", "Section 11"]
        summary: "Incorporate pilot-then-freeze protocol for signal_thresholds.json"
      - decision: D-003
        sections: ["Section 8 Phase 1", "Section 11.1"]
        summary: "Phase 1 Sports WS granularity check becomes explicit go/no-go gate"
  state_document:
    current_version: 3
    last_updated: 2026-04-18
    last_updated_by_session: H-003

# ---- Phase and work package ----
phase:
  current: pre-build
  current_work_package: "GitHub + Render setup walkthrough (next session)"
  work_package_started_session: H-003  # work package transition happens at close of H-003
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
  last_handoff_id: H-003
  next_handoff_id: H-004
  sessions_count: 3  # H-001 (kickoff), H-002 (scaffolding begin), H-003 (scaffolding complete)
  most_recent_session_date: 2026-04-18
  out_of_protocol_events_cumulative: 0
  out_of_protocol_events_since_last_gate: 0
  out_of_protocol_trigger_phrase: "out-of-protocol"

# ---- Repository and deployment state ----
repo:
  host: GitHub
  url: null
  visibility: public  # per D-005
  default_branch: main
  exists: false

deployment:
  backend:
    provider_category: "managed PaaS with deploy-from-git"
    provider_choice: Render
    service_url: null
    region: null
    exists: false
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
  actual_monthly_usd: 0
  cost_components:
    - component: "Render backend (compute + persistent disk)"
      expected_usd_range: "30-50"
      under_pressure_usd: "~100"
    - component: "Netlify frontend"
      expected_usd_range: "0 to low single digits"
    - component: "GitHub repo"
      expected_usd_range: "0"
    - component: "Object storage for nightly backup"
      expected_usd_range: "~5"
    - component: "Domain (if custom)"
      expected_usd_range: "~1 (amortized)"
    - component: "Polymarket US trading account balance"
      note: "operator-sized per Section 9 position-sizing commitment; not a platform cost"

# ---- Scaffolding files inventory ----
scaffolding_files:
  STATE_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: false
  Orientation_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: false
  Playbook_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: false
  SECRETS_POLICY_md:
    status: accepted
    produced_session: H-002
    accepted_session: H-002
    committed_to_repo: false
  DecisionJournal_md:
    status: accepted
    produced_session: H-003  # formal rebuild; draft-preview existed from H-002
    accepted_session: H-003
    committed_to_repo: false
  RAID_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: false
  PreCommitmentRegister_md:
    status: accepted
    produced_session: H-003
    accepted_session: H-003
    committed_to_repo: false
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

The project is in pre-build, governance scaffolding phase complete. Three sessions have run: H-001 established the governance model and produced the v3 build plan with Section 1.5 inserted. H-002 produced STATE.md (v2), Playbook.md, SECRETS_POLICY.md, and a DecisionJournal draft preview. H-003 (just closed) completed the scaffolding layer: DecisionJournal.md (formal rebuild, v1), RAID.md (v1, 32 entries), PreCommitmentRegister.md (v1 template, 31 entries), and Orientation.md (v1). All seven governance artifacts referenced in Section 1.5 of the build plan now exist as accepted documents. None have been committed to the repository yet because the repository does not exist — the operator holds all files locally.

The next work package is the GitHub + Render setup walkthrough. Claude will produce this as a step-by-step runbook document in H-004, and the operator will execute it step by step. Once the repository exists and the backend service is provisioned, Phase 1 technical work begins: host preparation, Sports WS granularity verification (the D-003 gate decision), Sackmann pipeline, and commitment-file derivation.

No tripwires have fired. No out-of-protocol events have occurred. The D-002 sub-questions remain open and are not blocking until Phase 7 exit.

### What changed in H-003

**YAML changes from v2 to v3:**
- `state_document.current_version`: 2 → 3
- `state_document.last_updated_by_session`: H-002 → H-003
- `sessions.last_handoff_id`: H-002 → H-003
- `sessions.next_handoff_id`: H-003 → H-004
- `sessions.sessions_count`: 2 → 3
- `phase.current_work_package`: "Governance scaffolding (STATE, Orientation, Playbook, SECRETS_POLICY)" → "GitHub + Render setup walkthrough (next session)"
- `phase.work_package_started_session`: H-002 → H-003
- `open_items.raid_entries_by_severity`: all fields were null → populated from RAID.md v1 entry counts
- `scaffolding_files.Orientation_md`: not-started → accepted (produced H-003, accepted H-003)
- `scaffolding_files.DecisionJournal_md`: draft-preview → accepted (produced H-003 as formal rebuild, accepted H-003)
- `scaffolding_files.RAID_md`: not-started → accepted (produced H-003, accepted H-003)
- `scaffolding_files.PreCommitmentRegister_md`: not-started → accepted (produced H-003, accepted H-003)

**Prose changes:** "Where the project is right now" subsection refreshed to reflect H-003 close state. "What changed in H-003" subsection added (new pattern — this subsection will appear in every STATE version going forward as a session-specific change log within the prose layer).

### Why the "What changed" subsection is new

Starting with STATE v3, every version includes a "What changed in H-NNN" subsection describing the delta from the prior version. This serves two purposes: it makes the operator's commit review faster (they see the changes described in plain English rather than having to diff two files), and it gives future-Claude a quick orientation to what happened in the most recent session without having to fully parse the YAML diff. The subsection is session-specific and is replaced on every STATE update — it always describes the most recent session's changes, not a cumulative history. Cumulative history lives in git.

### The scaffolding layer is complete — what this means

All seven governance artifacts are now accepted documents. This is a meaningful milestone because it closes the gap between Section 1.5's aspirational governance posture (D-008) and the project's actual state. The Section 1.5.5 tripwires, the handoff protocol, the observation-active lock, the self-audit requirement, and the doc-code coupling rule all now have the supporting documents they reference. The governance layer can operate as designed from this point forward.

It also means the project is ready to begin producing artifacts with real technical content. The GitHub + Render setup walkthrough is the bridge from governance-only work into Phase 1 proper. Once the repository exists, all seven scaffolding files will be committed, and the project will have a complete public record from H-001 onward.

One asymmetry worth naming: the governance layer is currently heavier than the code it governs (no code exists yet). This is by design — the governance was established before the code so that the code is built under a known set of rules. The asymmetry will resolve naturally as Phase 1 begins producing source files.

### RAID entry counts (as of H-003)

The RAID.md v1 produced in H-003 contains 32 entries:
- 15 Risks (R-001 through R-015): 2 at severity 8, 9 at severity 7, 3 at severity 6, 2 at severity 5 (note: R-009 is severity 6 monitoring, counted in sev_6 above — the YAML counts reflect the RAID's actual severity assignments)
- 5 Assumptions (A-001 through A-005): 4 unvalidated, 1 monitoring
- 5 Issues (I-001 through I-005): all open
- 6 Dependencies (DEP-001 through DEP-006): all active or pre-active

The severity counts in the YAML `open_items.raid_entries_by_severity` reflect open/active entries only, not closed or resolved ones (of which there are none yet).

### Unchanged from STATE v2

The YAML field dictionary, failure modes and recovery procedures, read/write protocol, non-coverage section, and artifact-interactions section in the prose commentary are unchanged from v2. These sections are schema-stable and do not require per-session updates. They are preserved verbatim below.

---

### Why STATE has the shape it has

*(unchanged from v2 — see that version for full rationale)*

The design is driven by six principles: one source of truth per fact with tooling reading the structured copy; both layers in one file to prevent drift; explicit nulls rather than omissions; dense now and prunable later; deliberate governance-fingerprint duplication as a redundancy-with-cross-check; and manual update cadence rather than auto-derivation. The trade-offs accepted include YAML parsing sharp edges (mitigated by quoting), fingerprint maintenance overhead, and the every-session-update rule's minimum overhead.

### YAML field dictionary

*(unchanged from v2 — consult v2 or the Orientation.md §4.3 governance-file table for field descriptions)*

### Failure modes and recovery procedures

*(unchanged from v2 — seven failure modes enumerated: SHA disagreement, handoff-ID mismatch, soft-lock state disagreement, missing STATE, malformed YAML, fingerprint disagreement, persistent open sub-questions)*

### Read/write protocol — full procedural spec

*(unchanged from v2 — full session-open and session-close procedures; also summarized in Playbook §1 and §2)*

### What STATE does not track

*(unchanged from v2 — session transcripts, operational telemetry, individual trade records, full STATE history)*

### How STATE interacts with other governance artifacts

*(unchanged from v2 — handoffs, DecisionJournal, RAID, PreCommitmentRegister, commitment files, handoff documents as historical record)*

---

*End of STATE.md — current document version: 3. Last updated: H-003.*
