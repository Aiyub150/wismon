"""
Socket & Connection Collector for Windows System Monitoring.
Enumerates active TCP/UDP sockets and resolves remote hostnames asynchronously with caching.
"""

import socket
import threading
import psutil
from typing import Dict, Any, List, Optional
from backend.collectors.base import BaseCollector

from concurrent.futures import ThreadPoolExecutor

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
        self._dns_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="wismon_dns")
        self._pid_name_cache: Dict[int, str] = {}
        self._windows_dns_cache: Dict[str, str] = {}
        self._last_dns_cache_poll: float = 0.0
        self._cleanup_tick: int = 0

    def _poll_windows_dns_cache(self):
        """Periodically queries Windows DNS Client Cache for accurate browser domain attribution."""
        now = time.time()
        if now - self._last_dns_cache_poll < 15.0:
            return
        self._last_dns_cache_poll = now

        def _worker():
            try:
                import subprocess, json
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                       "Get-DnsClientCache | Where-Object { $_.Data -ne $null } | Select-Object -Property Entry, Data | ConvertTo-Json -Compress"]
                out = subprocess.check_output(cmd, text=True, timeout=5, creationflags=flags)
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                new_mappings = {}
                for item in data:
                    entry = item.get("Entry")
                    val = item.get("Data")
                    if entry and val:
                        new_mappings[str(val).strip()] = str(entry).strip()
                with self._cache_lock:
                    self._windows_dns_cache.update(new_mappings)
            except Exception:
                pass

        self._dns_executor.submit(_worker)

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
            # Check Windows DNS client cache first (direct browser resolution)
            if ip in self._windows_dns_cache:
                return self._windows_dns_cache[ip]
            if ip in self._dns_cache:
                return self._dns_cache[ip]
            if ip not in self._dns_pending:
                self._dns_pending.add(ip)
                self._dns_executor.submit(self._async_resolve_dns, ip)
        return ip  # Immediate non-blocking response

    def _map_friendly_domain(self, host: str, ip: str) -> Tuple[str, str]:
        """
        Derives both a clean resolved domain and a recognizable service label.
        Returns: (resolved_domain, domain_label)
        """
        raw = host or ip or "—"
        if not host or host in ("—", ip):
            # Check if Windows DNS cache has mapped this IP
            with self._cache_lock:
                cached_entry = self._windows_dns_cache.get(ip)
            if cached_entry:
                raw = cached_entry

        r_lower = raw.lower()

        # YouTube / Google Services
        if any(k in r_lower for k in ("1e100.net", "googlevideo", "youtube", "ytimg", "google", "gstatic")):
            clean = "youtube.com" if any(y in r_lower for y in ("youtube", "googlevideo", "ytimg")) else "google.com"
            return clean, "YouTube / Google"

        # TikTok / ByteDance
        if any(k in r_lower for k in ("byteoversea", "tiktok", "ibytedtos", "pstatp")):
            return "tiktok.com", "TikTok"

        # Meta / Facebook / Instagram / WhatsApp
        if any(k in r_lower for k in ("fbcdn", "facebook", "meta.com", "instagram", "whatsapp")):
            return "meta.com", "Meta / Facebook / IG"

        # GitHub
        if any(k in r_lower for k in ("github.com", "githubusercontent")):
            return "github.com", "GitHub"

        # Discord
        if any(k in r_lower for k in ("discord.gg", "discord.com", "discordapp")):
            return "discord.com", "Discord"

        # Spotify
        if any(k in r_lower for k in ("spotify.com", "scdn.co", "spotifycdn")):
            return "spotify.com", "Spotify"

        # Netflix
        if any(k in r_lower for k in ("netflix.com", "nflxvideo.net", "nflxext")):
            return "netflix.com", "Netflix"

        # Steam / Valve
        if any(k in r_lower for k in ("steamcontent", "steampowered", "steamcommunity")):
            return "steampowered.com", "Steam / Valve"

        # Microsoft / Azure
        if any(k in r_lower for k in ("microsoft", "msedge", "azure", "windows.net", "live.com", "office.com")):
            return "microsoft.com", "Microsoft / Azure"

        # Cloudflare
        if "cloudflare" in r_lower:
            return "cloudflare.com", "Cloudflare CDN"

        # Akamai
        if "akamai" in r_lower:
            return "akamai.net", "Akamai CDN"

        # Fastly
        if "fastly" in r_lower:
            return "fastly.net", "Fastly CDN"

        # Amazon AWS
        if any(k in r_lower for k in ("aws", "amazon", "cloudfront")):
            return "amazonaws.com", "Amazon AWS / CloudFront"

        return raw, raw

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
            if remote_ip:
                resolved_domain, domain_label = self._map_friendly_domain(remote_host, remote_ip)
            else:
                resolved_domain, domain_label = "—", "—"

            pid = c.pid or 0
            if pid > 0:
                active_pids.add(pid)
            pname = self._resolve_process_name(pid)

            is_loopback = not remote_ip or remote_ip in ("127.0.0.1", "::1", "0.0.0.0", "::") or remote_ip.startswith("127.")
            is_external = bool(remote_ip and not is_loopback)

            connections_list.append({
                "protocol": proto,
                "local_address": laddr,
                "remote_address": raddr,
                "remote_ip": remote_ip or "—",
                "remote_port": remote_port or 0,
                "remote_host": remote_host,
                "resolved_domain": resolved_domain,
                "domain_label": domain_label,
                "state": c.status or "—",
                "pid": pid,
                "process_name": pname,
                "is_external": is_external
            })

        # Sort connections: External Established first, then external, then established, then listening
        def _sort_key(conn):
            ext = 1 if conn["is_external"] else 0
            est = 1 if conn["state"] == "ESTABLISHED" else 0
            return (ext * 2 + est), conn["remote_address"] != "—"

        connections_list.sort(key=_sort_key, reverse=True)

        # Periodic cleanup of terminated PIDs in cache every 20 ticks (~1-2 min)
        self._cleanup_tick += 1
        if self._cleanup_tick >= 20:
            self._cleanup_tick = 0
            self._pid_name_cache = {p: n for p, n in self._pid_name_cache.items() if p in active_pids}

        # Summary statistics
        established = sum(1 for c in connections_list if c["state"] == "ESTABLISHED")
        listening = sum(1 for c in connections_list if c["state"] == "LISTEN")
        external_count = sum(1 for c in connections_list if c["is_external"])

        return {
            "total_connections": len(connections_list),
            "established_count": established,
            "listening_count": listening,
            "external_count": external_count,
            "connections": connections_list,
            "status": "online"
        }
