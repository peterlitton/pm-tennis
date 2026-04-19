"""
Unit tests for src.stress_test.slug_selector.

Scope: everything that happens on disk and in memory, no SDK imports, no
network. The probe itself (src.stress_test.probe) is tested by its smoke
run in H-014 against the live gateway, not here — faking the SDK would be
the mock-heavy testing pattern that hides drift.

These tests build a fixture tree under tmp_path that mirrors
/data/matches/{event_id}/meta.json and exercise slug_selector against it,
overriding PMTENNIS_DATA_ROOT so no real /data is touched.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from src.stress_test import slug_selector
from src.stress_test.slug_selector import (
    NoProbeCandidateError,
    ProbeCandidate,
    list_candidates,
    select_probe_slug,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _meta(
    event_id: str,
    *,
    slug: str = "aec-atp-test-2026-04-25",
    discovered_at: str = "2026-04-19T14:00:00+00:00",
    event_date: str = "2026-04-25",
    active: bool = True,
    ended: bool = False,
    live: bool = False,
    markets: list[dict] | None = None,
    title: str = "Test A vs Test B",
    **extra: Any,
) -> dict:
    """Produce a meta.json-shaped dict matching discovery.TennisEventMeta.

    Only the fields slug_selector actually reads. Extra fields can be passed
    as kwargs to simulate real-world clutter.
    """
    if markets is None:
        markets = [
            {
                "market_id": f"mkt-{event_id}",
                "market_slug": slug,
                "active": active,
                "closed": ended,
            }
        ]
    out = {
        "event_id": event_id,
        "title": title,
        "event_date": event_date,
        "moneyline_markets": markets,
        "active_at_discovery": active,
        "ended_at_discovery": ended,
        "live_at_discovery": live,
        "discovered_at": discovered_at,
    }
    out.update(extra)
    return out


def _write_meta(root: Path, meta: dict) -> Path:
    """Write a single meta.json under {root}/matches/{event_id}/meta.json."""
    p = root / "matches" / meta["event_id"] / "meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta), encoding="utf-8")
    return p


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fresh empty data root per test, with PMTENNIS_DATA_ROOT pointed at it.

    We monkeypatch both the env var AND slug_selector.DATA_ROOT directly,
    because the module reads the env var once at import time. Real
    production code does the same — the env-var read is a module-level
    default, not a per-call fetch.
    """
    monkeypatch.setenv("PMTENNIS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(slug_selector, "DATA_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def frozen_today() -> date:
    """A single deterministic 'today' for all date-filter tests.

    Chosen to be before the fixture event_date defaults (2026-04-25) so
    candidates pass the date filter by default.
    """
    return date(2026, 4, 19)


# ---------------------------------------------------------------------------
# Positive-path tests
# ---------------------------------------------------------------------------


def test_list_candidates_returns_empty_when_directory_missing(
    data_root: Path, frozen_today: date
) -> None:
    """If /data/matches does not exist at all, return []."""
    # No 'matches' subdir created — the fixture leaves data_root empty.
    result = list_candidates(data_root=data_root, today=frozen_today)
    assert result == []


def test_list_candidates_returns_empty_when_no_events(
    data_root: Path, frozen_today: date
) -> None:
    (data_root / "matches").mkdir()
    result = list_candidates(data_root=data_root, today=frozen_today)
    assert result == []


def test_select_probe_slug_returns_single_valid_candidate(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="9001", slug="aec-atp-good-2026-04-25"),
    )
    chosen = select_probe_slug(data_root=data_root, today=frozen_today)
    assert isinstance(chosen, ProbeCandidate)
    assert chosen.event_id == "9001"
    assert chosen.market_slug == "aec-atp-good-2026-04-25"


def test_list_candidates_sorts_newest_first(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(
            event_id="old",
            slug="slug-old",
            discovered_at="2026-04-19T01:00:00+00:00",
        ),
    )
    _write_meta(
        data_root,
        _meta(
            event_id="new",
            slug="slug-new",
            discovered_at="2026-04-19T14:00:00+00:00",
        ),
    )
    _write_meta(
        data_root,
        _meta(
            event_id="middle",
            slug="slug-middle",
            discovered_at="2026-04-19T07:30:00+00:00",
        ),
    )
    candidates = list_candidates(data_root=data_root, today=frozen_today)
    assert [c.event_id for c in candidates] == ["new", "middle", "old"]


def test_select_probe_slug_picks_most_recent(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(
            event_id="older",
            slug="slug-older",
            discovered_at="2026-04-19T05:00:00+00:00",
        ),
    )
    _write_meta(
        data_root,
        _meta(
            event_id="newest",
            slug="slug-newest",
            discovered_at="2026-04-19T18:00:00+00:00",
        ),
    )
    chosen = select_probe_slug(data_root=data_root, today=frozen_today)
    assert chosen.event_id == "newest"


# ---------------------------------------------------------------------------
# Negative-path / filter tests
# ---------------------------------------------------------------------------


