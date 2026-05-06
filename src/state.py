"""In-memory match state.

Single dict keyed by API-Tennis event_key. Worker writes, endpoints read.
No locking yet — single asyncio loop, single writer. Revisit if that changes.

Also tracks last-event-arrived timestamps per upstream source. These are
process-level values (one per source), not per-match. The frontend uses
them to render the liveness counters in the header. Per Design Notes §8,
the counter resets on any message arrival from that source — not just
messages with score changes — so the counter measures connection health,
not match activity.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Player:
    name: str
    country_iso3: Optional[str] = None  # for flag rendering; None until resolved
    player_key: Optional[int] = None    # API-Tennis canonical numeric ID; None
                                        # if not yet bootstrapped (Polymarket-only
                                        # shadows before name → key resolution).
                                        # Once set for a given player, never changes.


@dataclass
class Position:
    """Operator's open position on one side of a match.

    Step 9-A C1 (v2): surfaced in /api/matches when the operator has an
    open position on a given side. Populated by the resolver loop via
    player-name overlap between Polymarket position outcome and the
    match's p1/p2 names — same join strategy prices use, not slug
    dictionary lookup.

    Field semantics:
      net_shares:   open shares; integer count.
      cost_cents:   total dollars-paid-in basis, in cents. Used for
                    entry-price math: entry = cost_cents / net_shares.
      cash_value_cents:  current notional value at last-known price, in
                    cents. Used for unrealized P&L:
                    pnl = cash_value_cents - cost_cents.
      realized_cents:   P&L already booked from prior partial closes on
                    this contract, in cents. Mostly informational.
      update_time:  ISO timestamp from Polymarket of last position change.

    All cents fields are stored as ints to match the rest of state.py
    convention (p1_price_cents etc) and to avoid float drift on money.
    """
    net_shares: int
    cost_cents: int
    cash_value_cents: int
    realized_cents: int
    update_time: Optional[str] = None


@dataclass
class SetScore:
    games: int                          # 0-7 (or higher in deciding sets without tiebreak)
    tiebreak: Optional[int] = None      # tiebreak point count if this set went to tiebreak


@dataclass
class Match:
    event_key: str
    tour: str                           # "ATP" | "WTA" | "Ch."
    venue: str                          # tournament city, e.g. "Madrid"
    round: str                          # e.g. "R32", "QF"
    status: str                         # "live" | "upcoming" | "finished"
    set_label: Optional[str] = None     # e.g. "2nd set"; None for non-live
    start_time: Optional[str] = None    # ISO scheduled start time. Set
                                         # on every match (live, upcoming,
                                         # finished). v0.8.3: previously
                                         # upcoming-only; now always
                                         # populated to support stable
                                         # cross-status sort order.

    p1: Player = field(default_factory=lambda: Player(name=""))
    p2: Player = field(default_factory=lambda: Player(name=""))

    p1_sets: list[SetScore] = field(default_factory=list)
    p2_sets: list[SetScore] = field(default_factory=list)

    p1_game: Optional[str] = None       # "0" | "15" | "30" | "40" | "AD"
    p2_game: Optional[str] = None

    server: Optional[int] = None        # 1 or 2; None until first serve

    # Phase 1C — populated by Polymarket worker via cross-feed mapping
    p1_price_cents: Optional[int] = None
    p2_price_cents: Optional[int] = None

    # Step 4 — momentum scores per player. Computed by api_tennis_worker
    # via momentum.compute_momentum() on every frame. Both fields are
    # None for upcoming matches and live matches with empty point_history.
    # Per the operator-confirmed spec (design/Dashboard_Indicators_Design.md):
    # raw weighted score over rolling last 12 individual points, with
    # weights 1/2/3/5 for serve-pt/return-pt/hold/break. Frontend applies
    # noise-floor and differential-threshold rules to determine the
    # three-state rendering (none / contested / leader+trailing).
    p1_momentum: Optional[int] = None
    p2_momentum: Optional[int] = None

    # Step 4.2 v2 (v2.1.0) — trend direction of the leader's lead over the
    # most recent 6 points. One of "extending" / "holding" / "closing".
    # Computed by api_tennis_worker via momentum.compute_trend() on every
    # frame. None when point_history is empty (no signal). When the match
    # has data but no clear leader, defaults to "holding" — the frontend
    # only renders this inside the leader pill, so non-leader values are
    # captured for state-log analysis but not visible.
    momentum_trend: Optional[str] = None

    # MI version label (e.g. "MI.1") — the parameter-set version of the
    # momentum indicator at the moment this Match's momentum was computed.
    # Set on every frame from momentum.MI_VERSION so the snapshot recorder
    # and trade attribution can capture which parameter regime each signal
    # came from. See momentum.MI_REGISTRY for the parameter dump per label.
    momentum_indicator_version: Optional[str] = None

    # Step 5 — surface classification + Sackmann-derived pre-match data.
    # Populated by api_tennis_worker on every frame (mutation-in-place):
    #   surface: from tournament_surface.classify_surface(tournament_name)
    #   p1_pre_pct / p2_pre_pct: from sackmann.match_probability with
    #     surface-aware Elo blend (50/50 overall + surface)
    #   p1_rank / p2_rank: from sackmann.lookup_ranking
    # All None when player not found in Sackmann data, or surface unknown.
    # Frontend uses these for: pre-match edge badge (compares pre_pct to
    # current Polymarket price_cents) and ranking display next to names.
    surface: Optional[str] = None
    p1_pre_pct: Optional[int] = None
    p2_pre_pct: Optional[int] = None
    p1_rank: Optional[int] = None
    p2_rank: Optional[int] = None

    # Step 3.2 (retention rename, expanded scope in Step 4) — recent
    # point-by-point history for the momentum indicator. List of
    # API-Tennis pointbypoint game entries: last ~16 games across set
    # boundaries (rolling window above the indicator's 12-point need).
    # Each entry shape: {set_number, number_game, player_served,
    # serve_winner, serve_lost, score, points: [...]}.
    point_history: list[dict] = field(default_factory=list)

    # Step 9-A C1 (v2) — operator's current open position on each side
    # of the match. Populated by the resolver loop via player-name
    # overlap between Polymarket position outcome and match player
    # names. None on a side means the operator does not currently hold
    # that side. Net P&L is computed CLIENT-SIDE from streaming prices,
    # not stored here.
    p1_position: Optional[Position] = None
    p2_position: Optional[Position] = None

    # PM-D.3/D.4 unfilled-orders feature — operator's resting limit
    # orders on each side of the match. Each side may carry zero, one,
    # or many orders (multiple price levels, or buy + sell on same
    # player). Populated by the resolver loop via player-name overlap
    # between Polymarket order outcome (marketMetadata.outcome) and
    # match player names — same join strategy as positions.
    #
    # Per-entry shape mirrors state.open_orders (see below). Empty list
    # on a side means no resting orders. Sort: closest-to-fill at top
    # (sells lowest price first; buys highest price first).
    p1_orders: list[dict] = field(default_factory=list)
    p2_orders: list[dict] = field(default_factory=list)


# Global match state. Worker mutates; endpoints read.
matches: dict[str, Match] = {}

# Last-event-arrived timestamps (epoch ms) per upstream source.
# None means "no event has arrived from that source yet this process."
# api_tennis: updated on every WS frame received from API-Tennis,
#   regardless of whether the frame contains data for any match we
#   care about. Heartbeat-style activity counts.
# polymarket: Phase 1C onward. Stays None until then.
source_timestamps: dict[str, Optional[int]] = {
    "api_tennis": None,
    "polymarket": None,
}

# Process start time (epoch ms). Captured at module import — i.e. at
# process startup. Stable for the life of the process; resets to "now"
# when the process restarts. Surfaced in snapshot() so the dashboard can
# render an uptime badge. Combined with the WS watchdog (v0.6.11), an
# unexpected drop in uptime signals "watchdog auto-restarted, investigate."
import time as _time
process_started_ms: int = int(_time.time() * 1000)


# Step 9-A C1 (v2) — operator's open positions, as a flat list of dicts.
# NOT keyed by slug because the slug returned by the positions API does
# not generally match the slug discovery registers (positions API gives
# per-side slugs; discovery only registers asset_index 0 slugs). Instead
# the resolver iterates this list and joins via player-name overlap to
# match.p1.name / match.p2.name — same strategy as price assignment.
#
# Per-entry shape:
#   {
#     "outcome": str,                # Player name from Polymarket
#                                     # marketMetadata.outcome — e.g.
#                                     # "Carlos Alcaraz". Used for name-
#                                     # overlap join in resolver.
#     "net_shares": int,
#     "cost_cents": int,
#     "cash_value_cents": int,
#     "realized_cents": int,
#     "update_time": str | None,
#     "event_slug": str | None,      # Polymarket eventSlug (event-level,
#                                     # shared across both sides). Logged
#                                     # for diagnostics but not used as
#                                     # join key — name overlap is more
#                                     # robust than relying on Polymarket
#                                     # eventSlug semantics being stable.
#     "title": str | None,
#   }
open_positions: list[dict] = []


# PM-D.3/D.4 unfilled-orders feature — operator's resting limit orders.
# Single-writer (the orders polling loop in polymarket_worker), atomic
# replace per cycle. Read by the resolver to attach to matches via the
# outcome → player-name overlap join (same strategy as positions). The
# resolver also reads this list to populate match.p1_orders/p2_orders.
#
# Filtered to ORDER_TYPE_LIMIT only — market orders aren't "resting" by
# definition; they execute on submit. Closed/cancelled orders fall off
# the SDK response naturally and disappear from the dashboard within
# one poll cycle.
#
# v0.7.3: per-entry shape carries BOTH operator-perspective and raw
# routed-side fields. Operator-perspective is what the iPhone receipt
# shows and what the dashboard renders. Raw is preserved for diagnostic
# and trade-attribution use. See docs/trade-data-semantics.md for the
# LONG/SHORT routing rules — the operator never places SELL orders, so
# resting limit orders are always BUY from the operator's perspective
# regardless of how Polymarket's order book routed them.
#
# Per-entry shape:
#   {
#     "id": str,                    # Polymarket order ID, stable
#     "outcome": str,               # Player name — join key (op-bought player)
#     # Operator-perspective fields (rendered by dashboard):
#     "side": "BUY",                # Always "BUY" — operator never sells
#     "price_cents": int,           # Operator-perspective price (0-100):
#                                   #   LONG  → raw price as-is
#                                   #   SHORT → 100 − raw price (complement)
#     # Raw routed-side fields (diagnostic / recorder):
#     "raw_side": "BUY" | "SELL",   # SDK side field (routing direction)
#     "raw_price_cents": int,       # SDK price field (routed-side price)
#     "intent": str,                # ORDER_INTENT_BUY_LONG / BUY_SHORT / etc.
#     "direction": "LONG" | "SHORT", # Derived from intent suffix
#     # Quantities and metadata:
#     "quantity": int,              # Original order size in shares
#     "cum_quantity": int,          # Filled so far
#     "leaves_quantity": int,       # Remaining to fill
#     "state": str,                 # "NEW" | "PARTIALLY_FILLED" | etc.
#     "insert_time": str | None,    # ISO timestamp; renders as age
#     "event_slug": str | None,     # Diagnostics only, not join key
#   }
open_orders: list[dict] = []


def snapshot() -> dict:
    """Return the current state for the dashboard.

    Shape:
        {
          "matches": [<match dict>, ...],   # sorted by scheduled
                                            # start_time, ascending,
                                            # across all statuses
                                            # (v0.8.3 — see operator
                                            # note in the sort block)
          "source_timestamps": {            # epoch ms or null per source
            "api_tennis": <int|null>,
            "polymarket": <int|null>,
          },
          "momentum_indicator": {           # MI bundle currently active
            "version": "MI.1",
            "parameters": {<full MI bundle from MI_REGISTRY>},
          },
          "process_started_ms": <int>,      # epoch ms, captured at module
                                            # import; stable for the life
                                            # of the process. Frontend
                                            # renders uptime badge from
                                            # (now - this).
        }

    The momentum_indicator block lets the frontend render an
    operator-facing legend footnote showing the live MI label and
    parameters. Single source of truth — backend MI_VERSION change
    propagates to the legend on next snapshot push.

    process_started_ms surfaces the worker's current uptime to the
    dashboard. Combined with the WS watchdog (v0.6.11), an unexpected
    uptime drop signals "process auto-restarted; check logs."
    """
    # Lazy import to avoid circular: state module is foundational and
    # shouldn't have import-time dep on the indicator modules.
    try:
        from . import momentum
        mi_block = {
            "version": momentum.MI_VERSION,
            "parameters": momentum.current_mi_parameters(),
        }
    except Exception:
        # If momentum module fails to load (shouldn't happen in prod),
        # surface a null block rather than crash the snapshot.
        mi_block = None

    # v0.8.3: stable single-list sort by scheduled start_time across
    # both live AND upcoming matches. Previously: live matches were
    # listed first in dict-insertion order, with upcoming after sorted
    # by start_time. That caused live rows to reshuffle as new matches
    # went live, making it hard for the operator to keep visual track
    # of any given match. With a single chronological sort, rows hold
    # their position regardless of status transitions. Live and
    # upcoming both have start_time populated (api_tennis_worker
    # v0.8.3 change). Matches with no start_time (rare data quality
    # issues) sort to the top via the empty-string fallback.
    all_matches = sorted(
        matches.values(),
        key=lambda m: m.start_time or "",
    )
    return {
        "matches": [asdict(m) for m in all_matches],
        "source_timestamps": dict(source_timestamps),
        "momentum_indicator": mi_block,
        "process_started_ms": process_started_ms,
    }
