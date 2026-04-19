"""
slug_selector — pick one fresh, active, not-ended, not-live tennis market slug
from Phase 2's immutable /data/matches/{event_id}/meta.json archive to serve as
the probe target for the D-025 hybrid-probe-first stress-test step.

Design constraints:

1. Schema source of truth is src.capture.discovery.TennisEventMeta (lines 139-193
   in discovery.py as of commit 17f44eb1). This module MUST NOT drift from that
   schema. Field names read here: event_id, moneyline_markets, active_at_discovery,
   ended_at_discovery, live_at_discovery, discovered_at, event_date.

2. Path source of truth is src.capture.discovery._meta_path. meta.json lives at
   {DATA_ROOT}/matches/{event_id}/meta.json where DATA_ROOT defaults to /data and
   is overridable via the PMTENNIS_DATA_ROOT env var (same convention as Phase 2
   discovery). This matches D-026: meta.json is under /data/matches/, NOT under
   /data/events/ (which is the raw-poll-snapshot JSONL directory).

3. Selection criteria per research-doc v4 §13.4:
     - active_at_discovery == True
     - ended_at_discovery == False
     - live_at_discovery == False  (we're probing pre-match, not a live match)
     - event_date >= today (UTC)   (skip matches scheduled in the past)
     - Prefer the most recent discovered_at (freshest record of market existence)

4. Read-only. Never writes, never mutates. Can be run repeatedly with no side
   effects beyond logging.

Per D-026 the H-012 survey recorded event 9392, aec-atp-digsin-meralk-2026-04-21
as a traceability-anchor default. We do NOT hard-code that here. The whole point
of re-selecting fresh at runtime is that survey-time candidates may have ended
by the time the probe runs.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# Same default and env-var convention as src.capture.discovery.DATA_ROOT.
# Override at test time with PMTENNIS_DATA_ROOT=/tmp/whatever.
DATA_ROOT: Path = Path(os.environ.get("PMTENNIS_DATA_ROOT", "/data"))


@dataclass(frozen=True)
class ProbeCandidate:
    """One meta.json record reduced to just the fields the probe needs."""
    event_id: str
    market_slug: str
    discovered_at: str   # ISO-8601 UTC, as written by discovery.py
    event_date: str      # YYYY-MM-DD, as written by discovery.py
    title: str           # for human-readable log lines only


class NoProbeCandidateError(RuntimeError):
    """Raised when no meta.json on disk satisfies the selection criteria."""


def _matches_dir() -> Path:
    """The directory containing per-event subdirectories.

    Mirrors src.capture.discovery._match_dir's parent. Kept private so that
    any future reshuffle of the storage layout touches one helper, not N
    callers.
    """
    return DATA_ROOT / "matches"


def _iter_meta_files(root: Path) -> list[Path]:
    """Return all meta.json files under {root}/*/meta.json.

    Uses a simple glob rather than os.walk because the layout is one level
    deep by construction ({root}/{event_id}/meta.json). If the directory does
    not exist we return []; the caller decides whether that is an error.
    """
    if not root.exists():
        return []
    return sorted(root.glob("*/meta.json"))


def _load_meta(path: Path) -> Optional[dict]:
    """Load one meta.json. Returns the parsed dict, or None on parse error.

    Parse errors are logged at WARN and the file is skipped. We do NOT raise
    because one malformed meta.json should not abort the entire probe
    selection — Phase 2's _write_meta is atomic-enough-in-practice but a
    partial write from a crash is still conceivable.
    """
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("skipping unreadable meta.json at %s: %s", path, exc)
        return None


def _extract_market_slug(meta: dict) -> Optional[str]:
    """Pull the first moneyline_markets[].market_slug from a meta.json dict.

    Per §6 survey (D-026 finding 3): distribution is uniform, one moneyline
    market per event. If the list is empty or malformed we return None and the
    caller skips this event. If the list has multiple entries we take the
    first — not ideal, but consistent with what research-doc v4 §13.2
    observed (74 events × 1 moneyline, never more), and any deviation is
    itself interesting data we surface by logging.
    """
    markets = meta.get("moneyline_markets")
    if not isinstance(markets, list) or not markets:
        return None
    first = markets[0]
    if not isinstance(first, dict):
        return None
    slug = first.get("market_slug")
    if not isinstance(slug, str) or not slug:
        return None
    if len(markets) > 1:
        log.info(
            "event %s has %d moneyline markets; using first (%s)",
            meta.get("event_id", "?"),
            len(markets),
            slug,
        )
    return slug


