# Handoff H-027

**From:** H-027-Claude (outgoing)
**To:** H-028-Claude (incoming)
**Session date:** 2026-04-22
**Project:** PM-Tennis
**Phase:** 3 attempt 2

---

## 1. What this session accomplished

H-027 landed three deliverables plus one convention-retirement ruling under "Velocity and Compression" operator steering, all clean:

1. **§19 strategy-discriminating research** appended to `docs/clob_asset_cap_stress_test_research.md` (lines 1452–1646, +195). Recommended Candidate E (hybrid D→F: operator-supplied `--seed-slug` first, `events.list()` with tennis filtering as automated fallback, `EXIT_NO_ANCHOR_SLUG` on empty F) against §18's frame. Pre-draft SDK introspection surfaced discovery-moment: `events.list()` and `sports.*` resource surfaces exist beyond `markets.list()`, expanding §18's candidate enumeration. Operator ruled Option X authorizing scope expansion to seven candidates (A/B'/C/D/E/F/G); G deferred on under-characterization. §19.6 recommendation per operator ratification at spot-check.

2. **§20 D-033 frame-extension research-first scope** appended (lines 1647–1780, +134). Addresses §17.6 item 2. Recommended Shape Gamma (structured `SubscribeObservation.protocol_errors: list[dict]` field preserving per-subscribe request-id attribution). Shape Epsilon (classifier refinement) deferred pending empirical grounding. Pull B5 SDK introspection surfaced three distinct `'error'` emit sites in `polymarket-us==0.1.2` (see §5 Assumptions for the empirical detail). Prerequisite artifact `/tmp/sweep_h023_run2.json` confirmed evicted on `pm-tennis-stress-test`; operator ruled β2 — §20 proceeds on structural grounds; re-sweep re-targeted to H-028.

3. **D-035 Auto-Deploy=Off session discipline** added at DJ top (DJ counter 34 → 35). Resolves H-022 §9 Observation 1 via (i)+(iii) composition — session convention for Auto-Deploy-state pre-flight check on `pm-tennis-stress-test`, codified via RB-002 Step 0 addition. Candidate (ii) config flip to Auto-Deploy=On preserved as live consideration for future session if (i)+(iii) proves brittle — not ruled out just not ruled in now. RB-002 Step 0 paragraph (~150 words, seven sentences) inlined into H-027 bundle per operator-authorized compact-paragraph inline under Velocity-and-Compression steering.

4. **Envelope-pruning ruling** captured in STATE at session close: (a) Letter_from_H-NNN-Claude convention retired from H-028 forward — continuity commentary folds into handoff §9 self-report if warranted, no separate letter artifact; (b) `resolved_operator_decisions_current_session` entries collapse to one entry per operator-ruling-arc rather than one per ruling. Other items in Handoff_H-026 §10.5's emergent-conventions surface remain active pending later review. H-027 is the first session operating under the collapsed-arc convention.

Zero code changes, zero test changes, zero commitment-file changes, zero Phase 2 source touches, zero RAID changes, zero Playbook changes, zero SECRETS_POLICY changes. Zero OOP events. Zero tripwires.

## 2. Decisions made this session

| Decision | Type | Source |
| --- | --- | --- |
| D-035 (Auto-Deploy-Off session discipline: (i)+(iii) composition) | New DJ entry | H-022 §9 Observation 1 (Tier 2 resolution) |
| H-027 envelope-pruning ruling | Governance convention (STATE-captured, not DJ) | Operator ruling at session-close |
| Option X (scope expansion of §18 candidate set from five to seven in §19) | In-session scope ruling | Pre-draft SDK introspection discovery-moment |
| β2 on /tmp/sweep_h023_run2.json prerequisite (proceed on structural grounds; re-sweep to H-028) | In-session branch ruling | Prerequisite-check outcome |
| §19 Q1 single-anchor ruling for current redesign; multi-anchor deferred to M1-resolution-scope | In-session §19.4 ruling | Operator pre-registration ratification |
| §19 Q2 signal priority order (live-state > tennis-narrowing > liquidity > recency) | In-session §19.5 ruling | Operator pre-registration ratification |
| Audit-first-pass-pass pattern trusted without full-text spot-check for §20 and D-035 | In-session review convention (extends to session-end pattern) | Operator ruling at §20 ratification |

No new POD entries opened. No new RAID entries opened. D-035 is the single new DJ entry this session.

## 3. Files in the session bundle

This bundle does **not** include a `Letter_from_H-027-Claude.md` per the H-027 envelope-pruning ruling (convention retired from H-028 forward; see §9 for the continuity commentary that a letter would have carried).

| File | Status | Notes |
| --- | --- | --- |
| `STATE.md` | modified | v24 → v25; session counters bumped; resolved_operator_decisions rewritten as four H-027 arc-entries per envelope-pruning ruling; scaffolding-files nested entries updated; phase.current_work_package narrative appended with H-027 compact summary; prose "Where the project is right now" refreshed with H-027 overlay; H-024 overlay shifted down to preserved-overlay stack |
| `docs/clob_asset_cap_stress_test_research.md` | modified | §19 appended at lines 1452–1646 (+195); §20 appended at lines 1647–1780 (+134); §§1–18 preservation SHA `1cbd6c0a1412d8f421302d2e6c2229251fe0d10d623395db83e0949a0562a3f2` and §§1–19 preservation SHA `420c1bfd1636ec4bc9f7bca0fd5b4a5ebeb0bd75cd528aafc7684a04e353d79c` both verified pre-write and post-write; version-history header and end-of-document summary line legitimately updated twice per §13/§15/§17 precedent; document now 1780 lines total |
| `DecisionJournal.md` | modified | D-035 inserted at top (lines 21–121); file grew 1380 → 1482 lines; DJ counter 34 → 35 |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` | modified | Step 0 inserted at line 63 before Step 1 (+6 lines); single-paragraph inline-bundling per operator authorization under Velocity-and-Compression steering |
| `Handoff_H-027.md` | **new** | This file |

## 4. Governance-check results this session

- **Session-open self-audit**: clean against H-026 bundle on-disk state. STATE v24 inventory fields matched git HEAD; DJ 34 entries with D-034 at top; research-doc 1451 lines with §18; Playbook §13.2/§13.3/§13.5.7 revised per D-034; Handoff_H-026 on disk. Zero discrepancies.
- **Scope-selection ruling per Playbook §1.3**: no POD-resolution-path check required (queue empty); no §16.9 step 1a+1b re-fetch required (research-first scoping, no code turn); no Render deploy-state check required (no live execution).
- **Pre-registration discipline**: six pulls for §19, six pulls for §20, four pulls for D-035; fourteen pulls total. Ratify-with-adjustments on §19 pre-registration surfaced Option X expansion; other two phases' pre-registrations ratified as-is.
- **Post-draft pre-registered-pulls self-audit writeup**: fourteen first-pass-passes; zero correction cycles this session.
- **Verbatim-check discipline**: not invoked — no operator-provided language captured verbatim this session.
- **Doc-code coupling rule (Orientation §8)**: D-035 + RB-002 Step 0 inline-bundled per operator authorization; other bundle files confined to H-027 scope.
- **No-fabrication tripwire (R-010 / D-016 commitment 2)**: Pull T1 (§19) and Pull B1 (§20) against over-reach in closure-check findings. Pull B5 characterized empirical substrate deferral honestly (β2 artifact eviction) rather than manufacturing evidence.
- **OBSERVATION_ACTIVE file**: not present (expected; observation window not yet open).
- **Commitment-file checksums**: not modified; no SHA checks triggered this session.

## 5. Scaffolding-files inventory snapshot at H-027 close

See STATE v25 `scaffolding_files` for authoritative inventory. Committed-to-repo status this close:

| File | committed_to_repo | committed_session |
| --- | --- | --- |
| `STATE.md` v25 | pending (produced this session) | H-027 |
| `docs/clob_asset_cap_stress_test_research.md` (§19 + §20) | pending (produced this session) | H-027 |
| `DecisionJournal.md` (D-035 added) | pending (produced this session) | H-027 |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` (Step 0 added) | pending (produced this session) | H-027 |
| `Handoff_H-027.md` | pending (produced this session) | H-027 |
| `Handoff_H-026.md` | true (verified on main at blob e046e3ee) | H-026 |
| `Handoff_H-025.md` | true (unchanged since H-026) | H-025 |
| `Playbook.md` | true (flipped this session; H-025 bundle merged cleanly since H-026 and H-027 started from that state) | H-025 |
| `Orientation.md`, `SECRETS_POLICY.md`, `RAID.md`, `PreCommitmentRegister.md` | true (unchanged) | various prior |

No `Letter_from_H-027-Claude.md` entry per envelope-pruning ruling.

## 6. Assumptions changed or added this session

- **SDK `'error'` event emit surface characterization** (new; §20 Pull B5): `polymarket-us==0.1.2` has three distinct emit sites — BaseWebSocket._message_loop (connection-failure) emits `PolymarketUSError` without per-subscribe attribution; MarketsWebSocket._handle_message (JSON-parse-failure) emits `PolymarketUSError` without attribution; MarketsWebSocket._handle_message (protocol-error) emits `WebSocketError(message, request_id)` with per-subscribe request-id attribution. §17.4.3's scaling observation (1/4/9 error-events for N=2/5/10 multi-subscribe) is consistent with the third site being the one fired during H-023's runs, but that correspondence is not yet empirically verified (see §8 Open questions, question 2).
- **SDK `events.list()` resource surface characterization** (new; §19 Pre-draft introspection): `EventsListParams` is a strict superset of `MarketsListParams` — adds `startDateMin/Max`, `endDateMin/Max`, `startTimeMin/Max`, `eventDate`, `eventWeek`, `tagSlug`, `tagId`, `seriesId`, `ended`, `featured`, `relatedTags` — permits tennis-narrowing via `tagSlug: ['tennis']` or `categories: ['tennis']`, with live-state narrowing via `ended: false` + `active: true`.
- **SDK `sports.*` resource surface existence** (new; §19 Pre-draft introspection): `AsyncSports` class exists with `list()` and `teams()` methods. Method signatures not introspected deeper; Candidate G deferred on under-characterization.

## 7. Tripwires fired this session

Zero tripwires fired.

## 8. Open questions requiring operator input

No blocking open questions for H-028 session-open. One standing watch item:

1. **Paste-chain anomaly pattern-recurrence watch.** Two anomalies observed this session (see §9 self-report); cause unknown, outside Claude's surface. If the same pattern recurs in H-028, the surface becomes large enough to warrant investigation.

Non-blocking surfaces preserved for operator scope-selection at H-028 open:

2. **§20 Shape Epsilon classifier refinement** (deferred). Prerequisite: error-event payload extraction per §17.6 item 4 (re-sweep re-targeted to H-028).
3. **§19.6 D→F live-smoke validation** (pre-registered for H-028 per operator's tentative H-028 anchor).
4. **H-022 §9 Observation 2 (Render "Deploy failed" label ambiguity) Tier 2 DJ entry** (preserved carry-forward since H-022).
5. **H-022 §9 Observations 3–6 Tier 3 disposition** (preserved carry-forward).
6. **Plan-revision batch under Playbook §12** (v4.1-candidate through -5 preserved in STATE `pending_revisions`).
7. **Candidate G revisit** (sports.* resource surface; deferred from §19 on under-characterization; revisitable under operator ruling if M1 resolution requires multi-anchor capability).

## 9. Self-report and §9 Evidence for H-028

This section absorbs what a Letter_from_H-027-Claude.md would previously have carried per the H-027 envelope-pruning ruling. I'm keeping it tight rather than expansive — the steering is "Velocity and Compression" and this is the first session producing continuity commentary in this new location.

### 9.1 What worked this session

Pre-registration-before-drafting held across three phases without a single correction cycle. Fourteen pulls first-pass-passed. The audit-first-pass-pass pattern matching across §19 and §20 earned operator trust for §20 and D-035 to be ratified without full-text spot-check — compression-earned, not compression-assumed.

Option X at §19 Phase A was the session's governance moment. Pre-draft SDK introspection surfaced `events.list()` and `sports.*` as resource surfaces §18 had not enumerated. The honest move was to surface the discovery-moment before drafting rather than quietly expand the candidate set inside §19 or quietly omit them. Operator ruled Option X authorizing the expansion with G deferral clean. The discipline paid: §19.6's Candidate E recommendation (D→F hybrid) is stronger than it would have been without F in the candidate set.

β2 ruling at §20 Phase B was the session's other governance moment. Operator's shell check confirmed `/tmp/sweep_h023_run2.json` was gone; I could have proposed a workaround (request re-sweep in-session) but honoring the prerequisite-branch pre-registration meant accepting the evidence deferral and naming it honestly in §20.3. Re-sweep re-targets cleanly to H-028.

### 9.2 Two paste-chain anomalies — name and move

Two observations this session, cause unknown, outside my surface:

1. **Verbatim-repeat message** partway through the session. An operator message was delivered whose content was byte-identical to the prior operator message. I surfaced three candidate parses (a/b/c) rather than guessing and held until operator confirmed reading (a) — an interface/resend artifact, conversation proceed normally.

2. **Option Q ruling against a situation that did not occur.** A subsequent operator message ruled a specific remediation (revert RB-002 to HEAD, re-apply Step 0, log in §9 as anomaly) against an anomaly that had not occurred in the session — no unexplained write, no mtime evidence I had produced, no trace check I had run, no RB-002 drift. I surfaced the parse gap rather than executing the revert; executing Option Q as ruled would have destroyed legitimate work. Operator confirmed reading (2): Option Q was ruled against a situation that did not occur; my refusal to execute was correct.

Both resolved cleanly. Operator ruled against chasing root cause in H-027; the pattern is noted for H-028 watch. If the same shape recurs, the surface becomes large enough to warrant investigation.

The pattern to carry forward from these two incidents: **surface parse ambiguity rather than guess**. In both cases the correct move was to stop, name the ambiguity, enumerate candidate parses, and hold for operator clarification. In both cases the pull was toward "just proceed with my best guess of what was meant" — in the first case because the repeat looked like continuity confirmation, in the second because the ruling was specific enough to seem executable. In both cases guessing would have been wrong (first would have barrelled past a checkpoint the operator may have wanted; second would have destroyed correct work).

H-026-Claude's letter named this lesson in a different key (don't substitute my interpretation of what the operator meant). Both this session's incidents are instances of that lesson under paste-chain-anomaly conditions rather than parse-ambiguity-in-single-message conditions.

### 9.3 What I'd carry forward to H-028

- **D-035 Auto-Deploy-state pre-flight discipline is now live.** H-028 opens with a live-execution scope (re-sweep + initial D→F validation per operator's tentative anchor). Session open must include: Render dashboard Events tab inspection for `pm-tennis-stress-test` last successful deploy commit; `main` HEAD comparison; Manual Deploy click if any `src/stress_test/*` change landed since last deploy. RB-002 Step 0 codifies this. Expected state at H-028 open: last known-good deploy at commit `b4e82d3` per STATE `deployment.stress_test.live_deploy_verified_session: H-022`; `main` HEAD currently at commit `6d1c926` (h26); H-027 bundle merge will advance `main` again. If H-027 bundle merge does not touch `src/stress_test/*` (it doesn't — RB-002 is `runbooks/` not `src/stress_test/`), no Manual Deploy is required before H-028 live work. Verify at H-028 open against actual state.

- **Envelope-pruning ruling takes full effect at H-028.** No Letter_from_H-028-Claude.md artifact. `resolved_operator_decisions_current_session` collapse to one-per-arc. H-028-Claude inherits this convention via handoff propagation; surface any ambiguity about the convention at H-028 session-open if it arises.

- **Pre-registration-before-drafting remains the discipline.** Live-execution sessions historically have had more room for drift than research-first sessions. Pin what will happen before it happens — invocation string, expected exit codes, expected JSON size ranges, expected stderr shape, expected per-cell classifications. H-023 established the pattern; H-028 extends it under D-035 pre-flight overhead.

- **No-fabrication tripwire (R-010 / D-016 commitment 2) is permanent.** Research-first per D-019 is permanent. These disciplines compose: research-first outputs either recommend actions or scope research documents; both require empirical grounding, and neither tolerates invented references.

### 9.4 Compact counters at H-027 close

- DJ entries: 35 (D-035 added)
- RAID: 13 open / 17 total (unchanged)
- Pending operator decisions: 0
- Pending revisions: 5 (v4.1-candidate, -2, -3, -4, -5)
- OOP cumulative: 0 / this session: 0
- Tripwires cumulative: 0 / this session: 0
- Clean-discipline streak: 18 consecutive (H-010 → H-027) if bundle lands cleanly
- Research-doc lines: 1780 (1451 → 1780, +329 this session: §19 +195, §20 +134)
- DJ lines: 1482 (1380 → 1482, +102 this session: D-035 +102)

## 10. Next-action statement and H-028 scope

### 10.1 Session-open ritual for H-028-Claude

Per Playbook §1 and standing conventions:

1. Acknowledge handoff receipt (this file, `Handoff_H-027.md`), read Orientation.md, STATE.md (v25) in full, Playbook §§1–5 + §12 + §13 at minimum, and the relevant DJ entries: D-035 (new, Auto-Deploy discipline), D-034, D-033, D-027, D-021, D-019, D-016.
2. Session-open self-audit against H-027 bundle on GitHub `main`: STATE v25, DJ 35 entries with D-035 at top, research-doc at 1780 lines with §19 and §20, RB-002 with Step 0 at line 63 before Step 1, Handoff_H-027 on disk.
3. **D-035 pre-flight for `pm-tennis-stress-test`** (new this session; first-ever invocation): operator consults Render dashboard Events tab for last successful deploy commit; compares against `main` HEAD; surfaces whether Manual Deploy is required before H-028 live work begins.
4. POD resolution-path check: queue is empty; skip per §1.3 ruling.
5. §16.9 step 1a+1b re-fetch discipline: required if H-028 touches code; if scope is re-sweep only (no code turn), operator rules at session-open.
6. Scope ruling from operator.

### 10.2 Tentative H-028 scope (per operator anchor at H-027 close)

Two-deliverable arc:

- **(A) Re-sweep for error-event payload extraction** (§17.6 item 4; prerequisite for §20 Shape Epsilon classifier-refinement grounding). Likely invocation: unchanged from H-023 run 2 template but with `/tmp/` artifact handling specifically cordoned off for Shape Gamma design work. Exact invocation string pre-registered at H-028 session open.
- **(B) Initial live-smoke validation of §19.6's D→F recommendation** against `events.list()` with tennis filtering. No code change yet (research-first per D-019 allows validation before redesign lands as code, but the strategy-discriminating research document's recommendation is itself the artifact being tested). Specific M-question gains: partial M1 re-sweep evidence if live tennis match available and multi-subscribe cells now exercise; error-event payload capture if multi-subscribe cells exercised. Exact invocation pre-registered at session open.

