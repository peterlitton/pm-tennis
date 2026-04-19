"""
CLOB WebSocket pool — Phase 3.

Maintains one WebSocket connection per active Polymarket US asset ID.
Writes every tick to data/clob/{asset_id}/{date}.jsonl as a timestamped envelope.

Design constraints from the build plan (§5.4, §12.2):
  - Proactive 15-minute recycle per connection regardless of health.
  - 90-second liveness probe: if no message received in 90 s, reconnect.
  - Soft 150-asset cap: warn above this, do not refuse connections.
  - Pool is managed by asyncio tasks; safe for use inside the FastAPI process.

CLOB WebSocket endpoint (Polymarket US):
  wss://clob.polymarket.us/ws/{asset_id}

Each envelope written to JSONL:
  {
    "ts":         "<UTC ISO-8601 ms>",
    "seq":        <int>,                  # monotonic within session
    "asset_id":   "<str>",
    "game_id":    "<str | null>",         # from correlation layer
    "regime":     "pre-match | in-play",  # from meta.json
    "payload":    { ...raw WS message... }
  }
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLOB_WS_BASE = "wss://clob.polymarket.us/ws"
RECYCLE_INTERVAL_SECONDS = 15 * 60        # 15 minutes
LIVENESS_TIMEOUT_SECONDS = 90             # 90-second liveness probe
SOFT_ASSET_CAP = 150                       # warn above this
RECONNECT_BACKOFF_SECONDS = 5             # base back-off on reconnect


# ---------------------------------------------------------------------------
# Envelope writer
# ---------------------------------------------------------------------------

class EnvelopeWriter:
    """Writes timestamped JSONL envelopes for one asset ID.

    Thread-safe for single-asyncio-task use (one writer per asset, one task
    per writer). File is rotated at UTC midnight.
    """

    def __init__(self, data_dir: Path, asset_id: str) -> None:
        self._data_dir = data_dir
        self._asset_id = asset_id
        self._seq = 0
        self._current_date: Optional[str] = None
        self._fh = None

    def _ensure_file(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._fh:
                self._fh.close()
            path = self._data_dir / "clob" / self._asset_id / f"{today}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "a", encoding="utf-8")  # noqa: SIM115
            self._current_date = today

    def write(
        self,
        payload: dict,
        *,
        game_id: Optional[str] = None,
        regime: str = "pre-match",
    ) -> None:
        self._ensure_file()
        self._seq += 1
        envelope = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "seq": self._seq,
            "asset_id": self._asset_id,
            "game_id": game_id,
            "regime": regime,
            "payload": payload,
        }
        self._fh.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        self._fh.flush()

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None


# ---------------------------------------------------------------------------
# Single connection handler
# ---------------------------------------------------------------------------

class CLOBConnection:
    """Manages one WebSocket connection for one asset ID.

    Runs as an asyncio task. Implements:
      - 15-minute proactive recycle via internal cycle counter.
      - 90-second liveness probe: reconnects if no message arrives.
      - Exponential back-off on connection errors.
    """

    def __init__(
        self,
        asset_id: str,
        writer: EnvelopeWriter,
        stop_event: asyncio.Event,
        *,
        game_id: Optional[str] = None,
    ) -> None:
        self.asset_id = asset_id
        self._writer = writer
        self._stop = stop_event
        self._game_id = game_id
        self._regime = "pre-match"
        self._backoff = RECONNECT_BACKOFF_SECONDS

    def set_regime(self, regime: str) -> None:
        """Called by the correlation/discovery layer when match goes live."""
        self._regime = regime

    def set_game_id(self, game_id: str) -> None:
        self._game_id = game_id

    async def run(self) -> None:
        """Main loop. Reconnects indefinitely until stop_event is set."""
        url = f"{CLOB_WS_BASE}/{self.asset_id}"
        while not self._stop.is_set():
            try:
                await self._connect_and_pump(url)
                self._backoff = RECONNECT_BACKOFF_SECONDS  # reset on clean cycle
            except asyncio.CancelledError:
                logger.debug("CLOBConnection %s cancelled", self.asset_id)
                break
            except (ConnectionClosed, WebSocketException, OSError) as exc:
                if self._stop.is_set():
                    break
                logger.warning(
                    "CLOB %s connection error (%s); retrying in %ds",
                    self.asset_id,
                    exc,
                    self._backoff,
                )
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, 60)

    async def _connect_and_pump(self, url: str) -> None:
        """Open one WebSocket connection, pump until recycle time or liveness failure."""
        deadline = asyncio.get_event_loop().time() + RECYCLE_INTERVAL_SECONDS
        logger.debug("CLOB %s connecting", self.asset_id)

        async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
            logger.info("CLOB %s connected", self.asset_id)
            while not self._stop.is_set():
                # Check proactive recycle deadline
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    logger.debug(
                        "CLOB %s proactive 15-min recycle", self.asset_id
                    )
                    return  # caller reconnects

                # Wait for next message with liveness timeout
                liveness_window = min(remaining, LIVENESS_TIMEOUT_SECONDS)
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=liveness_window)
                except asyncio.TimeoutError:
                    # No message within liveness window — probe failed
                    logger.warning(
                        "CLOB %s liveness probe failed (%ds silence); reconnecting",
                        self.asset_id,
                        liveness_window,
                    )
                    return  # caller reconnects

                # Parse and write
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {"_raw": raw}

                self._writer.write(
                    payload,
                    game_id=self._game_id,
                    regime=self._regime,
                )


# ---------------------------------------------------------------------------
# Pool manager
# ---------------------------------------------------------------------------

class CLOBPool:
    """Manages a pool of CLOBConnection tasks.

    Public interface:
      add(asset_id)      — start capturing a new asset
      remove(asset_id)   — stop capturing an asset
      set_game_id(...)   — wire correlation after discovery
      set_regime(...)    — mark in-play when Sports WS fires
      size               — current pool size
      shutdown()         — gracefully stop all connections
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._connections: Dict[str, CLOBConnection] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._stop_events: Dict[str, asyncio.Event] = {}
        self._writers: Dict[str, EnvelopeWriter] = {}

    @property
    def size(self) -> int:
        return len(self._connections)

    def add(self, asset_id: str, *, game_id: Optional[str] = None) -> None:
        """Start a connection for asset_id. No-op if already pooled."""
        if asset_id in self._connections:
            return

        if self.size >= SOFT_ASSET_CAP:
            logger.warning(
                "CLOB pool at %d assets (soft cap %d) — adding %s anyway",
                self.size,
                SOFT_ASSET_CAP,
                asset_id,
            )

        writer = EnvelopeWriter(self._data_dir, asset_id)
        stop_event = asyncio.Event()
        conn = CLOBConnection(asset_id, writer, stop_event, game_id=game_id)
        task = asyncio.create_task(conn.run(), name=f"clob-{asset_id}")

        self._writers[asset_id] = writer
        self._stop_events[asset_id] = stop_event
        self._connections[asset_id] = conn
        self._tasks[asset_id] = task

        logger.info("CLOB pool: added %s (pool size now %d)", asset_id, self.size)

    def remove(self, asset_id: str) -> None:
        """Stop and remove asset_id from the pool."""
        if asset_id not in self._connections:
            return

        self._stop_events[asset_id].set()
        self._tasks[asset_id].cancel()
        self._writers[asset_id].close()

        del self._connections[asset_id]
        del self._tasks[asset_id]
        del self._stop_events[asset_id]
        del self._writers[asset_id]

        logger.info("CLOB pool: removed %s (pool size now %d)", asset_id, self.size)

    def set_game_id(self, asset_id: str, game_id: str) -> None:
        if asset_id in self._connections:
            self._connections[asset_id].set_game_id(game_id)

    def set_regime(self, asset_id: str, regime: str) -> None:
        if asset_id in self._connections:
            self._connections[asset_id].set_regime(regime)

    async def shutdown(self) -> None:
        """Gracefully stop all connections."""
        logger.info("CLOB pool: shutting down %d connections", self.size)
        asset_ids = list(self._connections.keys())
        for asset_id in asset_ids:
            self.remove(asset_id)
        # Allow cancelled tasks to clean up
        await asyncio.sleep(0)

    def status_report(self) -> dict:
        """For admin UI / healthcheck: pool summary."""
        return {
            "pool_size": self.size,
            "soft_cap": SOFT_ASSET_CAP,
            "headroom": SOFT_ASSET_CAP - self.size,
            "asset_ids": sorted(self._connections.keys()),
        }
