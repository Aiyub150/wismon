"""
Configuration module for Windows System Monitoring.
Loads environment settings with sane defaults adhering to project specifications.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "monitoring.db"
STATIC_DIR = BASE_DIR / "frontend"

# Load .env if present
load_dotenv(BASE_DIR / ".env")

# Server settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8080"))

# Monitoring intervals (seconds)
INTERVAL_REALTIME = float(os.getenv("INTERVAL_REALTIME", "1.0"))
INTERVAL_PROCESS = float(os.getenv("INTERVAL_PROCESS", "2.0"))
INTERVAL_SOCKETS = float(os.getenv("INTERVAL_SOCKETS", "3.0"))
INTERVAL_SERVICES = float(os.getenv("INTERVAL_SERVICES", "5.0"))
INTERVAL_STORAGE_IO = float(os.getenv("INTERVAL_STORAGE_IO", "1.0"))

# Data retention policy
DETAILED_RETENTION_HOURS = int(os.getenv("DETAILED_RETENTION_HOURS", "24"))
AGGREGATED_RETENTION_DAYS = int(os.getenv("AGGREGATED_RETENTION_DAYS", "7"))
RING_BUFFER_SIZE = 300  # 300 samples in RAM for zero-latency charts & SSE

# Dahoo AI Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Gemini pricing estimates (USD per 1M tokens) - gemini-2.5-flash rates
INPUT_PRICE_PER_1M = 0.075
OUTPUT_PRICE_PER_1M = 0.300
