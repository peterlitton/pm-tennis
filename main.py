"""
PM-Tennis API — placeholder + Phase 2 discovery background task + Phase 3 CLOB capture pool.

The FastAPI app serves the /healthcheck and / endpoints (Phase 4 will
replace these with the full API). On startup it launches two independent
asyncio background tasks — the discovery loop and the CLOB capture pool —
both sharing the process, the disk, and the event loop with the web server.

Architecture note: running discovery and capture inside the web service is
the correct approach for Render because persistent disks are per-service
and cannot be shared between services. The discovery loop writes to
/data/matches; the CLOB pool tails /data/events/discovery_delta.jsonl and
writes to /data/clob. The Phase 4 API reads from /data. All live in the
same process here.
"""

import asyncio
import datetime
import logging
import os
import tracemalloc

from fastapi import FastAPI

log = logging.getLogger("pm_tennis.main")

# H-032 instrumentation: start tracemalloc before any background tasks
# launch so the heavy_snapshot_loop has trace data to surface. Cheap
# in idle but adds per-allocation overhead — acceptable for diagnostic
# observation window; revisit after Mechanism 1 source identified.
tracemalloc.start()

app = FastAPI(title="PM-Tennis API", version="0.1.0-phase3-capture")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def start_discovery():
    """
    Launch the discovery loop as a fire-and-forget asyncio task.
    The task runs for the lifetime of the process. If it crashes, the
    exception is logged and the task retries after a delay so the web
    server is never taken down by discovery failures.
    """
    async def _run():
        retry_delay = 30
        while True:
            try:
                from src.capture.discovery import (
                    GatewayClient, DiscoveryLoop,
                    TENNIS_SPORT_SLUG, verify_sport_slug,
                )
                client = GatewayClient()
                slug_ok = await verify_sport_slug(client, TENNIS_SPORT_SLUG)
                if not slug_ok:
                    log.warning(
                        "Discovery: sport slug %r not verified. Poll loop will run "
                        "but may return empty results.", TENNIS_SPORT_SLUG
                    )
                loop = DiscoveryLoop(client, TENNIS_SPORT_SLUG)
                await loop.run_forever()
            except Exception as exc:
                log.critical(
                    "Discovery background task crashed: %s — retrying in %ds",
                    exc, retry_delay, exc_info=True,
                )
                await asyncio.sleep(retry_delay)

    asyncio.create_task(_run())
    log.info("Discovery background task started.")


@app.on_event("startup")
async def start_clob_pool():
    """
    Launch the CLOB capture pool as a fire-and-forget asyncio task.
    Pattern mirrors start_discovery: runs for the lifetime of the process,
    retries on crash after a delay, never takes down the web server.

    Credentials are read from POLYMARKET_US_API_KEY_ID and
    POLYMARKET_US_API_SECRET_KEY (per D-023). If credentials are missing
    at startup (e.g. first deploy before env vars set in Render dashboard),
    the task logs CRITICAL and retries; operator can set credentials
    without redeploying.
    """
    async def _run():
        retry_delay = 30
        while True:
            try:
                from polymarket_us import AsyncPolymarketUS
                from src.capture.clob_pool import ClobPool
                from src.capture.archive_writer import ArchiveWriter

                key_id = os.environ.get("POLYMARKET_US_API_KEY_ID")
                secret_key = os.environ.get("POLYMARKET_US_API_SECRET_KEY")
                if not key_id or not secret_key:
                    log.critical(
                        "CLOB pool: POLYMARKET_US_API_KEY_ID/SECRET_KEY missing — "
                        "pool cannot start. Retrying in %ds (credentials may be "
                        "set via Render dashboard without a redeploy).",
                        retry_delay,
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                client = AsyncPolymarketUS(key_id=key_id, secret_key=secret_key)
                archive = ArchiveWriter()
                pool = ClobPool(client, archive)
                await pool.run_forever()
            except Exception as exc:
                log.critical(
                    "CLOB pool background task crashed: %s — retrying in %ds",
                    exc, retry_delay, exc_info=True,
                )
                await asyncio.sleep(retry_delay)

    asyncio.create_task(_run())
    log.info("CLOB pool background task started.")


@app.on_event("startup")
async def start_diagnostics_loops():
    """
    Launch H-032 diagnostics loops (5-min heavy snapshot, 1-min task
    snapshot). Background tasks; references kept on app.state so asyncio
    does not GC them per its create_task docs warning.
    """
    from src.capture.diagnostics import start_diagnostics
    heavy_task, task_task = start_diagnostics()
    # Hold references to prevent GC.
    app.state.diagnostics_heavy_task = heavy_task
    app.state.diagnostics_task_task = task_task
    log.info("Diagnostics background tasks started.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "ok",
        "service": "pm-tennis-api",
        "version": "0.1.0-phase3-capture",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "phase": "3 — capture running",
    }


@app.get("/")
def root():
    return {"service": "pm-tennis-api", "status": "phase3"}
