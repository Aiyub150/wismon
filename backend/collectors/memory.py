"""
Memory Collector for Windows System Monitoring.
Provides basic RAM statistics plus deep memory metrics via Win32 GetPerformanceInfo.
"""

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
        vmem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        deep = self._get_deep_memory()

        return {
            "total_bytes": vmem.total,
            "used_bytes": vmem.used,
            "available_bytes": vmem.available,
            "free_bytes": vmem.free,
            "cached_bytes": getattr(vmem, "cached", deep.get("system_cache", 0)),
            "percent": round(vmem.percent, 1),
            "swap": {
                "total_bytes": swap.total,
                "used_bytes": swap.used,
                "free_bytes": swap.free,
                "percent": round(swap.percent, 1)
            },
            "deep": deep,
            "status": "online"
        }
