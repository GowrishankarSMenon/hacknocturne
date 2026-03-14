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
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.geo_lookup import lookup_ip

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


def _enrich_session_with_geo(session: dict) -> dict:
    """Resolve public IP and attach geo data to a session dict."""
    raw_ip = session.get("client_ip", "")
    geo = lookup_ip(raw_ip) if raw_ip else None
    if geo:
        session["client_ip"] = geo.get("query", raw_ip)  # Resolved public IP
        session["geo"] = {
            "city": geo.get("city", "Unknown"),
            "country": geo.get("country", "Unknown"),
            "isp": geo.get("isp", "Unknown"),
            "lat": geo.get("lat", 0),
            "lon": geo.get("lon", 0),
        }
    return session


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
            
        _enrich_session_with_geo(session)
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
    _enrich_session_with_geo(result)

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


@app.get("/api/live-typing")
def get_live_typing():
    """Get real-time keystroke buffers for all active sessions."""
    conn = _get_db()
    rows = conn.execute("SELECT session_id, buffer, updated_at FROM live_typing").fetchall()
    conn.close()
    
    typing_data = {}
    for r in rows:
        typing_data[r["session_id"]] = {
            "buffer": r["buffer"],
            "updated_at": r["updated_at"]
        }
    return typing_data


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
    # Get IP mapping for sessions
    conn = _get_db()
    ip_map = {r["session_id"]: r["client_ip"] for r in conn.execute("SELECT session_id, client_ip FROM sessions").fetchall()}
    conn.close()

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".db"):
            continue
        session_id = fname.replace(".db", "")
        try:
            sdb = sqlite3.connect(os.path.join(sessions_dir, fname))
            sdb.row_factory = sqlite3.Row
            tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threat_events'").fetchall()
            if tables:
                if severity:
                    rows = sdb.execute("SELECT * FROM threat_events WHERE severity = ? ORDER BY timestamp DESC", (severity,)).fetchall()
                else:
                    rows = sdb.execute("SELECT * FROM threat_events ORDER BY timestamp DESC").fetchall()
                
                for r in rows:
                    alert = dict(r)
                    alert["session_id"] = session_id
                    alert["client_ip"] = ip_map.get(session_id, "unknown")
                    # Map event_type to threat_type for frontend compatibility
                    alert["threat_type"] = alert.get("event_type", "unknown")
                    # Extract message from data if details is missing
                    if "data" in alert and alert["data"]:
                        try:
                            data_obj = json.loads(alert["data"])
                            alert["details"] = data_obj.get("message", data_obj.get("filepath", "Unknown event"))
                        except:
                            alert["details"] = alert["data"]
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


@app.get("/api/sessions/{session_id}/intents")
def get_session_intents(session_id: str):
    """Get intent detections for a session."""
    sdb = _get_session_db(session_id)
    if not sdb:
        raise HTTPException(status_code=404, detail="Session database not found")
    try:
        tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='intents'").fetchall()
        if not tables:
            return {"session_id": session_id, "intents": [], "count": 0}
        rows = sdb.execute("SELECT * FROM intents ORDER BY timestamp ASC").fetchall()
        return {"session_id": session_id, "intents": [dict(r) for r in rows], "count": len(rows)}
    finally:
        sdb.close()


@app.get("/api/sessions/{session_id}/canaries")
def get_session_canaries(session_id: str):
    """Get canary files for a session."""
    sdb = _get_session_db(session_id)
    if not sdb:
        raise HTTPException(status_code=404, detail="Session database not found")
    try:
        tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='canary_files'").fetchall()
        if not tables:
            return {"session_id": session_id, "canaries": [], "count": 0}
        rows = sdb.execute("SELECT * FROM canary_files ORDER BY planted_at ASC").fetchall()
        return {"session_id": session_id, "canaries": [dict(r) for r in rows], "count": len(rows)}
    finally:
        sdb.close()


