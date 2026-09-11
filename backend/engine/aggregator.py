"""
Telemetry Aggregator & Coordinator for Windows System Monitoring.
Coordinates modular collectors, runs the ring buffer, calculates health,
and broadcasts real-time telemetry frames to connected SSE subscribers.
"""

import asyncio
import time
import logging
from collections import deque
from typing import Dict, Any, List, Set
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
from backend.engine.analysis import AnalysisEngine
from backend.engine.threat_center import threat_center
from backend.db import db_manager
from backend.config import RING_BUFFER_SIZE

logger = logging.getLogger("SystemMonitoring.Aggregator")

class Aggregator:
    def __init__(self):
        # Instantiate collectors
        self.cpu_collector = CPUCollector(interval=1.0)
        self.mem_collector = MemoryCollector(interval=1.0)
        self.gpu_collector = GPUCollector(interval=2.0)
        self.storage_collector = StorageCollector(interval=1.0)
        self.network_collector = NetworkCollector(interval=1.0)
        self.process_collector = ProcessCollector(interval=2.0)
        self.socket_collector = SocketCollector(interval=3.0)
        self.services_collector = ServicesCollector(interval=5.0)
        self.hardware_collector = HardwareCollector(interval=3.0)

        self.analysis_engine = AnalysisEngine()
        self.ring_buffer: deque = deque(maxlen=RING_BUFFER_SIZE)
        self.latest_snapshot: Dict[str, Any] = {}
        self._subscribers: Set[asyncio.Queue] = set()
        self._running = False
        self._task = None

    async def start(self):
        """Starts the background telemetry collection loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._collection_loop())
        logger.info("Aggregator collection loop started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await db_manager.flush()
        logger.info("Aggregator stopped.")

    def subscribe(self) -> asyncio.Queue:
        """Subscribes an SSE connection to live telemetry frames."""
        q = asyncio.Queue(maxsize=20)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def _collection_loop(self):
        retention_tick = 0
        while self._running:
            start_ts = time.time()
            try:
                # 1. Run collectors safe
                cpu = self.cpu_collector.collect_safe()
                mem = self.mem_collector.collect_safe()
                storage = self.storage_collector.collect_safe()
                net = self.network_collector.collect_safe()

                gpu = self.gpu_collector.collect_safe() if self.gpu_collector.should_collect(start_ts) else (self.gpu_collector.last_data or {})
                procs = self.process_collector.collect_safe() if self.process_collector.should_collect(start_ts) else (self.process_collector.last_data or {})
                sockets = self.socket_collector.collect_safe() if self.socket_collector.should_collect(start_ts) else (self.socket_collector.last_data or {})
                services = self.services_collector.collect_safe() if self.services_collector.should_collect(start_ts) else (self.services_collector.last_data or {})
                hardware = self.hardware_collector.collect_safe() if self.hardware_collector.should_collect(start_ts) else (self.hardware_collector.last_data or {})

                # 2. Update analysis engine baseline
                cpu_total = cpu.get("total_percent", 0.0)
                ram_perc = mem.get("percent", 0.0)
                net_mbps = (net.get("throughput", {}).get("bytes_recv_sec", 0) * 8) / (1024 * 1024)
                self.analysis_engine.update_telemetry(cpu_total, ram_perc, net_mbps)

                # 3. Scan for threats
                proc_list = procs.get("processes", [])
                conn_list = sockets.get("connections", [])
                threat_center.scan_telemetry(proc_list, conn_list, cpu_total, ram_perc)
                active_threats = threat_center.get_threats()

                # 4. Calculate health score
                storage_perc = storage.get("overall", {}).get("percent", 0.0)
                health = self.analysis_engine.calculate_health(cpu_total, ram_perc, storage_perc, len(active_threats))

                # 5. Build full normalized snapshot
                snapshot = {
                    "timestamp": start_ts,
                    "health": health,
                    "cpu": cpu,
                    "memory": mem,
                    "gpu": gpu,
                    "storage": storage,
                    "network": net,
                    "process": {
                        "total_count": procs.get("total_count", 0),
                        "top_cpu": procs.get("top_cpu", []),
                        "top_memory": procs.get("top_memory", [])
                    },
                    "socket": {
                        "total_connections": sockets.get("total_connections", 0),
                        "established_count": sockets.get("established_count", 0),
                        "listening_count": sockets.get("listening_count", 0)
                    },
                    "services": {
                        "total_count": services.get("total_count", 0),
                        "running_count": services.get("running_count", 0),
                        "stopped_count": services.get("stopped_count", 0)
                    },
                    "hardware": hardware,
                    "threats": active_threats
                }

                self.latest_snapshot = snapshot
                self.ring_buffer.append(snapshot)

                # 6. Queue for SQLite DB batch
                deep_mem = mem.get("deep", {})
                io = storage.get("io", {})
                tput = net.get("throughput", {})

                db_record = {
                    "timestamp": start_ts,
                    "cpu_percent": cpu_total,
                    "ram_percent": ram_perc,
                    "ram_used": mem.get("used_bytes", 0),
                    "ram_total": mem.get("total_bytes", 0),
                    "paged_pool": deep_mem.get("paged_pool", 0),
                    "nonpaged_pool": deep_mem.get("nonpaged_pool", 0),
                    "commit_charge": deep_mem.get("commit_charge", 0),
                    "commit_limit": deep_mem.get("commit_limit", 0),
                    "disk_read_bytes_sec": io.get("read_bytes_sec", 0.0),
                    "disk_write_bytes_sec": io.get("write_bytes_sec", 0.0),
                    "net_sent_bytes_sec": tput.get("bytes_sent_sec", 0.0),
                    "net_recv_bytes_sec": tput.get("bytes_recv_sec", 0.0),
                    "health_score": health["score"],
                    "health_status": health["status"]
                }
                await db_manager.insert_system_info(db_record)

                # 7. Broadcast to SSE subscribers
                if self._subscribers:
                    for sub in list(self._subscribers):
                        try:
                            if not sub.full():
                                sub.put_nowait(snapshot)
                        except Exception:
                            pass

                # 8. Periodic retention cleanup (every ~30 minutes)
                retention_tick += 1
                if retention_tick >= 1800:
                    retention_tick = 0
                    asyncio.create_task(db_manager.purge_old_data())

            except Exception as e:
                logger.error(f"Aggregator loop error: {e}", exc_info=True)

            # Sleep remaining delta to maintain exact ~1s cycle
            elapsed = time.time() - start_ts
            sleep_time = max(0.05, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)

aggregator = Aggregator()
