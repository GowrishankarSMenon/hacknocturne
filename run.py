#!/usr/bin/env python3
"""
AeroGhost — Cross-Platform Launcher.
Replaces start.bat/stop.bat with a single Python script
that works on Windows, Linux, and macOS.

Usage:
    python run.py          # Start all services
    python run.py --no-api # Start without REST API
    Ctrl+C                 # Graceful shutdown
"""

import os
import sys
import signal
import subprocess
import time
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("aeroghost")

BANNER = r"""
    ___                   ______               __
   /   | ___  _ __ ___  / ____/ /_ ____  _____/ /_
  / /| |/ _ \| '__/ _ \/ / __/ __ \/ __ \/ ___/ __/
 / ___ /  __/ | | (_) / /_/ / / / / /_/ (__  ) /_
/_/  |_\___/|_|  \___/\____/_/ /_/\____/____/\__/

    Autonomous Cyber-Deception System v2.0
"""

processes = []


def find_python():
    """Find the correct Python executable (venv or system)."""
    if os.name == "nt":
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join("venv", "bin", "python")

    if os.path.exists(venv_python):
        return venv_python
    return sys.executable


def check_dependencies(python_exe):
    """Install missing dependencies."""
    logger.info("Checking dependencies...")
    subprocess.run(
        [python_exe, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def start_honeypot(python_exe):
    """Start the SSH honeypot server."""
    logger.info("Starting SSH Honeypot on port 2222...")
    proc = subprocess.Popen(
        [python_exe, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(("Honeypot", proc))
    return proc


def start_dashboard(python_exe):
    """Start the Next.js enterprise intelligence dashboard."""
    logger.info("Starting Next.js Intelligence Dashboard on port 3000...")
    # Change dir to website and run npm dev
    cwd = os.path.join(os.getcwd(), "website")
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=(os.name == 'nt') # Needs shell=True on Windows to find npm
    )
    processes.append(("Dashboard", proc))
    return proc


def start_api(python_exe):
    """Start the FastAPI REST API."""
    logger.info("Starting REST API on port 8000...")
    proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "api.server:app",
         "--host", "0.0.0.0",
         "--port", "8000",
         "--log-level", "warning"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    processes.append(("API", proc))
    return proc


def shutdown(signum=None, frame=None):
    """Gracefully shut down all services."""
    logger.info("\nShutting down AeroGhost...")
    for name, proc in processes:
        if proc.poll() is None:
            logger.info(f"  Stopping {name} (PID {proc.pid})...")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    logger.info("All services stopped.")
    sys.exit(0)


def main():
    print(BANNER)

    # Parse args
    no_api = "--no-api" in sys.argv

    # Find Python
    python_exe = find_python()
    logger.info(f"Using Python: {python_exe}")

    # Ensure logs directory
    os.makedirs("logs", exist_ok=True)

    # Check deps
    check_dependencies(python_exe)

    # Register shutdown handler
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    if os.name == "nt":
        # Windows-specific: also handle Ctrl+C via SIGBREAK
        try:
            signal.signal(signal.SIGBREAK, shutdown)
        except (AttributeError, ValueError):
            pass

    # Start services
    start_honeypot(python_exe)
    time.sleep(1)

    start_dashboard(python_exe)
    time.sleep(1)

    if not no_api:
        start_api(python_exe)

    logger.info("")
    logger.info("=" * 55)
    logger.info("  AeroGhost is LIVE")
    logger.info("=" * 55)
    logger.info(f"  SSH Honeypot  :  ssh user@localhost -p 2222")
    logger.info(f"  Dashboard     :  http://localhost:8501")
    if not no_api:
        logger.info(f"  REST API      :  http://localhost:8000/api/docs")
    logger.info(f"  Press Ctrl+C to shut down")
    logger.info("=" * 55)
    logger.info("")

    # Monitor processes
    try:
        while True:
            for name, proc in processes:
                if proc.poll() is not None:
                    logger.warning(f"{name} exited with code {proc.returncode}")
            time.sleep(5)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
