# PM-D.7 — Polymarket-discovered match start_time fix

**Status:** Specification locked, build instructions below
**Author:** PM-D.7 with operator (Peter)
**Date:** 2026-05-06
**Version target:** v0.8.5
**Related:** v0.8.3 — stable cross-status sort by `start_time` (see `docs/PM-Tennis-Pricing-Architecture-Handoff.md` §2.7)

---

## Current condition

The live dashboard is sorting matches incorrectly post-v0.8.3. The intent of v0.8.3 was a single chronological sort across all matches by scheduled `start_time` ascending — soonest first at the top, with rows holding their vertical position through status transitions. The implementation works, but the data feeding it is broken: most matches arrive at the sort with `start_time=None`.

Empirical state of production at 2026-05-06:

```
Total matches:   68
start_time set:   9
start_time None: 59
```

87% of matches have no start time. With the sort key `m.start_time or ""`, all 59 nulls collapse to the empty string and sort to the very top. The 9 properly-timestamped matches — all live — sort to the bottom. From the operator's perspective, this is the inverse of what was specified: the matches actively in play are the hardest to find, and a wall of upcoming matches pushes them off the visible viewport.

The pattern is unmistakable when you bucket by event_key prefix:

| Source | event_key shape | start_time | Count |
|---|---|---|---|
| API-Tennis | numeric (e.g. `12124358`) | populated correctly | 9 |
| Polymarket-only "shadow" | `pm:{ev_id}` (e.g. `pm:10894`) | `None` | 59 |

Two-source dashboard. Matches arrive on either of two paths. The API-Tennis path was fixed in v0.8.3 (`api_tennis_worker._upsert_match` always populates `start_time` regardless of status). The Polymarket-only path was not touched in v0.8.3 and still hardcodes `start_time=None` at construction time, with this comment:

```python
start_time=None,  # Polymarket doesn't expose match-start time per-event in our discovery
```

The comment is wrong. Empirical check against the live Polymarket Global gateway:

```
GET https://gateway.polymarket.us/v2/sports/tennis/events?limit=5

  id=10975  startDate='2026-05-07T06:00:00Z'  (Adam Walton vs. James McCabe)
  id=10991  startDate='2026-05-07T06:00:00Z'  (Alafia Ayeni vs. Soon-Woo Kwon)
  id=10996  startDate='2026-05-07T07:30:00Z'  (Maximus Jones vs. Akira Santillan)
```

`startDate` is a full ISO 8601 string with time and timezone. It's available on every event Polymarket lists. So why does the worker think Polymarket doesn't expose match-start time?

Root cause is in `src/polymarket_global_worker.py` line 376:

```python
event_date = (ev.get("startDate") or "")[:10]
```

The slice `[:10]` truncates the full timestamp to its first 10 characters — keeping `"2026-05-07"` and discarding `"T06:00:00Z"`. From that point on, the time has been thrown away. The `pm:` shadow Match constructor downstream then can't reconstruct what was deleted upstream, so it sets `start_time=None` with a comment explaining a non-existent limitation.

This bug pre-dates v0.8.3. Before v0.8.3 it was invisible, because matches sorted by status first (live, then upcoming) and the upcoming-block's secondary sort masked the issue. v0.8.3 unified the sort, exposing the data quality problem.

## Business need

Operator works the dashboard primarily by **vertical position memory**. A match the operator has positioned a trade in lives somewhere on the page; over a 30–90 minute trading window, the operator's eye returns to that location repeatedly. v0.8.3 was specified specifically to make that workflow viable — rows that hold position through status transitions, sorted in a single chronological order, so "the Boulter match is about a third of the way down" stays true at minute 5 and minute 50.

That workflow is currently broken in two compounding ways:

1. **Live matches are at the bottom of the page**, hidden behind a tall list of upcoming matches that haven't started yet. To watch a position the operator has to scroll past everything they don't currently care about. Every glance back takes more time than it should.

2. **The sort within the upcoming block is meaningless** — 59 rows sorted by empty-string-tiebreaker is effectively dict insertion order, which means the same match can be at row 3 in one snapshot and row 47 in the next as upstream Polymarket discovery cadence shuffles which event_id was processed first. The vertical-memory anchor doesn't survive a refresh.

The cost is operational. The operator has open positions and resting limit orders; those need monitoring. When the dashboard fights the operator's attention pattern instead of supporting it, missed-fills and missed-exits become more likely. v0.8.3 was the operator-locked answer to this; this fix is what's required to actually deliver it.