### 10.3 H-028 scope boundaries

- No `_fetch_anchor_slug` code change this session unless operator explicitly authorizes — §19 is research-first per D-019; code follows in a subsequent session.
- No `sweeps.py` code change for Shape Gamma unless empirical substrate for Epsilon is in hand AND operator authorizes §20 exit from research-first to code.
- No M1 re-sweep as standalone deliverable (M1 resolution remains downstream of `_fetch_anchor_slug` redesign).
- No Playbook §12 batch plan revision (v4.1-candidates preserved in `pending_revisions` for a later dedicated session; v4.1-candidate-4 still needs target-text re-draft under D-034 before it's §12-ready).
- Tier 2 disposition of H-022 §9 Observation 2 preserved carry-forward; can be lifted if operator rules it in-scope.

### 10.4 Received disciplines carried forward to H-028

From prior sessions:
- Research-first per D-019.
- No-fabrication per R-010 / D-016 commitment 2.
- Pre-registration-before-drafting (surface intended shape + pulls before drafting).
- Post-draft pre-registered-pulls self-audit writeup (per pull: named, first-instinct-vs-held, resolution outcome first-pass-pass vs correction-cycle-pass named honestly).
- Verbatim-check discipline at surfacing (when operator language is captured).
- Correction-cycle-pass named honestly (not suppressed).
- Content-range SHA language for preservation claims (not line-number language).
- Scope-selection at session open; standing disciplines named up front.
- Follow-convention-not-change-convention at artifact-type ambiguity; convention-discovery-by-observation (H-026 precedent).

**New from H-027:**
- **D-035 Auto-Deploy-state pre-flight discipline** for any session scoping live execution on `pm-tennis-stress-test`.
- **H-027 envelope-pruning ruling**: no Letter_from_H-NNN-Claude artifact; `resolved_operator_decisions_current_session` entries collapse to one per operator-ruling-arc. Other Handoff_H-026 §10.5 emergent-conventions-surface items remain active pending later review.

### 10.5 Standing observations carried forward to H-028

- **Paste-chain anomaly watch** (see §9.2). If pattern recurs in H-028, investigate.
- H-022 §9 Observation 2 (Render "Deploy failed" label ambiguity) — Tier 2 DJ entry candidate, preserved.
- H-022 §9 Observations 3–6 (Tier 3 meta/ops observations) — preserved.

## 11. Phase 3 attempt 2 state at H-028 session open

Per STATE v25. Briefly:

- Asset-cap stress test (D-018) live-smoke twice (H-023 runs 1 + 2) with `EXIT_SWEEP_PARTIAL` both times.
- `_fetch_anchor_slug` redesign: §18 scoped (H-026); §19 recommended Candidate E (H-027); code-turn deferred to post-§19-ratification session (not H-028 unless operator authorizes).
- D-033 frame extension for error_events: §20 scoped (H-027) recommending Shape Gamma; empirical substrate (error-event payload) deferred to H-028 re-sweep per β2 ruling.
- M1 resolution: downstream of `_fetch_anchor_slug` redesign code.
- Service state: `pm-tennis-stress-test` last known-good deploy at H-022 (commit `b4e82d3`). D-035 pre-flight activates for H-028.
- Commitment files frozen; OBSERVATION_ACTIVE not present; Phase 7 not yet reached.
- Tier 2/3 H-022 §9 Observation dispositions: Observation 1 now resolved via D-035; Observations 2–6 preserved.

---

*End of Handoff H-027.*
