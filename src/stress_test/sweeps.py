"""
sweeps — the §7 Q3=(c) main-sweeps harness against the Polymarket US Markets
WebSocket.

WHAT THIS MODULE DOES

1. Entry point for main-sweeps execution on the isolated pm-tennis-stress-test
   Render service. Extends probe.py's one-slug probe to a grid of connection
   and subscription counts, measuring the five empirical questions §16 names.
2. Two modes, gated by CLI flag:
     - self-check (default): verify credentials load and SDK surfaces
       import. Does NOT touch the network. Safe to run every service boot.
       Parallels probe.py's self-check.
     - sweep (--sweep=subscriptions|connections|both): execute the sweep
       cells per §16.5 — connect, subscribe, observe per cell, emit a
       SweepRunOutcome JSON with one SweepCellOutcome record per cell.

SCOPE — WHAT THIS MODULE DOES NOT DO

- Does NOT read /data/matches/. The isolated Render stress-test service has
  no access to the disk (D-027, §15.2). Anchor slug source for default cells
  is client.markets.list() via the SDK; fallback is operator-supplied
  --seed-slug (parallels probe.py --slug).
- Does NOT modify pm-tennis-api/requirements.txt (D-024 commitment 1).
- Does NOT touch Phase 2 code (D-016 commitment 2).
- Does NOT write tick content to disk (§7 Q1=(a); §16.5 no-disk-writes).
- Does NOT mock the SDK in unit tests (D-021; H-012 addendum; H-008 root
  cause). Unit tests exercise non-network paths only; the network-touching
  path is exercised at live smoke time (H-021).

AUTHORITATIVE CITATIONS (every SDK symbol or wire value below traces to one)

[E] github.com/Polymarket/polymarket-us-python README (re-fetched H-020
    per §16.9 step 1; baseline unchanged from H-019's fetch at 10 commits
    on main; polymarket-us==0.1.2 still current). Surfaces used by this
    module:
    - client.markets.list(params?) — public endpoint, paged, returns dict
      with "markets" key; used to source real anchor slugs for 1+99
      default composition. Takes optional params dict with "limit",
      "offset" and similar filter fields analogous to events.list.
    - client.ws.markets() — factory for one markets WebSocket instance.
      M2 (§16.4) is the empirical question of whether N calls to this
      on one client produce N independent instances.
    - markets_ws.connect() / subscribe(request_id, subscription_type,
      market_slugs_list) / close() — async methods, same shape probe.py
      cites [A].
    - markets_ws.on(event_name, fn) — sync handler registration; six
      events per [A]: market_data, market_data_lite, trade, heartbeat,
      error, close.
    - README Error Handling example imports six exception types:
      AuthenticationError, APIConnectionError, APITimeoutError,
      BadRequestError, NotFoundError, RateLimitError. This list is an
      illustrative import example, not an exhaustive enumeration of
      exception classes the SDK exports. For the complete exception
      surface (twelve classes), see [I] below and D-033.

[F] docs.polymarket.us/api-reference/websocket/markets (re-fetched H-020).
    - Subscription Limits verbatim: "You can subscribe to a maximum of
      100 markets per subscription. Use multiple subscriptions if you
      need more."  — the hard documented cap the 100-slug-per-subscription
      default targets exactly.
    - Subscribe message wire shape: subscribe envelope with requestId,
      subscriptionType, marketSlugs, optional responsesDebounced. §16.5
      commits to NOT setting responsesDebounced (leave default / false)
      so sweeps measure maximum per-subscription message volume under
      load.

[G] libraries.io/pypi/polymarket-us (re-fetched H-020). polymarket-us==0.1.2
    still latest on PyPI (2 releases total, both 2026-01-22). Pin per
    src/stress_test/requirements.txt is current-against-upstream.

[H] docs/clob_asset_cap_stress_test_research.md §16 (H-019 main-sweeps-scope
    addendum; operator-accepted H-019 close; frozen at H-019). §16 is the
    design source of truth for this module:
      §16.1 fetch record (H-019 baseline; H-020 re-fetch in module header).
      §16.2 inherited rulings (D-018..D-031).
      §16.3 100-slug cap re-citation.
      §16.4 five measurement questions M1..M5.
      §16.5 harness design + 1+99 default + 100P/0R M4 control cell.
      §16.6 outcome record shapes.
      §16.7 seven-step classification precedence list.
      §16.8 acceptance bar.
      §16.9 session-close discipline for the code turn.
      §16.10 what §16 does not decide.
      §16.11 what §16 does not change.

[I] polymarket-us==0.1.2 installed module public surface (introspected
    H-020; polymarket_us.__all__ and polymarket_us/errors.py source read
    at /usr/local/lib/python3.12/dist-packages/polymarket_us/). This is
    the authoritative public-API declaration — broader than [E]'s README
    Error Handling import example. Recorded here so classifier frozenset
    membership traces to a specific source at code-read time. See D-033
    for the revision history and assignment reasoning.

    polymarket_us.__all__: PolymarketUS, AsyncPolymarketUS,
    PolymarketUSError, APIError, APIConnectionError, APITimeoutError,
    APIStatusError, AuthenticationError, BadRequestError,
    PermissionDeniedError, NotFoundError, RateLimitError,
    InternalServerError, WebSocketError — 14 entries, 12 of them
    exception classes.

    Exception hierarchy rooted at PolymarketUSError (inherits Exception):
      PolymarketUSError
      ├── APIError
      │   ├── APIConnectionError                [README] → transport
      │   │   └── APITimeoutError               [README] → transport
      │   └── APIStatusError (HTTP 4xx/5xx base)
      │       ├── BadRequestError (400)         [README] → rejected
      │       ├── AuthenticationError (401)     [README] → rejected
      │       ├── PermissionDeniedError (403)             → rejected
      │       ├── NotFoundError (404)           [README] → rejected
      │       ├── RateLimitError (429)          [README] → rejected
      │       └── InternalServerError (500+)              → transport
      └── WebSocketError                                  → transport

    Base classes (APIError, APIStatusError, PolymarketUSError) are not
    assigned to either frozenset — they are abstract and not raised
    directly under normal SDK behavior. If one does raise, catch-all in
    classify_cell routes to exception (defensive).

    Classifier frozensets (see DOCUMENTED_REJECTED_EXCEPTION_TYPES and
    DOCUMENTED_TRANSPORT_EXCEPTION_TYPES below) assign the eight non-base
    leaf types plus asyncio.TimeoutError's qualname per the HTTP-semantic
    partition (4xx client-refusal → rejected; 5xx server-infrastructure
    + transport + WS-layer → transport).

ENVIRONMENT VARIABLES READ

- POLYMARKET_US_API_KEY_ID (required for --sweep; optional for self-check).
  Canonical D-023 name; the README's illustrative POLYMARKET_KEY_ID /
  POLYMARKET_SECRET_KEY are not accepted here (see probe.py lines 200-204).
- POLYMARKET_US_API_SECRET_KEY (required for --sweep; optional for
  self-check).
- SWEEP_OBSERVATION_SECONDS (optional; default 30.0 per §16.10's "sweeps may
  want longer" note; clamped to [1.0, 300.0]).

NOT DONE HERE (deferred to H-021 per H-020 cut)

- Live smoke run against actual gateway. The acceptance-bar items 3 and 4
  per §16.8 defer to the session that runs the smoke (H-021 expected per
  one-deliverable-per-session pattern).
- §17 or further-additive research-doc addendum interpreting main-sweeps
  outcomes. Written after live smoke is in hand.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Exit codes. Parallels probe.py's exit-code convention but distinct values
# where the semantics diverge. Probe's EXIT_OK (0), EXIT_CONFIG_ERROR (10),
# EXIT_NO_CANDIDATE (11) are preserved; sweep-specific codes get 4-9 range.
EXIT_OK = 0
EXIT_SWEEP_FAILED = 4              # one or more cells rejected or exception
EXIT_SWEEP_PARTIAL = 5             # some cells degraded, none rejected/exception
EXIT_SWEEP_AMBIGUOUS = 6           # one or more cells ambiguous, none rejected/exception
EXIT_CONFIG_ERROR = 10
EXIT_NO_ANCHOR_SLUG = 12           # sweep mode requires anchor slug; markets.list() empty and no --seed-slug


log = logging.getLogger("stress_test.sweeps")


# ---------------------------------------------------------------------------
# Wire-format constants — per citation [E]/[F]
# ---------------------------------------------------------------------------

# Per citation [E]/[A]. Literal string is the enum the SDK/server accept.
# Named constant rather than scattered literals — changes are load-bearing.
SUBSCRIPTION_TYPE_MARKET_DATA = "SUBSCRIPTION_TYPE_MARKET_DATA"

# Per citation [F]: "You can subscribe to a maximum of 100 markets per
# subscription." This is THE documented cap. §16.3 anchors the 100-slug
# default against it; §16.5 uses 100 as default slugs_per_subscription.
DOCUMENTED_SLUGS_PER_SUBSCRIPTION_CAP = 100


# ---------------------------------------------------------------------------
# Defaults — per §16.5 and §16.10
# ---------------------------------------------------------------------------

# Default observation window per cell. §16.10 names this explicitly as a
# code-turn decision: probe.py's 10s default is likely too short for sweeps
# because aggregate message volume is the measurement. 30s gives reasonable
# data without extending total sweep runtime beyond §16.5's ~30-minute
# documented envelope.
DEFAULT_OBSERVATION_SECONDS = 30.0

# Per-cell observation-second bounds. Sanity clamp mirrors probe.py's
# ProbeConfig clamping pattern (probe.py lines 222-225).
MIN_OBSERVATION_SECONDS = 1.0
MAX_OBSERVATION_SECONDS = 300.0

# Sweep grid axes per §7 Q3=(c) and §16.5. Axis values are defaults; CLI
# surface does not allow overriding these in H-020's cut (committed grid
# shape; code-turn does not redesign it).
SUBSCRIPTIONS_AXIS_VALUES = (1, 2, 5, 10)
CONNECTIONS_AXIS_VALUES = (1, 2, 4)

# Default slug composition per §16.5: 1 real anchor + 99 placeholders.
DEFAULT_REAL_SLUGS_PER_SUBSCRIPTION = 1
DEFAULT_PLACEHOLDER_SLUGS_PER_SUBSCRIPTION = 99

# M4 control cell per §16.5: pure-placeholder composition, single-subscribe,
# single-connection. Flagged via cell_id and SubscribeObservation.real_slug="".
M4_CONTROL_CELL_ID = "m4-control-100p-0r"
M4_CONTROL_PLACEHOLDER_COUNT = 100
M4_CONTROL_REAL_COUNT = 0


# ---------------------------------------------------------------------------
# Config loading — parallels probe.py's load_probe_config
# ---------------------------------------------------------------------------


@dataclass
class SweepConfig:
    """Runtime configuration for a sweep invocation.

    Built from environment variables + CLI args. Credential values are
    stored here only in-process; they are never logged, never serialized to
    the outcome record, never returned in any user-visible surface. Mirrors
    probe.py's ProbeConfig discipline.
    """
    key_id: str
    secret_key: str
    observation_seconds: float


def load_sweep_config() -> SweepConfig:
    """Read required env vars for sweep mode. Raises KeyError on missing
    required vars; the caller is expected to translate this to
    EXIT_CONFIG_ERROR and a stderr message that names the variables.

    Env var names are the D-023 canonical names, the same probe.py uses
    (probe.py lines 200-215). The [E] README's illustrative
    POLYMARKET_KEY_ID / POLYMARKET_SECRET_KEY names are NOT accepted here.
    """
    key_id = os.environ.get("POLYMARKET_US_API_KEY_ID", "")
    secret_key = os.environ.get("POLYMARKET_US_API_SECRET_KEY", "")
    if not key_id or not secret_key:
        missing = []
        if not key_id:
            missing.append("POLYMARKET_US_API_KEY_ID")
        if not secret_key:
            missing.append("POLYMARKET_US_API_SECRET_KEY")
        raise KeyError(
            f"required environment variable(s) not set: {', '.join(missing)}"
        )
    try:
        observation_seconds = float(
            os.environ.get("SWEEP_OBSERVATION_SECONDS", DEFAULT_OBSERVATION_SECONDS)
        )
    except ValueError:
        observation_seconds = DEFAULT_OBSERVATION_SECONDS
    # Sanity clamp mirrors probe.py.
    if (
        observation_seconds < MIN_OBSERVATION_SECONDS
        or observation_seconds > MAX_OBSERVATION_SECONDS
    ):
        observation_seconds = DEFAULT_OBSERVATION_SECONDS
    return SweepConfig(
        key_id=key_id,
        secret_key=secret_key,
        observation_seconds=observation_seconds,
    )


# ---------------------------------------------------------------------------
# Grid specification — the cells §16.5 commits to
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CellSpec:
    """One grid cell to execute.

    A cell fully specifies one sweeps measurement: which axis, how many
    connections, how many subscriptions per connection, how the slug
    composition shapes up. The grid is enumerated deterministically from
    axis values (and the M4 control cell) so runs are reproducible.

    Fields:
      cell_id: human-readable identifier (e.g., "subscriptions-axis-n5",
        "connections-axis-n4", "m4-control-100p-0r"). Appears in
        SweepCellOutcome.cell_id for traceability.
      cell_axis: "subscriptions" or "connections" for main-grid cells;
        "m4-control" for the dedicated M4 control cell.
      cell_axis_value: N for the axis (e.g., 5 for subscriptions-axis-n5).
        For the M4 control cell this is 1 (single subscribe).
      connection_count: how many markets_ws instances this cell opens.
      subscriptions_per_connection: how many subscribe calls per connection.
      real_slugs_per_subscription: count of real anchor slugs (default 1,
        M4 control 0).
      placeholder_slugs_per_subscription: count of placeholder slugs
        (default 99, M4 control 100).
      is_m4_control: true only for the dedicated control cell; activates
        §16.7's relaxed-clean special case.

    Per-cell slug count is real + placeholder, always 100 in the committed
    grid (either 1+99 or 0+100).
    """
    cell_id: str
    cell_axis: str  # "subscriptions" | "connections" | "m4-control"
    cell_axis_value: int
    connection_count: int
    subscriptions_per_connection: int
    real_slugs_per_subscription: int
    placeholder_slugs_per_subscription: int
    is_m4_control: bool = False

    @property
    def slugs_per_subscription(self) -> int:
        """Total slugs per subscribe call — always 100 in the committed grid."""
        return (
            self.real_slugs_per_subscription
            + self.placeholder_slugs_per_subscription
        )

    @property
    def intended_subscribe_count(self) -> int:
        """Total number of subscribe() calls this cell issues across all
        connections. Used as the denominator in §16.7's subscribe-success
        ratio classification.
        """
        return self.connection_count * self.subscriptions_per_connection


def build_default_grid() -> list[CellSpec]:
    """Enumerate the committed sweep grid per §16.5.

    Shape:
      - Subscriptions axis: 1/2/5/10 subscriptions × 1 connection ×
        (1 real + 99 placeholder) slugs each.
      - Connections axis: 1/2/4 connections × 1 subscription ×
        (1 real + 99 placeholder) slugs each. Note the n=1 entry
        duplicates the subscriptions-axis n=1 entry in shape; kept as a
        separate cell so per-axis sweeps are self-contained when run
        individually (--sweep=subscriptions or --sweep=connections).
      - M4 control cell: 1 connection × 1 subscription × (0 real +
        100 placeholder) slugs. Runs FIRST in --sweep=both sequencing per
        H-020 decision (H-019-Claude's letter guidance — if M4 fails hard
        rejection, subsequent cells' interpretation has that context).

    §16.5 commits to this exact shape. §16.10 explicitly names "grid
    internals" as NOT decided by §16 — but the grid SHAPE is fixed in
    §16.5 ("1/2/5/10 subscriptions × 1/2/4 concurrent connections,
    1 real anchor + 99 placeholder").

    Return order is the execution order when --sweep=both is used. Individual
    --sweep=subscriptions or --sweep=connections filters to the respective
    axis.
    """
    grid: list[CellSpec] = []

    # M4 control cell FIRST per H-020 sequencing decision.
    grid.append(
        CellSpec(
            cell_id=M4_CONTROL_CELL_ID,
            cell_axis="m4-control",
            cell_axis_value=1,
            connection_count=1,
            subscriptions_per_connection=1,
            real_slugs_per_subscription=M4_CONTROL_REAL_COUNT,
            placeholder_slugs_per_subscription=M4_CONTROL_PLACEHOLDER_COUNT,
            is_m4_control=True,
        )
    )

    # Subscriptions axis: vary subscriptions per connection, hold connection=1.
    for n in SUBSCRIPTIONS_AXIS_VALUES:
        grid.append(
            CellSpec(
                cell_id=f"subscriptions-axis-n{n}",
                cell_axis="subscriptions",
                cell_axis_value=n,
                connection_count=1,
                subscriptions_per_connection=n,
                real_slugs_per_subscription=DEFAULT_REAL_SLUGS_PER_SUBSCRIPTION,
                placeholder_slugs_per_subscription=DEFAULT_PLACEHOLDER_SLUGS_PER_SUBSCRIPTION,
                is_m4_control=False,
            )
        )

    # Connections axis: vary connection count, hold subscription=1 per connection.
    for n in CONNECTIONS_AXIS_VALUES:
        grid.append(
            CellSpec(
                cell_id=f"connections-axis-n{n}",
                cell_axis="connections",
                cell_axis_value=n,
                connection_count=n,
                subscriptions_per_connection=1,
                real_slugs_per_subscription=DEFAULT_REAL_SLUGS_PER_SUBSCRIPTION,
                placeholder_slugs_per_subscription=DEFAULT_PLACEHOLDER_SLUGS_PER_SUBSCRIPTION,
                is_m4_control=False,
            )
        )

    return grid


def filter_grid_by_sweep_selector(
    grid: list[CellSpec], sweep_selector: str
) -> list[CellSpec]:
    """Filter a full grid down to the cells the CLI --sweep selector activates.

    Selector values:
      "subscriptions" — subscriptions axis only. Excludes M4 control and
                        connections axis.
      "connections"   — connections axis only. Excludes M4 control and
                        subscriptions axis.
      "both"          — entire grid: M4 control first, then both axes.

    Any other value raises ValueError; the CLI parser restricts choices so
    this should not be reached at runtime from main().
    """
    if sweep_selector == "both":
        return list(grid)
    if sweep_selector == "subscriptions":
        return [c for c in grid if c.cell_axis == "subscriptions"]
    if sweep_selector == "connections":
        return [c for c in grid if c.cell_axis == "connections"]
    raise ValueError(
        f"unknown sweep selector {sweep_selector!r}; "
        "expected one of 'subscriptions', 'connections', 'both'"
    )


# ---------------------------------------------------------------------------
# Placeholder-slug synthesis — per §16.5
# ---------------------------------------------------------------------------

# Observed slug format from §13.2: aec-<tour>-<abbrev_a>-<abbrev_b>-<YYYY-MM-DD>.
# All lowercase, hyphen-separated, aec- prefix consistent across all 40
# surveyed slugs + the 5 probe-time slugs in §14.2. Tour values observed:
# "atp", "wta". Abbreviations are ~6 characters (e.g., "paubad", "julgra",
# "digsin", "meralk").
#
# Synthesis strategy (§16.5 flags this as format-matching deterministic;
# §16.10 flags the exact construction as a code-turn decision informed by
# M4 pilot observations):
#
#   - Keep the aec- prefix + tour slot (use "ph" for placeholder — clearly
#     non-real to a reader glancing at logs; NOT "atp"/"wta" which could
#     collide with real slugs).
#   - Two abbreviation slots, each 8 chars (1 more than observed ~6 max, so
#     placeholder slug namespace is structurally distinct from real slugs).
#   - Date slot: 2099-12-31 (far-future, explicitly distinguishable from any
#     real tennis match). Using a single fixed future date is deterministic
#     and recognizable in log output.
#   - Uniqueness disambiguator: the two 8-char abbreviation slots encode a
#     deterministic index (cell_id + subscription index + slug index hashed)
#     so no two placeholder slugs within a run collide.
#
# This approach is a first-pass commitment per §16.5. If M4 control cell
# results at H-021 live smoke show the rejection behavior is format-sensitive
# in a way this synthesis missed (e.g., the server hard-rejects on the "ph"
# tour token rather than on the slug-not-found lookup), a targeted DJ entry
# at that session revises the strategy before the next run.
PLACEHOLDER_SLUG_TOUR = "ph"
PLACEHOLDER_SLUG_DATE = "2099-12-31"
PLACEHOLDER_SLUG_ABBREV_LEN = 8


def synthesize_placeholder_slug(
    cell_id: str,
    subscription_index: int,
    slug_index_within_subscription: int,
) -> str:
    """Produce one deterministic placeholder slug per §16.5 synthesis rules.

    The output has format: aec-ph-<abbrev_a>-<abbrev_b>-2099-12-31

    Determinism: identical (cell_id, subscription_index, slug_index_within_
    subscription) tuples always produce the same slug. Two placeholders
    within a single subscription never collide (different
    slug_index_within_subscription); two placeholders across different
    subscriptions in the same cell never collide (different
    subscription_index); two placeholders across different cells never
    collide (different cell_id).

    The abbreviation slots are derived from a SHA-256 of the input tuple,
    mapped to an 8-character lowercase-hex substring each. SHA-256 is
    overkill for disambiguation but provides deterministic uniform
    distribution without requiring a seed-PRNG call per slug.
    """
    seed = f"{cell_id}|sub-{subscription_index}|slug-{slug_index_within_subscription}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    abbrev_a = digest[0:PLACEHOLDER_SLUG_ABBREV_LEN]
    abbrev_b = digest[PLACEHOLDER_SLUG_ABBREV_LEN : 2 * PLACEHOLDER_SLUG_ABBREV_LEN]
    return f"aec-{PLACEHOLDER_SLUG_TOUR}-{abbrev_a}-{abbrev_b}-{PLACEHOLDER_SLUG_DATE}"


def build_slug_list_for_subscription(
    cell: CellSpec,
    subscription_index: int,
    real_anchor_slug: str,
) -> list[str]:
    """Build the full 100-slug list for one subscribe() call within a cell.

    Layout:
      - First: the real anchor slug (if the cell uses 1 real slug per
        subscription — i.e., default cells, not the M4 control cell).
      - Remaining slots: deterministically-synthesized placeholders.

    For the M4 control cell (real_slugs_per_subscription == 0):
      - Entire list is 100 placeholders; real_anchor_slug is ignored.

    real_anchor_slug MUST be provided even for M4 control cells (the caller
    has already fetched it via markets.list() and it's cheap to pass); this
    function simply does not use it for M4 control.

    Total list length is always cell.slugs_per_subscription (100 in the
    committed grid).
    """
    slugs: list[str] = []

    if cell.real_slugs_per_subscription > 0:
        # Default cells: first slot is the real anchor slug.
        # If real_slugs_per_subscription were ever > 1, we'd need a list
        # of real slugs; current grid commits to at most 1 real per
        # subscription, so one anchor suffices.
        slugs.append(real_anchor_slug)

    # Fill remaining slots with synthesized placeholders.
    for slug_index in range(cell.placeholder_slugs_per_subscription):
        slugs.append(
            synthesize_placeholder_slug(
                cell_id=cell.cell_id,
                subscription_index=subscription_index,
                slug_index_within_subscription=slug_index,
            )
        )

    return slugs


# ---------------------------------------------------------------------------
# Outcome record shapes — per §16.6
# ---------------------------------------------------------------------------
#
# These four dataclasses transcribe §16.6's field-by-field specification.
# Field names and types follow §16.6 exactly; nothing is renamed, nothing is
# added that §16.6 doesn't name, nothing is elided. §16.6 leaves "optional vs
# required" details to the code turn — here the convention is:
#   - Fields that are always populated (even if with an empty value) have
#     default_factory-provided defaults (empty string, 0, empty list, empty
#     dict) so the dataclass can be constructed incrementally as the cell
#     runs. This mirrors probe.py's ProbeOutcome pattern (probe.py lines
#     135-183): start with defaults, fill fields as events happen.
#   - Fields §16.6 types as Optional[float] or Optional[str] keep Optional
#     typing and default to None (e.g., first_message_latency_seconds).
#
# First-message-preview truncation: §16.6 says "truncated repr, like
# probe.py". Probe.py uses 500 chars (probe.py line 400). Sweeps mirror.

PREVIEW_TRUNCATION_CHARS = 500


@dataclass
class SubscribeObservation:
    """One `subscribe()` call within a connection. Per §16.6.

    Field-by-field transcription:
      - request_id: str — the requestId sent on subscribe. For sweeps, a
        deterministic per-(sweep_id, cell_id, connection_index,
        subscription_index) string so per-request attribution via the
        marketSlug echo (§14.3) is reliable.
      - subscribe_sent: bool — whether await markets_ws.subscribe(...)
        returned without raising.
      - slugs: list[str] — the 100 slugs sent on this subscribe call.
      - real_slug: str — the 1 real anchor from markets.list(). Empty
        string for the M4 control cell (flagged per §16.5).
      - placeholder_slugs_count: int — 99 for default cells, 100 for the
        M4 control cell.
      - message_count_by_event: dict[str, int] — per-event-type totals for
        this subscription, keyed by the six event names ("market_data",
        "market_data_lite", "trade", "heartbeat", "error", "close").
      - per_slug_message_counts: dict[str, int] — attribution via the
        `marketSlug` echo observed in payloads (§14.3 confirmed at n=1
        that market_data payloads carry marketSlug as a payload field).
      - first_message_latency_seconds: Optional[float] — seconds from
        subscribe_sent=True to first payload on this subscription.
      - first_message_event: Optional[str] — event name of the first
        message received on this subscription.
      - first_message_preview: Optional[str] — truncated repr of the
        first payload, truncated to PREVIEW_TRUNCATION_CHARS.
    """
    request_id: str = ""
    subscribe_sent: bool = False
    slugs: list[str] = field(default_factory=list)
    real_slug: str = ""
    placeholder_slugs_count: int = 0
    message_count_by_event: dict[str, int] = field(default_factory=dict)
    per_slug_message_counts: dict[str, int] = field(default_factory=dict)
    first_message_latency_seconds: Optional[float] = None
    first_message_event: Optional[str] = None
    first_message_preview: Optional[str] = None


@dataclass
class ConnectionObservation:
    """One connection within a cell. Per §16.6.

    Field-by-field transcription:
      - connection_index: int — 0-based index of this connection within
        the cell's connection list. For single-connection cells always 0.
      - connected: bool — whether await markets_ws.connect() returned
        without raising.
      - subscribe_calls: list[SubscribeObservation] — one entry per
        subscribe() call issued on this connection, in subscribe order.
      - error_events: list[str] — truncated repr of each `error` event
        received on this connection, in arrival order. Same truncation
        policy as probe.py (probe.py lines 418-423).
      - close_events: list[str] — truncated repr of each `close` event.
      - closed_cleanly: bool — whether await markets_ws.close() returned
        without raising at cell teardown. Mid-observation close events
        appear in close_events regardless.
    """
    connection_index: int = 0
    connected: bool = False
    subscribe_calls: list[SubscribeObservation] = field(default_factory=list)
    error_events: list[str] = field(default_factory=list)
    close_events: list[str] = field(default_factory=list)
    closed_cleanly: bool = False


@dataclass
class SweepCellOutcome:
    """One sweep cell's observation record. Per §16.6.

    Field-by-field transcription (cell-level metadata + connections +
    classification + measurement-question resolutions + exception capture):

      Identity:
        - sweep_id: str — identifier of the parent run this cell belongs to.
        - cell_id: str — per §16.5 convention (e.g., "subscriptions-axis-n5").
        - cell_axis: str — "subscriptions" | "connections" per §16.6's
          enum. §16.5 adds a third value "m4-control" for the dedicated
          control cell; §16.6 does not enumerate that literally but §16.5
          is the authoritative cell-shape spec and the M4 control cell is
          named in §16.5. Using "m4-control" as the third enum value.
          (FLAG: surfaced at checkpoint 2 pause — §16.6 vs §16.5 enum
          mismatch for the M4 cell's cell_axis.)
        - cell_axis_value: int — N for the axis.
        - slugs_per_subscription: int — always 100 in committed grid.

      Timing:
        - cell_started_at_utc: str — ISO-8601 UTC at cell start.
        - cell_ended_at_utc: str — ISO-8601 UTC at cell end.
        - observation_window_seconds: float — config value for this cell.
        - elapsed_seconds: float — wall-clock time the cell took.

      Per-connection records:
        - connections: list[ConnectionObservation] — length == connection
          count for connections-axis cells; 1 for subscriptions-axis cells;
          1 for the M4 control cell.

      Classification:
        - cell_classification: str — one of "clean" | "degraded" |
          "rejected" | "exception" | "ambiguous" per §16.7.
        - cell_classification_reason: str — human-readable rule-trace.

      Measurement-question resolutions (all per-cell; aggregate resolutions
      live on SweepRunOutcome):
        - m1_resolution: Optional[str] — "compose" | "replace" | "error" |
          "ambiguous" | None (None if the cell does not test M1; only cells
          with intended_subscribe_count >= 2 test M1).
        - m2_resolution: Optional[str] — "independent" | "shared" | "error"
          | "ambiguous" | None (None if the cell does not test M2; only
          connections-axis cells with connection_count >= 2 test M2).
        - m3_observations: dict — first-message latency, per-slug message
          counts. Populated for all cells with a real anchor (every cell
          except M4 control).
        - m4_observations: dict — per-slug attribution for placeholder vs
          real. Populated for all cells; the M4 control cell is the clean
          measurement.
        - m5_observations: dict — per-connection connect/subscribe/message
          outcomes. Populated for all cells.

      Exception capture (mirror of probe.py's ProbeOutcome exception fields):
        - exception_type: str — type name of the exception that terminated
          the cell's critical path, or empty string if no exception.
        - exception_message: str — str(exc)[:PREVIEW_TRUNCATION_CHARS] if
          an exception was raised, empty otherwise.
    """
    sweep_id: str = ""
    cell_id: str = ""
    cell_axis: str = ""
    cell_axis_value: int = 0
    slugs_per_subscription: int = 0
    cell_started_at_utc: str = ""
    cell_ended_at_utc: str = ""
    observation_window_seconds: float = 0.0
    elapsed_seconds: float = 0.0
    connections: list[ConnectionObservation] = field(default_factory=list)
    cell_classification: str = ""
    cell_classification_reason: str = ""
    m1_resolution: Optional[str] = None
    m2_resolution: Optional[str] = None
    m3_observations: dict = field(default_factory=dict)
    m4_observations: dict = field(default_factory=dict)
    m5_observations: dict = field(default_factory=dict)
    exception_type: str = ""
    exception_message: str = ""


@dataclass
class SweepRunOutcome:
    """Full sweep invocation record. Per §16.6.

    Field-by-field transcription. Aggregate resolutions are synthesized
    from cells at run end (see aggregate_* helpers below §16.7 block).

      - run_id: str — the sweep_id shared by all cells in the run.
      - sweep_started_at_utc: str — ISO-8601 UTC at run start.
      - sweep_ended_at_utc: str — ISO-8601 UTC at run end.
      - cells: list[SweepCellOutcome] — one per cell executed.
      - m1_aggregate_resolution: str — synthesized across all cells that
        tested M1. See aggregate_m1_resolution below.
      - m2_aggregate_resolution: str — synthesized across all cells that
        tested M2. See aggregate_m2_resolution below.
      - m3_aggregate_summary: dict — per-N latency medians, etc. Summary
        computed at run end across cells' m3_observations.
      - m4_aggregate_summary: dict — placeholder-rejection behavior across
        cells. Summary computed at run end across cells' m4_observations.
      - m5_upper_bound: int — highest connection count observed to succeed
        cleanly. Derived from connections-axis cells with cell_classification
        == "clean".
      - run_classification: str — "clean" | "partial" | "failed" |
        "ambiguous" per §16.7 aggregate rules.
      - sdk_version: str — best-effort read from polymarket_us.__version__.
      - run_notes: str — free text for anomalies that don't fit structured
        fields. Concatenated during the run by helpers that notice
        surface-worthy but non-fatal conditions.
    """
    run_id: str = ""
    sweep_started_at_utc: str = ""
    sweep_ended_at_utc: str = ""
    cells: list[SweepCellOutcome] = field(default_factory=list)
    m1_aggregate_resolution: str = ""
    m2_aggregate_resolution: str = ""
    m3_aggregate_summary: dict = field(default_factory=dict)
    m4_aggregate_summary: dict = field(default_factory=dict)
    m5_upper_bound: int = 0
    run_classification: str = ""
    sdk_version: str = ""
    run_notes: str = ""


# ---------------------------------------------------------------------------
# Classification state machine — per §16.7
# ---------------------------------------------------------------------------
#
# The seven-step precedence list is transcribed from §16.7 verbatim. Each
# step below is annotated with the §16.7 rule it encodes. Two special cases
# are honored:
#
#   (a) Single-subscribe cells (intended_subscribe_count == 1): the ratio
#       degenerates to 0 or 1. 0 → `rejected` at step 3; 1 → candidate for
#       `clean` at step 5. No `degraded` is possible at N=1 by construction
#       (§16.7 paragraph on single-subscribe cells).
#
#   (b) M4 control cell (is_m4_control == True): relaxed `clean` — no
#       anchor-slug traffic is expected; `clean` requires only subscribe
#       success and no error events (§16.7 `clean` row, M4 caveat). Also
#       not-ambiguous-by-zero-traffic-alone (§16.7 `ambiguous` row, M4
#       caveat).
#
# Classification reason strings are machine-trace-friendly: they name the
# precedence-step number and the rule that fired, so a reader scanning a
# run's cells can reconstruct the classification path without re-running
# the logic.

# Documented SDK exception types per [A]/[E]/[I]. These map to `rejected` in
# the classification per §16.7 step 2 and the `rejected` row.
# Stored as type names (strings) rather than type objects so the
# classification function does not depend on importing the SDK — imports
# are deferred to the network-touching path per probe.py's pattern.
#
# Membership per D-033: 4xx client-error class under APIStatusError. Five
# leaf types — the four named in [E]'s README import example plus
# PermissionDeniedError (403) surfaced at H-020 SDK introspection. See
# [I] citation block above for the full exception hierarchy and D-033
# for the frozenset-assignment reasoning.
DOCUMENTED_REJECTED_EXCEPTION_TYPES: frozenset[str] = frozenset({
    "AuthenticationError",       # 401 — [README]
    "BadRequestError",           # 400 — [README]
    "NotFoundError",             # 404 — [README]
    "PermissionDeniedError",     # 403 — D-033 addition
    "RateLimitError",            # 429 — [README]
})

# Documented transport / infrastructure exception types. These map
# to `exception` classification per §16.7 step 1 / `exception` row.
#
# Membership per D-033: network/transport/infrastructure errors where
# the request either didn't reach the server, didn't complete, or
# failed server-side in a way the client request didn't cause. Five
# types — the two named in [E]'s README import example plus
# asyncio.TimeoutError's qualname, InternalServerError (5xx server-
# infrastructure failure), and WebSocketError (WS-layer transport).
# See [I] citation block above for the full exception hierarchy and
# D-033 for the frozenset-assignment reasoning.
DOCUMENTED_TRANSPORT_EXCEPTION_TYPES: frozenset[str] = frozenset({
    "APIConnectionError",        # network — [README]
    "APITimeoutError",           # request timeout — [README]
    "TimeoutError",              # asyncio.TimeoutError qualname (3.11+)
    "InternalServerError",       # 5xx server-side — D-033 addition
    "WebSocketError",            # WS-layer transport — D-033 addition
})


def _count_intended_and_observed_subscribes(
    cell_outcome: SweepCellOutcome,
) -> tuple[int, int]:
    """Return (intended, observed) subscribe counts for a cell.

    Intended is derived from cell_axis_value and the cell's shape (pulled
    from the CellSpec via cell_outcome's recorded values — cell_axis and
    the shape of connections list). Observed is the count of
    SubscribeObservation.subscribe_sent == True across all connections.

    Matches §16.7's threshold-denominator definition:
      - subscriptions-axis cells: cell_axis_value
      - connections-axis cells: connection_count × 1 per connection
                                (i.e., equals len(connections))
      - M4 control cell: 1
    """
    intended = sum(
        len(c.subscribe_calls) for c in cell_outcome.connections
    )
    # Intended is what the cell tried to do, not what it achieved; we can
    # read it off the SubscribeObservation list lengths because we always
    # append one SubscribeObservation per subscribe attempt (whether it
    # succeeded or raised).
    observed = sum(
        1
        for c in cell_outcome.connections
        for s in c.subscribe_calls
        if s.subscribe_sent
    )
    return intended, observed


def _cell_has_anchor_slug_traffic_qualifying(cell_outcome: SweepCellOutcome) -> bool:
    """Return True if any subscription's anchor slug received at least one
    `market_data`, `market_data_lite`, `trade`, or `heartbeat` message.

    Per §16.7 Reading B (D-032): clean-(iii) for default cells is
    anchor-slug-specific traffic, not cell-wide traffic. The Meaning
    column of §16.7's clean row says "message traffic received on the
    anchor slug(s) within the observation window"; the Rule column's
    broader phrasing ("at least one ... received across the cell") is an
    imprecise transcription of the Meaning column. Reading B preserves
    the Meaning column's intent and makes the §16.7 degraded-row
    anchor-zero-traffic anomaly textually consistent with precedence
    step 6.

    error and close events explicitly do NOT count as traffic (same as
    probe.py's `accepted` classification rule, probe.py lines 545-557).

    For the M4 control cell: real_slug is empty by construction (§16.5);
    this check would always return False. Callers must branch on
    is_m4_control before calling this — the M4 control cell has its own
    relaxed-clean path that does not require clean-(iii) at all per
    §16.7's M4 caveat.
    """
    for conn in cell_outcome.connections:
        for sub in conn.subscribe_calls:
            if not sub.real_slug:
                # No anchor to attribute traffic to (M4 control or
                # malformed). Not counted. Caller branches on
                # is_m4_control before reaching here for M4.
                continue
            counts = sub.per_slug_message_counts
            if counts.get(sub.real_slug, 0) > 0:
                # Any per-anchor-slug attribution counts: market_data,
                # market_data_lite, or trade messages carry the
                # marketSlug echo per §14.3. Heartbeat is connection-
                # level and does not carry a marketSlug; it does not
                # populate per_slug_message_counts for any specific slug.
                # So any nonzero per-anchor-slug count means real
                # subscription-attributable traffic arrived for the
                # anchor — which is what §16.5 specifies the anchor for.
                return True
    return False


def _cell_has_anchor_slug_traffic(cell_outcome: SweepCellOutcome) -> bool:
    """Alias preserved for _classify_exception's existing caller shape and
    for readability at step 6. Semantically identical to
    _cell_has_anchor_slug_traffic_qualifying — the "qualifying" name
    emphasizes the clean-(iii) reading at step 5; the unadorned name
    emphasizes the anomaly-check reading at step 6. Same function, same
    behavior, different sites of call.
    """
    return _cell_has_anchor_slug_traffic_qualifying(cell_outcome)


def _cell_has_error_events(cell_outcome: SweepCellOutcome) -> bool:
    """True if any connection in the cell has a non-empty error_events list."""
    return any(len(c.error_events) > 0 for c in cell_outcome.connections)


def _cell_has_close_events(cell_outcome: SweepCellOutcome) -> bool:
    """True if any connection in the cell has a non-empty close_events list.

    §16.7 `degraded` row names "close_events non-empty mid-window" as an
    anomaly; the check here is on any close event recorded during
    observation. Teardown-time close outcomes are tracked separately via
    ConnectionObservation.closed_cleanly and do not populate close_events.
    """
    return any(len(c.close_events) > 0 for c in cell_outcome.connections)


def _all_connections_connected(cell_outcome: SweepCellOutcome) -> bool:
    """True if every ConnectionObservation has connected == True.

    §16.7 `clean` row requires this as a precondition.
    """
    if not cell_outcome.connections:
        return False
    return all(c.connected for c in cell_outcome.connections)


def _classify_exception(exception_type: str) -> Optional[str]:
    """Map an exception type name to the classification it forces.

    Returns:
      "exception" — transport-layer or undocumented exception type
                    (§16.7 step 1, `exception` row).
      "rejected"  — documented SDK exception type
                    (§16.7 step 2, `rejected` row).
      None        — exception_type is empty (no exception raised).
    """
    if not exception_type:
        return None
    if exception_type in DOCUMENTED_TRANSPORT_EXCEPTION_TYPES:
        return "exception"
    if exception_type in DOCUMENTED_REJECTED_EXCEPTION_TYPES:
        return "rejected"
    # Catch-all — undocumented exception type. §16.7 `exception` row says
    # "catch-all (Exception matched with undocumented type name)" —
    # undocumented types take the `exception` branch, not `rejected`,
    # because a type we didn't anticipate is more likely a genuine bug
    # or a transport/SDK surface change than an expected user-level error.
    return "exception"


def classify_cell(
    cell_outcome: SweepCellOutcome,
    is_m4_control: bool,
) -> tuple[str, str]:
    """Apply the seven-step precedence list from §16.7. Returns
    (classification, reason).

    The caller passes is_m4_control separately because §16.6's
    SweepCellOutcome does not carry the flag directly (cell_axis ==
    "m4-control" is the signal in cell_axis, but keeping the flag in the
    classifier signature makes the special-case logic explicit and
    testable).

    The seven steps below are verbatim transcriptions of §16.7's
    precedence list. Each step's docstring comment cites the §16.7 rule.
    """
    intended, observed = _count_intended_and_observed_subscribes(cell_outcome)
    ratio = observed / intended if intended > 0 else 0.0

    # ---- Step 1: uncaught exception escaped the cell's execution → exception.
    # §16.7 precedence step 1. `exception_type` is populated by
    # _run_cell_async's exception handlers; an empty exception_type means
    # no exception was raised.
    #
    # Note on precedence: §16.7 step 1 encompasses anything that escaped
    # the cell's try/except structure. In practice _run_cell_async's
    # catch-all will populate exception_type with the uncaught type's
    # name, so this step fires via _classify_exception returning
    # "exception" for undocumented types. We test step-1 first by checking
    # for transport or undocumented exception types explicitly.
    forced = _classify_exception(cell_outcome.exception_type)
    if forced == "exception":
        return (
            "exception",
            f"step 1: cell raised transport or undocumented exception "
            f"{cell_outcome.exception_type!r}: {cell_outcome.exception_message}",
        )

    # ---- Step 2: documented SDK exception on critical path → rejected.
    # §16.7 precedence step 2. The six documented exception types are
    # enumerated in [A]/[E]. Four of them map to `rejected`
    # (AuthenticationError, BadRequestError, NotFoundError,
    # RateLimitError — see §16.7 `rejected` row). The other two
    # (APIConnectionError, APITimeoutError) map to `exception` and are
    # caught by step 1 above.
    if forced == "rejected":
        return (
            "rejected",
            f"step 2: documented SDK exception {cell_outcome.exception_type!r}: "
            f"{cell_outcome.exception_message}",
        )

    # ---- Step 3: subscribe ratio ≤ 0.5 → rejected.
    # §16.7 precedence step 3. For single-subscribe cells, ratio is 0 or
    # 1; 0 fires this step (correct per §16.7's single-subscribe-cells
    # paragraph: "0 → rejected"). For N>1 cells, ratio ≤ 0.5 means half
    # or fewer subscribes succeeded.
    if ratio <= 0.5:
        return (
            "rejected",
            f"step 3: subscribe ratio {observed}/{intended} "
            f"({ratio:.3f}) ≤ 0.5",
        )

    # ---- Step 4: subscribe ratio in (0.5, 1.0) exclusive → degraded.
    # §16.7 precedence step 4. Fires only for N≥2 cells where some but
    # not all subscribes succeeded. Cannot fire at N=1 (ratio is 0 or 1).
    if ratio < 1.0:
        return (
            "degraded",
            f"step 4: subscribe ratio {observed}/{intended} "
            f"({ratio:.3f}) in (0.5, 1.0) exclusive",
        )

    # At this point ratio == 1.0 (all intended subscribes succeeded).
    # Steps 5, 6, 7 separate `clean` from `degraded` from `ambiguous`
    # based on the `clean` precondition-set and the `degraded` anomaly
    # conditions.

    # ---- Step 5: ratio == 1.0 AND all clean conditions hold → clean.
    # §16.7 precedence step 5. The clean conditions per §16.7 `clean` row
    # (under Reading B per D-032):
    #   (i)   Every connection connected (connections[*].connected == True).
    #   (ii)  Subscribe ratio observed == intended (already established).
    #   (iii) For default cells: at least one market_data, market_data_lite,
    #         trade, or heartbeat received ON THE ANCHOR SLUG within the
    #         observation window. This is the Meaning column's phrasing of
    #         §16.7's clean row; the Rule column's "across the cell"
    #         phrasing is Reading-A and produces the operationally-
    #         unreachable-anomaly inconsistency D-032 resolves.
    #   (iv)  No error_events during observation.
    #   (v)   No close_events during observation.
    #
    # For M4 control cell (§16.7 `clean` row M4 caveat): clean is
    # relaxed — no anchor-slug traffic expected. The requirement becomes:
    #   (i')   Every connection connected.
    #   (ii')  Subscribe ratio observed == intended (already established).
    #   (iv')  No error_events.
    #   (v')   No close_events.
    # (iii) is NOT required for the M4 control cell.
    all_connected = _all_connections_connected(cell_outcome)
    has_errors = _cell_has_error_events(cell_outcome)
    has_closes = _cell_has_close_events(cell_outcome)

    if is_m4_control:
        # M4 control: relaxed clean (no traffic requirement).
        if all_connected and not has_errors and not has_closes:
            return (
                "clean",
                "step 5 (M4 control): subscribe ratio 1.0; all connections "
                "connected; no error or close events. Traffic not required "
                "(pure-placeholder composition, §16.7 M4 caveat).",
            )
    else:
        # Default cells: full clean conditions (i) through (v), with
        # (iii) anchor-specific per Reading B / D-032.
        has_anchor_traffic = _cell_has_anchor_slug_traffic_qualifying(cell_outcome)
        if (
            all_connected
            and has_anchor_traffic
            and not has_errors
            and not has_closes
        ):
            return (
                "clean",
                "step 5: subscribe ratio 1.0; all connections connected; "
                "anchor-slug traffic received (clean-(iii) per D-032 "
                "Reading B); no error or close events.",
            )

    # ---- Step 6: ratio == 1.0 AND some anomaly condition fires → degraded.
    # §16.7 precedence step 6. Anomaly conditions per §16.7 `degraded` row:
    #   - error_events non-empty during observation, OR
    #   - close_events non-empty mid-window, OR
    #   - anchor slug produced zero traffic across the observation window.
    #
    # For the M4 control cell: the "anchor slug zero traffic" anomaly does
    # not apply (there is no anchor slug by construction). Only error_events
    # and close_events are anomalies for the M4 control cell in this branch.
    if has_errors:
        return (
            "degraded",
            "step 6: subscribe ratio 1.0 but error_events fired during "
            f"observation ({sum(len(c.error_events) for c in cell_outcome.connections)} total).",
        )
    if has_closes:
        return (
            "degraded",
            "step 6: subscribe ratio 1.0 but close_events fired during "
            f"observation ({sum(len(c.close_events) for c in cell_outcome.connections)} total).",
        )
    if not is_m4_control:
        # Default cells: anchor slug zero traffic is an anomaly.
        if not _cell_has_anchor_slug_traffic(cell_outcome):
            return (
                "degraded",
                "step 6: subscribe ratio 1.0 but anchor slug produced zero "
                "traffic across the observation window.",
            )

    # ---- Step 7: ambiguous — none of the above rules resolved.
    # §16.7 precedence step 7. This should be rare in practice; it fires
    # when ratio == 1.0, no exceptions, no errors, no closes, for an M4
    # control cell that also had some other unexpected shape, OR for a
    # default cell that had anchor traffic but also some other edge case
    # the rules don't capture. §16.7 `ambiguous` row: "surface literally,
    # not silently collapsed" — D-025 commitment 4.
    return (
        "ambiguous",
        "step 7: ratio 1.0 and no clean-condition or degraded-condition "
        "rule resolved; surfacing literally per D-025 commitment 4.",
    )


# ---------------------------------------------------------------------------
# Run-level aggregation — per §16.7 final paragraph
# ---------------------------------------------------------------------------
#
# Sweep-run classification aggregates per-cell classifications per the
# §16.7 aggregate rules:
#   - `clean`    — every cell is clean.
#   - `partial`  — some cells clean, some degraded, none rejected/exception/ambiguous.
#   - `failed`   — one or more cells rejected or exception.
#   - `ambiguous` — one or more cells ambiguous and none rejected/exception.


def aggregate_run_classification(cells: list[SweepCellOutcome]) -> str:
    """Compute SweepRunOutcome.run_classification from the cells' classifications.

    Precedence (same ordering as §16.7 `failed` takes precedence over
    `ambiguous` takes precedence over `partial`):
      - `failed`    — any cell is rejected or exception.
      - `ambiguous` — any cell is ambiguous, and no cell is rejected/exception.
      - `partial`   — any cell is degraded, and no cell is rejected/exception/ambiguous.
      - `clean`     — every cell is clean.
      - Empty cells list → "ambiguous" (no observations is an ambiguous run
        outcome, not a clean one; surface literally).
    """
    if not cells:
        return "ambiguous"
    classifications = {c.cell_classification for c in cells}
    if "rejected" in classifications or "exception" in classifications:
        return "failed"
    if "ambiguous" in classifications:
        return "ambiguous"
    if "degraded" in classifications:
        return "partial"
    if classifications == {"clean"}:
        return "clean"
    # Unknown classification labels land here — defensive ambiguous rather
    # than assuming clean.
    return "ambiguous"


def aggregate_m1_resolution(cells: list[SweepCellOutcome]) -> str:
    """Synthesize SweepRunOutcome.m1_aggregate_resolution across cells.

    Only cells with a non-None m1_resolution contribute. Aggregate rules
    per §16.4 M1:
      - If any contributing cell resolved "error" → "error".
      - Else if any resolved "replace" → "replace" (contradicts any
        "compose" resolution; surface literally).
      - Else if any resolved "ambiguous" → "ambiguous".
      - Else if all resolved "compose" → "compose".
      - Else (no cells tested M1) → "not-tested".
    """
    contributing = [c.m1_resolution for c in cells if c.m1_resolution is not None]
    if not contributing:
        return "not-tested"
    if "error" in contributing:
        return "error"
    if "replace" in contributing:
        return "replace"
    if "ambiguous" in contributing:
        return "ambiguous"
    if set(contributing) == {"compose"}:
        return "compose"
    return "ambiguous"


def aggregate_m2_resolution(cells: list[SweepCellOutcome]) -> str:
    """Synthesize SweepRunOutcome.m2_aggregate_resolution across cells.

    Only cells with a non-None m2_resolution contribute. Aggregate rules
    per §16.4 M2:
      - If any contributing cell resolved "error" → "error".
      - Else if any resolved "shared" → "shared" (contradicts "independent").
      - Else if any resolved "ambiguous" → "ambiguous".
      - Else if all resolved "independent" → "independent".
      - Else (no cells tested M2) → "not-tested".
    """
    contributing = [c.m2_resolution for c in cells if c.m2_resolution is not None]
    if not contributing:
        return "not-tested"
    if "error" in contributing:
        return "error"
    if "shared" in contributing:
        return "shared"
    if "ambiguous" in contributing:
        return "ambiguous"
    if set(contributing) == {"independent"}:
        return "independent"
    return "ambiguous"


def aggregate_m5_upper_bound(cells: list[SweepCellOutcome]) -> int:
    """Compute SweepRunOutcome.m5_upper_bound: highest connection count
    observed to succeed cleanly across connections-axis cells.

    Per §16.4 M5: "The connection-count sweep... success across all three
    cells answers M5 as '≥4 concurrent OK'." The upper bound here is the
    highest `cell_axis_value` observed with cell_classification == "clean"
    among connections-axis cells.

    Returns 0 if no connections-axis cell was clean (including the case
    where connections-axis cells were not run).
    """
    upper = 0
    for c in cells:
        if c.cell_axis == "connections" and c.cell_classification == "clean":
            if c.cell_axis_value > upper:
                upper = c.cell_axis_value
    return upper


# ---------------------------------------------------------------------------
# Self-check mode — no network, parallels probe.py's run_self_check
# ---------------------------------------------------------------------------
#
# Mirrors probe.py lines 238-330. The sweeps self-check verifies the same
# things probe.py does (SDK import, core SDK surfaces importable, credential
# env vars present by name) plus one additional check: that markets.list()
# exists as an attribute on the client's markets namespace. This is the
# first net-new SDK surface beyond probe.py's [A]-[D] block.
#
# Deliberately does NOT construct an SDK client (same reason as probe.py:
# construction might perform eager authentication work that touches the
# network or logs credential material).
#
# Exit 0 on success; non-zero on the first failed check (EXIT_CONFIG_ERROR).


def run_self_check() -> int:
    """Verify imports, credential presence (by name only), and required
    SDK surfaces are importable. No network, no client construction.

    Parallels probe.py's run_self_check. Returns EXIT_OK or
    EXIT_CONFIG_ERROR.
    """
    print("=== pm-tennis stress-test sweeps self-check ===", file=sys.stderr)

    # --- Step 1: can we import the SDK at all?
    try:
        import polymarket_us  # noqa: F401

        version = getattr(polymarket_us, "__version__", "<no __version__>")
        print(f"[ok] polymarket_us import ok (version: {version})", file=sys.stderr)
    except ImportError as exc:
        print(f"[FAIL] polymarket_us import failed: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # --- Step 2: can we import the SDK surfaces sweeps will use?
    # These are the same six exception types probe.py imports, plus
    # AsyncPolymarketUS. Sweeps uses the same six exception types at
    # classification time (via DOCUMENTED_*_EXCEPTION_TYPES string sets,
    # but import-checking at self-check time surfaces SDK-surface drift
    # before the network-touching path fires).
    try:
        from polymarket_us import AsyncPolymarketUS  # noqa: F401
        from polymarket_us import (  # noqa: F401
            APIConnectionError,
            APITimeoutError,
            AuthenticationError,
            BadRequestError,
            NotFoundError,
            RateLimitError,
        )

        print(
            "[ok] SDK surfaces AsyncPolymarketUS + six exception types importable",
            file=sys.stderr,
        )
    except ImportError as exc:
        print(f"[FAIL] SDK surface import failed: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # --- Step 3: credentials present (by name only — values are not logged).
    key_id_present = bool(os.environ.get("POLYMARKET_US_API_KEY_ID"))
    secret_present = bool(os.environ.get("POLYMARKET_US_API_SECRET_KEY"))
    print(
        f"[{'ok' if key_id_present else 'warn'}] "
        f"POLYMARKET_US_API_KEY_ID {'set' if key_id_present else 'NOT SET'}",
        file=sys.stderr,
    )
    print(
        f"[{'ok' if secret_present else 'warn'}] "
        f"POLYMARKET_US_API_SECRET_KEY {'set' if secret_present else 'NOT SET'}",
        file=sys.stderr,
    )
    # Missing credentials are a warning in self-check, not a failure.
    # sweep mode errors out explicitly if they're absent.

    # --- Step 4: sweep-specific — verify the markets.list attribute path
    # exists on an AsyncPolymarketUS instance's client.markets namespace.
    # We do NOT construct the client (no credentials, no network); we
    # verify the attribute path exists at the class level. If the SDK has
    # moved the method to a different location (or renamed it), this
    # surface fails here rather than at live-smoke time.
    try:
        # Instance attribute access without construction: check the class's
        # type hints or inspect the module. The safest check is just to
        # verify the module has AsyncPolymarketUS and an inspect-level
        # look at whether a 'markets' attribute is declared. polymarket-us
        # 0.1.2 defines markets as an instance attribute populated in
        # __init__; we cannot inspect it without construction.
        #
        # Fall back to a weaker check: verify the 'markets' sub-module
        # or class exists in the package namespace. Per [E] the SDK's
        # layout has MarketsClient (or similar) as a construction-time
        # attribute, not a module-level import.
        #
        # Since we cannot verify markets.list without constructing,
        # log informationally that the check is deferred to first real
        # invocation. This is honest: self-check cannot prove the surface
        # without hitting the network.
        import polymarket_us as _pm

        attrs = dir(_pm)
        has_async_client = "AsyncPolymarketUS" in attrs
        print(
            f"[info] markets.list() surface verification deferred to live "
            f"invocation (cannot inspect instance attributes without "
            f"constructing the client; AsyncPolymarketUS "
            f"{'present' if has_async_client else 'MISSING'} in package namespace)",
            file=sys.stderr,
        )
    except Exception as exc:
        print(
            f"[warn] SDK introspection raised (non-fatal): {exc!r}",
            file=sys.stderr,
        )

    # --- Step 5: sweep grid sanity check — pure-logic verification.
    # Builds the default grid and the M4 control cell; no network.
    # Confirms the grid shape matches §16.5 commitments.
    grid = build_default_grid()
    m4_present = any(c.is_m4_control for c in grid)
    cells_by_axis = {
        "subscriptions": sum(1 for c in grid if c.cell_axis == "subscriptions"),
        "connections": sum(1 for c in grid if c.cell_axis == "connections"),
        "m4-control": sum(1 for c in grid if c.cell_axis == "m4-control"),
    }
    all_100_slugs = all(c.slugs_per_subscription == 100 for c in grid)
    print(
        f"[{'ok' if m4_present and all_100_slugs else 'FAIL'}] "
        f"grid shape: {len(grid)} cells "
        f"(subs={cells_by_axis['subscriptions']}, "
        f"conns={cells_by_axis['connections']}, "
        f"m4-control={cells_by_axis['m4-control']}); "
        f"every cell slugs/subscription=100",
        file=sys.stderr,
    )
    if not (m4_present and all_100_slugs):
        return EXIT_CONFIG_ERROR

    print("=== sweeps self-check complete ===", file=sys.stderr)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Sweep execution — per §16.5; network-touching
# ---------------------------------------------------------------------------
#
# This section parallels probe.py's _run_probe_async (probe.py lines
# 338-584). Key generalizations from probe.py:
#
# 1. A cell can have N connections × M subscriptions-per-connection, each
#    with 100 slugs. probe.py had one subscription with one slug. Sweeps
#    fan out from connection → subscriptions → slugs.
#
# 2. Attribution is per-requestId (for per-subscription traffic counts)
#    and per-marketSlug (for per-slug attribution) — §14.3 confirmed at
#    n=1 that market_data payloads carry both fields. Sweeps register one
#    handler set per markets_ws; handlers dispatch to the correct
#    SubscribeObservation via the requestId echo.
#
# 3. Exceptions raised mid-cell are captured against the cell (same
#    precedence as probe.py: documented SDK exceptions → classification
#    hint; transport → exception; catch-all → exception).
#
# 4. Real-anchor-slug fetch via client.markets.list() is a net-new SDK
#    surface beyond probe.py's [A]-[D] block. See _fetch_anchor_slug
#    docstring for the defensive-shape-handling rationale.
#
# D-016 commitment 2 (no Phase 2 code touch, no network fabrication) is
# honored: SDK imports are deferred to inside this section so self-check
# mode can detect their absence without aborting. Every SDK symbol used
# traces to [E] per the module header.


async def _fetch_anchor_slug(
    client: Any,
    cli_seed_slug: Optional[str] = None,
) -> Optional[str]:
    """Fetch one real anchor slug for default-cell subscriptions.

    Per §16.5, the default slug source is `client.markets.list()` via the
    SDK. Fallback is the operator-supplied `--seed-slug` CLI argument
    (parallels probe.py's `--slug`).

    **Defensive shape handling (FLAG — surface at checkpoint 3 pause):**
    The [E] README example shows `len(markets['markets'])` — confirming
    the top-level return shape has a "markets" key containing a list. The
    README does NOT pin the inner element shape (whether each element is
    a dict, a dataclass, what the slug field name is). This function
    tries the likely field names in order and logs which one resolved; a
    truly-unexpected shape falls through to None and the caller reports
    EXIT_NO_ANCHOR_SLUG.

    Strategy:
      1. If cli_seed_slug is provided, use it directly. (Parallels
         probe.py --slug precedence per D-027.)
      2. Otherwise, call client.markets.list() and extract the first
         slug from the first market element, trying field names in order:
         "marketSlug" (camelCase, per §14.3 observed wire format),
         "market_slug" (snake_case, per §13.2 meta.json schema),
         "slug" (unadorned). Returns None if none resolve.

    Returns None if no anchor slug can be obtained. Caller must decide
    whether to proceed (M4 control cell doesn't need one) or abort
    with EXIT_NO_ANCHOR_SLUG.
    """
    if cli_seed_slug:
        log.info(
            "anchor slug: using operator-supplied --seed-slug=%s", cli_seed_slug
        )
        return cli_seed_slug

    try:
        # Per [E]: markets.list() is async-awaitable on AsyncPolymarketUS;
        # takes optional params dict. Pass limit=1 to minimize payload
        # (we only need one anchor).
        result = await client.markets.list({"limit": 1})
    except Exception as exc:
        log.warning("markets.list() raised: %r", exc)
        return None

    # Top-level shape: per [E] the key is "markets" containing a list.
    if not isinstance(result, dict):
        log.warning(
            "markets.list() returned non-dict (%s); cannot extract slug",
            type(result).__name__,
        )
        return None

    markets = result.get("markets")
    if not isinstance(markets, list) or not markets:
        log.warning(
            "markets.list() response missing 'markets' list or list is empty"
        )
        return None

    first = markets[0]

    # Try field names in order of likelihood.
    # §14.3 observed wire shape uses "marketSlug" on incoming WS payloads.
    # §13.2 meta.json uses "market_slug". Either could appear in
    # markets.list(); README does not pin which.
    if isinstance(first, dict):
        for field_name in ("marketSlug", "market_slug", "slug"):
            candidate = first.get(field_name)
            if isinstance(candidate, str) and candidate:
                log.info(
                    "anchor slug: fetched via markets.list() (field=%r): %s",
                    field_name, candidate,
                )
                return candidate
        log.warning(
            "markets.list() first element is a dict but no recognized slug "
            "field (tried marketSlug, market_slug, slug); keys present: %s",
            sorted(first.keys()) if hasattr(first, "keys") else "<unknown>",
        )
        return None

    # If the element is not a dict (e.g., a dataclass), try attribute access.
    for attr_name in ("marketSlug", "market_slug", "slug"):
        candidate = getattr(first, attr_name, None)
        if isinstance(candidate, str) and candidate:
            log.info(
                "anchor slug: fetched via markets.list() (attr=%r): %s",
                attr_name, candidate,
            )
            return candidate

    log.warning(
        "markets.list() first element type %s has no recognized slug attribute",
        type(first).__name__,
    )
    return None


async def _run_cell_async(
    client: Any,
    cell: CellSpec,
    sweep_id: str,
    anchor_slug: str,
    observation_seconds: float,
) -> SweepCellOutcome:
    """Execute one grid cell: N connections × M subscriptions each with 100 slugs.

    Returns the SweepCellOutcome record. Does NOT raise — every exception
    is captured into the outcome's exception_type / exception_message,
    mirroring probe.py's _run_probe_async discipline (probe.py lines
    338-584).

    Per-event handlers dispatch messages to the correct SubscribeObservation
    via the requestId echo observed in §14.3 payload preview. If a message
    arrives with a requestId we didn't issue (shouldn't happen, but
    defensively logged), it populates cell-level fallback counts, not any
    specific SubscribeObservation.
    """
    # Defer SDK exception imports to the function body so self-check mode
    # doesn't need them. Same pattern as probe.py line 350.
    from polymarket_us import (  # noqa: F401 — caught at classification via type-name strings
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        RateLimitError,
    )

    outcome = SweepCellOutcome(
        sweep_id=sweep_id,
        cell_id=cell.cell_id,
        cell_axis=cell.cell_axis,
        cell_axis_value=cell.cell_axis_value,
        slugs_per_subscription=cell.slugs_per_subscription,
        cell_started_at_utc=datetime.now(timezone.utc).isoformat(),
        observation_window_seconds=observation_seconds,
    )

    cell_start_monotonic = time.monotonic()

    # Build the connection list and populate subscribe specs BEFORE
    # connecting — so per-request_id bookkeeping is ready before any
    # traffic arrives.
    subscription_lookup: dict[str, SubscribeObservation] = {}
    markets_ws_list: list[Any] = []

    for conn_idx in range(cell.connection_count):
        conn_obs = ConnectionObservation(connection_index=conn_idx)
        for sub_idx in range(cell.subscriptions_per_connection):
            slugs = build_slug_list_for_subscription(
                cell=cell,
                subscription_index=conn_idx * cell.subscriptions_per_connection + sub_idx,
                real_anchor_slug=anchor_slug,
            )
            request_id = (
                f"sweep-{sweep_id}-{cell.cell_id}-conn{conn_idx}-sub{sub_idx}"
            )
            sub_obs = SubscribeObservation(
                request_id=request_id,
                slugs=list(slugs),
                real_slug=anchor_slug if cell.real_slugs_per_subscription > 0 else "",
                placeholder_slugs_count=cell.placeholder_slugs_per_subscription,
            )
            conn_obs.subscribe_calls.append(sub_obs)
            subscription_lookup[request_id] = sub_obs
        outcome.connections.append(conn_obs)

    # Per-subscription first-message-latency bookkeeping needs the subscribe
    # monotonic-time. Recorded when subscribe_sent flips True.
    subscribe_sent_monotonic: dict[str, float] = {}

    def _extract_request_id(payload: Any) -> Optional[str]:
        """Pull requestId from a payload. Per §14.3 observed shape, the
        first-message preview has a top-level 'requestId' key on
        market_data messages. Other event types may or may not carry it.
        Defensive: try dict.get first, then attribute access.
        """
        if payload is None:
            return None
        if isinstance(payload, dict):
            rid = payload.get("requestId")
            if isinstance(rid, str):
                return rid
        rid = getattr(payload, "requestId", None)
        if isinstance(rid, str):
            return rid
        return None

    def _extract_market_slug(payload: Any, event_name: str) -> Optional[str]:
        """Pull marketSlug from a payload for per-slug attribution. §14.3
        observed shape: market_data payloads have marketData.marketSlug;
        trade payloads have trade.marketSlug. Heartbeat / error / close
        do not carry a marketSlug (connection-level events).
        """
        if payload is None:
            return None
        # Direct path first: top-level marketSlug.
        if isinstance(payload, dict):
            direct = payload.get("marketSlug")
            if isinstance(direct, str):
                return direct
            # Nested: marketData.marketSlug (market_data event per §14.3)
            # or trade.marketSlug (trade event per [F] Trade Response shape).
            for nested_key in ("marketData", "marketDataLite", "trade"):
                nested = payload.get(nested_key)
                if isinstance(nested, dict):
                    slug = nested.get("marketSlug")
                    if isinstance(slug, str):
                        return slug
        # Attribute-access fallback (in case the SDK returns dataclass-like
        # objects rather than dicts).
        direct = getattr(payload, "marketSlug", None)
        if isinstance(direct, str):
            return direct
        return None

    def _handle_payload(event_name: str, payload: Any) -> None:
        """Per-event handler. Dispatches to the correct SubscribeObservation
        by requestId echo; falls back to marking on every known sub if the
        requestId doesn't match (shouldn't happen).
        """
        rid = _extract_request_id(payload)
        target_sub = subscription_lookup.get(rid) if rid else None

        # Per-subscription bookkeeping.
        if target_sub is not None:
            target_sub.message_count_by_event[event_name] = (
                target_sub.message_count_by_event.get(event_name, 0) + 1
            )
            # First-message latency per subscription.
            if target_sub.first_message_latency_seconds is None:
                sent_monotonic = subscribe_sent_monotonic.get(rid)
                if sent_monotonic is not None:
                    target_sub.first_message_latency_seconds = round(
                        time.monotonic() - sent_monotonic, 3
                    )
                    target_sub.first_message_event = event_name
                    try:
                        preview = repr(payload)
                    except Exception:
                        preview = "<unreprable payload>"
                    target_sub.first_message_preview = preview[
                        :PREVIEW_TRUNCATION_CHARS
                    ]
            # Per-slug attribution via marketSlug echo.
            slug = _extract_market_slug(payload, event_name)
            if slug:
                target_sub.per_slug_message_counts[slug] = (
                    target_sub.per_slug_message_counts.get(slug, 0) + 1
                )
        # If rid didn't match any known subscription (unexpected per
        # §14.3's requestId echo), log at WARN but don't fail the cell.
        elif rid is not None:
            log.warning(
                "cell %s: received %s payload with unrecognized "
                "requestId %r; ignoring",
                cell.cell_id, event_name, rid,
            )

    # Per-connection error / close handlers — these events are not tied
    # to a specific subscribe per §14.3's design, so they land on the
    # connection, not the subscription.
    def _make_error_handler(conn_obs: ConnectionObservation):
        def _on_error(payload: Any) -> None:
            try:
                repr_str = repr(payload)
            except Exception:
                repr_str = "<unreprable error>"
            conn_obs.error_events.append(repr_str[:PREVIEW_TRUNCATION_CHARS])
            # Also record at subscription level via _handle_payload
            # (in case the error carries a requestId).
            _handle_payload("error", payload)
        return _on_error

    def _make_close_handler(conn_obs: ConnectionObservation):
        def _on_close(payload: Any) -> None:
            try:
                repr_str = repr(payload)
            except Exception:
                repr_str = "<unreprable close>"
            conn_obs.close_events.append(repr_str[:PREVIEW_TRUNCATION_CHARS])
            _handle_payload("close", payload)
        return _on_close

    # Exception-scoped execution mirrors probe.py's async-context-manager
    # pattern (probe.py lines 436-530).
    try:
        # Per cell, create N markets_ws instances. Note M2 is the
        # empirical question of whether N calls to client.ws.markets()
        # produce N independent instances; the harness issues the calls
        # and observes what happens. If the SDK returns the same object
        # twice, that's the M2=shared resolution, recorded at cell end.
        for conn_idx, conn_obs in enumerate(outcome.connections):
            markets_ws = client.ws.markets()
            markets_ws_list.append(markets_ws)

            # Register handlers BEFORE connect/subscribe per §14.3 and
            # probe.py lines 443-450.
            markets_ws.on("market_data", lambda d: _handle_payload("market_data", d))
            markets_ws.on("market_data_lite", lambda d: _handle_payload("market_data_lite", d))
            markets_ws.on("trade", lambda d: _handle_payload("trade", d))
            markets_ws.on("heartbeat", lambda d: _handle_payload("heartbeat", d))
            markets_ws.on("error", _make_error_handler(conn_obs))
            markets_ws.on("close", _make_close_handler(conn_obs))

            await markets_ws.connect()
            conn_obs.connected = True

        # Issue all subscribes across all connections. Per-subscribe
        # exceptions are caught individually so one bad subscribe does
        # not abort the whole cell. Subscribe ratio at classification
        # time reflects how many succeeded.
        for conn_idx, conn_obs in enumerate(outcome.connections):
            markets_ws = markets_ws_list[conn_idx]
            for sub_obs in conn_obs.subscribe_calls:
                try:
                    subscribe_sent_monotonic[sub_obs.request_id] = time.monotonic()
                    await markets_ws.subscribe(
                        sub_obs.request_id,
                        SUBSCRIPTION_TYPE_MARKET_DATA,
                        sub_obs.slugs,
                    )
                    sub_obs.subscribe_sent = True
                except (
                    AuthenticationError,
                    BadRequestError,
                    NotFoundError,
                    RateLimitError,
                ) as exc:
                    # Documented SDK exception on a subscribe call.
                    # Record on the outcome so classify_cell() can route
                    # to step 2 (rejected). First one wins — later
                    # subscribes can still be attempted (subscribe ratio
                    # will reflect the mix).
                    if not outcome.exception_type:
                        outcome.exception_type = type(exc).__name__
                        outcome.exception_message = str(exc)[
                            :PREVIEW_TRUNCATION_CHARS
                        ]
                    log.warning(
                        "cell %s conn %d subscribe %s raised %s: %s",
                        cell.cell_id, conn_idx, sub_obs.request_id,
                        type(exc).__name__, str(exc)[:200],
                    )
                except Exception as exc:
                    # Non-documented exception mid-subscribe: treat as
                    # exception-class. Same logic as probe.py line 522.
                    if not outcome.exception_type:
                        outcome.exception_type = type(exc).__name__
                        outcome.exception_message = str(exc)[
                            :PREVIEW_TRUNCATION_CHARS
                        ]
                    log.warning(
                        "cell %s conn %d subscribe %s raised %s: %s",
                        cell.cell_id, conn_idx, sub_obs.request_id,
                        type(exc).__name__, str(exc)[:200],
                    )

        # Observe for the configured window. Same pattern as probe.py
        # line 469.
        await asyncio.sleep(observation_seconds)

        # Close every connection. Close exceptions are logged but do not
        # fail the cell — the observation is already complete.
        for conn_idx, conn_obs in enumerate(outcome.connections):
            markets_ws = markets_ws_list[conn_idx]
            try:
                await markets_ws.close()
                conn_obs.closed_cleanly = True
            except Exception as exc:
                log.warning(
                    "cell %s conn %d close() raised %s: %r",
                    cell.cell_id, conn_idx, type(exc).__name__, exc,
                )

    except (APIConnectionError, APITimeoutError) as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:PREVIEW_TRUNCATION_CHARS]
    except asyncio.TimeoutError as exc:
        outcome.exception_type = "TimeoutError"  # asyncio.TimeoutError's qualname
        outcome.exception_message = str(exc)[:PREVIEW_TRUNCATION_CHARS]
    except (AuthenticationError, BadRequestError, NotFoundError, RateLimitError) as exc:
        # Documented SDK exception outside the subscribe loop (e.g., on
        # connect). Record and move on.
        if not outcome.exception_type:
            outcome.exception_type = type(exc).__name__
            outcome.exception_message = str(exc)[:PREVIEW_TRUNCATION_CHARS]
    except Exception as exc:
        # Catch-all: undocumented exception type. classify_cell() routes
        # undocumented types to `exception`.
        if not outcome.exception_type:
            outcome.exception_type = type(exc).__name__
            outcome.exception_message = str(exc)[:PREVIEW_TRUNCATION_CHARS]

    # Finalize cell timing.
    outcome.cell_ended_at_utc = datetime.now(timezone.utc).isoformat()
    outcome.elapsed_seconds = round(time.monotonic() - cell_start_monotonic, 3)

    # Resolve per-cell measurement questions BEFORE classification, because
    # m1_resolution / m2_resolution / etc. live on the outcome record and
    # the run-level aggregation reads them.
    _resolve_cell_measurements(outcome, cell)

    # Classify.
    outcome.cell_classification, outcome.cell_classification_reason = classify_cell(
        outcome, is_m4_control=cell.is_m4_control
    )

    return outcome


# ---------------------------------------------------------------------------
# Per-cell measurement-question resolvers — per §16.4
# ---------------------------------------------------------------------------


def _resolve_cell_measurements(
    outcome: SweepCellOutcome,
    cell: CellSpec,
) -> None:
    """Populate outcome.m1_resolution through m5_observations per §16.4.

    Called after the cell's async execution completes. Reads from the
    populated SubscribeObservation / ConnectionObservation records.
    """
    outcome.m1_resolution = _resolve_m1(outcome, cell)
    outcome.m2_resolution = _resolve_m2(outcome, cell)
    outcome.m3_observations = _resolve_m3(outcome, cell)
    outcome.m4_observations = _resolve_m4(outcome, cell)
    outcome.m5_observations = _resolve_m5(outcome, cell)


def _resolve_m1(outcome: SweepCellOutcome, cell: CellSpec) -> Optional[str]:
    """M1 — multi-same-type subscription composition on one markets_ws.

    Per §16.4: M1 is tested by cells that issue ≥2 subscribe() calls on
    the same markets_ws. That's subscriptions-axis cells with
    cell_axis_value >= 2. connections-axis cells with N=1 subscription
    per connection do NOT test M1 (only one subscribe per markets_ws).

    Resolution:
      - compose: each requestId received distinct traffic (per-requestId
        message_count > 0 for at least 2 distinct request_ids).
      - replace: only the most recently subscribed request_id received
        traffic; earlier request_ids have zero messages.
      - error: a BadRequestError or similar fired on the second or later
        subscribe (captured as outcome.exception_type if set).
      - ambiguous: some other pattern (partial attribution, cross-sub
        noise that doesn't fit compose/replace cleanly).
      - None: cell does not test M1.
    """
    # M1 testable only at subscriptions-axis with N >= 2 subscriptions on
    # one connection (one markets_ws).
    if cell.cell_axis != "subscriptions" or cell.subscriptions_per_connection < 2:
        return None

    # If an exception fired, M1 resolution is "error" regardless of what
    # traffic arrived.
    if outcome.exception_type:
        return "error"

    # Gather per-request_id message counts across all connections in the
    # cell (should be one connection for subscriptions-axis cells).
    rid_counts: dict[str, int] = {}
    for conn in outcome.connections:
        for sub in conn.subscribe_calls:
            total = sum(sub.message_count_by_event.values())
            rid_counts[sub.request_id] = total

    # Count how many request_ids got any traffic.
    nonzero_rids = [rid for rid, n in rid_counts.items() if n > 0]

    if len(nonzero_rids) >= 2:
        # Multiple request_ids received traffic — compose confirmed.
        return "compose"
    if len(nonzero_rids) == 1:
        # Only one request_id got traffic. If it's the LAST subscribe
        # call (most recent), that's replace. Otherwise ambiguous
        # (some intermediate survived — unusual).
        # Our request_id convention is
        # "sweep-{sweep_id}-{cell_id}-conn{conn_idx}-sub{sub_idx}";
        # higher sub_idx = later subscribe. The last subscribe on conn 0
        # has sub_idx == cell.subscriptions_per_connection - 1.
        last_sub_idx = cell.subscriptions_per_connection - 1
        last_rid_suffix = f"sub{last_sub_idx}"
        if nonzero_rids[0].endswith(last_rid_suffix):
            return "replace"
        return "ambiguous"
    # Zero request_ids received traffic. Could be M4-like silent filter
    # applied to anchor slugs (unlikely — anchor is real), or a cell
    # where the anchor slug itself has no trades / quiet market. Surface
    # literally as ambiguous rather than assuming compose or replace.
    return "ambiguous"


def _resolve_m2(outcome: SweepCellOutcome, cell: CellSpec) -> Optional[str]:
    """M2 — multi-connection composition on one client.

    Per §16.4: M2 is tested by cells that instantiate ≥2 markets_ws via
    ≥2 calls to client.ws.markets() on one AsyncPolymarketUS. That's
    connections-axis cells with cell_axis_value >= 2.

    Resolution:
      - independent: all N connections connect cleanly; each receives
        traffic (if anchor is active).
      - shared: only one connection appears to have received traffic,
        OR all connections share identity (cannot be detected here without
        SDK-level introspection; we use a weaker observable — traffic
        distribution across connection slots).
      - error: an exception fired on a second or later connect call.
      - ambiguous: partial connect success or unclear pattern.
      - None: cell does not test M2.
    """
    if cell.cell_axis != "connections" or cell.connection_count < 2:
        return None

    if outcome.exception_type:
        return "error"

    # Count connections that connected and received any traffic.
    connected_count = sum(1 for c in outcome.connections if c.connected)
    trafficked_count = sum(
        1
        for c in outcome.connections
        if any(
            sum(s.message_count_by_event.values()) > 0
            for s in c.subscribe_calls
        )
    )

    if connected_count < cell.connection_count:
        # Not all connections connected. Partial = ambiguous unless we
        # saw zero connect — that would have been caught as rejected.
        return "ambiguous"

    # All connections connected. M2 independence is measured by traffic
    # distribution: if every connection received traffic on its own
    # anchor, they are independent. If only one connection received
    # traffic while the others were silent, they may be shared (same
    # underlying WS object; subscribes collapsed).
    if trafficked_count == cell.connection_count:
        return "independent"
    if trafficked_count == 1 and cell.connection_count > 1:
        # Only one connection got traffic despite multiple subscribes.
        # Likely-shared signal.
        return "shared"
    # Mixed: some got traffic, some didn't. Surface literally.
    return "ambiguous"


def _resolve_m3(outcome: SweepCellOutcome, cell: CellSpec) -> dict:
    """M3 — per-subscription cap behavior at 100 slugs.

    Per §16.4: M3 observations are first-message latency, per-slug
    message attribution, message-rate-under-load. Every default cell
    produces M3 data (every cell uses 100 slugs per subscription). The
    M4 control cell also produces M3-shaped data, but its per-slug
    counts are all placeholders.

    Returns a dict rather than an enum because M3 is observational, not
    a single-label resolution.
    """
    latencies: list[float] = []
    per_slug_totals: dict[str, int] = {}
    total_messages_by_event: dict[str, int] = {}

    for conn in outcome.connections:
        for sub in conn.subscribe_calls:
            if sub.first_message_latency_seconds is not None:
                latencies.append(sub.first_message_latency_seconds)
            for event_name, n in sub.message_count_by_event.items():
                total_messages_by_event[event_name] = (
                    total_messages_by_event.get(event_name, 0) + n
                )
            for slug, n in sub.per_slug_message_counts.items():
                per_slug_totals[slug] = per_slug_totals.get(slug, 0) + n

    return {
        "cell_slugs_per_subscription": cell.slugs_per_subscription,
        "cell_intended_subscribe_count": cell.intended_subscribe_count,
        "first_message_latencies_seconds": latencies,
        "median_first_message_latency_seconds": (
            _median(latencies) if latencies else None
        ),
        "total_messages_by_event": total_messages_by_event,
        "distinct_slugs_with_traffic": len(per_slug_totals),
        "per_slug_totals_top10": sorted(
            per_slug_totals.items(), key=lambda kv: kv[1], reverse=True
        )[:10],
    }


def _resolve_m4(outcome: SweepCellOutcome, cell: CellSpec) -> dict:
    """M4 — placeholder-slug rejection behavior.

    Per §16.4: M4 is observed across all cells (placeholder slugs present
    in every cell). The M4 control cell (100P/0R) is the clean unconfounded
    measurement. Default cells' M4 data is confounded by the anchor but
    still produces per-slug attribution.

    Resolution indicators:
      - placeholder_traffic_observed: True if any placeholder slug
        received a market_data/trade message. The placeholder synthesis
        guarantees these slugs don't correspond to real markets, so any
        traffic is surprising.
      - subscribe_succeeded: whether the subscribe call (at least one)
        succeeded without BadRequestError. Hard-rejection (M4 option b)
        would have raised BadRequestError and populated exception_type.
      - silent_filter_inferred: True if subscribes succeeded and no
        placeholder slug received traffic (M4 option a).
    """
    placeholder_messages = 0
    real_slug_messages = 0
    subscribe_successes = 0

    for conn in outcome.connections:
        for sub in conn.subscribe_calls:
            if sub.subscribe_sent:
                subscribe_successes += 1
            for slug, n in sub.per_slug_message_counts.items():
                if slug == sub.real_slug and sub.real_slug:
                    real_slug_messages += n
                else:
                    placeholder_messages += n

    return {
        "is_m4_control_cell": cell.is_m4_control,
        "placeholder_slugs_count": (
            cell.placeholder_slugs_per_subscription * cell.intended_subscribe_count
        ),
        "placeholder_traffic_observed": placeholder_messages > 0,
        "placeholder_message_count": placeholder_messages,
        "anchor_slug_message_count": real_slug_messages,
        "subscribe_successes": subscribe_successes,
        "hard_rejection_observed": (
            outcome.exception_type in ("BadRequestError", "NotFoundError")
        ),
        "silent_filter_inferred": (
            subscribe_successes > 0
            and placeholder_messages == 0
            and not outcome.exception_type
        ),
    }


def _resolve_m5(outcome: SweepCellOutcome, cell: CellSpec) -> dict:
    """M5 — connection-level concurrent-connection cap.

    Per §16.4: M5 is observed at the per-connection level across cells.
    Every cell produces M5 data; connections-axis cells are the primary
    instrument for characterizing the upper bound.

    Observations: per-connection connect/subscribe/traffic outcomes.
    """
    per_conn: list[dict] = []
    for conn in outcome.connections:
        subscribe_successes = sum(1 for s in conn.subscribe_calls if s.subscribe_sent)
        total_messages = sum(
            sum(s.message_count_by_event.values()) for s in conn.subscribe_calls
        )
        per_conn.append({
            "connection_index": conn.connection_index,
            "connected": conn.connected,
            "closed_cleanly": conn.closed_cleanly,
            "subscribe_attempts": len(conn.subscribe_calls),
            "subscribe_successes": subscribe_successes,
            "error_event_count": len(conn.error_events),
            "close_event_count": len(conn.close_events),
            "total_messages_received": total_messages,
        })
    return {
        "cell_connection_count": cell.connection_count,
        "all_connected": all(c["connected"] for c in per_conn) if per_conn else False,
        "per_connection": per_conn,
    }


def _median(values: list[float]) -> float:
    """Simple median for small latency lists. No numpy dependency needed."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 0:
        return (s[mid - 1] + s[mid]) / 2.0
    return s[mid]


# ---------------------------------------------------------------------------
# Run-level aggregate summary dicts — committed schemas per checkpoint 3
# ---------------------------------------------------------------------------


def build_m3_aggregate_summary(cells: list[SweepCellOutcome]) -> dict:
    """Schema: per-N latency medians, message-volume summary across cells.

    §16.6 names m3_aggregate_summary as a dict; §16.10 leaves the shape to
    code turn. Committed schema:
      - per_cell_median_latency_seconds: list of (cell_id, median)
      - overall_median_latency_seconds: float or None
      - total_messages_by_event: dict aggregating across all cells
      - cells_with_latency_data: int
    """
    per_cell: list[tuple[str, Optional[float]]] = []
    all_latencies: list[float] = []
    total_by_event: dict[str, int] = {}
    cells_with_latency = 0

    for cell in cells:
        obs = cell.m3_observations or {}
        med = obs.get("median_first_message_latency_seconds")
        per_cell.append((cell.cell_id, med))
        if isinstance(med, (int, float)):
            all_latencies.append(float(med))
            cells_with_latency += 1
        for event_name, n in obs.get("total_messages_by_event", {}).items():
            total_by_event[event_name] = total_by_event.get(event_name, 0) + int(n)

    return {
        "per_cell_median_latency_seconds": per_cell,
        "overall_median_latency_seconds": (
            _median(all_latencies) if all_latencies else None
        ),
        "total_messages_by_event": total_by_event,
        "cells_with_latency_data": cells_with_latency,
    }


def build_m4_aggregate_summary(cells: list[SweepCellOutcome]) -> dict:
    """Schema: M4 placeholder-rejection behavior across cells.

    Committed schema:
      - m4_control_cell_observed: bool (was the dedicated 100P/0R cell run?)
      - m4_control_behavior: "silent_filter" | "hard_rejection" |
                             "unexpected_traffic" | "ambiguous" | None
      - placeholder_traffic_in_any_cell: bool
      - hard_rejection_in_any_cell: bool
      - total_placeholder_messages: int
    """
    m4_control_obs: Optional[dict] = None
    total_placeholder = 0
    hard_rejection_any = False
    placeholder_any = False

    for cell in cells:
        obs = cell.m4_observations or {}
        if obs.get("is_m4_control_cell"):
            m4_control_obs = obs
        total_placeholder += int(obs.get("placeholder_message_count", 0))
        if obs.get("hard_rejection_observed"):
            hard_rejection_any = True
        if obs.get("placeholder_traffic_observed"):
            placeholder_any = True

    # Derive the M4 control cell's behavior category.
    m4_behavior: Optional[str] = None
    if m4_control_obs is not None:
        if m4_control_obs.get("hard_rejection_observed"):
            m4_behavior = "hard_rejection"
        elif m4_control_obs.get("silent_filter_inferred"):
            m4_behavior = "silent_filter"
        elif m4_control_obs.get("placeholder_traffic_observed"):
            m4_behavior = "unexpected_traffic"
        else:
            m4_behavior = "ambiguous"

    return {
        "m4_control_cell_observed": m4_control_obs is not None,
        "m4_control_behavior": m4_behavior,
        "placeholder_traffic_in_any_cell": placeholder_any,
        "hard_rejection_in_any_cell": hard_rejection_any,
        "total_placeholder_messages": total_placeholder,
    }


# ---------------------------------------------------------------------------
# Sweep execution entry point
# ---------------------------------------------------------------------------


async def _run_sweep_async(
    config: SweepConfig,
    sweep_selector: str,
    seed_slug: Optional[str],
) -> SweepRunOutcome:
    """Execute a full sweep (one or more cells) and return the outcome record.

    Parallels probe.py's top-level _run_probe_async + run_probe pattern
    but generalized to a grid. Does NOT raise — client-construction and
    anchor-fetch exceptions are captured onto the run outcome via
    run_notes rather than propagating.
    """
    from polymarket_us import AsyncPolymarketUS

    run = SweepRunOutcome(
        run_id=f"sweep-h020-{int(time.time())}",
        sweep_started_at_utc=datetime.now(timezone.utc).isoformat(),
    )

    # SDK version best-effort.
    try:
        import polymarket_us as _pm
        run.sdk_version = getattr(_pm, "__version__", "")
    except Exception:
        pass

    grid = filter_grid_by_sweep_selector(build_default_grid(), sweep_selector)
    anchor_slug: Optional[str] = None

    async with AsyncPolymarketUS(
        key_id=config.key_id,
        secret_key=config.secret_key,
    ) as client:
        # Fetch anchor slug once per run. Used by every default cell;
        # ignored by M4 control.
        if any(not c.is_m4_control for c in grid):
            anchor_slug = await _fetch_anchor_slug(client, cli_seed_slug=seed_slug)
            if not anchor_slug:
                run.run_notes += (
                    "anchor slug fetch returned None; default cells cannot "
                    "run without an anchor slug. Aborting before cell "
                    "execution. "
                )
                run.sweep_ended_at_utc = datetime.now(timezone.utc).isoformat()
                run.run_classification = "ambiguous"
                return run

        # Execute cells sequentially. M4 control runs first per the
        # committed grid order.
        for cell in grid:
            cell_anchor = anchor_slug or ""  # M4 control ignores this
            log.info(
                "running cell %s (axis=%s N=%d; intended_subs=%d)",
                cell.cell_id, cell.cell_axis, cell.cell_axis_value,
                cell.intended_subscribe_count,
            )
            cell_outcome = await _run_cell_async(
                client=client,
                cell=cell,
                sweep_id=run.run_id,
                anchor_slug=cell_anchor,
                observation_seconds=config.observation_seconds,
            )
            run.cells.append(cell_outcome)
            log.info(
                "cell %s classification=%s (reason: %s)",
                cell.cell_id, cell_outcome.cell_classification,
                cell_outcome.cell_classification_reason,
            )

    # Run-level aggregation.
    run.sweep_ended_at_utc = datetime.now(timezone.utc).isoformat()
    run.m1_aggregate_resolution = aggregate_m1_resolution(run.cells)
    run.m2_aggregate_resolution = aggregate_m2_resolution(run.cells)
    run.m3_aggregate_summary = build_m3_aggregate_summary(run.cells)
    run.m4_aggregate_summary = build_m4_aggregate_summary(run.cells)
    run.m5_upper_bound = aggregate_m5_upper_bound(run.cells)
    run.run_classification = aggregate_run_classification(run.cells)

    return run


def _run_classification_to_exit_code(run_classification: str) -> int:
    """Map run-level classification to process exit code.

    Parallels probe.py's _classification_to_exit_code (probe.py lines
    587-594), generalized to run-level classifications.
    """
    return {
        "clean": EXIT_OK,
        "partial": EXIT_SWEEP_PARTIAL,
        "failed": EXIT_SWEEP_FAILED,
        "ambiguous": EXIT_SWEEP_AMBIGUOUS,
    }.get(run_classification, EXIT_SWEEP_AMBIGUOUS)


def run_sweep(
    sweep_selector: str,
    seed_slug: Optional[str] = None,
) -> int:
    """Synchronous entry point for sweep mode.

    Parallels probe.py's run_probe (probe.py lines 597-702). Returns an
    exit code derived from run-level classification.
    """
    print(
        "=== pm-tennis stress-test sweep "
        f"(selector={sweep_selector!r}, §16) ===",
        file=sys.stderr,
    )

    try:
        config = load_sweep_config()
    except KeyError as exc:
        print(f"[FAIL] config error: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    run = asyncio.run(_run_sweep_async(config, sweep_selector, seed_slug))

    # Emit structured outcome JSON on stdout; human-readable summary on stderr.
    print(json.dumps(asdict(run), indent=2, default=str))

    print(
        f"=== sweep complete: run_classification={run.run_classification} "
        f"cells={len(run.cells)} ===",
        file=sys.stderr,
    )
    for cell in run.cells:
        print(
            f"  {cell.cell_id}: {cell.cell_classification} — "
            f"{cell.cell_classification_reason}",
            file=sys.stderr,
        )
    print(
        f"M1={run.m1_aggregate_resolution} "
        f"M2={run.m2_aggregate_resolution} "
        f"M5_upper_bound={run.m5_upper_bound}",
        file=sys.stderr,
    )
    if run.run_notes:
        print(f"run_notes: {run.run_notes}", file=sys.stderr)

    if run.run_classification in ("", "ambiguous") and not run.cells:
        # Empty-cells case (e.g., anchor fetch failed) — route to a
        # distinct exit code.
        return EXIT_NO_ANCHOR_SLUG

    return _run_classification_to_exit_code(run.run_classification)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
#
# Parallels probe.py's CLI (probe.py lines 710-765). Same argparse style,
# same log-level convention, same main() dispatch on a flag.


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.stress_test.sweeps",
        description=(
            "PM-Tennis Phase 3 attempt 2 main-sweeps harness per §16. "
            "Default action is a no-network self-check. Pass --sweep=... "
            "to execute the committed grid."
        ),
    )
    parser.add_argument(
        "--sweep",
        default=None,
        choices=["subscriptions", "connections", "both"],
        help=(
            "Execute the sweep: 'subscriptions' for the per-connection "
            "subscription-count axis (1/2/5/10), 'connections' for the "
            "concurrent-connection axis (1/2/4), 'both' for the full grid "
            "including the M4 control cell (100P/0R, runs first). "
            "Required to enter sweep mode; omitting --sweep runs self-check."
        ),
    )
    parser.add_argument(
        "--seed-slug",
        default=None,
        help=(
            "Operator-supplied anchor slug for default cells. Parallels "
            "probe.py's --slug. If omitted, the harness calls "
            "client.markets.list() to fetch one at runtime. If that call "
            "fails or returns an unexpected shape, the run aborts with "
            "EXIT_NO_ANCHOR_SLUG."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Python logging level (default: INFO).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if args.sweep:
        return run_sweep(
            sweep_selector=args.sweep,
            seed_slug=args.seed_slug,
        )
    return run_self_check()


if __name__ == "__main__":
    sys.exit(main())
