"""
Network Collector for Windows System Monitoring.
Monitors network interfaces, IP addresses, MAC, status, and live upload/download throughput.
"""

import time
import socket
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class NetworkCollector(BaseCollector):
    def __init__(self, interval: float = 1.0):
        super().__init__(name="network", interval=interval)
        self._last_net_io = None
        self._last_net_time = 0.0
        self._cached_interfaces: List[Dict[str, Any]] = []
        self._last_iface_time: float = 0.0
        self._cached_gateway: str = "Unavailable"

    def _get_default_gateway(self) -> str:
        """Finds primary local IP to infer gateway."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            # Most common gateway is x.x.x.1
            parts = ip.split(".")
            return f"{parts[0]}.{parts[1]}.{parts[2]}.1"
        except Exception:
            return "Unavailable"

    def _refresh_interfaces(self):
        """Refreshes adapter metadata on a lower 15-second frequency."""
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            interfaces: List[Dict[str, Any]] = []
            gateway_hint = self._get_default_gateway()
            self._cached_gateway = gateway_hint

            for iface_name, addr_list in addrs.items():
                stat = stats.get(iface_name)
                is_up = stat.isup if stat else False
                speed_mbps = stat.speed if stat and stat.speed > 0 else "Unavailable"

                ipv4 = "Unavailable"
                ipv6 = "Unavailable"
                mac = "Unavailable"

                for a in addr_list:
                    if a.family == socket.AF_INET:
                        ipv4 = a.address
                    elif a.family == getattr(socket, "AF_INET6", 23):
                        ipv6 = a.address.split("%")[0]
                    elif getattr(psutil, "AF_LINK", None) and a.family == psutil.AF_LINK:
                        mac = a.address

                iface_type = "Ethernet"
                lower_name = iface_name.lower()
                if "wi-fi" in lower_name or "wlan" in lower_name or "wireless" in lower_name:
                    iface_type = "Wi-Fi"
                elif "loopback" in lower_name:
                    iface_type = "Loopback"
                elif "virtual" in lower_name or "vethernet" in lower_name:
                    iface_type = "Virtual"

                interfaces.append({
                    "name": iface_name,
                    "type": iface_type,
                    "is_up": is_up,
                    "speed_mbps": speed_mbps,
                    "ipv4": ipv4,
                    "ipv6": ipv6,
                    "mac": mac,
                    "gateway": gateway_hint if is_up and ipv4 != "Unavailable" and not ipv4.startswith("127.") else "Unavailable",
                    "status": "Connected" if is_up else "Disconnected"
                })
            self._cached_interfaces = interfaces
        except Exception:
            pass

    def collect(self) -> Dict[str, Any]:
        now = time.time()

        # Refresh interfaces every 15 seconds to avoid expensive UDP socket & net_if query overhead
        if not self._cached_interfaces or (now - self._last_iface_time) > 15.0:
            self._refresh_interfaces()
            self._last_iface_time = now

        interfaces = self._cached_interfaces

        # Calculate live throughput
        io_current = psutil.net_io_counters(pernic=False)
        bytes_sent_sec = 0.0
        bytes_recv_sec = 0.0
        packets_sent_sec = 0.0
        packets_recv_sec = 0.0

        if self._last_net_io and self._last_net_time > 0 and io_current:
            dt = max(now - self._last_net_time, 0.001)
            bytes_sent_sec = max(0.0, (io_current.bytes_sent - self._last_net_io.bytes_sent) / dt)
            bytes_recv_sec = max(0.0, (io_current.bytes_recv - self._last_net_io.bytes_recv) / dt)
            packets_sent_sec = max(0.0, (io_current.packets_sent - self._last_net_io.packets_sent) / dt)
            packets_recv_sec = max(0.0, (io_current.packets_recv - self._last_net_io.packets_recv) / dt)

        self._last_net_io = io_current
        self._last_net_time = now

        return {
            "interfaces": interfaces,
            "throughput": {
                "bytes_sent_sec": round(bytes_sent_sec, 1),
                "bytes_recv_sec": round(bytes_recv_sec, 1),
                "packets_sent_sec": round(packets_sent_sec, 1),
                "packets_recv_sec": round(packets_recv_sec, 1),
                "total_bytes_sent": io_current.bytes_sent if io_current else 0,
                "total_bytes_recv": io_current.bytes_recv if io_current else 0
            },
            "status": "online"
        }
