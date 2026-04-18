"""
PM-Tennis API — placeholder.
This file is the minimal FastAPI application deployed to Render.
It will be replaced with the full API in Phase 4.
"""

from fastapi import FastAPI
import os
import datetime

app = FastAPI(title="PM-Tennis API", version="0.0.1-placeholder")


@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "ok",
        "service": "pm-tennis-api",
        "version": "0.0.1-placeholder",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "note": "Placeholder application. Phase 4 will replace this with the full API."
    }


@app.get("/")
def root():
    return {"service": "pm-tennis-api", "status": "placeholder"}
