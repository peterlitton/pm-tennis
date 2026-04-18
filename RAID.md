# RAID.md — PM-Tennis Risk, Assumption, Issue, Decision Log
**Last updated:** H-005 session close (2026-04-18)

---

## Risks

| ID | Risk | Severity | Mitigation | Status |
|----|------|----------|------------|--------|
| R-001 | Polymarket US API changes (endpoint shapes, auth, rate limits, fee schedule, tennis taxonomy) | High | Raw envelope storage; meta.json full discovery payloads; quarterly taxonomy review; fee-schedule change ends observation window and requires breakeven re-derivation | Open |
| R-002 | Silent CLOB WebSocket stall (ping/pong continues but messages stop) | High | Proactive 15-minute recycle; 90-second liveness probe backstop; pooled connections so single stall affects ≤25% of coverage | Open |
| R-003 | Sports WS / Gamma name correlation failure | Medium | Manual overrides file at `data/overrides/name_aliases.json`; unseen-gameId buffer across two discovery cycles; drops logged at WARN | Open |
| R-004 | Late match discovery (<5 min before live) | Low | Captured in full; excluded from window-close signal evaluation (insufficient pre-match ticks for 5-tick median handicap) | Open |
| R-005 | Host downtime (Render service restart, provider maintenance) | Medium | Render restart policy; recycle-and-reconnect produces clean snapshot-after-gap archive sequence | Open |
| R-006 | Storage growth faster than projected or disk failure between rotations | Medium | Nightly gzip (~10x compression); nightly backup sync to object storage; quarterly cold archive | Open |
| R-007 | Polymarket US internal MM desk activation changes book dynamics | Low | Monitor announcements; treat pre/post-launch data as separate regimes in window-close analysis if launch falls in window | Open |
| R-008 | Adverse selection on passive fills | High | Replay simulator (Phase 6) computes post-fill price-drift metric net of fair-price movement over 30s; significantly negative net drift fails the window (Section 9.3 seventh criterion) | Open |
| R-009 | Statistical power at small sample | High | Window runs to n=250 signals or 60 calendar days; pass criterion is Bayesian posterior (true win rate > breakeven) at ≥80% probability, not fixed threshold | Open |

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

---

## Issues

| ID | Issue | Severity | Action | Status |
|----|-------|----------|--------|--------|
| I-001 | Sports WebSocket point-level granularity — unknown whether public WS delivers per-point or per-game transitions | 7 | Phase 1 verification: capture 15+ min of live match and inspect sports.jsonl | ✅ **Resolved H-005** — Game-level only confirmed against two live Challenger matches (Tallahassee and Santa Cruz, 2026-04-18). Decision D-006 adopted. See `docs/sports_ws_granularity_verification.md`. |
| I-002 | CLOB pool asset-cap stress test — soft 150-asset pool cap not yet verified under stress | 2 | Deferred to Phase 3 when capture code skeleton exists | Open — deferred to Phase 3 |
| I-003 | First-server identification at match start — wrong player as first-server mirrors all state server dimensions | 8 | Phase 3: on first Sports message with live==true, record first-server in meta.json with explicit flag; window-close cross-check | Open — Phase 3 |
| I-004 | Tiebreak state representation — points 0..N at 6-6 outside standard (0..3) schema | 7 | State tuple includes in_tiebreak boolean and tb_points_a/b counters; P(S) lookup distinguishes tiebreak states | Open — Phase 3 implementation |
| I-005 | Retirement and suspension — mid-match retirement produces extreme price moves unrelated to score state | 7 | On Sports-WS status → "suspended", disable signal evaluation; on "finished"/"cancelled" with partial score, mark retired and exclude from window-close | Open — Phase 3 |
| I-006 | Maker-rebates-program artifact vs real mispricing — MM repositioning may look like undershoot | 7 | Section 4.4 recent-taker-activity filter: last_trade_price event must be present within 30s before signal | Open — Phase 4/5 |
| I-007 | Two-client sync and manual-log race (dashboard vs iPhone app) | 7 | Intent-first logging; app_displayed fields on envelopes; daily reconciliation; max 10% discrepancy rate in secondary criterion | Open — Phase 7 |
| I-008 | Operator fatigue and coverage gaps biasing secondary criterion | 7 | Pre-committed daily coverage windows; operator_availability.jsonl via dashboard toggle; signals outside active windows recorded but excluded from measured performance | Open — Phase 7 |
| I-009 | JS/Python fair-price implementation drift | 6 | Shared test vector in CI; both implementations produce identical output within numerical tolerance; Netlify build fails on divergence | Open — Phase 5 |
| I-010 | Stale pre-match handicap on lightly-traded matches | 6 | Last-5-tick median; 30-minute max-age on most recent tick; older handicaps marked stale and excluded from signal evaluation | Open — Phase 3/4 |
| I-011 | Commitment-file immutability during observation | 6 | Daily SHA-256 checksum in healthcheck; OBSERVATION_ACTIVE soft lock; optional GitHub Actions check | Open — Phase 7 |

---

## Decisions

| ID | Decision | Made | Commitment | Status |
|----|----------|------|------------|--------|
| D-001 | Use Render (managed PaaS) as backend host, replacing Hetzner VPS; Netlify for frontend; GitHub for source | H-001 | Environment is Render + Netlify + GitHub throughout | Active |
| D-002 | *(sub-questions not yet due)* | — | — | Open — Phase 7 |
| D-003 | *(sub-questions not yet due)* | — | — | Open |
| D-004 | Python pinned to 3.12 | H-005 | `.python-version` committed to repo root | Locked |
| D-005 | Sackmann pipeline v3 adopted; three Parquet tables committed to Render disk | H-005 | `sackmann/build_ps_tables.py` v3 is the canonical builder | Locked |
| D-006 | **Game-level signal model adopted** | H-005 | State tuple: `(sets_won_a, sets_won_b, games_won_a, games_won_b, server)`. Point-level dimensions dropped from live signal evaluation. Affects Phases 3, 4, 5, 6. | Locked |
| D-007 | **Breakeven win rate = 58.2%** | H-005 | Exit-based P&L model (70% passive / 30% sell-at-market, promo window). Locked in `breakeven.json`. Section 9.3 primary decision threshold. | Locked |

---

*RAID.md updated at H-005 session close. I-001 resolved. I-002 deferred to Phase 3.*
