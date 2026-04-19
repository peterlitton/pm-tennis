# PM-Tennis Session Handoff — H-007

**Session type:** Phase 2 execution — Discovery and metadata
**Handoff ID:** H-007
**Session start:** 2026-04-19
**Session end:** 2026-04-19
**Status:** Phase 2 complete. Gate passed by operator. Phase 3 ready to begin next session.

---

## 1. What this session accomplished

| Item | Status |
|------|--------|
| H-006 handoff accepted | ✅ Complete |
| Polymarket US API researched (docs.polymarket.us) | ✅ Complete |
| Critical finding: Polymarket US ≠ offshore Polymarket API | ✅ Documented |
| Discovery module written (src/capture/discovery.py) | ✅ Complete |
| 46 unit tests written and passing (tests/test_discovery.py) | ✅ Complete |
| Package init files added (src/__init__.py, src/capture/__init__.py) | ✅ Complete |
| main.py updated to run discovery as background task | ✅ Complete |
| Render build command corrected to `pip install -r requirements.txt` | ✅ Complete |
| Discovery loop deployed and running on pm-tennis-api | ✅ Complete |
| Phase 2 exit gate — operator UAT verdict | ✅ PASSED |

**First poll results:** 38 active tennis events discovered, 38 meta.json files written to persistent disk, discovery delta stream initiated.

---

## 2. Decisions made this session

### D-013: Polymarket US gateway is the correct API target
**Decision:** The discovery module polls `gateway.polymarket.us` (Polymarket US public API), not `gamma-api.polymarket.com` (offshore Polymarket). These are separate products with separate API structures.
**Rationale:** Build plan Section 1.2 is explicit that the offshore Polymarket product is out of scope. The Polymarket US public gateway requires no authentication for read operations.
**Endpoints used:**
- `GET /v2/sports` — enumerate sports, verify tennis slug
- `GET /v2/sports/{slug}/events` — paginated event discovery

### D-014: Discovery loop runs inside pm-tennis-api, not as a separate service
**Decision:** The discovery background task runs as an asyncio task inside the FastAPI process on pm-tennis-api, not as a separate Render background worker service.
**Rationale:** Render persistent disks are per-service and cannot be shared between services. Running discovery inside the API service ensures both read and write access to the same `/data` disk. A separate background worker service was created and deleted during this session after this constraint was discovered empirically.
**Consequence:** pm-tennis-api now serves two roles: HTTP API (Phase 4 will expand this) and continuous discovery worker. This is architecturally sound for the project's scale.

### D-015: Tennis sport slug confirmed as "tennis"
**Decision:** The Polymarket US gateway uses sport slug `"tennis"` with leagues `["wta", "atp"]`. The default value in TENNIS_SPORT_SLUG is correct and requires no override.
**Confirmed by:** Live gateway response at startup, logged at INFO level.

---

## 3. Key technical findings

### Polymarket US API structure (confirmed live)
- Public gateway base: `https://gateway.polymarket.us`
- No authentication required for read operations
- `/v2/sports` returns `{"sports": [...]}` — the key is `"sports"` (confirmed by response shape logging)
- `/v2/sports/tennis/events` returns paginated event objects with full market data
- Tennis event objects include: `sportradarGameId` (Sports WS correlation key), `participants[]` with `PARTICIPANT_TYPE_PLAYER`, nested `markets[]` with `sportsMarketTypeV2: "SPORTS_MARKET_TYPE_MONEYLINE"`, `marketSides[]` with `identifier` (asset ID for CLOB subscription)
- Events have `active`, `live`, `ended` boolean fields for state filtering

### Participant type confirmed
- Tennis players use `PARTICIPANT_TYPE_PLAYER` with nested `player.name`
- This matches the primary branch in `_extract_player_names()` — fallbacks to NOMINEE and TEAM are present but not exercised by real tennis data

### meta.json structure
- Written once per event, immutable thereafter
- Contains handicap stubs (`PENDING_PHASE3`) for Phase 3 to populate
- Contains `sportradar_game_id` for Sports WS correlation
- Contains `participants_raw` for diagnostic inspection
- Contains `moneyline_markets` with `marketSides[].identifier` for CLOB subscription

### Issues encountered and resolved
1. GitHub browser editor corrupts Python indentation on paste — resolved by using file upload instead of editor
2. Render build command was hardcoded to `pip install fastapi uvicorn` — corrected to `pip install -r requirements.txt` in service Settings
3. `verify_sport_slug` used `raise SystemExit(1)` which killed the web server when called from a background task — replaced with `raise RuntimeError(...)`
4. Persistent disk is per-service on Render — separate background worker cannot share disk with API service; resolved by running discovery inside the API process

