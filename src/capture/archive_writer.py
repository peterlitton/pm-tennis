"""
src/capture/archive_writer.py
PM-Tennis Phase 3 — CLOB archive writer (H-029 deliverable).

Constructs build-plan-§5.1-shaped envelopes around incoming CLOB WebSocket
messages and appends them as JSONL to slug-keyed paths under /data/clob/.

SDK surface dependencies (per H-029 phase1_sdk_surfaces.md):
  - polymarket_us.errors.WebSocketError — caught from on('error') for
    write_error() shortcut. Field: exc.request_id (Phase 1 §5).

Envelope shape per build plan §5.1 (with H-029 additions per Phase 2 §4.2):
  {
    "timestamp_utc":      str — ISO-8601 with millisecond precision + 'Z'
    "sequence_number":    int — global monotonic per process (operator ruling H-029)
    "match_id":           str — Polymarket event_id from meta.json
    "asset_id":           str — alias of market_slug for §5.1 conformance (drops at v4.1-candidate-7)
    "market_slug":        str — operational identifier carried by every SDK payload
    "sports_ws_game_id":  str — empty in Phase 3; populated in Phase 4
    "regime":             str — best-effort: "pre-match" | "in-play" | "unknown"
    "stream_type":        str — discriminator: "market_data" | "market_data_lite"
                                | "trade" | "heartbeat" | "error" | "python_error" | "unknown"
    "raw":                dict — verbatim parsed SDK message
  }

Path routing (Finding C, ratified at H-029):
  - market_data / market_data_lite / trade  → /data/clob/{market_slug}/{date}.jsonl
  - heartbeat                                → /data/clob/_misc/heartbeats-{date}.jsonl
  - error (server-emitted)                   → /data/clob/_misc/errors-{date}.jsonl
  - python_error (synthesized in write_error)→ /data/clob/_misc/python_errors-{date}.jsonl
  - unknown                                  → /data/clob/_misc/unknown-{date}.jsonl

Watch-items flagged in H-029 §9:
  - §4.6 synchronous file I/O may produce visible lag at high-tick bursts.
  - §4.7 per-message open-append-close is ~200+ syscalls/sec at peak; not
    catastrophic but profileable. Async-queue and file-handle caching are
    post-H-029 follow-ups, not in scope here.
"""

from __future__ import annotations

import itertools
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLOB_ARCHIVE_ROOT = Path("/data/clob")
MISC_DIR_NAME = "_misc"
HEARTBEATS_FILE_PREFIX = "heartbeats"
ERRORS_FILE_PREFIX = "errors"
PYTHON_ERRORS_FILE_PREFIX = "python_errors"
UNKNOWN_FILE_PREFIX = "unknown"


# ---------------------------------------------------------------------------
# Sequence number — global monotonic per process (operator ruling, H-029 Phase 2)
# ---------------------------------------------------------------------------

_seq_counter = itertools.count(start=1)


def next_sequence_number() -> int:
    """Return the next monotonic sequence number for this process.

    Global scope per operator ruling at H-029 Phase 2 ratification:
    Phase 6 replay simulator gets a single total ordering across the
    entire archive; per-match ordering derives from match_id filter.
    """
    return next(_seq_counter)


def _reset_sequence_counter_for_tests() -> None:
    """Reset the global sequence counter — TEST USE ONLY."""
    global _seq_counter
    _seq_counter = itertools.count(start=1)


# ---------------------------------------------------------------------------
# Envelope construction (build plan §5.1)
# ---------------------------------------------------------------------------


