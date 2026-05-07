"""Polymarket Global CLOB price feed worker.

This worker is the v0.8.0 replacement for the price-feed paths in
``polymarket_worker.py``. It reads tennis match prices from Polymarket
Global's public CLOB WebSocket, where each match's two outcomes have
independent real-time order books (unlike Polymarket US's slug-level
single book, which is the root cause of the historical Player B lag).

Architecture
============

Three layers, decoupled, each running on its own asyncio task:

  Layer 1  Discovery (60s cadence)
    - Poll Polymarket US gateway REST for currently live tennis matches.
    - Resolve each US match to its Polymarket Global counterpart by
      looking up `gamma-api.polymarket.com/events?tag_slug=tennis`,
      then fuzzy-matching player names against Gamma `question`.
    - Extract `clobTokenIds[]` (two ERC1155 token IDs per match) and
      assign them to (token_a, token_b) by matching outcome strings to
      player names.
    - Cache (US slug) -> (player names, token_a, token_b).

  Layer 2  WebSocket book maintenance (continuous)
    - One persistent connection to
      ``wss://ws-subscriptions-clob.polymarket.com/ws/market``.
    - Subscribe with all active token IDs at once.
    - Per-token in-memory order book: bids: dict[float, float],
      asks: dict[float, float], last_trade_px.
    - Apply ``book`` events (full snapshot replace), ``price_change``
      events (deltas: BUY -> bids, SELL -> asks, size 0 = remove),
      and ``last_trade_price`` events.
    - PING/PONG keepalive every 10s.
    - Reconnect+resubscribe on token-set changes or disconnect with
      exponential backoff (1s -> 2s -> 5s -> 10s -> 30s).

  Layer 3  Display projection (on-demand at state write)
    - For each match, for each player:
        display_price = best_bid(token) = max(bids.keys())
    - Writes into ``slug_prices[slug]`` with keys ``side_a_cents`` and
      ``side_b_cents`` (matching the existing worker's output schema,
      so the resolver loop in ``cross_feed`` and ``main`` requires no
      changes).

Validated display rule
======================

Operator iPhone comparison (final, 2026-05-06) confirmed:

  display = (best_bid + best_ask) / 2

Earlier validation 2026-05-05 had concluded best_bid. That single
sample was on a low-liquidity match where best_bid happened to track
close to midpoint and was indistinguishable from it by inspection.
The 2026-05-06 side-by-side test (bid, ask, midpoint each shown
in their own column on /dashboard-replica) showed midpoint
consistently matches the iPhone across active and quiet matches,
while best_bid sums consistently to ~98c (the spread, taken from
the trader rather than the platform).

The midpoint rule is also what the WS-only handoff doc specifies
(section 17): match-level sum_midpoint = a_midpoint + b_midpoint
expected ≈ 1.0, with CROSS_OUTCOME_GAP warning only when the
absolute deviation exceeds 0.03.

See PM-Tennis-Pricing-Architecture-Handoff.md (sections 2.5 and
3.3) for the full empirical derivation.

Module contract
===============

This module exposes one entry point, ``run()``, which starts all three
layers and never returns. Output is published to module-level dicts:

  slug_prices: dict[str, dict[str, Any]]
      Mirrors the existing worker's slug_prices contract. Per-slug
      dict with keys ``side_a_cents`` (player A best_bid in cents)
      and ``side_b_cents`` (player B best_bid in cents). Optional
      diagnostic keys: ``side_a_bid_cents``, ``side_a_ask_cents``,
      ``side_a_last_cents``, ``side_a_age_ms``, and the same for B.

  slug_metadata: dict[str, dict[str, Any]]
      Per-slug match metadata. Keys: ``polymarket_event_id``,
      ``player_a_name``, ``player_b_name``, ``tournament_name``,
      ``event_date``, ``token_a``, ``token_b``, ``global_question``.

The existing ``_resolver_loop`` in ``polymarket_worker.py`` reads these
dicts and projects them into ``state.matches[ek].p1.price_cents`` and
``p2.price_cents``. This module does NOT touch state.matches directly.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

import httpx
import websockets

# ---------- Logging ----------

log = logging.getLogger("polymarket_global")

# ---------- Endpoints ----------

US_GATEWAY = "https://gateway.polymarket.us"
GAMMA_BASE = "https://gamma-api.polymarket.com"
WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

# ---------- Tunables ----------

DISCOVERY_INTERVAL_SEC = 60
WS_PING_INTERVAL_SEC = 10
WS_RECONNECT_INITIAL_BACKOFF_SEC = 1.0
WS_RECONNECT_MAX_BACKOFF_SEC = 30.0
GAMMA_PAGE_LIMIT = 100
US_PAGE_LIMIT = 100
HTTP_TIMEOUT_SEC = 20.0
GAMMA_HTTP_TIMEOUT_SEC = 30.0

# Diag-log cadence and paths. Override via GLOBAL_PRICING_DIAG_DIR env var.
DIAG_SNAPSHOT_INTERVAL_SEC = 30.0
DIAG_DEFAULT_LOG_DIR = "/var/data/global_pricing_diag"
DIAG_FALLBACK_LOG_DIR = "log/global_pricing_diag"

# Excluded Gamma question tokens (these indicate non-moneyline markets).
# A Gamma question containing any of these tokens is filtered out of the
# match-resolution candidate pool.
DERIVATIVE_QUESTION_TOKENS: tuple[str, ...] = (
    "total sets",
    "o/u",
    "over/under",
    "total games",
    "spread",
    "handicap",
    "first set",
    "set 1",
    "set 2",
    "set 3",
    "set 4",
    "set 5",
    "set winner",
    "tiebreak",
    "tiebreaker",
    "props",
    "+",
    "1.5",
    "2.5",
    "3.5",
)

# ---------- Module-level published state ----------

# Per-slug prices (matches the existing worker's contract; the resolver
# loop in polymarket_worker reads this dict).
slug_prices: dict[str, dict[str, Any]] = {}

# Per-slug match metadata (for the resolver to map slug -> match).
slug_metadata: dict[str, dict[str, Any]] = {}

# Internal: in-memory per-token order books. Keyed by token ID.
_books: dict[str, "_TokenBook"] = {}

# Internal: bumped whenever the active token set changes (matches added
# or removed). The WS loop watches this counter and reconnects when it
# changes.
_token_set_version: int = 0

# Internal: protects writes to _books, slug_prices, slug_metadata, and
# _token_set_version. Reads are best-effort (single-writer-per-key
# pattern; no read locking needed for the resolver loop's snapshot).
_state_lock = asyncio.Lock()


# ---------- Token book ----------


class _TokenBook:
    """In-memory order book for a single Polymarket Global outcome token.

    Attributes
    ----------
    token_id : str
        ERC1155 token ID (long numeric string).
    slug : str
        US gateway slug this token's match belongs to. Used to route
        display-price computations back to the slug_prices dict.
    side : str
        ``'a'`` or ``'b'`` — which side of the slug this token represents.
    bids : dict[float, float]
        Map of price -> size for the bid side. Sorted by price desc when
        querying via ``best_bid()``.
    asks : dict[float, float]
        Map of price -> size for the ask side.
    last_trade_px : float | None
        Most recent trade price seen on this token. Diagnostic only;
        not used for the chosen display rule.
    last_event_ts_ms : int | None
        Server-side timestamp of the most recent WS event for this
        token. Used for staleness detection.
    last_local_ts_ms : int | None
        Local clock timestamp at which we processed the most recent
        event. Used to compute "frame age" for diagnostics.
    frames_received : int
        Counter of WS events applied (book + price_change +
        last_trade_price). Used to detect quiet tokens.
    """

    def __init__(self, token_id: str, slug: str, side: str) -> None:
        self.token_id = token_id
        self.slug = slug
        self.side = side
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.last_trade_px: Optional[float] = None
        self.last_event_ts_ms: Optional[int] = None
        self.last_local_ts_ms: Optional[int] = None
        self.frames_received: int = 0

    def best_bid(self) -> Optional[float]:
        return max(self.bids.keys()) if self.bids else None

    def best_ask(self) -> Optional[float]:
        return min(self.asks.keys()) if self.asks else None

    def display_price(self) -> Optional[float]:
        """The validated display rule: midpoint of bid/ask.

        display = (best_bid + best_ask) / 2

        Returns None when either side has no quotes. Falls back to
        whichever side does exist if only one side is populated
        (rare, transient — should resolve when the other side fills).

        Validation history (see PM-Tennis-Pricing-Architecture-Handoff
        section 2.5):
          2026-05-05: initial empirical iPhone comparison concluded
                      best_bid. Revised below.
          2026-05-06: side-by-side iPhone vs (bid, ask, midpoint)
                      diagnostic showed midpoint matches the iPhone
                      across active and inactive matches. The earlier
                      best_bid result reflected a single low-liquidity
                      sample where best_bid happened to track close
                      to midpoint by coincidence. Spec rule
                      (handoff doc section 17) confirms midpoint;
                      sum_midpoint expected ≈ 1.0; CROSS_OUTCOME_GAP
                      warning fires only if abs(1 - sum_midpoint) > 0.03.
        """
        b = self.best_bid()
        a = self.best_ask()
        if b is not None and a is not None:
            return (b + a) / 2.0
        if b is not None:
            return b
        if a is not None:
            return a
        return None


# Per-slug event ring buffer — atomic A/B snapshot recorded after every
# WS event for either token. Used by /api/raw-stream to drive the
# /raw-stream-live browser page. Sums will be tight because both books
# are read in the same stack frame as the WS event that just fired.
#
# Each entry: {
#   "seq": int (monotonically increasing per-slug),
#   "ts_ms": int (local time when the event landed),
#   "ts_iso": str ("YYYY-MM-DD HH:MM:SS"),
#   "side_a_bid_cents": int | None,
#   "side_b_bid_cents": int | None,
# }
_slug_event_buffers: dict[str, list[dict]] = {}
_slug_event_seqs: dict[str, int] = {}
SLUG_EVENT_BUFFER_SIZE = 500


# ---------- Helpers (filled in by Phase 1.2) ----------


def _normalize_name(s: str) -> str:
    """Lowercase, strip non-alphabetic characters.

    Used for fuzzy substring-matching player names against Gamma
    question text. Removes spaces, hyphens, periods, accents (the
    accented characters fall through the isalpha check and are kept,
    so this is a soft normalization rather than ASCII-only).

    Examples
    --------
    >>> _normalize_name("Justin Engel")
    'justinengel'
    >>> _normalize_name("Nikolas Sanchez Izquierdo")
    'nikolassanchezizquierdo'
    >>> _normalize_name("Daniel Dutra da Silva")
    'danieldutradasilva'
    """
    return "".join(ch for ch in s.lower() if ch.isalpha())


# ---------- Discovery (Phase 1.2) ----------


async def _fetch_us_live_matches(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    """Poll US gateway for currently live tennis matches.

    Returns a list of dicts, one per live tennis match. Each dict has:
        us_slug          : str   the gateway market slug
        polymarket_event_id : str  the gateway event ID
        player_a_name    : str   from marketSides[0].description
        player_b_name    : str   from marketSides[1].description
        tournament_name  : str   from event tennisState.tournamentName
        event_date       : str   YYYY-MM-DD from event startDate

    Side effects: none (read-only HTTP).

    Failure handling: HTTP errors raise. Caller is expected to be in a
    try/except in the discovery loop and to retry on next interval.

    Why this is the right discovery source even though we're moving
    pricing to Polymarket Global: the US gateway is what the existing
    dashboard already uses to know which matches are live and what
    their player names are. Reusing it here means the existing
    cross_feed match-resolution logic doesn't need to change. The new
    worker only takes responsibility for the prices, not for the
    "which matches exist" question.
    """
    all_events: list[dict[str, Any]] = []
    offset = 0
    while True:
        resp = await client.get(
            f"{US_GATEWAY}/v2/sports/tennis/events",
            params={"limit": US_PAGE_LIMIT, "offset": offset},
        )
        resp.raise_for_status()
        data = resp.json()
        page = data.get("events") or []
        all_events.extend(page)
        if len(page) < US_PAGE_LIMIT:
            break
        offset += US_PAGE_LIMIT

    live: list[dict[str, Any]] = []
    for ev in all_events:
        if not ev.get("live"):
            continue
        markets = ev.get("markets") or []
        if not markets:
            continue
        m = markets[0]
        # Only moneyline markets. Defensive — the tennis feed is
        # almost entirely moneyline anyway, but skip non-moneyline
        # so downstream logic doesn't get derivative slugs.
        if m.get("sportsMarketTypeV2") not in (
            "SPORTS_MARKET_TYPE_MONEYLINE",
            None,  # older payloads may omit this; still treat as moneyline
        ):
            continue
        sides = m.get("marketSides") or []
        if len(sides) != 2:
            continue
        names = [s.get("description") or "" for s in sides]
        if not all(names):
            continue

        # Tournament name lives at event.eventState.tennisState.tournamentName
        # in current gateway responses; defensively walk.
        tournament = ""
        es = ev.get("eventState") or {}
        ts = es.get("tennisState") or {}
        tournament = ts.get("tournamentName") or ""

        # v0.8.5 (PM-D7): preserve full startDate timestamp. Prior code
        # truncated to YYYY-MM-DD only, which destroyed the time data
        # needed for cross-status sort by scheduled start_time. event_date
        # stays date-only for backward compatibility with downstream
        # date-comparison callers (e.g. _is_within_24h); start_date_iso
        # is the new field carrying the full ISO 8601 timestamp.
        # See docs/PM-D7-Start-Time-Bug-Fix-2026-05-06.md.
        start_date_iso = ev.get("startDate") or ""
        event_date = start_date_iso[:10]

        live.append(
            {
                "us_slug": m.get("slug") or "",
                "polymarket_event_id": str(ev.get("id") or ""),
                "player_a_name": names[0],
                "player_b_name": names[1],
                "tournament_name": tournament,
                "event_date": event_date,
                "start_date_iso": start_date_iso,
            }
        )
    return live


async def _fetch_gamma_tennis_markets(
    client: httpx.AsyncClient,
) -> list[dict[str, Any]]:
    """Pull active tennis markets from Polymarket Global Gamma.

    Returns a flat list of market dicts (NOT events). Each market has at
    minimum: ``question``, ``outcomes`` (JSON-string), ``clobTokenIds``
    (JSON-string), ``slug``.

    IMPORTANT: We use the ``/events`` endpoint, not ``/markets``. The
    ``/markets`` endpoint at gamma-api.polymarket.com does NOT honor
    ``tag_slug=tennis`` — it returns all 25,000+ active markets. The
    ``/events`` endpoint DOES filter server-side to tennis events
    (~60 events, ~1,700 markets). This was empirically verified
    2026-05-05 during MVP construction.

    The flat-market output preserves the existing match_us_to_gamma
    logic which expects a list of markets, not events.

    Side effects: none (read-only HTTP).

    Failure handling: HTTP errors raise. Empty pages terminate. A safety
    cap of offset > 5000 prevents runaway pagination if the server
    starts returning unbounded results.
    """
    all_markets: list[dict[str, Any]] = []
    offset = 0
    while True:
        resp = await client.get(
            f"{GAMMA_BASE}/events",
            params={
                "active": "true",
                "closed": "false",
                "limit": GAMMA_PAGE_LIMIT,
                "offset": offset,
                "tag_slug": "tennis",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        # Gamma sometimes wraps data: {"data": [...]}; support both
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not isinstance(data, list) or not data:
            break
        for ev in data:
            for m in ev.get("markets") or []:
                all_markets.append(m)
        if len(data) < GAMMA_PAGE_LIMIT:
            break
        offset += GAMMA_PAGE_LIMIT
        if offset > 5000:
            log.warning(
                "Gamma pagination exceeded 5000 events; truncating to avoid runaway"
            )
            break
    return all_markets


def _match_us_to_gamma(
    us_match: dict[str, Any], gamma_markets: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Find the Gamma market that corresponds to a US match by player names.

    US slug format (e.g., ``aec-atp-juseng-nikizq-2026-05-04``) is not
    programmatically equivalent to Gamma slugs (e.g.,
    ``florent-bax-vs-adrian-arcon-2026-05-05``). Match instead by
    normalizing player full names from US ``marketSides[].description``
    and substring-matching against Gamma's ``question`` field.

    Filters out non-moneyline derivative markets by checking the
    question for derivative tokens (totals, set winners, props,
    spreads). See ``DERIVATIVE_QUESTION_TOKENS`` for the exclusion list.

    Returns the chosen Gamma market dict, or None if no candidate is
    found. When multiple candidates remain (rare), prefers the shortest
    question (which empirically is the plain moneyline).

    Note on the last-name fallback: short last names (< 4 chars) skip
    the last-name check to avoid false positives (e.g., ``"li"`` would
    match many questions). Full-name normalized substring is the
    primary match path.
    """
    a_full = _normalize_name(us_match["player_a_name"])
    b_full = _normalize_name(us_match["player_b_name"])
    a_last = _normalize_name(us_match["player_a_name"].split()[-1])
    b_last = _normalize_name(us_match["player_b_name"].split()[-1])

    candidates: list[dict[str, Any]] = []
    for gm in gamma_markets:
        question = gm.get("question") or ""
        q_lower = question.lower()
        # Exclude derivative markets
        if any(tok in q_lower for tok in DERIVATIVE_QUESTION_TOKENS):
            continue
        q_norm = _normalize_name(question)
        a_hit = a_full in q_norm or (len(a_last) >= 4 and a_last in q_norm)
        b_hit = b_full in q_norm or (len(b_last) >= 4 and b_last in q_norm)
        if a_hit and b_hit:
            candidates.append(gm)

    if not candidates:
        return None
    # Prefer shortest question (plain moneyline rather than missed-derivative)
    candidates.sort(key=lambda m: len(m.get("question") or ""))
    return candidates[0]


