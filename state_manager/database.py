"""
GhostNet Database Layer — Per-Session SQLite Isolation.

Main DB (ghostnet.db): session index only
Per-session DB (logs/sessions/<session_id>.db): commands, intents, canaries, threat events
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class GhostNetDatabase:
    """
    Main database — session index and global queries only.
    Uses logs/ghostnet.db.
    """

    def __init__(self, db_file: str = "logs/ghostnet.db"):
        self.db_file = db_file
        os.makedirs(os.path.dirname(db_file) if os.path.dirname(db_file) else "logs", exist_ok=True)
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            client_ip TEXT,
            username TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT,
            client_software TEXT,
            password_used TEXT,
            client_port INTEGER
        )
        """)

        # Live typing table (for real-time dashboard feed)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_typing (
            session_id TEXT PRIMARY KEY,
            buffer TEXT,
            updated_at TIMESTAMP
        )
        """)

        # HASSH fingerprints (global — for cross-IP correlation)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hassh_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            client_ip TEXT,
            hassh TEXT,
            username TEXT,
            timestamp TIMESTAMP
        )
        """)

        # RSA Alerts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS rsa_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_ip TEXT,
            alert_type TEXT,
            severity TEXT,
            similarity_score INTEGER,
            details TEXT,
            timestamp TIMESTAMP,
            resolved INTEGER DEFAULT 0
        )
        """)

        # Cyber team actions on alerts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cyber_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER,
            action TEXT,
            operator TEXT DEFAULT 'system',
            timestamp TIMESTAMP,
            FOREIGN KEY(alert_id) REFERENCES rsa_alerts(id)
        )
        """)

        conn.commit()
        conn.close()

    def create_session(self, session_id: str, client_ip: str, username: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO sessions (session_id, client_ip, username, start_time, status)
        VALUES (?, ?, ?, ?, ?)
        """, (session_id, client_ip, username, datetime.now(), "active"))
        conn.commit()
        conn.close()

    def update_session_fingerprint(self, session_id: str, client_software: str = None,
                                     password_used: str = None, client_port: int = None):
        """Update session with SSH fingerprint data."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        updates = []
        params = []
        if client_software is not None:
            updates.append("client_software = ?")
            params.append(client_software)
        if password_used is not None:
            updates.append("password_used = ?")
            params.append(password_used)
        if client_port is not None:
            updates.append("client_port = ?")
            params.append(client_port)
        if updates:
            params.append(session_id)
            cursor.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE session_id = ?", params)
            conn.commit()
        conn.close()

    def close_session(self, session_id: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE sessions SET status = 'closed', end_time = ? WHERE session_id = ?
        """, (datetime.now(), session_id))
        conn.commit()
        conn.close()
        # Also clear live typing
        self.clear_live_typing(session_id)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session metadata by session_id."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_session_hassh(self, session_id: str) -> Optional[str]:
        """Get the HASSH fingerprint for a specific session."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT hassh FROM hassh_fingerprints WHERE session_id = ? LIMIT 1", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_active_sessions(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE status = 'active' ORDER BY start_time DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def close_all_active_sessions(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status = 'closed', end_time = ? WHERE status = 'active'", (datetime.now(),))
        cursor.execute("DELETE FROM live_typing")
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions (active + closed) for historical analytics."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions ORDER BY start_time DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── HASSH Fingerprinting ───

    def record_hassh(self, session_id: str, client_ip: str, hassh: str, username: str = "user"):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO hassh_fingerprints (session_id, client_ip, hassh, username, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, client_ip, hassh, username, datetime.now())
        )
        conn.commit()
        conn.close()

    def get_hassh_sessions(self, hassh: str) -> List[Dict]:
        """Get all sessions with a given HASSH (cross-IP correlation)."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hassh_fingerprints WHERE hassh = ? ORDER BY timestamp DESC", (hassh,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_session_hassh(self, session_id: str) -> str:
        """Get HASSH for a specific session."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT hassh FROM hassh_fingerprints WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_hassh(self) -> List[Dict]:
        """Get all HASSH fingerprints."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hassh_fingerprints ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── RSA Alerts ───

    def record_rsa_alert(self, client_ip: str, alert_type: str, severity: str,
                          similarity_score: int, details: dict):
        import json
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rsa_alerts (client_ip, alert_type, severity, similarity_score, details, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (client_ip, alert_type, severity, similarity_score, json.dumps(details), datetime.now())
        )
        conn.commit()
        conn.close()

    def get_rsa_alerts(self) -> List[Dict]:
        """Get all unresolved RSA Alerts."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsa_alerts WHERE resolved = 0 ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_rsa_alerts(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rsa_alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_rsa_alerts(self):
        """Clear all RSA alerts and associated cyber actions."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cyber_actions")
        cursor.execute("DELETE FROM rsa_alerts")
        conn.commit()
        conn.close()

    def record_cyber_action(self, alert_id: int, action: str, operator: str = "system"):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cyber_actions (alert_id, action, operator, timestamp) VALUES (?, ?, ?, ?)",
            (alert_id, action, operator, datetime.now())
        )
        # Mark alert as resolved if action is Block or Dismiss
        if action in ("Block", "Dismiss"):
            cursor.execute("UPDATE rsa_alerts SET resolved = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()

    def get_cyber_actions(self, alert_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cyber_actions WHERE alert_id = ? ORDER BY timestamp DESC", (alert_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── Live typing (shared, for dashboard) ───

    def upsert_live_typing(self, session_id: str, buffer: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO live_typing (session_id, buffer, updated_at) VALUES (?, ?, ?)",
                        (session_id, buffer, datetime.now()))
        conn.commit()
        conn.close()

    def clear_live_typing(self, session_id: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM live_typing WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def get_all_live_typing(self) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, buffer FROM live_typing")
        rows = cursor.fetchall()
        conn.close()
        return {row['session_id']: row['buffer'] for row in rows}


class SessionDatabase:
    """
    Per-session database — stores all data for ONE attacker session.
    Completely isolated from other sessions (separate .db file).
    """

    def __init__(self, session_id: str, db_dir: str = "logs/sessions"):
        self.session_id = session_id
        os.makedirs(db_dir, exist_ok=True)
        self.db_file = os.path.join(db_dir, f"{session_id}.db")
        self._init_tables()

    def _init_tables(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            command TEXT,
            response TEXT,
            execution_time_ms INTEGER
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            intent_type TEXT,
            confidence REAL,
            trigger_command TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS canary_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT,
            intent TEXT,
            planted_at TIMESTAMP,
            triggered INTEGER DEFAULT 0,
            triggered_at TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS threat_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            event_type TEXT,
            severity TEXT,
            data TEXT
        )
        """)

        conn.commit()
        conn.close()

    # ─── Commands ───

    def log_command(self, command: str, response: str, execution_time_ms: int = 0):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO commands (timestamp, command, response, execution_time_ms) VALUES (?, ?, ?, ?)",
                        (datetime.now(), command, response, execution_time_ms))
        conn.commit()
        conn.close()

    def get_commands(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commands ORDER BY timestamp")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── Intents ───

    def log_intent(self, intent_type: str, confidence: float, trigger_command: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO intents (timestamp, intent_type, confidence, trigger_command) VALUES (?, ?, ?, ?)",
                        (datetime.now(), intent_type, confidence, trigger_command))
        conn.commit()
        conn.close()

    def get_intents(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM intents ORDER BY timestamp")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── Canary Files ───

    def register_canary(self, filepath: str, intent: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO canary_files (filepath, intent, planted_at) VALUES (?, ?, ?)",
                        (filepath, intent, datetime.now()))
        conn.commit()
        conn.close()

    def trigger_canary(self, filepath: str) -> Optional[Dict]:
        """Check if a file is a canary and trigger it. Returns canary info or None."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM canary_files WHERE filepath = ? AND triggered = 0", (filepath,))
        row = cursor.fetchone()
        if row:
            canary = dict(row)
            cursor.execute("UPDATE canary_files SET triggered = 1, triggered_at = ? WHERE id = ?",
                            (datetime.now(), canary['id']))
            conn.commit()
            conn.close()
            return canary
        conn.close()
        return None

    def get_canary_events(self) -> List[Dict]:
        """Get all triggered canaries."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM canary_files WHERE triggered = 1 ORDER BY triggered_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_canaries(self) -> List[Dict]:
        """Get all canaries (planted + triggered)."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM canary_files ORDER BY planted_at")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    # ─── Threat Events ───

    def log_threat_event(self, event_type: str, severity: str, data: Dict):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO threat_events (timestamp, event_type, severity, data) VALUES (?, ?, ?, ?)",
                        (datetime.now(), event_type, severity, json.dumps(data)))
        conn.commit()
        conn.close()

    def get_threat_events(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM threat_events ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def clear_threat_events(self, event_type: str = None):
        """Clear threat events. If event_type given, only clear that type."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        if event_type:
            cursor.execute("DELETE FROM threat_events WHERE event_type = ?", (event_type,))
        else:
            cursor.execute("DELETE FROM threat_events")
        conn.commit()
        conn.close()

    # ─── Report Data ───

    def generate_report_data(self) -> Dict:
        """Gather all session data for Groq report generation."""
        return {
            "session_id": self.session_id,
            "commands": self.get_commands(),
            "intents": self.get_intents(),
            "canaries": self.get_all_canaries(),
            "threat_events": self.get_threat_events()
        }
