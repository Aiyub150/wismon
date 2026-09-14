"""
Analysis & History REST API Routes for Windows System Monitoring.
"""

from fastapi import APIRouter, Query
from backend.engine.aggregator import aggregator
from backend.engine.storage_analyzer import storage_analyzer
from backend.db import db_manager

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

@router.get("/baseline")
async def get_baseline():
    return aggregator.analysis_engine.get_baseline_stats()

@router.get("/cpu_workload")
async def get_cpu_workload():
    cpu_data = aggregator.cpu_collector.last_data or {}
    total_cpu = cpu_data.get("total_percent", 0.0)
    proc_data = aggregator.process_collector.last_data or {}
    top_proc = proc_data.get("top_cpu", [{}])[0] if proc_data.get("top_cpu") else {}
    return aggregator.analysis_engine.analyze_cpu_workload(total_cpu, top_proc)

from pydantic import BaseModel, Field
from typing import Optional

class StorageScanRequest(BaseModel):
    drive: Optional[str] = Field(None, description="Target drive letter (e.g. C:, D:, E:) or directory to scan")

@router.post("/storage/scan")
async def trigger_storage_scan(payload: Optional[StorageScanRequest] = None):
    """Executes a scan for large files, unused folders, and temporary files on a designated drive or all drives."""
    target_drive = payload.drive if payload else None
    return storage_analyzer.scan(target_drive=target_drive)

@router.get("/storage/last")
async def get_last_storage_scan():
    return storage_analyzer.get_last_scan()

from pydantic import BaseModel, Field

class StorageDeleteRequest(BaseModel):
    filepath: str = Field(..., description="Absolute path of the file to move to the Windows Recycle Bin")

@router.post("/storage/delete")
async def delete_storage_file(payload: StorageDeleteRequest):
    """Safely moves a selected temporary or large file to the Windows Recycle Bin."""
    return storage_analyzer.move_to_recycle_bin(payload.filepath)

@router.get("/history")
async def get_telemetry_history(seconds: int = Query(default=3600, ge=30, le=86400)):
    """Fetches historical time-series telemetry from SQLite."""
    return await db_manager.get_history(duration_seconds=seconds)

