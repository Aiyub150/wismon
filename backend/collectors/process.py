"""
Process Collector for Windows System Monitoring.
Enumerates live Windows processes with CPU, Memory, Threads, Handles, and I/O.
"""

import time
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

COMMON_PROCESS_DESCRIPTIONS = {
    "System Idle Process": "Windows Kernel idle thread measuring available CPU capacity",
    "System": "NT Kernel & System worker threads",
    "svchost.exe": "Host Process for Windows Services",
    "explorer.exe": "Windows Desktop Shell & File Explorer",
    "dwm.exe": "Desktop Window Manager (UI Rendering)",
    "csrss.exe": "Client Server Runtime Subsystem",
    "services.exe": "Windows Service Control Manager",
    "lsass.exe": "Local Security Authority Subsystem Service",
    "smss.exe": "Session Manager Subsystem",
    "Registry": "Windows Registry Storage Process",
    "spoolsv.exe": "Print Spooler Service",
    "taskhostw.exe": "Host Process for Windows Tasks",
    "conhost.exe": "Console Window Host",
    "RuntimeBroker.exe": "Windows Runtime Broker (App Permissions)",
    "SearchIndexer.exe": "Windows Search Indexing Service",
    "python.exe": "Python Interpreter (WISMON Engine)",
    "msedge.exe": "Microsoft Edge Browser",
    "chrome.exe": "Google Chrome Browser",
    "code.exe": "Visual Studio Code"
}

class ProcessCollector(BaseCollector):
    def __init__(self, interval: float = 2.0):
        super().__init__(name="process", interval=interval)
        self._proc_cache: Dict[int, psutil.Process] = {}
        self._meta_cache: Dict[int, Dict[str, Any]] = {}

    def collect(self) -> Dict[str, Any]:
        processes: List[Dict[str, Any]] = []
        current_pids = set()

        for proc in psutil.process_iter(['pid', 'name', 'status', 'num_threads']):
            try:
                info = proc.info
                pid = info['pid']
                current_pids.add(pid)

                # Fetch or cache immutable process metadata (path, user, create_time)
                meta = self._meta_cache.get(pid)
                if not meta:
                    try:
                        exe = proc.exe()
                    except Exception:
                        exe = "Unavailable (System/Protected)"
                    try:
                        username = proc.username()
                    except Exception:
                        username = "SYSTEM"
                    try:
                        create_time = proc.create_time()
                    except Exception:
                        create_time = 0.0
                    meta = {
                        "path": exe,
                        "username": username,
                        "created_at": create_time
                    }
                    self._meta_cache[pid] = meta

                # CPU percentage requires two samples; psutil caches state on the Process object
                cached_proc = self._proc_cache.get(pid)
                if not cached_proc:
                    cached_proc = proc
                    self._proc_cache[pid] = proc
                    cpu_perc = 0.0
                else:
                    try:
                        cpu_perc = cached_proc.cpu_percent(interval=None)
                    except Exception:
                        cpu_perc = 0.0

                # Memory
                try:
                    mem_info = cached_proc.memory_info()
                    mem_rss = mem_info.rss
                    mem_vms = mem_info.vms
                except Exception:
                    mem_rss = 0
                    mem_vms = 0

                p_name = info.get("name") or f"PID {pid}"
                is_idle = (pid == 0) or ("idle" in p_name.lower())
                num_cores = psutil.cpu_count(logical=True) or 1
                cpu_norm = round(cpu_perc / num_cores, 1)

                processes.append({
                    "pid": pid,
                    "name": p_name,
                    "description": COMMON_PROCESS_DESCRIPTIONS.get(p_name, "Windows User/System Process"),
                    "path": meta["path"],
                    "username": meta["username"],
                    "status": info.get("status") or "running",
                    "cpu_percent": round(cpu_perc, 1),
                    "cpu_percent_normalized": cpu_norm,
                    "is_idle": is_idle,
                    "memory_bytes": mem_rss,
                    "virtual_memory_bytes": mem_vms,
                    "threads": info.get("num_threads") or 1,
                    "handles": 0,
                    "io_read_bytes": 0,
                    "io_write_bytes": 0,
                    "created_at": meta["created_at"]
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Clean cache of terminated processes
        self._proc_cache = {p: pr for p, pr in self._proc_cache.items() if p in current_pids}
        self._meta_cache = {p: m for p, m in self._meta_cache.items() if p in current_pids}

        # Sort descending by CPU by default
        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)

        # For the top 5 processes only, enrich with handle count and I/O (optimizes CPU syscalls)
        for top_p in processes[:5]:
            pr = self._proc_cache.get(top_p["pid"])
            if pr:
                try:
                    top_p["handles"] = pr.num_handles()
                except Exception:
                    pass
                try:
                    io = pr.io_counters()
                    top_p["io_read_bytes"] = io.read_bytes
                    top_p["io_write_bytes"] = io.write_bytes
                except Exception:
                    pass

        return {
            "total_count": len(processes),
            "processes": processes,
            "top_cpu": processes[:5],
            "top_memory": sorted(processes, key=lambda x: x["memory_bytes"], reverse=True)[:5],
            "status": "online"
        }

    def terminate_process(self, pid: int) -> Dict[str, Any]:
        """Safely terminates a process after explicit confirmation and safety validation."""
        import os
        wismon_pid = os.getpid()
        if pid == wismon_pid:
            return {
                "success": False,
                "is_protected": True,
                "message": "Security violation: Server utama WISMON tidak dapat dihentikan oleh aplikasi sendiri demi stabilitas."
            }

        if pid in (0, 4):
            return {
                "success": False,
                "is_protected": True,
                "message": "Security violation: Windows Core Kernel process cannot be terminated."
            }
        try:
            p = psutil.Process(pid)
            name = p.name()
            name_lower = name.lower()
            critical_names = {
                "system", "system idle process", "smss.exe", "csrss.exe", 
                "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe", "dwm.exe"
            }
            security_agents = {
                "bdservicehost.exe", "vsserv.exe", "bdredline.exe", "epsecurityservice.exe",
                "msmpeng.exe", "nissrv.exe", "securityhealthservice.exe", "smartscreen.exe"
            }
            if name_lower in critical_names:
                return {
                    "success": False,
                    "is_protected": True,
                    "message": f"Security violation: Critical Windows system process '{name}' cannot be terminated."
                }
            if name_lower in security_agents:
                return {
                    "success": False,
                    "is_protected": True,
                    "message": f"Security violation: Protected Security Agent / EDR '{name}' cannot be terminated."
                }

            p.terminate()
            p.wait(timeout=2)
            return {"success": True, "message": f"Process {name} (PID: {pid}) terminated successfully."}
        except psutil.TimeoutExpired:
            p.kill()
            return {"success": True, "message": f"Process {pid} killed forcefully."}
        except psutil.NoSuchProcess:
            return {"success": False, "message": f"Process {pid} no longer exists."}
        except psutil.AccessDenied:
            return {"success": False, "message": f"Access denied terminating PID {pid}. Administrator rights required."}
        except Exception as e:
            return {"success": False, "message": str(e)}

process_collector = ProcessCollector()
