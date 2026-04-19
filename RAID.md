# RAID.md — PM-Tennis Risk, Assumption, Issue, Decision Log
**Last updated:** H-010 session close (2026-04-19)

---

## Risks

| ID | Risk | Severity | Mitigation | Status |
|----|------|----------|------------|--------|
| R-001 | Polymarket US API changes (endpoint shapes, auth, rate limits, fee schedule, tennis taxonomy) | High | Raw envelope storage; meta.json full discovery payloads; quarterly taxonomy review; fee-schedule change ends observation window and requires breakeven re-derivation | Open |
| R-002 | Silent CLOB WebSocket stall (ping/pong continues but messages stop) | High | Proactive 15-minute recycle; 90-second liveness probe backstop; pooled connections so single stall affects ≤25% of coverage | Open |
| R-003 | Sports WS / Gamma name correlation failure | Medium | Manual overrides file at `data/overrides/name_aliases.json`; unseen-gameId buffer across two discovery cycles; drops logged at WARN | Open |
| R-004 | Late match discovery (<5 min before live) | Low | Captured in full; excluded from window-close signal evaluation (insufficient pre-match ticks for 5-tick median handicap) | Open |
| R-005 | Host downtime (Render service restart, provider maintenance) | Medium | Render restart policy; recycle-and-reconnect produces clean snapshot-after-gap archive sequence | Open |
| R-006 | Storage growth faster than projected or disk failure between rotations | Medium | Nightly gzip (~10x compression); nightly backup sync to object storage; quarterly cold archive | Open — elevated relevance post-H-009 (see R-012) |
| R-007 | Polymarket US internal MM desk activation changes book dynamics | Low | Monitor announcements; treat pre/post-launch data as separate regimes in window-close analysis if launch falls in window | Open |
| R-008 | Adverse selection on passive fills | High | Replay simulator (Phase 6) computes post-fill price-drift metric net of fair-price movement over 30s; significantly negative net drift fails the window (Section 9.3 seventh criterion) | Open |
| R-009 | Statistical power at small sample | High | Window runs to n=250 signals or 60 calendar days; pass criterion is Bayesian posterior (true win rate > breakeven) at ≥80% probability, not fixed threshold | Open |
| **R-010** | **Claude fabrication of external endpoints or internal symbols** | **High** | **Research-first discipline per D-016 commitment 2: before writing code that calls an external endpoint or imports a symbol from a pre-existing module, Claude produces a short research summary citing the actual documentation (endpoints) or module definition (symbols). Fabrication is a tripwire.** | **Open — new H-009** |
| **R-011** | **Session-close ritual failure (missed handoff when session ends abruptly mid-task)** | **Medium** | **Per D-016 commitment 3 and Playbook §2.5.2: Claude proactively offers to produce the handoff when the session seems near close. Missed-handoff at next session triggers Failure-mode-1.5.2 reconstruction per Playbook §9.3.** | **Open — new H-009** |
| **R-012** | **Phase 2 raw-poll archive growth outpaces Phase 4 compression arrival (~290 MB/day uncompressed; 10 GB disk)** | **Medium** | **Phase 4 ships nightly gzip compression. Until Phase 4, disk has ~35-day runway from 2026-04-19. Phase 3 attempt 2 scope should include a design decision on whether to add compression earlier, rotate files, or live with the runway.** | **Open — new H-009** |

---

## Assumptions

