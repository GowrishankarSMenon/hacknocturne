# ─────────────────────────────────────────────
# Stage 1: Build Next.js dashboard
# ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install dependencies
COPY website/package.json website/package-lock.json* ./
RUN npm ci

# Copy source and build
COPY website/ .

# Set API URL for production build
# The backend API will be on the same host, port 8000
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

RUN npm run build

# ─────────────────────────────────────────────
# Stage 2: Python backend (SSH honeypot + API)
# ─────────────────────────────────────────────
FROM python:3.11-slim AS backend

LABEL maintainer="AeroGhost Team"
LABEL description="AeroGhost - Autonomous AI Cyber-Deception Honeypot"

WORKDIR /app

# Install Node.js (to run Next.js production server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python backend
COPY agents/ agents/
COPY api/ api/
COPY ssh_listener/ ssh_listener/
COPY state_manager/ state_manager/
COPY main.py run.py setup.py rsa_tester.py ./
COPY .env.example .env 2>/dev/null || true

# Copy built Next.js app from stage 1
COPY --from=frontend-builder /frontend/.next ./.next
COPY --from=frontend-builder /frontend/node_modules ./node_modules
COPY --from=frontend-builder /frontend/public ./public
COPY --from=frontend-builder /frontend/package.json ./package.json

# Create logs directory
RUN mkdir -p logs/sessions logs/reports

# Ports:
#   2222 — SSH Honeypot
#   8000 — FastAPI REST API
#   3000 — Next.js Dashboard
EXPOSE 2222 8000 3000

# Health check on SSH port
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',2222),2); s.close()" || exit 1

# Entrypoint script starts all three services
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
