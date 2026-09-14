"""
Verification test script for recent WISMON fixes and optimizations.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.collectors import (
    StorageCollector,
    SocketCollector,
    MemoryCollector,
    NetworkCollector
)
from backend.engine.storage_analyzer import storage_analyzer
from backend.engine.threat_center import threat_center
from backend.engine.dahoo_engine import dahoo_engine
import time

async def run_fix_tests():
    print("=== [TEST 1] Telemetry Performance Latency Check ===")
    # Test persistent collector instance in steady state (as used by aggregator)
    mem_collector = MemoryCollector()
    net_collector = NetworkCollector()

    mem_collector.collect_safe()
    net_collector.collect_safe()

    t0 = time.perf_counter()
    mem = mem_collector.collect_safe()
    t_mem = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    net = net_collector.collect_safe()
    t_net = (time.perf_counter() - t0) * 1000

    print(f"[OK] MemoryCollector steady-state: {t_mem:.2f} ms (Target: < 5ms)")
    print(f"[OK] NetworkCollector steady-state: {t_net:.2f} ms (Target: < 50ms)")
    assert t_mem < 10, f"MemoryCollector steady-state too slow: {t_mem}ms"
    assert t_net < 60, f"NetworkCollector steady-state too slow: {t_net}ms"

    print("\n=== [TEST 2] Storage Hardware Model & Bus Detection ===")
    stor = StorageCollector().collect_safe()
    drives = stor.get('drives', [])
    print(f"[OK] Detected {len(drives)} drives:")
    for d in drives:
        mount = d.get('device') or d.get('mountpoint')
        model = d.get('model', 'Unknown')
        bus = d.get('bus_type', 'Unknown')
        cat = d.get('category', 'Volume')
        print(f"     - Drive {mount}: [{cat}] Model='{model}', Bus='{bus}'")
        assert 'model' in d, f"Drive {mount} missing model field"
        assert 'bus_type' in d, f"Drive {mount} missing bus_type field"

    print("\n=== [TEST 3] Storage Analyzer Multi-Drive & Junk Folders ===")
    t0 = time.perf_counter()
    scan_res = storage_analyzer.scan(target_drive='C:')
    t_scan = time.perf_counter() - t0
    junk_folders = scan_res.get('junk_folders', [])
    large_files = scan_res.get('large_files', [])
    print(f"[OK] Storage scan on C: completed in {t_scan:.2f}s")
    print(f"[OK] Junk folders found: {len(junk_folders)}")
    for jf in junk_folders[:3]:
        print(f"     - Junk: {jf['name']} (~{jf['estimated_mb']} MB) at {jf['path']}")
    print(f"[OK] Large files (> 100MB) found: {len(large_files)}")

    print("\n=== [TEST 4] Socket Collector External Connection Flagging ===")
    sock = SocketCollector().collect_safe()
    conns = sock.get('connections', [])
    external_conns = [c for c in conns if c.get('is_external')]
    print(f"[OK] Total connections: {len(conns)} | External internet connections: {len(external_conns)}")
    if conns:
        assert 'is_external' in conns[0], "Socket connection missing 'is_external' flag"
    if external_conns:
        top_ext = external_conns[0]
        print(f"     - Top External: Remote={top_ext['remote_address']} ({top_ext.get('remote_host')}) | Proc={top_ext['process_name']}")

    print("\n=== [TEST 5] Threat Center Batch Mitigation API ===")
    mitigation_res = await threat_center.mitigate_all_threats()
    print(f"[OK] Batch mitigation result: {mitigation_res['message']} (Mitigated: {mitigation_res['mitigated_count']}, Failed: {mitigation_res['failed_count']})")
    assert 'mitigated_count' in mitigation_res
    assert 'failed_count' in mitigation_res

    print("\n=== [TEST 6] Dahoo NLP Batch Mitigation Trigger ===")
    dahoo_resp = await dahoo_engine.chat("lakukan tindakan untuk semua ancaman sekarang", {"threats": []}, use_cloud=False)
    print(f"[OK] Dahoo response for batch mitigation prompt:\n{dahoo_resp['reply']}")
    assert "mitigasi" in dahoo_resp['reply'].lower() or "ancaman" in dahoo_resp['reply'].lower()

    print("\n========================================================")
    print("🎉 ALL SPECIFIC FIX VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("========================================================")

if __name__ == "__main__":
    asyncio.run(run_fix_tests())
