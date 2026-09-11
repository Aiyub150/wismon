"""
FastAPI Main Application Entrypoint for Windows System Monitoring.
Mounts REST endpoints, SSE streams, and static frontend assets.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import STATIC_DIR
from backend.db import db_manager
from backend.engine.aggregator import aggregator

# Routers
from backend.api.stream import router as stream_router
from backend.api.routes_telemetry import router as telemetry_router
from backend.api.routes_activity import router as activity_router
from backend.api.routes_security import router as security_router
from backend.api.routes_analysis import router as analysis_router
from backend.api.routes_dahoo import router as dahoo_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SystemMonitoring.Main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Windows System Monitoring backend...")
    await db_manager.initialize()
    await aggregator.start()
    yield
    # Shutdown
    logger.info("Stopping telemetry aggregator and flushing database...")
    await aggregator.stop()

app = FastAPI(
    title="Windows System Monitoring",
    description="Advanced system observability, threat detection, and telemetry platform for Windows.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(stream_router)
app.include_router(telemetry_router)
app.include_router(activity_router)
app.include_router(security_router)
app.include_router(analysis_router)
app.include_router(dahoo_router)

# Mount frontend static files
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Windows System Monitoring API is running. Frontend assets not yet initialized."}
