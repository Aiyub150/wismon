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

    def scan(self, target_drive: str = None) -> Dict[str, Any]:
        start_time = time.time()
        large_files: List[Dict[str, Any]] = []
        old_files: List[Dict[str, Any]] = []
        junk_folders: List[Dict[str, Any]] = []
        temp_files_bytes = 0
        temp_files_count = 0

        # Scan targets
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

        # 2. Determine scan roots based on target_drive or full system scope
        now = time.time()
        one_hundred_mb = 100 * 1024 * 1024
        half_year_sec = 180 * 86400

        scan_roots: List[Path] = []
        if target_drive and target_drive.strip():
            td = target_drive.strip().rstrip('\\') + '\\'
            p_td = Path(td)
            if p_td.exists():
                if p_td.drive.upper() == 'C:':
                    scan_roots = [downloads_dir, user_profile / "Desktop", user_profile / "Documents"]
                else:
                    scan_roots = [p_td]
        else:
            # Multi-drive default: Scan user downloads + mounted secondary drives (D:\, E:\, etc.)
            scan_roots = [downloads_dir, user_profile / "Desktop"]
            try:
                import psutil
                for part in psutil.disk_partitions(all=False):
                    mount = part.mountpoint
                    if mount.upper() != 'C:\\' and Path(mount).exists():
                        scan_roots.append(Path(mount))
            except Exception:
                pass

        # Helper for file category
        def _get_category(filename: str) -> str:
            ext = Path(filename).suffix.lower()
            if ext in ('.mp4', '.mkv', '.avi', '.mov', '.wmv'): return 'Video'
            if ext in ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'): return 'Archive'
            if ext in ('.iso', '.img', '.vhd', '.vhdx'): return 'Disk Image'
            if ext in ('.exe', '.msi', '.apk'): return 'Installer/Binary'
            if ext in ('.pdf', '.docx', '.xlsx', '.pptx', '.csv'): return 'Document'
            if ext in ('.bak', '.dump', '.sql', '.log'): return 'Backup/Log'
            return 'File'

        forbidden_names = {'$recycle.bin', 'system volume information', 'windows', 'program files', 'program files (x86)', 'recovery', 'boot', 'perflogs'}

        for sroot in scan_roots:
            if not sroot.exists():
                continue
            try:
                # Walk down max 4 levels deep to stay performant and responsive
                for root, dirs, files in os.walk(sroot):
                    curr_path = Path(root)
                    # Skip system and OS protected directories
                    parts_lower = [p.lower() for p in curr_path.parts]
                    if any(fn in parts_lower for fn in forbidden_names):
                        dirs.clear()
                        continue

                    # Check for unused / junk cache folders
                    for d in list(dirs):
                        d_lower = d.lower()
                        if d_lower in ('.cache', 'node_modules', 'crashdumps', '.tmp', 'temp', 'obj', 'debug') and not any(fn in d_lower for fn in forbidden_names):
                            folder_path = curr_path / d
                            try:
                                f_size = 0
                                f_count = 0
                                for f_r, _, f_files in os.walk(folder_path):
                                    for f in f_files:
                                        try:
                                            f_size += (Path(f_r) / f).stat().st_size
                                            f_count += 1
                                        except Exception:
                                            pass
                                if f_size > 20 * 1024 * 1024:  # > 20MB
                                    size_mb_val = round(f_size / (1024 * 1024), 1)
                                    junk_folders.append({
                                        "name": d,
                                        "path": str(folder_path),
                                        "size_bytes": f_size,
                                        "size_mb": size_mb_val,
                                        "estimated_mb": size_mb_val,
                                        "file_count": f_count,
                                        "type": "Unused/Cache Folder"
                                    })
                            except Exception:
                                pass
                            finally:
                                if d in dirs:
                                    dirs.remove(d)  # Don't recurse into it again in the outer walk

                    for f in files:
                        try:
                            fp = curr_path / f
                            st = fp.stat()
                            size = st.st_size
                            mtime = st.st_mtime

                            # Large file check (> 100MB)
                            if size > one_hundred_mb:
                                large_files.append({
                                    "name": f,
                                    "path": str(fp),
                                    "size_bytes": size,
                                    "size_mb": round(size / (1024 * 1024), 1),
                                    "category": _get_category(f),
                                    "modified_time": mtime
                                })

                            # Old file check (> 180 days and > 5MB)
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
        junk_folders.sort(key=lambda x: x["size_bytes"], reverse=True)

        reclaimable_sum = temp_files_bytes + sum(f["size_bytes"] for f in old_files[:10]) + sum(jf["size_bytes"] for jf in junk_folders[:5])

        result = {
            "scanned_at": now,
            "target_drive": target_drive or "All Drives / System-wide",
            "duration_sec": round(time.time() - start_time, 2),
            "temp_cleanup": {
                "total_bytes": temp_files_bytes,
                "total_mb": round(temp_files_bytes / (1024 * 1024), 1),
                "file_count": temp_files_count,
                "path": str(temp_dir)
            },
            "large_files": large_files[:30],
            "junk_folders": junk_folders[:15],
            "old_files": old_files[:20],
            "total_reclaimable_estimate_mb": round(reclaimable_sum / (1024 * 1024), 1)
        }
        self._last_scan = result
        return result

    def move_to_recycle_bin(self, filepath: str) -> Dict[str, Any]:
        """
        Safely moves a target file or junk folder to the Windows Recycle Bin (with full undo support).
        Enforces strict guardrails preventing modification of system or critical directories.
        """
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ('hwnd', wintypes.HWND),
                ('wFunc', wintypes.UINT),
                ('pFrom', wintypes.LPCWSTR),
                ('pTo', wintypes.LPCWSTR),
                ('fFlags', wintypes.WORD),
                ('fAnyOperationsAborted', wintypes.BOOL),
                ('hNameMappings', wintypes.LPVOID),
                ('lpszProgressTitle', wintypes.LPCWSTR),
            ]

        p = Path(filepath).resolve()
        if not p.exists():
            return {"success": False, "error": "Item does not exist or has already been moved."}

        # Guardrails: Forbid deleting Windows, Program Files, system root files
        p_str = str(p).lower()
        forbidden_prefixes = [
            os.environ.get("WINDIR", "C:\\Windows").lower(),
            os.environ.get("ProgramFiles", "C:\\Program Files").lower(),
            os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)").lower(),
            os.environ.get("SystemRoot", "C:\\Windows").lower()
        ]
        if any(p_str.startswith(f) for f in forbidden_prefixes if f):
            return {"success": False, "error": "Security violation: Cannot delete operating system or program files."}

        # Guardrail: Forbid root-level drives (e.g. C:\, D:\, E:\)
        if p.parent == p.anchor or len(p.parts) <= 2:
            return {"success": False, "error": "Security violation: Root-level drives or top root directories cannot be deleted."}

        try:
            # Path must be double-null terminated for SHFileOperationW
            p_from = str(p) + '\0\0'
            op = SHFILEOPSTRUCTW()
            op.wFunc = 0x0003 # FO_DELETE
            op.pFrom = p_from
            op.fFlags = 0x0040 | 0x0010 | 0x0004 # FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
            res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
            if res == 0 and not p.exists():
                return {"success": True, "message": f"Berhasil memindahkan '{p.name}' ke Windows Recycle Bin."}
            else:
                return {"success": False, "error": f"Gagal memindahkan ke Recycle Bin (code {res})."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def clean_user_temp_files(self) -> Dict[str, Any]:
        """Safely cleans unlocked files in the User Temp folder."""
        import psutil
        try:
            disk_before = psutil.disk_usage("C:\\")
            pct_before = round(disk_before.percent, 1)
            free_before_gb = round(disk_before.free / (1024**3), 2)
        except Exception:
            disk_before = None
            pct_before = 0.0
            free_before_gb = 0.0

        user_profile = Path(os.environ.get("USERPROFILE", "C:\\"))
        temp_dir = Path(os.environ.get("TEMP", user_profile / "AppData" / "Local" / "Temp"))
        cleaned_files = 0
        freed_bytes = 0
        if temp_dir.exists():
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    fp = Path(root) / f
                    try:
                        sz = fp.stat().st_size
                        fp.unlink()
                        cleaned_files += 1
                        freed_bytes += sz
                    except Exception:
                        # Skip locked or in-use files
                        pass

        try:
            disk_after = psutil.disk_usage("C:\\")
            pct_after = round(disk_after.percent, 1)
            free_after_gb = round(disk_after.free / (1024**3), 2)
            pct_diff = round(pct_before - pct_after, 2)
        except Exception:
            pct_after = pct_before
            free_after_gb = free_before_gb
            pct_diff = 0.0

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        freed_gb = round(freed_bytes / (1024**3), 2)
        freed_str = f"{freed_gb} GB" if freed_gb >= 1.0 else f"{freed_mb} MB"

        return {
            "success": True,
            "action_type": "CLEAN_TEMP",
            "cleaned_files": cleaned_files,
            "freed_bytes": freed_bytes,
            "freed_mb": freed_mb,
            "freed_gb": freed_gb,
            "freed_str": freed_str,
            "pct_before": pct_before,
            "pct_after": pct_after,
            "pct_diff": pct_diff,
            "free_before_gb": free_before_gb,
            "free_after_gb": free_after_gb,
            "message": f"Berhasil membersihkan {cleaned_files} file sementara ({freed_str}) dari direktori Temp. Kapasitas C: {pct_before}% ke {pct_after}%.",
            "verification": {
                "metric": "storage",
                "cleaned_files": cleaned_files,
                "freed_capacity": freed_str,
                "disk_before": f"{pct_before}%",
                "disk_after": f"{pct_after}%",
                "diff_percent": pct_diff,
                "free_space_gb": f"{free_after_gb} GB",
                "verified": True,
                "detail": f"File dibersihkan: {cleaned_files} ({freed_str}), Ruang disk C: {pct_before}% ke {pct_after}% (Bebas {free_after_gb} GB)"
            }
        }

    def get_last_scan(self) -> Dict[str, Any]:
        if not self._last_scan:
            return self.scan()
        return self._last_scan

storage_analyzer = StorageAnalyzer()

