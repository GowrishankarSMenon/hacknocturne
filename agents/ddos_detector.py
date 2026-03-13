"""
AeroGhost DDoS Detector.
Monitors connection rates per IP and flags potential
distributed denial-of-service or brute-force sweep attacks.
"""

import time
import logging
from collections import defaultdict
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class DDoSDetector:
    """
    Tracks connection rates and raises alerts for:
    - Too many connections from a single IP (brute force)
    - Rapid connection cycling (port scanner / DDoS)
    """

    # Configuration
    RATE_WINDOW_SEC = 60       # Rolling window in seconds
    MAX_CONNECTIONS = 10       # Max connections per IP per window before alert
    MAX_GLOBAL_CPS = 50        # Max global connections/sec before global alert

    def __init__(self, database):
        self.db = database
        self._connection_times: Dict[str, list] = defaultdict(list)
        self._global_times: list = []

    def record_connection(self, client_ip: str) -> Optional[Dict]:
        """
        Record an incoming connection attempt.
        Returns an alert dict if thresholds are exceeded, else None.
        """
        now = time.time()
        cutoff = now - self.RATE_WINDOW_SEC

        # Per-IP tracking
        self._connection_times[client_ip].append(now)
        self._connection_times[client_ip] = [
            t for t in self._connection_times[client_ip] if t > cutoff
        ]

        # Global rate tracking
        self._global_times.append(now)
        self._global_times = [t for t in self._global_times if t > cutoff]

        count = len(self._connection_times[client_ip])

        if count >= self.MAX_CONNECTIONS:
            alert = {
                "type": "brute_force_sweep",
                "severity": "critical" if count >= self.MAX_CONNECTIONS * 2 else "high",
                "client_ip": client_ip,
                "connection_count": count,
                "window_sec": self.RATE_WINDOW_SEC,
                "message": (
                    f"Brute-force sweep detected: {count} connections "
                    f"from {client_ip} in {self.RATE_WINDOW_SEC}s"
                ),
            }
            logger.warning(
                f"[DDOS] {alert['message']}"
            )
            return alert

        return None

    def get_top_sources(self, n: int = 10) -> list:
        """Return the top N most active source IPs."""
        now = time.time()
        cutoff = now - self.RATE_WINDOW_SEC
        rates = {
            ip: len([t for t in times if t > cutoff])
            for ip, times in self._connection_times.items()
        }
        return sorted(rates.items(), key=lambda x: x[1], reverse=True)[:n]
