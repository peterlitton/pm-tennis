"""
PM-Tennis API — placeholder + Phase 2 discovery background task.

The FastAPI app serves the /healthcheck and / endpoints (Phase 4 will
replace these with the full API). On startup it launches the discovery
loop as an asyncio background task so it shares the process, the disk,
and the event loop with the web server.

Architecture note: running discovery inside the web service is the correct
approach for Render because persistent disks are per-service and cannot be
shared between services. The discovery loop writes to /data; the Phase 4
API reads from /data. Both live in the same process here.
"""

import asyncio
import datetime
import logging
import os

from fastapi import FastAPI

log = logging.getLogger("pm_tennis.main")

app = FastAPI(title="PM-Tennis API", version="0.1.0-phase2")


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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "ok",
        "service": "pm-tennis-api",
        "version": "0.1.0-phase2",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "phase": "2 — discovery running",
    }


@app.get("/")
def root():
    return {"service": "pm-tennis-api", "status": "phase2"}