def _parse_clob_token_ids(gm: dict[str, Any]) -> Optional[list[str]]:
    """Extract the two clobTokenIds from a Gamma market.

    Gamma stores ``clobTokenIds`` as a JSON-encoded string at the top
    level (NOT a JSON array directly), e.g.::

        "clobTokenIds": "[\\"105060544933...\\", \\"101532849819...\\"]"

    Returns the parsed list of two token ID strings, or None if absent
    or malformed. Defensive against the field being already-parsed (a
    list) in case Gamma changes its serialization.
    """
    raw = gm.get("clobTokenIds")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None
    if (
        isinstance(raw, list)
        and len(raw) == 2
        and all(isinstance(x, str) and x for x in raw)
    ):
        return list(raw)
    return None


def _assign_tokens_to_sides(
    us_match: dict[str, Any], gm: dict[str, Any], token_ids: list[str]
) -> tuple[str, str]:
    """Return (token_a, token_b) where token_a corresponds to player A.

    Uses Gamma's ``outcomes`` field (parallel to ``clobTokenIds`` by
    index) to figure out which token belongs to which player. If
    ``outcomes[i]`` matches player A's name (full or last-name
    fallback), then ``token_ids[i]`` is player A's token.

    If outcomes is missing/malformed or the match is ambiguous, falls
    back to ``(token_ids[0], token_ids[1])`` — which may be wrong but
    is consistent across runs (the operator can detect this via
    iPhone comparison and we can patch with an override if needed).

    The fallback path is the place future bugs will hide. Add an
    override file or improved heuristic if the operator reports
    a match where prices are flipped.
    """
    outcomes_raw = gm.get("outcomes")
    outcomes: list[str] = []
    if isinstance(outcomes_raw, str):
        try:
            outcomes = json.loads(outcomes_raw)
        except (json.JSONDecodeError, ValueError):
            outcomes = []
    elif isinstance(outcomes_raw, list):
        outcomes = list(outcomes_raw)

    a_full = _normalize_name(us_match["player_a_name"])
    a_last = _normalize_name(us_match["player_a_name"].split()[-1])

    if len(outcomes) == 2 and len(token_ids) == 2:
        for i, oc in enumerate(outcomes):
            on = _normalize_name(oc or "")
            if not on:
                continue
            if a_full in on or (len(a_last) >= 4 and a_last in on):
                # token_ids[i] is player A's outcome
                if i == 0:
                    return token_ids[0], token_ids[1]
                else:
                    return token_ids[1], token_ids[0]

    # Fallback: positional. Log a warning so the operator notices if
    # this happens often.
    log.warning(
        "Could not match outcomes to player names for slug=%s; "
        "falling back to positional token assignment. "
        "outcomes=%r player_a=%r",
        us_match.get("us_slug"),
        outcomes,
        us_match.get("player_a_name"),
    )
    return token_ids[0], token_ids[1]


