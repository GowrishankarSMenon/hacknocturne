FROM python:3.11-slim

LABEL maintainer="AeroGhost Team"
LABEL description="AeroGhost - Autonomous Cyber-Deception Honeypot"

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose SSH honeypot, Streamlit dashboard, and REST API
EXPOSE 2222 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',2222),2); s.close()" || exit 1

# Launch all services
CMD python run.py
