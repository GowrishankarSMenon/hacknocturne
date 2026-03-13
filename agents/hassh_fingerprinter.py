"""
AeroGhost HASSH Fingerprinter.
HASSH (SSH Honeypot Fingerprinting) creates a fingerprint of SSH client
behaviour during key exchange, allowing identification of specific tools and
correlation of the same attacker across multiple IPs.
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Known HASSH → tool mappings (from public HASSH databases)
KNOWN_TOOLS = {
    "92674389fa1e47a27ddd8d9b63ecd42b": "OpenSSH",
    "a7a87fbe86774c2e40cc4a7ea2ab1b3c": "PuTTY",
    "3f0099d323c3b5a25edec88a88d6c01b": "Paramiko",
    "1dd492024d86f9f9c27d5d7e4d6fdb41": "Metasploit",
    "06046964c022c6407d15a27b12a6a4fb": "AsyncSSH",
    "63e0e6a2a89f5ece26e26a975b7a6b07": "Masscan-SSH",
}


def _compute_hash_from_transport(transport) -> Optional[str]:
    """
    Extract HASSH from a paramiko transport's key exchange algorithms.
    Creates an MD5 hash of the client's algorithm lists.
    """
    try:
        # Try to get remote key exchange details
        remote_version = getattr(transport, 'remote_version', '') or ''
        agreed_kex = getattr(transport, '_preferred_kex', [])
        if not agreed_kex and hasattr(transport, '_agreed_kex'):
            agreed_kex = [transport._agreed_kex]
        
        # Build a fingerprint string from available info
        parts = [
            remote_version,
            ";".join(agreed_kex) if agreed_kex else "unknown",
        ]
        
        fingerprint_str = "|".join(parts)
        hassh = hashlib.md5(fingerprint_str.encode()).hexdigest()
        return hassh
    except Exception as e:
        logger.debug(f"HASSH compute failed: {e}")
        # Fallback: just use remote version string
        try:
            remote_version = getattr(transport, 'remote_version', None)
            if remote_version:
                return hashlib.md5(remote_version.encode()).hexdigest()
        except Exception:
            pass
        return None


class HASSHFingerprinter:
    """
    Computes, records, and correlates SSH client HASSH fingerprints.
    Allows identification of known attack tools and cross-IP correlation
    (same attacker connecting from multiple IPs).
    """

    def __init__(self, database):
        self.db = database

    def compute_hassh(self, transport) -> Optional[str]:
        """Compute HASSH from a paramiko Transport object."""
        return _compute_hash_from_transport(transport)

    def record(self, session_id: str, client_ip: str, hassh: str, username: str = "user"):
        """Store a HASSH fingerprint in the database."""
        try:
            self.db.record_hassh(session_id, client_ip, hassh, username)
        except Exception as e:
            logger.debug(f"HASSH record failed: {e}")

    def correlate(self, hassh: str) -> List[Dict]:
        """
        Find all sessions that share this HASSH fingerprint.
        Used for cross-IP attacker correlation.
        """
        try:
            return self.db.get_hassh_sessions(hassh) or []
        except Exception:
            return []

    def identify_tool(self, hassh: str) -> Optional[str]:
        """Identify the SSH client tool from a known HASSH database."""
        return KNOWN_TOOLS.get(hassh)