There is a second-order benefit: the Polymarket-discovered upcoming matches are precisely the ones with the longest decision lead-time. If the operator can see "ah, that match starts in 45 minutes, not 4 hours, I should think about whether to enter" — that surfaces opportunity that the current truncated date-only display can't. Today, all upcoming matches collapse to "starts sometime today"; with this fix, "starts in 45 minutes" becomes a visible signal.

## Deliverable

A live dashboard where every match has a populated `start_time`, and the sort works as v0.8.3 intended:

- The match starting soonest is at the top.
- Live matches sit chronologically alongside upcoming matches, not segregated.
- A match holds its row position when it transitions from upcoming to live.
- When two matches share a start time (common at tournaments with batched start slots), they sort by Python's stable-sort tiebreaker, also stable across snapshots.

Quantitatively: `>95%` of matches show non-null `start_time` in `/api/matches`; the operator visits the dashboard and sees soonest-first ordering matching their iPhone's tournament schedule view.

The fix is internal to the worker pipeline. No schema change, no API contract change, no frontend change. Roll-forward is a worker restart picking up the new code; rollback is reverting two files.

## Build

Three coordinated changes across two files. Each is small. The order matters because change 3 reads what change 1+2 produce.

### Change 1 — preserve the full timestamp at ingestion

File: `src/polymarket_global_worker.py`. Function: `_fetch_us_live_matches` (around line 376).

The data lossy line:

```python
event_date = (ev.get("startDate") or "")[:10]
```

Replace with:

```python
# v0.8.5 (PM-D7): preserve full startDate timestamp. Prior code truncated
# to YYYY-MM-DD only, which destroyed the time data needed for cross-status
# sort by scheduled start_time. event_date stays date-only for backward
# compatibility with downstream date-comparison callers; start_date_iso
# is the new field carrying the full ISO 8601 timestamp.
start_date_iso = ev.get("startDate") or ""
event_date = start_date_iso[:10]
```

Then in the `live.append({...})` block immediately below, add the new field:

```python
live.append({
    "us_slug": m.get("slug") or "",
    "polymarket_event_id": str(ev.get("id") or ""),
    "player_a_name": names[0],
    "player_b_name": names[1],
    "tournament_name": tournament,
    "event_date": event_date,
    "start_date_iso": start_date_iso,   # NEW v0.8.5
})
```

This is additive. Any caller that already reads `event_date` continues to work unchanged.

### Change 2 — propagate start_date_iso through slug_metadata

Same file, `polymarket_global_worker.py`. Four hand-off points copy fields out of a `live` entry into a worker-facing metadata dict. Lines around 690, 707, 718, and 1417.

Each of these dicts gains one line:

```python
{
    ...
    "event_date": um["event_date"],
    "start_date_iso": um.get("start_date_iso", ""),   # NEW v0.8.5
    ...
}
```

The pattern is uniform — every site is a pass-through. Verify all four with:

```bash
grep -n "event_date.*um\[" src/polymarket_global_worker.py
```

Audit each match. If a `live` entry is being copied without `start_date_iso`, add it.

### Change 3 — use start_date_iso in the pm: shadow Match constructor

