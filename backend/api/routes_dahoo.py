"""
Dahoo Assistant REST API Routes for Windows System Monitoring.
Provides chat interactions, dynamic mascot expressions, session memory, and AI transparency metrics.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine.dahoo_engine import dahoo_engine
from backend.engine.aggregator import aggregator
from backend.db import db_manager
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_THINKING_LEVEL, DAHOO_MEMORY_ENABLED

router = APIRouter(prefix="/api/dahoo", tags=["Dahoo"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    use_cloud: bool = False
    thinking_level: Optional[str] = None

class ActionRequest(BaseModel):
    action_type: str
    session_id: Optional[str] = "default"
    action_id: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    confirmed: bool = True

@router.post("/chat")
async def chat_with_dahoo(req: ChatRequest):
    telemetry = aggregator.latest_snapshot or {}
    sid = req.session_id or "default"
    return await dahoo_engine.chat(
        message=req.message,
        telemetry=telemetry,
        session_id=sid,
        use_cloud=req.use_cloud,
        thinking_level=req.thinking_level
    )

@router.post("/action")
async def execute_dahoo_action(req: ActionRequest):
    sid = req.session_id or "default"
    return await dahoo_engine.execute_action(
        action_type=req.action_type,
        params=req.params,
        session_id=sid
    )

@router.post("/session/new")
async def create_new_session(title: Optional[str] = None):
    """Creates a new conversation session for Dahoo."""
    sid = await db_manager.create_or_get_session(None, title=title or "Percakapan Baru")
    return {"session_id": sid, "status": "created"}

@router.get("/history/{session_id}")
async def get_session_history(session_id: str):
    """Fetches recent conversation history for a given session."""
    messages = await db_manager.get_recent_messages(session_id, limit=30)
    return {"session_id": session_id, "messages": messages}

@router.delete("/history/{session_id}")
async def clear_session_history(session_id: str):
    """Clears conversation history and pending actions for a session."""
    await db_manager.clear_session_messages(session_id)
    dahoo_engine._clear_pending_action(session_id)
    return {"session_id": session_id, "status": "cleared"}

@router.get("/state")
async def get_dahoo_state():
    telemetry = aggregator.latest_snapshot or {}
    health = telemetry.get("health", {})
    score = health.get("score", 100)
    cpu = telemetry.get("cpu", {}).get("total_percent", 0.0)
    threats = telemetry.get("threats", [])

    expression = dahoo_engine.get_expression(score, len(threats), cpu)

    # Contextual proactive speech
    proactive = "Semua sistem berjalan prima dan optimal."
    if len(threats) > 0:
        proactive = f"Aww! Ada {len(threats)} anomali yang perlu kita periksa di Threat Center."
    elif cpu > 80:
        top_proc = telemetry.get("process", {}).get("top_cpu", [{}])[0].get("name", "proses")
        proactive = f"Beban CPU sedang cukup tinggi ({cpu}%), dipicu oleh {top_proc}."
    elif score < 60:
        proactive = "Kondisi sistem saat ini membutuhkan perhatian."

    return {
        "expression": expression,
        "health_score": score,
        "proactive_speech": proactive,
        "cloud_available": bool(GEMINI_API_KEY),
        "cloud_model": GEMINI_MODEL if GEMINI_API_KEY else "Not configured (Offline Local Engine Active)",
        "thinking_level": GEMINI_THINKING_LEVEL,
        "memory_enabled": DAHOO_MEMORY_ENABLED
    }

@router.get("/metrics")
async def get_dahoo_metrics():
    """Returns AI cost and token consumption transparency."""
    stats = await db_manager.get_dahoo_metrics()
    stats["cloud_configured"] = bool(GEMINI_API_KEY)
    stats["model"] = GEMINI_MODEL
    stats["thinking_level"] = GEMINI_THINKING_LEVEL
    return stats