def test_filter_rejects_ended_events(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="ended", ended=True),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_live_events(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="live-match", live=True),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_inactive_events(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="inactive", active=False),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_past_event_dates(
    data_root: Path, frozen_today: date
) -> None:
    """An event dated yesterday is excluded even if status flags look fine."""
    yesterday = "2026-04-18"
    _write_meta(
        data_root,
        _meta(event_id="past", event_date=yesterday),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_accepts_today_event_dates(
    data_root: Path, frozen_today: date
) -> None:
    """An event dated today passes (>= today)."""
    _write_meta(
        data_root,
        _meta(event_id="today-match", event_date="2026-04-19"),
    )
    candidates = list_candidates(data_root=data_root, today=frozen_today)
    assert len(candidates) == 1
    assert candidates[0].event_id == "today-match"


def test_filter_rejects_malformed_event_date(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="bad-date", event_date="not-a-date"),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_empty_event_date(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="empty-date", event_date=""),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


# -- I-016 fallback tests (H-016) -------------------------------------
#
# When event_date is empty or unparseable, _passes_date_filter falls
# back to start_date_iso[:10]. This exists for backward compatibility
# with meta.json files written before the H-016 fix to discovery.py
# (~116 affected files at H-015 close), all of which have empty
# event_date but populated start_date_iso. See _passes_date_filter
# docstring and DecisionJournal D-028 for full context.


def test_i016_fallback_empty_event_date_with_future_start_date_iso_passes(
    data_root: Path, frozen_today: date
) -> None:
    """The pre-H-016 historical case: empty event_date but start_date_iso
    populated with a future ISO timestamp. Fallback should accept."""
    _write_meta(
        data_root,
        _meta(
            event_id="historical-empty-date",
            event_date="",
            start_date_iso="2026-04-25T08:00:00Z",
        ),
    )
    candidates = list_candidates(data_root=data_root, today=frozen_today)
    assert len(candidates) == 1
    assert candidates[0].event_id == "historical-empty-date"


def test_i016_fallback_empty_event_date_with_past_start_date_iso_rejected(
    data_root: Path, frozen_today: date
) -> None:
    """Fallback respects the date check — past start_date_iso is rejected."""
    _write_meta(
        data_root,
        _meta(
            event_id="historical-past-date",
            event_date="",
            start_date_iso="2026-01-01T08:00:00Z",  # before frozen_today
        ),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_i016_fallback_both_fields_empty_rejected(
    data_root: Path, frozen_today: date
) -> None:
    """Conservative behavior when neither field provides a date."""
    _write_meta(
        data_root,
        _meta(
            event_id="no-date-anywhere",
            event_date="",
            start_date_iso="",
        ),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_i016_fallback_malformed_event_date_falls_through_to_start_date_iso(
    data_root: Path, frozen_today: date
) -> None:
    """An unparseable event_date should also trigger the fallback,
    not bail out — defensive against any future format drift."""
    _write_meta(
        data_root,
        _meta(
            event_id="malformed-event-date",
            event_date="not-a-date",
            start_date_iso="2026-04-25T08:00:00Z",
        ),
    )
    candidates = list_candidates(data_root=data_root, today=frozen_today)
    assert len(candidates) == 1
    assert candidates[0].event_id == "malformed-event-date"


def test_i016_fallback_event_date_wins_over_start_date_iso(
    data_root: Path, frozen_today: date
) -> None:
    """When both fields are populated and parseable, event_date is the
    canonical source (start_date_iso fallback only fires when the
    primary is unusable). For meta.json written from H-016 forward,
    both should agree; this test pins the precedence regardless."""
    _write_meta(
        data_root,
        _meta(
            event_id="both-populated",
            event_date="2026-04-25",
            start_date_iso="2099-01-01T08:00:00Z",  # diverging value
        ),
    )
    candidates = list_candidates(data_root=data_root, today=frozen_today)
    assert len(candidates) == 1
    assert candidates[0].event_id == "both-populated"
    # The candidate's event_date field stays as the meta.json's
    # event_date value (slug_selector copies it through verbatim).
    assert candidates[0].event_date == "2026-04-25"


def test_i016_fallback_non_string_start_date_iso_rejected(
    data_root: Path, frozen_today: date
) -> None:
    """Defensive against weird future schema drift — non-string fallback
    value should be rejected, not raise."""
    _write_meta(
        data_root,
        _meta(
            event_id="weird-fallback",
            event_date="",
            start_date_iso=12345,  # type: ignore[arg-type]
        ),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_empty_moneyline_markets(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(event_id="no-markets", markets=[]),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_missing_moneyline_markets_key(
    data_root: Path, frozen_today: date
) -> None:
    """A meta.json with no moneyline_markets key at all should be skipped."""
    bad = _meta(event_id="no-markets-key")
    bad.pop("moneyline_markets")
    _write_meta(data_root, bad)
    assert list_candidates(data_root=data_root, today=frozen_today) == []


def test_filter_rejects_market_entry_without_slug(
    data_root: Path, frozen_today: date
) -> None:
    _write_meta(
        data_root,
        _meta(
            event_id="no-slug",
            markets=[{"market_id": "mkt-no-slug", "active": True, "closed": False}],
        ),
    )
    assert list_candidates(data_root=data_root, today=frozen_today) == []


# ---------------------------------------------------------------------------
# Robustness: malformed JSON, unreadable files
# ---------------------------------------------------------------------------


def test_malformed_json_is_skipped_not_raised(
    data_root: Path, frozen_today: date, caplog: pytest.LogCaptureFixture
) -> None:
    # One good candidate and one broken file. We should still return the
    # good one and log a warning about the broken one.
    good = _meta(event_id="good", slug="slug-good")
    _write_meta(data_root, good)

    broken_path = data_root / "matches" / "broken" / "meta.json"
    broken_path.parent.mkdir(parents=True, exist_ok=True)
    broken_path.write_text("this is not json {{{", encoding="utf-8")

    with caplog.at_level("WARNING"):
        candidates = list_candidates(data_root=data_root, today=frozen_today)

    assert len(candidates) == 1
    assert candidates[0].event_id == "good"
    assert any("skipping unreadable meta.json" in r.message for r in caplog.records)


def test_select_probe_slug_raises_when_none_eligible(
    data_root: Path, frozen_today: date
) -> None:
    # Write only disqualified candidates (one ended, one past-date).
    _write_meta(data_root, _meta(event_id="ended", ended=True))
    _write_meta(data_root, _meta(event_id="past", event_date="2026-04-10"))

    with pytest.raises(NoProbeCandidateError):
        select_probe_slug(data_root=data_root, today=frozen_today)


# ---------------------------------------------------------------------------
# Multi-moneyline edge (§6 survey observed uniform 1/event; we log but still
# pick first if a 2+ case ever appears).
# ---------------------------------------------------------------------------


def test_multi_moneyline_event_picks_first_and_logs(
    data_root: Path,
    frozen_today: date,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _write_meta(
        data_root,
        _meta(
            event_id="multi",
            markets=[
                {"market_id": "mkt-a", "market_slug": "slug-a", "active": True, "closed": False},
                {"market_id": "mkt-b", "market_slug": "slug-b", "active": True, "closed": False},
            ],
        ),
    )
    with caplog.at_level("INFO"):
        chosen = select_probe_slug(data_root=data_root, today=frozen_today)
    assert chosen.market_slug == "slug-a"
    assert any(
        "has 2 moneyline markets" in r.message for r in caplog.records
    )


# ---------------------------------------------------------------------------
# Realistic-shape smoke: verify we consume a dict that looks like the §6
# survey sample (see Handoff_H-012 §4).
# ---------------------------------------------------------------------------


def test_realistic_meta_from_h012_survey_shape(
    data_root: Path, frozen_today: date
) -> None:
    """Meta dict with the full TennisEventMeta field set from discovery.py.

    This is the shape the H-012 §6 survey confirmed on the Render disk.
    We include unused fields (sportradar_game_id, participant_type, etc.)
    to verify slug_selector gracefully ignores them.
    """
    realistic = {
        "event_id": "9392",
        "event_slug": "aec-atp-digsin-meralk-2026-04-21",
        "slug_truncated": False,
        "title": "Digvijaypratap Singh vs Mert Alkaya",
        "tournament_name": "Mexico City Challenger",
        "round": "Round of 32",
        "sport_slug": "TENNIS_SPORT_SLUG",
        "series_slug": "atp-challenger",
        "event_date": "2026-04-21",
        "start_time": "14:00",
        "start_date_iso": "2026-04-21T14:00:00Z",
        "end_date_iso": "2026-04-21T18:00:00Z",
        "player_a_name": "Digvijaypratap Singh",
        "player_b_name": "Mert Alkaya",
        "participants_raw": [],
        "moneyline_markets": [
            {
                "market_id": "mkt-9392-ml",
                "market_slug": "aec-atp-digsin-meralk-2026-04-21",
                "active": True,
                "closed": False,
                "best_bid": None,
                "best_ask": None,
                "sides": [],
            }
        ],
        "sportradar_game_id": "",
        "live_at_discovery": False,
        "ended_at_discovery": False,
        "active_at_discovery": True,
        "doubles_flag": False,
        "duplicate_player_flag": False,
        "handicap_player_a": "PENDING_PHASE3",
        "handicap_player_b": "PENDING_PHASE3",
        "handicap_captured_at": "",
        "handicap_stale": False,
        "first_server": "PENDING_PHASE3",
        "discovered_at": "2026-04-19T14:04:52+00:00",
        "discovery_session": "H-007",
    }
    _write_meta(data_root, realistic)

    chosen = select_probe_slug(data_root=data_root, today=frozen_today)
    assert chosen.event_id == "9392"
    assert chosen.market_slug == "aec-atp-digsin-meralk-2026-04-21"
    assert chosen.event_date == "2026-04-21"
    assert chosen.discovered_at == "2026-04-19T14:04:52+00:00"
