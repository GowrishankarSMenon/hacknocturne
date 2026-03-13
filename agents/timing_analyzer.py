"""
AeroGhost Keystroke Timing Analyzer.
Detects whether an attacker is a human or an automated bot
based on inter-keypress delay (IPD) patterns.
"""

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class TimingAnalyzer:
    """Tracks keystroke timing per session and classifies human vs bot."""

    # Thresholds
    BOT_IPD_THRESHOLD_MS = 20       # Avg IPD < 20ms = definitely a bot
    FAST_TYPER_THRESHOLD_MS = 50    # 20-50ms = suspicious / fast script
    HUMAN_MIN_MS = 50              # Humans typically 50-300ms between keys
    HUMAN_MAX_MS = 1000            # Over 1s = pausing/thinking (still human)

    # Minimum keystrokes before classification
    MIN_SAMPLES = 10

    # Recon burst thresholds
    RECON_COMMANDS = {
        "uname", "whoami", "id", "hostname", "ifconfig", "ip",
        "cat /etc/os-release", "env", "printenv", "ps", "netstat",
        "ss", "lsb_release", "arch", "nproc", "free", "df",
        "cat /proc/version", "cat /proc/cpuinfo",
    }
    RECON_BURST_THRESHOLD = 3      # 3+ recon commands = burst
    RECON_BURST_WINDOW_SEC = 30    # Within 30 seconds

    def __init__(self):
        # Per-session data
        self._keystroke_times: Dict[str, list] = defaultdict(list)
        self._recon_timestamps: Dict[str, list] = defaultdict(list)
        self._classifications: Dict[str, str] = {}

    def record_keystroke(self, session_id: str):
        """Record the timestamp of a single keypress."""
        self._keystroke_times[session_id].append(time.time())

    def classify(self, session_id: str) -> Tuple[str, float]:
        """
        Classify the session as 'human', 'bot', or 'suspicious'.
        Returns: (classification, avg_ipd_ms)
        """
        times = self._keystroke_times.get(session_id, [])
        if len(times) < self.MIN_SAMPLES:
            return ("unknown", 0.0)

        # Calculate inter-keypress delays
        delays = []
        for i in range(1, len(times)):
            delay_ms = (times[i] - times[i - 1]) * 1000
            # Filter out obvious pauses (> 2 seconds = thinking, not typing)
            if delay_ms < 2000:
                delays.append(delay_ms)

        if not delays:
            return ("unknown", 0.0)

        avg_ipd = sum(delays) / len(delays)

        if avg_ipd < self.BOT_IPD_THRESHOLD_MS:
            classification = "bot"
        elif avg_ipd < self.FAST_TYPER_THRESHOLD_MS:
            classification = "suspicious"
        else:
            classification = "human"

        self._classifications[session_id] = classification
        return (classification, round(avg_ipd, 2))

    def record_command_for_recon(self, session_id: str, command: str) -> bool:
        """
        Track if a command is a reconnaissance command.
        Returns True if a recon burst is detected.
        """
        cmd_base = command.strip().lower().split()[0] if command.strip() else ""
        full_cmd = command.strip().lower()

        is_recon = (
            cmd_base in self.RECON_COMMANDS or
            full_cmd in self.RECON_COMMANDS
        )

        if not is_recon:
            return False

        now = time.time()
        self._recon_timestamps[session_id].append(now)

        # Check for burst: N+ recon commands within the window
        cutoff = now - self.RECON_BURST_WINDOW_SEC
        recent = [t for t in self._recon_timestamps[session_id] if t > cutoff]
        self._recon_timestamps[session_id] = recent  # Prune old entries

        return len(recent) >= self.RECON_BURST_THRESHOLD

    def get_classification(self, session_id: str) -> str:
        """Get cached classification for a session."""
        return self._classifications.get(session_id, "unknown")

    def get_stats(self, session_id: str) -> Dict:
        """Get full timing stats for a session."""
        times = self._keystroke_times.get(session_id, [])
        classification, avg_ipd = self.classify(session_id)
        return {
            "total_keystrokes": len(times),
            "classification": classification,
            "avg_ipd_ms": avg_ipd,
            "recon_commands": len(self._recon_timestamps.get(session_id, [])),
        }
