"""
Hardware & Thermal Zones Collector for Windows System Monitoring.
Queries thermal zones, battery state, and system platform metadata.
Adheres strictly to 'No Fake Data' — flags unsupported sensors as Unavailable.
"""

import time
import platform
import subprocess
import psutil
from typing import Dict, Any
from backend.collectors.base import BaseCollector

class HardwareCollector(BaseCollector):
    def __init__(self, interval: float = 3.0):
        super().__init__(name="hardware", interval=interval)
        self.boot_time = psutil.boot_time()
        self.platform_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node()
        }
        self._pdh_query = None
        self._pdh_thermal_counter = None
        self._is_high_precision = True
        self._init_pdh_thermal()
        self._thermal_cache: Dict[str, Any] = {
            "available": False,
            "zones": [],
            "cpu_temp_c": None,
            "status": "Initializing thermal sensors..."
        }
        self._last_thermal_check: float = 0.0
        self._thermal_check_interval: float = 2.0

    def _init_pdh_thermal(self):
        """Initializes native Windows PDH query for thermal zone information."""
        try:
            import ctypes
            from ctypes import wintypes
            pdh = ctypes.windll.pdh
            q = wintypes.HANDLE()
            if pdh.PdhOpenQueryW(None, 0, ctypes.byref(q)) == 0:
                cnt = wintypes.HANDLE()
                # Try high precision tenths-of-kelvin first
                res = pdh.PdhAddEnglishCounterW(q, '\\Thermal Zone Information(*)\\High Precision Temperature', 0, ctypes.byref(cnt))
                if res == 0:
                    self._pdh_query = q
                    self._pdh_thermal_counter = cnt
                    self._is_high_precision = True
                    pdh.PdhCollectQueryData(q)
                else:
                    # Fallback to standard kelvin counter
                    res2 = pdh.PdhAddEnglishCounterW(q, '\\Thermal Zone Information(*)\\Temperature', 0, ctypes.byref(cnt))
                    if res2 == 0:
                        self._pdh_query = q
                        self._pdh_thermal_counter = cnt
                        self._is_high_precision = False
                        pdh.PdhCollectQueryData(q)
        except Exception as e:
            self._pdh_query = None

    def _query_pdh_thermal(self) -> List[Dict[str, Any]]:
        """Queries native PDH for all thermal zone temperatures."""
        if not self._pdh_query or not self._pdh_thermal_counter:
            return []
        try:
            import ctypes
            from ctypes import wintypes
            class PDH_FMT_COUNTERVALUE_DOUBLE(ctypes.Structure):
                _fields_ = [('CStatus', wintypes.DWORD), ('doubleValue', ctypes.c_double)]

            class PDH_FMT_COUNTERVALUE_ITEM_W(ctypes.Structure):
                _fields_ = [('szName', wintypes.LPWSTR), ('FmtValue', PDH_FMT_COUNTERVALUE_DOUBLE)]

            pdh = ctypes.windll.pdh
            if pdh.PdhCollectQueryData(self._pdh_query) != 0:
                return []

            buf_size = wintypes.DWORD(0)
            item_count = wintypes.DWORD(0)
            pdh.PdhGetFormattedCounterArrayW(self._pdh_thermal_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), None)
            if buf_size.value == 0:
                return []

            buf = (ctypes.c_byte * buf_size.value)()
            if pdh.PdhGetFormattedCounterArrayW(self._pdh_thermal_counter, 0x200, ctypes.byref(buf_size), ctypes.byref(item_count), ctypes.byref(buf)) == 0:
                items = ctypes.cast(buf, ctypes.POINTER(PDH_FMT_COUNTERVALUE_ITEM_W))
                zones = []
                for i in range(item_count.value):
                    raw = items[i].FmtValue.doubleValue
                    if raw <= 0:
                        continue
                    if self._is_high_precision:
                        celsius = round((raw / 10.0) - 273.15, 1)
                    else:
                        celsius = round(raw - 273.15, 1)

                    if 0 < celsius < 125:
                        name = items[i].szName or f"Thermal Zone {i}"
                        zones.append({
                            "name": name,
                            "temperature_c": celsius
                        })
                return zones
        except Exception:
            return []
        return []

    def _get_thermal_zones(self) -> Dict[str, Any]:
        """Queries thermal zone temperatures via native PDH with CIM fallback."""
        now = time.time()
        if (now - self._last_thermal_check) < self._thermal_check_interval:
            return self._thermal_cache

        self._last_thermal_check = now

        # 1. First attempt: Native PDH (Ultra fast, zero subprocess)
        pdh_zones = self._query_pdh_thermal()
        if pdh_zones:
            self._thermal_cache = {
                "available": True,
                "zones": pdh_zones,
                "cpu_temp_c": pdh_zones[0]["temperature_c"],
                "status": "Online"
            }
            self._thermal_check_interval = 2.0
            return self._thermal_cache

        # 2. Second attempt: CIM Win32_PerfFormattedData_Counters_ThermalZoneInformation
        try:
            cmd = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation -ErrorAction SilentlyContinue | Select-Object Name, HighPrecisionTemperature, Temperature | ConvertTo-Json -Compress"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip():
                import json
                raw = json.loads(res.stdout.strip())
                items = raw if isinstance(raw, list) else [raw]
                zones = []
                for it in items:
                    raw_high = it.get("HighPrecisionTemperature")
                    raw_temp = it.get("Temperature")
                    if raw_high and raw_high > 0:
                        celsius = round((raw_high / 10.0) - 273.15, 1)
                    elif raw_temp and raw_temp > 0:
                        celsius = round(raw_temp - 273.15, 1)
                    else:
                        continue
                    if 0 < celsius < 125:
                        zones.append({
                            "name": it.get("Name", "ACPI Zone"),
                            "temperature_c": celsius
                        })
                if zones:
                    self._thermal_cache = {
                        "available": True,
                        "zones": zones,
                        "cpu_temp_c": zones[0]["temperature_c"],
                        "status": "Online"
                    }
                    self._thermal_check_interval = 3.0
                    return self._thermal_cache
        except Exception:
            pass

        # 3. Third attempt: MSAcpi_ThermalZoneTemperature (for administrative shells)
        try:
            cmd = [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object InstanceName, CurrentTemperature | ConvertTo-Json -Compress"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.5)
            if res.returncode == 0 and res.stdout.strip():
                import json
                raw = json.loads(res.stdout.strip())
                items = raw if isinstance(raw, list) else [raw]
                zones = []
                for it in items:
                    raw_temp = it.get("CurrentTemperature", 0)
                    celsius = round((raw_temp / 10.0) - 273.15, 1)
                    if 0 < celsius < 120:
                        zones.append({
                            "name": it.get("InstanceName", "ACPI Zone"),
                            "temperature_c": celsius
                        })
                if zones:
                    self._thermal_cache = {
                        "available": True,
                        "zones": zones,
                        "cpu_temp_c": zones[0]["temperature_c"],
                        "status": "Online"
                    }
                    self._thermal_check_interval = 3.0
                    return self._thermal_cache
        except Exception:
            pass

        self._thermal_cache = {
            "available": False,
            "zones": [],
            "cpu_temp_c": None,
            "status": "Thermal sensors unavailable on this hardware/BIOS"
        }
        self._thermal_check_interval = 30.0
        return self._thermal_cache

    def collect(self) -> Dict[str, Any]:
        # Battery
        battery = psutil.sensors_battery()
        battery_data = {
            "available": battery is not None,
            "percent": round(battery.percent, 1) if battery else None,
            "power_plugged": battery.power_plugged if battery else None,
            "secsleft": battery.secsleft if battery and battery.secsleft > 0 else None,
            "status": "Online" if battery else "Not supported (Desktop or no battery)"
        }

        # Thermal
        thermal = self._get_thermal_zones()

        # Uptime
        uptime_seconds = int(time.time() - self.boot_time)

        return {
            "system_info": self.platform_info,
            "boot_time": self.boot_time,
            "uptime_seconds": uptime_seconds,
            "battery": battery_data,
            "thermal": thermal,
            "status": "online"
        }