async def _discovery_loop() -> None:
    """Discovery layer: refresh active matches + token IDs every 60s.

    Each iteration:

      1. Fetch live tennis matches from Polymarket US gateway.
      2. Fetch tennis markets from Polymarket Global Gamma.
      3. For each live US match:
         a. If we already have token IDs cached for this slug, reuse them.
         b. Otherwise, find a matching Gamma market and extract token IDs.
      4. Update slug_metadata, _books, _token_set_version atomically.

    Retains existing cached tokens for already-resolved matches across
    iterations so we don't re-resolve every cycle (Gamma question text
    is stable for the lifetime of a market, so once we've matched, the
    mapping is permanent until the match ends).

    Drops matches that are no longer live (out of US gateway), which
    naturally garbage-collects ended matches.

    Failure handling: any HTTP error in this iteration is caught and
    logged; existing state is preserved and we retry next interval.
    """
    log.info("polymarket_global discovery loop starting")

    while True:
        try:
            await _discovery_iteration()
        except Exception:
            log.exception("polymarket_global discovery iteration failed; retrying")
        await asyncio.sleep(DISCOVERY_INTERVAL_SEC)


async def _discovery_iteration() -> None:
    """One pass of the discovery loop. Factored out for testability."""
    global _token_set_version

    async with httpx.AsyncClient(
        timeout=GAMMA_HTTP_TIMEOUT_SEC,
        headers={
            "User-Agent": "pm-dashboard-global/0.8",
            "Accept": "application/json",
        },
    ) as client:
        us_matches = await _fetch_us_live_matches(client)
        log.info("polymarket_global: US live tennis matches: %d", len(us_matches))

        if not us_matches:
            # No live matches: drop everything.
            async with _state_lock:
                if slug_metadata or _books:
                    log.info(
                        "polymarket_global: no live matches; dropping %d slugs / %d tokens",
                        len(slug_metadata),
                        len(_books),
                    )
                    slug_metadata.clear()
                    _books.clear()
                    slug_prices.clear()
                    _token_set_version += 1
            return

        # Only fetch Gamma when we need to resolve at least one new match.
        unresolved_slugs = [
            um["us_slug"]
            for um in us_matches
            if um["us_slug"] not in slug_metadata
            or "token_a" not in slug_metadata[um["us_slug"]]
        ]
        gamma_markets: list[dict[str, Any]] = []
        if unresolved_slugs:
            gamma_markets = await _fetch_gamma_tennis_markets(client)
            log.info(
                "polymarket_global: Gamma tennis markets fetched: %d (resolving %d new matches)",
                len(gamma_markets),
                len(unresolved_slugs),
            )

    # Build the new metadata table and decide which tokens are now active.
    new_metadata: dict[str, dict[str, Any]] = {}
    for um in us_matches:
        slug = um["us_slug"]
        if not slug:
            continue

        # Reuse cached resolution if available
        existing = slug_metadata.get(slug)
        if existing and existing.get("token_a") and existing.get("token_b"):
            new_metadata[slug] = existing
            continue

        # Try to resolve from Gamma
        gm = _match_us_to_gamma(um, gamma_markets)
        if gm is None:
            log.info(
                "polymarket_global: no Gamma match for %s (%s vs %s)",
                slug,
                um["player_a_name"],
                um["player_b_name"],
            )
            # Record the metadata anyway, sans tokens, so the resolver
            # can see this slug exists but mark it unresolved.
            new_metadata[slug] = {
                "polymarket_event_id": um["polymarket_event_id"],
                "player_a_name": um["player_a_name"],
                "player_b_name": um["player_b_name"],
                "tournament_name": um["tournament_name"],
                "event_date": um["event_date"],
                "start_date_iso": um.get("start_date_iso", ""),
                "global_status": "no_global_market",
            }
            continue

        token_ids = _parse_clob_token_ids(gm)
        if not token_ids:
            log.info(
                "polymarket_global: no clobTokenIds for slug=%s gm.question=%r",
                slug,
                gm.get("question"),
            )
            new_metadata[slug] = {
                "polymarket_event_id": um["polymarket_event_id"],
                "player_a_name": um["player_a_name"],
                "player_b_name": um["player_b_name"],
                "tournament_name": um["tournament_name"],
                "event_date": um["event_date"],
                "start_date_iso": um.get("start_date_iso", ""),
                "global_status": "no_global_market",
            }
            continue

        token_a, token_b = _assign_tokens_to_sides(um, gm, token_ids)
        new_metadata[slug] = {
            "polymarket_event_id": um["polymarket_event_id"],
            "player_a_name": um["player_a_name"],
            "player_b_name": um["player_b_name"],
            "tournament_name": um["tournament_name"],
            "event_date": um["event_date"],
            "start_date_iso": um.get("start_date_iso", ""),
            "token_a": token_a,
            "token_b": token_b,
            "global_question": gm.get("question", ""),
            "global_status": "resolved",
        }
        log.info(
            "polymarket_global: resolved %s: %s vs %s -> %s.../%s...",
            slug,
            um["player_a_name"],
            um["player_b_name"],
            token_a[:12],
            token_b[:12],
        )

    # Atomically swap state and rebuild the token book index
    async with _state_lock:
        old_token_set = set(_books.keys())

        slug_metadata.clear()
        slug_metadata.update(new_metadata)

        new_token_set: set[str] = set()
        for slug, meta in slug_metadata.items():
            ta = meta.get("token_a")
            tb = meta.get("token_b")
            if ta:
                new_token_set.add(ta)
                if ta not in _books:
                    _books[ta] = _TokenBook(token_id=ta, slug=slug, side="a")
                else:
                    # Preserve book contents across discovery; just refresh the
                    # routing fields in case a slug was reassigned.
                    _books[ta].slug = slug
                    _books[ta].side = "a"
            if tb:
                new_token_set.add(tb)
                if tb not in _books:
                    _books[tb] = _TokenBook(token_id=tb, slug=slug, side="b")
                else:
                    _books[tb].slug = slug
                    _books[tb].side = "b"

        # Drop books for tokens no longer needed
        for stale_token in old_token_set - new_token_set:
            _books.pop(stale_token, None)

        # Drop slug_prices entries for slugs no longer present
        for stale_slug in list(slug_prices.keys()):
            if stale_slug not in slug_metadata:
                slug_prices.pop(stale_slug, None)

        # Bump version if the active token set changed (triggers WS resubscribe)
        if old_token_set != new_token_set:
            _token_set_version += 1
            log.info(
                "polymarket_global: token set changed (%d -> %d tokens), "
                "version=%d",
                len(old_token_set),
                len(new_token_set),
                _token_set_version,
            )


