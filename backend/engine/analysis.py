"""
Analysis Engine for Windows System Monitoring.
Calculates overall System Health Score, dynamic baselines, and detects multi-level anomalies.
"""

from typing import Dict, Any, List
from collections import deque

class AnalysisEngine:
    def __init__(self, history_window: int = 120):
        self.cpu_history: deque = deque(maxlen=history_window)
        self.ram_history: deque = deque(maxlen=history_window)
        self.net_history: deque = deque(maxlen=history_window)

    def update_telemetry(self, cpu_perc: float, ram_perc: float, net_mbps: float):
        self.cpu_history.append(cpu_perc)
        self.ram_history.append(ram_perc)
        self.net_history.append(net_mbps)

    def calculate_health(self, cpu_perc: float, ram_perc: float, storage_perc: float, threat_count: int) -> Dict[str, Any]:
        """
        Calculates System Health (0-100) and qualitative status:
        Healthy (80-100), Normal (60-79), Warning (40-59), Critical (<40).
        """
        score = 100

        # CPU penalty
        if cpu_perc > 90:
            score -= 25
        elif cpu_perc > 75:
            score -= 15
        elif cpu_perc > 60:
            score -= 5

        # RAM penalty
        if ram_perc > 90:
            score -= 25
        elif ram_perc > 80:
            score -= 15
        elif ram_perc > 70:
            score -= 5

        # Storage penalty
        if storage_perc > 95:
            score -= 20
        elif storage_perc > 85:
            score -= 10

        # Threats penalty
        score -= min(threat_count * 15, 40)

        score = max(0, min(100, score))

        if score >= 80:
            status = "Healthy"
            badge = "healthy"
        elif score >= 60:
            status = "Normal"
            badge = "normal"
        elif score >= 40:
            status = "Warning"
            badge = "warning"
        else:
            status = "Critical"
            badge = "critical"

        return {
            "score": score,
            "status": status,
            "badge": badge
        }

    def get_baseline_stats(self) -> Dict[str, Any]:
        """Calculates rolling average and typical ranges."""
        def stats_for(dq: deque, default_min: float, default_max: float):
            if not dq:
                return {"min": default_min, "max": default_max, "avg": (default_min + default_max) / 2}
            vals = list(dq)
            avg = sum(vals) / len(vals)
            return {
                "min": round(min(vals), 1),
                "max": round(max(vals), 1),
                "avg": round(avg, 1)
            }

        return {
            "cpu": stats_for(self.cpu_history, 15.0, 45.0),
            "ram": stats_for(self.ram_history, 35.0, 65.0),
            "network_mbps": stats_for(self.net_history, 0.1, 10.0)
        }

    def analyze_cpu_workload(self, current_cpu: float, top_process: Dict[str, Any]) -> Dict[str, Any]:
        """Level 1-3 CPU analysis with human-readable diagnostic recommendations."""
        baseline = self.get_baseline_stats()["cpu"]
        pname = top_process.get("name", "Unknown")
        pcpu = top_process.get("cpu_percent", 0.0)

        is_high = current_cpu > 80
        is_above_baseline = current_cpu > (baseline["avg"] + 25)

        if is_high or is_above_baseline:
            summary = f"CPU usage ({current_cpu}%) is significantly higher than the baseline ({baseline['min']}–{baseline['max']}%)."
            rec = f"Review active process '{pname}' consuming {pcpu}% CPU."
            severity = "WARNING" if current_cpu < 90 else "HIGH"
        else:
            summary = f"CPU workload is within normal baseline parameters ({baseline['min']}–{baseline['max']}%)."
            rec = "System is operating smoothly. No immediate action required."
            severity = "INFO"

        return {
            "current_usage": current_cpu,
            "baseline": f"{baseline['min']}–{baseline['max']}%",
            "baseline_avg": baseline["avg"],
            "primary_contributor": pname,
            "contributor_cpu": pcpu,
            "analysis": summary,
            "recommendation": rec,
            "severity": severity
        }
