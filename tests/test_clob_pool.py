"""
tests/test_clob_pool.py
Unit tests for src/capture/clob_pool.py — H-029 Phase 3.

Mock discipline: MockMarketsWebSocket below mirrors phase1_sdk_surfaces.md
§3 signatures EXACTLY. If a test needs a method or signature not present
here, the test is wrong or Phase 1 introspection is incomplete.

Coverage:
  - subscribe_match wires both subscribe calls and three listeners
  - on('message') updates liveness timestamp and routes to archive
  - on('error') invokes archive.write_error with request_id attribution
  - unsubscribe_match cancels lifecycle tasks and unsubscribes both streams
  - unsubscribe_match is idempotent
  - delta-stream tail subscribes on 'added' and unsubscribes on 'removed'
  - _resolve_slug picks first active moneyline; rejects doubles_flag
  - reconnect closes and re-subscribes
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make src/capture importable from the bundle layout
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.capture import clob_pool as cp_module
from src.capture.archive_writer import _reset_sequence_counter_for_tests
from src.capture.clob_pool import (
    ClobPool,
    _md_request_id,
    _td_request_id,
)


# ---------------------------------------------------------------------------
# Mock SDK surface — matches phase1_sdk_surfaces.md §3 exactly
# ---------------------------------------------------------------------------


class MockMarketsWebSocket:
    """Mock that matches MarketsWebSocket surface from phase1_sdk_surfaces.md
    §3 (constructor, three subscribe methods, on/off, connect/close,
    unsubscribe, is_connected)."""

    def __init__(self):
        self._listeners = defaultdict(list)
        self.is_connected = False
        self.connect_calls = 0
        self.close_calls = 0
        # list of tuples: (request_id, subscription_type, market_slugs)
        self.subscribed: list[tuple[str, str, list[str]]] = []
        self.unsubscribed: list[str] = []

    async def connect(self) -> None:
        self.is_connected = True
        self.connect_calls += 1

    async def close(self) -> None:
        self.is_connected = False
        self.close_calls += 1

    async def subscribe_market_data(self, request_id, market_slugs):
        self.subscribed.append((request_id, "SUBSCRIPTION_TYPE_MARKET_DATA", market_slugs))

    async def subscribe_market_data_lite(self, request_id, market_slugs):
        self.subscribed.append((request_id, "SUBSCRIPTION_TYPE_MARKET_DATA_LITE", market_slugs))

    async def subscribe_trades(self, request_id, market_slugs):
        self.subscribed.append((request_id, "SUBSCRIPTION_TYPE_TRADE", market_slugs))

    async def unsubscribe(self, request_id):
        self.unsubscribed.append(request_id)

    def on(self, event, callback):
        self._listeners[event].append(callback)
        return self

    def off(self, event, callback):
        self._listeners[event] = [cb for cb in self._listeners[event] if cb != callback]
        return self

    # Test helper: simulate the SDK firing an event from its message loop.
    def emit(self, event, *args):
        for cb in list(self._listeners[event]):
            cb(*args)


class MockClient:
    """Mock AsyncPolymarketUS exposing only client.ws.markets()."""

    def __init__(self):
        self.created_websockets: list[MockMarketsWebSocket] = []
        self.ws = self  # so client.ws.markets() works

    def markets(self) -> MockMarketsWebSocket:
        ws = MockMarketsWebSocket()
        self.created_websockets.append(ws)
        return ws


class RecordingArchive:
    """Records calls instead of writing files."""

    def __init__(self):
        self.writes: list[dict] = []
        self.errors: list[tuple[BaseException, str, str]] = []

    def write(self, envelope: dict) -> None:
        self.writes.append(envelope)

    def write_error(self, exc, event_id, market_slug):
        self.errors.append((exc, event_id, market_slug))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_seq():
    _reset_sequence_counter_for_tests()
    yield


@pytest.fixture
def fast_lifecycle(monkeypatch):
    """Shrink lifecycle timers so tests don't sleep for minutes.
    Note: LIVENESS_TIMEOUT_SECONDS is set generous (1.0s) so delta-stream
    tests can verify subscription behavior without the liveness probe
    tearing down the just-subscribed connection. Liveness behavior
    itself is verified in dedicated tests with shorter timeouts."""
    monkeypatch.setattr(cp_module, "RECYCLE_INTERVAL_SECONDS", 1.0)
    monkeypatch.setattr(cp_module, "LIVENESS_CHECK_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(cp_module, "LIVENESS_TIMEOUT_SECONDS", 1.0)
    monkeypatch.setattr(cp_module, "DELTA_POLL_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(cp_module, "RECONNECT_BACKOFF_SECONDS", 0.001)


@pytest.fixture
def pool(tmp_path, fast_lifecycle):
    matches_root = tmp_path / "matches"
    delta_path = tmp_path / "events" / "discovery_delta.jsonl"
    matches_root.mkdir()
    delta_path.parent.mkdir()

    client = MockClient()
    archive = RecordingArchive()
    p = ClobPool(client, archive, matches_root=matches_root, delta_path=delta_path)
    yield p, client, archive, matches_root, delta_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_meta(matches_root: Path, event_id: str, *, market_slug="test-slug",
                doubles_flag=False, active=True, closed=False, no_active=False) -> None:
    d = matches_root / event_id
    d.mkdir(parents=True, exist_ok=True)
    if no_active:
        moneyline_markets = [{"market_slug": market_slug, "active": False, "closed": True}]
    else:
        moneyline_markets = [{"market_slug": market_slug, "active": active, "closed": closed}]
    meta = {
        "event_id": event_id,
        "doubles_flag": doubles_flag,
        "moneyline_markets": moneyline_markets,
    }
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


def _append_delta(delta_path: Path, *, added=None, removed=None) -> None:
    rec = {"poll_ts": "2026-04-23T12:00:00.000Z",
           "added": added or [], "removed": removed or []}
    with delta_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------------------
# subscribe_match tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe_match_creates_websocket_and_connects(pool):
    p, client, archive, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    assert len(client.created_websockets) == 1
    ws = client.created_websockets[0]
    assert ws.connect_calls == 1


@pytest.mark.asyncio
async def test_subscribe_match_subscribes_to_both_streams(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    types = {t for (_, t, _) in ws.subscribed}
    assert types == {"SUBSCRIPTION_TYPE_MARKET_DATA", "SUBSCRIPTION_TYPE_TRADE"}


@pytest.mark.asyncio
async def test_subscribe_match_uses_correct_request_ids(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    request_ids = {req for (req, _, _) in ws.subscribed}
    assert request_ids == {_md_request_id("slug-1"), _td_request_id("slug-1")}


@pytest.mark.asyncio
async def test_subscribe_match_subscribes_correct_slug(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-x")
    ws = client.created_websockets[0]
    for _, _, slugs in ws.subscribed:
        assert slugs == ["slug-x"]


@pytest.mark.asyncio
async def test_subscribe_match_registers_three_listeners(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    assert len(ws._listeners["message"]) == 1
    assert len(ws._listeners["error"]) == 1
    assert len(ws._listeners["close"]) == 1


@pytest.mark.asyncio
async def test_subscribe_match_idempotent(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    await p.subscribe_match("evt-1", "slug-1")
    # Second call should NOT create a second websocket
    assert len(client.created_websockets) == 1


@pytest.mark.asyncio
async def test_subscribe_match_registers_in_connections(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    assert "evt-1" in p._connections
    assert p._connections["evt-1"].market_slug == "slug-1"
    assert p._connections["evt-1"].event_id == "evt-1"


# ---------------------------------------------------------------------------
# on_message handler tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_message_updates_liveness_timestamp(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    conn = p._connections["evt-1"]
    initial_ts = conn.last_message_at
    await asyncio.sleep(0.01)
    msg = {"marketData": {"marketSlug": "slug-1", "bids": [], "offers": []}}
    ws.emit("message", msg)
    assert conn.last_message_at > initial_ts


@pytest.mark.asyncio
async def test_on_message_routes_to_archive(pool):
    p, client, archive, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    msg = {"marketData": {"marketSlug": "slug-1", "bids": [], "offers": []}}
    ws.emit("message", msg)
    assert len(archive.writes) == 1
    env = archive.writes[0]
    assert env["match_id"] == "evt-1"
    assert env["market_slug"] == "slug-1"
    assert env["stream_type"] == "market_data"
    assert env["raw"] is msg


@pytest.mark.asyncio
async def test_on_message_after_unsubscribe_is_safe(pool):
    p, client, archive, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    await p.unsubscribe_match("evt-1")
    # Late message arriving on a torn-down connection must not crash
    ws.emit("message", {"marketData": {"marketSlug": "slug-1"}})
    # And must not append to archive
    assert archive.writes == []


# ---------------------------------------------------------------------------
# on_error handler tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_error_with_websocketerror_invokes_write_error(pool):
    from polymarket_us.errors import WebSocketError
    p, client, archive, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    exc = WebSocketError("subscribe failed", _md_request_id("slug-1"))
    ws.emit("error", exc)
    assert len(archive.errors) == 1
    recorded_exc, recorded_event_id, recorded_slug = archive.errors[0]
    assert recorded_exc is exc
    assert recorded_event_id == "evt-1"
    assert recorded_slug == "slug-1"


@pytest.mark.asyncio
async def test_on_error_with_generic_exception_still_archives(pool):
    """on_error catches any exception type — request_id may be None."""
    p, client, archive, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    exc = RuntimeError("generic")
    ws.emit("error", exc)
    assert len(archive.errors) == 1
    assert archive.errors[0][0] is exc


# ---------------------------------------------------------------------------
# unsubscribe_match tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unsubscribe_match_unsubscribes_both_streams(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    await p.unsubscribe_match("evt-1")
    assert set(ws.unsubscribed) == {_md_request_id("slug-1"), _td_request_id("slug-1")}


@pytest.mark.asyncio
async def test_unsubscribe_match_closes_ws(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    ws = client.created_websockets[0]
    await p.unsubscribe_match("evt-1")
    assert ws.close_calls == 1


@pytest.mark.asyncio
async def test_unsubscribe_match_removes_from_connections(pool):
    p, _, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    await p.unsubscribe_match("evt-1")
    assert "evt-1" not in p._connections


@pytest.mark.asyncio
async def test_unsubscribe_match_idempotent(pool):
    p, _, _, _, _ = pool
    await p.unsubscribe_match("never-subscribed")  # should not raise
    await p.subscribe_match("evt-1", "slug-1")
    await p.unsubscribe_match("evt-1")
    await p.unsubscribe_match("evt-1")  # second call should be safe


# ---------------------------------------------------------------------------
# Delta stream tail tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tail_subscribes_on_added(pool):
    p, client, _, matches_root, delta_path = pool
    _write_meta(matches_root, "evt-A", market_slug="slug-A")
    # File needs to exist to start; touch with empty content to avoid the
    # "advance past pre-existing" path swallowing our test entries
    delta_path.touch()
    task = asyncio.create_task(p.run_forever())
    await asyncio.sleep(0.05)
    _append_delta(delta_path, added=["evt-A"])
    await asyncio.sleep(0.2)
    # Assert BEFORE shutdown, because close_all() clears _connections.
    assert "evt-A" in p._connections
    # Now shut down cleanly.
    p._closed = True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_tail_unsubscribes_on_removed(pool):
    p, client, _, matches_root, delta_path = pool
    _write_meta(matches_root, "evt-A", market_slug="slug-A")
    delta_path.touch()
    task = asyncio.create_task(p.run_forever())
    await asyncio.sleep(0.05)
    _append_delta(delta_path, added=["evt-A"])
    await asyncio.sleep(0.2)
    assert "evt-A" in p._connections
    _append_delta(delta_path, removed=["evt-A"])
    await asyncio.sleep(0.2)
    # Assert removal BEFORE shutdown.
    assert "evt-A" not in p._connections
    p._closed = True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_tail_advances_past_preexisting_entries(pool):
    """Pre-existing delta entries must NOT be replayed on pool start
    (we only react to deltas observed after the pool starts)."""
    p, client, _, matches_root, delta_path = pool
    _write_meta(matches_root, "evt-OLD", market_slug="slug-OLD")
    _append_delta(delta_path, added=["evt-OLD"])    # pre-existing
    task = asyncio.create_task(p.run_forever())
    await asyncio.sleep(0.1)
    # Assert BEFORE shutdown.
    assert "evt-OLD" not in p._connections
    p._closed = True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_tail_skips_malformed_lines(pool):
    p, client, _, matches_root, delta_path = pool
    _write_meta(matches_root, "evt-A", market_slug="slug-A")
    delta_path.touch()
    task = asyncio.create_task(p.run_forever())
    await asyncio.sleep(0.05)
    with delta_path.open("a", encoding="utf-8") as fh:
        fh.write("{not json\n")
        fh.write(json.dumps({"poll_ts": "x", "added": ["evt-A"], "removed": []}) + "\n")
    await asyncio.sleep(0.2)
    # Despite the malformed line, the second valid line is processed.
    # Assert BEFORE shutdown.
    assert "evt-A" in p._connections
    p._closed = True
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# _resolve_slug tests
# ---------------------------------------------------------------------------


def test_resolve_slug_picks_first_active_moneyline(pool):
    p, _, _, matches_root, _ = pool
    d = matches_root / "evt-1"
    d.mkdir()
    meta = {
        "event_id": "evt-1",
        "doubles_flag": False,
        "moneyline_markets": [
            {"market_slug": "first-slug", "active": True, "closed": False},
            {"market_slug": "second-slug", "active": True, "closed": False},
        ],
    }
    (d / "meta.json").write_text(json.dumps(meta))
    assert p._resolve_slug("evt-1") == "first-slug"


def test_resolve_slug_skips_closed_markets(pool):
    p, _, _, matches_root, _ = pool
    d = matches_root / "evt-1"
    d.mkdir()
    meta = {
        "event_id": "evt-1",
        "doubles_flag": False,
        "moneyline_markets": [
            {"market_slug": "closed-slug", "active": True, "closed": True},
            {"market_slug": "active-slug", "active": True, "closed": False},
        ],
    }
    (d / "meta.json").write_text(json.dumps(meta))
    assert p._resolve_slug("evt-1") == "active-slug"


def test_resolve_slug_rejects_doubles(pool):
    p, _, _, matches_root, _ = pool
    _write_meta(matches_root, "evt-1", doubles_flag=True)
    assert p._resolve_slug("evt-1") is None


def test_resolve_slug_returns_none_for_missing_meta(pool):
    p, _, _, _, _ = pool
    assert p._resolve_slug("nonexistent") is None


def test_resolve_slug_returns_none_when_no_active_markets(pool):
    p, _, _, matches_root, _ = pool
    _write_meta(matches_root, "evt-1", no_active=True)
    assert p._resolve_slug("evt-1") is None


# ---------------------------------------------------------------------------
# Reconnect test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reconnect_closes_old_and_creates_new_websocket(pool):
    p, client, _, _, _ = pool
    await p.subscribe_match("evt-1", "slug-1")
    old_ws = client.created_websockets[0]
    await p._reconnect("evt-1")
    # Old ws was closed during unsubscribe path
    assert old_ws.close_calls == 1
    # A new ws was created
    assert len(client.created_websockets) == 2
    new_ws = client.created_websockets[1]
    assert new_ws.connect_calls == 1
    # New ws is now what's in self._connections
    assert p._connections["evt-1"].ws is new_ws


# ---------------------------------------------------------------------------
# Liveness probe test (uses aggressive timeout — separate from fast_lifecycle)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_liveness_probe_recycles_silent_connection(tmp_path, monkeypatch):
    """Connection with no incoming messages for LIVENESS_TIMEOUT_SECONDS
    triggers a recycle. Verifies build plan §5.4 silent-stall backstop."""
    monkeypatch.setattr(cp_module, "RECYCLE_INTERVAL_SECONDS", 60.0)  # don't compete
    monkeypatch.setattr(cp_module, "LIVENESS_CHECK_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(cp_module, "LIVENESS_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(cp_module, "RECONNECT_BACKOFF_SECONDS", 0.001)
    matches_root = tmp_path / "matches"
    delta_path = tmp_path / "events" / "discovery_delta.jsonl"
    matches_root.mkdir()
    delta_path.parent.mkdir()
    client = MockClient()
    archive = RecordingArchive()
    p = ClobPool(client, archive, matches_root=matches_root, delta_path=delta_path)
    await p.subscribe_match("evt-1", "slug-1")
    assert len(client.created_websockets) == 1
    # Wait for liveness probe to fire (timeout=0.05s, check every 0.01s)
    await asyncio.sleep(0.15)
    # Reconnect should have created a second websocket
    assert len(client.created_websockets) >= 2
    await p.close_all()


@pytest.mark.asyncio
async def test_proactive_recycle_creates_new_websocket(tmp_path, monkeypatch):
    """15-min proactive recycle (build plan §5.4) replaces the connection
    even when messages are flowing."""
    monkeypatch.setattr(cp_module, "RECYCLE_INTERVAL_SECONDS", 0.05)
    monkeypatch.setattr(cp_module, "LIVENESS_CHECK_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(cp_module, "LIVENESS_TIMEOUT_SECONDS", 60.0)  # don't compete
    monkeypatch.setattr(cp_module, "RECONNECT_BACKOFF_SECONDS", 0.001)
    matches_root = tmp_path / "matches"
    delta_path = tmp_path / "events" / "discovery_delta.jsonl"
    matches_root.mkdir()
    delta_path.parent.mkdir()
    client = MockClient()
    archive = RecordingArchive()
    p = ClobPool(client, archive, matches_root=matches_root, delta_path=delta_path)
    await p.subscribe_match("evt-1", "slug-1")
    assert len(client.created_websockets) == 1
    # Wait for proactive recycle to fire (interval=0.05s)
    await asyncio.sleep(0.15)
    # Recycle should have created a second websocket
    assert len(client.created_websockets) >= 2
    await p.close_all()
