"""
probe — the D-025 hybrid-probe-first one-slug probe against the Polymarket US
Markets WebSocket.

WHAT THIS MODULE DOES

1. Entry point for the isolated pm-tennis-stress-test Render service.
2. Two modes, gated by CLI flag:
     - self-check (default): verify credentials load and SDK surfaces
       import. Does NOT touch the network. Safe to run every service boot.
     - probe (--probe --slug=SLUG): execute the D-025 probe — connect,
       subscribe to one slug, observe for ~10 seconds, disconnect, emit
       structured outcome JSON.

This split is deliberate. Per operator direction at H-013, the service is
deployed this session but the main sweeps are deferred to H-014. Under that
setup the service may sit idle, get re-deployed, restart, etc. Making the
default boot a no-op means deployment events don't accidentally consume
stress-test resources or make unnecessary WebSocket connections.

SLUG SOURCE — D-027 SUPERSEDES D-025 COMMITMENT 1

Render persistent disks are strictly single-service per render.com/docs/disks
("A persistent disk is accessible by only a single service instance ... You
can't access a service's disk from any other service"). D-025's original
commitment 1 specified reading the probe slug from Phase 2's meta.json
archive on the shared disk. That is not implementable with the isolated-
service architecture required by D-024 commitment 1 and D-020/Q2=(b).

D-027 (H-013) supersedes D-025 commitment 1 with Option D: the operator
selects a gateway-sourced slug from Phase 2's meta.json archive via the
pm-tennis-api Shell, then passes it to the probe as a CLI argument. The
research-question intent of D-025 is preserved — the probe still tests a
gateway-sourced slug against the api WebSocket — only the transport
changes. slug_selector still ships as a library for local testing and for
the pm-tennis-api-Shell helper command; it is no longer called from the
stress-test service's probe path.

AUTHORITATIVE CITATIONS (every SDK symbol or wire value below traces to one)

[A] github.com/Polymarket/polymarket-us-python README (fetched H-013):
    - Import path: `from polymarket_us import AsyncPolymarketUS`
    - Constructor: `AsyncPolymarketUS(key_id=..., secret_key=...)` (both str,
      secret_key is the Base64-encoded Ed25519 private key from developer
      portal).
    - Used as async context manager: `async with AsyncPolymarketUS(...) as client:`
    - WebSocket factory: `markets_ws = client.ws.markets()`
    - WebSocket methods (all async): `await markets_ws.connect()`,
      `await markets_ws.subscribe(request_id, subscription_type, market_slugs_list)`,
      `await markets_ws.close()`.
    - Event handler registration (sync): `markets_ws.on("market_data", fn)`,
      `markets_ws.on("trade", fn)`, `markets_ws.on("heartbeat", fn)`,
      `markets_ws.on("error", fn)`, `markets_ws.on("close", fn)`.
    - Subscription type enum string: `"SUBSCRIPTION_TYPE_MARKET_DATA"`.
    - Exception types: `AuthenticationError`, `APIConnectionError`,
      `APITimeoutError`, `BadRequestError`, `NotFoundError`, `RateLimitError`.

[B] docs.polymarket.us/api-reference/authentication (fetched H-013):
    - Three handshake headers: X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature.
    - Timestamp in milliseconds. 30-sec clock window.
    - SDK handles auth internally when key_id/secret_key are passed.

[C] docs.polymarket.us/api-reference/websocket/markets (cited via research-doc
    v4 §4.3; not re-fetched this session because the SDK path insulates us
    from the wire format — the SDK is responsible for emitting camelCase
    enum-string correctly per D-024 commitment 2).

[D] Research-doc v4 §13.4 — probe-slug default 9392/aec-atp-digsin-meralk-
    2026-04-21 is TRACEABILITY ONLY. Runtime slug selection is now operator-
    supplied via --slug=SLUG per D-027; slug_selector.select_probe_slug()
    remains available as a library for local testing and for the
    pm-tennis-api Shell helper command that surfaces candidates.

NOT DONE HERE (deferred to H-014 per operator cut at H-013 open)

- Main per-subscription-count sweep (§7 Q3=(c) part 1).
- Main concurrent-connection sweep (§7 Q3=(c) part 2).
- Placeholder-slug generation for > 100-slug subscriptions.
- SDK `markets.list()` call for api-sourced slugs (only needed if main sweeps
  choose the api-sourced branch based on probe outcome).

ENVIRONMENT VARIABLES READ

- POLYMARKET_US_API_KEY_ID (required for --probe; optional for self-check)
- POLYMARKET_US_API_SECRET_KEY (required for --probe; optional for self-check)
- PROBE_OBSERVATION_SECONDS (optional, default 10.0; float; probe mode only)

PMTENNIS_DATA_ROOT is read by slug_selector when slug_selector is invoked
(self-check or the listing helper), but is not used in the --probe code
path itself under D-027.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from src.stress_test import slug_selector

# Exit codes (documented in module docstring).
EXIT_OK = 0
EXIT_PROBE_REJECTED = 1
EXIT_PROBE_AMBIGUOUS = 2
EXIT_PROBE_EXCEPTION = 3
EXIT_CONFIG_ERROR = 10
EXIT_NO_CANDIDATE = 11


log = logging.getLogger("stress_test.probe")


# Default observation window per research-doc v4 §13.5 commitment 3.
DEFAULT_OBSERVATION_SECONDS = 10.0

# Per citation [A] above. Literal string value is the enum the SDK/server
# accept. We keep it here as a named constant rather than scattering the
# literal through the code — it's a wire-format value and changes to it
# would be load-bearing.
SUBSCRIPTION_TYPE_MARKET_DATA = "SUBSCRIPTION_TYPE_MARKET_DATA"


# ---------------------------------------------------------------------------
# Outcome record — what the probe writes at the end
# ---------------------------------------------------------------------------


@dataclass
class ProbeOutcome:
    """Structured record of everything the probe observed.

    Written as JSON to stdout at probe exit (and optionally to a file). This
    record is the raw material for the §14 addendum Claude will write in
    H-014 after main sweeps complete.

    Per D-025 commitment 4: if the outcome is ambiguous, that ambiguity is
    surfaced here literally (classification == "ambiguous", plus the raw
    observation that was ambiguous), not silently collapsed into success/fail.
    """

    # Probe identity and timing
    probe_started_at_utc: str = ""
    probe_ended_at_utc: str = ""
    observation_window_seconds: float = 0.0
    elapsed_seconds: float = 0.0

    # What we probed
    event_id: str = ""
    market_slug: str = ""
    candidate_discovered_at: str = ""
    candidate_event_date: str = ""
    eligible_candidates_count: int = 0

    # What we observed
    subscription_request_id: str = ""
    connected: bool = False
    subscribe_sent: bool = False
    first_message_latency_seconds: Optional[float] = None
    message_count_by_event: dict[str, int] = field(default_factory=dict)
    first_message_event: Optional[str] = None
    first_message_preview: Optional[str] = None  # truncated repr, for the log
    error_events: list[str] = field(default_factory=list)
    close_events: list[str] = field(default_factory=list)

    # Classification
    classification: str = ""  # "accepted" | "rejected" | "ambiguous" | "exception"
    classification_reason: str = ""

    # Exception capture (if any)
    exception_type: str = ""
    exception_message: str = ""

    # SDK metadata
    sdk_import_ok: bool = False
    sdk_version: str = ""  # best-effort; SDK may not expose __version__


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


@dataclass
class ProbeConfig:
    key_id: str
    secret_key: str
    observation_seconds: float


def load_probe_config() -> ProbeConfig:
    """Read required env vars for probe mode. Raises on missing required vars.

    Env-var names are the D-023 canonical names. We do not accept the SDK
    README's illustrative POLYMARKET_KEY_ID / POLYMARKET_SECRET_KEY — those
    are examples, not committed names. See D-023 and Handoff_H-011 for the
    decision record.
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
            os.environ.get("PROBE_OBSERVATION_SECONDS", DEFAULT_OBSERVATION_SECONDS)
        )
    except ValueError:
        observation_seconds = DEFAULT_OBSERVATION_SECONDS
    if observation_seconds <= 0 or observation_seconds > 300:
        # Sanity clamp. 5 minutes is well above the 10s default; beyond that
        # the probe is no longer a probe.
        observation_seconds = DEFAULT_OBSERVATION_SECONDS
    return ProbeConfig(
        key_id=key_id,
        secret_key=secret_key,
        observation_seconds=observation_seconds,
    )


