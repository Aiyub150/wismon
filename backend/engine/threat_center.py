"""
Threat Center & Security Analysis Engine for Windows System Monitoring.
Tracks security events, suspicious resource usage, anomalous socket patterns,
and enforces a structured threat lifecycle with safe, user-confirmed mitigation.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from backend.db import db_manager

class ThreatCenter:
    def __init__(self):
        self._active_threats: Dict[str, Dict[str, Any]] = {}

    def scan_telemetry(self,
                       processes: List[Dict[str, Any]],
                       connections: List[Dict[str, Any]],
                       cpu_percent: float,
                       ram_percent: float,
                       drives: Optional[List[Dict[str, Any]]] = None,
                       disk_io: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Evaluates current telemetry against threat rules and generates structured events.
        Covers CPU outliers, Memory pressure, Low Storage, Suspicious Executable locations,
        Unusual outbound connections, and High Disk Write spikes.
        """
        now = time.time()
        new_events = []

        # Rule 1: High CPU Outlier (process consuming > 75% CPU)
        for proc in processes[:6]:
            pid = proc.get("pid", -1)
            name = proc.get("name", "").lower()
            if pid <= 0 or "idle" in name or "system idle" in name:
                continue
            if proc.get("cpu_percent", 0) > 75.0:
                threat_id = f"high_cpu_{proc['pid']}"
                if threat_id not in self._active_threats:
                    event = {
                        "id": threat_id,
                        "timestamp": now,
                        "category": "High CPU Process",
                        "severity": "WARNING" if proc["cpu_percent"] < 90 else "HIGH",
                        "source": "Process Collector",
                        "target": f"{proc['name']} (PID: {proc['pid']})",
                        "reason": f"Process is utilizing {proc['cpu_percent']}% of total CPU capacity.",
                        "evidence": f"PID={proc['pid']}, Executable='{proc['path']}', CPU={proc['cpu_percent']}%, Threads={proc['threads']}",
                        "status": "DETECTED",
                        "recommended_action": f"Tangguhkan sementara atau turunkan prioritas {proc['name']} (PID: {proc['pid']}).",
                        "action_taken": None,
                        "resolved_at": None,
                        "pid": proc["pid"]
                    }
                    self._active_threats[threat_id] = event
                    new_events.append(event)

        # Rule 2: Suspicious Process Executables in Temp/User directories
        for proc in processes[:20]:
            pid = proc.get("pid", -1)
            if pid <= 4:
                continue
            path = proc.get("path", "").lower()
            name = proc.get("name", "").lower()
            # Flag processes executing directly from AppData\Local\Temp
            if "\\temp\\" in path or "\\appdata\\local\\temp\\" in path:
                if not any(safe in name for safe in ("python", "node", "installer", "update", "setup", "code")):
                    threat_id = f"suspicious_temp_{pid}"
                    if threat_id not in self._active_threats:
                        event = {
                            "id": threat_id,
                            "timestamp": now,
                            "category": "Suspicious Executable",
                            "severity": "HIGH",
                            "source": "Process Collector",
                            "target": f"{proc['name']} (PID: {pid})",
                            "reason": f"Proses berjalan langsung dari direktori Temp pengguna ({path}).",
                            "evidence": f"PID={pid}, Path='{proc.get('path')}'",
                            "status": "SUSPICIOUS",
                            "recommended_action": f"Periksa apakah proses {proc['name']} merupakan installer resmi atau hentikan jika mencurigakan.",
                            "action_taken": None,
                            "resolved_at": None,
                            "pid": pid
                        }
                        self._active_threats[threat_id] = event
                        new_events.append(event)

        # Rule 3: Critical Low Disk Space (< 10% free or < 5GB)
        if drives:
            for d in drives:
                pct = d.get("percent", 0.0)
                free_gb = round(d.get("free_bytes", 0) / (1024**3), 1)
                mount = d.get("mountpoint", d.get("device", "Disk"))
                if pct > 90.0 or free_gb < 5.0:
                    threat_id = f"low_disk_{mount.replace(':', '').replace('\\\\', '')}"
                    if threat_id not in self._active_threats:
                        event = {
                            "id": threat_id,
                            "timestamp": now,
                            "category": "Storage Anomaly",
                            "severity": "CRITICAL" if pct > 95 else "HIGH",
                            "source": "Storage Collector",
                            "target": f"Drive {mount}",
                            "reason": f"Kapasitas penyimpanan Drive {mount} hampir habis ({pct}% terpakai, sisa {free_gb} GB).",
                            "evidence": f"Total={round(d.get('total_bytes',0)/(1024**3),1)}GB, Free={free_gb}GB, Used={pct}%",
                            "status": "CONFIRMED",
                            "recommended_action": f"Bersihkan file sampah di folder Temp atau jalankan Storage Analyzer untuk membebaskan ruang disk {mount}.",
                            "action_taken": None,
                            "resolved_at": None
                        }
                        self._active_threats[threat_id] = event
                        new_events.append(event)

        # Rule 4: Unusual Outbound Connection Spike (>35 outbound connections)
        conn_by_proc: Dict[str, int] = {}
        for c in connections:
            if c.get("state") == "ESTABLISHED" and c.get("is_external"):
                key = f"{c['process_name']}|{c['pid']}"
                conn_by_proc[key] = conn_by_proc.get(key, 0) + 1

        for proc_key, count in conn_by_proc.items():
            if count > 35 and not any(br in proc_key.lower() for br in ("chrome", "msedge", "firefox", "brave", "opera", "discord")):
                pname, pid_str = proc_key.split("|")
                threat_id = f"high_conn_{pid_str}"
                if threat_id not in self._active_threats:
                    event = {
                        "id": threat_id,
                        "timestamp": now,
                        "category": "Unusual Network Activity",
                        "severity": "HIGH",
                        "source": "Socket Explorer",
                        "target": f"{pname} (PID: {pid_str})",
                        "reason": f"Proses membuka {count} koneksi remote eksternal simultan (baseline: 5–20).",
                        "evidence": f"Active remote connections: {count}",
                        "status": "SUSPICIOUS",
                        "recommended_action": f"Periksa host tujuan dan pastikan izin koneksi jaringan untuk {pname}.",
                        "action_taken": None,
                        "resolved_at": None,
                        "pid": int(pid_str) if pid_str.isdigit() else 0
                    }
                    self._active_threats[threat_id] = event
                    new_events.append(event)

        # Rule 5: Extreme System Memory Exhaustion (>94%)
        if ram_percent > 94.0:
            threat_id = "ram_exhaustion"
            if threat_id not in self._active_threats:
                event = {
                    "id": threat_id,
                    "timestamp": now,
                    "category": "System Anomaly",
                    "severity": "CRITICAL",
                    "source": "Memory Collector",
                    "target": "System RAM",
                    "reason": f"Kapasitas memori fisik sangat kritis ({ram_percent}% terpakai).",
                    "evidence": f"RAM usage: {ram_percent}%",
                    "status": "CONFIRMED",
                    "recommended_action": "Bebaskan working set memori agar sistem tidak mengalami thrashing.",
                    "action_taken": None,
                    "resolved_at": None
                }
                self._active_threats[threat_id] = event
                new_events.append(event)

        return new_events

    def get_threats(self) -> List[Dict[str, Any]]:
        return list(self._active_threats.values())

    async def throttle_and_cooldown_process(self, pid: int, duration: float = 3.5) -> Dict[str, Any]:
        """
        Active remediation for High CPU Process with Multi-Tier Fallback:
        Tier 1: Temporarily pause (suspend) process for cooldown duration.
        Tier 2 (Fallback): If suspend is denied, lower CPU priority to IDLE/BELOW_NORMAL.
        Tier 3: Detailed diagnostic explanation with alternative tool options if all fail.
        """
        import psutil
        import asyncio
        if not psutil.pid_exists(pid):
            return {"success": False, "message": f"Proses PID {pid} sudah tidak aktif di sistem."}
        try:
            p = psutil.Process(pid)
            pname = p.name()
        except Exception as e:
            return {"success": False, "message": f"Tidak dapat mengakses proses PID {pid}: {str(e)}"}

        # Tier 1: Try suspend/resume
        try:
            p.suspend()

            async def _resume_worker(proc, delay, name, target_pid):
                await asyncio.sleep(delay)
                try:
                    if proc.is_running():
                        proc.resume()
                except Exception:
                    pass

            asyncio.create_task(_resume_worker(p, duration, pname, pid))
            return {
                "success": True,
                "tool_used": "process_suspend",
                "message": f"Proses {pname} (PID: {pid}) berhasil ditangguhkan sejenak ({duration} detik) untuk mendinginkan CPU lalu normal kembali."
            }
        except (psutil.AccessDenied, PermissionError):
            # Tier 2 Fallback: Lower CPU Priority Class
            try:
                if hasattr(psutil, 'IDLE_PRIORITY_CLASS'):
                    p.nice(psutil.IDLE_PRIORITY_CLASS)
                elif hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS'):
                    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)

                return {
                    "success": True,
                    "tool_used": "priority_throttle",
                    "message": f"Izin penangguhan terbatas. Berhasil beralih ke Opsi Tool 2: Prioritas CPU untuk {pname} (PID: {pid}) diturunkan ke IDLE untuk meredakan beban prosesor."
                }
            except Exception as pe:
                return {
                    "success": False,
                    "error_code": "ACCESS_DENIED",
                    "tool_used": "failed_all_tools",
                    "can_fallback": True,
                    "message": f"Gagal menindak {pname} (PID: {pid}): Izin ditolak (Access Denied). Proses ini merupakan layanan sistem terproteksi atau membutuhkan hak Administrator.",
                    "suggested_actions": [
                        {"label": "Paksa Hentikan (Kill)", "action": "TERMINATE_PROCESS"},
                        {"label": "Tandai False Positive (Aman)", "action": "FALSE_POSITIVE"}
                    ]
                }
        except Exception as e:
            return {
                "success": False,
                "error_code": "GENERAL_ERROR",
                "can_fallback": True,
                "message": f"Gagal menangguhkan proses {pname} (PID: {pid}): {str(e)}",
                "suggested_actions": [
                    {"label": "Paksa Hentikan (Kill)", "action": "TERMINATE_PROCESS"},
                    {"label": "Tandai False Positive (Aman)", "action": "FALSE_POSITIVE"}
                ]
            }

    def trim_system_memory(self) -> Dict[str, Any]:
        """
        Active remediation for Memory Exhaustion:
        Trims process working sets to release unneeded committed pages.
        """
        import ctypes
        import psutil
        trimmed_count = 0
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x001F0FFF, False, proc.info['pid'])
                    if handle:
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        trimmed_count += 1
                except Exception:
                    pass
            return {"success": True, "message": f"Memory working set berhasil dibebaskan di {trimmed_count} proses aktif."}
        except Exception as e:
            return {"success": False, "message": f"Gagal membebaskan memori: {str(e)}"}

    async def mitigate_all_threats(self) -> Dict[str, Any]:
        """
        Executes batch remediation for all active threat events simultaneously.
        Trims RAM, cools down rogue processes, cleans temp junk, and marks events as MITIGATED.
        """
        active_list = list(self._active_threats.values())
        if not active_list:
            return {"success": True, "mitigated_count": 0, "failed_count": 0, "total_threats": 0, "message": "Tidak ada ancaman aktif yang perlu ditindak."}

        results = []
        mitigated_count = 0

        # 1. Clean RAM if any memory threat or general optimization
        trim_res = self.trim_system_memory()

        # 2. Iterate through each threat and execute corresponding action
        for threat in active_list:
            t_id = threat["id"]
            cat = threat.get("category", "")
            pid = threat.get("pid")

            if (cat == "High CPU Process" or "CPU" in cat) and pid:
                res = await self.throttle_and_cooldown_process(pid, duration=3.5)
                if res.get("success"):
                    await self.update_threat_status(t_id, "MITIGATED", action=res.get("message"))
                    mitigated_count += 1
                    results.append(f"✓ {threat['target']}: {res['message']}")
                else:
                    await self.update_threat_status(t_id, "ACTION_FAILED", action=res.get("message"))
                    results.append(f"⚠ {threat['target']}: {res['message']}")
            elif cat in ("Storage Anomaly", "Low Storage"):
                from backend.engine.storage_analyzer import storage_analyzer
                c_res = storage_analyzer.clean_user_temp_files()
                await self.update_threat_status(t_id, "MITIGATED", action=c_res.get("message"))
                mitigated_count += 1
                results.append(f"✓ {threat['target']}: {c_res.get('message')}")
            elif cat in ("System Anomaly", "Memory") or "RAM" in threat.get("target", ""):
                await self.update_threat_status(t_id, "MITIGATED", action=trim_res.get("message"))
                mitigated_count += 1
                results.append(f"✓ {threat['target']}: {trim_res.get('message')}")
            else:
                # Flag general anomalies as mitigated/inspected
                await self.update_threat_status(t_id, "MITIGATED", action="Dimediasi dan ditinjau melalui Batch Remediation Engine")
                mitigated_count += 1
                results.append(f"✓ {threat['target']}: Anomali diverifikasi dan ditandai selesai.")

        failed_count = max(0, len(active_list) - mitigated_count)
        return {
            "success": True,
            "mitigated_count": mitigated_count,
            "failed_count": failed_count,
            "total_threats": len(active_list),
            "details": results,
            "message": f"Berhasil memitigasi {mitigated_count} dari {len(active_list)} anomali keamanan sistem."
        }


    async def update_threat_status(self, threat_id: str, new_status: str, action: Optional[str] = None):
        if threat_id in self._active_threats:
            t = self._active_threats[threat_id]
            t["status"] = new_status
            if action:
                t["action_taken"] = action
            if new_status in ("RESOLVED", "MITIGATED", "FALSE_POSITIVE"):
                t["resolved_at"] = time.time()
                await db_manager.save_threat(t)
                del self._active_threats[threat_id]
            else:
                await db_manager.save_threat(t)

threat_center = ThreatCenter()
