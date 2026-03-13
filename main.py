"""
GhostNet: Autonomous AI Cyber-Deception System
Main entry point for the honeypot system
"""

import os
import logging
import sys
import time
import random
import threading
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ghostnet.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import components
from ssh_listener.server import SSHServerSocket
from agents.os_simulator import Orchestrator, Profiler
from agents.command_handler import CommandHandler
from agents.breadcrumbs import BreadcrumbAgent
from agents.timing_analyzer import TimingAnalyzer
from agents.hassh_fingerprinter import HASSHFingerprinter
from agents.rsa_detector import RSADetector
from state_manager.database import GhostNetDatabase, SessionDatabase
from state_manager.file_system import VirtualFileSystem, FSNode
from agents.intelligence_agency import GeneralIntelligenceAgency


class GhostNetHoneypot:
    """
    Main orchestrator for the GhostNet honeypot system.
    Coordinates SSH listener, command handler, AI agents, and state management.
    """

    def __init__(self, port: int = 2222):
        logger.info("=" * 60)
        logger.info("Initializing GhostNet - Autonomous Cyber-Deception System")
        logger.info("=" * 60)

        self.port = port
        self.database = GhostNetDatabase()  # Session index only

        # AI agents (Groq — optional)
        try:
            self.orchestrator = Orchestrator()
            self.profiler = Profiler()
            logger.info("✓ AI agents initialized (Groq) — Orchestrator + Profiler")
        except Exception as e:
            logger.warning(f"⚠ AI agents not available: {e}")
            self.orchestrator = None
            self.profiler = None

        # Breadcrumb agent (Groq — optional, has fallback templates)
        try:
            self.breadcrumb_agent = BreadcrumbAgent()
            logger.info("✓ Breadcrumb Agent initialized")
        except Exception as e:
            logger.warning(f"⚠ Breadcrumb Agent not available: {e}")
            self.breadcrumb_agent = None

        # Session tracking
        self.active_sessions = {}

        # Timing analyzer for bot/human detection
        self.timing_analyzer = TimingAnalyzer()
        logger.info("Timing Analyzer initialized")

        # HASSH Fingerprinter
        self.hassh_fingerprinter = HASSHFingerprinter(self.database)
        logger.info("✓ HASSH Fingerprinter initialized")

        # RSA Detector
        self.rsa_detector = RSADetector(self.database)
        logger.info("✓ RSA Detector initialized")

        # General Intelligence Agency — session watchdog
        self.gia = GeneralIntelligenceAgency(self.active_sessions, self.database)
        self.gia.start()
        logger.info("GIA (General Intelligence Agency) initialized")

        # SSH server
        self.ssh_server = SSHServerSocket(
            host="0.0.0.0",
            port=self.port,
            command_handler=self._handle_command,
            live_feed_callback=self._update_live_typing,
            fingerprint_callback=self._on_fingerprint,
            keystroke_callback=self._on_keystroke,
            prompt_callback=self._get_prompt,
            hassh_callback=self._on_hassh_captured,
            connection_callback=self._on_connection,
        )

        # Buffer for fingerprint data (arrives before session DB row exists)
        self._pending_fingerprints = {}

        logger.info(f"AeroGhost initialized on port {self.port}")

    def _on_fingerprint(self, session_id: str, client_version: str, password: str, client_port: int):
        """Buffer fingerprint data — will be applied when session is created."""
        self._pending_fingerprints[session_id] = {
            'client_software': client_version,
            'password_used': password,
            'client_port': client_port
        }
        logger.info(f"[{session_id}] Fingerprint buffered: {client_version} | Port: {client_port}")

    def _on_keystroke(self, session_id: str):
        """Callback for every single keypress — feeds the timing analyzer."""
        self.timing_analyzer.record_keystroke(session_id)

    def _get_prompt(self, session_id: str) -> str:
        """Return the current prompt based on session state."""
        session = self.active_sessions.get(session_id)
        if session:
            handler = session.get('handler')
            if handler:
                if handler._in_mysql:
                    return "mysql> "
                if handler._is_root:
                    return "root@aeroghost:~# "
        return "user@aeroghost:~$ "

    def _on_hassh_captured(self, transport, session_id: str, client_ip: str, username: str):
        """Callback: compute and store HASSH fingerprint after SSH handshake."""
        hassh = self.hassh_fingerprinter.compute_hassh(transport)
        if hassh:
            self.hassh_fingerprinter.record(session_id, client_ip, hassh, username)

            # Cross-IP correlation check
            correlated = self.hassh_fingerprinter.correlate(hassh)
            ips = list(set(s['client_ip'] for s in correlated))
            if len(ips) > 1:
                logger.warning(f"🚨 HASSH CROSS-IP: {hassh[:12]}... seen from {len(ips)} IPs: {ips}")

            # Identify known tool
            tool = self.hassh_fingerprinter.identify_tool(hassh)
            if tool:
                logger.info(f"🔧 Known tool identified: {tool} (HASSH: {hassh[:12]}...)")

    def _on_connection(self, client_ip: str):
        """Callback: record connection for RSA analysis."""
        alert = self.rsa_detector.record_connection(client_ip)
        if alert:
            logger.warning(
                f"🔥 Random Segment Assessment ALERT [{alert['type']}] from {client_ip} — "
                f"Severity: {alert['severity']} | Score: {alert['similarity_score']}/100"
            )

    def _update_live_typing(self, session_id: str, buffer: str):
        """Callback for live keystroke feed."""
        try:
            if buffer:
                self.database.upsert_live_typing(session_id, buffer)
            else:
                self.database.clear_live_typing(session_id)
        except Exception as e:
            logger.debug(f"Live typing update failed: {e}")

    def _get_session(self, session_id: str, client_ip: str):
        """Get or create a full session (filesystem + handler + session DB)."""
        if session_id not in self.active_sessions:
            # Per-session filesystem
            fs = VirtualFileSystem()

            # Per-session database (isolated SQLite file)
            session_db = SessionDatabase(session_id)

            # Create canary check/trigger callbacks bound to this session
            def canary_check(filepath):
                return session_db.trigger_canary(filepath)

            def canary_trigger(canary_info):
                self._on_canary_triggered(session_id, canary_info)

            # Command handler with canary callbacks
            handler = CommandHandler(fs, canary_check_fn=canary_check, canary_trigger_fn=canary_trigger)

            # Register session in main DB
            self.database.create_session(session_id, client_ip, "user")

            self.active_sessions[session_id] = {
                "commands": [],
                "client_ip": client_ip,
                "handler": handler,
                "filesystem": fs,
                "session_db": session_db
            }
            logger.info(f"[{session_id}] New session — isolated DB + filesystem created")

            # Apply any buffered fingerprint data now that session row exists
            if session_id in self._pending_fingerprints:
                fp = self._pending_fingerprints.pop(session_id)
                try:
                    self.database.update_session_fingerprint(
                        session_id,
                        client_software=fp.get('client_software'),
                        password_used=fp.get('password_used'),
                        client_port=fp.get('client_port')
                    )
                    logger.info(f"[{session_id}] Fingerprint applied from buffer")
                except Exception as e:
                    logger.debug(f"Fingerprint apply failed: {e}")

        return self.active_sessions[session_id]

    def _on_canary_triggered(self, session_id: str, canary_info: dict):
        """Called when attacker opens a canary file — fires Critical Threat Event."""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        filepath = canary_info.get('filepath', 'unknown')
        intent = canary_info.get('intent', 'unknown')

        # Log to per-session DB
        session["session_db"].log_threat_event(
            "canary_accessed",
            "critical",
            {"filepath": filepath, "intent": intent, "canary_id": canary_info.get('id')}
        )

        logger.warning(f"🚨 CRITICAL [{session_id}] — Canary triggered: '{filepath}' | Intent: {intent}")

    def _handle_command(self, command: str, session_id: str, client_ip: str) -> str:
        """Main command handler."""
        # Handle Ctrl+C signal — resets MySQL session and root state
        if command == "__ctrl_c__":
            session = self.active_sessions.get(session_id)
            if session:
                handler = session.get('handler')
                if handler:
                    handler._in_mysql = False
            return ""

        try:
            session = self._get_session(session_id, client_ip)
            handler = session["handler"]
            session_db = session["session_db"]

            # Add to command history
            session["commands"].append(command)

            # Handle exit
            if command.lower() in ["exit", "quit"]:
                self.database.close_session(session_id)
                self.database.clear_live_typing(session_id)
                self.gia.cleanup_session(session_id)
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                return ""

            # Execute command
            start_time = time.time()
            response = handler.execute(command)
            execution_time = int((time.time() - start_time) * 1000)

            # Log to per-session DB
            session_db.log_command(command, response, execution_time)

            # GIA: record command timing for bot detection
            self.gia.record_command_time(session_id)

            # Timing analyzer: check for reconnaissance burst
            is_recon_burst = self.timing_analyzer.record_command_for_recon(session_id, command)
            if is_recon_burst:
                session_db.log_threat_event(
                    "reconnaissance_burst",
                    "high",
                    {"message": f"Recon burst detected: {command}", "check": "reconnaissance_burst"}
                )
                logger.warning(f"[{session_id}] RECON BURST detected after: {command}")

            # Timing analyzer: classify bot/human periodically
            classification, avg_ipd = self.timing_analyzer.classify(session_id)
            if classification in ("bot", "suspicious"):
                session_db.log_threat_event(
                    "gia_warning",
                    "high" if classification == "bot" else "medium",
                    {"check": "bot_detected", "message": f"Typing classified as {classification} (avg IPD: {avg_ipd}ms)"}
                )

            logger.info(f"[{session_id}] Command: {command[:50]} ({execution_time}ms)")

            # Breadcrumb pipeline (background thread — non-blocking)
            # NOTE: increment_cmd moved INSIDE the pipeline thread (Bug 2 fix)
            if self.breadcrumb_agent:
                threading.Thread(
                    target=self._breadcrumb_pipeline,
                    args=(command, session_id),
                    daemon=True
                ).start()

            return response

        except Exception as e:
            logger.error(f"Error handling command '{command}': {e}")
            return f"Error: {str(e)}"

    def _breadcrumb_pipeline(self, command: str, session_id: str):
        """
        Background thread: detect intent → generate breadcrumb → plant it.
        Runs asynchronously so it never slows down the attacker's terminal.
        """
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return

            session_db = session["session_db"]
            fs = session["filesystem"]
            history = session["commands"]

            # Increment command counter INSIDE the background thread (Bug 2 fix)
            self.breadcrumb_agent.increment_cmd(session_id)

            # 1. Detect intent
            intent, confidence = self.breadcrumb_agent.detect_intent(command, history)

            # Log intent (even if not planting)
            if intent != "none":
                session_db.log_intent(intent, confidence, command)
                logger.info(f"[{session_id}] Intent detected: {intent} (confidence: {confidence:.2f})")

            # 2. Check rate limit
            if intent == "none" or not self.breadcrumb_agent.should_plant(session_id):
                return

            # 3. Generate breadcrumb
            filename, content = self.breadcrumb_agent.generate_breadcrumb(intent, fs.get_pwd())
            if not filename or not content:
                return

            # 4. Plausibility check: only plant in dirs that have other files
            visible_files = [c for c in fs.cwd.children.values() if not c.name.startswith(".")]
            if len(visible_files) < 1:
                logger.debug(f"[{session_id}] Skipping breadcrumb — empty directory")
                return

            # 5. Delay before planting (Bug 2 fix)
            # Random delay so file doesn't appear immediately after attacker's command
            delay = random.uniform(3, 10)
            time.sleep(delay)

            # Re-check session still exists after delay
            if session_id not in self.active_sessions:
                return

            # 6. Plant in filesystem
            existing = fs.cwd.get_child(filename)
            if existing:
                return  # Don't overwrite existing files

            breadcrumb_node = FSNode(
                filename, "file",
                owner="user", group="user",
                permissions="rw-r--r--",
                content=content,
                size=len(content)
            )
            # Set REALISTIC timestamp — file should look old, not just-created
            breadcrumb_node.modified = datetime.now() - timedelta(
                days=random.randint(5, 60),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            fs.cwd.add_child(breadcrumb_node)

            # 7. Register as canary in per-session DB
            canary_path = fs.get_pwd()
            if not canary_path.endswith("/"):
                canary_path += "/"
            canary_path += filename
            session_db.register_canary(canary_path, intent)

            # Record plant in rate limiter
            self.breadcrumb_agent.record_plant(session_id)

            logger.info(f"🎣 [{session_id}] Breadcrumb planted: '{filename}' at {fs.get_pwd()} (intent: {intent}) [delay: {delay:.1f}s]")

        except Exception as e:
            logger.debug(f"Breadcrumb pipeline error: {e}")

    def start(self):
        logger.info("")
        logger.info("🎭 GhostNet is now running...")
        logger.info(f"📡 SSH Server listening on 0.0.0.0:{self.port}")
        logger.info("🚀 Waiting for attackers...")
        logger.info("")
        logger.info("Dashboard: Run 'streamlit run dashboard/app.py' in another terminal")
        logger.info("")

        try:
            self.ssh_server.start()
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown signal received")
            self.shutdown()
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            self.shutdown()

    def shutdown(self):
        logger.info("Shutting down GhostNet...")
        self.gia.stop()
        self.ssh_server.stop()
        for session_id in list(self.active_sessions.keys()):
            self.database.close_session(session_id)
        logger.info("✓ GhostNet shutdown complete")


def main():
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("⚠ GROQ_API_KEY not found — AI features disabled, but honeypot shell works fine")

    port = int(os.getenv("SSH_PORT", "2222"))
    honeypot = GhostNetHoneypot(port=port)
    honeypot.start()


if __name__ == "__main__":
    main()