# ---------- WebSocket (Phase 1.3) ----------


def _handle_ws_event(ev: dict[str, Any]) -> None:
    """Dispatch a single WS event to the right token book.

    Routes by ``asset_id``. Events for tokens not in our active set
    are silently dropped (this can happen briefly after we unsubscribe
    a token but the server is still flushing).

    Unknown event types are logged at DEBUG and ignored. Production
    should never crash on a new event type — the Polymarket protocol
    is allowed to grow.
    """
    et = ev.get("event_type")
    asset_id = ev.get("asset_id")

    if not asset_id:
        # Some payloads omit event_type but carry bids/asks (early-feed
        # snapshot). Treat as a book event if the shape matches.
        if et is None and "bids" in ev and "asks" in ev:
            asset_id = ev.get("asset_id")
            if not asset_id:
                return
            et = "book"
        else:
            return

    book = _books.get(asset_id)
    if book is None:
        # Token not currently tracked. Could be a stale frame from a
        # token we just dropped. Silent drop.
        return

    if et == "book":
        _apply_book(book, ev)
    elif et == "price_change":
        _apply_price_change(book, ev)
    elif et == "last_trade_price":
        _apply_last_trade(book, ev)
    elif et == "best_bid_ask":
        # Optional corroboration. We rely on book + price_change for
        # state truth, so just ignore here. Could be used in future
        # for top-of-book mismatch detection.
        pass
    elif et == "tick_size_change":
        # We don't trade, so tick size doesn't affect our display.
        # Logged for audit.
        log.debug("polymarket_global: tick_size_change asset=%s", asset_id)
    elif et == "market_resolved":
        # Mark book as resolved by clearing it. The discovery loop
        # will drop the slug on its next iteration when the US gateway
        # also marks the match as no-longer-live.
        log.info("polymarket_global: market_resolved asset=%s", asset_id)
        book.bids.clear()
        book.asks.clear()
    elif et is None and "bids" in ev and "asks" in ev:
        ev = dict(ev)
        ev["event_type"] = "book"
        _apply_book(book, ev)
    else:
        log.debug("polymarket_global: unknown event_type=%r asset=%s", et, asset_id)


