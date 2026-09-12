"""
Socket & Connection Collector for Windows System Monitoring.
Enumerates active TCP/UDP sockets and resolves remote hostnames asynchronously with caching.
"""

import socket
import threading
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class SocketCollector(BaseCollector):
    def __init__(self, interval: float = 3.0):
        super().__init__(name="socket", interval=interval)
        self._dns_cache: Dict[str, str] = {
            "127.0.0.1": "localhost",
            "::1": "localhost",
            "0.0.0.0": "all-interfaces",
            "::": "all-interfaces"
        }
        self._dns_pending: set = set()
        self._cache_lock = threading.Lock()
        self._pid_name_cache: Dict[int, str] = {}
        self._cleanup_tick: int = 0

    def _async_resolve_dns(self, ip: str):
        """Asynchronously resolve an IP address in a background worker thread."""
        try:
            name, _, _ = socket.gethostbyaddr(ip)
            with self._cache_lock:
                self._dns_cache[ip] = name
        except Exception:
            with self._cache_lock:
                self._dns_cache[ip] = ip  # Fallback to IP itself
        finally:
            with self._cache_lock:
                self._dns_pending.discard(ip)

    def _get_hostname(self, ip: str) -> str:
        if not ip or ip in ("—", "0.0.0.0", "127.0.0.1", "::1", "::"):
            return self._dns_cache.get(ip, ip or "—")
        with self._cache_lock:
            if ip in self._dns_cache:
                return self._dns_cache[ip]
            if ip not in self._dns_pending:
                self._dns_pending.add(ip)
                threading.Thread(target=self._async_resolve_dns, args=(ip,), daemon=True).start()
        return ip  # Immediate non-blocking response

    def _resolve_process_name(self, pid: Optional[int]) -> str:
        """Lightweight on-demand PID name resolution with local caching."""
        if not pid or pid == 0:
            return "System"
        if pid in self._pid_name_cache:
            return self._pid_name_cache[pid]
        try:
            name = psutil.Process(pid).name()
            self._pid_name_cache[pid] = name
            return name
        except Exception:
            return f"PID {pid}"

    def collect(self) -> Dict[str, Any]:
        connections_list: List[Dict[str, Any]] = []

        try:
            conns = psutil.net_connections(kind='inet')
        except Exception:
            conns = []

        active_pids = set()
        for c in conns:
            proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
            laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "Unavailable"
            raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
            remote_ip = c.raddr.ip if c.raddr else None
            remote_port = c.raddr.port if c.raddr else None
            remote_host = self._get_hostname(remote_ip) if remote_ip else "—"

            pid = c.pid or 0
            if pid > 0:
                active_pids.add(pid)
            pname = self._resolve_process_name(pid)

            connections_list.append({
                "protocol": proto,
                "local_address": laddr,
                "remote_address": raddr,
                "remote_ip": remote_ip or "—",
                "remote_port": remote_port or 0,
                "remote_host": remote_host,
                "state": c.status or "—",
                "pid": pid,
                "process_name": pname
            })

        # Periodic cleanup of terminated PIDs in cache every 20 ticks (~1-2 min)
        self._cleanup_tick += 1
        if self._cleanup_tick >= 20:
            self._cleanup_tick = 0
            self._pid_name_cache = {p: n for p, n in self._pid_name_cache.items() if p in active_pids}

        # Summary statistics
        established = sum(1 for c in connections_list if c["state"] == "ESTABLISHED")
        listening = sum(1 for c in connections_list if c["state"] == "LISTEN")

        return {
            "total_connections": len(connections_list),
            "established_count": established,
            "listening_count": listening,
            "connections": connections_list,
            "status": "online"
        }