File: `src/polymarket_worker.py`. Function around line 1866 (the `pm:`-shadow path's Match construction).

Replace this:

```python
new_match = state.Match(
    event_key=shadow_key,
    tour=tour_label,
    venue=meta.get("tournament_name", "") or "",
    round="",
    status="upcoming",
    start_time=None,  # Polymarket doesn't expose match-start time per-event in our discovery
    p1=state.Player(...),
    ...
)
```

With this:

```python
# v0.8.5 (PM-D7): start_time IS available — Polymarket's startDate carries
# a full ISO timestamp; preserved as start_date_iso through slug_metadata
# (changes 1 and 2 above). The prior code's "Polymarket doesn't expose
# match-start time" comment was incorrect — the upstream code was
# truncating the timestamp. With this fix, pm: shadow matches sort
# correctly alongside API-Tennis-keyed matches in state.snapshot()'s
# chronological sort.
pm_start_time = meta.get("start_date_iso") or None

new_match = state.Match(
    event_key=shadow_key,
    tour=tour_label,
    venue=meta.get("tournament_name", "") or "",
    round="",
    status="upcoming",
    start_time=pm_start_time,
    p1=state.Player(...),
    ...
)
```

The else-branch (~line 1891), which updates an EXISTING shadow Match in place, also needs to refresh start_time. Otherwise existing shadows keep their stale `None` until the worker restarts. Add:

```python
existing.start_time = pm_start_time
```

near the other in-place field updates (alongside `existing.p1_price_cents`, `existing.p1_rank`, etc.).

### What this does NOT change

- API-Tennis match creation path — already correct as of v0.8.3.
- `event_date` field semantics — still date-only YYYY-MM-DD; backward-compatible.
- Sort logic in `state.snapshot()` — unchanged. The sort works once the data does.
- Match dataclass schema — no new fields on `Match`; only the worker pipeline gains one.
- Public API contracts — no change.
- Worker logic, schedules, watchdog behavior, restart semantics.
- Frontend (templates, CSS, JS).

### What this DOES change

- One ingestion line in `polymarket_global_worker.py` preserves the full timestamp instead of truncating it.
- Four hand-off points pass the new field through the metadata pipeline.
- One construction site (and one update site) in `polymarket_worker.py` reads the new field instead of hardcoding `None`.

## Acceptance criteria

1. `/api/matches` returns >95% of matches with non-null `start_time`.
2. The top of the live dashboard renders the soonest-scheduled match (live or upcoming).
3. Live matches sit chronologically among upcoming matches, not segregated at the bottom.
4. `pm:`-keyed matches get a non-`None` `start_time` populated from Polymarket's `startDate`.
5. A match's vertical position holds when it transitions from upcoming to live (the v0.8.3 stability property; this fix doesn't break it).
6. No regression on API-Tennis-keyed matches.
7. The public `/api/matches` JSON shape gains no new fields. The new `start_date_iso` field is internal to the worker metadata pipeline only.

## Smoke test

After deploy and worker restart:

1. `curl https://pm-dashboard-o71w.onrender.com/api/matches` — count matches with non-null `start_time`. Expect close to 100%.
2. Visit https://pm-dashboard-o71w.onrender.com/. Verify the topmost match has the earliest `start_time` and the bottommost has the latest. Live matches should appear in their correct chronological slot, not clumped at the bottom.
3. Wait for (or pick) an upcoming match transitioning to live in the next 5–15 minutes. Confirm it holds its vertical position across the transition.
4. `grep "[PMONLY] created" application_logs` — newly-created shadows should log with the full ISO timestamp visible in the log line.

## Rollback

The change touches two files: `polymarket_global_worker.py` and `polymarket_worker.py`. No schema, no API contract, no template, no CSS, no frontend.

To roll back: revert both files. Matches with `pm:` event keys revert to `start_time=None` and sort to the top of the dashboard. The v0.8.3 sort logic is unchanged and continues to work; it just gets bad data again.

If the rollback is partial (only one of the two files), the system stays correct: change 1+2 in isolation just adds an unused field to metadata; change 3 in isolation reads a missing key from `meta` and falls back to `None` (gracefully — `or None` short-circuits on missing key).

## Open questions

1. **Field naming.** `start_date_iso` matches the upstream Polymarket field name (`startDate`) for source-traceability. Could also be `start_time_iso` or `scheduled_start_iso`. Current pick is operator-overridable.

2. **Backward-compat on `event_date`.** Several downstream callers compare `meta.get("event_date", "")` as a date-only string (e.g., `_is_within_24h` at line 1781 of `polymarket_worker.py`). Preserving `event_date` separately keeps these working without modification. If a future refactor wants to consolidate to a single field, that's a separate concern outside this ship.

3. **API-Tennis `start_time` reliability.** v0.8.3's audit reported a small minority of API-Tennis-keyed matches with `start_time=None` (less than the Polymarket-shadow count, but still nonzero). Out of scope for this fix; worth a separate follow-up investigation into whether `_start_time` is rejecting valid data or whether some API-Tennis frames genuinely lack `event_date`/`event_time`.

## Cross-references

- `docs/PM-Tennis-Pricing-Architecture-Handoff.md` §2.7 — Match ordering, stable cross-status sort (v0.8.3)
- `docs/v0.8.3-release-notes.md` — original sort change
- `src/polymarket_global_worker.py` line 376 — root-cause truncation
- `src/polymarket_worker.py` line 1872 — incorrect `start_time=None` constant
