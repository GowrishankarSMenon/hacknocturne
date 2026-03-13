import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any


class GhostNetDatabase:
    """
    SQLite database for storing attack logs and intelligence data.
    """

    def __init__(self, db_file: str = "logs/ghostnet.db"):
        self.db_file = db_file
        self._init_database()

    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            client_ip TEXT,
            username TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT
        )
        """)

        # Commands table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP,
            command TEXT,
            response TEXT,
            execution_time_ms INTEGER,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        """)

        # Threat intelligence table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS threat_intel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp TIMESTAMP,
            event_type TEXT,
            data JSON,
            severity TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        """)

        # File uploads table (for malware tracking)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            filename TEXT,
            file_path TEXT,
            timestamp TIMESTAMP,
            file_hash TEXT,
            analysis JSON,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
        """)

        # Live typing table (real-time keystroke feed)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS live_typing (
            session_id TEXT PRIMARY KEY,
            buffer TEXT,
            updated_at TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()

    def create_session(self, session_id: str, client_ip: str, username: str):
        """Create a new session record"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO sessions (session_id, client_ip, username, start_time, status)
        VALUES (?, ?, ?, ?, ?)
        """, (session_id, client_ip, username, datetime.now(), "active"))
        
        conn.commit()
        conn.close()

    def log_command(self, session_id: str, command: str, response: str, execution_time_ms: int = 0):
        """Log a command execution"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO commands (session_id, timestamp, command, response, execution_time_ms)
        VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), command, response, execution_time_ms))
        
        conn.commit()
        conn.close()

    def log_threat_event(self, session_id: str, event_type: str, data: Dict, severity: str = "info"):
        """Log a threat intelligence event"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO threat_intel (session_id, timestamp, event_type, data, severity)
        VALUES (?, ?, ?, ?, ?)
        """, (session_id, datetime.now(), event_type, json.dumps(data), severity))
        
        conn.commit()
        conn.close()

    def get_session_commands(self, session_id: str) -> List[Dict]:
        """Get all commands for a session"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM commands WHERE session_id = ? ORDER BY timestamp
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def get_active_sessions(self) -> List[Dict]:
        """Get all active sessions"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM sessions WHERE status = 'active' ORDER BY start_time DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def close_session(self, session_id: str):
        """Mark session as closed"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE sessions SET status = 'closed', end_time = ? WHERE session_id = ?
        """, (datetime.now(), session_id))
        
        conn.commit()
        conn.close()

    def close_all_active_sessions(self):
        """Mark ALL active sessions as closed. Used on startup to clean stale sessions."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE sessions SET status = 'closed', end_time = ? WHERE status = 'active'
        """, (datetime.now(),))
        
        # Also clear all live typing buffers
        cursor.execute("DELETE FROM live_typing")
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected

    def upsert_live_typing(self, session_id: str, buffer: str):
        """Update live typing buffer for a session (called on every keystroke)."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO live_typing (session_id, buffer, updated_at)
        VALUES (?, ?, ?)
        """, (session_id, buffer, datetime.now()))
        conn.commit()
        conn.close()

    def clear_live_typing(self, session_id: str):
        """Clear live typing buffer (called after Enter is pressed)."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM live_typing WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

    def get_all_live_typing(self) -> Dict[str, str]:
        """Get all active typing buffers. Returns {session_id: buffer}."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, buffer FROM live_typing")
        rows = cursor.fetchall()
        conn.close()
        return {row['session_id']: row['buffer'] for row in rows}


# Test
if __name__ == "__main__":
    db = GhostNetDatabase()
    
    # Create test session
    db.create_session("test_session_001", "192.168.1.100", "attacker")
    
    # Log test command
    db.log_command("test_session_001", "whoami", "root", 50)
    db.log_command("test_session_001", "ls -la", "total 24\ndrwxr-xr-x...", 100)
    
    # Log threat event
    db.log_threat_event("test_session_001", "privilege_escalation", {"method": "sudo"}, "high")
    
    # Query data
    commands = db.get_session_commands("test_session_001")
    print(f"Logged {len(commands)} commands")
    
    sessions = db.get_active_sessions()
    print(f"Active sessions: {len(sessions)}")
