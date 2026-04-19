"""
src/capture/discovery.py
PM-Tennis Phase 2 — Discovery and Metadata

Polls the Polymarket US public gateway for active tennis events, extracts
moneyline markets and asset identifiers, writes meta.json per match, and
emits a discovery-delta stream (added / removed event IDs) that the Phase 3
capture worker will consume.

API surface used:
  Public gateway (no auth): https://gateway.polymarket.us
  GET /v2/sports              — enumerate all sports, verify slug resolves
  GET /v2/sports/{slug}/events — list active events for a sport

Field references:
  event.id                   — Polymarket US event ID (string)
  event.slug                 — URL slug
  event.title                — human-readable match title
  event.sportradarGameId     — Sportradar game ID (Sports WS correlation key)
  event.active               — bool: event is open for trading
  event.closed               — bool: event is closed/resolved
  event.ended                — bool: match has finished
  event.live                 — bool: match is currently in-play
  event.startDate / endDate  — ISO-8601 strings
  event.eventDate            — scheduled match date
  event.startTime            — scheduled start time
  event.eventState.tennisState.tournamentName — tournament name
  event.eventState.tennisState.round          — round (e.g. "R32", "QF", "F")
  event.participants[]       — player participant objects
  event.markets[]            — child markets for this event
    market.sportsMarketTypeV2 — "SPORTS_MARKET_TYPE_MONEYLINE" for moneylines
    market.active             — market is open
    market.closed             — market is closed
    market.id                 — market ID (string)
    market.slug               — market slug
    market.marketSides[]      — YES/NO sides
      side.identifier         — asset/token ID for CLOB subscription
      side.long               — true = YES/long side
      side.description        — side label (player name or "Yes"/"No")

Design notes:
  - TENNIS_SPORT_SLUG is a module-level constant; verified at startup.
  - Startup verification calls /v2/sports, checks the slug is present, and
    logs all available sports for operator visibility.
  - Poll loop runs at POLL_INTERVAL_SECONDS (default 60s).
  - Each poll response is written to data/events/ as a raw JSONL snapshot.
  - meta.json is written per newly-discovered match; existing meta.json files
    are never overwritten (they are immutable once written).
  - Pre-match handicap capture (5-tick median) is Phase 3 work; discovery
    writes a handicap_stub into meta.json that Phase 3 populates.
  - Discovery delta: added/removed event IDs are written to a delta JSONL
    that the capture worker tails.
  - Slug truncation (RAID lesser issue): event slugs longer than 200 chars
    are truncated and flagged in the meta with slug_truncated=true.
  - Player-appears-twice guard: if the same player slug appears on the same
    calendar day, both events are kept but a duplicate_player_flag is set.
  - Doubles/mixed exclusion: events whose title or participant list suggests
    doubles ("/ " separator pattern, more than 2 participants) are flagged
    and excluded from signal evaluation scope (captured for archival).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Sport slug used to query the Polymarket US gateway.
# Verified at startup against GET /v2/sports. Override via env var
# PMTENNIS_SPORT_SLUG if Polymarket US ever renames the sport.
TENNIS_SPORT_SLUG: str = os.environ.get("PMTENNIS_SPORT_SLUG", "tennis")

# Polymarket US public gateway — no auth required for read operations.
GATEWAY_BASE: str = "https://gateway.polymarket.us"

# How often to poll for new/changed events (seconds).
POLL_INTERVAL_SECONDS: int = int(os.environ.get("PMTENNIS_POLL_INTERVAL", "60"))

# Maximum slug length before truncation is applied and flagged.
MAX_SLUG_LENGTH: int = 200

# Marker value used in meta.json stubs awaiting Phase 3 population.
HANDICAP_STUB: str = "PENDING_PHASE3"

# Root for all persistent data on the Render disk.
DATA_ROOT: Path = Path(os.environ.get("PMTENNIS_DATA_ROOT", "/data"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger("pm_tennis.discovery")

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MarketSide:
    """One tradeable side (YES/long or NO/short) of a market."""
    side_id: str
    identifier: str          # asset/token ID for CLOB WebSocket subscription
    long: bool               # True = YES side
    description: str         # player name or generic label from API
    price: str               # last quoted price string (e.g. "0.62")
    market_side_type: str    # "MARKET_SIDE_TYPE_ERC1155" etc.


@dataclass
class MoneylineMarket:
    """A single moneyline market nested inside an event."""
    market_id: str
    market_slug: str
    active: bool
    closed: bool
    best_bid: float | None
    best_ask: float | None
    sides: list[MarketSide] = field(default_factory=list)


@dataclass
class TennisEventMeta:
    """
    Canonical metadata for one discovered tennis event.
    Written as meta.json to data/matches/{event_id}/meta.json.
    Immutable once written; Phase 3 populates handicap fields.
    """
    # --- Identity ---
    event_id: str
    event_slug: str
    slug_truncated: bool

    # --- Match context ---
    title: str
    tournament_name: str     # from eventState.tennisState.tournamentName
    round: str               # from eventState.tennisState.round
    sport_slug: str          # always TENNIS_SPORT_SLUG at write time
    series_slug: str

    # --- Timing ---
    event_date: str          # YYYY-MM-DD
    start_time: str          # HH:MM or empty
    start_date_iso: str      # full ISO from API
    end_date_iso: str

    # --- Players ---
    player_a_name: str
    player_b_name: str
    participants_raw: list[dict]   # full participant objects for auditability

    # --- Markets ---
    moneyline_markets: list[dict]  # serialised MoneylineMarket objects

    # --- Sportradar correlation ---
    sportradar_game_id: str  # Sports WS game ID; empty string if absent

    # --- Status at discovery time ---
    live_at_discovery: bool
    ended_at_discovery: bool
    active_at_discovery: bool

    # --- Quality flags ---
    doubles_flag: bool           # True = suspected doubles/mixed event
    duplicate_player_flag: bool  # True = same player seen today already

    # --- Handicap stub (Phase 3 populates) ---
    handicap_player_a: str = HANDICAP_STUB
    handicap_player_b: str = HANDICAP_STUB
    handicap_captured_at: str = ""
    handicap_stale: bool = False
    first_server: str = HANDICAP_STUB   # Phase 3 populates from first live WS msg

    # --- Provenance ---
    discovered_at: str = ""      # UTC ISO-8601 wall-clock at discovery
    discovery_session: str = ""  # "H-007" etc., injected by caller if known


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _extract_player_names(participants: list[dict]) -> tuple[str, str]:
    """
    Extract player A and player B names from the participants list.
    Polymarket US uses PARTICIPANT_TYPE_PLAYER for individual tennis players.
    Falls back to nominee name, then to a positional placeholder.
    Returns ("Player A", "Player B") strings.
    """
    names: list[str] = []
    for p in participants:
        ptype = p.get("type", "")
        if ptype == "PARTICIPANT_TYPE_PLAYER":
            player = p.get("player") or {}
            name = player.get("name", "").strip()
        elif ptype == "PARTICIPANT_TYPE_NOMINEE":
            nominee = p.get("nominee") or {}
            name = nominee.get("name", "").strip()
        elif ptype == "PARTICIPANT_TYPE_TEAM":
            team = p.get("team") or {}
            name = team.get("name", "").strip()
        else:
            name = ""
        if name:
            names.append(name)

    player_a = names[0] if len(names) > 0 else "Unknown_A"
    player_b = names[1] if len(names) > 1 else "Unknown_B"
    return player_a, player_b


def _is_doubles_event(title: str, participants: list[dict]) -> bool:
    """
    Heuristic doubles detection.
    Doubles titles typically contain " / " separating partner names within
    each side, e.g. "Smith/Jones vs Williams/Brown".
    Also flags if more than 2 named participants are present.
    """
    if " / " in title or "/" in title:
        # Slash in title is a strong doubles indicator
        return True
    named = [
        p for p in participants
        if (p.get("player") or p.get("nominee") or p.get("team") or {}).get("name", "")
    ]
    return len(named) > 2


def _parse_moneyline_markets(markets_raw: list[dict]) -> list[MoneylineMarket]:
    """
    Filter to moneyline markets only and parse their sides.
    Polymarket US uses sportsMarketTypeV2 == "SPORTS_MARKET_TYPE_MONEYLINE".
    """
    result: list[MoneylineMarket] = []
    for m in markets_raw:
        if m.get("sportsMarketTypeV2") != "SPORTS_MARKET_TYPE_MONEYLINE":
            continue
        sides_raw = m.get("marketSides") or []
        sides = [
            MarketSide(
                side_id=str(s.get("id", "")),
                identifier=str(s.get("identifier", "")),
                long=bool(s.get("long", False)),
                description=str(s.get("description", "")),
                price=str(s.get("price", "")),
                market_side_type=str(s.get("marketSideType", "")),
            )
            for s in sides_raw
        ]
        result.append(
            MoneylineMarket(
                market_id=str(m.get("id", "")),
                market_slug=str(m.get("slug", "")),
                active=bool(m.get("active", False)),
                closed=bool(m.get("closed", False)),
                best_bid=m.get("bestBid"),
                best_ask=m.get("bestAsk"),
                sides=sides,
            )
        )
    return result


def _safe_slug(slug: str) -> tuple[str, bool]:
    """Truncate slug if over MAX_SLUG_LENGTH; return (slug, was_truncated)."""
    if len(slug) > MAX_SLUG_LENGTH:
        return slug[:MAX_SLUG_LENGTH], True
    return slug, False


def _parse_event(event: dict) -> TennisEventMeta | None:
    """
    Parse one raw event dict from the gateway into a TennisEventMeta.
    Returns None if the event is missing required identity fields.
    """
    event_id = str(event.get("id", "")).strip()
    if not event_id:
        log.warning("Skipping event with missing id: %s", event.get("slug"))
        return None

    raw_slug = str(event.get("slug", "")).strip()
    event_slug, slug_truncated = _safe_slug(raw_slug)

    participants = event.get("participants") or []
    player_a, player_b = _extract_player_names(participants)
    title = str(event.get("title", "")).strip()
    doubles_flag = _is_doubles_event(title, participants)

    # Tennis-specific state
    event_state = event.get("eventState") or {}
    tennis_state = event_state.get("tennisState") or {}
    tournament_name = str(tennis_state.get("tournamentName", "")).strip()
    round_str = str(tennis_state.get("round", "")).strip()

    moneyline_markets = _parse_moneyline_markets(event.get("markets") or [])

    sportradar_game_id = str(event.get("sportradarGameId") or "").strip()

    slug_str, _ = _safe_slug(str(event.get("seriesSlug") or ""))

    return TennisEventMeta(
        event_id=event_id,
        event_slug=event_slug,
        slug_truncated=slug_truncated,
        title=title,
        tournament_name=tournament_name,
        round=round_str,
        sport_slug=TENNIS_SPORT_SLUG,
        series_slug=slug_str,
        event_date=str(event.get("eventDate") or "").strip(),
        start_time=str(event.get("startTime") or "").strip(),
        start_date_iso=str(event.get("startDate") or "").strip(),
        end_date_iso=str(event.get("endDate") or "").strip(),
        player_a_name=player_a,
        player_b_name=player_b,
        participants_raw=participants,
        moneyline_markets=[asdict(m) for m in moneyline_markets],  # type: ignore[call-overload]
        sportradar_game_id=sportradar_game_id,
        live_at_discovery=bool(event.get("live", False)),
        ended_at_discovery=bool(event.get("ended", False)),
        active_at_discovery=bool(event.get("active", False)),
        doubles_flag=doubles_flag,
        duplicate_player_flag=False,  # set by caller after dedup check
        discovered_at=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------


def _match_dir(event_id: str) -> Path:
    return DATA_ROOT / "matches" / event_id


def _meta_path(event_id: str) -> Path:
    return _match_dir(event_id) / "meta.json"


def _events_snapshot_dir() -> Path:
    return DATA_ROOT / "events"


def _delta_path() -> Path:
    return DATA_ROOT / "events" / "discovery_delta.jsonl"


def _write_meta(meta: TennisEventMeta) -> None:
    """Write meta.json for a newly discovered event. Never overwrites."""
    path = _meta_path(meta.event_id)
    if path.exists():
        return  # immutable once written
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(meta), indent=2), encoding="utf-8")  # type: ignore[call-overload]
    log.info("meta.json written: event_id=%s title=%r", meta.event_id, meta.title)


def _write_event_snapshot(events: list[dict], poll_ts: str) -> None:
    """
    Write raw poll response to data/events/{date}.jsonl for archival.
    One JSONL line per event, tagged with the poll timestamp.
    """
    snap_dir = _events_snapshot_dir()
    snap_dir.mkdir(parents=True, exist_ok=True)
    date_str = poll_ts[:10]  # YYYY-MM-DD
    snap_path = snap_dir / f"{date_str}.jsonl"
    with snap_path.open("a", encoding="utf-8") as fh:
        for ev in events:
            line = json.dumps({"poll_ts": poll_ts, "event": ev}, ensure_ascii=False)
            fh.write(line + "\n")


def _write_delta(added: list[str], removed: list[str], poll_ts: str) -> None:
    """Append a delta record to discovery_delta.jsonl."""
    if not added and not removed:
        return
    delta_path = _delta_path()
    delta_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "poll_ts": poll_ts,
        "added": added,
        "removed": removed,
    }
    with delta_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    if added:
        log.info("Discovery delta — added %d: %s", len(added), added)
    if removed:
        log.info("Discovery delta — removed %d: %s", len(removed), removed)


# ---------------------------------------------------------------------------
# Duplicate-player detection
# ---------------------------------------------------------------------------


def _check_duplicate_players(
    new_meta: TennisEventMeta,
    known_metas: dict[str, TennisEventMeta],
) -> bool:
    """
    Returns True if player_a or player_b from new_meta already appears in a
    known event on the same calendar day (event_date).
    """
    if not new_meta.event_date:
        return False
    for existing in known_metas.values():
        if existing.event_id == new_meta.event_id:
            continue
        if existing.event_date != new_meta.event_date:
            continue
        existing_players = {existing.player_a_name, existing.player_b_name}
        new_players = {new_meta.player_a_name, new_meta.player_b_name}
        if existing_players & new_players:
            return True
    return False


# ---------------------------------------------------------------------------
# Gateway client
# ---------------------------------------------------------------------------


class GatewayClient:
    """
    Thin async wrapper around the Polymarket US public gateway.
    No authentication required.
    Uses a single shared httpx.AsyncClient with a conservative timeout and
    a User-Agent that identifies the project.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=GATEWAY_BASE,
            timeout=httpx.Timeout(20.0, connect=10.0),
            headers={
                "User-Agent": "pm-tennis-discovery/phase2 (+https://github.com/peterlitton/pm-tennis)",
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get_all_sports(self) -> list[dict]:
        """GET /v2/sports — returns list of sport objects with name/slug/leagues."""
        resp = await self._client.get("/v2/sports")
        resp.raise_for_status()
        data = resp.json()
        return data.get("sports") or data if isinstance(data, list) else []

    async def get_events_by_sport(
        self,
        slug: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        GET /v2/sports/{slug}/events
        Returns events list. Paginates if offset > 0.
        The endpoint wraps results in {"events": [...], "sport": {...}}.
        """
        resp = await self._client.get(
            f"/v2/sports/{slug}/events",
            params={"limit": limit, "offset": offset},
        )
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events") or []
        return events

    async def get_all_tennis_events(self, slug: str) -> list[dict]:
        """
        Paginate through all events for the given sport slug.
        Stops when a page returns fewer results than the page limit.
        """
        all_events: list[dict] = []
        limit = 100
        offset = 0
        while True:
            page = await self.get_events_by_sport(slug, limit=limit, offset=offset)
            all_events.extend(page)
            if len(page) < limit:
                break
            offset += limit
        return all_events


# ---------------------------------------------------------------------------
# Startup verification
# ---------------------------------------------------------------------------


async def verify_sport_slug(client: GatewayClient, slug: str) -> bool:
    """
    Calls GET /v2/sports, logs all available sports, and returns True if
    the configured slug is present in the response. Hard-stops the process
    on network failure; returns False (non-fatal) if slug not found so the
    caller can decide.
    """
    log.info("Startup: verifying sport slug %r against gateway /v2/sports …", slug)
    try:
        sports = await client.get_all_sports()
    except Exception as exc:
        log.critical(
            "STARTUP FAILURE: could not reach gateway /v2/sports — %s", exc
        )
        raise SystemExit(1) from exc

    if not sports:
        log.critical("STARTUP FAILURE: /v2/sports returned empty list")
        raise SystemExit(1)

    available_slugs: list[str] = []
    matched = False
    for sport in sports:
        s = sport.get("slug", "")
        n = sport.get("name", "")
        leagues = [lg.get("slug", "") for lg in (sport.get("leagues") or [])]
        available_slugs.append(s)
        if s == slug:
            matched = True
            log.info(
                "  ✓ MATCH — sport slug=%r name=%r leagues=%s",
                s, n, leagues,
            )
        else:
            log.info("    sport slug=%r name=%r leagues=%s", s, n, leagues)

    if matched:
        log.info("Sport slug %r verified. Proceeding to poll loop.", slug)
    else:
        log.error(
            "Sport slug %r NOT found in gateway response. "
            "Available slugs: %s. "
            "Set PMTENNIS_SPORT_SLUG env var to override the default.",
            slug,
            available_slugs,
        )
    return matched


# ---------------------------------------------------------------------------
# Discovery loop
# ---------------------------------------------------------------------------


class DiscoveryLoop:
    """
    Runs the poll loop: fetches all tennis events from the Polymarket US
    gateway on a fixed interval, emits meta.json for new matches, and
    maintains the discovery delta stream.
    """

    def __init__(self, client: GatewayClient, slug: str) -> None:
        self._client = client
        self._slug = slug
        # event_id -> TennisEventMeta for all currently-known active events
        self._active: dict[str, TennisEventMeta] = {}

    async def run_once(self) -> None:
        """Execute one poll cycle."""
        poll_ts = datetime.now(timezone.utc).isoformat()
        log.debug("Poll start: %s", poll_ts)

        try:
            raw_events = await self._client.get_all_tennis_events(self._slug)
        except httpx.HTTPStatusError as exc:
            log.error("Gateway HTTP error during poll: %s", exc)
            return
        except Exception as exc:
            log.error("Gateway unreachable during poll: %s", exc)
            return

        # Write raw snapshot for archival
        _write_event_snapshot(raw_events, poll_ts)

        # Filter to events that are active and not yet ended.
        # We capture events that are scheduled (pre-match) or live (in-play).
        # Ended/closed events are removed from the active set.
        newly_seen: dict[str, TennisEventMeta] = {}

        for raw in raw_events:
            meta = _parse_event(raw)
            if meta is None:
                continue

            # Skip events that have already ended or closed.
            # We still write their last snapshot line above for archival.
            if meta.ended_at_discovery or not meta.active_at_discovery:
                continue

            # Duplicate-player detection (flag, do not exclude)
            meta.duplicate_player_flag = _check_duplicate_players(
                meta, {**self._active, **newly_seen}
            )
            if meta.duplicate_player_flag:
                log.warning(
                    "Duplicate player flag set for event_id=%s title=%r",
                    meta.event_id, meta.title,
                )

            if meta.doubles_flag:
                log.info(
                    "Doubles flag set for event_id=%s title=%r — captured but out of scope",
                    meta.event_id, meta.title,
                )

            newly_seen[meta.event_id] = meta

        # Compute delta
        prev_ids = set(self._active.keys())
        curr_ids = set(newly_seen.keys())
        added_ids = sorted(curr_ids - prev_ids)
        removed_ids = sorted(prev_ids - curr_ids)

        # Write meta.json for newly discovered events
        for eid in added_ids:
            _write_meta(newly_seen[eid])

        # Emit delta
        _write_delta(added_ids, removed_ids, poll_ts)

        # Update active set
        self._active = newly_seen

        log.info(
            "Poll complete: %s — active=%d added=%d removed=%d total_raw=%d",
            poll_ts, len(self._active), len(added_ids), len(removed_ids), len(raw_events),
        )

    async def run_forever(self) -> None:
        """Poll loop: run_once(), sleep, repeat."""
        log.info(
            "Discovery loop starting: slug=%r interval=%ds",
            self._slug, POLL_INTERVAL_SECONDS,
        )
        while True:
            await self.run_once()
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


async def main() -> None:
    slug = TENNIS_SPORT_SLUG
    client = GatewayClient()
    try:
        slug_ok = await verify_sport_slug(client, slug)
        if not slug_ok:
            # Non-fatal: warn loudly but continue. The poll will produce an
            # empty result set and log errors, which the operator can see in
            # the Render log viewer. This avoids a hard crash if Polymarket US
            # ever renames the sport slug without changing the env var.
            log.warning(
                "Proceeding despite unverified slug. Polls will likely return "
                "empty results. Set PMTENNIS_SPORT_SLUG to correct slug and redeploy."
            )
        loop = DiscoveryLoop(client, slug)
        await loop.run_forever()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
