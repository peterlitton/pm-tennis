# STATE.md — PM-Tennis Project State
**Version:** 5
**As of:** H-005 session close (2026-04-18)

---

## Current phase

**Phase 1 — Environment and data foundation**
Status: **5 of 6 items complete. Pending operator commits, then gate to Phase 2.**

---

## Phase 1 checklist

| Item | Status | Notes |
|------|--------|-------|
| Python pinned to 3.12 | ✅ Complete | `.python-version` committed |
| Sackmann pipeline built and validated | ✅ Complete | `sackmann/build_ps_tables.py` v3; three Parquet tables on Render disk |
| `fees.json` committed | ✅ Complete | Polymarket US fee schedule per Section 2.2 |
| `breakeven.json` committed | ✅ Complete | Exit-based model; breakeven win rate = 58.2% |
| Sports WS granularity verification | ✅ Complete | Game-level only confirmed (D-006) |
| CLOB pool asset-cap stress test | ⏳ Deferred | Moved to Phase 3 when capture code skeleton exists |

---

## Pending operator commits (before Phase 2 begins)

1. `docs/sports_ws_granularity_verification.md` — produced H-005, not yet committed
2. `STATE.md` (this file, v5)
3. `RAID.md` (updated — I-001 resolved)

Phase 2 does **not** begin until all three are committed.

---

## Decisions locked

| ID | Decision | Value/Commitment |
|----|----------|-----------------|
| D-006 | Signal model granularity | Game-level. State tuple: `(sets_won_a, sets_won_b, games_won_a, games_won_b, server)`. Point-level dimensions dropped. |
| D-007 | Breakeven win rate | **58.2%** — exit-based P&L model, blended 70% passive / 30% sell-at-market, promo window. Locked in `breakeven.json`. Section 9.3 threshold. |

---

## Commitment files — status

| File | Status | SHA to verify |
|------|--------|--------------|
| `fees.json` | ✅ Committed | verify at session open |
| `breakeven.json` | ✅ Committed | verify at session open |
| `data/sackmann/build_log.json` | ✅ On Render disk | verify at session open |

Observation window not yet open. Commitment-file immutability lock (OBSERVATION_ACTIVE) not yet in place.

---

## Sackmann tables — Render persistent disk `/data/sackmann/`

| Table | States | Transitions |
|-------|--------|-------------|
| P_S_best_of_3_mens.parquet | 15,645 | 4,445,240 |
| P_S_best_of_3_womens.parquet | 12,907 | 1,621,923 |
| P_S_best_of_5_mens.parquet | 226 | 31,343 |

Note: best_of_5 table is small (179 source matches); shrinkage fallback active for rare states. Acceptable for Phase 1.

---

## Repository structure at H-005 close

```
peterlitton/pm-tennis
├── .gitignore
├── .python-version
├── README.md
├── DecisionJournal.md
├── Handoff_H-004.md
├── Handoff_H-005.md          ← to be committed
├── Orientation.md
├── Playbook.md
├── PreCommitmentRegister.md
├── RAID.md                   ← needs v update (I-001 resolved)
├── SECRETS_POLICY.md
├── STATE.md                  ← this file (v5, needs commit)
├── breakeven.json
├── fees.json
├── main.py
├── requirements.txt
├── docs/
│   └── sports_ws_granularity_verification.md   ← needs commit
├── runbooks/
│   └── Runbook_GitHub_Render_Setup.md
└── sackmann/
    ├── build_ps_tables.py
    └── fair_price.py
```

---

## Open questions requiring operator input

None blocking for Phase 2.

Carried forward (not due until later phases):
- D-002 sub-questions — Phase 7
- Object storage provider — Phase 4 decision
- Plan document revision timing — D-002/D-003 pending

---

## Next session opening actions

1. Accept handoff (H-006)
2. Confirm all three pending commits are in the repo
3. Begin **Phase 2 — Discovery and metadata**

---

## Handoff chain

| ID | Date | Summary |
|----|------|---------|
| H-001 | earlier | Initial orientation and environment setup |
| H-002 | earlier | — |
| H-003 | earlier | — |
| H-004 | 2026-04-18 | Phase 1 work begun |
| H-005 | 2026-04-18 | Phase 1 substantially complete; see above |

---

*STATE.md v5 — produced at H-005 session close.*
