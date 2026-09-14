import time
import subprocess
import json
import re
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class StorageCollector(BaseCollector):
    def __init__(self, interval: float = 1.0):
        super().__init__(name="storage", interval=interval)
        self._last_io = None
        self._last_io_time = 0.0
        self._hw_map: Dict[str, Dict[str, Any]] = {}
        self._last_hw_time: float = 0.0

    def _refresh_hardware_map(self):
        """Discovers physical drive models, brands, and partition mappings via WMI."""
        drive_by_num = {}
        try:
            r_drives = subprocess.run(
                ['powershell', '-NoProfile', '-Command', 'Get-CimInstance Win32_DiskDrive | Select-Object DeviceID, Model, InterfaceType, MediaType | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=5
            )
            if r_drives.returncode == 0 and r_drives.stdout.strip():
                drives = json.loads(r_drives.stdout)
                if isinstance(drives, dict):
                    drives = [drives]
                for d in drives:
                    m = re.search(r'PHYSICALDRIVE(\d+)', d.get('DeviceID', ''))
                    if m:
                        drive_by_num[int(m.group(1))] = d
        except Exception:
            pass

        hw_mapping = {}
        try:
            r_rel = subprocess.run(
                ['powershell', '-NoProfile', '-Command', 'Get-CimInstance Win32_LogicalDiskToPartition | Select-Object Antecedent, Dependent | ConvertTo-Json -Compress'],
                capture_output=True, text=True, timeout=5
            )
            if r_rel.returncode == 0 and r_rel.stdout.strip():
                rels = json.loads(r_rel.stdout)
                if isinstance(rels, dict):
                    rels = [rels]
                for rel in rels:
                    ant_props = str(rel.get('Antecedent', {}).get('CimInstanceProperties', ''))
                    dep_props = str(rel.get('Dependent', {}).get('CimInstanceProperties', ''))
                    part_m = re.search(r'DeviceID\s*=\s*\"Disk #(\d+),', ant_props)
                    dl_m = re.search(r'DeviceID\s*=\s*\"([A-Za-z]:)\"', dep_props)
                    vol_m = re.search(r'VolumeName\s*=\s*\"([^\"]*)\"', dep_props)
                    if part_m and dl_m:
                        disk_num = int(part_m.group(1))
                        letter = dl_m.group(1).upper()
                        disk_info = drive_by_num.get(disk_num, {})
                        model = disk_info.get('Model') or 'Local Fixed Disk'
                        bus = disk_info.get('InterfaceType') or ('USB' if 'usb' in model.lower() else 'NVMe/SATA')
                        media = disk_info.get('MediaType') or 'Disk'
                        vol_name = vol_m.group(1) if vol_m else ''

                        # Infer readable device category
                        cat = "Local Disk"
                        lower_m = model.lower()
                        if "usb" in lower_m or bus == "USB":
                            cat = "USB Flash Disk"
                        elif "sdhc" in lower_m or "sd card" in lower_m or "card" in lower_m:
                            cat = "SD Card"
                        elif "nvme" in lower_m or "ssd" in lower_m:
                            cat = "NVMe SSD"
                        elif "scsi" in bus.lower():
                            cat = "Fixed SSD/HDD"

                        hw_mapping[letter] = {
                            'model': model,
                            'bus_type': bus,
                            'media_type': media,
                            'volume_name': vol_name,
                            'category': cat
                        }
            self._hw_map = hw_mapping
        except Exception:
            pass

    def collect(self) -> Dict[str, Any]:
        now = time.time()

        # Refresh drive hardware metadata every 30 seconds
        if not self._hw_map or (now - self._last_hw_time) > 30.0:
            self._refresh_hardware_map()
            self._last_hw_time = now

        # Partition information
        drives: List[Dict[str, Any]] = []
        total_storage_bytes = 0
        used_storage_bytes = 0

        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                total_storage_bytes += usage.total
                used_storage_bytes += usage.used
                dl_key = part.device[:2].upper()
                hw_info = self._hw_map.get(dl_key, {
                    'model': 'Local Fixed Disk',
                    'bus_type': 'Fixed',
                    'media_type': 'Disk',
                    'volume_name': '',
                    'category': 'Local Disk'
                })

                drives.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total_bytes": usage.total,
                    "used_bytes": usage.used,
                    "free_bytes": usage.free,
                    "percent": usage.percent,
                    "model": hw_info.get("model", "Local Disk"),
                    "bus_type": hw_info.get("bus_type", "Fixed"),
                    "media_type": hw_info.get("media_type", "Disk"),
                    "volume_name": hw_info.get("volume_name", ""),
                    "category": hw_info.get("category", "Local Disk")
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
