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
        self.current_state: Dict[str, Any] = {
            "process": {},
            "socket": {},
            "services": {},
            "hardware": {}
        }
        self.latest_snapshot: Dict[str, Any] = {}
        self._subscribers: Set[asyncio.Queue] = set()
        self._running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Starts the decoupled background telemetry collection loops."""
        if self._running:
            return
        self._running = True

        self._tasks = [
            asyncio.create_task(self._fast_collection_loop(), name="fast_telemetry_loop"),
            asyncio.create_task(self._process_worker(), name="process_worker"),
            asyncio.create_task(self._socket_worker(), name="socket_worker"),
            asyncio.create_task(self._services_worker(), name="services_worker"),
            asyncio.create_task(self._hardware_worker(), name="hardware_worker")
        ]
        logger.info("Aggregator decoupled collection workers started.")

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        for t in self._tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        await db_manager.flush()
        logger.info("Aggregator stopped.")

    def subscribe(self) -> asyncio.Queue:
        """Subscribes an SSE connection to live telemetry frames."""
        q = asyncio.Queue(maxsize=30)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def _process_worker(self):
        """Background worker for process enumeration and threat scanning."""
        while self._running:
            try:
                procs = await asyncio.to_thread(self.process_collector.collect_safe)
                self.current_state["process"] = procs
                # Scan for threats with updated process list
                conn_list = self.current_state.get("socket", {}).get("connections", [])
                cpu_total = self.latest_snapshot.get("cpu", {}).get("total_percent", 0.0)
                ram_perc = self.latest_snapshot.get("memory", {}).get("percent", 0.0)
                threat_center.scan_telemetry(procs.get("processes", []), conn_list, cpu_total, ram_perc)
            except Exception as e:
                logger.error(f"Process worker error: {e}")
            await asyncio.sleep(2.5)

    async def _socket_worker(self):
        """Background worker for network socket inspection."""
        while self._running:
            try:
                sockets = await asyncio.to_thread(self.socket_collector.collect_safe)
                self.current_state["socket"] = sockets
            except Exception as e:
                logger.error(f"Socket worker error: {e}")
            await asyncio.sleep(4.0)

    async def _services_worker(self):
        """Background worker for Windows services enumeration."""
        while self._running:
            try:
                services = await asyncio.to_thread(self.services_collector.collect_safe)
                self.current_state["services"] = services
            except Exception as e:
                logger.error(f"Services worker error: {e}")
            await asyncio.sleep(25.0)

    async def _hardware_worker(self):
        """Background worker for hardware and thermal telemetry."""
        while self._running:
            try:
                hardware = await asyncio.to_thread(self.hardware_collector.collect_safe)
                self.current_state["hardware"] = hardware
            except Exception as e:
                logger.error(f"Hardware worker error: {e}")
            await asyncio.sleep(8.0)

    async def _fast_collection_loop(self):
        """High-frequency ~1.0s telemetry loop delivering real-time UI frames."""
        retention_tick = 0
        while self._running:
            start_ts = time.time()
            try:
                # 1. Run ultra-fast collectors (<10ms total)
                cpu = self.cpu_collector.collect_safe()
                mem = self.mem_collector.collect_safe()
                storage = self.storage_collector.collect_safe()
                net = self.network_collector.collect_safe()
                gpu = self.gpu_collector.collect_safe() if self.gpu_collector.should_collect(start_ts) else (self.gpu_collector.last_data or {})

                # 2. Extract state from background workers
                procs = self.current_state.get("process") or {}
                sockets = self.current_state.get("socket") or {}
                services = self.current_state.get("services") or {}
                hardware = self.current_state.get("hardware") or {}
                active_threats = threat_center.get_threats()

                # 3. Update baseline & health score
                cpu_total = cpu.get("total_percent", 0.0)
                ram_perc = mem.get("percent", 0.0)
                net_mbps = (net.get("throughput", {}).get("bytes_recv_sec", 0) * 8) / (1024 * 1024)
                self.analysis_engine.update_telemetry(cpu_total, ram_perc, net_mbps)

                storage_perc = storage.get("overall", {}).get("percent", 0.0)
                health = self.analysis_engine.calculate_health(cpu_total, ram_perc, storage_perc, len(active_threats))

                # 4. Build normalized snapshot
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

                # 5. Queue for SQLite DB batch
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

                # 6. Broadcast to SSE subscribers immediately
                if self._subscribers:
                    for sub in list(self._subscribers):
                        try:
                            if not sub.full():
                                sub.put_nowait(snapshot)
                        except Exception:
                            pass

                # 7. Periodic retention cleanup (every ~30 minutes)
                retention_tick += 1
                if retention_tick >= 1800:
                    retention_tick = 0
                    asyncio.create_task(db_manager.purge_old_data())

            except Exception as e:
                logger.error(f"Aggregator fast loop error: {e}", exc_info=True)

            # Sleep remaining delta to maintain smooth ~1.0s stream
            elapsed = time.time() - start_ts
            sleep_time = max(0.05, 1.0 - elapsed)
            await asyncio.sleep(sleep_time)

aggregator = Aggregator()
