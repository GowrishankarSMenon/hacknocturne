"""
RSA Detector — Two-Phase Rate Analysis with Similarity Scoring.

Phase 1: Burst Detection — N+ connections from same IP within W seconds
Phase 2: Slow-Drip Detection — gap check + rolling counter over longer window
Similarity Check — HASSH match (50%) + timing regularity (30%) + username repetition (20%)
"""

import time
import logging
import statistics
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RSADetector:
    """
    Two-phase Random Segment Assessment detection system with configurable thresholds.
    Records every incoming connection and checks for burst/slow-drip patterns.
    """

    def __init__(self, database, **kwargs):
        """
        Args:
            database: GhostNetDatabase instance (global)
            **kwargs: Override default thresholds
        """
        self.database = database

        # Phase 1: Burst detection thresholds
        self.BURST_N = kwargs.get('burst_n', 10)           # connections to trigger
        self.BURST_WINDOW = kwargs.get('burst_window', 30)  # seconds

        # Phase 2: Slow-drip thresholds
        self.DRIP_N = kwargs.get('drip_n', 20)              # connections to trigger
        self.DRIP_WINDOW = kwargs.get('drip_window', 300)    # seconds (5 min)
        self.TTA = kwargs.get('tta', 2.0)                    # threshold time attack (seconds)

        # Per-IP tracking: {ip: [{timestamp, hassh, username}, ...]}
        self._connections: Dict[str, List[Dict]] = defaultdict(list)

        # Alerts already fired: {ip: set(alert_type)}
        self._alerts_fired: Dict[str, set] = defaultdict(set)

    def record_connection(self, client_ip: str, hassh: str = None,
                          username: str = "user") -> Optional[Dict]:
        """
        Record an incoming connection and check for Random Segment Assessment patterns.

        Returns an alert dict if triggered, None otherwise.
        Alert dict: {type, severity, ip, count, window, similarity_score, details}
        """
        now = time.time()
        entry = {
            "timestamp": now,
            "hassh": hassh,
            "username": username,
            "datetime": datetime.now().isoformat()
        }
        self._connections[client_ip].append(entry)

        # Prune old entries (keep last DRIP_WINDOW + buffer)
        cutoff = now - self.DRIP_WINDOW - 60
        self._connections[client_ip] = [
            c for c in self._connections[client_ip] if c['timestamp'] > cutoff
        ]

        # Phase 1: Burst check
        alert = self._check_burst(client_ip, now)
        if alert:
            return alert

        # Phase 2: Slow-drip check
        alert = self._check_slow_drip(client_ip, now)
        if alert:
            return alert

        return None

    def _check_burst(self, client_ip: str, now: float) -> Optional[Dict]:
        """Phase 1: Check for burst flood."""
        connections = self._connections[client_ip]
        window_start = now - self.BURST_WINDOW
        recent = [c for c in connections if c['timestamp'] > window_start]

        if len(recent) >= self.BURST_N:
            alert_key = f"burst_{int(now // self.BURST_WINDOW)}"
            if alert_key in self._alerts_fired[client_ip]:
                return None  # already fired for this window

            self._alerts_fired[client_ip].add(alert_key)

            # Run similarity check
            sim_score = self._similarity_score(recent)
            severity = "CRITICAL" if sim_score >= 70 else "HIGH"

            alert = {
                "type": "burst_detected",
                "severity": severity,
                "ip": client_ip,
                "count": len(recent),
                "window": self.BURST_WINDOW,
                "similarity_score": sim_score,
                "details": {
                    "connections_in_window": len(recent),
                    "window_seconds": self.BURST_WINDOW,
                    "hassh_values": list(set(c.get('hassh', 'unknown') for c in recent)),
                    "usernames": list(set(c.get('username', 'unknown') for c in recent)),
                }
            }

            # Store in DB
            self.database.record_rsa_alert(
                client_ip, alert["type"], alert["severity"],
                sim_score, alert["details"]
            )

            logger.warning(
                f"🔥 Random Segment Assessment BURST [{client_ip}] — {len(recent)} connections in "
                f"{self.BURST_WINDOW}s | Similarity: {sim_score}/100 | {severity}"
            )
            return alert

        return None

    def _check_slow_drip(self, client_ip: str, now: float) -> Optional[Dict]:
        """Phase 2: Check for slow-drip attack."""
        connections = self._connections[client_ip]

        if len(connections) < 2:
            return None

        # Gap check: last two connections
        gap = connections[-1]['timestamp'] - connections[-2]['timestamp']
        gap_suspicious = gap < self.TTA

        # Rolling counter check
        window_start = now - self.DRIP_WINDOW
        in_window = [c for c in connections if c['timestamp'] > window_start]

        if len(in_window) >= self.DRIP_N or (gap_suspicious and len(in_window) >= self.DRIP_N // 2):
            alert_key = f"drip_{int(now // self.DRIP_WINDOW)}"
            if alert_key in self._alerts_fired[client_ip]:
                return None

            self._alerts_fired[client_ip].add(alert_key)

            sim_score = self._similarity_score(in_window)
            severity = "HIGH" if sim_score >= 50 else "MEDIUM"

            alert = {
                "type": "slow_drip_detected",
                "severity": severity,
                "ip": client_ip,
                "count": len(in_window),
                "window": self.DRIP_WINDOW,
                "similarity_score": sim_score,
                "details": {
                    "connections_in_window": len(in_window),
                    "window_seconds": self.DRIP_WINDOW,
                    "last_gap_seconds": round(gap, 2),
                    "gap_suspicious": gap_suspicious,
                    "hassh_values": list(set(c.get('hassh', 'unknown') for c in in_window)),
                    "usernames": list(set(c.get('username', 'unknown') for c in in_window)),
                }
            }

            self.database.record_rsa_alert(
                client_ip, alert["type"], alert["severity"],
                sim_score, alert["details"]
            )

            logger.warning(
                f"💧 Random Segment Assessment SLOW-DRIP [{client_ip}] — {len(in_window)} connections in "
                f"{self.DRIP_WINDOW}s | Gap: {gap:.2f}s | Similarity: {sim_score}/100"
            )
            return alert

        return None

    def _similarity_score(self, batch: List[Dict]) -> int:
        """
        Compute similarity score 0-100 for a batch of connections.

        Weights:
        - HASSH match: 50% (identical = 50, mixed = proportional)
        - Timing regularity: 30% (low variance = 30, high = 0)
        - Username repetition: 20% (all same = 20, mixed = proportional)
        """
        if not batch:
            return 0

        score = 0

        # --- HASSH match (50 pts) ---
        hassh_values = [c.get('hassh') for c in batch if c.get('hassh')]
        if hassh_values:
            most_common = max(set(hassh_values), key=hassh_values.count)
            match_ratio = hassh_values.count(most_common) / len(hassh_values)
            score += int(match_ratio * 50)
        else:
            score += 25  # no HASSH data, assume moderate

        # --- Timing regularity (30 pts) ---
        timestamps = sorted(c['timestamp'] for c in batch)
        if len(timestamps) >= 3:
            intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
            mean_interval = statistics.mean(intervals)
            if mean_interval > 0:
                try:
                    cv = statistics.stdev(intervals) / mean_interval  # coefficient of variation
                    # Low CV (< 0.3) = very regular = automated
                    regularity = max(0, 1 - cv)
                    score += int(regularity * 30)
                except statistics.StatisticsError:
                    score += 15  # fallback
            else:
                score += 30  # all at same time = max regularity
        elif len(timestamps) == 2:
            score += 20  # only 2, moderate assumption

        # --- Username repetition (20 pts) ---
        usernames = [c.get('username', '') for c in batch]
        if usernames:
            most_common_user = max(set(usernames), key=usernames.count)
            user_ratio = usernames.count(most_common_user) / len(usernames)
            score += int(user_ratio * 20)

        return min(score, 100)

    def get_ip_stats(self, client_ip: str) -> Dict:
        """Get connection statistics for an IP."""
        connections = self._connections.get(client_ip, [])
        if not connections:
            return {"total": 0}

        now = time.time()
        return {
            "total": len(connections),
            "last_30s": len([c for c in connections if c['timestamp'] > now - 30]),
            "last_5m": len([c for c in connections if c['timestamp'] > now - 300]),
            "unique_hassh": len(set(c.get('hassh', '') for c in connections)),
            "unique_usernames": len(set(c.get('username', '') for c in connections)),
        }

    def cleanup_ip(self, client_ip: str):
        """Clean up tracking data for an IP."""
        self._connections.pop(client_ip, None)
        self._alerts_fired.pop(client_ip, None)