| ID | Assumption | Logged | Phase | Status |
|----|------------|--------|-------|--------|
| A-001 | Polymarket US Maker Rebates Program (25% rebate, taker Θ=0.05) is in effect and reflects the April 3 2026 schedule captured in `fees.json` | H-001 | 1 | Active |
| A-002 | Promo 50% taker rebate window extends through April 30 2026; `fees.json` and `breakeven.json` computed accordingly | H-005 | 1 | Active — verify before May 1 |
| A-003 | Render (managed PaaS) is the backend host per Section 1.5.1 substitution for Hetzner VPS | H-001 | 1 | Active |
| A-004 | Sackmann P(S) tables, pooled across tours, produce log-odds deltas whose distributional equivalence across tours is acceptable for Phase 1; refinement post-build if deltas diverge >15% at high-leverage states | H-001 | 1 | Active |
| A-005 | Game-level signal model (state tuple without point-level dimensions) is viable given Sports WS game-boundary-only delivery — confirmed by D-006 | H-005 | 1 | Active — confirmed |
| A-006 | best_of_5 Parquet table with 226 states / 31,343 transitions is acceptable for Phase 1 with shrinkage fallback covering rare states | H-005 | 1 | Active |
| A-007 | Exit-based P&L model (blended 70% passive / 30% sell-at-market) correctly represents the strategy's 10-minute exit rule; breakeven win rate = 58.2% | H-005 | 1 | Active — locked in `breakeven.json` |
| **A-008** | **Sports WS and CLOB WS endpoints and subscription formats will be researched from Polymarket US / Sportradar documentation at the start of Phase 3 attempt 2, not assumed or inferred. Confirmation by operator before any code references these endpoints.** | **H-009** | **3 attempt 2** | **Active — new H-009** |
| **A-009** | **Participant type in Polymarket US gateway responses may be `PARTICIPANT_TYPE_TEAM` or `PARTICIPANT_TYPE_PLAYER`; discovery extractor handles both. H-007 handoff claim that tennis uses `PLAYER` exclusively is corrected per H-009 V2 finding that observed events use `TEAM`.** | **H-009** | **2** | **Active — new H-009** |

---

## Issues

