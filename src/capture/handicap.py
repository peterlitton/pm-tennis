"""
Handicap updater — Phase 3.

Listens to the CLOB tick stream for each asset and computes a 5-tick
median of the last-5 midpoint prices for each YES contract discovered
before the match goes live.

Per build plan §4.1:
  - Handicap = last-5-tick median, captured just before in-play.
  - If the most recent of those 5 ticks is older than 30 minutes,
    the handicap is marked stale and the asset is excluded from signal
    evaluation.
  - Handicap is fixed at match start (regime transition to in-play).
  - Written back to meta.json, replacing the PENDING_PHASE3 stub.

This module is passive — it subscribes to tick data from CLOBPool
via a callback and tracks per-asset price history.
"""

from __future__ import annotations

import json
import logging
import statistics
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

TICK_WINDOW = 5              # last N ticks for median
STALE_THRESHOLD_SECONDS = 30 * 60   # 30 minutes


# ---------------------------------------------------------------------------
# Per-asset tick buffer
# ---------------------------------------------------------------------------

class _AssetBuffer:
    def __init__(self, asset_id: str) -> None:
        self.asset_id = asset_id
        self.ticks: deque = deque(maxlen=TICK_WINDOW)  # (price, ts_utc)
        self.handicap_fixed = False
        self.handicap_value: Optional[float] = None
        self.handicap_ts: Optional[str] = None
        self.handicap_stale: bool = False

    def record_tick(self, price: float, ts_utc: datetime) -> None:
        if not self.handicap_fixed:
            self.ticks.append((price, ts_utc))

    def fix_handicap(self, game_id: str, data_dir: Path) -> Optional[float]:
        """Compute and persist the handicap. Called at regime → in-play."""
        if self.handicap_fixed:
            return self.handicap_value
        if not self.ticks:
            logger.warning("Handicap: no ticks available for %s — cannot fix", self.asset_id)
            return None

        prices = [p for p, _ in self.ticks]
        timestamps = [t for _, t in self.ticks]
        median_price = statistics.median(prices)
        most_recent_ts = max(timestamps)

        age_seconds = (datetime.now(timezone.utc) - most_recent_ts).total_seconds()
        stale = age_seconds > STALE_THRESHOLD_SECONDS

        self.handicap_fixed = True
        self.handicap_value = median_price
        self.handicap_ts = most_recent_ts.isoformat(timespec="milliseconds")
        self.handicap_stale = stale

        logger.info(
            "Handicap fixed for %s: %.4f (ticks=%d, age=%.0fs, stale=%s)",
            self.asset_id,
            median_price,
            len(prices),
            age_seconds,
            stale,
        )

        # Write to meta.json
        _write_handicap_to_meta(
            data_dir, game_id, self.asset_id, median_price, self.handicap_ts, stale
        )

        return median_price


def _write_handicap_to_meta(
    data_dir: Path,
    game_id: str,
    asset_id: str,
    price: float,
    ts: str,
    stale: bool,
) -> None:
    """Update the pre-match handicap fields in meta.json."""
    meta_path = data_dir / "matches" / game_id / "meta.json"
    if not meta_path.exists():
        logger.warning(
            "HandicapUpdater: meta.json not found for game_id %s (asset %s)",
            game_id,
            asset_id,
        )
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        # Find the moneyline market for this asset_id and update handicap
        updated = False
        for market in meta.get("moneyline_markets", []):
            for side in market.get("marketSides", []):
                if str(side.get("identifier")) == asset_id:
                    side["handicap_price"] = price
                    side["handicap_ts"] = ts
                    side["handicap_stale"] = stale
                    updated = True

        # Also update top-level handicap fields for convenience
        if "pre_match_handicap" not in meta:
            meta["pre_match_handicap"] = {}
        meta["pre_match_handicap"][asset_id] = {
            "price": price,
            "ts": ts,
            "stale": stale,
        }

        meta_path.write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        if updated:
            logger.info(
                "HandicapUpdater: wrote handicap %.4f to meta for asset %s (game %s, stale=%s)",
                price,
                asset_id,
                game_id,
                stale,
            )
        else:
            logger.warning(
                "HandicapUpdater: asset_id %s not found in moneyline_markets for game %s — "
                "wrote to pre_match_handicap top-level only",
                asset_id,
                game_id,
            )
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(
            "HandicapUpdater: failed to update meta for %s: %s", game_id, exc
        )


# ---------------------------------------------------------------------------
# HandicapUpdater — the public interface
# ---------------------------------------------------------------------------

class HandicapUpdater:
    """Tracks pre-match CLOB prices per asset and fixes handicaps at in-play.

    Usage:
        updater = HandicapUpdater(data_dir)
        updater.on_tick(asset_id, price, ts_utc)    # from CLOBPool callback
        updater.on_regime_change(game_id, asset_id, "in-play")  # fixes handicap
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._buffers: Dict[str, _AssetBuffer] = {}
        self._asset_to_game: Dict[str, str] = {}

    def register(self, asset_id: str, game_id: str) -> None:
        """Register an asset for handicap tracking."""
        if asset_id not in self._buffers:
            self._buffers[asset_id] = _AssetBuffer(asset_id)
        self._asset_to_game[asset_id] = game_id

    def on_tick(self, asset_id: str, price: float, ts_utc: Optional[datetime] = None) -> None:
        """Record a pre-match price tick. Ignored for assets already fixed."""
        if asset_id not in self._buffers:
            return
        buf = self._buffers[asset_id]
        if not buf.handicap_fixed:
            buf.record_tick(price, ts_utc or datetime.now(timezone.utc))

    def on_regime_change(self, game_id: str, asset_id: str, new_regime: str) -> None:
        """Fix the handicap when the match goes in-play."""
        if new_regime != "in-play":
            return
        if asset_id not in self._buffers:
            logger.warning(
                "HandicapUpdater: regime change for unregistered asset %s (game %s)",
                asset_id,
                game_id,
            )
            return
        self._buffers[asset_id].fix_handicap(game_id, self._data_dir)

    @staticmethod
    def extract_price_from_envelope(envelope: dict) -> Optional[float]:
        """Extract mid-price or last-trade-price from a CLOB envelope payload.

        Handles the two common Polymarket CLOB WS message shapes:
          - Book update: {"asks": [[price, size], ...], "bids": [[price, size], ...]}
          - Last trade:  {"type": "last_trade_price", "price": "0.62"}
        """
        payload = envelope.get("payload", {})
        msg_type = payload.get("type", "")

        if msg_type == "last_trade_price":
            try:
                return float(payload.get("price", 0))
            except (TypeError, ValueError):
                return None

        # Book update: compute mid from best bid and best ask
        asks = payload.get("asks") or []
        bids = payload.get("bids") or []
        try:
            best_ask = float(asks[0][0]) if asks else None
            best_bid = float(bids[0][0]) if bids else None
            if best_ask is not None and best_bid is not None:
                return (best_ask + best_bid) / 2.0
            return best_ask or best_bid
        except (IndexError, TypeError, ValueError):
            return None

    def status_report(self) -> dict:
        fixed = sum(1 for b in self._buffers.values() if b.handicap_fixed)
        stale = sum(1 for b in self._buffers.values() if b.handicap_stale)
        pending = len(self._buffers) - fixed
        return {
            "tracked_assets": len(self._buffers),
            "handicaps_fixed": fixed,
            "handicaps_stale": stale,
            "pending": pending,
        }
