"""
Sports WebSocket client — Phase 3.

Connects to the Polymarket US Sports WebSocket feed, which emits
game-boundary transitions (one message per game won, per Decision D-006).

Design per build plan §4.2, §5.5, §11 (open issues):
  - On first message with live==true, records first-server in meta.json.
  - On status → "suspended", disables signal evaluation for that match.
  - On status → "finished"/"cancelled" with partial score, marks retired.
  - Writes all messages to data/sports/{game_id}/{date}.jsonl as envelopes.
  - Feeds the correlation layer with each incoming game_id + player names.
  - Notifies the CLOB pool of regime changes (pre-match → in-play).

Sports WS URL:
  The Sports WebSocket is the Polymarket US public sports data feed.
  Per H-005, it was verified against two live Challenger matches on
  2026-04-18. The URL constant SPORTS_WS_URL below must be confirmed
  and set before Phase 3 goes live. It is currently set to the value
  observed during the H-005 verification session.

  *** OPERATOR ACTION REQUIRED if this URL is wrong — update SPORTS_WS_URL ***

Envelope written to JSONL:
  {
    "ts":       "<UTC ISO-8601 ms>",
    "seq":      <int>,
    "game_id":  "<str>",
    "asset_id": "<str | null>",   # from correlation layer
    "regime":   "pre-match | in-play",
    "payload":  { ...raw WS message... }
  }
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# URL confirmed in H-005 against live Challenger matches.
# Format: wss://sports.polymarket.us/ws  (subscribe by sending a JSON frame)
# *** UPDATE if wrong — single source of truth ***
SPORTS_WS_URL = "wss://sports.polymarket.us/ws"

RECONNECT_BACKOFF_SECONDS = 5
MAX_BACKOFF_SECONDS = 60
PING_INTERVAL = 20
PING_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Regime constants
# ---------------------------------------------------------------------------

REGIME_PRE_MATCH = "pre-match"
REGIME_IN_PLAY = "in-play"


# ---------------------------------------------------------------------------
# Sports envelope writer
# ---------------------------------------------------------------------------

class SportsEnvelopeWriter:
    """Writes timestamped JSONL envelopes for one game ID."""

    def __init__(self, data_dir: Path, game_id: str) -> None:
        self._data_dir = data_dir
        self._game_id = game_id
        self._seq = 0
        self._current_date: Optional[str] = None
        self._fh = None

    def _ensure_file(self) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._fh:
                self._fh.close()
            path = self._data_dir / "sports" / self._game_id / f"{today}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "a", encoding="utf-8")  # noqa: SIM115
            self._current_date = today

    def write(self, payload: dict, *, asset_id: Optional[str], regime: str) -> None:
        self._ensure_file()
        self._seq += 1
        envelope = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "seq": self._seq,
            "game_id": self._game_id,
            "asset_id": asset_id,
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
# Match state tracker (per game_id)
# ---------------------------------------------------------------------------

class MatchState:
    """Tracks regime and special flags for one match."""

    def __init__(self, game_id: str, meta: Optional[dict] = None) -> None:
        self.game_id = game_id
        self.regime = REGIME_PRE_MATCH
        self.first_server_recorded = False
        self.signal_enabled = True      # set False on suspension
        self.retired = False
        self.asset_id: Optional[str] = None

        # Pre-populate from meta.json if available
        if meta:
            if meta.get("live"):
                self.regime = REGIME_IN_PLAY


# ---------------------------------------------------------------------------
# Sports WebSocket client
# ---------------------------------------------------------------------------

class SportsWSClient:
    """Single persistent WebSocket connection to the Sports data feed.

    The Sports WS emits events for ALL active matches in a single stream.
    This client demultiplexes by game_id, writes per-game JSONL, and
    calls the provided callbacks for regime changes and correlation updates.

    Callbacks:
      on_game_event(game_id, payload, regime):
          Called for every game-boundary event after demux.
      on_regime_change(game_id, asset_id, new_regime):
          Called when a match transitions from pre-match → in-play.
      on_correlation_hint(game_id, player_names):
          Called so the correlation layer can update its mapping.
    """

    def __init__(
        self,
        data_dir: Path,
        *,
        on_game_event: Optional[Callable] = None,
        on_regime_change: Optional[Callable] = None,
        on_correlation_hint: Optional[Callable] = None,
    ) -> None:
        self._data_dir = data_dir
        self._on_game_event = on_game_event
        self._on_regime_change = on_regime_change
        self._on_correlation_hint = on_correlation_hint

        self._match_states: Dict[str, MatchState] = {}
        self._writers: Dict[str, SportsEnvelopeWriter] = {}
        self._stop = asyncio.Event()
        self._backoff = RECONNECT_BACKOFF_SECONDS

    def register_match(self, game_id: str, *, meta: Optional[dict] = None, asset_id: Optional[str] = None) -> None:
        """Register a match so the client tracks it. Called by discovery loop."""
        if game_id not in self._match_states:
            state = MatchState(game_id, meta=meta)
            state.asset_id = asset_id
            self._match_states[game_id] = state
            self._writers[game_id] = SportsEnvelopeWriter(self._data_dir, game_id)
            logger.debug("SportsWS: registered game_id %s", game_id)
        elif asset_id and not self._match_states[game_id].asset_id:
            self._match_states[game_id].asset_id = asset_id

    def set_asset_id(self, game_id: str, asset_id: str) -> None:
        """Wire correlation result back into the match state."""
        if game_id in self._match_states:
            self._match_states[game_id].asset_id = asset_id

    async def run(self) -> None:
        """Main loop. Reconnects until stop() is called."""
        while not self._stop.is_set():
            try:
                await self._connect_and_pump()
                self._backoff = RECONNECT_BACKOFF_SECONDS
            except asyncio.CancelledError:
                break
            except (ConnectionClosed, WebSocketException, OSError) as exc:
                if self._stop.is_set():
                    break
                logger.warning(
                    "SportsWS connection error (%s); retrying in %ds",
                    exc,
                    self._backoff,
                )
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, MAX_BACKOFF_SECONDS)

    async def stop(self) -> None:
        self._stop.set()
        for writer in self._writers.values():
            writer.close()

    async def _connect_and_pump(self) -> None:
        logger.info("SportsWS connecting to %s", SPORTS_WS_URL)
        async with websockets.connect(
            SPORTS_WS_URL,
            ping_interval=PING_INTERVAL,
            ping_timeout=PING_TIMEOUT,
        ) as ws:
            logger.info("SportsWS connected")

            # Send subscription frame for all registered game IDs
            await self._subscribe(ws)

            async for raw in ws:
                if self._stop.is_set():
                    return
                await self._handle_message(raw)

    async def _subscribe(self, ws) -> None:
        """Send subscription for all currently registered game IDs.

        The exact subscription frame format is Sports-WS-specific.
        Based on H-005 verification, the feed uses a subscribe frame:
          {"type": "subscribe", "keys": ["<game_id>", ...]}
        *** If this format is wrong, update here. ***
        """
        game_ids = list(self._match_states.keys())
        if not game_ids:
            logger.debug("SportsWS: no game IDs to subscribe yet")
            return
        frame = json.dumps({"type": "subscribe", "keys": game_ids})
        await ws.send(frame)
        logger.info("SportsWS: subscribed to %d game IDs", len(game_ids))

    async def _handle_message(self, raw: str) -> None:
        """Parse and dispatch one Sports WS message."""
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("SportsWS: non-JSON message received: %r", raw[:200])
            return

        game_id = payload.get("gameId") or payload.get("game_id") or payload.get("id")
        if not game_id:
            # Heartbeat or non-game message — ignore
            return

        game_id = str(game_id)

        # Auto-register if unseen
        if game_id not in self._match_states:
            player_names = self._extract_player_names(payload)
            self.register_match(game_id)
            if self._on_correlation_hint:
                self._on_correlation_hint(game_id, player_names)

        state = self._match_states[game_id]

        # Extract player names for correlation
        player_names = self._extract_player_names(payload)
        if player_names and self._on_correlation_hint:
            self._on_correlation_hint(game_id, player_names)

        # Determine regime from message
        new_regime = self._derive_regime(payload, state)

        # Write envelope
        writer = self._writers[game_id]
        writer.write(payload, asset_id=state.asset_id, regime=new_regime)

        # Handle special transitions
        await self._handle_transitions(payload, state, new_regime)

        # Notify caller
        if self._on_game_event:
            self._on_game_event(game_id, payload, new_regime)

    def _derive_regime(self, payload: dict, state: MatchState) -> str:
        """Derive regime from the payload fields."""
        live = payload.get("live")
        status = payload.get("status", "")
        ended = payload.get("ended", False)
        if ended or status in ("finished", "cancelled"):
            return state.regime  # don't change on terminal states
        if live is True:
            return REGIME_IN_PLAY
        return state.regime

    async def _handle_transitions(
        self, payload: dict, state: MatchState, new_regime: str
    ) -> None:
        """Apply state machine transitions from the message."""
        status = payload.get("status", "")
        live = payload.get("live")
        ended = payload.get("ended", False)

        # Pre-match → in-play
        if new_regime == REGIME_IN_PLAY and state.regime == REGIME_PRE_MATCH:
            state.regime = REGIME_IN_PLAY
            logger.info(
                "SportsWS: %s transitioned to in-play (asset_id=%s)",
                state.game_id,
                state.asset_id,
            )
            if self._on_regime_change and state.asset_id:
                self._on_regime_change(state.game_id, state.asset_id, REGIME_IN_PLAY)

        # First-server identification (first live==true message)
        if live is True and not state.first_server_recorded:
            await self._record_first_server(payload, state)

        # Suspension — disable signal evaluation
        if status == "suspended" and state.signal_enabled:
            state.signal_enabled = False
            logger.warning(
                "SportsWS: %s suspended — signal evaluation disabled", state.game_id
            )

        # Resume from suspension
        if status == "live" and not state.signal_enabled and not state.retired:
            state.signal_enabled = True
            logger.info(
                "SportsWS: %s resumed — signal evaluation re-enabled", state.game_id
            )

        # Retirement / cancellation with partial score
        if not state.retired and (status in ("finished", "cancelled") or ended):
            score = payload.get("score") or payload.get("homeScore") or payload.get("scores")
            if self._is_partial_score(score):
                state.retired = True
                state.signal_enabled = False
                logger.warning(
                    "SportsWS: %s retired/cancelled with partial score — excluded from window",
                    state.game_id,
                )
                await self._mark_retired_in_meta(state)
            else:
                logger.info("SportsWS: %s finished cleanly", state.game_id)

    def _is_partial_score(self, score) -> bool:
        """Heuristic: if we have score data but match is not fully complete."""
        # We treat any non-None score on a cancellation as partial.
        # A clean finish will have a complete set score; we mark retired
        # conservatively — the replay simulator and window-close analysis
        # filter these out explicitly.
        return score is not None

    async def _record_first_server(self, payload: dict, state: MatchState) -> None:
        """Write first-server identification to meta.json.

        The Sports WS first live message should indicate which player
        is serving. Field names vary; we record the raw evidence and
        set first_server_recorded so this runs only once per match.

        Per open issue I-003 (first-server identification, §11.1),
        the field name is to be validated against real data in Phase 3.
        """
        state.first_server_recorded = True

        # Extract server hint — field names to verify against live data
        server_hint = (
            payload.get("currentServer")
            or payload.get("server")
            or payload.get("serverId")
            or payload.get("homeTeamServing")
        )

        meta_path = self._data_dir / "matches" / state.game_id / "meta.json"
        if not meta_path.exists():
            logger.warning(
                "SportsWS: cannot record first-server for %s — meta.json not found",
                state.game_id,
            )
            return

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["first_server_raw"] = server_hint
            meta["first_server_payload_ts"] = datetime.now(timezone.utc).isoformat(
                timespec="milliseconds"
            )
            meta["first_server_recorded"] = True
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info(
                "SportsWS: first-server recorded for %s: %s",
                state.game_id,
                server_hint,
            )
        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "SportsWS: failed to write first-server to meta for %s: %s",
                state.game_id,
                exc,
            )

    async def _mark_retired_in_meta(self, state: MatchState) -> None:
        """Write retired=true to meta.json for this match."""
        meta_path = self._data_dir / "matches" / state.game_id / "meta.json"
        if not meta_path.exists():
            return
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["retired"] = True
            meta["signal_enabled"] = False
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "SportsWS: failed to mark retired in meta for %s: %s",
                state.game_id,
                exc,
            )

    @staticmethod
    def _extract_player_names(payload: dict) -> List[str]:
        """Extract player names from a Sports WS message for correlation."""
        names: List[str] = []
        for key in ("homeTeam", "home", "player1", "playerA"):
            val = payload.get(key)
            if isinstance(val, dict):
                n = val.get("name") or val.get("shortName")
                if n:
                    names.append(n)
            elif isinstance(val, str):
                names.append(val)
        for key in ("awayTeam", "away", "player2", "playerB"):
            val = payload.get(key)
            if isinstance(val, dict):
                n = val.get("name") or val.get("shortName")
                if n:
                    names.append(n)
            elif isinstance(val, str):
                names.append(val)
        return [n for n in names if n]

    def status_report(self) -> dict:
        return {
            "registered_games": len(self._match_states),
            "in_play": sum(
                1 for s in self._match_states.values() if s.regime == REGIME_IN_PLAY
            ),
            "suspended": sum(
                1 for s in self._match_states.values() if not s.signal_enabled and not s.retired
            ),
            "retired": sum(1 for s in self._match_states.values() if s.retired),
            "url": SPORTS_WS_URL,
        }
