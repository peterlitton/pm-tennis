# Handoff_H-028

**From:** H-028-Claude
**To:** H-029-Claude
**Date:** 2026-04-22
**Bundle version:** STATE v26 / DJ 36 / this handoff

---

## §1 — What this session accomplished

H-028 ratified a **single substantive governance decision**: D-036, Phase 3 exit on scope-framing reversal grounds, with three operational deliverables landing earlier in the session that produced the empirical evidence the reversal rests on.

**Three original deliverables landed clean** under operator-ruled three-deliverable arc per H-027 §10 tentative anchoring:

1. **D3 — events.list() tennis-filter validation.** Executed first per dependency-chain reasoning (D2 anchor sourcing depends on D3's filter call). `events.list({tagSlug:'tennis', active:True, ended:False, limit:20})` returned 12 live/upcoming tennis events at first call. 5/5 sampled tennis-pure (all carry tag id 22 'Tennis'). 5/5 sampled live-state consistent with filter (active=True, closed=False, ended=False; startDate within hours). §19.6 D→F recommendation validated empirically. One correction-cycle-pass surfaced during D3 pre-execution: fabricated `api_key_id`/`api_secret_key` constructor parameter names (those are env-var names, not constructor params); R-010-pattern caught by SDK rejecting with TypeError; corrected via sandbox introspection to `key_id`/`secret_key`. Named honestly.

2. **D1 — D-035 Auto-Deploy pre-flight (first-ever invocation).** Last known-good deploy b4e82d3 (H-022). Current main HEAD 7c8855c. Nine commits between. Zero drift in `src/stress_test/*` and `src/stress_test/requirements.txt` verified via `git diff --stat`. One unexpected commit surfaced: c89c021 'Add files via upload' modifies `src/__init__.py` with a docstring-only change ('latency-validation code package'). Outside `src/stress_test/*` drift scope per D-035 Commitment §1. Operator ruled standing/§9 hygiene flag for later cleanup; cross-project contamination unrelated to PM-Tennis. D-035 verdict: proceed unchanged on pm-tennis-stress-test state; no Manual Deploy required. **First operational exercise of D-035 discipline successful.**

3. **D2 — Sweep re-run with structured error_events payload extraction.** Anchor sourced via D3 traversal: events.list re-call returned 8 candidates with `markets[].slug` populated; selected event 9395 (ATP Mukund vs Erel, Challenger Abidjan, in-play first set, market slug `aec-atp-sasmuk-yanere-2026-04-21`). Sweep invocation `python -m src.stress_test.sweeps --sweep=both --log-level=INFO --seed-slug=aec-atp-sasmuk-yanere-2026-04-21` exit code 5 (`EXIT_SWEEP_PARTIAL`); json 187,944 bytes; stderr 4,395 bytes; wall-clock 4 min 5 sec. Per-cell classifications field-for-field match against H-023 Run 2 (M4 cell[0] `silent_filter_inferred=true` third independent sample at 2.5-day wall-clock spread / three-match spread; subscriptions-axis-n1 clean; n2/n5/n10 degraded with 1/4/9 error_events; connections-axis-n1/n2/n4 clean). M2 resolved `independent` (second project-history non-ambiguous M2). Then **central D2 deliverable — error_events payload extraction**: all 14 payloads across n2/n5/n10 cells uniform `WebSocketError(message='slug already subscribed: aec-atp-sasmuk-yanere-2026-04-21', request_id='sweep-sweep-h020-1776882888-subscriptions-axis-n<N>-conn0-sub<K>')` strings. Three findings: (i) only Pull B5 protocol-error site firing in tested config (not all three); (ii) **1/4/9 scaling exactly equals (N-1) duplicate-slug rejections from server's per-connection slug-uniqueness enforcement — harness-configuration artifact, not server-capacity signal**; (iii) `request_id` content carries per-subscribe attribution surviving repr layer. Reframes §20 against pre-registered three-outcome framework to a fourth outcome (partial discrimination via request_id parsing). M1 observable answer reframes from 'ambiguous' to 'per-connection slug-uniqueness prevents same-anchor multi-subscribe as tested.'

**Operator scope-framing reversal triggered by D2 finding.** Question sequence: 'measuring for what purpose' → 'how was 100+ concurrent matches calculated' → recognition that build plan §5.4's 150-asset soft cap was stated without derivation and that operational surface peaks ~20 concurrent matches at absolute peak (Grand Slam first round). **Items 1-4 of post-D2 reshape** (Item 1 H-022 §9 Observation 2 Tier 2 DJ entry; Item 2 §21 research-doc addendum on D2 finding; Item 3 v4.1-candidate-4 re-draft; Item 4 H-022 §9 Observations 3-6 disposition) **retired from H-028 scope**. D-036 pre-registered as single-deliverable session reshape.

**D-036 pre-registration ratified with five adjustments**, then drafted, then ratified-as-drafted:
1. Court counts labeled 'per operator's empirical surfacing at H-028, not verified against current venue configurations'.
2. D-033 preserved as SDK exception-surface reference distinct from sweeps.py retirement (operationalization in sweeps.py retired with sweeps.py; structural knowledge preserved).
3. Build plan §5.4/§11.3/§8 Phase 1 text updates queued as v4.1-candidate-6 in STATE pending_revisions for future Playbook §12 batch (build plan v4 text not modified this session).
4. Integration-test concurrency acceptance range 5-20 with reshape criterion (b) triggering below 5.
5. c89c021 cross-project contamination preserved as independent cleanup item unchanged by D-036.

**Path-(α) re-scoped from path-(b)** when ACTIVE_NOW=0 surfaced (Phase 3 capture code never deployed since H-009 D-016 revert; `/data/clob/` absent; success criteria 3+4 targeting Phase 3 code unobservable). Re-scoped to Phase-2-health-in-situ as adjacent evidence of Phase 2 capture worker health — explicitly not Phase 3 exit-specific evidence; D-036 rests on scope-framing grounds. 25-minute observation window 21:18:39Z-21:43:41Z on `pm-tennis-api`: poll cadence 60s held across 25 cycles; active event count stable at 101 (one removal during window via delta at 21:19:37Z event 9665); zero unhandled exceptions; zero service restarts; zero ERROR lines; `2026-04-22.jsonl` grew 1,240,043,023 → 1,262,639,388 bytes (+22.6 MB / 25 min = ~54 MB/hour ≈ 1.30 GB/day, consistent with sustained 1.17-1.43 GB/day baseline); discovery_delta.jsonl mtime advanced 20:45:11Z → 21:42:55Z confirming delta writer live throughout window.

**D-036 drafted and ratified.** Q1 ratified: compressed Reasoning ~300 words inside D-036; full empirical case (sections 1-5 of pre-registration) preserved at this handoff §9 per Q1 ratification for future re-litigation receipts. Q2 ratified: Section 11 rebindings as table inside D-036 Commitment section (8 items individually bound; 4 to Phase 4, 1 to Phase 5, 3 unchanged). Post-draft self-audit: four pulls all first-pass-pass; zero correction cycles. Operator ratified as-drafted.

**Phase 3 closes via D-036 scope-framing reversal.** Phase 3 capture-component implementation (CLOB tick capture, Sports WS, correlation layer, handicap updater) **rebinds to Phase 4 opening scope**. H-029 picks this up per attached pre-registration in §10 — first substantive code-turn under D-019 research-first discipline since H-009.

---

## §2 — Decisions made this session

**D-036** — Phase 3 exit on integration-readiness grounds; asset-cap stress-test arc retired on scope-framing reversal. Single DJ entry added at top, bumping counter 35 → 36. Full text in DecisionJournal.md.

**Envelope-pruning conventions continue per H-027 ruling** (in effect from H-028 forward):
- No Letter_from_H-028-Claude.md artifact. Continuity commentary folds into this handoff §9 self-report.
- `resolved_operator_decisions_current_session` collapsed to four H-028 arc-entries replacing what would have been ~15+ ruling-level entries.

**Five pre-registration adjustments** absorbed as drafting guidance (court counts as operator-surfaced; D-033 SDK-reference-distinct; v4.1-candidate-6 queue; concurrency range 5-20; c89c021 independent cleanup) — not separate decisions, mechanically folded into D-036 itself.

---

## §3 — Files in bundle

**Three-file bundle.** Collapsed from the seven-file bundle that would have been produced by the pre-reshape Items 1-4 scope. D-036 pre-registration explicitly predicted the three-file bundle outcome:

| File | Status | Note |
|---|---|---|
| `STATE.md` | Modified (v25 → v26) | YAML and prose updated; phase.current renamed; resolved_operator_decisions rewritten as H-028 arc-entries; pending_revisions grew to 6 with v4.1-candidate-6; scaffolding_files updated; prose footer corrected v24/H-026 → v26/H-028 |
| `DecisionJournal.md` | Modified (D-036 added) | Counter 35 → 36; D-036 at top per reverse-chronological convention |
| `Handoff_H-028.md` | New | This file. §9 carries full empirical case per Q1 ratification; §10 carries H-029 pre-registration verbatim |

**Not in bundle:** no research-doc changes (no §21 addendum — Items 1-4 retired per D-036 scope-framing reversal); no Playbook changes; no RB-002 changes; no RAID changes; no commitment-file changes (signal_thresholds.json, fees.json, breakeven.json, sackmann/build_log.json all unchanged); no code changes; no test changes; no SECRETS_POLICY changes; no Letter_from_H-028-Claude.md per envelope-pruning ruling.

---

## §4 — Governance-check results

**Session-open self-audit:** clean against H-027 bundle on-disk state (STATE v25, DJ 35 entries with D-035 at top, Handoff_H-027 present, RB-002 with Step 0). Zero discrepancies. One drift surfaced and noted for correction at close: STATE prose footer line 810 was stale (`v24/H-026`) while authoritative YAML field was at v25/H-027 — operator ruled correction-at-close to v26/H-028.

**D-035 first-ever pre-flight invocation:** verbalized reasoning per RB-002 Step 0 protocol. Last known-good b4e82d3 vs current HEAD 7c8855c; `git diff --stat b4e82d3..HEAD -- src/stress_test/` returned zero drift. One out-of-scope commit (c89c021 docstring change to `src/__init__.py`) surfaced and ruled out-of-D-035-scope; standing as independent cleanup item. Verdict: no Manual Deploy required; pm-tennis-stress-test state safe to use against. **First operational exercise of D-035 discipline successful.**

**Tripwires fired:** zero.

**OOP events:** zero.

**Pre-registration discipline:** D3, D1, D2, items 1-4 (later retired), D-036 — six pre-registrations across the session. All ratified or ratified-with-adjustments. One correction-cycle-pass on D3 (constructor parameter fabrication caught pre-execution by SDK TypeError; re-introspected and corrected). Zero correction cycles in D1, D2, D-036 drafting. Four-pulls post-draft self-audit on D-036: all first-pass-pass.

**Code-state verification at session-open:** **gap surfaced, named honestly for forward-propagation.** ACTIVE_NOW=0 and `/data/clob/` absence (Phase 3 code never deployed) surfaced post-ratification of D-036 path-(b) integration test, when they should have surfaced pre-ratification. The pre-registration assumed Phase 3 capture code was deployed; STATE had main.py at version `0.1.0-phase2` which would have refuted that assumption had it been checked at ratification. Received-discipline addition for H-029+ (see §9): code-state verification at session-open before pre-registration ratification, not after.

---

## §5 — Scaffolding-files inventory snapshot

| File | Version | Committed |
|---|---|---|
| STATE.md | v26 | pending (this bundle) |
| DecisionJournal.md | 36 entries | pending (this bundle) |
| Handoff_H-027.md | — | true (H-028 started from merged state) |
| Handoff_H-028.md | — | pending (this bundle) |
| Playbook.md | — | true (no changes this session) |
| Orientation.md | — | true |
| RAID.md | 13 open / 17 total | true (no changes this session) |
| PreCommitmentRegister.md | — | true |
| SECRETS_POLICY.md | — | true |
| RB-002 (Stress Test runbook) | — | true (no changes this session) |
| docs/clob_asset_cap_stress_test_research.md | 1780 lines, §§1-20 | true (no changes this session — Items 1-4 retired) |
| signal_thresholds.json | — | true (commitment file; unchanged) |
| fees.json | — | true (commitment file; unchanged) |
| breakeven.json | — | true (commitment file; unchanged) |
| data/sackmann/build_log.json | — | true (commitment file; unchanged) |

---

## §6 — Assumptions changed

**Pull B5 (§20 framework) reframed.** H-027's §20 enumerated three 'error' emit sites in `polymarket-us==0.1.2` as a structural-introspection finding and predicted that error_events payload extraction at H-028 would produce one of three outcomes: discrimination present (structural variance per emit site); ceiling hit (no attribution); empirical agnosticism. D2's empirical extraction surfaced a **fourth outcome not pre-registered**: only one of the three emit sites fires in the tested configuration (the protocol-error site), producing payloads of uniform shape that carry per-subscribe attribution via `request_id` content rather than via structural type variance. Shape Gamma (structured `SubscribeObservation.protocol_errors` field) remains the validated remediation for surfacing this attribution structurally rather than via repr-string parsing. Shape Epsilon (classifier refinement to discriminate "duplicate-slug" from other error semantics within the protocol-error site) is groundable per the empirical evidence but not implemented per D-036 retirement of sweeps.py.

**M1 observable-level answer.** H-023/H-027 carried M1 as 'ambiguous' at sweep-classification layer. D2's empirical evidence resolves M1 at observable layer to: **per-connection slug-uniqueness prevents same-anchor multi-subscribe composition as tested.** The harness configuration of "1 anchor + 99 placeholders per subscription, N subscriptions per cell" causes the anchor slug to be subscribed N times on one connection; subscriptions 2 through N collide with server's per-connection deduplication. M1 in the "can multi-distinct-subscribe compose independently" shape is unresolved (different test required); M1 in the "does multi-same-anchor-subscribe compose" shape is empirically resolved to "no, server enforces uniqueness per connection."

**Build plan §5.4 soft-cap framing.** Pre-H-028, the 150-asset soft cap was treated as a known operational ceiling to characterize via stress testing. D-036 reframes this: the 150 was stated without derivation; operational surface peaks ~20 concurrent matches; ratio 7.5× at peak / 15-30× typical. The stress-test arc was characterizing an envelope the instrument doesn't approach. Build plan §5.4/§11.3/§8 Phase 1 text updates queued as v4.1-candidate-6.

**Phase 3 exit framing.** Pre-H-028, Phase 3 exit was implicitly tied to capacity-envelope characterization (the asset-cap stress test was its load-bearing deliverable). D-036 reframes Phase 3 exit to scope-framing grounds: the original capacity-envelope question is operationally non-binding; Phase 3 closes on scope-framing reversal; Phase 3 capture-component implementation (the engineering work) rebinds to Phase 4. Build plan §8 Phase 3 acceptance criteria (48-hour unattended, pool stale-connection handling, retirement handler, handicap median, first-server identification) are inherited as Phase 4 acceptance bar.

---

## §7 — Tripwires fired

Zero. No fabrication tripwire (one R-010-adjacent pattern caught pre-execution at D3 constructor introspection — corrected before any commit). No commitment-file modification attempt during observation. No phase-gate skip attempt. No operator request that would have fired any tripwire. No terminal-only verification step (all observations through Render dashboard or sandbox introspection). No silent adaptation.

---

## §8 — Open questions

**Paste-chain anomaly watch from H-027 cleared.** H-027 §9 flagged for H-028 pattern recurrence: two paste-chain anomalies (verbatim-repeat message; Option Q ruling against situation that did not occur). H-028 saw **no recurrence of those H-027-pattern anomalies**. Three Render Shell heredoc paste-corruption observations did surface this session, but those are H-015/H-016 lineage (Shell heredoc handling mechanic, not chat-protocol), distinct from H-027's paste-chain governance-anomaly. Mitigation pattern adopted: `cat > file.py; python3 file.py` (separate cat and run commands rather than heredoc inline) — three occurrences self-resolved cleanly via this pattern.

**One operator-message paste-state ambiguity at mid-window observation.** Operator pasted what appeared to be the Step 3 baseline log sample twice (byte-identical). H-028-Claude surfaced parse-(a) (re-paste accident) vs parse-(b) (status-check request) explicitly rather than guessing; operator implicitly clarified by sending the actual T=15 log content next turn. Pattern: surface ambiguity, don't guess. Carry-forward as standing discipline.

**Other pending operator decisions:** none. POD queue empty.

---

## §9 — Self-report (carry-forward to H-029+)

This section is load-bearing per Q1 ratification. The full empirical case for D-036 (sections 1-5 from the pre-registration) is preserved verbatim below for future re-litigation. Subsequent subsections carry per-discipline-area observations and forward-propagation notes.

### §9.1 — D-036 full empirical case (verbatim per Q1 ratification)

#### §9.1.1 — Operational surface: tennis match concurrency at realistic peak

The instrument's scope per build plan §1.1 is "men's and women's singles on Polymarket US — ATP main-tour, WTA main-tour, Grand Slams, and Challenger-level tournaments."

Grand Slam singles draw structure (structural fact):
- 128 players per gender, single-elimination
- Round 1: 64 matches per gender × 2 = 128 matches, scheduled across 2 days
- Played on ~16-18 courts at the largest venues (Wimbledon 18, US Open 17, Australian Open 16, Roland Garros 15) — **per operator's empirical surfacing at H-028, not verified against current venue configurations**

Peak concurrent in-play at a Grand Slam first-round day (estimate from court counts): approximately 12-16 matches simultaneously mid-play, accounting for changeovers, set ends, and match completions creating momentary gaps. This is the heaviest possible moment in the sport.

Parallel tournament contribution: a single ATP/WTA tour event running the same week adds 2-4 additional courts, maybe 2-3 concurrent mid-play. Challenger events globally add another ~2-4 concurrent. Combined heaviest-moment upper bound: **~20 concurrent in-play matches**.

Non-Grand-Slam day peak: ATP/WTA tour event + Challengers = roughly **5-12 concurrent in-play matches**.

Typical day peak: **single digits**.

Project observation supporting this range: the capture worker's `/data/matches/` at H-015 Diagnostic A showed 116 event directories cumulative; at H-028 baseline observation showed 339 cumulative. These are cumulative event records, not concurrent-match counts, but the cumulative growth rate is consistent with operational surface in the tens of matches per day, not hundreds. H-028 D3 events.list returned 12 live/upcoming at one query moment; later anchor-sourcing call returned 8.

#### §9.1.2 — Build plan §5.4 soft cap: 150 assets

The 150-asset soft CLOB connection pool cap specified in §5.4 was stated without explicit derivation in the build plan. Reviewing §5.4: "Pool size is bounded by the soft 150-asset cap (to be stress-tested in Phase 3)." No calculation chain from expected operational load to 150 is provided in the build plan or the research arc.

Ratio of soft cap to operational peak: 150 / 20 ≈ **7.5× headroom** at absolute peak, **15-30× headroom** on typical days.

#### §9.1.3 — What the stress-test arc actually measured

`sweeps.py` runs a grid of N=1/2/5/10 subscriptions × 1/2/4 connections, with each cell composed of 1 anchor slug + 99 placeholder slugs per subscription. H-028 D2 established that the N=2/5/10 multi-subscribe cells were measuring per-connection slug-uniqueness enforcement on the duplicated anchor (finding: 1/4/9 error-events exactly equal (N-1)), not independent multi-subscribe composition.

M-question post-arc status:

- **M1** (multi-same-type subscription composition): resolved as "per-connection slug-uniqueness prevents same-anchor multi-subscribe as tested; original question requires harness redesign to answer; harness redesign not operationally relevant because production subscribes to distinct slugs, not repeated anchors."
- **M2** (multi-connection independence): resolved `independent` at N=2 and N=4 connection counts. Real finding. Limited by N=4 being the highest grid-tested.
- **M3** (per-subscription 100-slug cap): not grid-tested in sweep form. Documentation claim in §16.3.
- **M4** (placeholder-slug rejection): resolved `silent_filter` across three independent samples at 2.5-day wall-clock spread / three matches. Real finding. Operationally irrelevant because production doesn't use placeholder slugs.
- **M5** (concurrent connection upper bound): observed ≥4 concurrent connections operational; no upper bound discovered because grid-tested only to N=4.

**Findings of operational forward value:**

- M2 `independent` at N=2 and N=4: confirms the capture worker can run multiple connections in parallel without interference, at the small-N counts the operational surface actually requires.
- M4 `silent_filter`: confirms defensive-programming isn't required for placeholder-slug edge cases; production doesn't produce placeholder slugs.
- SDK exception surface per D-033: not exercised during sweep; structural characterization preserved as SDK reference, not as validated-in-production behavior.

**Findings not operationally forward-valuable:**

- M1 resolution about same-anchor multi-subscribe: harness-configuration artifact, not server-behavior finding relevant to production.
- 1/4/9 scaling pattern: harness-configuration artifact.
- M5 upper-bound at ≥4: operational peak is ~20 concurrent matches; even if all on one connection (impossible per M1 finding) or each on own connection (extreme over-provisioning), N=5-8 connections is the relevant regime, not bounded here.

#### §9.1.4 — The scoping failure diagnosed

The build plan's Phase 3 as originally specified (v3) included "CLOB asset-cap stress test" as a task deferred to Phase 3 from Phase 1 (v4 §8 Phase 1 table row: "CLOB asset-cap stress test — Deferred to Phase 3"). The deferral didn't re-examine whether the stress test was the right-sized work for the operational surface.

The research arc from H-019 onward treated the 150-asset soft cap as a given and built measurement infrastructure to characterize capacity envelope approaching that cap. At no point across H-019 / H-020 / H-023 / H-024 / H-026 / H-027 did any session (Claude or operator) surface the question "does the operational surface approach 150 concurrent assets?" The research-first discipline (D-019) protected scope integrity within the stress-test frame, but the frame itself was not re-examined.

Honest assessment: research-first discipline as practiced held sub-scope-integrity but not scope-calibration. The lesson forward is that scope-framing questions need to be asked explicitly at phase-open and periodically during multi-session arcs, not assumed to persist from the build plan's original scoping.

#### §9.1.5 — What Phase 3 exit actually requires

The build plan's Phase 3 acceptance criteria (§8 Phase 3): "48-hour unattended capture run with no data gaps; CLOB pool correctly handles stale connections; Sports WS retirement handler correctly marks retired matches."

None of these require the stress-grid measurement infrastructure. They require the capture worker to handle realistic concurrent load without breaking. Path (b) integration test addresses this directly: ~15-20 live tennis slugs, 20-30 minute observation, archive writes cleanly, no stalls, Sports WS correlation healthy, pool recycle behavior observable at least once. **Re-scoped at H-028 to path-(α) Phase-2-health-in-situ when ACTIVE_NOW=0 surfaced and Phase 3 capture code confirmed never deployed since H-009 D-016 revert. Path-(α) provides adjacent evidence of Phase 2 capture worker health under continuous operation; not Phase 3 exit-specific evidence; D-036 rests on scope-framing grounds independently.**

### §9.2 — Phase 4 nightly-compression urgency flag

Archive growth rate observed during H-028 Phase-2-health-in-situ window: `2026-04-22.jsonl` grew 1,240,043,023 → 1,262,639,388 bytes (+22.6 MB / 25 min). Hourly rate: ~54 MB/hour. Daily rate: ~1.30 GB/day. Compared against H-028 baseline observation of two daily archives: `2026-04-22.jsonl` 1.24 GB at 21:18Z (incomplete day), `2026-04-21.jsonl` 1.43 GB (complete day). Sustained range: **1.17-1.43 GB/day**.

This is **4-5× H-009's 290 MB/day projection** for raw-poll archive size. The discovery worker is polling more data per event than originally modeled (Gamma response shape grew, event counts grew, or both — root cause not investigated).

**Phase 4 implication.** Build plan §5.8 specifies nightly gzip ~10× compression as part of the post-processing pipeline. At 1.3 GB/day uncompressed and Render persistent disk capacity (10 GB per STATE), the disk has approximately 7-8 days of headroom without compression. Once Phase 4 nightly compression lands, headroom restores per the original projection. **Phase 4 nightly-compression scope is more time-sensitive than the original build plan implied.** Not a Phase 4 acceptance criterion change; an urgency-tier observation.

This finding is §9 carry-forward, not D-036 evidence trail (per operator Ruling 3 — adjacent hygiene, not Phase-3-exit-ruling evidence).

### §9.3 — Duplicate-player WARN observation (Phase 4 retirement-handler signal)

Two persistent WARN signals observed in every Phase-2-health-in-situ poll cycle during the 25-minute observation window:

```
WARNING  pm_tennis.discovery — Duplicate player flag set for event_id=9752 title='Cristian Garin vs. Alexander Blockx 2026-04-23'
WARNING  pm_tennis.discovery — Duplicate player flag set for event_id=9526 title='Botic van de Zandschulp vs. Alexander Blockx 2026-04-21'
```

Source per H-016 D-028 logic in `src/capture/discovery.py:_check_duplicate_players` (lines 432-451): same-day same-player detection. Returns True if player_a or player_b from new_meta already appears in a known event on the same calendar day (event_date string compare). Both events have populated `event_date` (post-H-016 I-016 fix) sharing the same value at current poll time, despite their title suffixes reading different dates (2026-04-21 vs 2026-04-23). Plausible reads:

- **(parse p)** Event 9526 (titled 2026-04-21) is a completed match still in the active discovery set because its `ended` flag has not flipped. Stale event record persisting past match completion.
- **(parse r)** Event 9526 has been rescheduled or its `event_date` field has rolled forward to today's date.

Either parse points at the same Phase 4 scope: **retirement-and-suspension handler work** (Section 11 item rebound by D-036 to Phase 4). The WARN is firing because the existing checker is doing its job; the data state is what needs handling. Phase 4's Sports WS retirement handler will need to flip `ended: true` or remove events from the active set when matches conclude or are no longer scheduled.

Not a current-session bug; not load-bearing for D-036; carry-forward to Phase 4 retirement-handler work.

### §9.4 — c89c021 cross-project contamination

Commit c89c021 ("Add files via upload") modified `src/__init__.py` with a docstring-only change: from blank to `"""latency-validation code package."""`. This is content from another project (PM-Tennis is not a "latency-validation code package"). Cross-project contamination, surfaced during H-028 D1's D-035 pre-flight `git diff` review.

**Disposition per operator ruling at H-028:** preserved as **independent cleanup item**. Not D-035 scope (modification is outside `src/stress_test/*` per D-035 Commitment §1). Not D-036 scope (D-036 addresses Phase 3 exit; this docstring is unrelated). Not Phase-3-exit-gating. Standing as a **§9 hygiene flag for future session with incidental scope to revert**. The fix is mechanically trivial: revert `src/__init__.py` to blank or to its pre-c89c021 content. No urgency.

H-029-Claude: do NOT touch this in H-029 (per H-029 pre-reg Pull 4 scope discipline). Future session beyond H-029 with adjacent scope can fold this in as ~1-line cleanup.

### §9.5 — Render Shell heredoc paste-corruption pattern

Observed three times this session during operator paste of multi-line `cat << 'PYEOF' ... PYEOF` heredocs into Render Shell. Pattern: portions of the next line in the paste arrive interleaved with the heredoc body, mangling the resulting Python file. Self-recovers when the corrupted Python file fails to import or runs partially.

**Mitigation adopted:** `cat > file.py` (no heredoc — inline content via a different mechanism, or chunked into smaller blocks, or via the operator's local clipboard manager) followed by `python3 file.py` as a separate command. Three occurrences this session self-recovered cleanly via this pattern.

**Distinct from H-027 paste-chain governance-anomaly.** H-027's anomaly was at the chat-protocol layer (verbatim-repeat message; Option Q phantom-context). H-028's anomaly is at the Render Shell text-handling layer (heredoc input mangling). Different surface, different mitigation. H-027 anomaly did NOT recur this session.

Carry-forward as Render Shell operating discipline: prefer non-heredoc patterns when pasting Python into Render Shell.

### §9.6 — §19-era introspection-scope gap (AsyncPolymarketUS constructor)

Surfaced during H-028 D3 pre-execution. §19 closure-check on `events.list()` candidate F characterized the EventsListParams field surface in detail (filter parameters, return shape, paging mechanics). It did NOT introspect the `AsyncPolymarketUS` constructor signature. When D3 needed to instantiate the client, H-028-Claude reached for parameter names from memory (`api_key_id`, `api_secret_key`) — these are env-var names, not constructor parameter names. SDK rejected with TypeError; correction-cycle-pass via `inspect.signature(polymarket_us.AsyncPolymarketUS.__init__)` revealed correct keyword-only params: `key_id`, `secret_key`.

**Received-discipline for H-029+:** when introspecting an SDK surface for use, introspect the **full surface that will be touched at use time**, not just the surface named in the design question. EventsListParams was the named surface in §19; AsyncPolymarketUS construction is the surface that gets touched whenever events.list() is called, and that surface was not introspected at §19 time.

H-029 Phase 1 SDK re-verification per H-029 pre-reg should introspect: AsyncPolymarketUS.__init__ (constructor signature); client.ws.markets() (factory + return type); MarketsWebSocket.__init__; MarketsWebSocket.subscribe; MarketsWebSocket.on; **MarketsWebSocket message-event payload structure** (the key gap); error event payload structure; connection lifecycle methods; authentication. All via inspect.getsource per D-019/R-010 discipline.

### §9.7 — STATE prose footer staleness observation

STATE.md prose footer at line 818 (pre-H-028-correction) read `*End of STATE.md — current document version: 24. Last updated: H-026.*` while the authoritative YAML field `state_document.current_version` was at v25/H-027. Staleness drift accumulated across two session bumps (H-026's v23→v24 footer-update did not propagate; H-027's v24→v25 also did not). Same pattern observed at H-024 close on the nested `scaffolding_files.STATE_md.current_version: 19` field — that drift was caught and corrected at H-024 close.

**Corrected at H-028 close to v26/H-028.** Note that the pre-correction string is preserved verbatim in `phase.current_work_package` history and in this §9.7 record — historical accuracy of "what the footer said" is preserved while current state is current.

**Received-discipline for H-029+:** STATE prose footer staleness should be checked at session-open self-audit (line-anchored grep for `End of STATE.md — current document version`) and corrected at session-close as part of the standard STATE bump ritual. Current ritual implicitly assumes prose footer auto-updates; it doesn't.

### §9.8 — Scope-framing-questions-explicit-at-phase-open (D-036 lesson)

H-028's D-036 demonstrated that research-first discipline (D-019) protects sub-scope integrity within an accepted frame, but doesn't substitute for periodic scope-calibration check on the frame itself. Six sessions of rigorous research-first work (H-019 through H-027) advanced the asset-cap stress-test arc without any session asking "does the operational surface approach 150 concurrent assets?" — the framing question that, once asked, dissolves the arc.

**Received-discipline for H-029+:** at every phase-open session, explicitly ask:
1. What is the operational surface this phase is engineered for?
2. What is the build plan's scoping-rationale for that operational surface? (If absent, surface this gap before proceeding.)
3. Does the proposed work characterize a meaningful slice of that operational surface, or does it characterize an envelope orthogonal to it?

Question 3 is the D-036 lesson distilled. It applies at phase-open, not just at phase-exit, because surfacing the framing question at phase-open is much cheaper than discovering it at phase-exit after multiple sessions of work.

**Note for H-029:** Phase 4 opens with H-029. The scope-framing questions for Phase 4 should be asked at H-029 session-open per this discipline. H-029's pre-registration §10.1 already implicitly answers: Phase 4 opening scope is CLOB tick capture implementation against the operational surface of ~20 concurrent matches at peak (D-036's empirical case). The connection-pool design choice in H-029 Phase 2 (per-match connection rather than shared pool, per Pull 2) is matched to this operational surface — not over-engineered for 150 concurrent.

### §9.9 — Code-state verification at session-open before pre-registration ratification

H-028's path-(b) pre-registration assumed Phase 3 capture code was deployed and runnable on `pm-tennis-api`. It was not (main.py at version `0.1.0-phase2`; Phase 3 components reverted at H-009 D-016). The assumption was implicit; no explicit code-state check was performed at pre-registration ratification time. The gap surfaced post-ratification when ACTIVE_NOW=0 (zero active matches) and `/data/clob/` absent both surfaced at observation start, requiring path-(α) re-scope mid-execution.

**Received-discipline for H-029+:** when a pre-registration assumes specific code state on a deployed service, verify that code state at pre-registration ratification time. For H-029 specifically, this is built into the H-029 pre-reg's session-open block ("Code-state verification (~5 minutes) before ratifying scope"): confirm `src/capture/` directory contents (no Phase 3 code present); confirm `src/capture/main.py` version identifier still reads `0.1.0-phase2`; confirm c89c021 still present (out of H-029 scope per Pull 4); confirm `/data/clob/` still absent. If any of these checks surfaces state inconsistent with pre-registration assumptions, surface to operator before proceeding.

### §9.10 — Discipline carry-forward propagation set (cumulative)

Standing disciplines that propagate from prior sessions, augmented with H-028 additions:

- Pre-registration before drafting (D-018 era; standing).
- Post-draft pre-registered-pulls self-audit writeup format (H-024 received-discipline; H-025 + later sessions practicing).
- Four-pulls post-draft self-audit format with each pull named, first-instinct-vs-held, resolution-outcome named honestly (H-025 received-discipline).
- Verbatim-check on enumerating sections at review time (H-025 Ruling 7).
- Correction-cycle-pass-named-honestly pattern (H-024 era; carried).
- Convention-discovery-by-observation: before invoking any 'convention', look at actual filenames in the repo and the internal headers of the documents the convention purportedly governs (H-026 received-discipline).
- Follow-convention-not-change-convention at artifact-type ambiguity: when a proposed artifact type has no repo precedent, surface that explicitly rather than invent naming and claim convention-adherence (H-026 received-discipline).
- D-035 Auto-Deploy-state pre-flight session-convention discipline for any Render service with Auto-Deploy=Off (H-027 ruling; H-028 first operational exercise successful).
- Envelope-pruning ruling: no Letter_from_H-NNN-Claude artifact; arc-level resolved_operator_decisions entries (H-027 ruling; H-028 second session under).
- **Scope-framing-questions-explicit-at-phase-open** (H-028 D-036 lesson; new).
- **Code-state verification at session-open before pre-registration ratification** when pre-reg assumes specific deployed-code state (H-028 lesson; new).
- **Render Shell heredoc paste-corruption mitigation** via `cat > file.py; python3 file.py` separate-command pattern (H-028 observation; new operating discipline).
- **Surface paste-state ambiguity rather than guess** (H-028 mid-window observation; standing-since-H-027 reinforced).
- **Full SDK constructor introspection** when planning to use a class, not just the class's per-method surface (H-028 D3 lesson; new).

These carry forward to H-029 via this handoff.

---

## §10 — H-029 pre-registration (attached verbatim per operator)

The following is the operator's pre-registration document for H-029, attached at H-028 close per the handoff-carries-next-session-plan protocol. H-029-Claude reads this at session-open along with this handoff.

---

### H-029 pre-registration — CLOB tick capture implementation

**Operator pre-registration for H-029-Claude. Attached to Handoff_H-028 per established handoff-carries-next-session-plan protocol. Single deliverable session under research-first D-019 discipline.**

#### Session scope

**Single deliverable:** CLOB tick capture code shipped to `pm-tennis-api`, with live smoke test if tennis-active during session, otherwise first-tennis-window as fallback.

**Why this session now:** D-036 (landed in H-028 close bundle) retired the asset-cap stress-test arc on scope-framing grounds and rebound Phase 3 capture component implementation to Phase 4 opening scope. H-029 is that Phase 4 opening scope. The project has been accumulating discovery data daily since H-009 but not CLOB tick data; that daily accumulation of missed tick archives is the operational cost D-036 implicitly acknowledges. H-029 closes that gap.

**What got us here:** H-009 reverted Phase 3 capture code under D-016 Option A1 after a fabrication incident. Research-first discipline (D-019) was established as the governing rule. Nineteen sessions of discipline-holding followed. H-029 is the first code-turn session writing capture code under the discipline that was built specifically to prevent fabrication recurrence. Applying D-016 commitment 2 / R-010 no-fabrication rigorously is non-negotiable.

#### Session-open block (~20 minutes)

Standard session-open self-audit against H-028 bundle on `main`. Confirm:

- STATE v26 landed with D-036's Phase 3 exit on scope-framing grounds.
- DecisionJournal has D-036 at top (counter 35 → 36).
- Handoff_H-028 on disk; this pre-registration attached.
- Phase 2 discovery loop on `pm-tennis-api` running healthy (quick `/data/matches/` and `/data/events/` mtime check).

**D-035 pre-flight on `pm-tennis-api`.** This session is live-execution against `pm-tennis-api`, not `pm-tennis-stress-test`. Per STATE, `pm-tennis-api` has `auto_deploy: On commit` per D-014; pushes to `main` trigger redeploy automatically. That's different from `pm-tennis-stress-test`'s Auto-Deploy=Off. D-035's session-convention discipline still applies — verbalize reasoning — but the conclusion is different: "Auto-Deploy On; main merge triggers redeploy; no Manual Deploy step required."

**Code-state verification (~5 minutes; new discipline addition per H-028 compounding-frame lesson).** Before ratifying scope, verify current `main` state matches pre-registration assumptions. Specifically:

- `src/capture/` directory contents — confirm no `clob_pool.py`, no `sports_ws.py`, no CLOB-capture code present.
- `src/capture/main.py` or equivalent — confirm version identifier still reads `0.1.0-phase2` or equivalent Phase-2-only marker.
- `src/__init__.py` — confirm `c89c021` docstring still present (cross-project contamination from H-028 §9; not in H-029 scope).
- `/data/clob/` on `pm-tennis-api` persistent disk — confirm still absent (consistent with "no capture code ever deployed").

If any of these checks surfaces state inconsistent with pre-registration assumptions, surface to operator before proceeding. The H-028 lesson was: when pre-registration claims "system state X," verify against actual deployed code before ratification, not after execution surfaces the gap.

**Scope ratification.** Operator rules the six-phase plan ratify-as-drafted, ratify-with-adjustments, or refine. Ratification includes explicit affirmation of: (a) no scope beyond CLOB tick capture; (b) reshape authority held such that Phase 5 (live smoke) is opportunistic, deferrable to H-030 or next tennis-window without blocking close; (c) research-first discipline per D-019 applies to the SDK re-verification step specifically.

#### Four pulls before code-turn

**Pull 1 — No-fabrication rigor at every SDK surface.** Every SDK symbol, parameter name, event name, method signature used in Phase 3 code must be verified via `inspect.getsource` in Phase 1 before Phase 3 writes against it. "I think `MarketsWebSocket.on` supports event name X" is not acceptable; "`inspect.getsource(MarketsWebSocket.on)` at Phase 1 surfaced event names [A, B, C] at line range Y-Z, and X is among them" is. R-010 / D-016 commitment 2 is the tripwire; H-029 is the session that earns the nineteen-session streak's worth of discipline capital by applying it rigorously.

Counter-vector: the pull to skip re-verification because "we characterized the SDK at H-020/H-023/H-026/H-028 already." Those characterizations covered subscription mechanics, error surface, events.list() filter surface, and credential constructor signature. They did not cover CLOB *message-event payload structure*, which is what tick capture actually consumes. That's the gap Phase 1 closes. Hold the pull against it.

**Pull 2 — Simplest workable design; no premature optimization.** Per-match CLOB connection rather than shared-pool. One archive writer rather than per-asset-dedicated writers. One error-handling path rather than emit-site-discriminated paths (Shape Gamma/Epsilon are retired per D-036). File layout per build plan §5.6 exactly, not re-architected.

Counter-vector: the pull to build for scale H-028's D-036 retired as unnecessary. The operational surface is ~20 concurrent matches at absolute peak. Per-match connections at 20 concurrent is trivially fine. If operational volume eventually requires pooling, that's a future session's scope, not H-029's. Hold the pull; simple wins.

**Pull 3 — Test discipline per D-021.** Unit tests for logic (archive writer envelope format, CLOB pool lifecycle transitions, discovery-to-pool wiring). Live smoke test for transport (if tennis-active in session). No mocks of Polymarket US SDK behavior beyond what's necessary for unit-test isolation.

Counter-vector: the pull to over-mock for test-speed reasons or to under-mock and require live gateway for every test run. D-021 testing posture is unit + live smoke; unit tests exercise logic that doesn't require network, live smoke exercises transport that can't be faithfully mocked.

**Pull 4 — Scope discipline: one deliverable, reshape authority held.** No `c89c021` cleanup even though it's adjacent. No Shape Gamma implementation. No H-022 §9 Observation 2 Tier 2 DJ entry. No plan-revision batch. No additional DJ entries beyond one potential D-037 if warranted (likely not required; D-036 already made the framing decision; H-029 is executing against that framing, not making a new framing decision).

Counter-vector: the pull to bundle adjacent work because the Velocity-and-Compression operator steering authorizes it. H-028's overreach-then-D-036-reshape lesson suggests the steering earns compression when simple deliverables land cleanly, not by front-loading additional scope. Let H-029 be a single clean deliverable; compression comes later.

#### Phase 1 — SDK surface re-verification (~30 minutes)

**Objective:** characterize `MarketsWebSocket` end-to-end for CLOB capture, grounded in `inspect.getsource` evidence. Output is a written record of verified surfaces that Phase 3 code will reference.

**Specific surfaces to characterize:**

1. `AsyncPolymarketUS.ws` — attribute type, factory methods available.
2. `client.ws.markets()` — signature, return type (presumably `MarketsWebSocket` instance).
3. `MarketsWebSocket.__init__()` — constructor parameters and their meaning.
4. `MarketsWebSocket.subscribe()` — parameter name(s), payload shape, return value.
5. `MarketsWebSocket.on(event, handler)` — events supported. Minimum: `'message'`, `'error'`, `'close'`. Others if present. Handler signature expected.
6. **Message-event payload structure.** This is the key gap. When `on('message', handler)` fires, what does `handler` receive? A dict? A typed object? A raw string? What fields? This has not been characterized in prior sessions and is load-bearing for the archive writer.
7. Error event payload structure — Pull B5 from H-027 identified three emit sites; Phase 1 confirms which fire in message-handling paths.
8. Connection lifecycle methods — connect, disconnect, close, any reconnect affordance. How does the pool know a connection has died.
9. Authentication — is auth handled by `AsyncPolymarketUS` constructor (`key_id` / `secret_key` per H-028 D3 correction), or does `MarketsWebSocket` require separate auth? Verify at introspection.

**Execution:** Python sandbox in chat environment. `import polymarket_us; import inspect`. Read the source for each symbol, capture line ranges, verify against installed `polymarket-us==0.1.2` (not README documentation, which can drift). Output a short markdown block with each surface, its signature, and the `inspect.getsource` line range where it was verified.

**Exit state:** a written record of verified SDK surfaces. Phase 3 references this record for every import, every method call, every parameter name, every event string. No Phase 3 line is written against an unverified surface.

**Reshape trigger:** if Phase 1 surfaces SDK complexity that makes the Phase 3 scope meaningfully larger than pre-registered (e.g., message payload is a nested multi-format union requiring per-match-type discrimination), surface to operator. Operator rules on scope-expand (continue with larger scope; accept session may run long or require continuation), scope-defer (close H-029 after Phase 1 with SDK characterization as deliverable, Phase 3 code to H-030), or scope-narrow (simplify Phase 3 design to handle complexity downstream in a separate session).

#### Phase 2 — Code shape pre-registration (~15 minutes)

**Objective:** pin the Phase 3 code structure before writing it. Names of files, names of classes and functions, envelope shape, error handling posture, wiring to discovery loop.

**Files to be created:**

- `src/capture/clob_pool.py` — CLOB WebSocket pool manager. Subscribes to matches as discovery adds them; unsubscribes when matches end; routes incoming messages to archive writer. Handles connection lifecycle per build plan §5.4 (15-min proactive recycle, 90-sec liveness probe).
- `src/capture/archive_writer.py` — thin layer taking envelope + raw message, appending to `/data/clob/{asset_id}/{date}.jsonl` per build plan §5.6.
- `tests/test_clob_pool.py` — unit tests for pool lifecycle, wiring, error handling.
- `tests/test_archive_writer.py` — unit tests for envelope format, file append behavior.

**Files to be modified:**

- `src/capture/main.py` (or wherever the discovery loop lives) — wire CLOB pool into the loop so discovery-discovered matches trigger CLOB subscription. Minimal change; pool owns its own loop, discovery signals via shared data structure.

**Envelope shape per build plan §5.1:**

```python
{
    "timestamp_utc": "2026-04-DD HH:MM:SS.fffZ",  # ISO-8601 ms precision
    "match_id": "<event_id>",
    "asset_id": "<polymarket_asset_id>",
    "sports_ws_game_id": "<optional>",
    "regime": "pre_match" | "in_play",
    "sequence_number": <int, session-scoped>,
    "raw": <raw SDK payload as received>
}
```

**Error handling posture:** `on('error', handler)` logs the error with `request_id` attribution (per H-027 Pull B5 characterization) and a decision matrix on whether to recycle the connection. Simplest acceptable: log-and-continue for transient errors; recycle connection on persistent errors; escalate to WARN log on pattern recurrence. D-033 frozensets from sweeps.py retired per D-036 are NOT re-used here; error-type handling is simpler and scope-matched.

**Discovery-to-pool wiring:** discovery writes `meta.json` per match under `/data/matches/{event_id}/`. CLOB pool periodically scans that directory (or uses a shared queue populated by discovery) to detect new matches and subscribe. Simplest: directory scan every 30 seconds, compare against current subscriptions, subscribe newly-appearing matches, unsubscribe matches whose `meta.json` shows `ended: True` or `live: False` for >5 minutes.

**What Phase 2 defers to Phase 3 judgment (not pre-registered):** specific class names, internal structure of the pool (dict of asset_id → connection, or list of connection objects, or whatever Phase 3 finds cleanest), retry logic specifics, logging format specifics. These are implementation-detail choices Phase 3 makes during code-writing.

#### Phase 3 — Code turn (~60 minutes)

**Objective:** write the two new files and modify the one existing file. Unit tests pass in the sandbox.

**Discipline during code-writing:**

- Every `import polymarket_us` subject referenced is one verified in Phase 1.
- Every method call, parameter name, event string matches Phase 1 verification exactly. If Phase 3 discovers a name it didn't think to verify in Phase 1, STOP and re-verify before using. No guessing.
- Envelope format matches Phase 2 pre-registration exactly. Any deviation surfaces to operator before writing.
- File paths match build plan §5.6 exactly (`/data/clob/{asset_id}/{date}.jsonl`).
- Unit tests cover: archive writer envelope format round-trip, archive writer file-append behavior, CLOB pool subscribe/unsubscribe lifecycle with mock SDK, CLOB pool error handling with mock error events, discovery-to-pool wiring with mock discovery state.
- Unit tests do not mock SDK behavior in ways that contradict Phase 1 verified surfaces. If `MarketsWebSocket.on` signature from Phase 1 is `on(event: str, handler: Callable)`, mocks match that.

**Exit state:** three new files and one modified file, all unit tests passing, code ready to deploy.

**Reshape trigger:** if Phase 3 code turn runs longer than budget (~60 minutes), reshape authority kicks in. Three options: (a) close Phase 3 with what lands, deploy in Phase 4 if tests pass, defer any incomplete piece to H-030; (b) close session without deploy, ship what lands as H-029 deliverable with Phase 4 deferred; (c) continue past budget if session bandwidth genuinely allows and operator rules it.

#### Phase 4 — Deployment (~15 minutes)

**Objective:** land the code on `pm-tennis-api` and verify it's running.

**Procedure per D-034:**

1. Bundle the changed files (two new, one modified) plus updated STATE + new DJ entry if warranted + Handoff_H-029.
2. Drag-and-drop to `claude-staging` branch per D-034.
3. Operator merges to `main`.
4. `pm-tennis-api` Auto-Deploy triggers automatically per D-014.
5. Wait for Live status in Render dashboard.
6. Verify self-check output or startup logs show the new CLOB pool initialized cleanly.
7. Verify Phase 2 discovery still running healthy (shouldn't have been affected, but verify).

**Exit state:** `pm-tennis-api` running with new capture code deployed. No errors in startup logs. Discovery and CLOB pool both active (CLOB pool may be idle if no active matches, but it's running).

**Reshape trigger:** if deployment surfaces a startup error (import failure, config miss, dependency missing), stop and surface. Options: (a) fix and redeploy in-session if fix is small; (b) revert the bundle and defer to H-030 with specific remediation.

#### Phase 5 — Live smoke (opportunistic, ~20-30 min if tennis-active)

**Objective:** observe the deployed CLOB capture against live tennis markets.

**Preconditions:**

- At least one tennis match currently live or imminently live (use `events.list()` with `active=True, ended=False, live=True` filter to check).
- `/data/matches/{event_id}/meta.json` exists for at least one live match with `live_at_discovery: true` or current `active: true, ended: false`.

**Procedure:**

1. Confirm live-active tennis via `events.list()` query (same pattern as H-028 D3).
2. Identify one or more target match slugs with known in-play status.
3. Observe `/data/clob/{asset_id}/*.jsonl` appearing on `pm-tennis-api` persistent disk.
4. Tail the JSONL: confirm messages arriving, envelope format matches spec, timestamps advance monotonically, sequence numbers increment.
5. Tail capture worker logs: confirm no exceptions, no WARN-level error patterns.
6. Observe for ~20-25 minutes (crosses 15-minute proactive recycle boundary so recycle behavior is observable).

**Success criteria:**

- CLOB JSONL files appear for at least one active match.
- Envelope format matches build plan §5.1 specification.
- No unhandled exceptions.
- Proactive recycle visible in logs at 15-minute boundary; reconnect produces clean gap-handled archive sequence.
- Archive write rate plausible for tennis in-play order-book activity.

**Reshape trigger:** if no tennis is active during session, Phase 5 defers without blocking close. Success criteria will be validated at first tennis-active window after deploy — operator observes incidentally, or H-030 session runs quick verification.

**Reshape if Phase 5 surfaces a failure:** code is deployed but behaving unexpectedly. Characterize honestly; session closes with deploy-state known and remediation scoped for H-030. Do not attempt patch-in-session unless the fix is mechanically trivial and operator rules it in scope.

#### Phase 6 — Close (~20 minutes)

**Objective:** clean session close per established protocol.

**Standard close activities:**

1. STATE v26 → v27: session counters bumped; scaffolding inventory updated; phase.current_work_package appended with H-029 compact summary; resolved_operator_decisions arc-entries per envelope-pruning ruling; prose "Where the project is right now" refreshed with H-029 overlay.
2. DJ: no new entry unless warranted. D-037 only if H-029 produces a decision-point governance-level finding (unlikely; H-029 is execution, not governance).
3. Handoff_H-029: standard 11-section shape per Handoff_H-027 precedent; §9 self-report carries any observations worth forward-propagating; §10 names H-030 scope.
4. Phase 4/5 observations captured in Handoff §9 with honest characterization (did live smoke succeed; what was archive write rate; did recycle behavior validate).
5. Received-discipline additions for H-030+ if any surface (e.g., code-state verification at session-open if H-029's session-open verification caught anything worth memorializing).
6. Bundle: STATE v27, DJ (updated if D-037), new/modified capture code files, Handoff_H-029. Drag-and-drop to staging per D-034.

**Streak disposition:** if H-029 closes clean (D-036 landed at H-028, Phase 1-4 landed in H-029, Phase 5 either succeeded or deferred opportunistically), streak advances to twenty. First substantive code-turn under D-019 research-first discipline in the project's history — earned, not assumed.

**Next-session anchor (H-030 scope):**

- If Phase 5 ran clean in H-029: H-030 can advance to Phase 5 dashboard scoping or Phase 4 API work per build plan §8.
- If Phase 5 deferred: H-030 first action is live smoke against the deployed capture code at a tennis-active window; then advance to Phase 5 dashboard or Phase 4 API.
- If H-029 Phase 3 ran long and ship-state is partial: H-030 completes the partial piece.

#### Honest risks to name at session open

1. **Phase 1 SDK re-verification surprises.** Message-event payload structure may be more complex than anticipated. Mitigation: Phase 1 is specifically designed to catch this before Phase 3 commits to a design.
2. **Phase 3 code turn time budget.** 60 minutes is tight for three files including tests; reshape authority held.
3. **Phase 5 calendar dependency.** Tennis may not be live at deploy time. Code ships regardless; smoke defers if needed.
4. **Discovery-to-pool wiring edge cases.** Matches ending exactly during a poll-cycle, matches discovered but never going live, meta.json updates racing with pool scans. Simplest wiring choice (periodic directory scan, 30-sec cadence, unsubscribe on ended=True or live=False for 5+ min) handles these cleanly; pre-register the simplest choice and don't re-architect mid-code.
5. **`c89c021` cross-project contamination still in `src/__init__.py`.** Adjacent to `src/capture/` where Phase 3 writes new files; incidentally tempting to clean up. Pull 4 scope discipline says leave it alone. H-029-Claude resists the temptation.

#### Streak-integrity framing

Eighteen sessions of clean discipline (H-010 → H-027) culminating in H-028's D-036 scope-framing reversal. H-029 is the first session since H-009 writing capture code. It is also the first session applying the full accumulated discipline stack to that task: research-first per D-019, no-fabrication per R-010 / D-016 commitment 2, pre-registration-before-drafting, post-draft self-audit, verbatim-check where applicable, correction-cycle-pass named honestly, doc-code coupling, D-034 drag-and-drop deploy, D-035 pre-flight (Auto-Deploy=On here, not Off, but discipline applies).

If H-029 lands clean, the streak semantic is earned twice: eighteen sessions avoiding the fabrication failure that caused H-009, then one session writing capture code successfully under the discipline built specifically to prevent that failure from recurring.

If H-029 surfaces a fabrication risk — Phase 1 SDK re-verification surfaces a gap that could tempt a guess — the R-010 tripwire fires. Stop, surface to operator, do not guess. That's the discipline working. A session that catches its own fabrication attempt before committing code is a stronger session than one that doesn't face the test.

#### Holding for operator ratification

Pre-registration ratify-as-drafted, ratify-with-adjustments, or refine. Operator rules at H-029 session-open.

**Two specific questions for operator ruling at session-open, not requiring pre-answer now:**

1. **Reshape authority specifics.** If Phase 3 code turn runs long, which fallback — close with what lands and ship partial (requires Phase 4 mental model of what partial-ship means), close without deploy (defer all Phase 4 to H-030), or continue past budget (session time flexibility)?
2. **D-037 trigger.** Does H-029 produce any decision-point finding warranting DJ entry (would be D-037)? Likely not — H-029 is execution against D-036's framing. But if Phase 1 SDK re-verification surfaces a surprise that materially changes the capture design from what's pre-registered, that's a D-037 candidate.

---

*End of H-029 pre-registration. Attached to Handoff_H-028.*

---

## §11 — State at H-029 session open

**Phase:** Phase 3 closed via D-036 scope-framing reversal at H-028. **Phase 4 opens at H-029** with CLOB tick capture implementation as the opening scope. Build plan §8 Phase 3 acceptance criteria (48-hour unattended capture, CLOB pool stale-connection handling, Sports WS retirement handler, handicap median, first-server identification) inherited as Phase 4 acceptance bar; not all gated at H-029 (H-029 is the implementation start, not the full Phase 4 close).

**Repo state:**
- GitHub repo `peterlitton/pm-tennis` main HEAD as of H-028 close: 7c8855c (pre-H-028-bundle-merge); H-028 close bundle to be drag-and-dropped to claude-staging and merged at session close.
- Phase 2 discovery code on `pm-tennis-api`: deployed, healthy, polling at 60s cadence, writing `/data/events/discovery_delta.jsonl` and `/data/events/<date>.jsonl` raw-poll archive (~1.30 GB/day sustained).
- Phase 3 capture code: never deployed since H-009 D-016 revert; `src/capture/clob_pool.py`, `src/capture/sports_ws.py`, `src/capture/correlation.py`, `src/capture/handicap_updater.py` do not exist on main; `src/capture/main.py` at version `0.1.0-phase2` (Phase 2 discovery loop only); `/data/clob/` does not exist on `pm-tennis-api` persistent disk.
- `src/__init__.py`: contains c89c021 cross-project contamination docstring; preserved as independent cleanup item per H-028 §9.4; not in H-029 scope.
- `pm-tennis-stress-test` Render service: retained per D-036 disposition, Auto-Deploy=Off preserved; sweeps.py and tests/test_stress_test_sweeps.py retained as historical record per D-036 retirement list.

**Service state:**
- `pm-tennis-api` (srv-d7hsb9hj2pic73afalt0): live, healthy, Auto-Deploy=On per D-014 — pushes to main trigger redeploy automatically. D-035 pre-flight at H-029 session-open will verbalize reasoning but conclude no Manual Deploy needed (different from `pm-tennis-stress-test` Auto-Deploy=Off).
- `pm-tennis-stress-test` (srv-d7ii277aqgkc739ul9bg): retained per D-036; no active session work runs against it by default.

**Open questions queue:**
- POD queue empty.
- pending_revisions: 6 entries (v4.1-candidate, -2, -3, -4, -5, -6 per H-028 close addition).
- RAID: 13 open / 17 total; unchanged.
- pre_commitment_register: standing commitments only.

**Discipline-state for H-029-Claude to inherit:**
- Nineteen-session clean-discipline streak (H-010 → H-028) if this bundle lands cleanly.
- D-019 research-first discipline applies to H-029's Phase 1 SDK re-verification specifically.
- R-010 / D-016 commitment 2 no-fabrication tripwire applies throughout H-029, with particular emphasis on Phase 3 code-turn (every SDK symbol referenced must trace to Phase 1 introspection evidence).
- Envelope-pruning ruling continues: no Letter_from_H-029-Claude artifact; resolved_operator_decisions_current_session entries collapse to arc-level.
- All §9.10 received-discipline carry-forward propagation set items active.

**Streak semantics if H-028 bundle lands cleanly:** nineteen consecutive clean-discipline sessions (H-010 → H-028). H-029 is the first substantive code-turn under D-019 research-first discipline since H-009 — earning the discipline capital accumulated, not assuming it.

---

*End of Handoff_H-028. To be presented to operator alongside STATE.md v26 and DecisionJournal.md (D-036 added). Three-file bundle for drag-and-drop to claude-staging branch per D-034.*