| ID | Issue | Severity | Action | Status |
|----|-------|----------|--------|--------|
| I-001 | Sports WebSocket point-level granularity — unknown whether public WS delivers per-point or per-game transitions | 7 | Phase 1 verification: capture 15+ min of live match and inspect sports.jsonl | ✅ **Resolved H-005** — Game-level only confirmed against two live Challenger matches (Tallahassee and Santa Cruz, 2026-04-18). Decision D-006 adopted. See `docs/sports_ws_granularity_verification.md`. |
| I-002 | CLOB pool asset-cap stress test — soft 150-asset pool cap not yet verified under stress | 2 | Deferred to Phase 3 when capture code skeleton exists | Open — deferred to Phase 3 attempt 2 |
| I-003 | First-server identification at match start — wrong player as first-server mirrors all state server dimensions | 8 | Phase 3: on first Sports message with live==true, record first-server in meta.json with explicit flag; window-close cross-check | Open — Phase 3 attempt 2 |
| I-004 | Tiebreak state representation — points 0..N at 6-6 outside standard (0..3) schema | 7 | State tuple includes in_tiebreak boolean and tb_points_a/b counters; P(S) lookup distinguishes tiebreak states | Open — Phase 3 attempt 2 implementation |
| I-005 | Retirement and suspension — mid-match retirement produces extreme price moves unrelated to score state | 7 | On Sports-WS status → "suspended", disable signal evaluation; on "finished"/"cancelled" with partial score, mark retired and exclude from window-close | Open — Phase 3 attempt 2 |
| I-006 | Maker-rebates-program artifact vs real mispricing — MM repositioning may look like undershoot | 7 | Section 4.4 recent-taker-activity filter: last_trade_price event must be present within 30s before signal | Open — Phase 4/5 |
| I-007 | Two-client sync and manual-log race (dashboard vs iPhone app) | 7 | Intent-first logging; app_displayed fields on envelopes; daily reconciliation; max 10% discrepancy rate in secondary criterion | Open — Phase 7 |
| I-008 | Operator fatigue and coverage gaps biasing secondary criterion | 7 | Pre-committed daily coverage windows; operator_availability.jsonl via dashboard toggle; signals outside active windows recorded but excluded from measured performance | Open — Phase 7 |
| I-009 | JS/Python fair-price implementation drift | 6 | Shared test vector in CI; both implementations produce identical output within numerical tolerance; Netlify build fails on divergence | Open — Phase 5 |
| I-010 | Stale pre-match handicap on lightly-traded matches | 6 | Last-5-tick median; 30-minute max-age on most recent tick; older handicaps marked stale and excluded from signal evaluation | Open — Phase 3 attempt 2 / Phase 4 |
| I-011 | Commitment-file immutability during observation | 6 | Daily SHA-256 checksum in healthcheck; OBSERVATION_ACTIVE soft lock; optional GitHub Actions check | Open — Phase 7 |
| **I-012** | **Phase 3 attempt 1 failed via fabricated Sports WS URL + fabricated `DiscoveryConfig` symbol. Option A1 revert executed at H-009; Phase 3 attempt 2 pending.** | **8** | **See D-016. Revert validated V1–V7 all passing. Phase 3 attempt 2 begins from c63f7c1d-equivalent repo state with research-first discipline per R-010.** | **Open — Phase 3 attempt 2** |
| **I-013** | **H-008 missed session-close ritual — no handoff produced; STATE and DecisionJournal ran ahead of repo through H-009 session open.** | **7** | **Addressed at H-009: DecisionJournal backfilled D-009–D-015 as reconstructed entries; D-016 and D-017 added for H-009 decisions and H-006 plan revision respectively. STATE v7 supersedes v6. Future mitigation: R-011 (session-close discipline).** | **✅ Resolved H-009** |
| **I-014** | **v4.1-candidate plan-text patch: Section 5.6 lists `data/baseline/` as a Render persistent disk path, but baseline files live in the repo under `baseline/`, not on disk.** | **3** | **Apply under Playbook §12 when next plan revision is cut. Tracked in STATE `pending_revisions`.** | **Open — awaiting next plan revision** |
| **I-015** | **The plan's "150-asset pool cap" (§5.4 and §11.3) does not correspond to any documented Polymarket US limit. H-010 research against `docs.polymarket.us` found one explicit numeric cap on Markets WebSocket: 100 market slugs per subscription. 150 is inherited plan language without a cited source. The stress-test deliverable has implicitly shifted from "verify the documented cap" to "characterize undocumented connection and subscription limits."** | **3** | **Dual action. (a) Plan text: §5.4 "bounded by the soft 150-asset cap" and §11.3's related line get revised in the next plan revision to reflect the actual documented cap structure (100 slugs per subscription, undocumented concurrency). Tracked in STATE `pending_revisions` alongside I-014. (b) Phase 3 attempt 2 stress test proceeds under the reframed objective per `docs/clob_asset_cap_stress_test_research.md` v3. No immediate code change.** | **Open — awaiting next plan revision and stress-test execution** |

---

## Decisions

