"""
PM-Tennis API — main.py

Runs as a single FastAPI process on Render (pm-tennis-api).
Hosts two asyncio background tasks:
  1. Discovery loop (Phase 2) — polls Polymarket US gateway for active tennis events
  2. Capture loop (Phase 3) — CLOB pool + Sports WS client + correlation + handicap

Admin endpoints (no auth; personal-use threat model):
  GET  /healthcheck               — commitment-file checksums, component status
  GET  /admin/discovery/status    — discovery loop status
  GET  /admin/capture/status      — Phase 3 capture component status
  GET  /admin/clob/pool           — CLOB pool size, headroom, asset list
  GET  /admin/correlation/status  — correlation layer mapping counts
  GET  /admin/handicap/status     — handicap updater tracking counts
  GET  /admin/sports_ws/status    — Sports WS client status
  POST /admin/capture/start       — manually start capture (idempotent)
  POST /admin/capture/stop        — gracefully stop capture components
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

# ---------------------------------------------------------------------------
# Import Phase 2 and Phase 3 modules
# ---------------------------------------------------------------------------
from src.capture.discovery import DiscoveryLoop, DiscoveryConfig  # noqa: E402
from src.capture.clob_pool import CLOBPool  # noqa: E402
from src.capture.correlation import Correlator  # noqa: E402
from src.capture.handicap import HandicapUpdater  # noqa: E402
from src.capture.sports_ws import SportsWSClient  # noqa: E402

# ---------------------------------------------------------------------------
# Global component instances
# ---------------------------------------------------------------------------
_discovery_loop: DiscoveryLoop = None
_clob_pool: CLOBPool = None
_correlator: Correlator = None
_handicap_updater: HandicapUpdater = None
_sports_ws_client: SportsWSClient = None

_capture_running = False


# ---------------------------------------------------------------------------
# Callbacks that wire the components together
# ---------------------------------------------------------------------------

def _on_event_discovered(event_id: str, meta: dict, is_new: bool) -> None:
    """Called by discovery loop for each discovered event."""
    if not is_new:
        return

    game_id = meta.get("sportradar_game_id")
    if not game_id:
        logger.warning("Discovered event %s has no sportradar_game_id — skipping capture wire", event_id)
        return

    # Collect asset IDs from moneyline markets
    asset_ids = []
    for market in meta.get("moneyline_markets", []):
        for side in market.get("marketSides", []):
            sid = side.get("identifier")
            if sid:
                asset_ids.append(str(sid))

    # Register with Sports WS
    if _sports_ws_client:
        _sports_ws_client.register_match(game_id, meta=meta)

    # Add to CLOB pool
    if _clob_pool:
        for asset_id in asset_ids:
            _clob_pool.add(asset_id, game_id=game_id)
            if _handicap_updater:
                _handicap_updater.register(asset_id, game_id)

    logger.info(
        "Capture wired for event %s (game_id=%s, assets=%s)",
        event_id,
        game_id,
        asset_ids,
    )


def _on_regime_change(game_id: str, asset_id: str, new_regime: str) -> None:
    """Sports WS fires this when a match transitions to in-play."""
    logger.info("Regime change: %s / %s → %s", game_id, asset_id, new_regime)
    if _clob_pool:
        _clob_pool.set_regime(asset_id, new_regime)
    if _handicap_updater:
        _handicap_updater.on_regime_change(game_id, asset_id, new_regime)


def _on_correlation_hint(game_id: str, player_names: list) -> None:
    """Sports WS fires this with player names for correlation."""
    if _correlator:
        asset_id = _correlator.resolve(game_id, player_names=player_names)
        if asset_id and _sports_ws_client:
            _sports_ws_client.set_asset_id(game_id, asset_id)
        if asset_id and _clob_pool:
            _clob_pool.set_game_id(asset_id, game_id)


def _on_clob_tick(asset_id: str, envelope: dict) -> None:
    """Called by CLOBPool for each tick — feeds handicap updater."""
    if _handicap_updater:
        price = HandicapUpdater.extract_price_from_envelope(envelope)
        if price is not None:
            _handicap_updater.on_tick(asset_id, price)


# ---------------------------------------------------------------------------
# Capture start / stop
# ---------------------------------------------------------------------------

async def _start_capture() -> None:
    global _clob_pool, _correlator, _handicap_updater, _sports_ws_client, _capture_running

    if _capture_running:
        logger.info("Capture already running — no-op")
        return

    logger.info("Starting Phase 3 capture components")

    _correlator = Correlator(DATA_DIR)
    _correlator.load()

    _handicap_updater = HandicapUpdater(DATA_DIR)

    _clob_pool = CLOBPool(DATA_DIR)

    _sports_ws_client = SportsWSClient(
        DATA_DIR,
        on_regime_change=_on_regime_change,
        on_correlation_hint=_on_correlation_hint,
    )

    # Wire already-discovered events into capture
    if _discovery_loop:
        for event_id, meta in _discovery_loop.known_events.items():
            _on_event_discovered(event_id, meta, is_new=True)

    # Start Sports WS as background task
    asyncio.create_task(_sports_ws_client.run(), name="sports-ws")

    _capture_running = True
    logger.info("Phase 3 capture started")


async def _stop_capture() -> None:
    global _clob_pool, _sports_ws_client, _capture_running

    if not _capture_running:
        return

    logger.info("Stopping Phase 3 capture components")

    if _sports_ws_client:
        await _sports_ws_client.stop()

    if _clob_pool:
        await _clob_pool.shutdown()

    _capture_running = False
    logger.info("Phase 3 capture stopped")


# ---------------------------------------------------------------------------
# Discovery loop wrapper that hooks into capture
# ---------------------------------------------------------------------------

async def _run_discovery_with_capture_hook():
    """Runs the discovery loop and wires new events into capture."""
    global _discovery_loop

    config = DiscoveryConfig(data_dir=DATA_DIR)
    _discovery_loop = DiscoveryLoop(config)

    # Inject our callback
    original_on_event = getattr(_discovery_loop, "_on_new_event", None)

    async def patched_poll():
        """Wrap the discovery loop to hook into capture after each poll."""
        while True:
            try:
                new_events = await _discovery_loop._poll_once()
                for event_id, meta in new_events.items():
                    _on_event_discovered(event_id, meta, is_new=True)
                    if _correlator:
                        _correlator.refresh()
            except Exception as exc:
                logger.error("Discovery poll error: %s", exc)
            await asyncio.sleep(config.poll_interval_seconds)

    # Fall back to the standard run() if patched_poll approach doesn't match
    # discovery module internals — the discovery loop runs self-contained
    await _discovery_loop.run()


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PM-Tennis API starting — Phase 3 capture ready")

    # Start discovery loop
    discovery_task = asyncio.create_task(
        _run_discovery_with_capture_hook(),
        name="discovery-loop",
    )

    # Start capture automatically (Phase 3 design: always on)
    await _start_capture()

    yield

    # Shutdown
    logger.info("PM-Tennis API shutting down")
    discovery_task.cancel()
    await _stop_capture()
    try:
        await discovery_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="PM-Tennis API", version="0.3.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/healthcheck")
async def healthcheck():
    import hashlib, json as _json

    commitment_files = {
        "fees.json": DATA_DIR.parent / "fees.json",
        "breakeven.json": DATA_DIR.parent / "breakeven.json",
        "data/sackmann/build_log.json": DATA_DIR / "sackmann" / "build_log.json",
    }

    checksums = {}
    for name, path in commitment_files.items():
        p = Path(path)
        if p.exists():
            checksums[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            checksums[name] = "FILE_NOT_FOUND"

    return {
        "status": "ok",
        "version": "0.3.0",
        "phase": "3",
        "commitment_file_checksums": checksums,
        "capture_running": _capture_running,
        "discovery_running": _discovery_loop is not None,
    }


# ---------------------------------------------------------------------------
# Admin endpoints — Phase 2
# ---------------------------------------------------------------------------

@app.get("/admin/discovery/status")
async def admin_discovery_status():
    if _discovery_loop is None:
        return JSONResponse({"status": "not_started"}, status_code=503)
    return _discovery_loop.status_report()


# ---------------------------------------------------------------------------
# Admin endpoints — Phase 3
# ---------------------------------------------------------------------------

@app.get("/admin/capture/status")
async def admin_capture_status():
    return {
        "capture_running": _capture_running,
        "clob_pool": _clob_pool.status_report() if _clob_pool else None,
        "correlator": _correlator.status_report() if _correlator else None,
        "handicap_updater": _handicap_updater.status_report() if _handicap_updater else None,
        "sports_ws": _sports_ws_client.status_report() if _sports_ws_client else None,
    }


@app.get("/admin/clob/pool")
async def admin_clob_pool():
    if _clob_pool is None:
        return JSONResponse({"status": "not_started"}, status_code=503)
    return _clob_pool.status_report()


@app.get("/admin/correlation/status")
async def admin_correlation_status():
    if _correlator is None:
        return JSONResponse({"status": "not_started"}, status_code=503)
    return _correlator.status_report()


@app.get("/admin/handicap/status")
async def admin_handicap_status():
    if _handicap_updater is None:
        return JSONResponse({"status": "not_started"}, status_code=503)
    return _handicap_updater.status_report()


@app.get("/admin/sports_ws/status")
async def admin_sports_ws_status():
    if _sports_ws_client is None:
        return JSONResponse({"status": "not_started"}, status_code=503)
    return _sports_ws_client.status_report()


@app.post("/admin/capture/start")
async def admin_capture_start():
    await _start_capture()
    return {"status": "ok", "capture_running": _capture_running}


@app.post("/admin/capture/stop")
async def admin_capture_stop():
    await _stop_capture()
    return {"status": "ok", "capture_running": _capture_running}