---

## 4. Files created / modified this session

| File | Action | Notes |
|------|--------|-------|
| src/capture/discovery.py | Created | Phase 2 discovery module |
| src/capture/__init__.py | Created | Package init |
| src/__init__.py | Created | Package init |
| tests/test_discovery.py | Created | 46 unit tests, all passing |
| main.py | Modified | Discovery background task added |
| Render build command | Modified | Changed to `pip install -r requirements.txt` |

---

## 5. Repository state at H-007 close

```
peterlitton/pm-tennis
├── src/
│   ├── __init__.py
│   └── capture/
│       ├── __init__.py
│       └── discovery.py          ← Phase 2 discovery module
├── tests/
│   └── test_discovery.py         ← 46 unit tests
├── baseline/                     ← Phase 1 baseline artifacts
├── docs/
├── runbooks/
├── sackmann/
├── .gitignore
├── .python-version
├── DecisionJournal.md
├── Handoff_H-004.md through H-007.md
├── Orientation.md
├── PM-Tennis_Build_Plan_v4.docx
├── Playbook.md
├── PreCommitmentRegister.md
├── RAID.md
├── README.md
├── SECRETS_POLICY.md
├── STATE.md
├── breakeven.json
├── fees.json
├── main.py                       ← updated with discovery background task
└── requirements.txt
```

**Render persistent disk** (`/data` on pm-tennis-api):
- `/data/events/2026-04-19.jsonl` — raw poll snapshots
- `/data/events/discovery_delta.jsonl` — delta stream (38 added on first poll)
- `/data/matches/{event_id}/meta.json` — 38 files written on first poll

---

## 6. Open questions requiring operator input

None blocking for Phase 3.

Carried forward from prior sessions:
- Object storage provider — Phase 4 decision
- Pilot-then-freeze protocol content — Phase 7 decision (D-011)

---

## 7. Pending items / notes for next session

**DecisionJournal:** Decisions D-013, D-014, D-015 made this session need to be added to DecisionJournal.md. This can be done at the start of the next session or batched — operator's call.

**v4.1 candidate patch (from H-006):** Section 5.6 of the build plan lists `data/baseline/` as a path on the Render persistent disk. This is incorrect — baseline files live in the repo under `baseline/`, not on the disk. Minor correction, handle under Playbook §12 when convenient.

**Phase 3 scope:** Full capture — CLOB pool, Sports WS client, correlation layer, JSONL archive, CLOB pool management (15-minute proactive recycle, 90-second liveness probe), Sports WS retirement/suspension handler, deferred CLOB asset-cap stress test.

**Note on `/v2/sports` intermittent empty response:** During debugging, the gateway returned empty sports lists several times before returning the correct response. This appeared to be a transient gateway issue (possibly geo-routing or cold-start behaviour). The module now handles this gracefully — it logs a RuntimeError and retries after 30 seconds rather than crashing.

---

## 8. Flagged issues / tripwires

**No tripwires fired.**

**Governance note:** D-014 (discovery runs inside API service) represents an architectural deviation from the build plan's implied separation of services. The build plan did not explicitly specify separate services for discovery and API — it described a "capture worker" and "API service" as separate Render services. This deviation is justified by the disk-sharing constraint and is logged here for transparency. Future phases should be aware that the capture worker and API share a process.

---

## 9. Claude self-report

Per Playbook §2.

**Research performed before coding:** Polymarket US API fully researched from official docs at `docs.polymarket.us` before writing any code. Critical finding that Polymarket US is a separate API from offshore Polymarket surfaced and confirmed before proceeding.

**Issues encountered:**
- GitHub browser editor indentation corruption: discovered empirically, resolved by switching to file upload
- Render build command misconfiguration: discovered from logs, corrected in service settings
- SystemExit in background task: caught from traceback, fixed in code
- Render disk per-service constraint: discovered empirically when attempting to attach disk to separate worker, resolved architecturally

**Out-of-protocol events this session:** 0. Cumulative: 0.

**Phase 2 gate:** Passed by operator after observing 38 live tennis events discovered, meta.json files written, and delta stream initiated.

---

## 10. Next-action statement

**The next session's first actions are: (1) accept handoff H-007, (2) begin Phase 3 — Capture (CLOB pool, Sports WS client, correlation layer, JSONL archive).**

Phase 3 is the longest build phase. The CLOB pool and Sports WS client are the two primary deliverables. The deferred asset-cap stress test from Phase 1 is also due in Phase 3.

---

*End of handoff H-007.*
