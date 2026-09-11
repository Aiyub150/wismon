"""
Comprehensive Verification Test Suite for Windows System Monitoring.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.db import db_manager
from backend.collectors import (
    CPUCollector,
    MemoryCollector,
    GPUCollector,
    StorageCollector,
    NetworkCollector,
    ProcessCollector,
    SocketCollector,
    ServicesCollector,
    HardwareCollector
)
from backend.engine.aggregator import aggregator
from backend.engine.analysis import AnalysisEngine
from backend.engine.storage_analyzer import storage_analyzer
from backend.engine.dahoo_engine import dahoo_engine

async def run_tests():
    print("=== 1. Testing Database Initialization ===")
    await db_manager.initialize()
    print("[OK] Database initialized successfully.")

    print("\n=== 2. Testing Telemetry Collectors ===")
    cpu = CPUCollector().collect_safe()
    print(f"[OK] CPU: {cpu['processor_name']} | Total: {cpu['total_percent']}% | Cores: {cpu['physical_cores']}P/{cpu['logical_cores']}L")

    mem = MemoryCollector().collect_safe()
    print(f"[OK] RAM: {mem['percent']}% | Paged: {mem['deep']['paged_pool']} bytes | Commit: {mem['deep']['commit_charge']} bytes")

    gpu = GPUCollector().collect_safe()
    print(f"[OK] GPU: {gpu['name']} | Status: {gpu['status']}")

    storage = StorageCollector().collect_safe()
    print(f"[OK] Storage: {len(storage['drives'])} drives | Read: {storage['io']['read_bytes_sec']} B/s | Write: {storage['io']['write_bytes_sec']} B/s")

    net = NetworkCollector().collect_safe()
    print(f"[OK] Network: {len(net['interfaces'])} interfaces | Throughput: Sent {net['throughput']['bytes_sent_sec']} B/s")

    proc = ProcessCollector().collect_safe()
    print(f"[OK] Processes: {proc['total_count']} active processes | Top CPU: {proc['top_cpu'][0]['name']}")

    sock = SocketCollector().collect_safe()
    print(f"[OK] Sockets: {sock['total_connections']} connections ({sock['established_count']} established)")

    serv = ServicesCollector().collect_safe()
    print(f"[OK] Services: {serv['total_count']} services | svchost groups: {len(serv['svchost_groups'])}")

    hw = HardwareCollector().collect_safe()
    print(f"[OK] Hardware: OS {hw['system_info']['system']} {hw['system_info']['release']} | Battery: {hw['battery']['status']}")

    print("\n=== 3. Testing Analysis Engine & Health Scoring ===")
    analysis = AnalysisEngine()
    health = analysis.calculate_health(cpu['total_percent'], mem['percent'], storage['overall']['percent'], 0)
    print(f"[OK] Health Score: {health['score']}/100 ({health['status']})")

    print("\n=== 4. Testing Storage Analyzer ===")
    scan_res = storage_analyzer.scan()
    print(f"[OK] Storage Analyzer: {scan_res['temp_cleanup']['total_mb']} MB in Temp ({scan_res['temp_cleanup']['file_count']} files)")

    print("\n=== 5. Testing Dahoo Local Engine ===")
    sample_snapshot = {
        "cpu": cpu,
        "memory": mem,
        "storage": storage,
        "network": net,
        "health": health,
        "process": proc,
        "threats": []
    }
    dahoo_reply = await dahoo_engine.chat("Berapa penggunaan CPU saat ini?", sample_snapshot, use_cloud=False)
    print(f"[OK] Dahoo Reply:\n{dahoo_reply['reply']}")

    print("\n=== ALL SYSTEM TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