def _passes_status_filter(meta: dict) -> bool:
    """Require active==True and ended==False and live==False."""
    return bool(
        meta.get("active_at_discovery") is True
        and meta.get("ended_at_discovery") is False
        and meta.get("live_at_discovery") is False
    )


def _passes_date_filter(meta: dict, today: date) -> bool:
    """Require event_date to be today or future.

    event_date is written by discovery.py as YYYY-MM-DD. An unparseable or
    empty value is treated as failing the filter (conservative: if we can't
    verify it's in the future, we skip it).
    """
    event_date_str = meta.get("event_date", "")
    if not isinstance(event_date_str, str) or len(event_date_str) < 10:
        return False
    try:
        event_date = date.fromisoformat(event_date_str[:10])
    except ValueError:
        return False
    return event_date >= today


def _candidate_from_meta(meta: dict) -> Optional[ProbeCandidate]:
    """Build a ProbeCandidate if the meta.json has everything we need."""
    event_id = meta.get("event_id")
    discovered_at = meta.get("discovered_at", "")
    event_date = meta.get("event_date", "")
    title = meta.get("title", "")
    slug = _extract_market_slug(meta)
    if not isinstance(event_id, str) or not event_id:
        return None
    if slug is None:
        return None
    return ProbeCandidate(
        event_id=event_id,
        market_slug=slug,
        discovered_at=discovered_at if isinstance(discovered_at, str) else "",
        event_date=event_date if isinstance(event_date, str) else "",
        title=title if isinstance(title, str) else "",
    )


def list_candidates(
    data_root: Optional[Path] = None,
    today: Optional[date] = None,
) -> list[ProbeCandidate]:
    """Return all meta.json records passing status + date filters.

    Ordered newest-first by discovered_at (lexicographic on ISO-8601 is
    chronological-correct). Used by select_probe_slug but exposed publicly
    so diagnostics can see the full set without forcing a single pick.

    Arguments are optional and default to DATA_ROOT / today-UTC respectively.
    They exist so unit tests can point at a fixture tree and freeze time.
    """
    root = (data_root if data_root is not None else DATA_ROOT) / "matches"
    now_date = today if today is not None else datetime.now(timezone.utc).date()

    candidates: list[ProbeCandidate] = []
    for path in _iter_meta_files(root):
        meta = _load_meta(path)
        if meta is None:
            continue
        if not _passes_status_filter(meta):
            continue
        if not _passes_date_filter(meta, now_date):
            continue
        c = _candidate_from_meta(meta)
        if c is None:
            continue
        candidates.append(c)

    # Sort newest discovered_at first. Empty strings sort last.
    candidates.sort(key=lambda c: c.discovered_at, reverse=True)
    return candidates


def select_probe_slug(
    data_root: Optional[Path] = None,
    today: Optional[date] = None,
) -> ProbeCandidate:
    """Pick exactly one probe candidate, freshest first.

    Raises NoProbeCandidateError if no meta.json on disk satisfies the
    criteria. That is never a silent failure — the probe's caller is
    expected to surface it to the operator explicitly (per D-025 commitment 4
    about surfacing ambiguous outcomes rather than resolving them silently).
    """
    candidates = list_candidates(data_root=data_root, today=today)
    if not candidates:
        raise NoProbeCandidateError(
            f"no probe candidates under {data_root or DATA_ROOT}/matches "
            f"matching active=True, ended=False, live=False, event_date>=today"
        )
    chosen = candidates[0]
    log.info(
        "probe candidate selected: event_id=%s slug=%s discovered_at=%s "
        "event_date=%s (from %d eligible candidates)",
        chosen.event_id,
        chosen.market_slug,
        chosen.discovered_at,
        chosen.event_date,
        len(candidates),
    )
    return chosen