@app.post("/api/sessions/{session_id}/report")
def generate_threat_report(session_id: str):
    """Generate a Groq-powered threat intelligence report for a session."""
    sdb = _get_session_db(session_id)
    if not sdb:
        raise HTTPException(status_code=404, detail="Session database not found")

    try:
        # Gather report data
        commands = [dict(r) for r in sdb.execute("SELECT * FROM commands ORDER BY timestamp ASC").fetchall()]

        intents = []
        tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='intents'").fetchall()
        if tables:
            intents = [dict(r) for r in sdb.execute("SELECT * FROM intents ORDER BY timestamp ASC").fetchall()]

        canaries = []
        tables = sdb.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='canary_files'").fetchall()
        if tables:
            canaries = [dict(r) for r in sdb.execute("SELECT * FROM canary_files ORDER BY planted_at ASC").fetchall()]
    finally:
        sdb.close()

    # Get session metadata
    conn = _get_db()
    row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
    conn.close()
    session_meta = dict(row) if row else {}

    # Build prompt for Groq
    commands_text = "\n".join([f"  [{c['timestamp']}] {c['command']}" for c in commands[-20:]])
    intents_text = "\n".join([
        f"  - {i['intent_type']} (confidence: {i.get('confidence', 'N/A')}, trigger: {i.get('trigger_command', 'N/A')})"
        for i in intents
    ])
    canaries_text = "\n".join([
        f"  - {c['filepath']} (intent: {c['intent']}, triggered: {bool(c.get('triggered', 0))})"
        for c in canaries
    ])

    prompt = f"""Generate a concise Threat Intelligence Report in markdown for this honeypot session:

Session ID: {session_id}
Attacker IP: {session_meta.get('client_ip', 'unknown')}

Commands executed:
{commands_text if commands_text else '  None'}

Intent detections:
{intents_text if intents_text else '  None detected'}

Canary files:
{canaries_text if canaries_text else '  None planted'}

Generate a professional report with:
1. Executive Summary (2-3 sentences)
2. Intent Progression (numbered list)
3. Canary Tripwire Results
4. Risk Assessment (LOW/MEDIUM/HIGH/CRITICAL)
5. Recommended Actions (bullet list)

Keep it concise. Use markdown formatting."""

    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="GROQ_API_KEY not set in environment")

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800,
        )
        report_text = response.choices[0].message.content
        return {"session_id": session_id, "report": report_text}

    except ImportError:
        raise HTTPException(status_code=503, detail="Groq library not installed. Run: pip install groq")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/api/rsa-alerts")
def get_rsa_alerts():
    """Get all RSA (Random Segment Assessment) alerts."""
    conn = _get_db()
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rsa_alerts'").fetchall()
        if not tables:
            return {"alerts": [], "count": 0}
        rows = conn.execute("SELECT * FROM rsa_alerts WHERE resolved = 0 ORDER BY timestamp DESC").fetchall()
        alerts = []
        for r in rows:
            alert = dict(r)
            # Parse JSON details
            if alert.get("details"):
                try:
                    alert["details"] = json.loads(alert["details"]) if isinstance(alert["details"], str) else alert["details"]
                except Exception:
                    pass
            alerts.append(alert)
        return {"alerts": alerts, "count": len(alerts)}
    finally:
        conn.close()


@app.post("/api/rsa-alerts/{alert_id}/action")
def record_rsa_action(alert_id: int, action: str):
    """Record a cyber team action on an RSA alert."""
    conn = _get_db()
    try:
        # Verify alert exists
        alert = conn.execute("SELECT id FROM rsa_alerts WHERE id = ?", (alert_id,)).fetchone()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")

        conn.execute(
            "INSERT INTO cyber_actions (alert_id, action, operator, timestamp) VALUES (?, ?, 'dashboard', ?)",
            (alert_id, action, datetime.now().isoformat()),
        )
        if action in ("Block", "Dismiss"):
            conn.execute("UPDATE rsa_alerts SET resolved = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        return {"status": "ok", "alert_id": alert_id, "action": action}
    finally:
        conn.close()


@app.get("/api/hassh")
def get_all_hassh():
    """Get all HASSH fingerprints with cross-IP correlation."""
    conn = _get_db()
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hassh_fingerprints'").fetchall()
        if not tables:
            return {"fingerprints": [], "correlations": [], "count": 0}

        rows = conn.execute("SELECT * FROM hassh_fingerprints ORDER BY timestamp DESC").fetchall()
        fingerprints = [dict(r) for r in rows]

        # Build cross-IP correlation: group by HASSH, find those seen from >1 IP
        hassh_groups: dict = {}
        for fp in fingerprints:
            hv = fp.get("hassh", "")
            if not hv:
                continue
            if hv not in hassh_groups:
                hassh_groups[hv] = {"ips": set(), "sessions": [], "usernames": set()}
            hassh_groups[hv]["ips"].add(fp.get("client_ip", ""))
            hassh_groups[hv]["sessions"].append(fp.get("session_id", ""))
            hassh_groups[hv]["usernames"].add(fp.get("username", ""))

        correlations = []
        for hassh_val, data in hassh_groups.items():
            if len(data["ips"]) > 1:
                correlations.append({
                    "hassh": hassh_val,
                    "ips": list(data["ips"]),
                    "ip_count": len(data["ips"]),
                    "sessions": data["sessions"],
                    "usernames": list(data["usernames"]),
                })

        return {"fingerprints": fingerprints, "correlations": correlations, "count": len(fingerprints)}
    finally:
        conn.close()


@app.get("/api/sessions/{session_id}/hassh")
def get_session_hassh(session_id: str):
    """Get HASSH fingerprint for a specific session."""
    conn = _get_db()
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hassh_fingerprints'").fetchall()
        if not tables:
            return {"session_id": session_id, "hassh": None}
        row = conn.execute("SELECT hassh FROM hassh_fingerprints WHERE session_id = ? LIMIT 1", (session_id,)).fetchone()
        return {"session_id": session_id, "hassh": row["hassh"] if row else None}
    finally:
        conn.close()