def _apply_book(book: _TokenBook, ev: dict[str, Any]) -> None:
    """Apply a full ``book`` snapshot to a token's local order book.

    Clears existing levels and reloads from the snapshot. Defensive
    against malformed entries (skip rather than crash).
    """
    book.bids.clear()
    book.asks.clear()

    for level in ev.get("bids") or []:
        try:
            px = float(level["price"])
            sz = float(level["size"])
        except (KeyError, TypeError, ValueError):
            continue
        if sz > 0 and 0.0 <= px <= 1.0:
            book.bids[px] = sz

    for level in ev.get("asks") or []:
        try:
            px = float(level["price"])
            sz = float(level["size"])
        except (KeyError, TypeError, ValueError):
            continue
        if sz > 0 and 0.0 <= px <= 1.0:
            book.asks[px] = sz

    book.frames_received += 1
    book.last_event_ts_ms = _safe_ts_ms(ev.get("timestamp"))
    book.last_local_ts_ms = int(time.time() * 1000)
    _record_slug_event(book.slug)


def _apply_price_change(book: _TokenBook, ev: dict[str, Any]) -> None:
    """Apply incremental price level changes to a token's order book.

    Side mapping per the Polymarket Global protocol:

      side == "BUY"   -> bid level update
      side == "SELL"  -> ask level update
      size == 0       -> remove level
      size > 0        -> set level size

    Both ``price_changes`` and ``changes`` field names are observed in
    the wild (different Polymarket deployments). Support both.
    """
    changes = ev.get("price_changes") or ev.get("changes") or []
    for c in changes:
        try:
            px = float(c["price"])
            sz = float(c["size"])
        except (KeyError, TypeError, ValueError):
            continue
        side = c.get("side", "")
        if not (0.0 <= px <= 1.0):
            continue

        if side == "BUY":
            target = book.bids
        elif side == "SELL":
            target = book.asks
        else:
            continue

        if sz == 0:
            target.pop(px, None)
        else:
            target[px] = sz

    book.frames_received += 1
    book.last_event_ts_ms = _safe_ts_ms(ev.get("timestamp"))
    book.last_local_ts_ms = int(time.time() * 1000)
    _record_slug_event(book.slug)


