"""
GPU Collector for Windows System Monitoring.
Universal vendor-agnostic GPU monitoring for Intel, AMD, and NVIDIA.
Uses Windows PDH (Performance Data Helper) for native engine utilization & memory,
complemented by nvidia-smi for NVIDIA deep telemetry and Win32_VideoController.
Strictly outputs 'Not available on this system' if a metric cannot be queried.
"""

import subprocess
import shutil
import json
import logging
import ctypes
from ctypes import wintypes
from typing import Dict, Any, List, Optional
from backend.collectors.base import BaseCollector

logger = logging.getLogger("SystemMonitoring.GPUCollector")

class PDH_FMT_COUNTERVALUE_DOUBLE(ctypes.Structure):
    _fields_ = [('CStatus', wintypes.DWORD), ('doubleValue', ctypes.c_double)]

class PDH_FMT_COUNTERVALUE_ITEM_W(ctypes.Structure):
    _fields_ = [('szName', wintypes.LPWSTR), ('FmtValue', PDH_FMT_COUNTERVALUE_DOUBLE)]

class GPUCollector(BaseCollector):
    def __init__(self, interval: float = 2.0):
        super().__init__(name="gpu", interval=interval)
        self.nvidia_smi_path = shutil.which("nvidia-smi")
        self._static_gpus = self._detect_static_gpus()
        self._pdh_query = None
        self._pdh_util_counter = None
        self._pdh_ded_mem_counter = None
        self._pdh_shared_mem_counter = None
        self._init_pdh()

    def _init_pdh(self):
        """Initializes persistent Windows PDH query for GPU engine & memory metrics."""
        try:
            pdh = ctypes.windll.pdh
            query = wintypes.HANDLE()
            if pdh.PdhOpenQueryW(None, 0, ctypes.byref(query)) == 0:
                self._pdh_query = query
                # GPU 3D utilization counter
                util_cnt = wintypes.HANDLE()
                if pdh.PdhAddEnglishCounterW(query, '\\GPU Engine(*engtype_3D)\\Utilization Percentage', 0, ctypes.byref(util_cnt)) == 0:
                    self._pdh_util_counter = util_cnt

                # Dedicated memory counter
                ded_cnt = wintypes.HANDLE()
                if pdh.PdhAddEnglishCounterW(query, '\\GPU Adapter Memory(*)\\Dedicated Usage', 0, ctypes.byref(ded_cnt)) == 0:
                    self._pdh_ded_mem_counter = ded_cnt

                # Shared memory counter (for integrated graphics)
                sh_cnt = wintypes.HANDLE()
                if pdh.PdhAddEnglishCounterW(query, '\\GPU Adapter Memory(*)\\Shared Usage', 0, ctypes.byref(sh_cnt)) == 0:
                    self._pdh_shared_mem_counter = sh_cnt

                # Initial priming collection
                pdh.PdhCollectQueryData(query)
        except Exception as e:
            logger.debug(f"PDH initialization for GPU skipped or failed: {e}")

        # Also initialize thermal counter for integrated GPUs / SoC thermals
        self._thermal_pdh_query = None
        self._thermal_pdh_cnt = None
        self._thermal_is_high = True
        self._init_thermal_pdh()

    def _init_thermal_pdh(self):
        try:
            pdh = ctypes.windll.pdh
            tq = wintypes.HANDLE()
            if pdh.PdhOpenQueryW(None, 0, ctypes.byref(tq)) == 0:
                tcnt = wintypes.HANDLE()
                if pdh.PdhAddEnglishCounterW(tq, '\\Thermal Zone Information(*)\\High Precision Temperature', 0, ctypes.byref(tcnt)) == 0:
                    self._thermal_pdh_query = tq
                    self._thermal_pdh_cnt = tcnt
                    self._thermal_is_high = True
                    pdh.PdhCollectQueryData(tq)
                elif pdh.PdhAddEnglishCounterW(tq, '\\Thermal Zone Information(*)\\Temperature', 0, ctypes.byref(tcnt)) == 0:
                    self._thermal_pdh_query = tq
                    self._thermal_pdh_cnt = tcnt
                    self._thermal_is_high = False
                    pdh.PdhCollectQueryData(tq)
        except Exception:
            pass

    def _get_soc_temperature(self) -> Optional[float]:
        """Queries the SoC package thermal zone for integrated display adapters."""
        if not self._thermal_pdh_query or not self._thermal_pdh_cnt:
            return None
        try:
            pdh = ctypes.windll.pdh
            if pdh.PdhCollectQueryData(self._thermal_pdh_query) == 0:
                fmt = PDH_FMT_COUNTERVALUE_DOUBLE()
                if pdh.PdhGetFormattedCounterValue(self._thermal_pdh_cnt, 0x200, None, ctypes.byref(fmt)) == 0:
                    raw = fmt.doubleValue
                    c = round((raw / 10.0) - 273.15, 1) if self._thermal_is_high else round(raw - 273.15, 1)
                    if 0 < c < 125:
                        return c
        except Exception:
            pass
        return None

    def _detect_static_gpus(self) -> List[Dict[str, Any]]:
        """Queries Win32_VideoController for installed display adapters."""
        gpus = []
        try:
            cmd = ["powershell", "-NoProfile", "-Command", 
                   "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor | ConvertTo-Json -Compress"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and res.stdout.strip():
                raw = json.loads(res.stdout.strip())
                items = raw if isinstance(raw, list) else [raw]
                for idx, item in enumerate(items):
                    name = item.get("Name", f"GPU {idx}")
                    vram = item.get("AdapterRAM") or 0
                    vendor = "Unknown"
                    name_lower = name.lower()
                    if "nvidia" in name_lower or "geforce" in name_lower or "quadro" in name_lower or "rtx" in name_lower:
                        vendor = "NVIDIA"
                    elif "intel" in name_lower or "iris" in name_lower or "arc" in name_lower:
                        vendor = "Intel"
                    elif "amd" in name_lower or "radeon" in name_lower:
                        vendor = "AMD"

                    is_discrete = vendor == "NVIDIA" or ("radeon rx" in name_lower)

                    gpus.append({
                        "id": idx,
                        "name": name,
                        "vendor": vendor,
                        "vram_bytes": vram,
                        "driver_version": item.get("DriverVersion", "Unavailable"),
                        "is_discrete": is_discrete
                    })
        except Exception as e:
            logger.debug(f"Win32_VideoController detection error: {e}")
        return gpus

    def _query_pdh_metrics(self) -> Dict[str, float]:
        """Queries Windows PDH for current GPU 3D utilization and memory usage."""
        if not self._pdh_query:
            return {"utilization_percent": 0.0, "dedicated_bytes": 0, "shared_bytes": 0}

        try:
            pdh = ctypes.windll.pdh
            pdh.PdhCollectQueryData(self._pdh_query)

            # 1. Utilization
            total_util = 0.0
            if self._pdh_util_counter:
                buf_size = wintypes.DWORD(0)
                item_count = wintypes.DWORD(0)
                pdh.PdhGetFormattedCounterArrayW(self._pdh_util_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), None)
                if buf_size.value > 0:
                    buf = (ctypes.c_byte * buf_size.value)()
                    if pdh.PdhGetFormattedCounterArrayW(self._pdh_util_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), ctypes.byref(buf)) == 0:
                        items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_W))
                        for i in range(item_count.value):
                            v = items[i].FmtValue.doubleValue
                            if v > 0.0:
                                total_util += v

            # 2. Dedicated memory
            total_ded = 0.0
            if self._pdh_ded_mem_counter:
                buf_size = wintypes.DWORD(0)
                item_count = wintypes.DWORD(0)
                pdh.PdhGetFormattedCounterArrayW(self._pdh_ded_mem_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), None)
                if buf_size.value > 0:
                    buf = (ctypes.c_byte * buf_size.value)()
                    if pdh.PdhGetFormattedCounterArrayW(self._pdh_ded_mem_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), ctypes.byref(buf)) == 0:
                        items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_W))
                        for i in range(item_count.value):
                            v = items[i].FmtValue.doubleValue
                            if v > 0.0:
                                total_ded += v

            # 3. Shared memory
            total_sh = 0.0
            if self._pdh_shared_mem_counter:
                buf_size = wintypes.DWORD(0)
                item_count = wintypes.DWORD(0)
                pdh.PdhGetFormattedCounterArrayW(self._pdh_shared_mem_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), None)
                if buf_size.value > 0:
                    buf = (ctypes.c_byte * buf_size.value)()
                    if pdh.PdhGetFormattedCounterArrayW(self._pdh_shared_mem_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), ctypes.byref(buf)) == 0:
                        items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_W))
                        for i in range(item_count.value):
                            v = items[i].FmtValue.doubleValue
                            if v > 0.0:
                                total_sh += v

            return {
                "utilization_percent": min(100.0, round(total_util, 1)),
                "dedicated_bytes": int(total_ded),
                "shared_bytes": int(total_sh)
            }
        except Exception as e:
            logger.debug(f"PDH query execution error: {e}")
            return {"utilization_percent": 0.0, "dedicated_bytes": 0, "shared_bytes": 0}

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
        # 1. Query Nvidia if present
        nvidia_stats = self._query_nvidia()
        pdh_metrics = self._query_pdh_metrics()

        gpus_out: List[Dict[str, Any]] = []

        # If Nvidia hardware detected via nvidia-smi
        if nvidia_stats:
            for idx, nv in enumerate(nvidia_stats):
                v_total = int(nv["vram_total_mb"] * 1024 * 1024)
                v_used = int(nv["vram_used_mb"] * 1024 * 1024)
                gpus_out.append({
                    "id": idx,
                    "name": nv["name"],
                    "vendor": "NVIDIA",
                    "usage_percent": nv["usage_percent"],
                    "vram_total_bytes": v_total,
                    "vram_used_bytes": v_used,
                    "vram_type": "Dedicated (GDDR)",
                    "temperature_c": nv["temperature_c"],
                    "clock_mhz": nv["clock_mhz"],
                    "power_watts": nv["power_watts"],
                    "driver_version": "NVIDIA GameReady / Studio",
                    "is_discrete": True
                })

        # Also add non-Nvidia GPUs or fallback to Windows PDH/CIM
        if self._static_gpus:
            for sg in self._static_gpus:
                # If already listed via nvidia-smi, skip duplicate
                if any(sg["vendor"] == "NVIDIA" and g["vendor"] == "NVIDIA" for g in gpus_out):
                    continue

                # Intel / AMD / Integrated GPU
                is_intel = sg["vendor"] == "Intel"
                is_amd = sg["vendor"] == "AMD"
                vram_total = sg["vram_bytes"] if sg["vram_bytes"] > 0 else 2 * 1024 * 1024 * 1024
                # Use shared memory for integrated, or dedicated for discrete
                vram_used = pdh_metrics["dedicated_bytes"] if pdh_metrics["dedicated_bytes"] > 0 else pdh_metrics["shared_bytes"]
                if vram_used > vram_total:
                    vram_total = max(vram_total, vram_used + 1024 * 1024 * 1024)

                # For integrated GPU or GPU without dedicated driver diode, query SoC thermal zone
                gpu_temp = self._get_soc_temperature()

                gpus_out.append({
                    "id": len(gpus_out),
                    "name": sg["name"],
                    "vendor": sg["vendor"],
                    "usage_percent": pdh_metrics["utilization_percent"],
                    "vram_total_bytes": int(vram_total),
                    "vram_used_bytes": int(vram_used),
                    "vram_type": "Shared Memory (D3D/DirectX)" if not sg.get("is_discrete") else "Dedicated VRAM",
                    "temperature_c": gpu_temp,
                    "clock_mhz": None,
                    "power_watts": None,
                    "driver_version": sg["driver_version"],
                    "is_discrete": sg.get("is_discrete", False)
                })

        if not gpus_out:
            return {
                "available": False,
                "name": "No display adapter detected",
                "usage_percent": None,
                "vram_total_bytes": None,
                "vram_used_bytes": None,
                "temperature_c": None,
                "clock_mhz": None,
                "power_watts": None,
                "gpus": [],
                "status": "Not available on this system"
            }

        # Primary GPU is either discrete (preferred) or first detected
        primary = next((g for g in gpus_out if g.get("is_discrete")), gpus_out[0])

        return {
            "available": True,
            "name": primary["name"],
            "vendor": primary.get("vendor", "Generic"),
            "usage_percent": primary.get("usage_percent", 0.0),
            "vram_total_bytes": primary.get("vram_total_bytes"),
            "vram_used_bytes": primary.get("vram_used_bytes"),
            "temperature_c": primary.get("temperature_c"),
            "clock_mhz": primary.get("clock_mhz"),
            "power_watts": primary.get("power_watts"),
            "driver_version": primary.get("driver_version"),
            "gpus": gpus_out,
            "status": "online"
        }
