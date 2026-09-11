"""
Process Collector for Windows System Monitoring.
Enumerates live Windows processes with CPU, Memory, Threads, Handles, and I/O.
"""

import time
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class ProcessCollector(BaseCollector):
    def __init__(self, interval: float = 2.0):
        super().__init__(name="process", interval=interval)
        self._proc_cache: Dict[int, psutil.Process] = {}

    def collect(self) -> Dict[str, Any]:
        processes: List[Dict[str, Any]] = []
        current_pids = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe', 'username', 'status', 'create_time', 'num_threads']):
            try:
                info = proc.info
                pid = info['pid']
                current_pids.add(pid)

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

                # Handles
                try:
                    num_handles = cached_proc.num_handles()
                except Exception:
                    num_handles = 0

                # I/O
                try:
                    io = cached_proc.io_counters()
                    io_read = io.read_bytes
                    io_write = io.write_bytes
                except Exception:
                    io_read = 0
                    io_write = 0

                processes.append({
                    "pid": pid,
                    "name": info.get("name") or f"PID {pid}",
                    "path": info.get("exe") or "Unavailable (System/Protected)",
                    "username": info.get("username") or "SYSTEM",
                    "status": info.get("status") or "running",
                    "cpu_percent": round(cpu_perc, 1),
                    "memory_bytes": mem_rss,
                    "virtual_memory_bytes": mem_vms,
                    "threads": info.get("num_threads") or 1,
                    "handles": num_handles,
                    "io_read_bytes": io_read,
                    "io_write_bytes": io_write,
                    "created_at": info.get("create_time", 0.0)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Clean cache of terminated processes
        self._proc_cache = {p: pr for p, pr in self._proc_cache.items() if p in current_pids}

        # Sort descending by CPU by default
        processes.sort(key=lambda x: x["cpu_percent"], reverse=True)

        return {
            "total_count": len(processes),
            "processes": processes,
            "top_cpu": processes[:5],
            "top_memory": sorted(processes, key=lambda x: x["memory_bytes"], reverse=True)[:5],
            "status": "online"
        }

    def terminate_process(self, pid: int) -> Dict[str, Any]:
        """Safely terminates a process after explicit confirmation."""
        try:
            p = psutil.Process(pid)
            name = p.name()
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