| ID | Decision | Made | Commitment | Status |
|----|----------|------|------------|--------|
| D-001 | Use Render (managed PaaS) as backend host, replacing Hetzner VPS; Netlify for frontend; GitHub for source | H-001 | Environment is Render + Netlify + GitHub throughout | Active |
| D-002 | Pilot-then-freeze for signal_thresholds.json; sub-questions open | H-002 | Full specification at Phase 7 | Open — Phase 7 |
| D-003 | Sports WS granularity as go/no-go gate | H-002 | Resolved by D-006 | Resolved |
| D-004 | Out-of-protocol trigger phrase is "out-of-protocol"; does not override OBSERVATION_ACTIVE lock | H-002 | OOP discipline per Playbook §5 | Active |
| D-005 | Public GitHub repository; no secrets in repo | H-002 | SECRETS_POLICY.md authoritative | Active |
| D-006 | Handoff carrier is markdown files | H-002 | `Handoff_H-NNN.md` per session | Active |
| D-007 | Session-open self-audit block is mandatory | H-002 | Per Playbook §1 | Active |
| D-008 | Section 1.5 forward references are aspirational; scaffolding realizes them | H-002 | Scaffolding files implement §1.5's described behavior | Active |
| D-009 | H3 hypothesis (hold-strategy rehabilitation) dropped from v4 | H-006 | v4 tests H1 and H2 only | Locked |
| D-010 | Conviction scoring + exit context ship together at Phase 5 | H-006 | Neither ships without the other | Locked |
| D-011 | Pilot-then-freeze protocol content deferred to Phase 7 | H-006 | Phase 7 exit gate adds pilot protocol document requirement | Open — Phase 7 |
| D-012 | Decision numbering corrected — canonical IDs per DecisionJournal | H-006 | All future IDs derive from DecisionJournal | Active |
| D-013 | Polymarket US gateway (`gateway.polymarket.us`) is correct API target, not offshore | H-007 | All Polymarket endpoints come from `gateway.polymarket.us` / `api.polymarket.us` | Locked |
| D-014 | Discovery loop runs inside `pm-tennis-api` process, not separate Render worker | H-007 | pm-tennis-api serves two roles: HTTP API + discovery worker | Locked |
| D-015 | Tennis sport slug confirmed as `tennis` with leagues `[wta, atp]` | H-007 | `TENNIS_SPORT_SLUG` default stands | Locked |
| **D-016** | **Phase 3 attempt 1 failed; Option A1 revert to c63f7c1d-equivalent state; tripwire reclassification; research-first discipline established; H-009 produces no new Phase 3 code** | **H-009** | **Phase 3 attempt 2 begins from clean baseline with R-010 / A-008 in force. Commitment-file integrity preserved throughout.** | **Active** |
| **D-017** | **v3→v4 plan revision (retroactive journaling of H-006 decision)** | **H-006 (journaled H-009)** | **v4 is the active build plan** | **Active** |
| **D-018** | **Ruling 1: first deliverable of Phase 3 attempt 2 is the deferred CLOB asset-cap stress test (I-002)** | **H-010** | **Stress test runs before CLOB pool construction** | **Active** |
| **D-019** | **Ruling 2: research-first form = standalone research document → operator review → code in a subsequent turn** | **H-010** | **Applies for duration of Phase 3 attempt 2 unless explicitly lifted** | **Active** |
| **D-020** | **Ruling 3: definition of done for first deliverable = unit tests + operator code review + stress test runs to completion against actual gateway with actual asset count** | **H-010** | **Per-deliverable acceptance bar distinct from Phase 3 exit gate** | **Active** |
| **D-021** | **Ruling 4: testing posture = unit tests + lightweight live smoke test per deliverable** | **H-010** | **No deliverable accepted on unit-test evidence alone** | **Active** |
| **D-022** | **Ruling 5: commit cadence = periodic commits within a deliverable permitted; handoff required at session end** | **H-010** | **Matches Phase 2 cadence; attempt-1 problem was missed handoff not commit frequency** | **Active** |

---

## Python version pin

Confirmed at Render deploy time (H-007 and H-009 revert deploy): Python 3.12.13 per `.python-version`. Not a RAID item, recorded here for cross-session reference.

---

## Commitment file state at H-009 close

| File | Path | Status | Session last modified |
|------|------|--------|----------------------|
| fees.json | repo root | Committed, SHA deferred to Phase 7 | H-005 |
| breakeven.json | repo root | Committed (58.2% breakeven, exit-based model), SHA deferred to Phase 7 | H-005 |
| sackmann/build_log.json | `/data/sackmann/build_log.json` (Render disk) | Committed, SHA deferred to Phase 7 | H-005 |
| signal_thresholds.json | — | Does not yet exist; created at Phase 7 pilot-complete per D-002 | — |

OBSERVATION_ACTIVE soft lock: not present (pre-observation). Commitment files modifiable under Playbook §6 discipline.

---

*RAID.md updated at H-010 session close. New items this session:*
- *Issues I-015 (150-asset-cap inheritance finding)*
- *Decisions D-018 through D-022 (Rulings 1–5 for Phase 3 attempt 2 scope)*

*Prior updates at H-009:*
- *Risks R-010, R-011, R-012*
- *Assumptions A-008, A-009*
- *Issues I-012, I-013 (resolved same session), I-014*
- *Decisions D-016, D-017*