# ---------------------------------------------------------------------------
# Self-check mode — no network
# ---------------------------------------------------------------------------


def run_self_check() -> int:
    """Verify imports, credential presence (by name only), and slug selection.

    Deliberately does NOT construct an SDK client: SDK client construction
    might perform eager authentication work that touches the network or
    logs credential material, and we want the self-check to be a no-op at
    network boundaries.

    Exit 0 on success. Non-zero on the first failed check.
    """
    print("=== pm-tennis stress-test self-check ===", file=sys.stderr)

    # --- Step 1: can we import the SDK at all?
    try:
        import polymarket_us  # noqa: F401

        version = getattr(polymarket_us, "__version__", "<no __version__>")
        print(f"[ok] polymarket_us import ok (version: {version})", file=sys.stderr)
    except ImportError as exc:
        print(f"[FAIL] polymarket_us import failed: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # --- Step 2: can we import the required SDK surfaces we will use in
    # probe mode? We import by name so a typo or SDK breakage is caught here
    # rather than surfacing mid-connection.
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
            "[ok] SDK surfaces AsyncPolymarketUS + exception types importable",
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
    # In self-check, missing credentials are a warning, not a failure. The
    # service is allowed to come up without them; probe mode will error
    # explicitly if they're absent.

    # --- Step 4: slug_selector probe of /data/matches/ (informational only
    # under D-027). On the isolated Render stress-test service this will
    # report 0 candidates by design — Render disks are strictly
    # single-service and the shared-disk architecture is not available. We
    # surface the result either way so a local dev run can verify the
    # fallback path still works.
    try:
        candidates = slug_selector.list_candidates()
    except Exception as exc:  # surface any unexpected filesystem error
        print(f"[warn] slug_selector raised (non-fatal under D-027): {exc!r}", file=sys.stderr)
        candidates = []
    n = len(candidates)
    if n == 0:
        print(
            "[info] 0 probe candidates from slug_selector "
            f"(PMTENNIS_DATA_ROOT={os.environ.get('PMTENNIS_DATA_ROOT', '/data')}). "
            "Expected on Render stress-test service per D-027 — disks are "
            "single-service. Probe mode requires --slug=SLUG from operator.",
            file=sys.stderr,
        )
    else:
        top = candidates[0]
        print(
            f"[ok] {n} probe candidate(s) eligible from slug_selector "
            "(local dev / fallback path); freshest: "
            f"event_id={top.event_id} slug={top.market_slug} "
            f"discovered_at={top.discovered_at} event_date={top.event_date}",
            file=sys.stderr,
        )

    print("=== self-check complete ===", file=sys.stderr)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Probe mode — D-025 (research question) + D-027 (slug-source transport)
# ---------------------------------------------------------------------------


async def _run_probe_async(
    config: ProbeConfig,
    candidate: slug_selector.ProbeCandidate,
    eligible_count: int,
) -> ProbeOutcome:
    """Execute one subscribe / observe / disconnect cycle. No retries.

    Returns the outcome record. Does NOT raise — every exception is captured
    into the outcome's exception_type / exception_message / classification.
    """
    # SDK imports are deferred to inside this function so self-check mode
    # can detect their absence without aborting.
    from polymarket_us import AsyncPolymarketUS  # citation [A]
    from polymarket_us import (  # citation [A] — exception surface
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        BadRequestError,
        NotFoundError,
        RateLimitError,
    )

    outcome = ProbeOutcome(
        probe_started_at_utc=datetime.now(timezone.utc).isoformat(),
        observation_window_seconds=config.observation_seconds,
        event_id=candidate.event_id,
        market_slug=candidate.market_slug,
        candidate_discovered_at=candidate.discovered_at,
        candidate_event_date=candidate.event_date,
        eligible_candidates_count=eligible_count,
        subscription_request_id=f"probe-h013-{int(time.time())}",
        sdk_import_ok=True,
    )
    try:
        import polymarket_us

        outcome.sdk_version = getattr(polymarket_us, "__version__", "")
    except Exception:
        pass

    start_monotonic = time.monotonic()
    first_message_monotonic: Optional[float] = None

    def _bump(event_name: str) -> None:
        outcome.message_count_by_event[event_name] = (
            outcome.message_count_by_event.get(event_name, 0) + 1
        )

    def _on_first(event_name: str, payload: Any) -> None:
        """Record first-message latency and a truncated preview on the first
        message of ANY event type. Idempotent after the first call."""
        nonlocal first_message_monotonic
        if first_message_monotonic is None:
            first_message_monotonic = time.monotonic()
            outcome.first_message_latency_seconds = round(
                first_message_monotonic - start_monotonic, 3
            )
            outcome.first_message_event = event_name
            try:
                preview = repr(payload)
            except Exception:
                preview = "<unreprable payload>"
            outcome.first_message_preview = preview[:500]

    def on_market_data(data: Any) -> None:
        _bump("market_data")
        _on_first("market_data", data)

    def on_market_data_lite(data: Any) -> None:
        _bump("market_data_lite")
        _on_first("market_data_lite", data)

    def on_trade(data: Any) -> None:
        _bump("trade")
        _on_first("trade", data)

    def on_heartbeat(data: Any) -> None:
        _bump("heartbeat")
        _on_first("heartbeat", data)

    def on_error(data: Any) -> None:
        _bump("error")
        try:
            outcome.error_events.append(repr(data)[:500])
        except Exception:
            outcome.error_events.append("<unreprable error>")
        _on_first("error", data)

    def on_close(data: Any) -> None:
        _bump("close")
        try:
            outcome.close_events.append(repr(data)[:500])
        except Exception:
            outcome.close_events.append("<unreprable close>")
        _on_first("close", data)

    # Scoped exception capture. The async-context-manager usage matches the
    # README example exactly.
    try:
        async with AsyncPolymarketUS(
            key_id=config.key_id,
            secret_key=config.secret_key,
        ) as client:
            markets_ws = client.ws.markets()

            # Register handlers BEFORE connect/subscribe. The README shows
            # this ordering.
            markets_ws.on("market_data", on_market_data)
            markets_ws.on("market_data_lite", on_market_data_lite)
            markets_ws.on("trade", on_trade)
            markets_ws.on("heartbeat", on_heartbeat)
            markets_ws.on("error", on_error)
            markets_ws.on("close", on_close)

            await markets_ws.connect()
            outcome.connected = True
            log.info("probe: connected to markets WebSocket")

            await markets_ws.subscribe(
                outcome.subscription_request_id,
                SUBSCRIPTION_TYPE_MARKET_DATA,
                [candidate.market_slug],
            )
            outcome.subscribe_sent = True
            log.info(
                "probe: subscribe sent (request_id=%s slug=%s)",
                outcome.subscription_request_id,
                candidate.market_slug,
            )

            # Observe for the configured window.
            await asyncio.sleep(config.observation_seconds)

            try:
                await markets_ws.close()
            except Exception as exc:
                log.warning("probe: markets_ws.close() raised: %r", exc)

    except AuthenticationError as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "rejected"
        outcome.classification_reason = (
            f"AuthenticationError from SDK: {outcome.exception_message}"
        )
    except BadRequestError as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "rejected"
        outcome.classification_reason = (
            f"BadRequestError from SDK (likely slug rejection): "
            f"{outcome.exception_message}"
        )
    except NotFoundError as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "rejected"
        outcome.classification_reason = (
            f"NotFoundError from SDK (slug not recognized): "
            f"{outcome.exception_message}"
        )
    except RateLimitError as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        # Treat rate-limit as ambiguous, not rejected: it tells us auth
        # succeeded, so the slug path is probably fine. Surface it for the
        # operator to read.
        outcome.classification = "ambiguous"
        outcome.classification_reason = (
            "RateLimitError — auth and subscribe reached the server but we "
            "hit a rate limit before observing messages"
        )
    except (APITimeoutError, APIConnectionError) as exc:
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "exception"
        outcome.classification_reason = (
            f"transport-layer error: {outcome.exception_message}"
        )
    except asyncio.TimeoutError as exc:
        outcome.exception_type = "asyncio.TimeoutError"
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "exception"
        outcome.classification_reason = "asyncio timeout during probe"
    except Exception as exc:
        # Catch-all: if the SDK surfaces an error type not in its documented
        # set, we want to see the type name, not silently bury it.
        outcome.exception_type = type(exc).__name__
        outcome.exception_message = str(exc)[:500]
        outcome.classification = "exception"
        outcome.classification_reason = (
            f"unexpected exception from SDK: {outcome.exception_type}"
        )

    # Finalise timing.
    outcome.probe_ended_at_utc = datetime.now(timezone.utc).isoformat()
    outcome.elapsed_seconds = round(time.monotonic() - start_monotonic, 3)

    # If we never got a classification from an exception branch, derive one
    # from what we observed. Rules:
    #   - Any market_data or heartbeat received => accepted.
    #   - error event received with no other traffic => rejected.
    #   - subscribe_sent but nothing back within the window => ambiguous.
    #   - Not even a connect? Ambiguous (the SDK didn't raise, so we don't
    #     want to call it rejected either).
    if not outcome.classification:
        events = outcome.message_count_by_event
        got_data = (events.get("market_data", 0) + events.get("market_data_lite", 0)) > 0
        got_trade = events.get("trade", 0) > 0
        got_heartbeat = events.get("heartbeat", 0) > 0
        got_error = events.get("error", 0) > 0
        got_close = events.get("close", 0) > 0

        if got_data or got_trade or got_heartbeat:
            outcome.classification = "accepted"
            outcome.classification_reason = (
                f"subscription produced traffic: market_data={events.get('market_data', 0)} "
                f"market_data_lite={events.get('market_data_lite', 0)} "
                f"trade={events.get('trade', 0)} heartbeat={events.get('heartbeat', 0)}"
            )
        elif got_error and not (got_data or got_trade or got_heartbeat):
            outcome.classification = "rejected"
            outcome.classification_reason = (
                f"error event(s) received with no market traffic: "
                f"{outcome.error_events[:3]}"
            )
        elif got_close and not (got_data or got_trade or got_heartbeat or got_error):
            outcome.classification = "ambiguous"
            outcome.classification_reason = (
                f"connection closed without market traffic or explicit error: "
                f"{outcome.close_events[:3]}"
            )
        elif outcome.subscribe_sent:
            outcome.classification = "ambiguous"
            outcome.classification_reason = (
                "subscribe sent; observation window elapsed with no response "
                "and no explicit error — surface to operator per D-025 "
                "commitment 4"
            )
        elif outcome.connected:
            outcome.classification = "ambiguous"
            outcome.classification_reason = "connected but subscribe never sent"
        else:
            outcome.classification = "ambiguous"
            outcome.classification_reason = "connect never completed"

    return outcome


def _classification_to_exit_code(classification: str) -> int:
    """Map classification to process exit code."""
    return {
        "accepted": EXIT_OK,
        "rejected": EXIT_PROBE_REJECTED,
        "ambiguous": EXIT_PROBE_AMBIGUOUS,
        "exception": EXIT_PROBE_EXCEPTION,
    }.get(classification, EXIT_PROBE_AMBIGUOUS)


def run_probe(
    cli_slug: Optional[str] = None,
    cli_event_id: Optional[str] = None,
) -> int:
    """Synchronous entry point for probe mode.

    Per D-027, slug source precedence is:

      1. cli_slug (--slug on the command line) — the production path on
         the isolated pm-tennis-stress-test Render service, where the
         persistent disk is not accessible.
      2. slug_selector.list_candidates() reading from /data/matches/ — the
         local-development and fallback path. Only reachable if the caller
         omits --slug AND the process has disk access to a populated
         PMTENNIS_DATA_ROOT.

    cli_event_id is informational only — used for traceability in the
    outcome record and stderr summary when --slug is given. The probe itself
    only needs the slug string.
    """
    print("=== pm-tennis stress-test probe (D-025 / D-027) ===", file=sys.stderr)

    try:
        config = load_probe_config()
    except KeyError as exc:
        print(f"[FAIL] config error: {exc}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Slug source — operator-supplied takes precedence per D-027.
    candidate: slug_selector.ProbeCandidate
    eligible_count: int

    if cli_slug:
        # Synthetic candidate from CLI args. event_id/discovered_at/event_date
        # may be unknown at this point; that's fine — they're metadata on
        # the outcome record, not inputs to the probe itself.
        candidate = slug_selector.ProbeCandidate(
            event_id=cli_event_id or "",
            market_slug=cli_slug,
            discovered_at="",
            event_date="",
            title="",
        )
        eligible_count = 1  # by definition — operator picked one
        print(
            f"[ok] probe slug supplied via --slug: {cli_slug} "
            f"(event_id={cli_event_id or '<not supplied>'})",
            file=sys.stderr,
        )
    else:
        # Fallback: disk-based slug_selector. In production on Render this
        # path won't find anything (no shared disk), so we surface the
        # condition clearly rather than silently proceeding with whatever
        # slug_selector might return from an unexpected /data mount.
        print(
            "[info] --slug not provided; falling back to slug_selector. "
            "Note: under D-027 the Render stress-test service has no "
            "access to /data/matches/. This path only works in local "
            "development or if PMTENNIS_DATA_ROOT points at a populated "
            "fixture tree.",
            file=sys.stderr,
        )
        try:
            candidates = slug_selector.list_candidates()
        except Exception as exc:
            print(f"[FAIL] slug_selector failed: {exc!r}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

        if not candidates:
            print(
                "[FAIL] no --slug provided and no probe candidates on "
                "disk. Under D-027 the expected invocation is "
                "--slug=SLUG [--event-id=EID]. See RB-002 for the "
                "operator workflow to pick a slug from pm-tennis-api "
                "Shell and pass it in.",
                file=sys.stderr,
            )
            return EXIT_NO_CANDIDATE

        candidate = candidates[0]
        eligible_count = len(candidates)
        print(
            f"[ok] selected probe candidate from slug_selector: "
            f"event_id={candidate.event_id} slug={candidate.market_slug} "
            f"discovered_at={candidate.discovered_at} "
            f"event_date={candidate.event_date} "
            f"(from {eligible_count} eligible)",
            file=sys.stderr,
        )

    outcome = asyncio.run(
        _run_probe_async(config, candidate, eligible_count=eligible_count)
    )

    # Emit structured outcome JSON on stdout so it's trivially scrapable from
    # Render logs. stderr gets the human-readable summary.
    print(json.dumps(asdict(outcome), indent=2, default=str))

    print(
        f"=== probe complete: classification={outcome.classification} "
        f"elapsed={outcome.elapsed_seconds}s ===",
        file=sys.stderr,
    )
    print(f"reason: {outcome.classification_reason}", file=sys.stderr)

    return _classification_to_exit_code(outcome.classification)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.stress_test.probe",
        description=(
            "PM-Tennis Phase 3 attempt 2 stress-test probe. "
            "Default action is a no-network self-check. Pass --probe to "
            "execute the D-025 / D-027 one-slug WebSocket probe."
        ),
    )
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Execute the D-025 / D-027 probe (network, credentials required).",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help=(
            "Market slug to probe (required on Render per D-027; optional "
            "locally — falls back to slug_selector if omitted). Typically a "
            "gateway-sourced slug obtained from the pm-tennis-api Shell; "
            "see Runbook RB-002."
        ),
    )
    parser.add_argument(
        "--event-id",
        default=None,
        help=(
            "Event ID for traceability in the outcome record. Informational "
            "only; the probe does not dispatch on it. Use alongside --slug."
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
    if args.probe:
        return run_probe(cli_slug=args.slug, cli_event_id=args.event_id)
    return run_self_check()


if __name__ == "__main__":
    sys.exit(main())