def _apply_last_trade(book: _TokenBook, ev: dict[str, Any]) -> None:
    """Update the token's last trade price.

    Diagnostic only under the validated display rule (best_bid). Kept
    so we can fall back to it if production observation reveals the
    iPhone uses last-trade when bids are empty.
    """
    try:
        px = float(ev.get("price"))
    except (TypeError, ValueError):
        return
    if not (0.0 <= px <= 1.0):
        return

    book.last_trade_px = px
    book.frames_received += 1
    book.last_event_ts_ms = _safe_ts_ms(ev.get("timestamp"))
    book.last_local_ts_ms = int(time.time() * 1000)
    _record_slug_event(book.slug)


def _record_slug_event(slug: str) -> None:
    """Snapshot the current A/B best_bid for this slug into the ring buffer.

    Called from the WS event handlers (book / price_change / last_trade)
    after the local order book has been updated. Captures both player
    tokens' best_bid in the same stack frame so sums are tight.

    The browser's /raw-stream-live page polls /api/raw-stream?slug=...
    with the highest seq it's already seen and gets just the new tail.
    """
    meta = slug_metadata.get(slug)
    if not meta:
        return
    ta = meta.get("token_a")
    tb = meta.get("token_b")
    book_a = _books.get(ta) if ta else None
    book_b = _books.get(tb) if tb else None

    a_bid = book_a.best_bid() if book_a else None
    b_bid = book_b.best_bid() if book_b else None

    now_ms = int(time.time() * 1000)
    ts_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(now_ms / 1000))

    seq = _slug_event_seqs.get(slug, 0) + 1
    _slug_event_seqs[slug] = seq

    rec = {
        "seq": seq,
        "ts_ms": now_ms,
        "ts_iso": ts_iso,
        "side_a_bid_cents": _to_cents(a_bid),
        "side_b_bid_cents": _to_cents(b_bid),
    }

    buf = _slug_event_buffers.get(slug)
    if buf is None:
        buf = []
        _slug_event_buffers[slug] = buf
    buf.append(rec)
    if len(buf) > SLUG_EVENT_BUFFER_SIZE:
        del buf[: len(buf) - SLUG_EVENT_BUFFER_SIZE]


def slug_events_since(slug: str, since_seq: int = 0) -> tuple[list[dict], int]:
    """Public accessor: return events with seq > since_seq for the slug.

    Returns (rows, latest_seq). Caller passes the latest_seq back as
    since_seq on the next call to get just the new tail.
    """
    buf = _slug_event_buffers.get(slug, [])
    if not buf:
        return [], _slug_event_seqs.get(slug, 0)
    rows = [e for e in buf if e["seq"] > since_seq]
    latest = buf[-1]["seq"] if buf else _slug_event_seqs.get(slug, 0)
    return rows, latest


def _safe_ts_ms(raw: Any) -> Optional[int]:
    """Best-effort parse of a Polymarket WS timestamp into int ms.

    The protocol sends timestamps as numeric strings (e.g.,
    ``"1710000000000"``). Defensive against unexpected types.
    """
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


async def _ws_loop() -> None:
    """WS layer: maintain a persistent connection with all active tokens.

    Single connection, multiple tokens subscribed at once. The loop
    structure:

      while True:
          snapshot active tokens + version
          if no tokens: wait, retry
          connect, subscribe, dispatch messages
          if token-set version changes: close, reconnect with new set
          on disconnect: backoff, reconnect

    Reconnect backoff: 1s -> 2s -> 5s -> 10s -> 30s (capped). Reset to
    1s after a successful subscription.

    On any disconnect, all currently-tracked books are NOT cleared:
    the next ``book`` snapshot from Polymarket Global will overwrite
    them anyway. We accept a brief window of stale data over loss of
    state during transient disconnects.
    """
    log.info("polymarket_global ws loop starting")
    backoff = WS_RECONNECT_INITIAL_BACKOFF_SEC

    while True:
        # Snapshot what we should subscribe to.
        async with _state_lock:
            active_tokens = sorted(_books.keys())
            version_at_connect = _token_set_version

        if not active_tokens:
            # No active matches — wait for discovery.
            await asyncio.sleep(2.0)
            continue

        try:
            await _ws_one_session(active_tokens, version_at_connect)
            # Clean exit (token set changed). Reset backoff.
            backoff = WS_RECONNECT_INITIAL_BACKOFF_SEC
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning(
                "polymarket_global: WS session error (%s: %s); reconnect in %.1fs",
                type(exc).__name__,
                exc,
                backoff,
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2.0, WS_RECONNECT_MAX_BACKOFF_SEC)


async def _ws_one_session(
    active_tokens: list[str], version_at_connect: int
) -> None:
    """One WS session: connect, subscribe, dispatch until token-set changes.

    Returns normally when the token set version changes (we exit so the
    outer loop reconnects with the new token list). Raises on connection
    errors so the outer loop's backoff applies.
    """
    log.info(
        "polymarket_global: WS connecting (subscribing to %d tokens, version=%d)",
        len(active_tokens),
        version_at_connect,
    )

    async with websockets.connect(
        WS_URL,
        ping_interval=None,  # we send PING text frames manually
        close_timeout=5.0,
    ) as ws:
        sub_msg = {
            "assets_ids": active_tokens,
            "type": "market",
            "custom_feature_enabled": True,
        }
        await ws.send(json.dumps(sub_msg))
        log.info(
            "polymarket_global: WS subscribed to %d tokens", len(active_tokens)
        )

        # Two background tasks: keepalive ping, and watchdog for token-set change.
        ping_task = asyncio.create_task(_ws_pinger(ws))
        version_watchdog_event = asyncio.Event()
        watchdog_task = asyncio.create_task(
            _ws_version_watchdog(version_at_connect, version_watchdog_event, ws)
        )

        try:
            async for raw_msg in ws:
                if raw_msg == "PONG" or raw_msg == b"PONG":
                    continue

                # Decode binary frames if any
                if isinstance(raw_msg, bytes):
                    try:
                        raw_msg = raw_msg.decode("utf-8")
                    except UnicodeDecodeError:
                        continue

                try:
                    payload = json.loads(raw_msg)
                except (json.JSONDecodeError, ValueError):
                    log.debug(
                        "polymarket_global: non-JSON WS msg (first 100 chars): %r",
                        raw_msg[:100] if isinstance(raw_msg, str) else raw_msg,
                    )
                    continue

                # Polymarket Global sometimes sends arrays of events
                if isinstance(payload, list):
                    for ev in payload:
                        if isinstance(ev, dict):
                            _handle_ws_event(ev)
                elif isinstance(payload, dict):
                    _handle_ws_event(payload)

                # Was the version watchdog tripped?
                if version_watchdog_event.is_set():
                    log.info(
                        "polymarket_global: token set version changed; "
                        "closing WS to resubscribe"
                    )
                    return  # clean exit, outer loop reconnects
        finally:
            ping_task.cancel()
            watchdog_task.cancel()
            for t in (ping_task, watchdog_task):
                try:
                    await t
                except (asyncio.CancelledError, Exception):
                    pass


