"""
Activity REST API Routes for Windows System Monitoring.
Handles processes, network sockets, Windows services, and secure process termination.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.engine.aggregator import aggregator

router = APIRouter(prefix="/api/activity", tags=["Activity"])

class TerminateRequest(BaseModel):
    pid: int
    confirm: bool

@router.get("/processes")
async def get_processes():
    return aggregator.process_collector.last_data or aggregator.process_collector.collect_safe()

@router.get("/process/{pid}")
async def get_process_detail(pid: int):
    """Finds detailed telemetry for a single process."""
    data = aggregator.process_collector.last_data or aggregator.process_collector.collect_safe()
    for p in data.get("processes", []):
        if p["pid"] == pid:
            return p
    raise HTTPException(status_code=404, detail="Process not found or already terminated.")

@router.post("/process/terminate")
async def terminate_process(req: TerminateRequest):
    """Safely terminates a process only after confirmation."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation required to terminate process.")
    # Protected PIDs safeguard
    if req.pid in (0, 4):
        raise HTTPException(status_code=403, detail="Cannot terminate Windows core kernel process.")
    res = aggregator.process_collector.terminate_process(req.pid)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.get("/sockets")
async def get_sockets():
    return aggregator.socket_collector.last_data or aggregator.socket_collector.collect_safe()

@router.get("/services")
async def get_services():
    return aggregator.services_collector.last_data or aggregator.services_collector.collect_safe()
