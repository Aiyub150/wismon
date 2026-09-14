"""
Memory Collector for Windows System Monitoring.
Provides basic RAM statistics plus deep memory metrics via Win32 GetPerformanceInfo.
"""

import time
import ctypes
from ctypes import wintypes
import psutil
from typing import Dict, Any
from backend.collectors.base import BaseCollector

class PERFORMANCE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("CommitTotal", ctypes.c_size_t),
        ("CommitLimit", ctypes.c_size_t),
        ("CommitPeak", ctypes.c_size_t),
        ("PhysicalTotal", ctypes.c_size_t),
        ("PhysicalAvailable", ctypes.c_size_t),
        ("SystemCache", ctypes.c_size_t),
        ("KernelTotal", ctypes.c_size_t),
        ("KernelPaged", ctypes.c_size_t),
        ("KernelNonpaged", ctypes.c_size_t),
        ("PageSize", ctypes.c_size_t),
        ("HandleCount", wintypes.DWORD),
        ("ProcessCount", wintypes.DWORD),
        ("ThreadCount", wintypes.DWORD),
    ]

class MemoryCollector(BaseCollector):
    def __init__(self, interval: float = 1.0):
        super().__init__(name="memory", interval=interval)
        self._psapi = None
        self._last_swap = None
        self._last_swap_time = 0.0
        try:
            self._psapi = ctypes.windll.psapi
        except Exception:
            pass

    def _get_deep_memory(self) -> Dict[str, Any]:
        """Queries Win32 GetPerformanceInfo for kernel pools and commit totals."""
        if not self._psapi:
            return {
                "paged_pool": 0,
                "nonpaged_pool": 0,
                "commit_charge": 0,
                "commit_limit": 0,
                "system_cache": 0,
                "handle_count": 0
            }
        perf = PERFORMANCE_INFORMATION()
        perf.cb = ctypes.sizeof(PERFORMANCE_INFORMATION)
        if self._psapi.GetPerformanceInfo(ctypes.byref(perf), perf.cb):
            page_size = perf.PageSize
            return {
                "paged_pool": perf.KernelPaged * page_size,
                "nonpaged_pool": perf.KernelNonpaged * page_size,
                "commit_charge": perf.CommitTotal * page_size,
                "commit_limit": perf.CommitLimit * page_size,
                "system_cache": perf.SystemCache * page_size,
                "handle_count": perf.HandleCount,
                "process_count": perf.ProcessCount,
                "thread_count": perf.ThreadCount
            }
        return {
            "paged_pool": 0,
            "nonpaged_pool": 0,
            "commit_charge": 0,
            "commit_limit": 0,
            "system_cache": 0,
            "handle_count": 0
        }

    def collect(self) -> Dict[str, Any]:
        now = time.time()
        vmem = psutil.virtual_memory()
        deep = self._get_deep_memory()

        # Cache psutil.swap_memory() for 20 seconds to eliminate 600ms disk/registry I/O bottleneck
        if self._last_swap is None or (now - self._last_swap_time) > 20.0:
            try:
                raw_swap = psutil.swap_memory()
                self._last_swap = {
                    "total_bytes": raw_swap.total,
                    "used_bytes": raw_swap.used,
                    "free_bytes": raw_swap.free,
                    "percent": round(raw_swap.percent, 1)
                }
            except Exception:
                commit_total = deep.get("commit_charge", 0)
                commit_limit = deep.get("commit_limit", 1)
                swap_pct = round((commit_total / max(1, commit_limit)) * 100, 1)
                self._last_swap = {
                    "total_bytes": commit_limit,
                    "used_bytes": commit_total,
                    "free_bytes": max(0, commit_limit - commit_total),
                    "percent": swap_pct
                }
            self._last_swap_time = now

        return {
            "total_bytes": vmem.total,
            "used_bytes": vmem.used,
            "available_bytes": vmem.available,
            "free_bytes": vmem.free,
            "cached_bytes": getattr(vmem, "cached", deep.get("system_cache", 0)),
            "percent": round(vmem.percent, 1),
            "swap": self._last_swap,
            "deep": deep,
            "status": "online"
        }
