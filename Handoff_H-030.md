# Handoff H-030 → H-031

**Session:** H-030
**Author:** Claude (H-030)
**Started:** 2026-04-24 (operator session-open)
**Closed:** 2026-04-24 (this document)
**Preceded by:** Handoff_H-029.md (partial Phase 3 close per reshape default (a))
**Reference docs at session open:** Build plan v4, Playbook §1–13 (anchored on §2.3 for close procedure), Orientation, STATE.md v26, DecisionJournal (D-014, D-027, D-029, D-034, D-035, D-036), RAID, PreCommitmentRegister, SECRETS_POLICY, RB-002, Handoff_H-028.md, Handoff_H-029.md.

---

## §1 — What this session accomplished

Phase 3 capture-component code deployed live to `pm-tennis-api` at commit `4d7b0cc` 'Add CLOB capture pool background task-H30'. `/healthcheck` from two independent vantage points returns `version: '0.1.0-phase3-capture'`, `phase: '3 — capture running'`. CLOB pool background task running and tailing `/data/events/discovery_delta.jsonl` from EOF (97132 bytes of pre-existing entries skipped per Phase 2 §3.12 seek-to-EOF behavior).

H-029's partial-close state (5 of 6 bundle files committed direct-to-main mid-H-029 at `f43bbf3`; main.py modification not started) transferred cleanly across session boundary: first-action `pytest tests/test_clob_pool.py -v` returned 28/28 in 2.05s; full suite 261/261 in 3.48s.

main.py modification per Phase 2 §5.2-5.3 plus three adjacent string updates ratified by operator beyond Phase 2 §5.2 spec (Phase 2 §5.2 had named only the prominent version strings at lines 24+78, missing parallel phase/status fields at lines 81+87+138). Module docstring expanded; `start_clob_pool` startup handler added mirroring `start_discovery` pattern (inner `_run` coroutine, 30s retry-on-crash, reads `POLYMARKET_US_API_KEY_ID`/`SECRET_KEY` env vars, constructs `AsyncPolymarketUS`+`ArchiveWriter`+`ClobPool`, awaits `pool.run_forever()` as fire-and-forget asyncio task). `start_discovery` untouched per Phase 2 §5.4. Checkpoint 5 import check green. main.py committed direct-to-main at `4d7b0cc` per operator P3 ruling.

