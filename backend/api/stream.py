"""
Server-Sent Events (SSE) streaming route for Windows System Monitoring.
Pushes real-time normalized telemetry frames to web frontend.
"""

import asyncio
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.engine.aggregator import aggregator

router = APIRouter(prefix="/api/stream", tags=["Streaming"])

@router.get("/realtime")
async def stream_realtime():
    """SSE endpoint delivering live 1-second system telemetry frames."""
    async def event_generator():
        q = aggregator.subscribe()
        try:
            # Yield latest cached snapshot immediately so UI doesn't wait
            if aggregator.latest_snapshot:
                yield f"data: {json.dumps(aggregator.latest_snapshot)}\n\n"

            while True:
                data = await q.get()
                yield f"data: {json.dumps(data)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            aggregator.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
