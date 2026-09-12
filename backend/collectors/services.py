import time
import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class ServicesCollector(BaseCollector):
    def __init__(self, interval: float = 15.0):
        super().__init__(name="services", interval=interval)
        self._meta_cache: Dict[str, Dict[str, Any]] = {}
        self._last_full_refresh: float = 0.0

    def collect(self) -> Dict[str, Any]:
        now = time.time()
        is_full_refresh = (now - self._last_full_refresh) > 60.0 or not self._meta_cache

        services_list: List[Dict[str, Any]] = []
        svchost_groups: Dict[int, List[Dict[str, Any]]] = {}

        try:
            for s in psutil.win_service_iter():
                try:
                    s_name = s.name()
                    meta = self._meta_cache.get(s_name)

                    if is_full_refresh or not meta:
                        s_info = s.as_dict()
                        meta = {
                            "name": s_name,
                            "display_name": s_info.get("display_name", ""),
                            "start_type": s_info.get("start_type", "unknown"),
                            "binpath": s_info.get("binpath", ""),
                            "username": s_info.get("username", ""),
                            "is_svchost": "svchost.exe" in (s_info.get("binpath", "")).lower()
                        }
                        self._meta_cache[s_name] = meta

                    # Dynamic status and pid
                    try:
                        status = s.status()
                    except Exception:
                        status = "unknown"

                    try:
                        pid = s.pid()
                    except Exception:
                        pid = None

                    item = {
                        "name": meta["name"],
                        "display_name": meta["display_name"],
                        "status": status,
                        "start_type": meta["start_type"],
                        "pid": pid,
                        "binpath": meta["binpath"],
                        "username": meta["username"]
                    }
                    services_list.append(item)

                    # Map svchost instances
                    if pid and pid > 0 and meta.get("is_svchost"):
                        if pid not in svchost_groups:
                            svchost_groups[pid] = []
                        svchost_groups[pid].append({
                            "name": meta["name"],
                            "display_name": meta["display_name"],
                            "status": status
                        })
                except Exception:
                    continue

            if is_full_refresh:
                self._last_full_refresh = now
        except Exception:
            pass

        # Format svchost hierarchy
        svchost_tree = [
            {"pid": pid, "services": svcs, "service_count": len(svcs)}
            for pid, svcs in svchost_groups.items()
        ]

        running_count = sum(1 for s in services_list if s["status"] == "running")
        stopped_count = sum(1 for s in services_list if s["status"] == "stopped")

        return {
            "total_count": len(services_list),
            "running_count": running_count,
            "stopped_count": stopped_count,
            "services": services_list,
            "svchost_groups": svchost_tree,
            "status": "online"
        }
