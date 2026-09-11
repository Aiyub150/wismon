"""
Windows Services Collector for Windows System Monitoring.
Enumerates installed Windows services and analyzes services mapped under svchost.exe instances.
"""

import psutil
from typing import Dict, Any, List
from backend.collectors.base import BaseCollector

class ServicesCollector(BaseCollector):
    def __init__(self, interval: float = 5.0):
        super().__init__(name="services", interval=interval)

    def collect(self) -> Dict[str, Any]:
        services_list: List[Dict[str, Any]] = []
        svchost_groups: Dict[int, List[Dict[str, Any]]] = {}

        try:
            for s in psutil.win_service_iter():
                try:
                    s_info = s.as_dict()
                    name = s_info.get("name", "")
                    display_name = s_info.get("display_name", "")
                    status = s_info.get("status", "unknown")
                    start_type = s_info.get("start_type", "unknown")
                    pid = s_info.get("pid")
                    binpath = s_info.get("binpath", "")
                    username = s_info.get("username", "")

                    item = {
                        "name": name,
                        "display_name": display_name,
                        "status": status,
                        "start_type": start_type,
                        "pid": pid,
                        "binpath": binpath,
                        "username": username
                    }
                    services_list.append(item)

                    # Check svchost association
                    if pid and pid > 0 and ("svchost.exe" in binpath.lower() or "svchost" in (s_info.get("description", "").lower())):
                        if pid not in svchost_groups:
                            svchost_groups[pid] = []
                        svchost_groups[pid].append({
                            "name": name,
                            "display_name": display_name,
                            "status": status
                        })
                except Exception:
                    continue
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
