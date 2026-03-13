"""
GhostNet: Autonomous AI Cyber-Deception System
Main entry point for the honeypot system
"""

import os
import logging
import sys
import time
from dotenv import load_dotenv
from datetime import datetime

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
from state_manager.database import GhostNetDatabase
from state_manager.file_system import VirtualFileSystem


class GhostNetHoneypot:
    """
    Main orchestrator for the GhostNet honeypot system.
    Coordinates SSH listener, command handler, AI agents, and state management.
    """

    def __init__(self, port: int = 2222):
        """Initialize GhostNet system"""
        logger.info("="*60)
        logger.info("Initializing GhostNet - Autonomous Cyber-Deception System")
        logger.info("="*60)
        
        self.port = port
        self.database = GhostNetDatabase()
        
        # AI agents for intelligence (Groq API)
        try:
            self.orchestrator = Orchestrator()
            self.profiler = Profiler()
            logger.info("✓ AI agents initialized successfully (Groq)")
        except Exception as e:
            logger.warning(f"⚠ AI agents not available (Groq API issue): {e}")
            logger.warning("  Honeypot will still work — just without intent analysis/profiling")
            self.orchestrator = None
            self.profiler = None
        
        # Session tracking: each session gets its own filesystem + command handler
        self.active_sessions = {}
        
        # Create SSH server
        self.ssh_server = SSHServerSocket(
            host="0.0.0.0",
            port=self.port,
            command_handler=self._handle_command,
            live_feed_callback=self._update_live_typing
        )
        
        logger.info(f"✓ GhostNet initialized and ready on port {self.port}")

    def _update_live_typing(self, session_id: str, buffer: str):
        """Callback for live keystroke feed. Called on every keypress."""
        try:
            if buffer:
                self.database.upsert_live_typing(session_id, buffer)
            else:
                self.database.clear_live_typing(session_id)
        except Exception as e:
            logger.debug(f"Live typing update failed: {e}")

    def _get_session_handler(self, session_id: str, client_ip: str) -> CommandHandler:
        """Get or create a CommandHandler for a session."""
        if session_id not in self.active_sessions:
            # Create a fresh filesystem for this session
            fs = VirtualFileSystem()
            handler = CommandHandler(fs)
            
            self.database.create_session(session_id, client_ip, "user")
            self.active_sessions[session_id] = {
                "commands": [],
                "client_ip": client_ip,
                "handler": handler,
                "filesystem": fs
            }
            logger.info(f"[{session_id}] New session — fresh filesystem created")
        
        return self.active_sessions[session_id]["handler"]

    def _handle_command(self, command: str, session_id: str, client_ip: str) -> str:
        """
        Main command handler.
        
        Flow:
        1. Get/create per-session CommandHandler
        2. Execute command deterministically
        3. Orchestrator analyzes intent (async, non-blocking for response)
        4. Database logs everything
        5. Profiler updates attacker profile periodically
        """
        
        try:
            handler = self._get_session_handler(session_id, client_ip)
            
            # Add to command history
            self.active_sessions[session_id]["commands"].append(command)
            
            # Special commands
            if command.lower() in ["exit", "quit"]:
                self.database.close_session(session_id)
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                return ""
            
            # Start timing
            start_time = time.time()
            
            # Execute command deterministically (no LLM!)
            response = handler.execute(command)
            
            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log command to database
            self.database.log_command(
                session_id,
                command,
                response,
                execution_time
            )
            
            logger.info(f"[{session_id}] Command: {command[:50]} ({execution_time}ms)")
            
            # Analyze intent with Orchestrator (if available)
            if self.orchestrator:
                try:
                    intent = self.orchestrator.analyze_intent(
                        command,
                        self.active_sessions[session_id]["commands"]
                    )
                    
                    # Log threat event if necessary
                    if intent.get("threat_level") in ["high", "critical"]:
                        self.database.log_threat_event(
                            session_id,
                            intent["intent"],
                            intent,
                            intent["threat_level"]
                        )
                        logger.warning(f"⚠️ [{session_id}] {intent['threat_level'].upper()}: {intent['intent']}")
                except Exception as e:
                    logger.debug(f"Intent analysis skipped: {e}")
            
            # Periodically profile attacker (every 5 commands)
            cmd_count = len(self.active_sessions[session_id]["commands"])
            if self.profiler and cmd_count % 5 == 0:
                try:
                    profile = self.profiler.profile_attacker(
                        self.active_sessions[session_id]["commands"]
                    )
                    logger.info(f"[{session_id}] Attacker Profile: {profile.get('skill_level', 'unknown')} level")
                except Exception as e:
                    logger.debug(f"Profiling skipped: {e}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling command '{command}': {e}")
            return f"Error: {str(e)}"

    def start(self):
        """Start the GhostNet honeypot"""
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
        """Gracefully shutdown GhostNet"""
        logger.info("Shutting down GhostNet...")
        self.ssh_server.stop()
        
        # Close all active sessions
        for session_id in list(self.active_sessions.keys()):
            self.database.close_session(session_id)
        
        logger.info("✓ GhostNet shutdown complete")


def main():
    """Main entry point"""
    
    # Groq API key is optional now (honeypot works without it, just no AI analysis)
    if not os.getenv("GROQ_API_KEY"):
        logger.warning("⚠ GROQ_API_KEY not found in .env — AI intent analysis will be disabled")
        logger.warning("  The honeypot shell will still work perfectly!")
    
    # Get port from environment or use default
    port = int(os.getenv("SSH_PORT", "2222"))
    
    # Create and start honeypot
    honeypot = GhostNetHoneypot(port=port)
    honeypot.start()


if __name__ == "__main__":
    main()