def _utc_iso_ms() -> str:
    """UTC ISO-8601 wall-clock with millisecond precision and trailing 'Z'."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _infer_stream_type(msg: dict[str, Any]) -> str:
    """Discriminate SDK message type by top-level key membership.

    Mirrors MarketsWebSocket._handle_message dispatch ordering exactly
    (phase1_sdk_surfaces.md §3.3). Order matters because some messages
    might in principle carry multiple keys; we follow SDK ordering.
    """
    if "marketData" in msg:
        return "market_data"
    if "marketDataLite" in msg:
        return "market_data_lite"
    if "trade" in msg:
        return "trade"
    if "heartbeat" in msg:
        return "heartbeat"
    if "error" in msg:
        return "error"
    return "unknown"


def _infer_regime(msg: dict[str, Any]) -> str:
    """Best-effort regime inference from the message payload.

    Phase 3 conservative posture: 'unknown' unless explicit signal.
    Authoritative regime is computed elsewhere (signal qualification,
    Phase 5+); this field exists for build plan §5.1 conformance.
    """
    # MarketData payload may carry a 'state' field that hints at regime,
    # but the mapping is not pinned in Phase 1 introspection. Return
    # 'unknown' rather than fabricate a mapping (R-010).
    return "unknown"


def envelope_from(
    msg: dict[str, Any],
    event_id: str,
    market_slug: str,
) -> dict[str, Any]:
    """Build a build-plan-§5.1-compliant envelope around a parsed SDK message.

    Args:
        msg: The dict the SDK delivered to on('message', ...) — verbatim
             parsed payload, no transformation.
        event_id: Polymarket event_id from meta.json (the discovery key).
        market_slug: The slug the SDK subscription is keyed on; equals
            msg['marketData']['marketSlug'] etc. for slug-bearing messages,
            or the pool's stored slug for heartbeat/error messages that
            carry no slug themselves.

    Returns: envelope dict per module docstring.
    """
    return {
        "timestamp_utc": _utc_iso_ms(),
        "sequence_number": next_sequence_number(),
        "match_id": event_id,
        "asset_id": market_slug,        # §5.1 conformance; drops at v4.1-candidate-7
        "market_slug": market_slug,     # operational term per Finding D
        "sports_ws_game_id": "",        # Phase 4 populates
        "regime": _infer_regime(msg),
        "stream_type": _infer_stream_type(msg),
        "raw": msg,
    }


# ---------------------------------------------------------------------------
# ArchiveWriter
# ---------------------------------------------------------------------------


class ArchiveWriter:
    """JSONL archive writer for CLOB capture envelopes.

    write() routes envelopes to slug-keyed or _misc/ paths per Finding C
    and appends a single JSONL line. Synchronous file I/O — see watch-items
    flagged in H-029 §9.
    """

    def __init__(self, root: Path = CLOB_ARCHIVE_ROOT) -> None:
        self._root = Path(root)

    # ----- path routing (§4.4) -----

    def _archive_path(self, envelope: dict[str, Any]) -> Path:
        date_str = envelope["timestamp_utc"][:10]  # YYYY-MM-DD
        stream_type = envelope["stream_type"]
        if stream_type in ("market_data", "market_data_lite", "trade"):
            slug = envelope["market_slug"]
            if not slug:
                # Defensive: a slug-bearing stream without a slug is malformed;
                # route to _misc/unknown so we don't drop the message silently.
                return self._root / MISC_DIR_NAME / f"{UNKNOWN_FILE_PREFIX}-{date_str}.jsonl"
            return self._root / slug / f"{date_str}.jsonl"
        if stream_type == "heartbeat":
            return self._root / MISC_DIR_NAME / f"{HEARTBEATS_FILE_PREFIX}-{date_str}.jsonl"
        if stream_type == "error":
            return self._root / MISC_DIR_NAME / f"{ERRORS_FILE_PREFIX}-{date_str}.jsonl"
        if stream_type == "python_error":
            return self._root / MISC_DIR_NAME / f"{PYTHON_ERRORS_FILE_PREFIX}-{date_str}.jsonl"
        return self._root / MISC_DIR_NAME / f"{UNKNOWN_FILE_PREFIX}-{date_str}.jsonl"

    # ----- public surface (§4.5) -----

    def write(self, envelope: dict[str, Any]) -> None:
        """Append an envelope as a single JSONL line.

        Creates parent directory if missing. Opens in append mode and
        flushes after write to survive process restart mid-line.
        """
        path = self._archive_path(envelope)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(envelope, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()

    def write_error(
        self,
        exc: BaseException,
        event_id: str,
        market_slug: str,
    ) -> None:
        """Synthesize an envelope around a Python-level exception (caught
        in on('error', ...)) and route to _misc/python_errors-{date}.jsonl.

        Args:
            exc: The exception caught from MarketsWebSocket on('error', ...).
                For WebSocketError, exc.request_id carries per-subscribe
                attribution (phase1_sdk_surfaces.md §5).
            event_id: Match identity for the connection that raised.
            market_slug: Market slug for the connection that raised.
        """
        request_id = getattr(exc, "request_id", None)
        envelope = {
            "timestamp_utc": _utc_iso_ms(),
            "sequence_number": next_sequence_number(),
            "match_id": event_id,
            "asset_id": market_slug,
            "market_slug": market_slug,
            "sports_ws_game_id": "",
            "regime": "unknown",
            "stream_type": "python_error",
            "raw": {
                "exc_type": type(exc).__name__,
                "exc_message": str(exc),
                "request_id": request_id,
            },
        }
        path = self._archive_path(envelope)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(envelope, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
