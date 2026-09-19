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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "medium").lower()

# Dahoo Assistant & Session Memory Settings
DAHOO_MEMORY_ENABLED = os.getenv("DAHOO_MEMORY_ENABLED", "true").lower() == "true"
DAHOO_ACTION_TTL_SECONDS = int(os.getenv("DAHOO_ACTION_TTL_SECONDS", "60"))
DAHOO_MAX_CONTEXT_TURNS = int(os.getenv("DAHOO_MAX_CONTEXT_TURNS", "10"))
DAHOO_DEFAULT_LANGUAGE = os.getenv("DAHOO_DEFAULT_LANGUAGE", "id")

# Gemini pricing estimates (USD per 1M tokens) - Google AI Studio standard rates
INPUT_PRICE_PER_1M = 0.300
OUTPUT_PRICE_PER_1M = 2.500
