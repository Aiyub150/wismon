"""
CPU Collector for Windows System Monitoring.
Collects total CPU usage, per-core usage, frequencies, core counts, and processor name.
"""

import winreg
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

def get_processor_name() -> str:
    """Reads the official processor brand string from the Windows Registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        return str(name).strip()
    except Exception:
        return "Windows Processor"

class CPUCollector(BaseCollector):
    def __init__(self, interval: float = 1.0):
        super().__init__(name="cpu", interval=interval)
        self.processor_name = get_processor_name()
        self.physical_cores = psutil.cpu_count(logical=False) or 1
        self.logical_cores = psutil.cpu_count(logical=True) or 1
        # Prime psutil cpu_percent
        psutil.cpu_percent(interval=None, percpu=True)

    def collect(self) -> Dict[str, Any]:
        # Non-blocking query
        per_core: List[float] = psutil.cpu_percent(interval=None, percpu=True)
        total_percent: float = round(sum(per_core) / len(per_core), 1) if per_core else 0.0

        # Frequencies
        freq_info = psutil.cpu_freq()
        current_freq = round(freq_info.current, 0) if freq_info and freq_info.current else 0.0
        max_freq = round(freq_info.max, 0) if freq_info and freq_info.max else 0.0
        min_freq = round(freq_info.min, 0) if freq_info and freq_info.min else 0.0

        # CPU times breakdown
        cpu_times = psutil.cpu_times()
        times_dict = {
            "user": round(cpu_times.user, 1),
            "system": round(cpu_times.system, 1),
            "idle": round(cpu_times.idle, 1),
            "interrupt": round(getattr(cpu_times, "interrupt", 0.0), 1),
            "dpc": round(getattr(cpu_times, "dpc", 0.0), 1)
        }

        # Stats (ctx switches, interrupts)
        cpu_stats = psutil.cpu_stats()
        stats_dict = {
            "ctx_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "soft_interrupts": cpu_stats.soft_interrupts,
            "syscalls": cpu_stats.syscalls
        }

        return {
            "processor_name": self.processor_name,
            "physical_cores": self.physical_cores,
            "logical_cores": self.logical_cores,
            "total_percent": total_percent,
            "per_core": per_core,
            "frequency": {
                "current_mhz": current_freq,
                "max_mhz": max_freq,
                "min_mhz": min_freq
            },
            "times": times_dict,
            "stats": stats_dict,
            "status": "online"
        }
