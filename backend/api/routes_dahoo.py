"""
Dahoo Assistant REST API Routes for Windows System Monitoring.
Provides chat interactions, dynamic mascot expressions, and AI cost transparency metrics.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from backend.engine.dahoo_engine import dahoo_engine
from backend.engine.aggregator import aggregator
from backend.db import db_manager
from backend.config import GEMINI_API_KEY, GEMINI_MODEL

router = APIRouter(prefix="/api/dahoo", tags=["Dahoo"])

class ChatRequest(BaseModel):
    message: str
    use_cloud: bool = False

@router.post("/chat")
async def chat_with_dahoo(req: ChatRequest):
    telemetry = aggregator.latest_snapshot or {}
    return await dahoo_engine.chat(req.message, telemetry, use_cloud=req.use_cloud)

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
        "cloud_model": GEMINI_MODEL if GEMINI_API_KEY else "Not configured (Offline Local Engine Active)"
    }

@router.get("/metrics")
async def get_dahoo_metrics():
    """Returns AI cost and token consumption transparency."""
    stats = await db_manager.get_dahoo_metrics()
    stats["cloud_configured"] = bool(GEMINI_API_KEY)
    stats["model"] = GEMINI_MODEL
    return stats