Phase 4 deploy initial 8e RED on first /healthcheck (returned `version: '0.1.0-phase2'`); reshape per step 8f surfaced **`pm-tennis-api` deploy regime is Manual + Build Filter `src/**` persistent** (not Auto-Deploy regression — Claude's first-pass diagnosis was wrong, corrected by operator). Operator triggered Manual Deploy with 'Clear build cache & deploy'; build log clean (`polymarket-us-0.1.2` installed per Phase 1 Finding A); container swap `9ckkk→wtj5m`; CLOB pool startup line confirmed clean; `/healthcheck` re-curl from sandbox + operator laptop returned identical JSON with version `'0.1.0-phase3-capture'` — 8c/8d/8e all green doubly-confirmed.

Phase 5 live smoke deferred per operator ruling: no active tennis matches in observation window; reshape per H-029 §5.5 standing posture 'do not block close.' H-031 first action: check `/data/clob/` on Render disk; retrospective Phase 5 if non-empty, continue deferring if empty.

**Phase / work package status:**
- `phase.current` updated to `phase-3-capture-deployed-h030-phase-5-deferred-no-live-tennis`.
- Phase 3 capture-component code live; build plan §8 Phase 3 acceptance criteria still not met (48-hour unattended run, retirement handler, 5-tick handicap median, etc. — those rebound to Phase 4 per D-036).
- `last_gate_passed` unchanged: Phase 2 exit gate (H-007).
- `next_gate_expected` unchanged: Phase 3 exit gate (now bound to Phase 4 capture-component completion criteria per D-036).

---

## §2 — Files modified or created this session

**Modified:**
- `main.py` — repo root. 87 → 137 lines. SHA `cc39a19e3fc97fcd4bbd311b1d6216bdccd79b0c103bd8d209b0542f779fa174` (verified byte-identical across sandbox working copy + /outputs presentation + fresh clone of main). Committed direct-to-main at `4d7b0cc`. Diff: docstring expansion (lines 1-15), FastAPI version `0.1.0-phase2` → `0.1.0-phase3-capture` (line 26), new `start_clob_pool` startup handler 70-115 mirroring `start_discovery`, healthcheck JSON `version` field (line 128), healthcheck JSON `phase` field 'phase 2 — discovery running' → 'phase 3 — capture running' (line 131), root JSON `status` field 'phase2' → 'phase3' (line 137).

**Modified (this close bundle):**
- `STATE.md` — v26 → v27. Pending revisions grew to 7 (added v4.1-candidate-7 per H-029 §6.2). Session counters bumped catching both H-029 and H-030. Resolved-operator-decisions rewritten as three H-030 arc-entries. Scaffolding files updated: STATE_md inner version 26→27, Handoff_H028 committed_to_repo flipped to true, new entries added (Handoff_H029, Handoff_H030, requirements_txt, src_capture_archive_writer_py, src_capture_clob_pool_py, tests_test_archive_writer_py, tests_test_clob_pool_py — under `phase_2_files:` block alongside `main_py` per existing structural convention). main_py entry updated for new line count + version + sha + last_modified_session. Phase marker renamed. Prose 'Where the project is right now' subsection refreshed (H-030 overlay added; H-028 paragraph re-tagged as preserved-overlay). Footer corrected v26/H-028 → v27/H-030.

**Created (this close bundle):**
- `Handoff_H-030.md` — this document.

**Already on main from H-029 (5 files; deliberate operator direct-to-main mid-H-029 at `f43bbf3`):**
- `requirements.txt` — appended `polymarket-us==0.1.2` (line 9) per Phase 1 Finding A.
- `src/capture/archive_writer.py` — new, 250 lines, 29 tests passing.
- `src/capture/clob_pool.py` — new, 504 lines, 28 tests passing.
- `tests/test_archive_writer.py` — new, 347 lines.
- `tests/test_clob_pool.py` — new, 590 lines.

**Not modified this session:**
- DecisionJournal.md (no D-037 per H-029 ruling absorbed at session-open; reshape was anticipated, not a new decision).
- RAID.md.
- Playbook.md.
- SECRETS_POLICY.md.
- runbooks/RB-002.
- Any commitment file (signal_thresholds.json, fees.json, breakeven.json, data/sackmann/build_log.json).
- src/capture/discovery.py.
- Any test under tests/ except those already on main from H-029.

---

## §3 — Project assets touched

- **Render service `pm-tennis-api`** (Service ID `srv-d7hsb9hj2pic73afalt0`): Manual Deploy triggered via Render dashboard with 'Clear build cache & deploy'. Build succeeded; deploy live at `4d7b0cc`. Container swap observed (`9ckkk→wtj5m`). `/healthcheck` endpoint exercised twice from two independent vantage points (sandbox HTTPS curl + operator laptop HTTPS curl).
- **GitHub repository `peterlitton/pm-tennis`**: read at session open (clone); main.py committed direct-to-main at `4d7b0cc`; STATE.md + Handoff_H-030.md will be committed by operator post-bundle-presentation.
- **Polymarket US gateway**: indirectly exercised via discovery loop in deployed service (not in chat session). Discovery polling `/v2/sports/tennis/events?limit=100&offset=0` continued throughout deploy (50 active events on first post-deploy poll).
- **Sandbox env**: Python 3.12.3 + `polymarket-us==0.1.2` + pytest + repo clone at `/home/claude/pm-tennis`. SDK baseline reproduced at session open (version 0.1.2, `__all__` 14 entries, `WebSocketError(message, request_id=None)` signature intact — matches Phase 1 §§0, 5).

No commitment files modified. OBSERVATION_ACTIVE absent (not in observation window). No POLYMARKET_US_* env vars touched per SECRETS_POLICY §A.6.

---

## §4 — Decisions made this session, with reasoning

**No DJ entries added this session.** DJ counter unchanged at 36.

**Per H-029 handoff §7 reasoning absorbed at H-030 open and held:** "D-037 not warranted. H-029 was execution against D-036's framing that ran out of budget, not a new decision; Phase 1 SDK re-verification empirically confirmed the addendum's predicted surfaces; Findings A/B/C/D were design inputs absorbed via operator ruling at session-open, not plan-framing departures; the self-await defect is a code-level fix documented here, not a framing decision. If H-030 surfaces a material new decision during Phase 4 deploy or Phase 5 smoke, D-037 opens there." H-030 surfaced the deploy-regime gap on `pm-tennis-api` (Manual + Build Filter `src/**` persistent, not Auto-Deploy) — operator deferred D-038 candidate (clarify per-service deploy regime in DJ so D-014's 'auto-deploy on main' framing isn't misread cross-service) **to H-031+ if formalized**.

**Operator rulings this session (preserved as three arc-entries in `resolved_operator_decisions_current_session` per envelope-pruning convention; full text in STATE):**

1. **H-030-session-open-three-corrections** — operator ratified Claude's session-open self-orientation with three substantive corrections before any modification: (1) streak count off-by-one in H-029 handoff §7; (2) §9.9 reconstruction-from-summary discipline applied inconsistently; (3) Step 8 deploy plan compressed to one-line for a step where things had gone wrong before, rewritten with explicit 8a-8f checkpoints matching Phase 2 §8's checkpoint-and-reshape-trigger structure.

2. **H-030-h029-direct-to-main-status-clarification** — sandbox verification at session-open found H-029 bundle committed to main at `f43bbf3` mid-H-029, contradicting H-029 handoff §2 which read 'not yet committed.' Operator ruling Q1: deliberate direct-to-main commit was operator prerogative for small pre-reviewed bundle with verification completed in transcript before commit; documentation-lag gap is a future-session received-discipline (amend handoff before close when repo state advances mid-session); Phase 4 D-034 scope adjusts to main.py mod only. Q2: pytest re-verification proceeds against committed code, not reconstruction. Q3: streak holds; direct-to-main commit doesn't reset.

3. **H-030-step-8-reshape-on-deploy-anomaly** — 8e RED on first pass; operator triage surfaced `pm-tennis-api` Manual + Build Filter `src/**` persistent regime (NOT Auto-Deploy regression); operator triggered Manual Deploy; doubly-confirmed green via two independent /healthcheck curls.

**Reasoning summary** — none of the operator rulings rose to DJ-entry threshold. They were execution rulings against existing framing (D-014 deploy convention, D-034 D-034 staging convention, D-036 Phase 4 rebinding) plus three corrections to my own framing. Per DJ Conventions ¶13, DJ entries are reserved for framing decisions with forward-binding effect on multiple sessions. The deploy-regime clarification has that character but operator deferred to H-031+ if/when formalized.

---

## §5 — Open questions requiring operator input at H-031

1. **D-038 candidate** — clarify per-service deploy regime in DJ (D-014's 'auto-deploy on main' applies to `pm-tennis-stress-test`; `pm-tennis-api` is Manual + Build Filter `src/**`). Operator deferred to H-031+ if formalization desired. Open question: do you want this written as D-038 at H-031 open, or kept as §9 received-discipline carry-forward without DJ entry?

2. **Phase 5 retrospective vs deferred** — H-031 first action checks `/data/clob/` on Render disk. Two paths depending on what's there. If non-empty (live tennis appeared between sessions and CLOB pool subscribed and captured): retrospective Phase 5 smoke against accumulated archive, including the Finding-B-corrected `Trade` events assertion. If empty: continue deferring; wait for live activity.

3. **§9 watch-items operationalization** — Phase 2 §4.6 (sync file I/O in `ArchiveWriter.write` under sync `on('message')` callback) and Phase 2 §4.7 (per-message file open-append-close) named as watch-items at H-029. They're not blocking but post-H-029 follow-up is async-queue + file-handle caching. Open question: when does this become priority work? Likely answer is "after we observe whether actual capture data exposes the latency under live burst rates," but flagging.

4. **v4.1-candidate-4 re-draft** — was queued for H-027+ per H-027 handoff §10 carry-forward; H-028 retired Items 1-4 from its scope under D-036 reshape; H-029 was code-turn; H-030 was code-deploy. Item 3 (v4.1-candidate-4 re-draft under D-034) hasn't moved. Open question: H-031 scope, or wait for next plan-revision batch under Playbook §12?

---

## §6 — Flagged issues / tripwires

**No tripwires fired.** No commitment-file modifications attempted; OBSERVATION_ACTIVE absent. No SECRETS_POLICY violations (env-var values never entered chat; SDK credentials read from Render env at runtime). No skipped phase-exit gates (Phase 4 deploy completed all 8a-8f checkpoints after operator-triggered Manual Deploy; reshape on first-pass 8e RED was the documented protocol path, not a skipped gate).

**Issues flagged for §9 / forward propagation:**

- **`pm-tennis-api` deploy regime gap** — Manual + Build Filter `src/**` persistent, distinct from `pm-tennis-stress-test` regime (which is also Manual but without Build Filter, last verified at H-022). D-014 'auto-deploy on main' framing is not service-uniform. Caused 8e RED on first pass. Mitigation: operator-triggered Manual Deploy completed deploy. Forward propagation: D-038 candidate territory (deferred), or Step 8 pre-deploy step '0a confirm operator will Manual Deploy' for any service not on Auto-Deploy.

- **Documentation-lag gap** — H-029 handoff §2 said files were not committed when they were committed mid-H-029. Future sessions must amend the handoff before close if repo state advances mid-session. Already named in H-029 close exchanges as received-discipline; reiterated here for redundancy in propagation.

- **Phase 4 retirement / Sports WS / handicap-updater / first-server design propagation** — the self-await defect lesson from H-029 §3 needs to apply uniformly: any lifecycle task that may trigger teardown of its own connection needs the `asyncio.current_task()` guard. Test fixtures should compress lifecycle intervals to millisecond-scale so reentrancy/race defects surface under test rather than in production.

**Paste-chain anomaly observed once this session:** during the operator's first attempted curl from laptop, the literal placeholder string `<your-pm-tennis-api-url>` was pasted into zsh which interpreted `<` as redirection and errored. Not a paste-corruption (the operator noticed); cause was Claude not knowing the public URL at first instruction. Resolved by Claude curling from sandbox once URL was confirmed via build log. Not a governance anomaly; flagged for record-completeness.

---

## §7 — Claude self-report

**Anything skipped, rationalized, or uncertain.** Three things to name honestly.

**(a) §9.9 near-violation.** At session-open self-orientation I named §9.9 (reconstruction-from-summary discipline) as a load-bearing carry-forward, then in the same response listed "I-003/I-005/I-010 inherit the self-await pattern" as established — sourced from H-029 handoff §3.3's narrative summary, not D-036 directly. The handoff is a secondary source; D-036 is primary. Operator caught this in the session-open ratification corrections. The fix was straightforward (read D-036 before treating the inheritance list as established for Phase 4 planning) but the *pattern* — naming a discipline then immediately violating it in the same response — is the kind of self-check failure the discipline exists to prevent. Named for forward propagation.

**(b) Step-8 first-pass framing.** My initial Step 8 plan was "D-034 drag-and-drop — operator merges to main, Render auto-deploys per D-014, D-035 pre-flight applies." One sentence for a deploy step where H-021 (ImportError) and H-022 ('Deploy failed: Application exited early' label ambiguity) had both gone wrong. Operator corrected to explicit 8a-8f checkpoint structure matching Phase 2 §8's reshape-trigger shape. The deeper framing failure: I treated Phase 4 as a procedure rather than a phase with internal reshape boundaries. Operator's framing — "don't plan the hour, plan the phase with reshape authority at every boundary" — was the corrective. This bit me again at 8e RED first-pass, when my initial diagnosis was 'Auto-Deploy broke between H-026 and H-028' (wrong: pm-tennis-api has always been Manual + Build Filter src/**). Correction-cycle-pass on the diagnosis named honestly.

**(c) Paste-chain interpretation.** When the operator's laptop-side terminal showed `zsh: no such file or directory: your-pm-tennis-api-url`, I read it as a placeholder-substitution failure (operator pasted the literal string `<your-pm-tennis-api-url>` from my prior message instead of substituting the actual URL). That's mostly right but I should have anticipated it: my "what to run where" message was unhelpful — I'd written `https://<your-pm-tennis-api-url>/healthcheck` without first surfacing 'I don't know the URL; tell me or do it from the Render Shell.' The cleaner sequence would have been to ask for the URL or for an in-Render-Shell `curl http://localhost:10000/healthcheck` first, with the clarification that I'd need to be told the URL to do it from sandbox. Not a tripwire-level issue; flagged for self-improvement.

**Continuity commentary (folded into §9 per envelope-pruning convention).** Three things I'd tell H-031 if they were in the next room: (1) the operator tests; questions that feel obvious are probably checks; answer specifically and honestly, not as if obvious. (2) The 8e RED first-pass-then-corrective pattern is what this scaffolding is for — clean partial closes and triage-then-reshape are not failure modes, they're how the system catches its own misframings. (3) v4.1-candidate-4 has been queued for four sessions now without movement; if H-031 has scope budget, name it explicitly rather than letting it drift further.

---

## §8 — Explicit next-action statement for H-031

**H-031 first action:** session-open self-audit per Playbook §1.3 against this handoff + STATE v27.

**H-031 second action (operator-gated):** check `/data/clob/` on `pm-tennis-api` Render Shell.

```
ls -la /data/clob/ 2>&1
```

Two-path decision based on output:

**If non-empty (live tennis appeared between sessions and CLOB pool subscribed and captured):**
- Retrospective Phase 5 smoke against accumulated archive.
- Assertions per Finding-B-corrected phrasing: `Trade` events (messages with a `trade` key) appear in `/data/clob/{slug}/{date}.jsonl` for at least one observed match (not `last_trade_price`; that's a signal-qualification concept, not the SDK event name).
- Spot-check envelope conformance against build plan §5.1 (timestamp_utc ISO-8601-ms-Z, sequence_number monotonic across slugs/streams, market_slug + asset_id dual-naming during v4.1-candidate-7 carry-forward, stream_type discriminator, raw payload).
- Observe across one 15-minute proactive-recycle boundary if archive spans long enough.
- Operator UAT verdict on Phase 5 acceptance.

**If empty:**
- Continue Phase 5 deferral.
- Pool is live and tailing the delta stream from the H-030-deploy moment forward; subscriptions will fire as discovery emits added events; Phase 5 smoke remains pending live tennis.
- Optionally: H-031 picks alternative scope (D-038 candidate formalization; v4.1-candidate-4 re-draft; Phase 4 design propagation work for retirement handler / Sports WS / handicap updater / first-server identification with self-await guard discipline; or another operator-ruled scope).

**H-031 prerequisites:**
- Streak math: H-030 close advances streak from 20 to 21 if bundle lands cleanly.
- DJ counter unchanged at 36.
- STATE bump v26 → v27 carrying both H-029's missing bump and H-030's; sessions_count 28 → 30 catching both.
- Phase marker `phase-3-capture-deployed-h030-phase-5-deferred-no-live-tennis`.

---

## §9 — Self-report carry-forwards (received-disciplines and watch-items)

### §9.1 — Documentation-lag gap (received-discipline for H-031+)

When repo state advances between handoff-drafting and session-close, amend the handoff before close. H-029 handoff §2 said 'H-030 opens with them not yet committed to the repo; D-034 drag-and-drop happens at Phase 4' — written before the mid-session direct-to-main commit at `f43bbf3` and not amended at close. H-030 had to discover the commit at session-open via sandbox verification rather than receive it via handoff. The verification cost was bounded but the framing-error propagation is the real cost: my Phase 4 step-8 plan was written assuming D-034 drag-and-drop for 6 files when it was 1 file (main.py). Fixable in a single operator clarification exchange; preventable by a 30-second handoff amendment at H-029 close.

Pattern generalizes: any handoff produced before session-close artifacts land becomes potentially stale by close. The fix is mechanical — amend before the present_files call.

### §9.2 — Grep-before-naming for string changes (received-discipline for H-031+)

Phase 2 §5.2 named main.py modifications at lines 24+78 (FastAPI version strings), missing the parallel phase/status fields at lines 81+87+138 that share the same version-cohort semantic. H-030 caught the gap during pre-write read of main.py and surfaced for ratification; operator ratified all four string updates plus the three Phase-2-§5.2-missed adjacents.

Pattern generalizes: when pre-registering a string change in code-shape phase (Phase 2 §X.Y or equivalent), grep for every occurrence of the old string in the file before naming the change list. Don't rely on prominent-occurrence enumeration — strings come in cohorts.

### §9.3 — §9.9 reconstruction-from-summary at code AND documentation level (received-discipline propagation)

The H-029 §6.4 / H-028 §9.9 lineage applied to documentation-state at H-030 session-open. When reconstructing rulings, decision lists, or inheritance claims from a handoff narrative, flag the reconstruction explicitly and verify against source before the reconstruction becomes load-bearing. Summaries compress; the compression can drop detail that matters. Applies to: code-state (H-029 §9.9 lesson — verify repo state against handoff claims at session open), governance-state (H-028 lesson — verify DJ entries against handoff narrative summary), and now framing-state at H-030 (verify D-036 directly before treating handoff §3.3 inheritance list as established).

The triple-source pattern (handoff narrative + STATE prose + governance-doc primary text) usually has at least one source available for cross-check; use it.

### §9.4 — Streak-math off-by-one correction (lineage propagation)

H-029 handoff §7 wrote 'Streak holds at 19+ pending H-030 close.' Correct math: H-029 was the 19th consecutive clean-discipline session (H-010 → H-028 was 19 sessions per H-028 close ratification 'Nineteen consecutive clean-discipline sessions (H-010 → H-028) if close bundle lands cleanly'). H-029 clean partial close → 20. H-030 clean close → 21.

Pattern generalizes: when stating streak counts in handoffs, state the math explicitly. Example template: "H-N landed clean → streak was X at H-N+1 open; H-N+1 clean close advances to X+1." Bare numbers like '19+' invite ambiguity; arithmetic statements don't.

### §9.5 — `pm-tennis-api` deploy regime is Manual + Build Filter `src/**` persistent (forward-propagation observation)

Not a regression; persistent state. Distinct from `pm-tennis-stress-test` (also Manual, no Build Filter). Distinct from D-014's 'auto-deploy on main' framing in DJ. The H-016 → H-026 "via Auto-Deploy" labels in `pm-tennis-api` Events history have a separate explanation (Render UI label artifact, or a different historical setting) that H-030 did not investigate; not load-bearing for forward work.

**Step 8 candidate refinement for Phase 4 propagation:** pre-deploy step '0a confirm operator will Manual Deploy' for any service not on Auto-Deploy. **D-038 candidate territory** (clarify per-service deploy regime in DJ) deferred to H-031+ if operator wants formalization.

### §9.6 — Phase 5 watch-items at first live-smoke (carry from H-029 §6.1)

Two watch-items inherited from H-029 carry forward to H-031 (or whichever session lands the first live Phase 5 smoke):

- **§4.6 sync file I/O in `ArchiveWriter.write`**. Called from sync `on('message')` callback running in asyncio event loop. At ~20 matches × realistic tick rates (probably higher than sub-10-Hz during bursts like set ends or deuce sequences), append-flush-close under the event loop can produce visible lag. Watch Phase 5 for event-loop stalls or message-delivery delays at high-activity moments. Fix if observed: route writes through async queue.

- **§4.7 per-message file open-append-close**. ~200+ file-open syscalls/sec at peak is real but not catastrophic. Co-watch-item with §4.6. Fix: file-handle caching keyed by (slug, date).

Neither blocks Phase 5 acceptance; both are post-Phase-5 follow-up if observed.

### §9.7 — Self-await defect Phase 4 design propagation (carry from H-029 §3.3)

H-029 surfaced the self-await defect in `unsubscribe_match`: when `_liveness_task` or `_recycle_task` triggers `_reconnect → unsubscribe_match → await on currently-executing-task`, Python raises 'RuntimeError: Task cannot await on itself.' Fix: `asyncio.current_task()` guard skips self in cancel-and-await loop.

**Generalizes to Phase 4 design discipline.** Any lifecycle task that may trigger teardown of its own connection needs the `current_task()` guard. The Phase 4 components carrying this pattern:

- **Sports WS client** (will run its own per-match connections with recycle / liveness mirroring `clob_pool.py`).
- **Retirement and suspension handler** (RAID I-005, Sev 7) — calls unsubscribe path from inside callback.
- **Handicap updater** (RAID I-010, Sev 6) — may run timer tasks calling reconciliation paths.
- **First-server identification** (RAID I-003, Sev 8) — hooks into Sports WS first-message callback.

**Test-fixture pressure (millisecond-scale lifecycle intervals) deliberately surfaces reentrancy/race defects under test rather than in production.** Without aggressive timeouts forcing the probe to fire during every test, the H-029 defect would have shipped silently and degraded over hours-to-days.

This list is documented per §9.3 (reconstruction-from-summary discipline) — H-030 read D-036 Commitment directly to verify the inheritance list rather than reconstructing from H-029 handoff §3.3 narrative.

### §9.8 — Finding B near-verbatim mapping (carry from H-029 §6.3)

Plan §4.4's `last_trade_price` is a signal-qualification concept, not an SDK event name. The SDK event that delivers it is `'trade'`, fired when the incoming message contains a `'trade'` key. The per-trade timestamp `tradeTime` required for §4.4's 30-second recent-taker-activity filter comes from `Trade.tradeTime`, not from `MarketData.stats.lastTradePx` (the latter is a rolling stats-block field on every market_data update, not per-trade). Subscribing to `subscribe_trades` is therefore NOT substitutable with reading `stats.lastTradePx` from market_data: `lastTradePx` in stats lacks the per-trade timestamp §4.4 requires.

This mapping affects: Phase 5 smoke-review assertion phrasing (preserved in §8 above as "Trade events appear in archive" not "last_trade_price events"); Phase 5+ dashboard signal-panel design when building the signal-qualification filter; observation-window implementation; window-close analysis. Near-verbatim preservation here saves every future session from re-deriving the SDK-vs-plan terminology distinction.

### §9.9 — Per-match connection model grounding (carry from H-029 §6.5)

Per operator ruling at H-029 Phase 2 ratification: the per-match connection choice in `clob_pool.py` is grounded in **D-036's operational-peak finding (~20 concurrent matches at absolute peak), NOT in an SDK structural constraint**. The SDK supports a single connection subscribing to many slugs (`subscribe_market_data(request_id, market_slugs=[slug1, slug2, ...])`). The optimization is worth zero at our operational surface, and per-match gives cleaner failure isolation, lifecycle, and per-subscribe `request_id` attribution. Future session reading `clob_pool.py` and wondering "why not shared connection" has the rationale documented here, in the `clob_pool.py` module docstring, and in H-029 §6.5.

### §9.10 — Discipline carry-forward propagation set (cumulative as of H-030)

For H-031+ session-open self-orientation. Not exhaustive — handoff documents are the primary source for received-disciplines:

- **Standing disciplines (apply every session):** D-019 research-first; R-010 / D-016 commitment 2 no-fabrication; D-021 unit tests + live smoke per deliverable; D-035 / RB-002 Step 0 Auto-Deploy-state pre-flight on `pm-tennis-stress-test`; envelope-pruning convention (collapsed arc-entries; no Letter_from_H-NNN-Claude); H-014-settled stricter-reading pruning of `resolved_operator_decisions_current_session`.
- **From H-026:** follow-convention-not-change-convention at artifact-type ambiguity; convention-discovery-by-observation.
- **From H-028:** scope-framing-questions-explicit-at-phase-open (D-036 lesson); code-state verification at session-open before pre-registration ratification; full SDK constructor introspection when planning to use a class.
- **From H-029 (this carry-forward set):** §3.3 self-await defect lesson Phase 4 propagation; §9.9 reconstruction-from-summary at code level (verify repo state against handoff claims); fast-lifecycle-test-fixture discipline.
- **From H-030 (new this session):** §9.1 documentation-lag gap (amend handoff before close when repo state advances mid-session); §9.2 grep-before-naming for string changes; §9.3 §9.9 at documentation-state level (verify primary source before treating reconstructed claims as load-bearing); §9.4 streak-math explicit arithmetic; §9.5 pm-tennis-api Manual + Build Filter regime + Step 8 '0a confirm Manual Deploy' candidate.

---

## STATE diff summary (Playbook §2.3.6 item 11)

- `project.plan_document.pending_revisions`: appended `v4.1-candidate-7` (§5.6 path template `{asset_id}` → `{market_slug}` per H-029 Finding D). Count: 6 → 7.
- `project.state_document.current_version`: 26 → 27.
- `project.state_document.last_updated`: 2026-04-22 → 2026-04-24.
- `project.state_document.last_updated_by_session`: H-028 → H-030.
- `phase.current`: `phase-3-closed-d036-phase-4-opening-at-h029` → `phase-3-capture-deployed-h030-phase-5-deferred-no-live-tennis`.
- `phase.current_work_package`: H-029 + H-030 narrative compact summary appended.
- `sessions.last_handoff_id`: H-028 → H-030.
- `sessions.next_handoff_id`: H-029 → H-031.
- `sessions.sessions_count`: 28 → 30 (catching both H-029 and H-030).
- `sessions.most_recent_session_date`: 2026-04-22 → 2026-04-24.
- `open_items.resolved_operator_decisions_current_session`: H-028 entries pruned per H-014-settled; three H-030 arc-entries added per envelope-pruning convention.
- `scaffolding_files.STATE_md`: `current_version` 26 → 27; `committed_to_repo` reset to pending; `committed_session` H-028 → H-030; `note` rewritten for H-030.
- `scaffolding_files.Handoff_H028_md.committed_to_repo`: pending → true.
- `scaffolding_files.Handoff_H029_md`: new entry; `committed_to_repo: true`; `committed_session: H-029`; deliberate direct-to-main mid-H-029 at `f43bbf3`.
- `scaffolding_files.Handoff_H030_md`: new entry; `committed_to_repo: pending`.
- `phase_2_files.main_py`: `committed_session` H-009 → H-030; `last_modified_session` added (H-030); `size_bytes` 2989 → 5211; `line_count` 87 → 137; `version_string` `0.1.0-phase2` → `0.1.0-phase3-capture`; `sha256` updated; `notes` rewritten.
- `phase_2_files.requirements_txt`: new entry; `last_modified_session: H-029`; `polymarket-us==0.1.2` line added.
- `phase_2_files.src_capture_archive_writer_py`: new entry (H-029 capture-component file).
- `phase_2_files.src_capture_clob_pool_py`: new entry (H-029 capture-component file).
- `phase_2_files.tests_test_archive_writer_py`: new entry (H-029 test file, 29 tests passing).
- `phase_2_files.tests_test_clob_pool_py`: new entry (H-029 test file, 28 tests passing).
- Prose subsection: H-030 overlay added as new "Where the project is right now"; H-028 paragraph re-tagged as "(as of H-028 — preserved-overlay)".
- Prose footer: `v26 / H-028` → `v27 / H-030`.

---

*End of Handoff_H-030. H-031 opens with: session-open self-audit; read this handoff; verify STATE v27 + scaffolding entries on disk; check `/data/clob/` on Render disk for accumulated archive; two-path decision per §8 (retrospective Phase 5 if non-empty; continued Phase 5 deferral or alternative-scope ruling if empty). Streak: 21 if H-030 close bundle lands cleanly.*
