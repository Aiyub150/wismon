"""
Base Collector Module for Windows System Monitoring.
Provides error isolation, timing, execution statistics, and fail-safe wrappers.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger("SystemMonitoring.Collector")

class BaseCollector(ABC):
    def __init__(self, name: str, interval: float = 1.0):
        self.name = name
        self.interval = interval
        self.last_run: float = 0.0
        self.last_duration_ms: float = 0.0
        self.last_data: Optional[Dict[str, Any]] = None
        self.is_healthy: bool = True
        self.error_count: int = 0
        self.last_error: Optional[str] = None

    def should_collect(self, current_time: float) -> bool:
        """Determines if the collector is due to run."""
        return (current_time - self.last_run) >= self.interval

    def collect_safe(self) -> Dict[str, Any]:
        """
        Executes collect() inside a fail-safe boundary.
        Any exception is captured, logged, and isolated without crashing the application.
        """
        start = time.perf_counter()
        now = time.time()
        try:
            data = self.collect()
            self.last_data = data
            self.is_healthy = True
            self.last_error = None
            return data
        except Exception as e:
            self.error_count += 1
            self.is_healthy = False
            self.last_error = str(e)
            logger.warning(f"Collector [{self.name}] failed: {e}", exc_info=False)
            if self.last_data is not None:
                return self.last_data
            return {"status": "unavailable", "error": str(e), "name": self.name}
        finally:
            self.last_run = now
            self.last_duration_ms = (time.perf_counter() - start) * 1000.0

    @abstractmethod
    def collect(self) -> Dict[str, Any]:
        """Collect and return raw/normalized metrics from Windows APIs."""
        pass
