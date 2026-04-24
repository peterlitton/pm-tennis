"""
tests/test_archive_writer.py
Unit tests for src/capture/archive_writer.py — H-029 Phase 3.

Covers envelope construction (build plan §5.1), stream-type discrimination
(Finding B mapping), path routing (Finding C), file I/O behavior, and the
write_error() shortcut.

Test-discipline notes:
  - Uses pytest's tmp_path fixture for isolated archive roots.
  - Resets the global sequence counter between tests for determinism.
  - No mocks of the SDK here — archive writer has no SDK dependency
    beyond catching exceptions in write_error().
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

# Make src/capture importable from the bundle layout
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.capture.archive_writer import (
    ArchiveWriter,
    _reset_sequence_counter_for_tests,
    envelope_from,
    next_sequence_number,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_sequence():
    """Reset the global sequence counter before each test."""
    _reset_sequence_counter_for_tests()
    yield


@pytest.fixture
def writer(tmp_path: Path) -> ArchiveWriter:
    return ArchiveWriter(root=tmp_path)


# Sample SDK message payloads — shaped per phase1_sdk_surfaces.md §4.
SAMPLE_MARKET_DATA = {
    "requestId": "clob-test-slug-md",
    "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
    "marketData": {
        "marketSlug": "test-slug",
        "bids": [{"px": "0.42", "qty": "100"}],
        "offers": [{"px": "0.44", "qty": "100"}],
        "state": "OPEN",
        "stats": {"lastTradePx": "0.43", "sharesTraded": "1000"},
        "transactTime": "2026-04-23T12:00:00.000Z",
    },
}

SAMPLE_MARKET_DATA_LITE = {
    "requestId": "clob-test-slug-mdl",
    "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA_LITE",
    "marketDataLite": {
        "marketSlug": "test-slug",
        "bestBid": "0.42",
        "bestAsk": "0.44",
        "lastTradePx": "0.43",
    },
}

SAMPLE_TRADE = {
    "requestId": "clob-test-slug-td",
    "subscriptionType": "SUBSCRIPTION_TYPE_TRADE",
    "trade": {
        "marketSlug": "test-slug",
        "price": "0.43",
        "quantity": "100",
        "tradeTime": "2026-04-23T12:00:00.123Z",
        "maker": {"side": "BUY", "intent": "MAKER"},
        "taker": {"side": "SELL", "intent": "TAKER"},
    },
}

SAMPLE_HEARTBEAT = {"heartbeat": {"timestamp": "2026-04-23T12:00:00Z"}}

SAMPLE_ERROR = {"requestId": "clob-test-slug-md", "error": "subscription failed"}

SAMPLE_UNKNOWN = {"someUnrecognizedKey": "weirdShape"}


# ---------------------------------------------------------------------------
# Envelope construction tests
# ---------------------------------------------------------------------------


def test_envelope_has_required_fields():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-123", "test-slug")
    required = {
        "timestamp_utc",
        "sequence_number",
        "match_id",
        "asset_id",
        "market_slug",
        "sports_ws_game_id",
        "regime",
        "stream_type",
        "raw",
    }
    assert set(env.keys()) == required


def test_envelope_match_id_and_market_slug_populated():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-123", "test-slug")
    assert env["match_id"] == "evt-123"
    assert env["market_slug"] == "test-slug"


def test_envelope_raw_is_verbatim():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-123", "test-slug")
    assert env["raw"] is SAMPLE_MARKET_DATA


def test_envelope_sports_ws_game_id_empty_in_phase3():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-123", "test-slug")
    assert env["sports_ws_game_id"] == ""


def test_envelope_regime_unknown_in_phase3():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-123", "test-slug")
    assert env["regime"] == "unknown"


def test_asset_id_equals_market_slug_dual_naming():
    """Per H-029 Phase 2 ratification: dual-naming carry-forward until
    v4.1-candidate-7 lands. Test exists to document this and to fail
    loudly if a future change drops one without dropping the other."""
    env = envelope_from(SAMPLE_TRADE, "evt-789", "another-slug")
    assert env["asset_id"] == env["market_slug"] == "another-slug"


def test_sequence_number_monotonic_global():
    e1 = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "slug-1")
    e2 = envelope_from(SAMPLE_TRADE, "evt-2", "slug-2")
    e3 = envelope_from(SAMPLE_HEARTBEAT, "evt-3", "slug-3")
    assert e1["sequence_number"] == 1
    assert e2["sequence_number"] == 2
    assert e3["sequence_number"] == 3


def test_sequence_number_monotonic_across_matches():
    """Confirms global scope per operator ruling (not per-match)."""
    e1 = envelope_from(SAMPLE_MARKET_DATA, "evt-A", "slug-A")
    e2 = envelope_from(SAMPLE_MARKET_DATA, "evt-B", "slug-B")
    e3 = envelope_from(SAMPLE_MARKET_DATA, "evt-A", "slug-A")
    assert e2["sequence_number"] == e1["sequence_number"] + 1
    assert e3["sequence_number"] == e2["sequence_number"] + 1


def test_timestamp_utc_iso8601_ms_precision():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "slug-1")
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
    assert re.match(pattern, env["timestamp_utc"]), env["timestamp_utc"]


# ---------------------------------------------------------------------------
# Stream-type discrimination tests (Finding B mapping)
# ---------------------------------------------------------------------------


def test_stream_type_market_data():
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "slug-1")
    assert env["stream_type"] == "market_data"


def test_stream_type_market_data_lite():
    env = envelope_from(SAMPLE_MARKET_DATA_LITE, "evt-1", "slug-1")
    assert env["stream_type"] == "market_data_lite"


def test_stream_type_trade():
    """Per Finding B: SDK event name is 'trade' (not 'last_trade_price')
    and the discriminator key is 'trade' in the message."""
    env = envelope_from(SAMPLE_TRADE, "evt-1", "slug-1")
    assert env["stream_type"] == "trade"


def test_stream_type_heartbeat():
    env = envelope_from(SAMPLE_HEARTBEAT, "evt-1", "")
    assert env["stream_type"] == "heartbeat"


def test_stream_type_error():
    env = envelope_from(SAMPLE_ERROR, "evt-1", "")
    assert env["stream_type"] == "error"


def test_stream_type_unknown():
    env = envelope_from(SAMPLE_UNKNOWN, "evt-1", "")
    assert env["stream_type"] == "unknown"


# ---------------------------------------------------------------------------
# Path routing tests (Finding C)
# ---------------------------------------------------------------------------


def test_archive_path_routes_market_data_to_slug_dir(writer, tmp_path):
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "test-slug")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "test-slug" / f"{date_str}.jsonl"


def test_archive_path_routes_market_data_lite_to_slug_dir(writer, tmp_path):
    env = envelope_from(SAMPLE_MARKET_DATA_LITE, "evt-1", "test-slug")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "test-slug" / f"{date_str}.jsonl"


def test_archive_path_routes_trade_to_slug_dir(writer, tmp_path):
    env = envelope_from(SAMPLE_TRADE, "evt-1", "test-slug")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "test-slug" / f"{date_str}.jsonl"


def test_archive_path_routes_heartbeat_to_misc(writer, tmp_path):
    env = envelope_from(SAMPLE_HEARTBEAT, "evt-1", "")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "_misc" / f"heartbeats-{date_str}.jsonl"


def test_archive_path_routes_error_to_misc(writer, tmp_path):
    env = envelope_from(SAMPLE_ERROR, "evt-1", "")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "_misc" / f"errors-{date_str}.jsonl"


def test_archive_path_routes_unknown_to_misc(writer, tmp_path):
    env = envelope_from(SAMPLE_UNKNOWN, "evt-1", "")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "_misc" / f"unknown-{date_str}.jsonl"


def test_archive_path_slug_bearing_without_slug_routes_to_misc_unknown(writer, tmp_path):
    """Defensive: if a market_data/trade arrives with empty market_slug
    (shouldn't happen per SDK contract; defensive guard for malformed input),
    route to _misc/unknown rather than dropping silently."""
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "")
    path = writer._archive_path(env)
    date_str = env["timestamp_utc"][:10]
    assert path == tmp_path / "_misc" / f"unknown-{date_str}.jsonl"


# ---------------------------------------------------------------------------
# write() behavior tests
# ---------------------------------------------------------------------------


def test_write_creates_parent_directory(writer, tmp_path):
    env = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "fresh-slug")
    writer.write(env)
    assert (tmp_path / "fresh-slug").is_dir()


def test_write_appends_not_truncates(writer, tmp_path):
    e1 = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "slug-x")
    e2 = envelope_from(SAMPLE_TRADE, "evt-1", "slug-x")
    writer.write(e1)
    writer.write(e2)
    date_str = e1["timestamp_utc"][:10]
    path = tmp_path / "slug-x" / f"{date_str}.jsonl"
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2


def test_write_each_line_is_valid_jsonl(writer, tmp_path):
    e1 = envelope_from(SAMPLE_MARKET_DATA, "evt-1", "slug-x")
    e2 = envelope_from(SAMPLE_TRADE, "evt-1", "slug-x")
    writer.write(e1)
    writer.write(e2)
    date_str = e1["timestamp_utc"][:10]
    path = tmp_path / "slug-x" / f"{date_str}.jsonl"
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        parsed = json.loads(line)
        assert "stream_type" in parsed
        assert "raw" in parsed


def test_write_heartbeat_routes_to_misc(writer, tmp_path):
    env = envelope_from(SAMPLE_HEARTBEAT, "evt-1", "")
    writer.write(env)
    date_str = env["timestamp_utc"][:10]
    path = tmp_path / "_misc" / f"heartbeats-{date_str}.jsonl"
    assert path.exists()


# ---------------------------------------------------------------------------
# write_error() tests (caught Python-level exceptions)
# ---------------------------------------------------------------------------


def test_write_error_synthesizes_envelope_with_python_error_stream_type(writer, tmp_path):
    # WebSocketError construction matches phase1_sdk_surfaces.md §5 signature
    from polymarket_us.errors import WebSocketError
    exc = WebSocketError("subscription failed", "clob-slug-md")
    writer.write_error(exc, "evt-42", "slug-42")
    date_str_re = re.compile(r"^python_errors-\d{4}-\d{2}-\d{2}\.jsonl$")
    misc_dir = tmp_path / "_misc"
    files = [p.name for p in misc_dir.iterdir()]
    assert any(date_str_re.match(name) for name in files), files


def test_write_error_carries_request_id_attribution(writer, tmp_path):
    from polymarket_us.errors import WebSocketError
    exc = WebSocketError("subscription failed", "clob-slug-md")
    writer.write_error(exc, "evt-42", "slug-42")
    misc_dir = tmp_path / "_misc"
    [error_file] = list(misc_dir.glob("python_errors-*.jsonl"))
    parsed = json.loads(error_file.read_text(encoding="utf-8").strip())
    assert parsed["raw"]["exc_type"] == "WebSocketError"
    assert parsed["raw"]["exc_message"] == "subscription failed"
    assert parsed["raw"]["request_id"] == "clob-slug-md"
    assert parsed["match_id"] == "evt-42"
    assert parsed["market_slug"] == "slug-42"


def test_write_error_handles_non_websocket_exception(writer, tmp_path):
    """write_error accepts any BaseException, not just WebSocketError."""
    exc = RuntimeError("generic failure")
    writer.write_error(exc, "evt-99", "slug-99")
    misc_dir = tmp_path / "_misc"
    [error_file] = list(misc_dir.glob("python_errors-*.jsonl"))
    parsed = json.loads(error_file.read_text(encoding="utf-8").strip())
    assert parsed["raw"]["exc_type"] == "RuntimeError"
    assert parsed["raw"]["request_id"] is None  # no attribution on plain exception
