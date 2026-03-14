#!/bin/bash
# docker-entrypoint.sh
# Starts all three services inside the single-image setup:
#   1. Python SSH Honeypot + REST API (via run.py)
#   2. Next.js dashboard (next start)
# Used by the monolithic Dockerfile (not docker-compose multi-service)

set -e

echo "🔴🟡🟢 AeroGhost starting..."
echo "   SSH Honeypot  → :2222"
echo "   REST API      → :8000"
echo "   Dashboard     → :3000"

# Start Next.js dashboard in background
echo "[dashboard] Starting Next.js..."
npm start --prefix /app &

# Start Python backend (SSH server + FastAPI) — keep in foreground
echo "[backend] Starting Python services..."
exec python run.py