async def _ws_pinger(ws: Any) -> None:
    """Send PING text frames every WS_PING_INTERVAL_SEC seconds."""
    while True:
        await asyncio.sleep(WS_PING_INTERVAL_SEC)
        try:
            await ws.send("PING")
        except Exception:
            return  # connection closed; outer loop will reconnect


async def _ws_version_watchdog(
    version_at_connect: int, fired: asyncio.Event, ws: Any
) -> None:
    """Poll _token_set_version; fire event + close ws when it changes.

    Runs as a background task during a WS session. When discovery
    bumps the version (new match started, old one ended), this signals
    the message loop to exit cleanly so we can reconnect with the new
    token set.
    """
    while True:
        await asyncio.sleep(2.0)
        if _token_set_version != version_at_connect:
            fired.set()
            try:
                await ws.close()
            except Exception:
                pass
            return


# ---------- Display projection (Phase 1.4) ----------


def _project_to_slug_prices() -> None:
    """Read all token books, compute display prices, write slug_prices.

    Output schema matches the existing ``polymarket_worker.slug_prices``
    contract so the existing resolver loop (in ``polymarket_worker``)
    needs no changes:

        slug_prices[slug] = {
            "side_a_cents": int | None,   # validated: best_bid in cents
            "side_b_cents": int | None,
            # Diagnostics (optional, for audit / future fallback logic):
            "side_a_bid_cents":  int | None,   # same as side_a_cents
            "side_a_ask_cents":  int | None,
            "side_a_last_cents": int | None,
            "side_a_age_ms":     int | None,
            "side_b_bid_cents":  int | None,
            "side_b_ask_cents":  int | None,
            "side_b_last_cents": int | None,
            "side_b_age_ms":     int | None,
            "global_status":     str,           # "resolved" or "no_global_market"
            "updated_ms":        int,           # local clock at projection
        }

    Side effects: replaces (does not merge) ``slug_prices[slug]`` for
    every slug currently in ``slug_metadata``. Slugs no longer in
    ``slug_metadata`` are NOT touched here; the discovery loop drops
    them on its next iteration.

    Concurrency: this function is intended to be called from one task
    only (the projection loop). It reads ``_books`` and
    ``slug_metadata``; both are mutated by the discovery loop under
    ``_state_lock``. We accept eventual-consistency reads (no lock)
    here because:
      - Discovery only mutates these dicts atomically inside the lock
      - A projection that reads a half-updated dict would just be
        slightly-stale-by-one-cycle, never corrupt
      - The display freshness gain from no-lock reads outweighs the
        very rare race
    """
    now_ms = int(time.time() * 1000)

    for slug, meta in slug_metadata.items():
        ta = meta.get("token_a")
        tb = meta.get("token_b")
        global_status = meta.get("global_status", "unknown")

        book_a = _books.get(ta) if ta else None
        book_b = _books.get(tb) if tb else None

        side_a_cents = _book_display_cents(book_a)
        side_b_cents = _book_display_cents(book_b)

        slug_prices[slug] = {
            "side_a_cents": side_a_cents,
            "side_b_cents": side_b_cents,
            "side_a_bid_cents": _to_cents(book_a.best_bid()) if book_a else None,
            "side_a_ask_cents": _to_cents(book_a.best_ask()) if book_a else None,
            "side_a_last_cents": _to_cents(book_a.last_trade_px) if book_a else None,
            "side_a_age_ms": _book_age_ms(book_a, now_ms),
            "side_b_bid_cents": _to_cents(book_b.best_bid()) if book_b else None,
            "side_b_ask_cents": _to_cents(book_b.best_ask()) if book_b else None,
            "side_b_last_cents": _to_cents(book_b.last_trade_px) if book_b else None,
            "side_b_age_ms": _book_age_ms(book_b, now_ms),
            "global_status": global_status,
            "updated_ms": now_ms,
        }


def _book_display_cents(book: Optional[_TokenBook]) -> Optional[int]:
    """Apply the validated display rule and convert to int cents.

    Validated 2026-05-05 against iPhone: ``display = best_bid``.
    """
    if book is None:
        return None
    px = book.display_price()
    return _to_cents(px)


def _book_age_ms(book: Optional[_TokenBook], now_ms: int) -> Optional[int]:
    """Return ms since the book's last local update, or None."""
    if book is None or book.last_local_ts_ms is None:
        return None
    return max(0, now_ms - book.last_local_ts_ms)


def _to_cents(price: Optional[float]) -> Optional[int]:
    """Convert a 0.0-1.0 probability to integer cents (0-100). Rounds to nearest."""
    if price is None:
        return None
    if not (0.0 <= price <= 1.0):
        return None
    return int(round(price * 100))


async def _projection_loop() -> None:
    """Periodically read token books and project prices into slug_prices.

    Runs at a fast cadence (every 250ms) so display prices keep up with
    WS update bursts without flooding the resolver loop. The resolver
    reads ``slug_prices`` on its own cadence and only sees the latest
    snapshot.

    This loop does NOT block on WS or discovery. If they hang, this
    keeps republishing the most recent values from the last successful
    book updates.
    """
    log.info("polymarket_global projection loop starting")
    while True:
        try:
            _project_to_slug_prices()
        except Exception:
            log.exception("polymarket_global projection iteration failed")
        await asyncio.sleep(0.25)


# ---------- Diagnostic logging (Phase 1.6) ----------


