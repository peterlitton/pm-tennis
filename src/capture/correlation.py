"""
Correlation layer — Phase 3.

Maps Sports WS game IDs to Polymarket asset IDs (and vice versa).

Algorithm (§5.5):
  1. Exact match on sportradar_game_id stored in meta.json at discovery time.
  2. If no exact match: fuzzy player-name matching on the player names
     surfaced by the Sports WS message vs. those stored in meta.json.
  3. Manual overrides: data/overrides/name_aliases.json takes precedence
     over both.

Unseen-gameId buffer:
  Sports WS messages that arrive before the corresponding meta.json has
  been written (discovery lag) are held in a buffer for up to two
  discovery cycles (2 × 60 s = 120 s by default). After that they are
  dropped with a WARN log.

Usage:
  correlator = Correlator(data_dir, discovery_cycle_seconds=60)
  await correlator.load()          # reads meta.json files and overrides
  asset_ids = correlator.resolve(game_id, player_names=["A", "B"])
  correlator.refresh()             # call after each discovery poll cycle
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fuzzy name matching
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    """Lower-case, strip punctuation, collapse whitespace."""
    import re
    name = name.lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _name_overlap_score(sports_names: List[str], meta_names: List[str]) -> float:
    """Return fraction of Sports WS player tokens that appear in meta player names.

    A score of 1.0 means every Sports WS name token matches at least one
    meta name token. Used to rank candidate matches.
    """
    if not sports_names or not meta_names:
        return 0.0
    normed_meta = " ".join(_normalise(n) for n in meta_names)
    scores = []
    for name in sports_names:
        tokens = _normalise(name).split()
        if not tokens:
            continue
        matched = sum(1 for t in tokens if t in normed_meta)
        scores.append(matched / len(tokens))
    return sum(scores) / len(scores) if scores else 0.0


# ---------------------------------------------------------------------------
# Unseen-gameId buffer entry
# ---------------------------------------------------------------------------

@dataclass
class _BufferedMessage:
    game_id: str
    player_names: List[str]
    first_seen: float           # time.monotonic()
    arrival_cycle: int          # discovery cycle count at arrival
    cycles_held: int = 0


# ---------------------------------------------------------------------------
# Correlator
# ---------------------------------------------------------------------------

class Correlator:
    """Maintains the game_id → asset_id mapping for all active matches.

    All public methods are synchronous; this class does not own any async
    tasks. The pool manager calls refresh() after each discovery cycle.
    """

    FUZZY_THRESHOLD = 0.5       # minimum overlap score to accept a fuzzy match

    def __init__(
        self,
        data_dir: Path,
        *,
        discovery_cycle_seconds: int = 60,
        buffer_cycles: int = 2,
    ) -> None:
        self._data_dir = data_dir
        self._discovery_cycle_seconds = discovery_cycle_seconds
        self._buffer_cycles = buffer_cycles

        # game_id → asset_id (authoritative mapping, from exact or fuzzy match)
        self._game_to_asset: Dict[str, str] = {}

        # asset_id → list of player names (from meta.json)
        self._asset_players: Dict[str, List[str]] = {}

        # asset_id → sportradar_game_id (from meta.json)
        self._asset_sportradar_id: Dict[str, Optional[str]] = {}

        # manual overrides: game_id → asset_id (takes precedence over all)
        self._overrides: Dict[str, str] = {}

        # unseen-gameId buffer
        self._buffer: Dict[str, _BufferedMessage] = {}

        # discovery cycle counter (incremented by refresh())
        self._cycle: int = 0

    # ------------------------------------------------------------------
    # Initialisation and refresh
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load meta.json files and overrides. Call once at startup."""
        self._load_overrides()
        self._scan_meta_files()
        logger.info(
            "Correlator loaded: %d meta files, %d overrides, %d pre-existing mappings",
            len(self._asset_players),
            len(self._overrides),
            len(self._game_to_asset),
        )

    def refresh(self) -> None:
        """Call after each discovery poll cycle.

        - Rescans meta.json files for new entries.
        - Ages out unseen-gameId buffer entries that have been held too long.
        - Retries buffered messages against newly loaded meta files.
        """
        self._cycle += 1
        self._load_overrides()   # overrides file may be updated by operator
        self._scan_meta_files()
        self._flush_buffer()

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        game_id: str,
        *,
        player_names: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return asset_id for game_id, or None if not yet correlated.

        If the game_id is not yet mapped, it is buffered for up to
        buffer_cycles discovery cycles. A WARN is logged when dropped.
        """
        # 1. Manual override
        if game_id in self._overrides:
            asset_id = self._overrides[game_id]
            self._game_to_asset[game_id] = asset_id
            return asset_id

        # 2. Already mapped
        if game_id in self._game_to_asset:
            return self._game_to_asset[game_id]

        # 3. Try to resolve now
        asset_id = self._try_resolve(game_id, player_names or [])
        if asset_id:
            self._game_to_asset[game_id] = asset_id
            # Remove from buffer if it was waiting
            self._buffer.pop(game_id, None)
            return asset_id

        # 4. Buffer for later
        if game_id not in self._buffer:
            self._buffer[game_id] = _BufferedMessage(
                game_id=game_id,
                player_names=player_names or [],
                first_seen=time.monotonic(),
                arrival_cycle=self._cycle,
            )
            logger.debug(
                "Correlator: game_id %s buffered (cycle %d)", game_id, self._cycle
            )
        return None

    def reverse_lookup(self, asset_id: str) -> Optional[str]:
        """Return game_id for asset_id, or None."""
        for gid, aid in self._game_to_asset.items():
            if aid == asset_id:
                return gid
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_resolve(self, game_id: str, player_names: List[str]) -> Optional[str]:
        """Try exact sportradar match, then fuzzy name match."""
        # Exact sportradar_game_id match
        for asset_id, sr_id in self._asset_sportradar_id.items():
            if sr_id and sr_id == game_id:
                logger.debug(
                    "Correlator: exact sportradar match %s → %s", game_id, asset_id
                )
                return asset_id

        # Fuzzy name match
        if not player_names:
            return None

        best_score = 0.0
        best_asset: Optional[str] = None
        for asset_id, meta_names in self._asset_players.items():
            score = _name_overlap_score(player_names, meta_names)
            if score > best_score:
                best_score = score
                best_asset = asset_id

        if best_asset and best_score >= self.FUZZY_THRESHOLD:
            logger.info(
                "Correlator: fuzzy match %s → %s (score %.2f)",
                game_id,
                best_asset,
                best_score,
            )
            return best_asset

        return None

    def _scan_meta_files(self) -> None:
        """Read all meta.json files under data/matches/."""
        matches_dir = self._data_dir / "matches"
        if not matches_dir.exists():
            return

        for meta_path in matches_dir.glob("*/meta.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Correlator: could not read %s: %s", meta_path, exc)
                continue

            # Derive canonical asset_id from moneyline market side identifiers
            # (written by discovery module), falling back to directory name.
            side_ids: List[str] = []
            for market in meta.get("moneyline_markets", []):
                for side in market.get("marketSides", []):
                    sid = side.get("identifier")
                    if sid:
                        side_ids.append(str(sid))
            asset_id = side_ids[0] if side_ids else str(meta_path.parent.name)

            # Collect player names from participants
            names: List[str] = []
            for p in meta.get("participants", []):
                n = p.get("name") or p.get("player", {}).get("name")
                if n:
                    names.append(n)
            self._asset_players[asset_id] = names

            # Record sportradar game ID
            sr_id = meta.get("sportradar_game_id")
            self._asset_sportradar_id[asset_id] = sr_id

            # If sportradar ID is already known, register mapping immediately
            if sr_id and sr_id not in self._game_to_asset:
                self._game_to_asset[sr_id] = asset_id

    def _load_overrides(self) -> None:
        """Load manual overrides from data/overrides/name_aliases.json."""
        overrides_path = self._data_dir / "overrides" / "name_aliases.json"
        if not overrides_path.exists():
            return
        try:
            data = json.loads(overrides_path.read_text(encoding="utf-8"))
            self._overrides = {str(k): str(v) for k, v in data.items()}
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Correlator: could not read overrides: %s", exc)

    def _flush_buffer(self) -> None:
        """Retry buffered game IDs; drop those that have waited too long."""
        to_drop = []
        for game_id, entry in self._buffer.items():
            entry.cycles_held = self._cycle - entry.arrival_cycle

            # Retry resolution
            asset_id = self._try_resolve(game_id, entry.player_names)
            if asset_id:
                self._game_to_asset[game_id] = asset_id
                to_drop.append(game_id)
                logger.info(
                    "Correlator: buffered %s resolved to %s after %d cycles",
                    game_id,
                    asset_id,
                    entry.cycles_held,
                )
                continue

            # Expire
            if entry.cycles_held >= self._buffer_cycles:
                to_drop.append(game_id)
                logger.warning(
                    "Correlator: dropping game_id %s after %d cycles unresolved "
                    "(player_names=%s)",
                    game_id,
                    entry.cycles_held,
                    entry.player_names,
                )

        for game_id in to_drop:
            self._buffer.pop(game_id, None)

    def status_report(self) -> dict:
        """For admin UI / healthcheck."""
        return {
            "mapped_games": len(self._game_to_asset),
            "known_assets": len(self._asset_players),
            "buffered_unresolved": len(self._buffer),
            "overrides_loaded": len(self._overrides),
            "discovery_cycle": self._cycle,
        }
