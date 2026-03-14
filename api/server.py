"""
AeroGhost REST API — FastAPI-based endpoint layer.
Provides programmatic access to honeypot data for SIEM integration,
external dashboards, and third-party tools.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AeroGhost API",
    description="REST API for the AeroGhost cyber-deception honeypot system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = os.path.join("logs", "ghostnet.db")


def _get_db():
    """Get a database connection."""
    if not os.path.exists(DB_FILE):
        raise HTTPException(status_code=503, detail="Database not initialized — start the honeypot first")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _session_db_path(session_id: str) -> str:
    return os.path.join("logs", "sessions", f"{session_id}.db")


def _get_session_db(session_id: str):
    path = _session_db_path(session_id)
    if not os.path.exists(path):
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────────

@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "aeroghost", "timestamp": datetime.now().isoformat()}


@app.get("/api/sessions")
def get_sessions(status: Optional[str] = None):
    """
    Get all sessions. Optional filter: ?status=active or ?status=closed
    Includes dynamic threat score calculation.
    """
    conn = _get_db()
    if status:
        rows = conn.execute("SELECT * FROM sessions WHERE status = ? ORDER BY start_time DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sessions ORDER BY start_time DESC").fetchall()
    conn.close()
    
    sessions = []
    for r in rows:
        session = dict(r)
        # Calculate live threat score
        score = 0
        sdb = _get_session_db(session["session_id"])
        if sdb:
            # Add points based on threat events severity
            threats = sdb.execute("SELECT severity FROM threat_events").fetchall()
            for t in threats:
                sev = t["severity"]
                if sev == "critical": score += 25
                elif sev == "high": score += 15
                elif sev == "medium": score += 10
                elif sev == "low": score += 5
                
            # Cap at 100
            session["threat_score"] = min(100, score)
            sdb.close()
        else:
            session["threat_score"] = 0
            
        sessions.append(session)
        
    return {"sessions": sessions, "count": len(sessions)}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Get details for a specific session."""
    conn = _get_db()
    row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    result = dict(row)

    # Attach command log from session-specific DB
    sdb = _get_session_db(session_id)
    if sdb:
        commands = sdb.execute("SELECT * FROM commands ORDER BY timestamp ASC").fetchall()
        result["commands"] = [dict(c) for c in commands]
        result["command_count"] = len(commands)
        sdb.close()

    return result


@app.get("/api/sessions/{session_id}/commands")
def get_session_commands(session_id: str):
    """Get all commands executed in a session."""
    sdb = _get_session_db(session_id)
    if not sdb:
        raise HTTPException(status_code=404, detail="Session database not found")
    rows = sdb.execute("SELECT * FROM commands ORDER BY timestamp ASC").fetchall()
    sdb.close()
    return {"session_id": session_id, "commands": [dict(r) for r in rows], "count": len(rows)}


@app.get("/api/alerts")
def get_alerts(severity: Optional[str] = None):
    """
    Get threat events across all sessions.
    Optional filter: ?severity=critical or ?severity=high
    """
    sessions_dir = os.path.join("logs", "sessions")
    if not os.path.exists(sessions_dir):
        return {"alerts": [], "count": 0}

    all_alerts = []
    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".db"):
            continue
        session_id = fname.replace(".db", "")
        try:
            sdb = sqlite3.connect(os.path.join(sessions_dir, fname))
            sdb.row_factory = sqlite3.Row
            # Check if threat_events table exists
            tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threat_events'").fetchall()
            if tables:
                if severity:
                    rows = sdb.execute("SELECT * FROM threat_events WHERE severity = ? ORDER BY timestamp DESC", (severity,)).fetchall()
                else:
                    rows = sdb.execute("SELECT * FROM threat_events ORDER BY timestamp DESC").fetchall()
                for r in rows:
                    alert = dict(r)
                    alert["session_id"] = session_id
                    all_alerts.append(alert)
            sdb.close()
        except Exception:
            pass

    all_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"alerts": all_alerts, "count": len(all_alerts)}


@app.get("/api/stats")
def get_stats():
    """Get summary statistics."""
    conn = _get_db()

    total = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    active = conn.execute("SELECT COUNT(*) as c FROM sessions WHERE status = 'active'").fetchone()["c"]
    unique_ips = conn.execute("SELECT COUNT(DISTINCT client_ip) as c FROM sessions").fetchone()["c"]

    # Get password stats
    passwords = conn.execute(
        "SELECT password_used, COUNT(*) as c FROM sessions WHERE password_used IS NOT NULL GROUP BY password_used ORDER BY c DESC LIMIT 10"
    ).fetchall()

    # Get SSH client stats
    clients = conn.execute(
        "SELECT client_software, COUNT(*) as c FROM sessions WHERE client_software IS NOT NULL GROUP BY client_software ORDER BY c DESC LIMIT 10"
    ).fetchall()

    conn.close()

    # Count total alerts across sessions
    alert_count = 0
    sessions_dir = os.path.join("logs", "sessions")
    if os.path.exists(sessions_dir):
        for fname in os.listdir(sessions_dir):
            if fname.endswith(".db"):
                try:
                    sdb = sqlite3.connect(os.path.join(sessions_dir, fname))
                    tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threat_events'").fetchall()
                    if tables:
                        count = sdb.execute("SELECT COUNT(*) as c FROM threat_events").fetchone()[0]
                        alert_count += count
                    sdb.close()
                except Exception:
                    pass

    return {
        "total_sessions": total,
        "active_sessions": active,
        "unique_attacker_ips": unique_ips,
        "total_alerts": alert_count,
        "top_passwords": [{"password": p["password_used"], "count": p["c"]} for p in passwords],
        "top_ssh_clients": [{"client": c["client_software"], "count": c["c"]} for c in clients],
    }
