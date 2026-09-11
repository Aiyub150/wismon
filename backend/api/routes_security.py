"""
Security & Threat Center REST API Routes for Windows System Monitoring.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.engine.threat_center import threat_center
from backend.engine.aggregator import aggregator
from backend.db import db_manager

router = APIRouter(prefix="/api/security", tags=["Security"])

class MitigateRequest(BaseModel):
    threat_id: str
    action: str  # TERMINATE_PROCESS, RESOLVE, FALSE_POSITIVE
    confirm: bool

@router.get("/threats")
async def get_active_threats():
    return threat_center.get_threats()

@router.get("/events")
async def get_threat_history(limit: int = 100):
    return await db_manager.get_all_threats(limit=limit)

@router.post("/mitigate")
async def mitigate_threat(req: MitigateRequest):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Explicit confirmation required to execute mitigation.")

    threats = {t["id"]: t for t in threat_center.get_threats()}
    target_threat = threats.get(req.threat_id)
    if not target_threat:
        raise HTTPException(status_code=404, detail="Threat event not found.")

    if req.action == "TERMINATE_PROCESS":
        pid = target_threat.get("pid")
        if not pid:
            raise HTTPException(status_code=400, detail="No target process PID associated with this threat.")
        term_res = aggregator.process_collector.terminate_process(pid)
        if not term_res["success"]:
            raise HTTPException(status_code=500, detail=term_res["message"])
        await threat_center.update_threat_status(req.threat_id, "RESOLVED", action=f"Terminated process PID {pid}")
        return {"success": True, "message": f"Threat mitigated: Process {pid} terminated."}

    elif req.action == "RESOLVE":
        await threat_center.update_threat_status(req.threat_id, "RESOLVED", action="Manually marked resolved by user.")
        return {"success": True, "message": "Threat marked as resolved."}

    elif req.action == "FALSE_POSITIVE":
        await threat_center.update_threat_status(req.threat_id, "FALSE_POSITIVE", action="Flagged as false positive by user.")
        return {"success": True, "message": "Threat flagged as false positive."}

    raise HTTPException(status_code=400, detail="Unsupported mitigation action.")
