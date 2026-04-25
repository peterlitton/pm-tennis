"""
src/capture/clob_pool.py
PM-Tennis Phase 3 — CLOB WebSocket pool (H-029 deliverable).

Maintains one MarketsWebSocket connection per actively-tracked tennis match.
Discovers matches by tailing /data/events/discovery_delta.jsonl (which the
discovery loop writes); subscribes to both market_data and trades on each
fresh connection per H-029 phase1_sdk_surfaces.md §3.2 (addendum-driven);
archives every incoming message via ArchiveWriter; recycles connections
proactively every 15 minutes (build plan §5.4) and reconnects on silent
stalls (90-second liveness backstop, §5.4).

SDK surface dependencies (per H-029 phase1_sdk_surfaces.md):
  §1   AsyncPolymarketUS(key_id=..., secret_key=...)
  §2   client.ws.markets() returns a fresh MarketsWebSocket per call
  §3.1 MarketsWebSocket(**kwargs) — invoked transparently via factory
  §3.2 subscribe_market_data(request_id, market_slugs)
       subscribe_trades(request_id, market_slugs)
  §3.3 on('message', cb), on('error', cb), on('close', cb) — sync callbacks
  §3.4 connect(), close(), unsubscribe(request_id), is_connected
  §5   WebSocketError(message, request_id) — caught from on('error')

Design choices grounded in operator rulings (H-029 Phase 2):
  - Per-match connection model (Pull 2 simplest-workable; D-036 ~20-match
    operational peak; SDK structurally supports shared connections but the
    optimization is worth zero at our scale and per-match gives cleaner
    failure isolation, lifecycle, and request_id attribution).
  - Discovery wiring via discovery_delta.jsonl tail (NOT meta.json scan):
    discovery.py line 47 documents that meta.json is immutable once
    written, so its live/active/ended flags freeze at discovery time.
    Match-end detection therefore comes from the delta stream's 'removed'
    event-id list, which the discovery loop writes when an event drops
    out of the active list. See Phase 2 §3.9 → §3.12 transition.

Watch-items flagged in H-029 §9 for Phase 5 smoke review:
  - Synchronous archive writes from on('message'); see archive_writer.py
    docstring.

Out of scope per Pull 4 (rebound to Phase 4 per D-036):
  - First-server identification, tiebreak/retirement handlers, handicap
    median updater, Sports WS client, correlation layer, signal evaluation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from polymarket_us import AsyncPolymarketUS
from polymarket_us.errors import WebSocketError

from src.capture.archive_writer import (
    ArchiveWriter,
    envelope_from,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants (build plan §5.4 + Phase 2 §3.3)
# ---------------------------------------------------------------------------

RECYCLE_INTERVAL_SECONDS = 15 * 60        # build plan §5.4 proactive recycle
LIVENESS_TIMEOUT_SECONDS = 90              # build plan §5.4 silent-stall backstop
LIVENESS_CHECK_INTERVAL_SECONDS = 30       # check 3x per timeout window
DELTA_POLL_INTERVAL_SECONDS = 30           # tail interval for discovery_delta.jsonl
RECONNECT_BACKOFF_SECONDS = 2              # short fixed backoff after close

MATCHES_ROOT = Path("/data/matches")
DELTA_PATH = Path("/data/events/discovery_delta.jsonl")


# ---------------------------------------------------------------------------
# MatchConnection — one per subscribed match (Phase 2 §3.4)
# ---------------------------------------------------------------------------


@dataclass
class MatchConnection:
    """State for one active per-match CLOB connection.

    Field meanings:
      market_slug: the slug the SDK keys subscriptions on; equals the value
                   carried inside every message payload (marketData.marketSlug
                   etc., per phase1_sdk_surfaces.md §4).
      event_id:    Polymarket event_id from meta.json — discovery key.
      ws:          the live MarketsWebSocket instance for this match.
      connected_at: monotonic time at last connect; recycle scheduling key.
      last_message_at: monotonic time of last incoming message (any kind,
                       including heartbeats); liveness probe key.
      recycle_task: 15-min proactive recycle timer task.
      liveness_task: silent-stall probe task.
      subscribe_request_ids: (md_request_id, td_request_id) pair, kept for
                             unsubscribe calls and for per-subscribe error
                             attribution via WebSocketError.request_id.
    """
    market_slug: str
    event_id: str
    ws: Any                       # MarketsWebSocket; Any to avoid SDK import here
    connected_at: float
    last_message_at: float
    subscribe_request_ids: tuple[str, str]
    recycle_task: Optional[asyncio.Task] = None
    liveness_task: Optional[asyncio.Task] = None


# ---------------------------------------------------------------------------
# ClobPool
# ---------------------------------------------------------------------------


def _md_request_id(market_slug: str) -> str:
    return f"clob-{market_slug}-md"


def _td_request_id(market_slug: str) -> str:
    return f"clob-{market_slug}-td"


class ClobPool:
    """Per-match CLOB WebSocket pool.

    Lifecycle:
      run_forever()  — main loop: tail discovery_delta.jsonl, dispatch
                       subscribe/unsubscribe per added/removed event ids.
      subscribe_match(event_id, market_slug)
                     — create fresh MarketsWebSocket via client.ws.markets(),
                       wire on(message/error/close), connect(), subscribe
                       both market_data + trades, start recycle + liveness
                       tasks, register in self._connections.
      unsubscribe_match(event_id)
                     — cancel tasks, unsubscribe both streams, close ws,
                       remove from registry. Idempotent.
      close_all()    — shutdown; unsubscribe every match.

    Internal:
      _make_message_handler / _make_error_handler / _make_close_handler:
        callback factories that close over (event_id, market_slug) so the
        on() listener has the routing context.
      _recycle_task: per-connection 15-min proactive recycle.
      _liveness_task: per-connection silent-stall reconnect.
      _reconnect: orchestrates close + re-subscribe.
      _tail_delta_stream: tails discovery_delta.jsonl for event additions
                          and removals.
      _resolve_slug: reads meta.json once per event_id at subscribe time
                     to extract the first active moneyline market_slug.
    """

    def __init__(
        self,
        client: AsyncPolymarketUS,
        archive: ArchiveWriter,
        matches_root: Path = MATCHES_ROOT,
        delta_path: Path = DELTA_PATH,
    ) -> None:
        self._client = client
        self._archive = archive
        self._matches_root = Path(matches_root)
        self._delta_path = Path(delta_path)
        self._connections: dict[str, MatchConnection] = {}
        self._closed = False

    # ----- main loop -----

    async def run_forever(self) -> None:
        """Main loop: tail discovery delta stream forever."""
        log.info(
            "ClobPool starting; matches_root=%s delta_path=%s",
            self._matches_root, self._delta_path,
        )
        try:
            await self._tail_delta_stream()
        finally:
            await self.close_all()

    # ----- subscription lifecycle -----

    async def subscribe_match(self, event_id: str, market_slug: str) -> None:
        """Create connection for event_id+market_slug; subscribe to both
        market_data and trades; wire listeners and lifecycle tasks.

        Idempotent: if event_id is already connected, logs and returns.
        """
        if event_id in self._connections:
            log.info(
                "subscribe_match: event_id=%s already connected; skipping",
                event_id,
            )
            return

        log.info(
            "subscribe_match: event_id=%s market_slug=%s",
            event_id, market_slug,
        )

        ws = self._client.ws.markets()    # phase1_sdk_surfaces.md §2

        md_req = _md_request_id(market_slug)
        td_req = _td_request_id(market_slug)
        now_mono = time.monotonic()

        conn = MatchConnection(
            market_slug=market_slug,
            event_id=event_id,
            ws=ws,
            connected_at=now_mono,
            last_message_at=now_mono,
            subscribe_request_ids=(md_req, td_req),
        )

        # Wire listeners BEFORE connect/subscribe so we don't miss the
        # 'open' / first 'message' arriving on a fast connection.
        ws.on("message", self._make_message_handler(event_id))
        ws.on("error", self._make_error_handler(event_id))
        ws.on("close", self._make_close_handler(event_id))

        # H-032 Issue A fix: if connect or either subscribe raises, the ws
        # has been created and (after connect) has a running _message_task
        # plus an open underlying socket. Without this guard the ws is
        # orphaned — never registered, never closed, never GC'able — which
        # is a permanent leak path that fires more often under memory
        # pressure (when subscribe calls are likelier to fail).
        try:
            await ws.connect()                                     # §3.4
            await ws.subscribe_market_data(md_req, [market_slug])  # §3.2
            await ws.subscribe_trades(td_req, [market_slug])       # §3.2
        except BaseException:
            # Best-effort cleanup; ws.close() cancels _message_task and
            # closes the underlying socket. Swallow cleanup errors so the
            # original exception (which carries the diagnostic) propagates.
            try:
                await ws.close()
            except Exception:
                log.exception(
                    "subscribe_match: cleanup ws.close() failed event_id=%s",
                    event_id,
                )
            raise

        # Register before starting tasks so handlers can find the conn.
        self._connections[event_id] = conn

        conn.recycle_task = asyncio.create_task(self._recycle_task(event_id))
        conn.liveness_task = asyncio.create_task(self._liveness_task(event_id))

    async def unsubscribe_match(self, event_id: str) -> None:
        """Tear down connection for event_id. Idempotent."""
        conn = self._connections.pop(event_id, None)
        if conn is None:
            return

        log.info(
            "unsubscribe_match: event_id=%s market_slug=%s",
            event_id, conn.market_slug,
        )

        # Cancel lifecycle tasks first so they don't try to reconnect mid-tear-down.
        for task in (conn.recycle_task, conn.liveness_task):
            if task is not None and not task.done():
                task.cancel()
        # Await task cleanup, but skip the current task — a lifecycle task
        # calling unsubscribe via _reconnect cannot await itself (would
        # raise "Task cannot await on itself"). The current task is
        # cancelled and will exit on its own when the awaiter returns.
        current = asyncio.current_task()
        for task in (conn.recycle_task, conn.liveness_task):
            if task is None or task is current:
                continue
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                log.exception(
                    "unsubscribe_match: task cleanup raised event_id=%s",
                    event_id,
                )

        # Unsubscribe both streams, then close ws.
        md_req, td_req = conn.subscribe_request_ids
        try:
            await conn.ws.unsubscribe(md_req)
        except Exception:
            log.exception(
                "unsubscribe_match: market_data unsubscribe failed event_id=%s",
                event_id,
            )
        try:
            await conn.ws.unsubscribe(td_req)
        except Exception:
            log.exception(
                "unsubscribe_match: trades unsubscribe failed event_id=%s",
                event_id,
            )
        try:
            await conn.ws.close()                          # §3.4
        except Exception:
            log.exception(
                "unsubscribe_match: ws.close failed event_id=%s",
                event_id,
            )

        # H-032 Issue B fix: explicit reference release. Defense-in-depth.
        # The conn dataclass has already been popped from self._connections
        # (line ~235), but lifecycle-task cancellation tracebacks and any
        # in-flight callback frames may briefly retain references to conn.
        # Nulling conn.ws breaks one chain (conn -> ws) so the ws is
        # GC-eligible the moment its other references drop.
        conn.ws = None

        # H-033 file-handle cache teardown. Same unsubscribe-cleanup
        # discipline as Issue A: per-match resources released on
        # unsubscribe, not deferred to process shutdown. release_slug
        # is idempotent and safe even if no handles were ever opened
        # for this slug (e.g., subscribe succeeded but no messages
        # arrived before recycle).
        try:
            self._archive.release_slug(conn.market_slug)
        except Exception:
            log.exception(
                "unsubscribe_match: archive.release_slug failed event_id=%s slug=%s",
                event_id, conn.market_slug,
            )

    async def close_all(self) -> None:
        """Shutdown path: unsubscribe every match."""
        self._closed = True
        event_ids = list(self._connections.keys())
        log.info("close_all: tearing down %d connections", len(event_ids))
        for eid in event_ids:
            try:
                await self.unsubscribe_match(eid)
            except Exception:
                log.exception("close_all: unsubscribe_match raised event_id=%s", eid)

        # H-033 file-handle cache teardown. After every connection is
        # unsubscribed, release_slug has handled all slug-keyed handles.
        # Misc handles (_misc/heartbeats, _misc/errors, etc.) are global
        # and persist across connection lifecycles; close_all on the
        # writer flushes those at process shutdown.
        try:
            self._archive.close_all()
        except Exception:
            log.exception("close_all: archive.close_all raised")

    # ----- callback factories (Phase 2 §3.6) -----

    def _make_message_handler(self, event_id: str):
        def on_message(msg: dict) -> None:
            conn = self._connections.get(event_id)
            if conn is None:
                # Message arriving for a connection already torn down;
                # archive defensively under the slug we know if we can.
                return
            conn.last_message_at = time.monotonic()
            try:
                env = envelope_from(msg, event_id, conn.market_slug)
                self._archive.write(env)
            except Exception:
                log.exception(
                    "on_message: archive write raised event_id=%s", event_id,
                )
        return on_message

    def _make_error_handler(self, event_id: str):
        def on_error(exc) -> None:
            req_id = getattr(exc, "request_id", None)
            log.warning(
                "CLOB error event_id=%s exc_type=%s request_id=%s msg=%r",
                event_id, type(exc).__name__, req_id, str(exc),
            )
            conn = self._connections.get(event_id)
            slug = conn.market_slug if conn else ""
            try:
                self._archive.write_error(exc, event_id, slug)
            except Exception:
                log.exception(
                    "on_error: archive write_error raised event_id=%s",
                    event_id,
                )
        return on_error

    def _make_close_handler(self, event_id: str):
        def on_close(*args) -> None:
            log.info("CLOB connection closed event_id=%s", event_id)
            if self._closed:
                return  # shutdown in progress; don't spawn reconnect
            asyncio.create_task(self._reconnect(event_id))
        return on_close

    # ----- lifecycle tasks (Phase 2 §3.7) -----

    async def _recycle_task(self, event_id: str) -> None:
        """Sleep RECYCLE_INTERVAL_SECONDS then trigger a recycle.
        Build plan §5.4 proactive 15-minute recycle."""
        try:
            await asyncio.sleep(RECYCLE_INTERVAL_SECONDS)
            log.info("Proactive recycle event_id=%s", event_id)
            await self._reconnect(event_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("recycle_task crashed event_id=%s", event_id)

    async def _liveness_task(self, event_id: str) -> None:
        """Silent-stall backstop: if no message for LIVENESS_TIMEOUT_SECONDS,
        force reconnect. Build plan §5.4 90-second probe."""
        try:
            while True:
                await asyncio.sleep(LIVENESS_CHECK_INTERVAL_SECONDS)
                conn = self._connections.get(event_id)
                if conn is None:
                    return
                elapsed = time.monotonic() - conn.last_message_at
                if elapsed > LIVENESS_TIMEOUT_SECONDS:
                    log.warning(
                        "Liveness probe: no messages for %.0fs; recycling event_id=%s",
                        elapsed, event_id,
                    )
                    await self._reconnect(event_id)
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("liveness_task crashed event_id=%s", event_id)

    # ----- reconnect (Phase 2 §3.8) -----

    async def _reconnect(self, event_id: str) -> None:
        """Close and re-subscribe a single match. Triggered by:
        - on_close callback
        - 15-min proactive recycle
        - liveness probe stall."""
        conn = self._connections.get(event_id)
        if conn is None:
            return
        market_slug = conn.market_slug
        await self.unsubscribe_match(event_id)
        if self._closed:
            return
        await asyncio.sleep(RECONNECT_BACKOFF_SECONDS)
        try:
            await self.subscribe_match(event_id, market_slug)
        except Exception:
            log.exception(
                "_reconnect failed event_id=%s; will be retried by next delta event",
                event_id,
            )

    # ----- discovery wiring (Phase 2 §3.12) -----

    async def _tail_delta_stream(self) -> None:
        """Tail /data/events/discovery_delta.jsonl for added/removed event IDs.

        Reads from a remembered byte offset across iterations; if file is
        absent or empty at startup, waits politely. New 'added' ids resolve
        their market_slug via meta.json and call subscribe_match.
        Removed ids call unsubscribe_match.
        """
        last_offset = 0
        # If the delta file exists at startup, advance past historical entries —
        # we only react to deltas observed after the pool starts.
        if self._delta_path.exists():
            last_offset = self._delta_path.stat().st_size
            log.info(
                "Delta tail: advancing past %d bytes of pre-existing entries",
                last_offset,
            )

        while not self._closed:
            try:
                if self._delta_path.exists():
                    size = self._delta_path.stat().st_size
                    if size > last_offset:
                        await self._consume_delta_chunk(last_offset, size)
                        last_offset = size
                    elif size < last_offset:
                        # File shrank — likely log rotation or fresh recreate.
                        # Reset to start so we don't miss events.
                        log.warning(
                            "Delta tail: file shrank from %d to %d; resetting offset",
                            last_offset, size,
                        )
                        last_offset = 0
                await asyncio.sleep(DELTA_POLL_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Delta tail iteration raised; continuing")
                await asyncio.sleep(DELTA_POLL_INTERVAL_SECONDS)

    async def _consume_delta_chunk(self, start: int, end: int) -> None:
        """Read delta lines in [start, end) and dispatch added/removed."""
        with self._delta_path.open("r", encoding="utf-8") as fh:
            fh.seek(start)
            chunk = fh.read(end - start)
        for line in chunk.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                log.warning("Delta tail: skipping malformed line: %r", line[:120])
                continue
            for event_id in record.get("added", []):
                slug = self._resolve_slug(event_id)
                if slug is None:
                    log.info(
                        "Delta tail: added event_id=%s — no eligible moneyline market; skipping",
                        event_id,
                    )
                    continue
                try:
                    await self.subscribe_match(event_id, slug)
                except Exception:
                    log.exception(
                        "Delta tail: subscribe_match raised event_id=%s slug=%s",
                        event_id, slug,
                    )
            for event_id in record.get("removed", []):
                try:
                    await self.unsubscribe_match(event_id)
                except Exception:
                    log.exception(
                        "Delta tail: unsubscribe_match raised event_id=%s",
                        event_id,
                    )

    def _resolve_slug(self, event_id: str) -> Optional[str]:
        """Read meta.json once and return the first active moneyline market_slug.
        Returns None if meta is missing, malformed, doubles-flagged, or has
        no active moneyline market."""
        meta_path = self._matches_root / event_id / "meta.json"
        if not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            log.warning("_resolve_slug: meta.json unreadable event_id=%s", event_id)
            return None
        if meta.get("doubles_flag"):
            log.info("_resolve_slug: doubles_flag set; skipping event_id=%s", event_id)
            return None
        ml_markets = meta.get("moneyline_markets") or []
        active = [m for m in ml_markets if m.get("active") and not m.get("closed")]
        if not active:
            return None
        return active[0].get("market_slug") or None
