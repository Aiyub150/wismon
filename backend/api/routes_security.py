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

    action_msg = "Threat marked as resolved."
    action_log = "Manually marked resolved by user."

    if req.action == "TERMINATE_PROCESS":
        pid = target_threat.get("pid")
        if not pid:
            raise HTTPException(status_code=400, detail="No target process PID associated with this threat.")
        term_res = aggregator.process_collector.terminate_process(pid)
        if not term_res["success"]:
            return {
                "success": False,
                "message": term_res["message"],
                "can_fallback": True,
                "suggested_actions": [
                    {"label": "Tandai False Positive (Aman)", "action": "FALSE_POSITIVE"}
                ]
            }
        action_log = f"Terminated process PID {pid}"
        action_msg = f"Threat mitigated: Process {pid} terminated."
        await threat_center.update_threat_status(req.threat_id, "RESOLVED", action=action_log)
        return {"success": True, "message": action_msg}

    elif req.action in ("RESOLVE", "COOLDOWN_PROCESS", "THROTTLE_PROCESS"):
        category = target_threat.get("category", "")
        pid = target_threat.get("pid")

        # 1. High CPU Process Remediation: Pause / Cooldown with multi-tier fallback
        if (category == "High CPU Process" or req.action in ("COOLDOWN_PROCESS", "THROTTLE_PROCESS")) and pid:
            cool_res = await threat_center.throttle_and_cooldown_process(pid, duration=3.5)
            if cool_res.get("success"):
                action_log = cool_res["message"]
                await threat_center.update_threat_status(req.threat_id, "RESOLVED", action=action_log)
                return {"success": True, "message": cool_res["message"]}
            else:
                # Remediation failed: DO NOT resolve! Return failure details and fallback tools
                return {
                    "success": False,
                    "message": cool_res["message"],
                    "can_fallback": cool_res.get("can_fallback", True),
                    "suggested_actions": cool_res.get("suggested_actions", [
                        {"label": "Paksa Hentikan (Kill)", "action": "TERMINATE_PROCESS"},
                        {"label": "Tandai False Positive (Aman)", "action": "FALSE_POSITIVE"}
                    ])
                }

        # 2. Memory Exhaustion Remediation: Trim working set memory
        elif category == "System Anomaly" or "Memory" in category:
            trim_res = threat_center.trim_system_memory()
            if trim_res.get("success"):
                action_log = trim_res["message"]
                action_msg = f"Mitigasi Memori Selesai: {trim_res['message']}"
                await threat_center.update_threat_status(req.threat_id, "RESOLVED", action=action_log)
                return {"success": True, "message": action_msg}
            else:
                return {"success": False, "message": trim_res["message"]}

        else:
            action_log = "Status diverifikasi dan diselesaikan oleh administrator sistem."
            action_msg = "Anomali berhasil diselesaikan dan dicatat."
            await threat_center.update_threat_status(req.threat_id, "RESOLVED", action=action_log)
            return {"success": True, "message": action_msg}

    elif req.action == "FALSE_POSITIVE":
        await threat_center.update_threat_status(req.threat_id, "FALSE_POSITIVE", action="Flagged as false positive by user.")
        return {"success": True, "message": "Ancaman ditandai sebagai False Positive (Aman)."}

    raise HTTPException(status_code=400, detail="Unsupported mitigation action.")
