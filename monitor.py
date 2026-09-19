"""
Windows System Monitoring - Single Unified Startup Script.
Launches the background telemetry collectors, SQLite database, REST/SSE backend,
and the modern web dashboard interface.
"""

import sys
import time
import socket
import uvicorn
import psutil

from backend.config import HOST, PORT

def is_port_in_use(host: str, port: int) -> bool:
    """Checks whether the specified port is already bound by another process."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def get_pid_using_port(port: int):
    """Finds the PID of the process occupying the port."""
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port:
                return conn.pid
    except Exception:
        pass
    return None

import argparse

def main():
    parser = argparse.ArgumentParser(description="Windows System Monitoring")
    parser.add_argument("--host", type=str, default=HOST, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=PORT, help="Port to bind the server to")
    args = parser.parse_args()

    host = args.host
    port = args.port

    # Pre-flight check: Verify if the port is already occupied
    if is_port_in_use(host, port):
        pid = get_pid_using_port(port)
        pname = "Unknown"
        if pid and psutil.pid_exists(pid):
            try:
                pname = psutil.Process(pid).name()
            except Exception:
                pass

        print("=======================================")
        print(" WISMON — Port Conflict Detected")
        print("=======================================")
        print(f"[ERROR] Port {port} sedang digunakan oleh proses lain: {pname} (PID: {pid})!")
        print()
        print("Penyebab:")
        print(" - Kemungkinan ada instance WISMON sebelumnya yang masih berjalan di latar belakang.")
        print()
        print("Solusi:")
        print(f" 1. Hentikan proses tersebut via Task Manager atau PowerShell:")
        if pid:
            print(f"    Stop-Process -Id {pid} -Force")
        print(f" 2. Atau ganti konfigurasi PORT di file .env (misalnya PORT=8081).")
        print("=======================================")
        sys.exit(1)

    # Warm up CPU measurement
    psutil.cpu_percent(interval=None)
    time.sleep(0.3)
    cpu_initial = round(psutil.cpu_percent(interval=None), 1)
    ram_initial = round(psutil.virtual_memory().percent, 1)

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
    try:
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            log_level="warning",
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n[INFO] WISMON dihentikan oleh pengguna.")
    except OSError as e:
        if "10048" in str(e) or "address already in use" in str(e).lower():
            print(f"\n[ERROR] Port {port} baru saja digunakan oleh proses lain: {e}")
        else:
            raise e

if __name__ == "__main__":
    main()
