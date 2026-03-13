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

        # General Intelligence Agency — session watchdog
        self.gia = GeneralIntelligenceAgency(self.active_sessions, self.database)
        self.gia.start()
        logger.info("✓ GIA (General Intelligence Agency) initialized")

        # SSH server
        self.ssh_server = SSHServerSocket(
            host="0.0.0.0",
            port=self.port,
            command_handler=self._handle_command,
            live_feed_callback=self._update_live_typing
        )

        logger.info(f"✓ GhostNet initialized on port {self.port}")

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
