"""
AeroGhost General Intelligence Agency (GIA) — Session Watchdog.

Monitors all active sessions for anomalies:
  - Bot detection (command speed analysis)
  - Suspicion scoring (ls-after-ls patterns, timestamp checking)
  - Breadcrumb realism validation (file timestamps)
  - Session integrity checks (DB ↔ memory sync)
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class GeneralIntelligenceAgency:
    """
    Background watchdog that monitors honeypot sessions for anomalies.
    Runs in a daemon thread, checking every 5 seconds.
    """

    # Thresholds
    BOT_SPEED_THRESHOLD_MS = 200      # Commands < 200ms apart = bot
    BOT_BURST_COUNT = 5               # Need 5 fast commands in a row to trigger
    SUSPICION_LS_REPEAT = 3           # 3+ ls commands in last 5 = suspicious
    CHECK_INTERVAL_SECONDS = 5        # How often to run checks

    def __init__(self, active_sessions: dict, database=None):
        """
        Args:
            active_sessions: Reference to GhostNetHoneypot.active_sessions dict
            database: Reference to GhostNetDatabase (session index)
        """
        self.active_sessions = active_sessions
        self.database = database
        self._running = False
        self._thread = None

        # Per-session tracking (session_id -> data)
        self._command_times: Dict[str, List[float]] = defaultdict(list)
        self._alerts_fired: Dict[str, set] = defaultdict(set)  # avoid duplicate alerts
        self._session_scores: Dict[str, dict] = defaultdict(
            lambda: {"bot_score": 0.0, "suspicion_score": 0.0, "realism_score": 1.0}
        )

    def start(self):
        """Start the GIA background monitoring thread."""
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("🕵️ GIA (General Intelligence Agency) started — monitoring sessions")

    def stop(self):
        """Stop the GIA monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def record_command_time(self, session_id: str):
        """Call from _handle_command to record exact timestamp of each command."""
        self._command_times[session_id].append(time.time())

    def get_session_scores(self, session_id: str) -> dict:
        """Get the current GIA scores for a session."""
        return dict(self._session_scores[session_id])

    def _monitor_loop(self):
        """Main monitoring loop — runs every CHECK_INTERVAL_SECONDS."""
        while self._running:
            try:
                self._run_checks()
            except Exception as e:
                logger.debug(f"GIA monitor error: {e}")
            time.sleep(self.CHECK_INTERVAL_SECONDS)

    def _run_checks(self):
        """Run all checks across all active sessions."""
        for session_id, session in list(self.active_sessions.items()):
            session_db = session.get("session_db")
            if not session_db:
                continue

            # 1. Bot detection — command speed analysis
            self._check_bot_speed(session_id, session_db)

            # 2. Suspicion scoring — ls-after-ls, stat, find -newer
            self._check_suspicion_patterns(session_id, session, session_db)

            # 3. Breadcrumb realism — validate planted file timestamps
            self._check_breadcrumb_realism(session_id, session, session_db)

        # 4. Session integrity — DB vs memory sync
        if self.database:
            self._check_session_integrity()

    # ─── Check 1: Bot Speed Detection ───

    def _check_bot_speed(self, session_id: str, session_db):
        """Detect automated scanners by checking command timing."""
        times = self._command_times.get(session_id, [])
        if len(times) < self.BOT_BURST_COUNT + 1:
            return

        # Check the last N command intervals
        recent = times[-(self.BOT_BURST_COUNT + 1):]
        intervals_ms = [(recent[i+1] - recent[i]) * 1000 for i in range(len(recent) - 1)]

        fast_count = sum(1 for ms in intervals_ms if ms < self.BOT_SPEED_THRESHOLD_MS)
        bot_score = fast_count / len(intervals_ms)

        self._session_scores[session_id]["bot_score"] = bot_score

        if bot_score >= 0.8 and "bot_detected" not in self._alerts_fired[session_id]:
            self._alerts_fired[session_id].add("bot_detected")
            avg_ms = sum(intervals_ms) / len(intervals_ms)
            session_db.log_threat_event(
                "gia_warning",
                "high",
                {
                    "check": "bot_detected",
                    "message": f"Automated scanner detected — avg {avg_ms:.0f}ms between commands",
                    "bot_score": round(bot_score, 2),
                    "avg_interval_ms": round(avg_ms, 1)
                }
            )
            logger.warning(f"🤖 GIA [{session_id[:8]}] Bot detected! Avg interval: {avg_ms:.0f}ms")

    # ─── Check 2: Suspicion Patterns ───

    def _check_suspicion_patterns(self, session_id: str, session: dict, session_db):
        """Detect suspicious behavior patterns."""
        commands = session.get("commands", [])
        if len(commands) < 3:
            return

        recent = commands[-8:]
        suspicion = 0.0

        # Pattern: Repeated ls (checking for new files)
        ls_count = sum(1 for c in recent if c.strip() in ("ls", "ls -la", "ls -al", "ls -l", "dir"))
        if ls_count >= self.SUSPICION_LS_REPEAT:
            suspicion += 0.4
            if "ls_spam" not in self._alerts_fired[session_id]:
                self._alerts_fired[session_id].add("ls_spam")
                session_db.log_threat_event(
                    "gia_warning",
                    "medium",
                    {
                        "check": "suspicious_behavior",
                        "message": f"Repeated ls commands ({ls_count}x in last 8) — attacker may be checking for honeypot file changes",
                        "pattern": "ls_spam",
                        "count": ls_count
                    }
                )
                logger.info(f"🔍 GIA [{session_id[:8]}] Suspicious: {ls_count}x ls in last 8 commands")

        # Pattern: Checking file timestamps (stat, find -newer)
        timestamp_cmds = sum(1 for c in recent if any(p in c for p in ["stat ", "find / -newer", "find . -newer", "ls -lt"]))
        if timestamp_cmds >= 2:
            suspicion += 0.3
            if "timestamp_check" not in self._alerts_fired[session_id]:
                self._alerts_fired[session_id].add("timestamp_check")
                session_db.log_threat_event(
                    "gia_warning",
                    "medium",
                    {
                        "check": "suspicious_behavior",
                        "message": "Attacker checking file timestamps — may suspect honeypot",
                        "pattern": "timestamp_checking",
                        "count": timestamp_cmds
                    }
                )

        # Pattern: Rapid exploration (cd + ls chains)
        cd_ls_pairs = 0
        for i in range(len(recent) - 1):
            if recent[i].startswith("cd ") and recent[i+1].strip().startswith("ls"):
                cd_ls_pairs += 1
        if cd_ls_pairs >= 3:
            suspicion += 0.2

        # Pattern: Trying to escape (multiple exit/logout, Ctrl+C patterns)
        escape_cmds = sum(1 for c in recent if c.strip() in ("exit", "logout", "quit", "bye"))
        if escape_cmds >= 2:
            suspicion += 0.1

        self._session_scores[session_id]["suspicion_score"] = min(suspicion, 1.0)

    # ─── Check 3: Breadcrumb Realism ───

    def _check_breadcrumb_realism(self, session_id: str, session: dict, session_db):
        """Validate that planted breadcrumbs have realistic timestamps."""
        fs = session.get("filesystem")
        if not fs:
            return

        canaries = session_db.get_all_canaries()
        now = datetime.now()
        issues = []

        for canary in canaries:
            filepath = canary.get("filepath", "")
            node = fs.resolve_path(filepath)
            if node and node.is_file():
                # Check: file modified time should NOT be very recent (within last 60s)
                age = now - node.modified
                if age.total_seconds() < 60:
                    issues.append(filepath)

        if issues and "realism_fail" not in self._alerts_fired[session_id]:
            self._alerts_fired[session_id].add("realism_fail")
            session_db.log_threat_event(
                "gia_warning",
                "low",
                {
                    "check": "realism_check_failed",
                    "message": f"Breadcrumb file(s) have too-recent timestamps: {issues}",
                    "files": issues
                }
            )
            logger.info(f"⏰ GIA [{session_id[:8]}] Realism check: {len(issues)} file(s) with too-recent timestamps")

        # Update realism score
        if canaries:
            realism = 1.0 - (len(issues) / max(len(canaries), 1))
            self._session_scores[session_id]["realism_score"] = max(realism, 0.0)

    # ─── Check 4: Session Integrity ───

    def _check_session_integrity(self):
        """Verify active_sessions dict is in sync with the database."""
        try:
            db_sessions = self.database.get_active_sessions()
            db_sids = {s['session_id'] for s in db_sessions}
            memory_sids = set(self.active_sessions.keys())

            # Sessions in DB but not in memory (zombie sessions)
            zombies = db_sids - memory_sids
            if zombies:
                for sid in zombies:
                    self.database.close_session(sid)
                logger.info(f"🧹 GIA cleaned {len(zombies)} zombie session(s) from DB")

        except Exception as e:
            logger.debug(f"GIA session integrity check failed: {e}")

    def cleanup_session(self, session_id: str):
        """Clean up GIA tracking data when a session ends."""
        self._command_times.pop(session_id, None)
        self._alerts_fired.pop(session_id, None)
        self._session_scores.pop(session_id, None)
