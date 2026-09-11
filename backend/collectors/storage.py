"""
Storage Collector for Windows System Monitoring.
Monitors mounted drive capacities, file system types, and live disk I/O rates.
"""

import time
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class StorageCollector(BaseCollector):
    def __init__(self, interval: float = 1.0):
        super().__init__(name="storage", interval=interval)
        self._last_io = None
        self._last_io_time = 0.0

    def collect(self) -> Dict[str, Any]:
        now = time.time()
        # Partition information
        drives: List[Dict[str, Any]] = []
        total_storage_bytes = 0
        used_storage_bytes = 0

        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_storage_bytes += usage.total
                used_storage_bytes += usage.used
                drives.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue

        overall_percent = round((used_storage_bytes / total_storage_bytes * 100), 1) if total_storage_bytes > 0 else 0.0

        # Disk I/O rates
        io_current = psutil.disk_io_counters(perdisk=False)
        read_bytes_sec = 0.0
        write_bytes_sec = 0.0
        read_ops_sec = 0.0
        write_ops_sec = 0.0
        read_time_ms = 0
        write_time_ms = 0

        if self._last_io and self._last_io_time > 0 and io_current:
            dt = max(now - self._last_io_time, 0.001)
            read_bytes_sec = max(0.0, (io_current.read_bytes - self._last_io.read_bytes) / dt)
            write_bytes_sec = max(0.0, (io_current.write_bytes - self._last_io.write_bytes) / dt)
            read_ops_sec = max(0.0, (io_current.read_count - self._last_io.read_count) / dt)
            write_ops_sec = max(0.0, (io_current.write_count - self._last_io.write_count) / dt)
            read_time_ms = getattr(io_current, "read_time", 0) - getattr(self._last_io, "read_time", 0)
            write_time_ms = getattr(io_current, "write_time", 0) - getattr(self._last_io, "write_time", 0)

        self._last_io = io_current
        self._last_io_time = now

        return {
            "drives": drives,
            "overall": {
                "total_bytes": total_storage_bytes,
                "used_bytes": used_storage_bytes,
                "free_bytes": max(0, total_storage_bytes - used_storage_bytes),
                "percent": overall_percent
            },
            "io": {
                "read_bytes_sec": round(read_bytes_sec, 1),
                "write_bytes_sec": round(write_bytes_sec, 1),
                "read_ops_sec": round(read_ops_sec, 1),
                "write_ops_sec": round(write_ops_sec, 1),
                "read_time_ms": max(0, read_time_ms),
                "write_time_ms": max(0, write_time_ms)
            },
            "drive_health": "Drive telemetry unavailable (requires administrative driver query)",
            "status": "online"
        }
