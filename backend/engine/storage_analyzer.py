"""
Storage Analyzer Engine for Windows System Monitoring.
Scans designated directories for large files, old files, temporary items, and download footprints.
Adheres strictly to the safety rule: NEVER auto-delete; recommendations only.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, List

class StorageAnalyzer:
    def __init__(self):
        self._last_scan: Dict[str, Any] = {}

    def scan(self, target_path: str = None) -> Dict[str, Any]:
        start_time = time.time()
        large_files: List[Dict[str, Any]] = []
        old_files: List[Dict[str, Any]] = []
        temp_files_bytes = 0
        temp_files_count = 0

        # Scan targets: Windows User Temp directory and user profile
        user_profile = Path(os.environ.get("USERPROFILE", "C:\\"))
        temp_dir = Path(os.environ.get("TEMP", user_profile / "AppData" / "Local" / "Temp"))
        downloads_dir = user_profile / "Downloads"

        # 1. Scan Temp Directory
        if temp_dir.exists():
            try:
                for root, _, files in os.walk(temp_dir):
                    for f in files:
                        try:
                            fp = Path(root) / f
                            st = fp.stat()
                            temp_files_bytes += st.st_size
                            temp_files_count += 1
                        except (PermissionError, OSError):
                            continue
            except Exception:
                pass

        # 2. Scan Downloads Directory for Large Files (>100MB) & Old Files (>180 days)
        now = time.time()
        one_hundred_mb = 100 * 1024 * 1024
        half_year_sec = 180 * 86400

        scan_roots = [downloads_dir]
        if target_path and Path(target_path).exists():
            scan_roots = [Path(target_path)]

        for sroot in scan_roots:
            if not sroot.exists():
                continue
            try:
                for root, _, files in os.walk(sroot):
                    for f in files:
                        try:
                            fp = Path(root) / f
                            st = fp.stat()
                            size = st.st_size
                            mtime = st.st_mtime

                            # Large file check
                            if size > one_hundred_mb:
                                large_files.append({
                                    "name": f,
                                    "path": str(fp),
                                    "size_bytes": size,
                                    "size_mb": round(size / (1024 * 1024), 1),
                                    "modified_time": mtime
                                })

                            # Old file check
                            if (now - mtime) > half_year_sec and size > (5 * 1024 * 1024):
                                old_files.append({
                                    "name": f,
                                    "path": str(fp),
                                    "size_bytes": size,
                                    "size_mb": round(size / (1024 * 1024), 1),
                                    "days_old": int((now - mtime) / 86400)
                                })
                        except (PermissionError, OSError):
                            continue
            except Exception:
                pass

        large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
        old_files.sort(key=lambda x: x["size_bytes"], reverse=True)

        result = {
            "scanned_at": now,
            "duration_sec": round(time.time() - start_time, 2),
            "temp_cleanup": {
                "total_bytes": temp_files_bytes,
                "total_mb": round(temp_files_bytes / (1024 * 1024), 1),
                "file_count": temp_files_count,
                "path": str(temp_dir)
            },
            "large_files": large_files[:25],
            "old_files": old_files[:25],
            "total_reclaimable_estimate_mb": round(
                (temp_files_bytes + sum(f["size_bytes"] for f in old_files[:10])) / (1024 * 1024), 1
            )
        }
        self._last_scan = result
        return result

    def get_last_scan(self) -> Dict[str, Any]:
        if not self._last_scan:
            return self.scan()
        return self._last_scan

storage_analyzer = StorageAnalyzer()
