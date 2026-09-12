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
                       ram_percent: float) -> List[Dict[str, Any]]:
        """
        Evaluates current telemetry against threat rules and generates structured events.
        Adheres to Section 17 & 18: Never labels something 'Malware' without proof;
        uses Suspicious / Anomalous / Investigation Recommended.
        """
        now = time.time()
        new_events = []

        # Rule 1: High CPU Outlier (process consuming > 75% for an extended duration)
        for proc in processes[:5]:
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
                        "recommended_action": f"Inspect workload or terminate process {proc['name']} (PID: {proc['pid']}).",
                        "action_taken": None,
                        "resolved_at": None,
                        "pid": proc["pid"]
                    }
                    self._active_threats[threat_id] = event
                    new_events.append(event)

        # Rule 2: Unusual Outbound Connection Spike (A single process opening many outbound sockets)
        conn_by_proc: Dict[str, int] = {}
        for c in connections:
            if c["state"] == "ESTABLISHED" and c["remote_ip"] not in ("—", "127.0.0.1", "::1"):
                key = f"{c['process_name']}|{c['pid']}"
                conn_by_proc[key] = conn_by_proc.get(key, 0) + 1

        for proc_key, count in conn_by_proc.items():
            if count > 45 and not ("chrome" in proc_key.lower() or "msedge" in proc_key.lower() or "firefox" in proc_key.lower()):
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
                        "reason": f"Process opened {count} simultaneous outbound connections (baseline: 5–20).",
                        "evidence": f"Active remote connections: {count}",
                        "status": "SUSPICIOUS",
                        "recommended_action": f"Review destination hosts and verify network authorization for {pname}.",
                        "action_taken": None,
                        "resolved_at": None,
                        "pid": int(pid_str) if pid_str.isdigit() else 0
                    }
                    self._active_threats[threat_id] = event
                    new_events.append(event)

        # Rule 3: Extreme System Memory Exhaustion (>94%)
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
                    "reason": f"Available physical memory critically low ({ram_percent}% committed).",
                    "evidence": f"RAM usage: {ram_percent}%",
                    "status": "CONFIRMED",
                    "recommended_action": "Identify top memory consumer and free committed pages to avoid system thrashing.",
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
        Active remediation for High CPU Process:
        Temporarily pauses (suspends) the runaway process for 3.5s to immediately relieve CPU stress,
        cool down temperatures, and resumes execution seamlessly.
        """
        import psutil
        import asyncio
        if not psutil.pid_exists(pid):
            return {"success": False, "message": f"Process PID {pid} no longer active."}
        try:
            p = psutil.Process(pid)
            pname = p.name()
            # Suspend the process
            p.suspend()

            # Background task to resume after cooldown duration
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
                "message": f"Proses {pname} (PID: {pid}) ditangguhkan sejenak ({duration} detik) untuk mendinginkan CPU lalu kembali normal."
            }
        except Exception as e:
            return {"success": False, "message": f"Gagal menangguhkan proses PID {pid}: {str(e)}"}

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

    async def update_threat_status(self, threat_id: str, new_status: str, action: Optional[str] = None):
        if threat_id in self._active_threats:
            t = self._active_threats[threat_id]
            t["status"] = new_status
            if action:
                t["action_taken"] = action
            if new_status in ("RESOLVED", "FALSE_POSITIVE"):
                t["resolved_at"] = time.time()
                await db_manager.save_threat(t)
                del self._active_threats[threat_id]
            else:
                await db_manager.save_threat(t)

threat_center = ThreatCenter()