async def _diag_log_loop() -> None:
    """Periodically log per-match diagnostic snapshots.

    Writes one JSON line per match per snapshot interval to a daily-
    rotated JSONL file. The audit trail enables side-by-side comparison
    of dashboard prices vs iPhone prices vs raw book values during the
    Phase 2 validation window.

    Output schema (per line)::

        {
          "ts": "2026-05-05T19:35:12.345+0000",
          "ts_ms": 1746477312345,
          "slug": "aec-atp-flobax-adrarc-2026-05-05",
          "polymarket_event_id": "10678",
          "tournament": "ATP Brazzaville",
          "player_a": {
            "name": "Florent Bax",
            "display_cents": 91,
            "bid_cents": 91,
            "ask_cents": 93,
            "last_cents": 90,
            "age_ms": 1234,
            "frames_received": 287,
            "token": "105060544933..."
          },
          "player_b": { ... },
          "global_status": "resolved",
          "global_question": "Brazzaville: Florent Bax vs Adrian Arcon"
        }

    Cadence: one snapshot per match per 30 seconds (matches Phase 2's
    AC observation cadence). At 6 live matches, this is 12 lines/min,
    ~17,000 lines/day — well under any reasonable disk concern.

    Path: ``/var/data/global_pricing_diag/YYYY-MM-DD.jsonl`` on Render
    (disk mount), with fallback to ``./log/global_pricing_diag/`` if
    the disk mount isn't available (local dev).

    Failure handling: any disk write error is caught and logged. The
    loop never exits. Loss of a snapshot is acceptable; what matters
    is that the loop keeps running.
    """
    log.info("polymarket_global diag log loop starting")

    log_dir = _resolve_diag_log_dir()
    log.info("polymarket_global diag log dir: %s", log_dir)

    while True:
        try:
            _emit_diag_snapshot(log_dir)
        except Exception:
            log.exception("polymarket_global diag snapshot failed")
        await asyncio.sleep(DIAG_SNAPSHOT_INTERVAL_SEC)


def _resolve_diag_log_dir() -> str:
    """Choose a writable directory for diag logs.

    Tries the env var first, then the Render Disk path, then the
    repo-local fallback. Creates the directory if needed. Falls back
    silently rather than crashing — diag logging is best-effort.
    """
    candidates: list[str] = []
    env_dir = os.environ.get("GLOBAL_PRICING_DIAG_DIR", "").strip()
    if env_dir:
        candidates.append(env_dir)
    candidates.append(DIAG_DEFAULT_LOG_DIR)
    candidates.append(DIAG_FALLBACK_LOG_DIR)

    for d in candidates:
        try:
            from pathlib import Path
            Path(d).mkdir(parents=True, exist_ok=True)
            # Probe write permission
            probe = Path(d) / ".write_probe"
            probe.write_text("ok")
            probe.unlink()
            return d
        except Exception:
            continue

    # All candidates failed; return the fallback anyway so writes
    # continue to fail visibly and we don't silently drop logs.
    log.warning(
        "polymarket_global: no diag log dir writable; using %s anyway",
        DIAG_FALLBACK_LOG_DIR,
    )
    return DIAG_FALLBACK_LOG_DIR


def _emit_diag_snapshot(log_dir: str) -> None:
    """Write one diag-log line per resolved match to the daily file."""
    from pathlib import Path

    now_ms = int(time.time() * 1000)
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now_ms / 1000)) + (
        f".{now_ms % 1000:03d}+0000"
    )
    today_str = time.strftime("%Y-%m-%d", time.gmtime(now_ms / 1000))
    log_path = Path(log_dir) / f"{today_str}.jsonl"

    lines: list[str] = []
    for slug, meta in slug_metadata.items():
        ta = meta.get("token_a")
        tb = meta.get("token_b")
        book_a = _books.get(ta) if ta else None
        book_b = _books.get(tb) if tb else None

        record = {
            "ts": now_iso,
            "ts_ms": now_ms,
            "slug": slug,
            "polymarket_event_id": meta.get("polymarket_event_id"),
            "tournament": meta.get("tournament_name"),
            "event_date": meta.get("event_date"),
            "start_date_iso": meta.get("start_date_iso"),
            "global_status": meta.get("global_status"),
            "global_question": meta.get("global_question"),
            "player_a": _diag_player_record(
                meta.get("player_a_name"), book_a, ta, now_ms
            ),
            "player_b": _diag_player_record(
                meta.get("player_b_name"), book_b, tb, now_ms
            ),
        }
        lines.append(json.dumps(record, separators=(",", ":")))

    if not lines:
        return

    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
        fh.write("\n")


def _diag_player_record(
    name: Optional[str], book: Optional[_TokenBook], token: Optional[str], now_ms: int
) -> dict[str, Any]:
    """Build the per-player block of a diag snapshot."""
    if book is None:
        return {
            "name": name,
            "display_cents": None,
            "bid_cents": None,
            "ask_cents": None,
            "last_cents": None,
            "age_ms": None,
            "frames_received": 0,
            "token": token,
        }
    return {
        "name": name,
        "display_cents": _to_cents(book.display_price()),
        "bid_cents": _to_cents(book.best_bid()),
        "ask_cents": _to_cents(book.best_ask()),
        "last_cents": _to_cents(book.last_trade_px),
        "age_ms": _book_age_ms(book, now_ms),
        "frames_received": book.frames_received,
        "token": token,
    }


# ---------- Public entry point ----------


async def run() -> None:
    """Start all three layers. Never returns under normal operation.

    Designed to be launched as an asyncio task from main.py:

        asyncio.create_task(polymarket_global_worker.run())

    Concurrent with (not replacing) ``polymarket_worker.run()`` during
    Phase 2 shadow mode. In Phase 3 cutover, main.py wires the dashboard
    frontend to read from this module's ``slug_prices`` instead of the
    old worker's.
    """
    log.info("polymarket_global_worker starting (shadow mode)")

    # Layer 1: discovery
    discovery_task = asyncio.create_task(_discovery_loop(), name="pm_global_discovery")
    # Layer 2: WS book maintenance
    ws_task = asyncio.create_task(_ws_loop(), name="pm_global_ws")
    # Layer 3: display projection
    projection_task = asyncio.create_task(_projection_loop(), name="pm_global_projection")
    # Layer 4: diagnostic logging (audit trail for shadow-mode validation)
    diag_task = asyncio.create_task(_diag_log_loop(), name="pm_global_diag_log")

    tasks = [discovery_task, ws_task, projection_task, diag_task]

    try:
        # Wait until any task fails (it shouldn't — they all loop forever).
        # If one does, log and re-raise to surface the failure.
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for t in done:
            exc = t.exception()
            if exc is not None:
                log.exception(
                    "polymarket_global_worker subtask %s raised; shutting down",
                    t.get_name(),
                    exc_info=exc,
                )
        # If we get here, one task died. Cancel the rest and re-raise.
        for t in pending:
            t.cancel()
        for t in pending:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        # Surface the first exception
        for t in done:
            exc = t.exception()
            if exc is not None:
                raise exc
    except asyncio.CancelledError:
        # Normal shutdown path
        log.info("polymarket_global_worker cancelled; stopping subtasks")
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except (asyncio.CancelledError, Exception):
                pass
        raise
