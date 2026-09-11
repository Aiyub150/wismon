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
        self._thermal_cache: Dict[str, Any] = {
            "available": False,
            "zones": [],
            "cpu_temp_c": None,
            "status": "Unavailable on this hardware/BIOS without custom kernel driver"
        }
        self._last_thermal_check: float = 0.0
        self._thermal_check_interval: float = 60.0  # Probe at most once a minute

    def _get_thermal_zones(self) -> Dict[str, Any]:
        """Queries WMI MSAcpi_ThermalZoneTemperature if supported (with rate limiting)."""
        now = time.time()
        if (now - self._last_thermal_check) < self._thermal_check_interval:
            return self._thermal_cache

        self._last_thermal_check = now
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
                    # Convert from tenths of Kelvin to Celsius
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
                    self._thermal_check_interval = 5.0
                    return self._thermal_cache
        except Exception:
            pass

        self._thermal_cache = {
            "available": False,
            "zones": [],
            "cpu_temp_c": None,
            "status": "Unavailable on this hardware/BIOS without custom kernel driver"
        }
        # Back off if unsupported
        self._thermal_check_interval = 60.0
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
