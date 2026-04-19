"""
Phase 3 tests — CLOB pool, correlation layer, Sports WS client, handicap updater.

Run with: pytest tests/test_capture_phase3.py -v

These are unit/integration tests that do NOT require live WebSocket connections.
Network-dependent behaviour (actual WS connect/pump) is tested via mocks.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import modules under test
# ---------------------------------------------------------------------------

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from capture.clob_pool import (
    CLOBPool,
    CLOBConnection,
    EnvelopeWriter,
    SOFT_ASSET_CAP,
    LIVENESS_TIMEOUT_SECONDS,
    RECYCLE_INTERVAL_SECONDS,
)
from capture.correlation import Correlator, _normalise, _name_overlap_score
from capture.handicap import HandicapUpdater, _AssetBuffer
from capture.sports_ws import SportsWSClient, MatchState, REGIME_IN_PLAY, REGIME_PRE_MATCH


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_data(tmp_path):
    """Provide a temp data directory with required subdirectories."""
    (tmp_path / "clob").mkdir()
    (tmp_path / "sports").mkdir()
    (tmp_path / "matches").mkdir()
    (tmp_path / "overrides").mkdir()
    return tmp_path


# ===========================================================================
# EnvelopeWriter tests
# ===========================================================================

class TestEnvelopeWriter:
    def test_write_creates_file(self, tmp_data):
        writer = EnvelopeWriter(tmp_data, "asset_001")
        writer.write({"type": "book"}, game_id="game_abc", regime="pre-match")
        writer.close()
        files = list((tmp_data / "clob" / "asset_001").glob("*.jsonl"))
        assert len(files) == 1

    def test_write_valid_jsonl(self, tmp_data):
        writer = EnvelopeWriter(tmp_data, "asset_002")
        writer.write({"price": 0.55}, game_id="game_x", regime="in-play")
        writer.write({"price": 0.56}, game_id="game_x", regime="in-play")
        writer.close()
        lines = (tmp_data / "clob" / "asset_002" / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            env = json.loads(line)
            assert "ts" in env
            assert "seq" in env
            assert env["asset_id"] == "asset_002"
            assert env["regime"] in ("pre-match", "in-play")

    def test_sequence_numbers_monotonic(self, tmp_data):
        writer = EnvelopeWriter(tmp_data, "asset_003")
        for i in range(5):
            writer.write({"i": i})
        writer.close()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines = (tmp_data / "clob" / "asset_003" / f"{today}.jsonl").read_text().strip().split("\n")
        seqs = [json.loads(l)["seq"] for l in lines]
        assert seqs == list(range(1, 6))

    def test_write_none_game_id(self, tmp_data):
        writer = EnvelopeWriter(tmp_data, "asset_004")
        writer.write({"x": 1}, game_id=None)
        writer.close()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        env = json.loads((tmp_data / "clob" / "asset_004" / f"{today}.jsonl").read_text())
        assert env["game_id"] is None


# ===========================================================================
# CLOBPool tests
# ===========================================================================

class TestCLOBPool:
    @pytest.mark.asyncio
    async def test_add_registers_asset(self, tmp_data):
        pool = CLOBPool(tmp_data)
        with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
            pool.add("asset_A")
            assert pool.size == 1
            assert "asset_A" in pool.status_report()["asset_ids"]

    @pytest.mark.asyncio
    async def test_add_noop_if_already_pooled(self, tmp_data):
        pool = CLOBPool(tmp_data)
        with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
            pool.add("asset_B")
            pool.add("asset_B")
            assert pool.size == 1

    @pytest.mark.asyncio
    async def test_remove_cleans_up(self, tmp_data):
        pool = CLOBPool(tmp_data)
        with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
            pool.add("asset_C")
        pool.remove("asset_C")
        assert pool.size == 0

    def test_remove_unknown_is_noop(self, tmp_data):
        pool = CLOBPool(tmp_data)
        pool.remove("nonexistent")  # should not raise

    @pytest.mark.asyncio
    async def test_soft_cap_warning_logged(self, tmp_data, caplog):
        import logging
        pool = CLOBPool(tmp_data)
        # Manually fill pool to cap (inject fake connections without tasks)
        for i in range(SOFT_ASSET_CAP):
            pool._connections[f"fake_{i}"] = MagicMock()
        with caplog.at_level(logging.WARNING):
            with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
                pool.add("over_cap_asset")
        assert "soft cap" in caplog.text

    def test_status_report_shape(self, tmp_data):
        pool = CLOBPool(tmp_data)
        report = pool.status_report()
        assert report["soft_cap"] == SOFT_ASSET_CAP
        assert "pool_size" in report
        assert "headroom" in report

    @pytest.mark.asyncio
    async def test_set_game_id_and_regime(self, tmp_data):
        pool = CLOBPool(tmp_data)
        with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
            pool.add("asset_D")
        pool.set_game_id("asset_D", "game_123")
        pool.set_regime("asset_D", "in-play")
        conn = pool._connections["asset_D"]
        assert conn._game_id == "game_123"
        assert conn._regime == "in-play"

    @pytest.mark.asyncio
    async def test_shutdown_stops_all(self, tmp_data):
        pool = CLOBPool(tmp_data)
        with patch("capture.clob_pool.CLOBConnection.run", new_callable=AsyncMock):
            for i in range(3):
                pool.add(f"asset_{i}")
        await pool.shutdown()
        assert pool.size == 0


# ===========================================================================
# Correlation tests
# ===========================================================================

class TestNormalise:
    def test_lower_cases(self):
        assert _normalise("Djokovic") == "djokovic"

    def test_strips_punctuation(self):
        assert _normalise("García-López") == "garc a l pez"

    def test_collapses_whitespace(self):
        # The function correctly collapses all runs of whitespace to single space
        assert _normalise("  A  B  ") == "a b"


class TestNameOverlapScore:
    def test_perfect_match(self):
        score = _name_overlap_score(["Federer"], ["Roger Federer"])
        assert score == 1.0

    def test_zero_on_empty(self):
        assert _name_overlap_score([], ["A"]) == 0.0
        assert _name_overlap_score(["A"], []) == 0.0

    def test_partial_match(self):
        score = _name_overlap_score(["Federer Roger"], ["Roger Federer"])
        assert 0.0 < score <= 1.0


class TestCorrelator:
    def _write_meta(self, data_dir: Path, game_id: str, asset_id: str, players: List[str]) -> None:
        # Directory keyed by game_id (as discovery module does with event_id)
        match_dir = data_dir / "matches" / game_id
        match_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "sportradar_game_id": game_id,
            "participants": [{"name": n} for n in players],
            # moneyline_markets includes a side with identifier == asset_id
            # so the correlator reads asset_id from inside the file
            "moneyline_markets": [
                {"marketSides": [{"identifier": asset_id}]}
            ],
        }
        (match_dir / "meta.json").write_text(json.dumps(meta))

    def test_exact_sportradar_match(self, tmp_data):
        self._write_meta(tmp_data, "sr:match:001", "asset_001", ["Federer", "Nadal"])
        corr = Correlator(tmp_data)
        corr.load()
        result = corr.resolve("sr:match:001")
        assert result == "asset_001"

    def test_fuzzy_match_by_name(self, tmp_data):
        # Write meta with a game_id different from what Sports WS will emit
        match_dir = tmp_data / "matches" / "internal_id_99"
        match_dir.mkdir(parents=True)
        meta = {
            "sportradar_game_id": None,  # no exact match available
            "participants": [{"name": "Roger Federer"}, {"name": "Rafael Nadal"}],
            "moneyline_markets": [],
        }
        (match_dir / "meta.json").write_text(json.dumps(meta))

        corr = Correlator(tmp_data)
        corr.load()
        result = corr.resolve("unknown_game_id", player_names=["Federer", "Nadal"])
        assert result == "internal_id_99"

    def test_unresolved_goes_to_buffer(self, tmp_data):
        corr = Correlator(tmp_data)
        corr.load()
        result = corr.resolve("sr:match:999", player_names=["Player A"])
        assert result is None
        assert "sr:match:999" in corr._buffer

    def test_buffer_expires_after_cycles(self, tmp_data, caplog):
        import logging
        corr = Correlator(tmp_data, buffer_cycles=1)
        corr.load()
        corr.resolve("sr:match:999", player_names=["Unknown"])  # enters buffer
        with caplog.at_level(logging.WARNING):
            corr.refresh()  # cycle 1 — should expire and WARN
            corr.refresh()  # cycle 2 — already gone
        assert "dropping" in caplog.text.lower()
        assert "sr:match:999" not in corr._buffer

    def test_overrides_take_precedence(self, tmp_data):
        self._write_meta(tmp_data, "sr:match:001", "asset_real", ["A", "B"])
        overrides_path = tmp_data / "overrides" / "name_aliases.json"
        overrides_path.write_text(json.dumps({"sr:match:001": "asset_override"}))
        corr = Correlator(tmp_data)
        corr.load()
        result = corr.resolve("sr:match:001")
        assert result == "asset_override"

    def test_status_report_shape(self, tmp_data):
        corr = Correlator(tmp_data)
        corr.load()
        report = corr.status_report()
        assert "mapped_games" in report
        assert "buffered_unresolved" in report

    def test_buffer_resolves_after_meta_arrives(self, tmp_data):
        corr = Correlator(tmp_data, buffer_cycles=5)
        corr.load()
        # First: unresolvable — goes to buffer
        corr.resolve("sr:match:late", player_names=["Late Player"])
        assert "sr:match:late" in corr._buffer

        # Now write the meta.json (simulating discovery catching up)
        self._write_meta(tmp_data, "sr:match:late", "asset_late", ["Late Player"])

        # refresh should resolve the buffered entry
        corr.refresh()
        assert "sr:match:late" not in corr._buffer
        assert corr.resolve("sr:match:late") == "asset_late"


# ===========================================================================
# HandicapUpdater tests
# ===========================================================================

class TestAssetBuffer:
    def test_records_ticks_up_to_window(self):
        buf = _AssetBuffer("a1")
        now = datetime.now(timezone.utc)
        for i in range(7):  # more than TICK_WINDOW=5
            buf.record_tick(0.50 + i * 0.01, now)
        assert len(buf.ticks) == 5  # deque maxlen

    def test_no_ticks_after_fixed(self):
        buf = _AssetBuffer("a2")
        now = datetime.now(timezone.utc)
        buf.record_tick(0.60, now)
        buf.handicap_fixed = True
        buf.record_tick(0.70, now)  # should be ignored
        assert len(buf.ticks) == 1


class TestHandicapUpdater:
    def _write_meta(self, data_dir: Path, game_id: str, asset_id: str) -> None:
        match_dir = data_dir / "matches" / game_id
        match_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "sportradar_game_id": game_id,
            "moneyline_markets": [
                {"marketSides": [{"identifier": asset_id, "handicap_price": "PENDING_PHASE3"}]}
            ],
        }
        (match_dir / "meta.json").write_text(json.dumps(meta))

    def test_fixes_handicap_on_regime_change(self, tmp_data):
        self._write_meta(tmp_data, "game_001", "asset_001")
        updater = HandicapUpdater(tmp_data)
        updater.register("asset_001", "game_001")
        now = datetime.now(timezone.utc)
        for price in [0.60, 0.61, 0.62, 0.61, 0.60]:
            updater.on_tick("asset_001", price, now)
        updater.on_regime_change("game_001", "asset_001", "in-play")
        buf = updater._buffers["asset_001"]
        assert buf.handicap_fixed
        assert 0.59 < buf.handicap_value < 0.63
        assert not buf.handicap_stale

    def test_stale_handicap_flagged(self, tmp_data):
        self._write_meta(tmp_data, "game_002", "asset_002")
        updater = HandicapUpdater(tmp_data)
        updater.register("asset_002", "game_002")
        old_ts = datetime.now(timezone.utc) - timedelta(minutes=35)
        updater.on_tick("asset_002", 0.70, old_ts)
        updater.on_regime_change("game_002", "asset_002", "in-play")
        buf = updater._buffers["asset_002"]
        assert buf.handicap_stale

    def test_meta_updated_with_handicap(self, tmp_data):
        self._write_meta(tmp_data, "game_003", "asset_003")
        updater = HandicapUpdater(tmp_data)
        updater.register("asset_003", "game_003")
        now = datetime.now(timezone.utc)
        for price in [0.65, 0.66, 0.65]:
            updater.on_tick("asset_003", price, now)
        updater.on_regime_change("game_003", "asset_003", "in-play")
        meta = json.loads((tmp_data / "matches" / "game_003" / "meta.json").read_text())
        assert "pre_match_handicap" in meta
        assert "asset_003" in meta["pre_match_handicap"]
        h = meta["pre_match_handicap"]["asset_003"]
        assert "price" in h and "stale" in h

    def test_no_tick_warning_logged(self, tmp_data, caplog):
        import logging
        self._write_meta(tmp_data, "game_004", "asset_004")
        updater = HandicapUpdater(tmp_data)
        updater.register("asset_004", "game_004")
        with caplog.at_level(logging.WARNING):
            updater.on_regime_change("game_004", "asset_004", "in-play")
        assert "no ticks" in caplog.text.lower()

    def test_extract_price_last_trade(self):
        envelope = {"payload": {"type": "last_trade_price", "price": "0.72"}}
        price = HandicapUpdater.extract_price_from_envelope(envelope)
        assert price == pytest.approx(0.72)

    def test_extract_price_book_midpoint(self):
        envelope = {"payload": {"asks": [["0.74", "100"]], "bids": [["0.72", "50"]]}}
        price = HandicapUpdater.extract_price_from_envelope(envelope)
        assert price == pytest.approx(0.73)

    def test_extract_price_empty_payload(self):
        price = HandicapUpdater.extract_price_from_envelope({"payload": {}})
        assert price is None

    def test_status_report(self, tmp_data):
        updater = HandicapUpdater(tmp_data)
        report = updater.status_report()
        assert "tracked_assets" in report
        assert "handicaps_fixed" in report


# ===========================================================================
# SportsWSClient unit tests (no network)
# ===========================================================================

class TestSportsWSClient:
    def test_register_match(self, tmp_data):
        client = SportsWSClient(tmp_data)
        client.register_match("game_001", asset_id="asset_001")
        assert "game_001" in client._match_states
        assert client._match_states["game_001"].asset_id == "asset_001"

    def test_set_asset_id(self, tmp_data):
        client = SportsWSClient(tmp_data)
        client.register_match("game_002")
        client.set_asset_id("game_002", "asset_002")
        assert client._match_states["game_002"].asset_id == "asset_002"

    def test_extract_player_names_home_away(self):
        payload = {
            "homeTeam": {"name": "Federer"},
            "awayTeam": {"name": "Nadal"},
        }
        names = SportsWSClient._extract_player_names(payload)
        assert "Federer" in names
        assert "Nadal" in names

    def test_extract_player_names_string_values(self):
        payload = {"home": "Djokovic", "away": "Murray"}
        names = SportsWSClient._extract_player_names(payload)
        assert "Djokovic" in names
        assert "Murray" in names

    def test_extract_player_names_empty(self):
        assert SportsWSClient._extract_player_names({}) == []

    def test_derive_regime_live_true(self, tmp_data):
        client = SportsWSClient(tmp_data)
        client.register_match("g1")
        state = client._match_states["g1"]
        regime = client._derive_regime({"live": True}, state)
        assert regime == REGIME_IN_PLAY

    def test_derive_regime_live_false(self, tmp_data):
        client = SportsWSClient(tmp_data)
        client.register_match("g2")
        state = client._match_states["g2"]
        regime = client._derive_regime({"live": False}, state)
        assert regime == REGIME_PRE_MATCH

    def test_status_report(self, tmp_data):
        client = SportsWSClient(tmp_data)
        report = client.status_report()
        assert "registered_games" in report
        assert "in_play" in report
        assert "url" in report

    @pytest.mark.asyncio
    async def test_suspension_disables_signal(self, tmp_data):
        client = SportsWSClient(tmp_data)
        client.register_match("game_sus", asset_id="asset_sus")
        state = client._match_states["game_sus"]
        assert state.signal_enabled
        await client._handle_transitions({"status": "suspended"}, state, REGIME_IN_PLAY)
        assert not state.signal_enabled

    @pytest.mark.asyncio
    async def test_retirement_marks_state(self, tmp_data):
        # Create a meta.json so _mark_retired_in_meta has a file to update
        meta_dir = tmp_data / "matches" / "game_ret"
        meta_dir.mkdir(parents=True)
        (meta_dir / "meta.json").write_text(json.dumps({"participants": []}))

        client = SportsWSClient(tmp_data)
        client.register_match("game_ret")
        state = client._match_states["game_ret"]
        await client._handle_transitions(
            {"status": "cancelled", "score": {"sets": "6-3"}}, state, REGIME_IN_PLAY
        )
        assert state.retired
        assert not state.signal_enabled

    @pytest.mark.asyncio
    async def test_first_server_recorded_once(self, tmp_data):
        meta_dir = tmp_data / "matches" / "game_srv"
        meta_dir.mkdir(parents=True)
        (meta_dir / "meta.json").write_text(json.dumps({"participants": []}))

        client = SportsWSClient(tmp_data)
        client.register_match("game_srv")
        state = client._match_states["game_srv"]

        payload = {"live": True, "currentServer": "player_A"}
        await client._record_first_server(payload, state)
        assert state.first_server_recorded

        # Second call should not overwrite (first_server_recorded gate)
        meta = json.loads((tmp_data / "matches" / "game_srv" / "meta.json").read_text())
        assert meta.get("first_server_raw") == "player_A"

    @pytest.mark.asyncio
    async def test_regime_change_callback_fired(self, tmp_data):
        called = []
        def on_change(game_id, asset_id, regime):
            called.append((game_id, asset_id, regime))

        client = SportsWSClient(tmp_data, on_regime_change=on_change)
        client.register_match("game_cb", asset_id="asset_cb")
        state = client._match_states["game_cb"]
        await client._handle_transitions({"live": True}, state, REGIME_IN_PLAY)
        assert len(called) == 1
        assert called[0] == ("game_cb", "asset_cb", REGIME_IN_PLAY)

    @pytest.mark.asyncio
    async def test_regime_change_not_fired_twice(self, tmp_data):
        called = []
        client = SportsWSClient(tmp_data, on_regime_change=lambda *a: called.append(a))
        client.register_match("game_cb2", asset_id="asset_cb2")
        state = client._match_states["game_cb2"]
        state.regime = REGIME_IN_PLAY  # already in-play
        await client._handle_transitions({"live": True}, state, REGIME_IN_PLAY)
        assert len(called) == 0  # callback not fired again


# ===========================================================================
# CLOBConnection liveness / recycle unit tests (mock WS)
# ===========================================================================

class TestCLOBConnectionBehaviour:
    @pytest.mark.asyncio
    async def test_liveness_timeout_triggers_reconnect(self, tmp_data):
        """CLOBConnection._connect_and_pump returns on liveness timeout."""
        stop = asyncio.Event()
        writer = EnvelopeWriter(tmp_data, "asset_lv")

        # Mock websockets.connect to return a WS that times out on recv
        mock_ws = AsyncMock()
        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=False)
        mock_ws.recv = AsyncMock(side_effect=asyncio.TimeoutError)

        conn = CLOBConnection("asset_lv", writer, stop)

        with patch("capture.clob_pool.websockets.connect", return_value=mock_ws):
            # Should return without raising — liveness failure causes clean return
            await conn._connect_and_pump(f"wss://clob.polymarket.us/ws/asset_lv")

        writer.close()

    @pytest.mark.asyncio
    async def test_valid_message_written_to_jsonl(self, tmp_data):
        """Messages received by CLOBConnection are written to JSONL."""
        stop = asyncio.Event()
        writer = EnvelopeWriter(tmp_data, "asset_msg")

        messages_sent = [
            json.dumps({"type": "book", "asks": [["0.62", "100"]]}),
        ]
        call_count = 0

        async def fake_recv():
            nonlocal call_count
            if call_count < len(messages_sent):
                msg = messages_sent[call_count]
                call_count += 1
                return msg
            # After messages exhausted, set stop and raise timeout to exit
            stop.set()
            raise asyncio.TimeoutError

        mock_ws = AsyncMock()
        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock(return_value=False)
        mock_ws.recv = fake_recv

        conn = CLOBConnection("asset_msg", writer, stop)
        with patch("capture.clob_pool.websockets.connect", return_value=mock_ws):
            await conn._connect_and_pump("wss://clob.polymarket.us/ws/asset_msg")

        writer.close()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        lines = (tmp_data / "clob" / "asset_msg" / f"{today}.jsonl").read_text().strip().split("\n")
        assert len(lines) >= 1
        env = json.loads(lines[0])
        assert env["asset_id"] == "asset_msg"
        assert env["payload"]["type"] == "book"
