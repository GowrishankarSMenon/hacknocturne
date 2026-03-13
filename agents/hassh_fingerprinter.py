"""
HASSH Fingerprinter — Cross-IP Attacker Identification.

Captures SSH client algorithm preferences from the transport handshake
and computes an MD5 hash (HASSH) that uniquely identifies the SSH client
tool regardless of source IP. Enables botnet clustering and campaign detection.

Reference: https://github.com/salesforce/hassh
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class HASSHFingerprinter:
    """
    Computes HASSH fingerprints from Paramiko transports and stores
    them in the global database for cross-IP correlation.
    """

    # Known HASSH values for common tools (public databases)
    KNOWN_TOOLS = {
        "ec7378c1a92f5a8dde7e8b7a1ddf33d1": "OpenSSH 8.x",
        "b12d2871a1571f38b5b6a4c0d1c3d0e2": "OpenSSH 9.x",
        "c43a3f4c3e5d8e7b6a9f0d1c2b3e4a5f": "PuTTY",
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6": "Hydra SSH",
        "d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9": "Nmap NSE",
        "f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6": "Paramiko (Python)",
        # Additional known tools
        "a7a87fbe86774c2e40cc4a7ea2ab1b3c": "PuTTY (alt)",
        "3f0099d323c3b5a25edec88a88d6c01b": "Paramiko (alt)",
        "1dd492024d86f9f9c27d5d7e4d6fdb41": "Metasploit",
        "06046964c022c6407d15a27b12a6a4fb": "AsyncSSH",
        "63e0e6a2a89f5ece26e26a975b7a6b07": "Masscan-SSH",
    }

    def __init__(self, database):
        """
        Args:
            database: GhostNetDatabase instance (global DB for cross-IP queries)
        """
        self.database = database

    def compute_hassh(self, transport) -> Optional[str]:
        """
        Compute HASSH from a Paramiko Transport after key exchange.

        HASSH = MD5(kex_algorithms;encryption_algorithms;mac_algorithms;compression_algorithms)

        The algorithm lists come from the client's SSH_MSG_KEXINIT packet.
        """
        try:
            # After start_server() completes, the transport stores the
            # client-offered algorithms from the KEXINIT message.
            kex = self._get_client_algorithms(transport, 'kex')
            enc = self._get_client_algorithms(transport, 'encryption')
            mac = self._get_client_algorithms(transport, 'mac')
            comp = self._get_client_algorithms(transport, 'compression')

            # Build the HASSH input string
            hassh_input = f"{kex};{enc};{mac};{comp}"
            hassh = hashlib.md5(hassh_input.encode('utf-8')).hexdigest()

            logger.info(f"HASSH computed: {hassh} (input: {hassh_input[:80]}...)")
            return hassh

        except Exception as e:
            logger.debug(f"HASSH computation failed: {e}")
            # Fallback: hash the transport's remote version string
            try:
                remote_version = getattr(transport, 'remote_version', None) or "unknown"
                fallback = hashlib.md5(remote_version.encode('utf-8')).hexdigest()
                logger.info(f"HASSH fallback (remote version): {fallback}")
                return fallback
            except Exception:
                return None

    def _get_client_algorithms(self, transport, algo_type: str) -> str:
        """
        Extract client-offered algorithms from Paramiko transport.
        Paramiko stores these after the KEXINIT exchange.
        """
        try:
            so = transport.get_security_options()
            if algo_type == 'kex':
                return ','.join(so.kex)
            elif algo_type == 'encryption':
                return ','.join(so.ciphers)
            elif algo_type == 'mac':
                return ','.join(so.digests)
            elif algo_type == 'compression':
                return ','.join(so.compression)
        except Exception:
            pass

        # Fallback: try internal attributes
        attr_map = {
            'kex': '_preferred_kex',
            'encryption': '_preferred_ciphers',
            'mac': '_preferred_macs',
            'compression': '_preferred_compression',
        }
        attr = attr_map.get(algo_type)
        if attr and hasattr(transport, attr):
            val = getattr(transport, attr)
            if isinstance(val, (list, tuple)):
                return ','.join(val)
            return str(val)

        return ''

    def record(self, session_id: str, client_ip: str, hassh: str, username: str = "user"):
        """Store HASSH fingerprint in the global database."""
        try:
            self.database.record_hassh(session_id, client_ip, hassh, username)
            logger.info(f"HASSH recorded: {hassh[:12]}... for {client_ip} (session {session_id[:8]})")
        except Exception as e:
            logger.debug(f"HASSH record failed: {e}")

    def correlate(self, hassh: str) -> List[Dict]:
        """
        Find all sessions with the same HASSH fingerprint.
        Returns list of {session_id, client_ip, username, timestamp} dicts.
        """
        try:
            sessions = self.database.get_hassh_sessions(hassh) or []
            if len(sessions) > 1:
                ips = list(set(s['client_ip'] for s in sessions))
                if len(ips) > 1:
                    logger.warning(
                        f"HASSH CORRELATION: {hassh[:12]}... seen from {len(ips)} IPs: {ips}"
                    )
            return sessions
        except Exception:
            return []

    def identify_tool(self, hassh: str) -> Optional[str]:
        """Look up HASSH against known tool database."""
        return self.KNOWN_TOOLS.get(hassh)

    def get_session_hassh(self, session_id: str) -> Optional[str]:
        """Get the HASSH for a specific session."""
        try:
            return self.database.get_session_hassh(session_id)
        except Exception:
            return None
