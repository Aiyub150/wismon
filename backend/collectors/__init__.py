"""
Collectors package initialization.
"""

from backend.collectors.cpu import CPUCollector
from backend.collectors.memory import MemoryCollector
from backend.collectors.gpu import GPUCollector
from backend.collectors.storage import StorageCollector
from backend.collectors.network import NetworkCollector
from backend.collectors.process import ProcessCollector
from backend.collectors.socket import SocketCollector
from backend.collectors.services import ServicesCollector
from backend.collectors.temperature import HardwareCollector

__all__ = [
    "CPUCollector",
    "MemoryCollector",
    "GPUCollector",
    "StorageCollector",
    "NetworkCollector",
    "ProcessCollector",
    "SocketCollector",
    "ServicesCollector",
    "HardwareCollector",
]
