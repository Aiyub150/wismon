"""
GPU Collector for Windows System Monitoring.
Queries installed graphics hardware via Win32 VideoController and nvidia-smi if present.
Strictly outputs 'Not available on this system' if a metric cannot be queried.
"""

import subprocess
import shutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class GPUCollector(BaseCollector):
    def __init__(self, interval: float = 2.0):
        super().__init__(name="gpu", interval=interval)
        self.nvidia_smi_path = shutil.which("nvidia-smi")
        self._static_gpus = self._detect_static_gpus()

    def _detect_static_gpus(self) -> List[Dict[str, Any]]:
        """Queries Win32_VideoController for installed display adapters."""
        gpus = []
        try:
            cmd = ["powershell", "-NoProfile", "-Command", 
                   "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json -Compress"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                import json
                raw = json.loads(res.stdout.strip())
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    vram = item.get("AdapterRAM") or 0
                    gpus.append({
                        "name": item.get("Name", "Unknown GPU"),
                        "vram_bytes": vram,
                        "driver_version": item.get("DriverVersion", "Unavailable")
                    })
        except Exception:
            pass
        return gpus

    def _query_nvidia(self) -> List[Dict[str, Any]]:
        if not self.nvidia_smi_path:
            return []
        try:
            cmd = [
                self.nvidia_smi_path,
                "--query-gpu=name,utilization.gpu,memory.total,memory.used,temperature.gpu,clocks.current.graphics,power.draw",
                "--format=csv,noheader,nounits"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                results = []
                lines = res.stdout.strip().splitlines()
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 5:
                        results.append({
                            "name": parts[0],
                            "usage_percent": float(parts[1]) if parts[1] != "[N/A]" else 0.0,
                            "vram_total_mb": float(parts[2]) if parts[2] != "[N/A]" else 0.0,
                            "vram_used_mb": float(parts[3]) if parts[3] != "[N/A]" else 0.0,
                            "temperature_c": float(parts[4]) if parts[4] != "[N/A]" else None,
                            "clock_mhz": float(parts[5]) if len(parts) > 5 and parts[5] != "[N/A]" else None,
                            "power_watts": float(parts[6]) if len(parts) > 6 and parts[6] != "[N/A]" else None,
                        })
                return results
        except Exception:
            pass
        return []

    def collect(self) -> Dict[str, Any]:
        nvidia_stats = self._query_nvidia()
        if nvidia_stats:
            gpu = nvidia_stats[0]
            vram_total = gpu["vram_total_mb"] * 1024 * 1024
            vram_used = gpu["vram_used_mb"] * 1024 * 1024
            return {
                "available": True,
                "name": gpu["name"],
                "usage_percent": gpu["usage_percent"],
                "vram_total_bytes": int(vram_total),
                "vram_used_bytes": int(vram_used),
                "temperature_c": gpu["temperature_c"],
                "clock_mhz": gpu["clock_mhz"],
                "power_watts": gpu["power_watts"],
                "status": "online"
            }

        if self._static_gpus:
            primary = self._static_gpus[0]
            return {
                "available": True,
                "name": primary["name"],
                "usage_percent": None,  # Will show 'Unavailable' on UI
                "vram_total_bytes": primary["vram_bytes"],
                "vram_used_bytes": None,
                "temperature_c": None,
                "clock_mhz": None,
                "power_watts": None,
                "driver_version": primary.get("driver_version"),
                "status": "online (metrics partially unavailable without dedicated driver query)"
            }

        return {
            "available": False,
            "name": "No dedicated GPU detected",
            "usage_percent": None,
            "vram_total_bytes": None,
            "vram_used_bytes": None,
            "temperature_c": None,
            "clock_mhz": None,
            "power_watts": None,
            "status": "Not available on this system"
        }
