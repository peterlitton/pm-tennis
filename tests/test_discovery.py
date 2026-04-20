"""
tests/test_discovery.py
Unit tests for src/capture/discovery.py — Phase 2

Coverage:
  - _extract_player_names: all participant type variants, fallbacks
  - _is_doubles_event: singles/doubles/slash detection
  - _parse_moneyline_markets: type filter, side parsing, non-moneyline excluded
  - _safe_slug: passthrough, truncation, flag
  - _parse_event: full golden-path parse, missing-id guard
  - _check_duplicate_players: same-day clash, different-day no-clash
  - _write_meta: immutability (second write is no-op)
  - _write_delta: added/removed/empty behaviour
  - verify_sport_slug: matched, unmatched, empty response

All filesystem operations use tmp_path (pytest fixture).
All network calls are mocked via monkeypatch / AsyncMock.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Patch DATA_ROOT before importing the module under test so all Path()
# references inside discovery.py resolve to tmp_path.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("PMTENNIS_DATA_ROOT", str(tmp_path))
    # Re-import to pick up the patched env var is not needed here because
    # we patch the module attribute directly below in each test that touches FS.
    return tmp_path


# Import after env patch
import importlib
import src.capture.discovery as disc


@pytest.fixture(autouse=True)
def set_data_root(tmp_path):
    """Point the module-level DATA_ROOT at tmp_path for every test."""
    original = disc.DATA_ROOT
    disc.DATA_ROOT = tmp_path
    yield
    disc.DATA_ROOT = original


# ---------------------------------------------------------------------------
# Fixtures — canonical raw event dict
# ---------------------------------------------------------------------------


def make_raw_event(
    event_id: str = "12345",
    slug: str = "federer-vs-nadal-roland-garros-2026",
    title: str = "Federer vs Nadal — Roland Garros 2026 QF",
    player_a: str = "Roger Federer",
    player_b: str = "Rafael Nadal",
    tournament: str = "Roland Garros",
    round_str: str = "QF",
    sportradar_id: str = "sr:match:99001",
    live: bool = False,
    ended: bool = False,
    active: bool = True,
    event_date: str = "2026-06-03",
    markets: list | None = None,
) -> dict:
    if markets is None:
        markets = [make_raw_moneyline_market()]
    return {
        "id": event_id,
        "slug": slug,
        "title": title,
        "active": active,
        "closed": False,
        "ended": ended,
        "live": live,
        # Note: the real Polymarket gateway response does NOT include a
        # top-level "eventDate" key — verified at H-016 against a live
        # raw payload (event 9471). Earlier versions of this fixture
        # included one and silently masked RAID I-016 (empty event_date
        # in production meta.json). The fixture now matches real
        # gateway shape: startDate is the canonical source for the
        # date, as a full ISO timestamp; discovery.py extracts the
        # YYYY-MM-DD form by slicing the first 10 characters.
        "startTime": "14:00",
        "startDate": f"{event_date}T14:00:00Z",
        "endDate": f"{event_date}T18:00:00Z",
        "seriesSlug": "roland-garros-2026",
        "sportradarGameId": sportradar_id,
        "eventState": {
            "tennisState": {
                "tournamentName": tournament,
                "round": round_str,
            }
        },
        "participants": [
            {
                "type": "PARTICIPANT_TYPE_PLAYER",
                "player": {"id": "p1", "name": player_a},
            },
            {
                "type": "PARTICIPANT_TYPE_PLAYER",
                "player": {"id": "p2", "name": player_b},
            },
        ],
        "markets": markets,
    }


def make_raw_moneyline_market(
    market_id: str = "m001",
    slug: str = "federer-win-rg26",
    active: bool = True,
) -> dict:
    return {
        "id": market_id,
        "slug": slug,
        "sportsMarketTypeV2": "SPORTS_MARKET_TYPE_MONEYLINE",
        "active": active,
        "closed": False,
        "bestBid": 0.60,
        "bestAsk": 0.62,
        "marketSides": [
            {
                "id": "s1",
                "identifier": "token_abc",
                "long": True,
                "description": "Roger Federer",
                "price": "0.62",
                "marketSideType": "MARKET_SIDE_TYPE_ERC1155",
            },
            {
                "id": "s2",
                "identifier": "token_xyz",
                "long": False,
                "description": "Rafael Nadal",
                "price": "0.38",
                "marketSideType": "MARKET_SIDE_TYPE_ERC1155",
            },
        ],
    }


def make_raw_non_moneyline_market() -> dict:
    m = make_raw_moneyline_market(market_id="m999", slug="some-spread")
    m["sportsMarketTypeV2"] = "SPORTS_MARKET_TYPE_SPREAD"
    return m


# ---------------------------------------------------------------------------
# _extract_player_names
# ---------------------------------------------------------------------------


class TestExtractPlayerNames:
    def test_two_players(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Alice"}},
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Bob"}},
        ]
        a, b = disc._extract_player_names(participants)
        assert a == "Alice"
        assert b == "Bob"

    def test_nominee_type(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_NOMINEE", "nominee": {"name": "Carol"}},
            {"type": "PARTICIPANT_TYPE_NOMINEE", "nominee": {"name": "Dave"}},
        ]
        a, b = disc._extract_player_names(participants)
        assert a == "Carol"
        assert b == "Dave"

    def test_team_type(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_TEAM", "team": {"name": "TeamA"}},
            {"type": "PARTICIPANT_TYPE_TEAM", "team": {"name": "TeamB"}},
        ]
        a, b = disc._extract_player_names(participants)
        assert a == "TeamA"
        assert b == "TeamB"

    def test_single_participant_fallback(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Solo"}},
        ]
        a, b = disc._extract_player_names(participants)
        assert a == "Solo"
        assert b == "Unknown_B"

    def test_empty_participants(self):
        a, b = disc._extract_player_names([])
        assert a == "Unknown_A"
        assert b == "Unknown_B"

    def test_unknown_type_skipped(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_UNKNOWN", "other": {"name": "Ghost"}},
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Real"}},
        ]
        a, b = disc._extract_player_names(participants)
        assert a == "Real"
        assert b == "Unknown_B"


# ---------------------------------------------------------------------------
# _is_doubles_event
# ---------------------------------------------------------------------------


class TestIsDoublesEvent:
    def test_singles_clean(self):
        assert not disc._is_doubles_event(
            "Federer vs Nadal",
            [
                {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Federer"}},
                {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "Nadal"}},
            ],
        )

    def test_slash_in_title(self):
        assert disc._is_doubles_event(
            "Smith/Jones vs Brown/Wilson",
            [],
        )

    def test_space_slash_space_in_title(self):
        assert disc._is_doubles_event(
            "Federer / Nadal vs Murray / Djokovic",
            [],
        )

    def test_four_participants(self):
        participants = [
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "A"}},
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "B"}},
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "C"}},
            {"type": "PARTICIPANT_TYPE_PLAYER", "player": {"name": "D"}},
        ]
        assert disc._is_doubles_event("A B vs C D", participants)


# ---------------------------------------------------------------------------
# _parse_moneyline_markets
# ---------------------------------------------------------------------------


class TestParseMoneylineMarkets:
    def test_picks_only_moneyline(self):
        markets = [make_raw_moneyline_market(), make_raw_non_moneyline_market()]
        result = disc._parse_moneyline_markets(markets)
        assert len(result) == 1
        assert result[0].market_id == "m001"

    def test_sides_parsed(self):
        markets = [make_raw_moneyline_market()]
        result = disc._parse_moneyline_markets(markets)
        assert len(result[0].sides) == 2
        yes_side = next(s for s in result[0].sides if s.long)
        assert yes_side.identifier == "token_abc"
        assert yes_side.description == "Roger Federer"

    def test_empty_markets(self):
        assert disc._parse_moneyline_markets([]) == []

    def test_best_bid_ask_captured(self):
        markets = [make_raw_moneyline_market()]
        result = disc._parse_moneyline_markets(markets)
        assert result[0].best_bid == pytest.approx(0.60)
        assert result[0].best_ask == pytest.approx(0.62)


# ---------------------------------------------------------------------------
# _safe_slug
# ---------------------------------------------------------------------------


class TestSafeSlug:
    def test_short_slug_unchanged(self):
        slug, truncated = disc._safe_slug("federer-vs-nadal")
        assert slug == "federer-vs-nadal"
        assert not truncated

    def test_long_slug_truncated(self):
        long_slug = "x" * 250
        slug, truncated = disc._safe_slug(long_slug)
        assert len(slug) == disc.MAX_SLUG_LENGTH
        assert truncated

    def test_exactly_max_length_not_truncated(self):
        slug = "a" * disc.MAX_SLUG_LENGTH
        result, truncated = disc._safe_slug(slug)
        assert not truncated
        assert len(result) == disc.MAX_SLUG_LENGTH


# ---------------------------------------------------------------------------
# _parse_event
# ---------------------------------------------------------------------------


class TestParseEvent:
    def test_golden_path(self):
        raw = make_raw_event()
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.event_id == "12345"
        assert meta.player_a_name == "Roger Federer"
        assert meta.player_b_name == "Rafael Nadal"
        assert meta.tournament_name == "Roland Garros"
        assert meta.round == "QF"
        assert meta.sportradar_game_id == "sr:match:99001"
        assert meta.sport_slug == disc.TENNIS_SPORT_SLUG
        assert len(meta.moneyline_markets) == 1
        assert not meta.doubles_flag
        assert not meta.slug_truncated

    def test_missing_id_returns_none(self):
        raw = make_raw_event()
        raw["id"] = ""
        assert disc._parse_event(raw) is None

    def test_long_slug_flagged(self):
        raw = make_raw_event(slug="s" * 250)
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.slug_truncated
        assert len(meta.event_slug) == disc.MAX_SLUG_LENGTH

    def test_doubles_flagged(self):
        raw = make_raw_event(title="Smith/Jones vs Brown/Wilson")
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.doubles_flag

    def test_ended_event_still_parsed(self):
        # _parse_event itself does not filter ended events; the loop does.
        raw = make_raw_event(ended=True)
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.ended_at_discovery

    def test_non_moneyline_market_excluded(self):
        raw = make_raw_event(markets=[make_raw_non_moneyline_market()])
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.moneyline_markets == []

    def test_missing_event_state_graceful(self):
        raw = make_raw_event()
        del raw["eventState"]
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.tournament_name == ""
        assert meta.round == ""

    def test_discovered_at_is_iso(self):
        raw = make_raw_event()
        meta = disc._parse_event(raw)
        from datetime import datetime
        # Should parse without error
        datetime.fromisoformat(meta.discovered_at.replace("Z", "+00:00"))

    # -- I-016 regression tests (H-016) --------------------------------
    #
    # The following three tests pin down the H-016 fix for RAID I-016
    # (event_date empty in production meta.json). The pre-fix code at
    # discovery.py line 328 read event.get("eventDate"), which the real
    # gateway response does not include. The fix sources event_date from
    # startDate[:10] instead. These tests ensure: (a) event_date is
    # populated correctly from startDate; (b) the code does NOT regress
    # back to reading a non-existent eventDate key; (c) a payload
    # missing startDate degrades safely to empty rather than raising.

    def test_i016_event_date_sourced_from_startDate(self):
        """The fix: event_date is the YYYY-MM-DD prefix of startDate."""
        raw = make_raw_event(event_date="2026-04-21")
        # Make sure the fixture actually omits eventDate — guards
        # against a future re-introduction masking the bug again.
        assert "eventDate" not in raw, (
            "fixture must NOT include eventDate; the real gateway has "
            "no such key (verified at H-016 against event 9471)"
        )
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.event_date == "2026-04-21"
        assert meta.start_date_iso == "2026-04-21T14:00:00Z"

    def test_i016_event_date_empty_when_startDate_missing(self):
        """No startDate in payload → event_date is empty, no exception.

        Conservative: an unparseable date is downstream-rejected by
        slug_selector._passes_date_filter rather than crashing here.
        """
        raw = make_raw_event()
        del raw["startDate"]
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.event_date == ""
        assert meta.start_date_iso == ""

    def test_i016_event_date_ignores_legacy_eventDate_key(self):
        """If a payload happens to include both keys, startDate wins.

        This pins the new behavior: event_date is sourced from
        startDate, never from eventDate, even if a future gateway
        change adds an eventDate key with a different value. Sources
        of truth must be unambiguous; we have one canonical date
        source.
        """
        raw = make_raw_event(event_date="2026-04-21")
        # Plant a contradicting eventDate to ensure it's ignored.
        raw["eventDate"] = "2099-01-01"
        meta = disc._parse_event(raw)
        assert meta is not None
        assert meta.event_date == "2026-04-21"
        assert meta.event_date != "2099-01-01"


# ---------------------------------------------------------------------------
# _check_duplicate_players
# ---------------------------------------------------------------------------


class TestCheckDuplicatePlayers:
    def _make_meta(self, event_id, player_a, player_b, event_date="2026-06-03"):
        raw = make_raw_event(
            event_id=event_id,
            player_a=player_a,
            player_b=player_b,
            event_date=event_date,
        )
        return disc._parse_event(raw)

    def test_no_known_events(self):
        meta = self._make_meta("1", "Alice", "Bob")
        assert not disc._check_duplicate_players(meta, {})

    def test_different_day_no_flag(self):
        meta_new = self._make_meta("2", "Alice", "Carol", event_date="2026-06-04")
        known = {"1": self._make_meta("1", "Alice", "Dave", event_date="2026-06-03")}
        assert not disc._check_duplicate_players(meta_new, known)

    def test_same_day_same_player_flagged(self):
        meta_new = self._make_meta("2", "Alice", "Carol", event_date="2026-06-03")
        known = {"1": self._make_meta("1", "Alice", "Bob", event_date="2026-06-03")}
        assert disc._check_duplicate_players(meta_new, known)

    def test_same_event_id_not_self_flagged(self):
        meta = self._make_meta("1", "Alice", "Bob", event_date="2026-06-03")
        known = {"1": meta}
        assert not disc._check_duplicate_players(meta, known)


# ---------------------------------------------------------------------------
# _write_meta (filesystem)
# ---------------------------------------------------------------------------


class TestWriteMeta:
    def test_meta_written(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        raw = make_raw_event()
        meta = disc._parse_event(raw)
        disc._write_meta(meta)
        path = disc._meta_path(meta.event_id)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["event_id"] == "12345"
        assert data["player_a_name"] == "Roger Federer"

    def test_meta_immutable(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        raw = make_raw_event()
        meta = disc._parse_event(raw)
        disc._write_meta(meta)
        # Mutate and try to overwrite
        meta.player_a_name = "OVERWRITTEN"
        disc._write_meta(meta)
        data = json.loads(disc._meta_path(meta.event_id).read_text())
        assert data["player_a_name"] == "Roger Federer"  # original preserved

    def test_handicap_stub_present(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        raw = make_raw_event()
        meta = disc._parse_event(raw)
        disc._write_meta(meta)
        data = json.loads(disc._meta_path(meta.event_id).read_text())
        assert data["handicap_player_a"] == disc.HANDICAP_STUB
        assert data["first_server"] == disc.HANDICAP_STUB


# ---------------------------------------------------------------------------
# _write_delta
# ---------------------------------------------------------------------------


class TestWriteDelta:
    def test_delta_appended(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        disc._write_delta(["id1", "id2"], ["id3"], "2026-06-03T10:00:00+00:00")
        path = disc._delta_path()
        assert path.exists()
        record = json.loads(path.read_text().strip())
        assert record["added"] == ["id1", "id2"]
        assert record["removed"] == ["id3"]

    def test_empty_delta_not_written(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        disc._write_delta([], [], "2026-06-03T10:00:00+00:00")
        assert not disc._delta_path().exists()

    def test_delta_appends_multiple_lines(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        disc._write_delta(["a"], [], "ts1")
        disc._write_delta(["b"], ["a"], "ts2")
        lines = disc._delta_path().read_text().strip().splitlines()
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# verify_sport_slug (mocked network)
# ---------------------------------------------------------------------------


class TestVerifySportSlug:
    def _make_client_with_sports(self, sports: list[dict]) -> disc.GatewayClient:
        client = MagicMock(spec=disc.GatewayClient)
        client.get_all_sports = AsyncMock(return_value=sports)
        return client

    def test_slug_found(self):
        sports = [
            {"slug": "tennis", "name": "Tennis", "leagues": []},
            {"slug": "football", "name": "Football", "leagues": []},
        ]
        client = self._make_client_with_sports(sports)
        result = asyncio.get_event_loop().run_until_complete(
            disc.verify_sport_slug(client, "tennis")
        )
        assert result is True

    def test_slug_not_found(self):
        sports = [
            {"slug": "football", "name": "Football", "leagues": []},
            {"slug": "basketball", "name": "Basketball", "leagues": []},
        ]
        client = self._make_client_with_sports(sports)
        result = asyncio.get_event_loop().run_until_complete(
            disc.verify_sport_slug(client, "tennis")
        )
        assert result is False

    def test_network_failure_raises_runtime_error(self):
        # Per D-031 (H-018): reconciles with commit bae6ee8e (2026-04-18 20:46:03)
        # which deliberately replaced SystemExit(1) with RuntimeError in
        # verify_sport_slug. Commit message: "fix: replace SystemExit with
        # RuntimeError in verify_sport_slug". Tests were not updated at that
        # time (pre-H-004, pre-single-authoring-channel). RAID I-017 tracked
        # the drift; D-031 resolves it by aligning the tests with the
        # intentional production behavior.
        client = MagicMock(spec=disc.GatewayClient)
        client.get_all_sports = AsyncMock(side_effect=Exception("connection refused"))
        with pytest.raises(RuntimeError):
            asyncio.get_event_loop().run_until_complete(
                disc.verify_sport_slug(client, "tennis")
            )

    def test_empty_sports_list_raises_runtime_error(self):
        # Per D-031 (H-018): see companion test above for full rationale.
        client = self._make_client_with_sports([])
        with pytest.raises(RuntimeError):
            asyncio.get_event_loop().run_until_complete(
                disc.verify_sport_slug(client, "tennis")
            )


# ---------------------------------------------------------------------------
# DiscoveryLoop.run_once (integration-style, mocked network)
# ---------------------------------------------------------------------------


class TestDiscoveryLoopRunOnce:
    def _make_loop(self, events: list[dict]) -> disc.DiscoveryLoop:
        client = MagicMock(spec=disc.GatewayClient)
        client.get_all_tennis_events = AsyncMock(return_value=events)
        return disc.DiscoveryLoop(client, "tennis")

    def test_new_event_writes_meta(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event()])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        assert disc._meta_path("12345").exists()

    def test_new_event_writes_delta(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event()])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        delta_path = disc._delta_path()
        assert delta_path.exists()
        record = json.loads(delta_path.read_text().strip())
        assert "12345" in record["added"]

    def test_ended_event_not_in_active(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event(ended=True)])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        assert len(loop._active) == 0

    def test_inactive_event_not_in_active(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event(active=False)])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        assert len(loop._active) == 0

    def test_event_removed_on_second_poll(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event()])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        # Second poll: event gone
        loop._client.get_all_tennis_events = AsyncMock(return_value=[])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        # Delta file should have two lines
        lines = disc._delta_path().read_text().strip().splitlines()
        assert len(lines) == 2
        removal = json.loads(lines[1])
        assert "12345" in removal["removed"]

    def test_snapshot_written(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        loop = self._make_loop([make_raw_event()])
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        snap_dir = disc._events_snapshot_dir()
        jsonl_files = list(snap_dir.glob("*.jsonl"))
        # delta file is also in events dir; find the date-named one
        date_files = [f for f in jsonl_files if f.name != "discovery_delta.jsonl"]
        assert len(date_files) >= 1

    def test_http_error_does_not_crash(self, tmp_path):
        disc.DATA_ROOT = tmp_path
        client = MagicMock(spec=disc.GatewayClient)
        client.get_all_tennis_events = AsyncMock(
            side_effect=Exception("gateway 503")
        )
        loop = disc.DiscoveryLoop(client, "tennis")
        # Should log error but not raise
        asyncio.get_event_loop().run_until_complete(loop.run_once())
        assert len(loop._active) == 0
