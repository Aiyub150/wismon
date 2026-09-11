"""
Telemetry REST API Routes for Windows System Monitoring.
"""

from fastapi import APIRouter
from backend.engine.aggregator import aggregator

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.get("/current")
async def get_current_snapshot():
    """Returns the latest consolidated telemetry snapshot."""
    return aggregator.latest_snapshot or aggregator.ring_buffer[-1] if aggregator.ring_buffer else {}

@router.get("/cpu")
async def get_cpu():
    return aggregator.cpu_collector.last_data or aggregator.cpu_collector.collect_safe()

@router.get("/memory")
async def get_memory():
    return aggregator.mem_collector.last_data or aggregator.mem_collector.collect_safe()

@router.get("/storage")
async def get_storage():
    return aggregator.storage_collector.last_data or aggregator.storage_collector.collect_safe()

@router.get("/network")
async def get_network():
    return aggregator.network_collector.last_data or aggregator.network_collector.collect_safe()

@router.get("/gpu")
async def get_gpu():
    return aggregator.gpu_collector.last_data or aggregator.gpu_collector.collect_safe()

@router.get("/hardware")
async def get_hardware():
    return aggregator.hardware_collector.last_data or aggregator.hardware_collector.collect_safe()
