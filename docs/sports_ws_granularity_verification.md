# Sports WebSocket Granularity Verification
**Phase 1 verification item — D-003**
**Date:** 2026-04-18
**Session:** H-005

## Finding

The public Polymarket Sports WebSocket (`wss://sports-api.polymarket.com/ws`) emits **game-level transitions only**. Point-level score data is not available on this feed.

## Evidence

Live capture against two Challenger matches (2026-04-18 ~19:55–19:59 UTC):

- Challenger Tallahassee: Joao Lucas Da Silva vs Jack Kennedy (S3 in progress)
- Challenger Santa Cruz: Mariano Kestelboim vs Federico Zeballos (S1 in progress)

Score field observed across multiple messages:
```
6-2, 2-6, 3-1  →  6-2, 2-6, 3-2  →  6-2, 2-6, 3-3
```

Messages fire at game boundaries only. No intermediate point scores (e.g. `3-1, 15-0`) were observed. The Santa Cruz match held at `0-0` across multiple polling cycles while points were being played, confirming that intra-game point state is not transmitted.

Message payload fields: `gameId`, `leagueAbbreviation`, `homeTeam`, `awayTeam`, `status`, `score`, `period`, `live`, `ended`, `eventState.type`, `eventState.score`, `eventState.period`, `eventState.tournamentName`, `eventState.tennisRound`.

No `points`, `currentGame`, or any intra-game score field was present.

## Decision

Per build plan Section 8 Phase 1 contingency:

> "If the public WS emits only game-boundary transitions, proceed with a game-level signal model and adjust the P(S) lookup granularity accordingly — the thesis is weaker but still viable at game granularity."

**Decision: proceed with game-level signal model.**

## Implications

1. **State tuple simplification.** The live signal model uses a reduced state tuple: `(sets_won_a, sets_won_b, games_won_a, games_won_b, server)`. The point-level dimensions (`points_won_a`, `points_won_b`, `in_tiebreak`, `tb_points_a`, `tb_points_b`) are dropped from the signal model. The Sackmann P(S) tables built in Phase 1 remain valid — they will be queried at game-boundary states only.

2. **Signal fires at game boundaries.** The undershoot signal is evaluated once per game won, not once per point played. Log-odds evidence per event is larger (a full game rather than a single point), making individual signals more meaningful but less frequent within a game.

3. **Tiebreak handling.** Tiebreaks are visible as game-boundary events (6-6 → 7-6). The P(S) lookup at the 6-6 game state captures the tiebreak entry; the outcome is captured at the 7-6 state. Intra-tiebreak point granularity is not available.

4. **Thesis impact.** The build plan characterises this as "weaker but still viable." The core mispricing thesis — market underreacts to a score event — still applies at game level. Break-of-serve events remain the highest-leverage signal events and are fully captured at game granularity.

5. **Sackmann table usage.** Phase 3 capture and Phase 6 replay simulator will use game-boundary state lookups only. The point-level columns in the Parquet tables (`points_won_a`, `points_won_b`, etc.) will be queried with zeros at game boundaries, which are valid states in the archive.

## RAID update

- RAID issue I-001 (Sports WS point granularity, Sev 7): **resolved — game-level only confirmed**. Downstream adjustment: game-level signal model adopted.
- Signal model granularity assumption updated accordingly in PreCommitmentRegister.

## Recorded by

Claude, session H-005, per build plan Section 8 Phase 1 verification requirement.
