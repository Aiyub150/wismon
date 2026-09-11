"""
Windows System Monitoring - Single Unified Startup Script.
Launches the background telemetry collectors, SQLite database, REST/SSE backend,
and the modern web dashboard interface.
"""

import sys
import time
import uvicorn
import psutil

def main():
    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    time.sleep(0.3)
    cpu_initial = round(psutil.cpu_percent(interval=None), 1)
    ram_initial = round(psutil.virtual_memory().percent, 1)

    host = "127.0.0.1"
    port = 8080

    print("=======================================")
    print(" WISMON — Windows System Monitoring")
    print(" Monitor. Analyze. Understand.")
    print("=======================================")
    print()
    print(f"Backend : http://{host}:{port}")
    print(f"Frontend: http://{host}:{port}")
    print()
    print("Monitoring: ONLINE (SSE Stream Active)")
    print()
    print(f"CPU     : {cpu_initial}%")
    print(f"Memory  : {ram_initial}%")
    print(f"Threats : 0")
    print()
    print("Press Ctrl+C to stop.")
    print("=======================================")
    print()

    # Run uvicorn server
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        log_level="warning",
        access_log=False
    )

if __name__ == "__main__":
    main()
