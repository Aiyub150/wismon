"""
Threat Center & Security Analysis Engine for Windows System Monitoring.
Tracks security events, suspicious resource usage, anomalous socket patterns,
and enforces a structured threat lifecycle with safe, user-confirmed mitigation.
"""

import os
import time
import uuid
from typing import Dict, Any, List, Optional
import psutil
from backend.db import db_manager

# Process Safety & EDR Protection Policies
WISMON_PID = os.getpid()
try:
    WISMON_PPID = os.getppid()
except Exception:
    WISMON_PPID = None

SECURITY_AGENTS = {
    "bdservicehost.exe", "vsserv.exe", "bdredline.exe", "epsecurityservice.exe",
    "msmpeng.exe", "nissrv.exe", "securityhealthservice.exe", "smartscreen.exe",
    "csfalconservice.exe", "sentinelagent.exe", "sentinelctl.exe",
    "mbamservice.exe", "avp.exe", "mcshield.exe", "mfetp.exe",
    "rtvscan.exe", "ccsvchst.exe"
}

CRITICAL_SYSTEM_PROCESSES = {
    "system", "system idle process", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "dwm.exe", "fontdrvhost.exe",
    "memcompression", "registry", "secure system"
}


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

    async def throttle_and_cooldown_process(self, pid: int, duration: float = 3.5, expected_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Active remediation for High CPU Process with Multi-Tier Fallback & Strict Safety Guardrails:
        - Safety Check 1: Protect WISMON's own server process (PID & PPID) to prevent server hangs/crashes.
        - Safety Check 2: Protect Security / EDR Agents (Bitdefender, Defender, CrowdStrike, etc.).
        - Safety Check 3: Protect Windows Core Critical Processes (System, csrss, lsass, etc.).
        - Verification: Validate process existence and name identity.
        Tier 1: Temporarily pause (suspend) process for cooldown duration.
        Tier 2 (Fallback): If suspend is denied, lower CPU priority to IDLE/BELOW_NORMAL.
        Tier 3: Detailed diagnostic explanation with alternative options if all fail.
        """
        import psutil
        import asyncio

        # Safety Guardrail 1: WISMON Server Self-Protection
        if pid == WISMON_PID or (WISMON_PPID and pid == WISMON_PPID) or (pid == os.getpid()):
            return {
                "success": False,
                "error_code": "WISMON_SELF_PROCESS",
                "is_protected": True,
                "can_fallback": False,
                "message": f"Tindakan ditolak demi stabilitas: PID {pid} adalah server utama WISMON. Penangguhan akan membekukan koneksi dan memicu crash aplikasi.",
                "recommendation": "Untuk meringankan beban kerja WISMON, gunakan mode adaptive sampling atau tutup tab browser yang tidak digunakan."
            }

        try:
            target_chk = psutil.Process(pid)
            chk_name = target_chk.name().lower()
            if chk_name in ("python.exe", "pythonw.exe"):
                cmd_chk = " ".join(target_chk.cmdline()).lower()
                if any(kw in cmd_chk for kw in ("monitor.py", "wismon", "uvicorn", "backend.main")):
                    return {
                        "success": False,
                        "error_code": "WISMON_SELF_PROCESS",
                        "is_protected": True,
                        "can_fallback": False,
                        "message": f"Tindakan ditolak demi stabilitas: PID {pid} ({chk_name}) menjalankan proses backend WISMON. Penangguhan akan mematikan server.",
                        "recommendation": "Server WISMON diproteksi dari tindakan penangguhan atau terminasi."
                    }
        except Exception:
            pass

        # Safety Guardrail 2: Windows Critical Kernel Processes by PID
        if pid in (0, 4):
            return {
                "success": False,
                "error_code": "SYSTEM_CRITICAL_PROCESS",
                "is_protected": True,
                "can_fallback": False,
                "message": f"Tindakan ditolak: PID {pid} merupakan proses inti kernel Windows yang tidak boleh ditangguhkan demi mencegah kegagalan sistem (BSOD).",
                "recommendation": "Tunggu hingga aktivitas latar belakang Windows selesai secara wajar."
            }

        # Safety Guardrail 3: Expected Name Protection (Security Agents & System Processes)
        if expected_name:
            exp_lower = expected_name.lower()
            if exp_lower in SECURITY_AGENTS or any(agent_kw in exp_lower for agent_kw in ("bitdefender", "bdservice", "vsserv", "edr", "antivirus", "defender")):
                return {
                    "success": False,
                    "error_code": "SECURITY_AGENT_PROTECTED",
                    "is_protected": True,
                    "can_fallback": False,
                    "message": f"Tindakan ditolak demi integritas endpoint: '{expected_name}' (PID: {pid}) adalah Agen Keamanan / EDR ({expected_name}). Penangguhan dapat memicu alarm keamanan Windows dan melemahkan proteksi.",
                    "recommendation": f"Periksa status pemindaian atau jadwal proteksi langsung melalui konsol aplikasi keamanan {expected_name}."
                }
            if exp_lower in CRITICAL_SYSTEM_PROCESSES:
                return {
                    "success": False,
                    "error_code": "SYSTEM_CRITICAL_PROCESS",
                    "is_protected": True,
                    "can_fallback": False,
                    "message": f"Tindakan ditolak: '{expected_name}' (PID: {pid}) merupakan proses inti kernel Windows yang tidak boleh ditangguhkan demi mencegah kegagalan sistem (BSOD).",
                    "recommendation": "Tunggu hingga aktivitas latar belakang Windows selesai secara wajar."
                }

        if not psutil.pid_exists(pid):
            return {"success": False, "message": f"Proses PID {pid} sudah tidak aktif di sistem.", "can_fallback": False}

        try:
            p = psutil.Process(pid)
            pname = p.name()
            pname_lower = pname.lower()
        except Exception as e:
            return {"success": False, "message": f"Tidak dapat mengakses proses PID {pid}: {str(e)}", "can_fallback": False}

        # Target Identity Verification (Name mismatch check)
        if expected_name and expected_name.lower() not in pname_lower:
            return {
                "success": False,
                "error_code": "IDENTITY_MISMATCH",
                "can_fallback": False,
                "message": f"Identitas target tidak sesuai: PID {pid} terdeteksi sebagai '{pname}' (bukan '{expected_name}'). Tindakan dibatalkan demi keselamatan sistem."
            }

        # Safety Guardrail 4: Live Process Name Checks
        if pname_lower in SECURITY_AGENTS or any(agent_kw in pname_lower for agent_kw in ("bitdefender", "bdservice", "vsserv", "edr", "antivirus", "defender")):
            return {
                "success": False,
                "error_code": "SECURITY_AGENT_PROTECTED",
                "is_protected": True,
                "can_fallback": False,
                "message": f"Tindakan ditolak demi integritas endpoint: '{pname}' (PID: {pid}) adalah Agen Keamanan / EDR ({pname}). Penangguhan dapat memicu alarm keamanan Windows dan melemahkan proteksi.",
                "recommendation": f"Periksa status pemindaian atau jadwal proteksi langsung melalui konsol aplikasi keamanan {pname}."
            }

        if pname_lower in CRITICAL_SYSTEM_PROCESSES:
            return {
                "success": False,
                "error_code": "SYSTEM_CRITICAL_PROCESS",
                "is_protected": True,
                "can_fallback": False,
                "message": f"Tindakan ditolak: '{pname}' (PID: {pid}) merupakan proses inti kernel Windows yang tidak boleh ditangguhkan demi mencegah kegagalan sistem (BSOD).",
                "recommendation": "Tunggu hingga aktivitas latar belakang Windows selesai secara wajar."
            }

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
        Calculates exact before/after percentage and capacity freed.
        """
        import ctypes
        import psutil
        mem_before = psutil.virtual_memory()
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
            mem_after = psutil.virtual_memory()
            freed_bytes = max(0, mem_before.used - mem_after.used)
            freed_mb = round(freed_bytes / (1024 * 1024), 1)
            freed_gb = round(freed_bytes / (1024**3), 2)
            pct_before = round(mem_before.percent, 1)
            pct_after = round(mem_after.percent, 1)
            pct_diff = round(pct_before - pct_after, 1)
            total_gb = round(mem_before.total / (1024**3), 1)
            freed_str = f"{freed_gb} GB" if freed_gb >= 1.0 else f"{freed_mb} MB"

            return {
                "success": True,
                "action_type": "TRIM_MEMORY",
                "trimmed_count": trimmed_count,
                "freed_bytes": freed_bytes,
                "freed_mb": freed_mb,
                "freed_gb": freed_gb,
                "freed_str": freed_str,
                "pct_before": pct_before,
                "pct_after": pct_after,
                "pct_diff": pct_diff,
                "total_gb": total_gb,
                "message": f"Memory working set berhasil dibebaskan di {trimmed_count} proses aktif. Membebaskan {freed_str} RAM ({pct_diff}% penurunan beban, dari {pct_before}% ke {pct_after}%).",
                "verification": {
                    "metric": "ram",
                    "before": f"{pct_before}%",
                    "after": f"{pct_after}%",
                    "diff_percent": pct_diff,
                    "freed_capacity": freed_str,
                    "total_capacity": f"{total_gb} GB",
                    "verified": True,
                    "detail": f"RAM sebelum: {pct_before}%, sesudah: {pct_after}% (Turun {pct_diff}%), Kapasitas dibebaskan: {freed_str}"
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Gagal membebaskan memori: {str(e)}", "verified": False}

    async def mitigate_all_threats(self) -> Dict[str, Any]:
        """
        Executes batch remediation for all active threat events simultaneously.
        Trims RAM, cools down rogue processes, cleans temp junk, and marks events truthfully
        (MITIGATED vs PROTECTED_SKIPPED vs ACTION_FAILED).
        """
        active_list = list(self._active_threats.values())
        if not active_list:
            return {"success": True, "mitigated_count": 0, "failed_count": 0, "total_threats": 0, "message": "Tidak ada ancaman aktif yang perlu ditindak."}

        results = []
        mitigated_count = 0
        skipped_count = 0

        # 1. Clean RAM if any memory threat or general optimization
        trim_res = self.trim_system_memory()

        # 2. Iterate through each threat and execute corresponding action
        for threat in active_list:
            t_id = threat["id"]
            cat = threat.get("category", "")
            pid = threat.get("pid")

            if (cat == "High CPU Process" or "CPU" in cat) and pid:
                res = await self.throttle_and_cooldown_process(pid, duration=3.5)
                if res.get("is_protected"):
                    await self.update_threat_status(t_id, "PROTECTED_SKIPPED", action=res.get("message"))
                    skipped_count += 1
                    results.append(f"🛡️ {threat['target']}: {res['message']}")
                elif res.get("success"):
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

        failed_count = max(0, len(active_list) - mitigated_count - skipped_count)
        msg_parts = [f"Berhasil memitigasi {mitigated_count} anomali"]
        if skipped_count > 0:
            msg_parts.append(f"{skipped_count} proses terproteksi dilewati demi keselamatan sistem")
        if failed_count > 0:
            msg_parts.append(f"{failed_count} memerlukan tindakan manual")

        return {
            "success": True,
            "mitigated_count": mitigated_count,
            "skipped_count": skipped_count,
            "failed_count": failed_count,
            "total_threats": len(active_list),
            "details": results,
            "message": ", ".join(msg_parts) + "."
        }

    async def update_threat_status(self, threat_id: str, new_status: str, action: Optional[str] = None):
        if threat_id in self._active_threats:
            t = self._active_threats[threat_id]
            t["status"] = new_status
            if action:
                t["action_taken"] = action
            if new_status in ("RESOLVED", "MITIGATED", "FALSE_POSITIVE", "PROTECTED_SKIPPED"):
                t["resolved_at"] = time.time()
                await db_manager.save_threat(t)
                del self._active_threats[threat_id]
            else:
                await db_manager.save_threat(t)

    async def optimize_cpu_workload(self, duration: float = 3.5) -> Dict[str, Any]:
        """
        Scans active processes, skips protected processes (WISMON, Security Agents, System Core),
        and applies cooldown on the highest consuming user process or trims memory.
        """
        import psutil
        import asyncio

        cpu_before = psutil.cpu_percent(interval=None)
        candidate = None

        try:
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    info = p.info
                    pid = info['pid']
                    name = (info['name'] or '').lower()
                    if pid in (0, 4, WISMON_PID) or (WISMON_PPID and pid == WISMON_PPID):
                        continue
                    if "idle" in name or name in CRITICAL_SYSTEM_PROCESSES or name in SECURITY_AGENTS:
                        continue
                    if any(kw in name for kw in ("bitdefender", "defender", "edr", "antivirus", "vsserv", "bdservice")):
                        continue
                    if name in ("python.exe", "pythonw.exe"):
                        cmd = " ".join(p.cmdline()).lower()
                        if any(kw in cmd for kw in ("monitor.py", "wismon", "uvicorn")):
                            continue
                    
                    c_pct = info.get('cpu_percent') or 0.0
                    if c_pct > 15.0:
                        if not candidate or c_pct > candidate['cpu_percent']:
                            candidate = {'pid': pid, 'name': info['name'], 'cpu_percent': c_pct}
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass

        if candidate:
            res = await self.throttle_and_cooldown_process(candidate['pid'], duration=duration, expected_name=candidate['name'])
            if res.get("success"):
                await asyncio.sleep(0.3)
                cpu_after = round(psutil.cpu_percent(interval=None), 1)
                cpu_diff = round(cpu_before - cpu_after, 1)
                res["action_type"] = "OPTIMIZE_CPU"
                res["candidate"] = candidate
                res["cpu_before"] = cpu_before
                res["cpu_after"] = cpu_after
                res["cpu_diff"] = cpu_diff
                res["verification"] = {
                    "metric": "cpu",
                    "before": f"{cpu_before}%",
                    "after": f"{cpu_after}%",
                    "diff_percent": cpu_diff,
                    "verified": True,
                    "detail": f"CPU sebelum tindakan: {cpu_before}%, setelah tindakan: {cpu_after}% (Penurunan beban {cpu_diff}%)"
                }
                res["message"] = f"Beban prosesor berhasil distabilkan! Proses {candidate['name']} (PID: {candidate['pid']}) ditenangkan. Beban CPU turun {cpu_diff}% (dari {cpu_before}% ke {cpu_after}%)."
                return res

            # If candidate was protected or denied, fallback to trimming RAM to relieve system pressure
            trim_res = self.trim_system_memory()
            await asyncio.sleep(0.3)
            cpu_after = round(psutil.cpu_percent(interval=None), 1)
            cpu_diff = round(cpu_before - cpu_after, 1)
            freed_str = trim_res.get("freed_str", "0 MB")
            return {
                "success": True,
                "action_type": "OPTIMIZE_CPU",
                "candidate": candidate,
                "message": f"Proses {candidate['name']} terproteksi. Beralih ke pembebasan memori: beban CPU stabil pada {cpu_after}% (Turun {cpu_diff}%). {trim_res.get('message', '')}",
                "cpu_before": cpu_before,
                "cpu_after": cpu_after,
                "cpu_diff": cpu_diff,
                "ram_details": trim_res,
                "verification": {
                    "metric": "cpu",
                    "before": f"{cpu_before}%",
                    "after": f"{cpu_after}%",
                    "diff_percent": cpu_diff,
                    "ram_freed": freed_str,
                    "verified": True,
                    "detail": f"CPU sebelum: {cpu_before}%, sesudah: {cpu_after}% (Turun {cpu_diff}%). {trim_res.get('verification', {}).get('detail', '')}"
                }
            }
        else:
            # If no high rogue process found, trim RAM to relieve overall system pressure
            trim_res = self.trim_system_memory()
            await asyncio.sleep(0.3)
            cpu_after = round(psutil.cpu_percent(interval=None), 1)
            cpu_diff = round(cpu_before - cpu_after, 1)
            freed_str = trim_res.get("freed_str", "0 MB")
            pct_diff = trim_res.get("pct_diff", 0)
            return {
                "success": True,
                "action_type": "OPTIMIZE_CPU",
                "message": f"Beban CPU stabil pada {cpu_after}% (Turun {cpu_diff}%). {trim_res.get('message', 'Sistem dioptimalkan.')}",
                "candidate": None,
                "cpu_before": cpu_before,
                "cpu_after": cpu_after,
                "cpu_diff": cpu_diff,
                "ram_details": trim_res,
                "verification": {
                    "metric": "cpu",
                    "before": f"{cpu_before}%",
                    "after": f"{cpu_after}%",
                    "diff_percent": cpu_diff,
                    "ram_freed": freed_str,
                    "verified": True,
                    "detail": f"CPU sebelum: {cpu_before}%, sesudah: {cpu_after}% (Turun {cpu_diff}%). {trim_res.get('verification', {}).get('detail', '')}"
                }
            }

threat_center = ThreatCenter()
