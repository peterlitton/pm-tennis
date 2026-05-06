"""API-Tennis WebSocket worker.

Connects to wss://wss.api-tennis.com/live with ?APIkey=... query auth.
Server pushes JSON-list messages of match-state items; no subscribe
protocol. Each item gets parsed and its event_key becomes the state
dict key.

Ported from latency-validation (code/capture/api_tennis_ws.py). Differences:
  - Writes into in-memory `state.matches` instead of JSONL to disk
  - No cross_feed routing (Phase 1A doesn't need Polymarket joins yet)
  - Field extraction is defensive — first real run will reveal the
    exact schema of unfamiliar fields, log warnings on first miss only

Connection model:
  - Single WebSocket. URL carries ?APIkey=...&timezone=UTC
  - No subscribe message. Server pushes whatever the account sees.
  - Messages: JSON list of dicts. ~24 fields per item, ~0.18 msg/s
    overall, ~1 update per match per minute.
  - Reconnect on transport errors with exponential backoff.

For demo-mode (no API key set), seeds state.matches with the v11 mockup
matches so the dashboard renders something visible. Demo mode is
explicitly opt-in via DEMO_MODE=1 env var. With API key set and
DEMO_MODE unset, the worker connects for real.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

import httpx

try:
    from websockets.asyncio.client import connect as ws_connect
except ImportError:  # older websockets layouts
    try:
        from websockets.client import connect as ws_connect  # type: ignore[no-redef]
    except ImportError:
        import websockets
        ws_connect = websockets.connect  # type: ignore[assignment]

from . import state
from . import country_codes
from . import momentum
from . import player_metadata
from . import sackmann
from . import tournament_surface
from .state import Match, Player, SetScore

log = logging.getLogger("api_tennis_worker")

# --- Config --------------------------------------------------------------

API_TENNIS_KEY: str = os.environ.get("API_TENNIS_KEY", "")
API_TENNIS_WS_BASE: str = os.environ.get(
    "API_TENNIS_WS_BASE", "wss://wss.api-tennis.com/live"
)
API_TENNIS_TIMEZONE: str = os.environ.get("API_TENNIS_TIMEZONE", "UTC")
DEMO_MODE: bool = os.environ.get("DEMO_MODE") == "1"

WS_RECONNECT_INITIAL_SECONDS: float = 1.0
WS_RECONNECT_MAX_SECONDS: float = 60.0
WS_RECONNECT_FACTOR: float = 2.0

# Statuses considered "live" for our purposes. Mirrors latency-validation
# guidance: do not trust event_live ("1" string even after match ends);
# trust event_status.
_FINISHED_STATUSES = {"Finished", "Retired", "Cancelled", "Walkover"}
_LIVE_INTERRUPTION_STATUSES = {
    "Medical Timeout",
    "Suspended",
    "Interrupted",
    "Toilet Break",
    "Time Violation",
}

# Track which schema fields we've already warned about, so logs don't
# explode on every message when a field is consistently missing.
_warned_missing: set[str] = set()

# One-shot raw-item logger. The first dict that reaches _apply_item gets
# logged in full at INFO level, so the operator has at least one
# guaranteed full-schema sample in Render logs without hunting through
# warning lines. Subsequent items are not logged.
_raw_sample_logged: bool = False


# --- Demo seeding --------------------------------------------------------

def _seed_demo_state() -> None:
    """Populate state.matches with the v11 mockup matches. Used only when
    DEMO_MODE=1 and an API key is not present.

    Step 4: demo seed momentum values cover all three states for visual
    validation of pill rendering:
      demo-1 (Carabelli/Cobolli): leader state — clear leader (12 vs 9, |diff|=3)
      demo-2 (Tien/Vallejo): contested state — both above floor, close (5 vs 4)
      demo-3 (Baptiste/Paolini): leader state — strong leader
      demo-4 (Guerrieri/Jianu): "none" state — both below noise floor
      demo-5 (Alcaraz/Korda): upcoming, momentum None
    """
    demo = [
        Match(
            event_key="demo-1",
            tour="ATP", venue="Munich", round="R16",
            status="live", set_label="2nd set",
            p1=Player(name="Camilo Ugo Carabelli", country_iso3="ARG"),
            p2=Player(name="Flavio Cobolli", country_iso3="ITA"),
            p1_sets=[SetScore(games=7, tiebreak=9), SetScore(games=1)],
            p2_sets=[SetScore(games=6, tiebreak=7), SetScore(games=4)],
            p1_game="30", p2_game="40", server=2,
            p1_price_cents=31, p2_price_cents=70,
            p1_momentum=12, p2_momentum=9,
            # Step 5.1: ranks reflect fresh 2026-04-20 snapshot
            surface="Clay",
            p1_rank=57, p2_rank=13,
        ),
        Match(
            event_key="demo-2",
            tour="ATP", venue="Madrid", round="R32",
            status="live", set_label="2nd set",
            p1=Player(name="Learner Tien", country_iso3="USA"),
            p2=Player(name="Adolfo Vallejo", country_iso3="PAR"),
            p1_sets=[SetScore(games=4), SetScore(games=2)],
            p2_sets=[SetScore(games=6), SetScore(games=1)],
            p1_game="40", p2_game="40", server=1,
            p1_price_cents=24, p2_price_cents=77,
            p1_momentum=5, p2_momentum=4,
            surface="Clay",
            p1_rank=21, p2_rank=96,
        ),
        Match(
            event_key="demo-3",
            tour="WTA", venue="Madrid", round="R32",
            status="live", set_label="2nd set",
            p1=Player(name="Hailey Baptiste", country_iso3="USA"),
            p2=Player(name="Jasmine Paolini", country_iso3="ITA"),
            p1_sets=[SetScore(games=7), SetScore(games=1)],
            p2_sets=[SetScore(games=5), SetScore(games=1)],
            p1_game="15", p2_game="40", server=2,
            p1_price_cents=66, p2_price_cents=35,
            p1_momentum=8, p2_momentum=5,
            surface="Clay",
            p1_rank=32, p2_rank=9,
        ),
        Match(
            event_key="demo-4",
            tour="Ch.", venue="Rome", round="QF",
            status="live", set_label="2nd set",
            p1=Player(name="Andrea Guerrieri", country_iso3="ITA"),
            p2=Player(name="Filip Jianu", country_iso3="ROU"),
            p1_sets=[SetScore(games=6), SetScore(games=3)],
            p2_sets=[SetScore(games=6), SetScore(games=2)],
            p1_game="15", p2_game="0", server=1,
            p1_price_cents=94, p2_price_cents=6,
            p1_momentum=2, p2_momentum=1,
            # Challengers: no Sackmann ranks expected, leave None
            # Step 5.1: this case now exercises the "—" placeholder for layout stability
        ),
        Match(
            event_key="demo-5",
            tour="ATP", venue="Madrid", round="R16",
            status="upcoming",
            start_time="2026-04-25T16:45:00Z",
            p1=Player(name="Carlos Alcaraz", country_iso3="ESP"),
            p2=Player(name="Sebastian Korda", country_iso3="USA"),
            p1_price_cents=72, p2_price_cents=28,
            # Step 5: Alcaraz fair-value 85% (clay) vs price 72¢ → +13 edge (medium)
            # Step 5.1: ranks reflect fresh 2026-04-20 snapshot — Alcaraz #2 (was #3),
            # Korda #40 (was #22; fell substantially)
            surface="Clay",
            p1_pre_pct=85, p2_pre_pct=15,
            p1_rank=2, p2_rank=40,
        ),
    ]
    for m in demo:
        state.matches[m.event_key] = m


# --- Field extraction (defensive) ----------------------------------------

def _warn_once(field: str, item_keys: list[str]) -> None:
    if field in _warned_missing:
        return
    _warned_missing.add(field)
    log.warning(
        "API-Tennis schema: field %r not found on incoming item; "
        "available keys=%s. Update extractor if needed.",
        field, sorted(item_keys),
    )


def _str_or_none(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _int_or_none(v: Any) -> Optional[int]:
    if v is None or v == "":
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _classify_tour(item: dict) -> Optional[str]:
    """Map API-Tennis event_type into ATP/WTA/Ch., or None.

    Returns None for:
      - Doubles events (any event_type containing "doubles")
      - Mixed/unknown formats we don't render

    None is the signal to the caller (`_apply_item`) to skip the match
    entirely. No row is rendered, the match doesn't occupy space in the
    dashboard. Doubles events are excluded specifically because:
      1. Polymarket doesn't list doubles moneyline markets, confirmed
         empirically in Step 3.2-fix live test, so prices column is
         always blank for them
      2. Without prices, doubles rows add visual noise without trading
         signal
      3. Earlier behavior — defaulting unknown types to "ATP" — caused
         doubles to render as fake ATP singles rows. Step 3.3 fix.

    Singles classifications come from event_type_key (probe data) or
    event_type_type string. Both are checked; either one definitively
    classifies the match as singles.
    """
    type_str = (_str_or_none(item.get("event_type_type")) or "").lower()
    type_key = _int_or_none(item.get("event_type_key"))

    # Step 3.3: hard reject doubles. event_type_type strings observed:
    # "Atp Doubles", "Wta Doubles", "Mixed Doubles", "Challenger Men Doubles",
    # "Challenger Women Doubles". Substring "doubles" catches all.
    if "doubles" in type_str:
        return None

    # Singles by event_type_key (probe-confirmed values).
    if type_key == 265:
        return "ATP"
    if type_key == 266:
        return "WTA"
    if type_key in (281, 272):
        return "Ch."

    # Singles by event_type_type string. "atp singles", "wta singles",
    # "challenger men singles", "itf women singles", etc.
    if "challenger" in type_str:
        return "Ch."
    if "wta" in type_str or ("women" in type_str and "singles" in type_str):
        return "WTA"
    if "atp" in type_str or ("men" in type_str and "singles" in type_str):
        return "ATP"

    # Tournament-name keyword fallback — only confidently classifies
    # Challengers, since "Madrid" is ambiguous between ATP and WTA.
    tn = (_str_or_none(item.get("tournament_name")) or "").lower()
    if "challenger" in tn:
        return "Ch."

    # Truly unknown — return None so caller skips. This is the
    # behavior change from earlier versions, which defaulted to
    # "ATP" and caused doubles + ITF + exhibitions to render as
    # fake ATP rows.
    return None


def _venue_from_tournament(item: dict) -> str:
    """tournament_name in probe data is bare city names like "Madrid".
    Fall back to "Tour" if missing."""
    return _str_or_none(item.get("tournament_name")) or "Tour"


def _round_label(item: dict) -> str:
    """Round label. Real field name is unknown until first run; try a
    few common candidates and fall back to empty string."""
    for key in ("tournament_round", "event_round", "round"):
        v = _str_or_none(item.get(key))
        if v:
            return v
    if "tournament_round" not in item and "event_round" not in item and "round" not in item:
        _warn_once("round", list(item.keys()))
    return ""


def _player(item: dict, side: int) -> Player:
    """Build a Player. Names are 'M. Surname' format on API-Tennis;
    we render them as-is.

    Country code field name is `event_first_player_country_key` /
    `event_second_player_country_key` per Design Notes §6. API-Tennis
    returns alpha-2 in some cases, alpha-3 in others. We normalize to
    alpha-3 uppercase via country_codes.to_alpha3 so state.matches
    always carries the form Polymarket's flag CDN expects.

    Unknown alpha-2 codes (not in the tennis-nations table) pass
    through uppercased so the dashboard keeps rendering, and we
    warn-once with the unrecognized code so the operator can add it
    to country_codes.ALPHA2_TO_ALPHA3.

    2026-05-03 — Step A of player database build: extract player_key
    (`first_player_key` / `second_player_key`) from API-Tennis payload.
    Numeric ID present on every WS frame and every fixtures REST item.
    Becomes the canonical join key once Step F migrates cross-feed
    away from name-token matching. Until then, harmless metadata.
    """
    name_field = "event_first_player" if side == 1 else "event_second_player"
    country_field = (
        f"event_{'first' if side == 1 else 'second'}_player_country_key"
    )
    key_field = "first_player_key" if side == 1 else "second_player_key"
    name = _str_or_none(item.get(name_field)) or ""
    raw_country = _str_or_none(item.get(country_field))
    country = country_codes.to_alpha3(raw_country)
    player_key = _int_or_none(item.get(key_field))

    # Fallback: if API-Tennis didn't supply a country (rare; some
    # payloads omit it), try the player_metadata table by player_key.
    # Step E of player database build. Doesn't override existing
    # country values from API-Tennis — only fills the gap.
    if country is None and player_key is not None:
        meta = player_metadata.lookup_by_key(player_key)
        if meta:
            country = meta.get("country_iso3")
    # Warn once if we got a 2-char input that wasn't in the table —
    # the value passes through but we want it in logs so the table
    # gets updated. 3-char inputs are trusted as already-alpha-3.
    if (
        raw_country
        and len(raw_country.strip()) == 2
        and country
        and country == raw_country.strip().upper()
        and not country_codes.is_known_alpha3(country)
    ):
        _warn_once(f"unknown_country_alpha2:{country}", [country_field])
    return Player(name=name, country_iso3=country, player_key=player_key)


def _parse_decimal_score(value: Any) -> tuple[Optional[int], Optional[int]]:
    """Parse a `score_first` / `score_second` value into (games, tiebreak).

    EMPIRICAL FINDING (Step 3.4, validated against live WSS frame on
    2026-04-26 14:25 UTC): API-Tennis encodes set games + tiebreak
    points as a decimal-compound string when a set went to tiebreak.
    The integer part is set games (always 7), the fractional digits are
    the loser's tiebreak point count.

    Examples observed:
      "7.7" → games=7, tiebreak=7   (winner of a 7-6 set with the
                                      loser scoring 7 in the breaker;
                                      so the tiebreak went 9-7 or
                                      similar — the field encodes
                                      ONE side's score)
      "6.2" → games=6, tiebreak=2
      "6"   → games=6, tiebreak=None
      "6.0" → games=6, tiebreak=0   (defensive: tiebreak field exists
                                      but loser scored zero — possible
                                      in a 7-0 tiebreak)

    Note: the previous parser (Step 2.6) used `_int_or_none` which
    fails on "7.7" and silently dropped the entire set from state.
    Symptom on dashboard: completed sets with tiebreaks disappeared,
    set count looked off by one, set_label was wrong.

    Returns (None, None) on unparseable input — matches the
    previous "skip this set" behavior gracefully.
    """
    if value is None:
        return None, None
    s = str(value).strip()
    if not s:
        return None, None
    if "." in s:
        # Compound — split games.tiebreak.
        try:
            games_str, tb_str = s.split(".", 1)
            games = int(games_str)
            # Tiebreak digit string can be empty (defensive: "7." would
            # split to ["7", ""]) — treat as no-tiebreak.
            tiebreak: Optional[int] = int(tb_str) if tb_str else None
            return games, tiebreak
        except (ValueError, AttributeError):
            return None, None
    # Whole number — just games.
    try:
        return int(s), None
    except ValueError:
        return None, None


def _parse_set_scores(item: dict) -> tuple[list[SetScore], list[SetScore]]:
    """Extract per-set games and tiebreaks.

    EMPIRICAL FINDING (Step 2.6, validated against live WSS frame on
    2026-04-26): `event_final_result` is the SET COUNT for in-progress
    matches, not a games-per-set string. A live match showing
    "event_final_result": "1 - 0" means "player 1 has won 1 set, player
    2 has won 0 sets" — NOT "1 game vs 0 games in current set." Step
    2.2's earlier guess (treating it as "6-4, 3-2" format) was wrong
    for live matches. It may still hold for finished matches in some
    contexts, but we no longer trust it as the primary source.

    Source of truth is the `scores` list: each entry is one set's
    games-by-player, with the LAST entry being the in-progress current
    set (if any). Format observed on live frames:
        [{"score_first":"6","score_second":"3","score_set":"1"},
         {"score_first":"4","score_second":"2","score_set":"2"}]

    EMPIRICAL FINDING (Step 3.4): tiebreaks are encoded inline as
    decimal-compound strings: `score_first: "7.7"` means
    games=7, tiebreak=7. NOT a separate `score_first_tb` field as
    Step 2.6 guessed. The defensive `score_first_tb` lookup is
    retained for forward compatibility but the primary parse is
    via _parse_decimal_score.

    Returns ([], []) for matches with no scores array — typically
    matches that haven't started yet.
    """
    p1_sets: list[SetScore] = []
    p2_sets: list[SetScore] = []

    # Primary source: scores list. This is what we read for live and
    # post-completion alike.
    scores = item.get("scores")
    if isinstance(scores, list):
        for s in scores:
            if not isinstance(s, dict):
                continue
            f_games, f_tb = _parse_decimal_score(s.get("score_first"))
            sec_games, sec_tb = _parse_decimal_score(s.get("score_second"))
            if f_games is None or sec_games is None:
                continue
            # Defensive: also look for separate _tb fields in case a
            # future schema variant uses them.
            if f_tb is None:
                f_tb = _int_or_none(s.get("score_first_tb"))
            if sec_tb is None:
                sec_tb = _int_or_none(s.get("score_second_tb"))
            p1_sets.append(SetScore(games=f_games, tiebreak=f_tb))
            p2_sets.append(SetScore(games=sec_games, tiebreak=sec_tb))
        return p1_sets, p2_sets

    # No `scores` array. Empty result is the right answer here.
    # `event_final_result` is set-count not games-per-set, so we
    # cannot reconstruct per-set games from it. Warn once if we
    # genuinely have no source so the operator sees it.
    if "scores" not in item and "event_final_result" not in item:
        _warn_once("scores|event_final_result", list(item.keys()))
    return p1_sets, p2_sets


def _parse_current_game(item: dict) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """Extract current game point score (0/15/30/40/AD) and current server.

    Empirical from latency-validation normalize.py:
      - event_game_result: string like "30 - 40" (NOT a dict)
      - event_serve: string "First Player" / "Second Player" / None

    Defensive fallbacks retained for the rare case the schema diverges.
    """
    p1_game: Optional[str] = None
    p2_game: Optional[str] = None
    server: Optional[int] = None

    # Game points: empirical string format "p1 - p2"
    game_result = _str_or_none(item.get("event_game_result"))
    if game_result and "-" in game_result:
        try:
            left, right = game_result.split("-", 1)
            p1_game = left.strip() or None
            p2_game = right.strip() or None
        except ValueError:
            pass

    # Defensive fallback: dict-shaped variants from other API-Tennis tiers.
    if p1_game is None and p2_game is None:
        for key in ("event_game_result", "current_game"):
            v = item.get(key)
            if isinstance(v, dict):
                p1_game = _str_or_none(v.get("first")) or _str_or_none(v.get("score_first"))
                p2_game = _str_or_none(v.get("second")) or _str_or_none(v.get("score_second"))
                if p1_game or p2_game:
                    break

    # Server: empirical "First Player" / "Second Player" string.
    serve = _str_or_none(item.get("event_serve"))
    if serve == "First Player":
        server = 1
    elif serve == "Second Player":
        server = 2
    else:
        # Defensive fallback for int-coded variants.
        for key in ("event_server", "first_to_serve", "current_server"):
            v = item.get(key)
            s = _int_or_none(v)
            if s in (1, 2):
                server = s
                break

    return p1_game, p2_game, server


def _set_label(item: dict, p1_sets: list[SetScore], p2_sets: list[SetScore]) -> Optional[str]:
    """Human label like '2nd set'. Inferred from the count of sets seen,
    not from a dedicated field — keeps us robust to schema variants."""
    n = max(len(p1_sets), len(p2_sets))
    if n == 0:
        return None
    return {1: "1st set", 2: "2nd set", 3: "3rd set", 4: "4th set", 5: "5th set"}.get(n, f"set {n}")


def _classify_status(item: dict) -> str:
    """live | upcoming | finished. Use event_status authoritatively.

    Empirical values observed (latency-validation + Step 2.6 live test):
      - "Set 1", "Set 2", ... → live (in-progress sets)
      - "Finished", "Retired", "Cancelled", "Walkover" → finished
      - "Medical Timeout", "Suspended", "Interrupted", "Toilet Break",
        "Time Violation" → live (mid-match interruptions; match is
        paused but technically still in progress)

    Pre-match status values are not in our corpus because both
    upstream workers filtered them at discovery. Anything not matching
    a known pattern gets warn-once'd and treated as upcoming so the
    operator sees what API-Tennis actually sends.

    Empty event_status → upcoming (best guess for not-yet-started).
    """
    status = _str_or_none(item.get("event_status")) or ""
    if not status:
        return "upcoming"
    if status in _FINISHED_STATUSES:
        return "finished"
    if status.startswith("Set "):
        return "live"
    if status in _LIVE_INTERRUPTION_STATUSES:
        return "live"
    # Unknown non-empty status. Warn once with the value so we know what
    # to add to the classifier next session.
    _warn_once(f"event_status:{status}", list(item.keys()))
    return "upcoming"


def _start_time(item: dict) -> Optional[str]:
    """ISO start time for upcoming matches. Combine event_date +
    event_time if present."""
    d = _str_or_none(item.get("event_date"))
    t = _str_or_none(item.get("event_time"))
    if d and t:
        return f"{d}T{t}:00Z"
    return None


def _upcoming_within_window(start_iso: Optional[str], hours: int = 24) -> bool:
    """Return True if start_iso is within the next `hours` hours OR in
    the past (delayed match).

    The header copy says "starting within 1h" — this enforces it.

    DELAYED MATCH HANDLING (Step 3.5 clarification): a match scheduled
    for 2pm that hasn't started by 3pm is delayed, NOT cancelled. The
    operator may want to know about delayed matches as part of evaluating
    the day's slate. So the predicate accepts:
      - Future start times within the next `hours` hours (starting soon)
      - Past start times (delayed; hasn't yet flipped to "live" or
        "finished" status from API-Tennis)
    What gets filtered out: matches scheduled MORE than `hours` hours
    in the future (tomorrow's slate, late tonight's matches).

    Implementation note: `dt <= now + timedelta(hours=hours)` is
    inclusive of past `dt` because there's no lower bound. This is
    intentional. Don't add `dt >= now` thinking it's "obviously a bug
    that past times pass" — that would break delayed-match display.

    Garbage input returns False (better to drop a malformed time than
    render it). A missing start_time (returns None from _start_time
    when event_date or event_time is absent) also returns False —
    treated as too-far-out so we don't pollute the upcoming list with
    matches whose timing we can't even confirm.

    2026-05-02: default expanded 1h → 24h to support fixtures-driven
    upcoming-match rendering. Operator wants today's full slate visible,
    sorted by start_time. Live matches still take priority via existing
    sort behavior on the frontend.
    """
    if not isinstance(start_iso, str) or not start_iso:
        return False
    from datetime import datetime, timezone, timedelta
    try:
        # Tolerate "Z" suffix and timezone-less ISO; treat as UTC.
        s = start_iso.rstrip("Z")
        dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
        return False
    now = datetime.now(timezone.utc)
    return dt <= now + timedelta(hours=hours)


def _recent_point_history(item: dict, max_games: int = 16) -> list[dict]:
    """Extract recent pointbypoint games (across set boundaries) for the
    momentum indicator.

    SPEC EVOLUTION:
    - Step 3.2: kept only current-set games. Indicator window was set-bounded.
    - Step 4: spec changed to rolling-last-12-points across set boundaries
      (per design/Dashboard_Indicators_Design.md). With current-set-only
      retention, a rolling-12 indicator can't reach into the previous set
      when the current set has fewer than 12 points played. So we now
      retain the last `max_games` games regardless of set boundary.

    Why games-based retention rather than flattened individual points:
      - Preserves API-Tennis data shape (worker doesn't reshape upstream data)
      - Keeps game/set structure available for any future indicator variant
        that wants per-game info (e.g., serve breaks weighted differently)
      - Momentum module flattens points internally — knows what unit it
        wants, doesn't depend on retention choice

    Why max_games=16:
      - Tennis games average 4-7 points each; even hold-rich service
        stretches give us 16 × 4 = 64 points minimum, comfortably above
        the rolling 12-point window
      - Bounded payload size (~15-25KB per match including game metadata)
      - Headroom for any future variant that wants more than 12 points

    Tiebreak handling: API-Tennis emits tiebreak entries with
    `set_number: "Set 1 TieBreak"` (separate from "Set 1"). These are
    games for retention purposes — each tiebreak point IS a "game" in
    the data, and they accumulate into the rolling window naturally.

    Returns [] for items without a pointbypoint array (upcoming matches,
    items where the field is absent or not a list). Empty list reads
    naturally as "no momentum data yet" by the indicator's noise-floor
    suppression rule.
    """
    pbp = item.get("pointbypoint")
    if not isinstance(pbp, list) or not pbp:
        return []
    # Filter to dict entries only (defensive against malformed data),
    # then take the trailing max_games. API-Tennis emits chronologically-
    # ordered entries, so the tail is the most recent.
    valid = [entry for entry in pbp if isinstance(entry, dict)]
    return valid[-max_games:]


# --- Main parse ----------------------------------------------------------

def _apply_item(item: dict[str, Any]) -> None:
    """Translate one API-Tennis match-state dict into a Match in
    state.matches. Match key is the API-Tennis event_key.

    MUTATION-IN-PLACE (Step 3.5): when an existing Match exists for
    this event_key, update its fields rather than constructing a new
    object. This enforces "distinct field ownership" through structure:
    api_tennis_worker writes only to the score/serve/sets/point_history
    fields it owns; polymarket_worker writes only to the price fields
    it owns; neither tramples the other's writes. Previous behavior
    (full-object replacement) caused visible cents flicker on the
    dashboard — every WS frame would reset p1_price_cents and
    p2_price_cents to None until the next 2-second resolver pass
    re-wrote them. The architectural decision in Step 3.2 specified
    distinct field ownership; the implementation now matches that
    decision.

    Fields the api_tennis_worker writes (and only these):
      tour, venue, round, status, set_label, start_time,
      p1, p2, p1_sets, p2_sets, p1_game, p2_game, server,
      point_history, p1_momentum, p2_momentum,
      surface, p1_pre_pct, p2_pre_pct, p1_rank, p2_rank.

    Fields the polymarket_worker writes (and only these):
      p1_price_cents, p2_price_cents.
    """
    global _raw_sample_logged
    if not _raw_sample_logged:
        _raw_sample_logged = True
        log.info("API-Tennis raw item sample (one-shot): %s", json.dumps(item, default=str))

    event_key = _int_or_none(item.get("event_key"))
    if event_key is None:
        # Without an event_key we can't address the match. Skip with a
        # warn-once; this should never happen on real data.
        _warn_once("event_key", list(item.keys()))
        return

    p1_sets, p2_sets = _parse_set_scores(item)
    p1_game, p2_game, server = _parse_current_game(item)
    status = _classify_status(item)
    point_history = _recent_point_history(item)
    p1_momentum, p2_momentum = momentum.compute_momentum(point_history)
    momentum_trend = momentum.compute_trend(point_history)
    tour = _classify_tour(item)

    # Step 5 — Sackmann-derived pre-match data.
    # Computed from player names + tournament surface. All values are None
    # if Sackmann data lookup fails (player not in 2024-end snapshot, surface
    # unknown). Per working-log staleness note: 2025-breakthrough players
    # may not appear at all → pre_pct returns None for those matchups.
    p1_player = _player(item, 1)
    p2_player = _player(item, 2)
    surface = tournament_surface.classify_surface(item.get("tournament_name"))
    p1_pre_pct: Optional[int] = None
    p2_pre_pct: Optional[int] = None
    p1_rank: Optional[int] = None
    p2_rank: Optional[int] = None
    if tour in ("ATP", "WTA"):
        sackmann_tour = tour.lower()
        # Step 4.2 (frontend addition): resolve canonical full names.
        # API-Tennis sometimes emits abbreviated names ("C. Norrie");
        # we want Polymarket-style display ("Cameron Norrie"). Sackmann's
        # CSVs carry the canonical full names. Falls back to whatever
        # API-Tennis provided if Sackmann doesn't have the player.
        canon_p1 = sackmann.canonical_name(p1_player.name, sackmann_tour)
        canon_p2 = sackmann.canonical_name(p2_player.name, sackmann_tour)
        if canon_p1:
            p1_player = Player(name=canon_p1, country_iso3=p1_player.country_iso3, player_key=p1_player.player_key)
        if canon_p2:
            p2_player = Player(name=canon_p2, country_iso3=p2_player.country_iso3, player_key=p2_player.player_key)
        prob = sackmann.match_probability(p1_player.name, p2_player.name, sackmann_tour, surface)
        if prob is not None:
            p1_pre_pct = int(round(prob[0]))
            p2_pre_pct = int(round(prob[1]))
        p1_rank = sackmann.lookup_ranking(p1_player.name, sackmann_tour)
        p2_rank = sackmann.lookup_ranking(p2_player.name, sackmann_tour)
    # Note: Challengers ("Ch.") not in Sackmann's tour-level ranking data
    # by design — leave all Step 5 fields as None for those, including
    # canonical-name resolution. The API-provided "M. Surname" form
    # passes through for Challengers.

    if status == "finished":
        # Drop finished matches from the dashboard. If they reappear
        # on a future message, they get re-added; but generally they
        # stop being pushed.
        state.matches.pop(str(event_key), None)
        return

    # Step 3.3: skip matches with no classifiable tour. None means
    # doubles, mixed, or genuinely unknown event types we don't render.
    # Drop from state if we had it before (e.g. from an earlier frame
    # before the doubles classifier was strict) so a row doesn't get
    # stuck.
    if tour is None:
        state.matches.pop(str(event_key), None)
        return

    # Step 3.3: upcoming window — only keep upcoming matches starting
    # within the next hour OR delayed (past start_time, hasn't yet
    # flipped to live status). See _upcoming_within_window docstring
    # for the rationale on accepting past start_times.
    if status == "upcoming":
        start = _start_time(item)
        if not _upcoming_within_window(start, hours=1):
            state.matches.pop(str(event_key), None)
            return

    # Mutation-in-place: update existing Match fields, or construct
    # fresh on first sighting.
    ek_str = str(event_key)
    existing = state.matches.get(ek_str)
    new_set_label = _set_label(item, p1_sets, p2_sets) if status == "live" else None
    # v0.8.3: always set start_time, regardless of status. Operator
    # wants stable match ordering — sorted by scheduled start time
    # across BOTH live and upcoming matches so rows don't reshuffle
    # when a match transitions live -> upcoming or vice versa. The
    # field was previously upcoming-only and got nulled on live
    # transition, which caused live matches to appear in dict
    # insertion order at the top and reshuffle as new matches went
    # live. See state.snapshot() for the corresponding sort change.
    new_start_time = _start_time(item)

    if existing is None:
        # First sighting — construct fresh. Price fields default to
        # None per Match dataclass; polymarket_worker resolver will
        # fill them in within ~2s on its next pass if there's a market.
        state.matches[ek_str] = Match(
            event_key=ek_str,
            tour=tour,
            venue=_venue_from_tournament(item),
            round=_round_label(item),
            status=status,
            set_label=new_set_label,
            start_time=new_start_time,
            p1=p1_player,
            p2=p2_player,
            p1_sets=p1_sets,
            p2_sets=p2_sets,
            p1_game=p1_game,
            p2_game=p2_game,
            server=server,
            point_history=point_history,
            p1_momentum=p1_momentum,
            p2_momentum=p2_momentum,
            momentum_trend=momentum_trend,
            momentum_indicator_version=momentum.MI_VERSION,
            surface=surface,
            p1_pre_pct=p1_pre_pct,
            p2_pre_pct=p2_pre_pct,
            p1_rank=p1_rank,
            p2_rank=p2_rank,
        )
        return

    # Existing Match — mutate the api_tennis-owned fields. Price fields
    # (p1_price_cents, p2_price_cents) deliberately untouched — they
    # belong to polymarket_worker.
    existing.tour = tour
    existing.venue = _venue_from_tournament(item)
    existing.round = _round_label(item)
    existing.status = status
    existing.set_label = new_set_label
    existing.start_time = new_start_time
    existing.p1 = p1_player
    existing.p2 = p2_player
    existing.p1_sets = p1_sets
    existing.p2_sets = p2_sets
    existing.p1_game = p1_game
    existing.p2_game = p2_game
    existing.server = server
    existing.point_history = point_history
    existing.p1_momentum = p1_momentum
    existing.p2_momentum = p2_momentum
    existing.momentum_trend = momentum_trend
    existing.momentum_indicator_version = momentum.MI_VERSION
    existing.surface = surface
    existing.p1_pre_pct = p1_pre_pct
    existing.p2_pre_pct = p2_pre_pct
    existing.p1_rank = p1_rank
    existing.p2_rank = p2_rank


def _handle_message(raw: str | bytes) -> None:
    """Parse one WS frame and apply each contained item to state.matches.

    The frame-arrival timestamp is recorded for the api_tennis source
    before any parsing, so even malformed frames count as "the
    connection is alive" — that's the semantic the liveness counter
    measures, per Design Notes §8.
    """
    state.source_timestamps["api_tennis"] = int(time.time() * 1000)

    if isinstance(raw, (bytes, bytearray)):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError:
            log.warning("API-Tennis WS: non-UTF8 frame, skipping")
            return

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        log.warning("API-Tennis WS: non-JSON frame (%s), skipping", exc)
        return

    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict) and "event_key" in parsed:
        items = [parsed]
    elif isinstance(parsed, dict):
        log.warning("API-Tennis WS: dict without event_key (keys=%s), skipping",
                    sorted(parsed.keys())[:10])
        return
    else:
        log.warning("API-Tennis WS: unexpected payload type %s, skipping",
                    type(parsed).__name__)
        return

    for item in items:
        if isinstance(item, dict):
            try:
                _apply_item(item)
            except Exception:
                log.exception("API-Tennis WS: failed to apply item, skipping")


# --- Fixtures REST poll (2026-05-02) -------------------------------------

API_TENNIS_REST_BASE: str = os.environ.get(
    "API_TENNIS_REST_BASE", "https://api.api-tennis.com/tennis/"
)
FIXTURES_POLL_INTERVAL_SECONDS: float = float(
    os.environ.get("FIXTURES_POLL_INTERVAL_SECONDS", "300")
)


async def _fixtures_poll_once(client: httpx.AsyncClient) -> int:
    """Single fixtures REST fetch. Returns count of items applied.

    Pulls a 2-day window (today + tomorrow UTC) so the 24-hour upcoming
    filter has data to work with even when operator's local-time crosses
    UTC midnight. The _apply_item path will further filter to the
    24-hour window via _upcoming_within_window.

    Errors are logged but don't propagate — the poll loop continues
    on next interval. The WS stream is the authoritative live-match
    source; fixtures are supplementary upcoming-match data.
    """
    from datetime import datetime, timezone, timedelta
    today = datetime.now(timezone.utc).date()
    tomorrow = today + timedelta(days=1)
    params = {
        "method": "get_fixtures",
        "APIkey": API_TENNIS_KEY,
        "date_start": today.isoformat(),
        "date_stop": tomorrow.isoformat(),
    }
    try:
        resp = await client.get(API_TENNIS_REST_BASE, params=params, timeout=15.0)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("api_tennis_worker: fixtures fetch failed: %s", exc)
        return 0

    try:
        payload = resp.json()
    except ValueError as exc:
        log.warning("api_tennis_worker: fixtures bad JSON: %s", exc)
        return 0

    if not isinstance(payload, dict) or payload.get("success") != 1:
        log.warning(
            "api_tennis_worker: fixtures unexpected payload (success=%s)",
            payload.get("success") if isinstance(payload, dict) else "?",
        )
        return 0

    items = payload.get("result") or []
    if not isinstance(items, list):
        return 0

    applied = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            _apply_item(item)
            applied += 1
        except Exception:
            log.exception("api_tennis_worker: fixtures _apply_item failed, skipping")
    return applied


async def _fixtures_poll_loop() -> None:
    """Repeatedly fetch fixtures every FIXTURES_POLL_INTERVAL_SECONDS.

    Runs alongside the WS stream as a separate async task. WS handles
    live-match updates; fixtures handles the upcoming-match horizon.
    Same _apply_item path for both so there's no schema duplication.
    """
    log.info(
        "api_tennis_worker: fixtures poll starting (interval=%.0fs)",
        FIXTURES_POLL_INTERVAL_SECONDS,
    )
    async with httpx.AsyncClient() as client:
        # Initial fetch is immediate so the dashboard has upcoming matches
        # by the time the operator first opens it after a deploy.
        first = True
        while True:
            try:
                if not first:
                    await asyncio.sleep(FIXTURES_POLL_INTERVAL_SECONDS)
                first = False
                count = await _fixtures_poll_once(client)
                if count:
                    log.info("api_tennis_worker: fixtures applied %d items", count)
            except asyncio.CancelledError:
                log.info("api_tennis_worker: fixtures poll cancelled")
                raise
            except Exception:
                log.exception("api_tennis_worker: fixtures poll loop iteration failed")
                # Continue — don't let a single failure kill the loop.
                await asyncio.sleep(FIXTURES_POLL_INTERVAL_SECONDS)


# --- Worker entry point --------------------------------------------------

async def _run_once() -> None:
    """Single connect-receive cycle. Returns on connection close."""
    url = (
        f"{API_TENNIS_WS_BASE}"
        f"?APIkey={API_TENNIS_KEY}"
        f"&timezone={API_TENNIS_TIMEZONE}"
    )
    log.info("api_tennis_worker: opening WS")
    async with ws_connect(url, open_timeout=10, ping_interval=20) as ws:
        log.info("api_tennis_worker: connected, streaming events")
        async for raw in ws:
            _handle_message(raw)
    log.info("api_tennis_worker: WS closed by server, will reconnect")


async def _ws_supervisor() -> None:
    """WS connection supervisor with exponential backoff on transport errors.
    Extracted from run() so it can run concurrently with the fixtures poll."""
    backoff = WS_RECONNECT_INITIAL_SECONDS
    while True:
        try:
            await _run_once()
            # Clean close from the server. Reset backoff but still wait
            # the initial interval before reconnecting — prevents tight
            # loops if the server is in a state where it accepts then
            # immediately closes connections.
            backoff = WS_RECONNECT_INITIAL_SECONDS
            await asyncio.sleep(backoff)
        except asyncio.CancelledError:
            log.info("api_tennis_worker: WS supervisor cancelled, exiting")
            raise
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "api_tennis_worker: WS error (%s), reconnecting in %.1fs",
                exc, backoff,
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * WS_RECONNECT_FACTOR, WS_RECONNECT_MAX_SECONDS)


async def run() -> None:
    """Supervisor for both WS (live matches) and fixtures REST poll
    (upcoming matches). Each runs as an independent async task so failures
    in one don't kill the other. Returns only on CancelledError.

    2026-05-02: extended from WS-only to WS + fixtures REST. Fixtures poll
    hydrates upcoming matches into state.matches via the same _apply_item
    path the WS uses (schemas are identical between the two feeds).
    """
    if DEMO_MODE:
        _seed_demo_state()
        log.info("api_tennis_worker: DEMO_MODE=1, seeded %d demo matches", len(state.matches))
        # Simulate frame-arrival cadence so the liveness counter cycles
        # realistically (otherwise it sits at "—" forever in demo). Probe 2
        # measured ~0.18 msg/s overall on real API-Tennis; 5s between bumps
        # is a reasonable mid-range simulation.
        while True:
            state.source_timestamps["api_tennis"] = int(time.time() * 1000)
            await asyncio.sleep(5)

    if not API_TENNIS_KEY:
        log.error(
            "api_tennis_worker: API_TENNIS_KEY not set and DEMO_MODE not set; "
            "worker idle. Set one of them."
        )
        await asyncio.Future()  # idle forever

    # Run WS supervisor and fixtures poll concurrently. asyncio.gather
    # propagates exceptions and cancellation correctly. If one task crashes
    # uncleanly (which their internal try/except should prevent), the other
    # continues until cancelled by the outer task supervisor.
    await asyncio.gather(
        _ws_supervisor(),
        _fixtures_poll_loop(),
    )
