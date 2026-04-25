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


# ---------------------------------------------------------------------------
# H-033 file-handle cache tests
# ---------------------------------------------------------------------------


def _make_envelope(slug: str, stream_type: str = "market_data",
                   timestamp: str = "2026-04-25T12:00:00.000Z") -> dict:
    """Helper: minimal envelope shaped for path routing."""
    return {
        "timestamp_utc": timestamp,
        "sequence_number": next_sequence_number(),
        "match_id": "evt-x",
        "asset_id": slug,
        "market_slug": slug,
        "sports_ws_game_id": "",
        "regime": "unknown",
        "stream_type": stream_type,
        "raw": {"placeholder": True},
    }


def test_handle_cache_reuses_handle_across_writes(writer, tmp_path):
    """H-033: writing twice to the same path opens the file once and
    keeps the handle cached. Verified by inspecting writer._handles
    after writes."""
    env1 = _make_envelope("slug-cache")
    env2 = _make_envelope("slug-cache")
    writer.write(env1)
    writer.write(env2)

    expected_path = tmp_path / "slug-cache" / "2026-04-25.jsonl"
    assert expected_path.exists()
    # File must contain both envelopes (cached handle wrote both).
    lines = expected_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    # Cache must hold exactly one handle for this path.
    assert expected_path in writer._handles
    assert len(writer._handles) == 1


def test_handle_cache_distinct_paths_get_distinct_handles(writer, tmp_path):
    """Different slugs route to different paths and get distinct cache entries."""
    writer.write(_make_envelope("slug-a"))
    writer.write(_make_envelope("slug-b"))
    assert len(writer._handles) == 2


def test_release_slug_closes_and_evicts_handle(writer, tmp_path):
    """H-033 unsubscribe-cleanup discipline: release_slug evicts the
    cached handle and closes the file. Subsequent write reopens cleanly."""
    env = _make_envelope("slug-rel")
    writer.write(env)
    expected_path = tmp_path / "slug-rel" / "2026-04-25.jsonl"
    cached_fh = writer._handles[expected_path]
    assert not cached_fh.closed

    writer.release_slug("slug-rel")

    # Cache cleared.
    assert expected_path not in writer._handles
    # Underlying file handle closed.
    assert cached_fh.closed
    # Subsequent write to same slug must succeed (reopens).
    writer.write(_make_envelope("slug-rel"))
    lines = expected_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # one pre-release, one post-release


def test_release_slug_idempotent_on_unknown_slug(writer):
    """release_slug on a slug with no cached handles is a no-op, not an error.
    Required because subscribe_match may fail before any message arrives,
    yet unsubscribe_match still calls release_slug."""
    writer.release_slug("never-seen")
    writer.release_slug("")  # empty-slug guard
    assert writer._handles == {}


def test_release_slug_does_not_touch_misc_handles(writer, tmp_path):
    """Misc paths (_misc/heartbeats, _misc/errors, _misc/python_errors)
    are global and must persist across slug releases — only close_all
    drops them."""
    writer.write(_make_envelope("slug-x", stream_type="market_data"))
    writer.write(_make_envelope("slug-x", stream_type="heartbeat"))
    # Two handles cached: one slug-keyed, one misc.
    assert len(writer._handles) == 2

    writer.release_slug("slug-x")

    # Slug handle gone; misc handle remains.
    misc_paths = [p for p in writer._handles if "_misc" in p.parts]
    slug_paths = [p for p in writer._handles if "slug-x" in p.parts]
    assert len(misc_paths) == 1
    assert len(slug_paths) == 0


def test_release_slug_does_not_touch_other_slug_handles(writer, tmp_path):
    """release_slug('a') must not evict cached handles for slug 'b'."""
    writer.write(_make_envelope("slug-a"))
    writer.write(_make_envelope("slug-b"))
    assert len(writer._handles) == 2

    writer.release_slug("slug-a")

    remaining = list(writer._handles.keys())
    assert len(remaining) == 1
    assert "slug-b" in remaining[0].parts


def test_close_all_releases_every_handle(writer, tmp_path):
    """close_all evicts every handle (slug-keyed + misc) and closes them.
    Called at process shutdown."""
    writer.write(_make_envelope("slug-a"))
    writer.write(_make_envelope("slug-b"))
    writer.write(_make_envelope("slug-c", stream_type="heartbeat"))
    cached = list(writer._handles.values())
    assert len(cached) == 3

    writer.close_all()

    assert writer._handles == {}
    for fh in cached:
        assert fh.closed


def test_close_all_idempotent(writer):
    """close_all on an empty cache is a no-op."""
    writer.close_all()
    writer.close_all()
    assert writer._handles == {}


def test_write_error_evicts_stale_handle(writer, tmp_path):
    """If a cached handle fails to write (simulated by closing the
    handle out-of-band), the writer evicts it and re-raises. Next
    write reopens cleanly."""
    env = _make_envelope("slug-evict")
    writer.write(env)
    expected_path = tmp_path / "slug-evict" / "2026-04-25.jsonl"
    stale_fh = writer._handles[expected_path]

    # Simulate a wedged handle by closing it out-of-band.
    stale_fh.close()

    # Next write should raise (write to closed file), evict the stale
    # handle, and leave the cache clean for retry.
    with pytest.raises(ValueError):  # CPython: write to closed file → ValueError
        writer.write(_make_envelope("slug-evict"))
    assert expected_path not in writer._handles

    # Retry must succeed by reopening.
    writer.write(_make_envelope("slug-evict"))
    assert expected_path in writer._handles


def test_date_rollover_opens_new_handle(writer, tmp_path):
    """At UTC date rollover, an envelope's timestamp_utc routes to a new
    path. The new path opens a fresh handle; the old handle remains
    cached until release_slug or close_all (acceptable per H-033 design
    note — typical matches span <24h)."""
    writer.write(_make_envelope("slug-roll",
                                timestamp="2026-04-25T23:59:59.000Z"))
    writer.write(_make_envelope("slug-roll",
                                timestamp="2026-04-26T00:00:01.000Z"))
    day1 = tmp_path / "slug-roll" / "2026-04-25.jsonl"
    day2 = tmp_path / "slug-roll" / "2026-04-26.jsonl"
    assert day1 in writer._handles
    assert day2 in writer._handles
    # Both files contain one line each.
    assert len(day1.read_text(encoding="utf-8").splitlines()) == 1
    assert len(day2.read_text(encoding="utf-8").splitlines()) == 1


def test_release_slug_closes_both_rollover_handles(writer, tmp_path):
    """release_slug must close every handle whose path is under the
    slug-keyed directory, including post-rollover handles for the
    same slug."""
    writer.write(_make_envelope("slug-roll",
                                timestamp="2026-04-25T23:59:59.000Z"))
    writer.write(_make_envelope("slug-roll",
                                timestamp="2026-04-26T00:00:01.000Z"))
    assert len(writer._handles) == 2
    cached_handles = list(writer._handles.values())

    writer.release_slug("slug-roll")

    assert writer._handles == {}
    for fh in cached_handles:
        assert fh.closed
