"""
GhostNet Breadcrumb Agent — AI-Generated Adaptive Deception.

Detects attacker intent using Groq and plants convincing fake files
(breadcrumbs) as canary tripwires in the virtual filesystem.
"""

import os
import json
import logging
import random
from datetime import datetime
from typing import Tuple, Optional, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class BreadcrumbAgent:
    """
    AI-powered deception agent. After each command:
    1. Detects attacker intent via Groq
    2. Generates a convincing fake file tailored to their intent
    3. Plants it where they'll find it
    4. Registers it as a canary tripwire
    """

    INTENT_CATEGORIES = [
        "credential_hunt",
        "ssh_key_hunt",
        "database_hunt",
        "lateral_movement",
        "exfil_prep",
        "none"
    ]

    # Templates for breadcrumb files (used as fallback if Groq fails)
    FALLBACK_BREADCRUMBS = {
        "credential_hunt": {
            "filename": "config.php",
            "content": (
                "<?php\n"
                "// Database configuration — Production\n"
                "define('DB_HOST', '10.0.0.5');\n"
                "define('DB_USER', 'admin');\n"
                "define('DB_PASS', 'Pr0d_S3cret!2025');\n"
                "define('DB_NAME', 'users_production');\n"
                "define('DB_PORT', 3306);\n"
                "?>\n"
            )
        },
        "ssh_key_hunt": {
            "filename": "id_rsa",
            "content": (
                "-----BEGIN OPENSSH PRIVATE KEY-----\n"
                "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn\n"
                "NhAAAAAwEAAQAAAYEA2xR4v3n8K2pL+OeCfdJlbmKZ9J4E7r6YI6c4oBg+V2sNqmdOkR\n"
                "7UzFCJNm5e2kZ3vGt5p7rZH8K1jN8XQKZ+dXe6L5PwGrN8nFJ4hK3e4R+J7DqXR+b5T\n"
                "m8KsN3wXe5G7UqZ+fK3pDr4s8VN9Y2tP6cJFH3mX7zKQ+nB6R8oT2pN+dW5xY7qK4n\n"
                "Y+rT3s8e6wJn5eX7kR3dN+fJ2hK9lY4bP8mT3zR7sQ+kN6cW5pD9nX2dL+hJ4rB7qK\n"
                "R+oT3pN8cW5dY9nK7sX+eJ2hK4lB7rP9mT6zR3sQ+kN6dW2pD5nX8dL+hJ4rB7qK4n\n"
                "3mX7zKQ+nB6R8oT2pNdW5xY7qK4nY+rT3s8e6wJn5eX7kR3N+fJ2hK9lY4bP8mT3zR\n"
                "7sQ+kN6cW5pD9nXdL+hJ4rB7qKR+oT3pN8cW5dY9nK7sX+eJ2hK4lB7rP9mT6zR3sQ\n"
                "+kN6dW2pD5nX8dL+hJ4rBAAAAAwEAAQAAAYBpR7K3k8dfT6nL+9eX2mD5hJ7qK4nYrT\n"
                "-----END OPENSSH PRIVATE KEY-----\n"
            )
        },
        "database_hunt": {
            "filename": ".my.cnf",
            "content": (
                "[client]\n"
                "user = root\n"
                "password = MySQL_R00t_2025!\n"
                "host = 10.0.0.5\n"
                "port = 3306\n"
                "\n"
                "[mysqldump]\n"
                "user = backup_admin\n"
                "password = Bkup_Adm1n_Secret\n"
            )
        },
        "lateral_movement": {
            "filename": "vpn_connect.sh",
            "content": (
                "#!/bin/bash\n"
                "# Internal VPN connection script\n"
                "# DO NOT SHARE — Internal use only\n"
                "VPN_SERVER='vpn.internal.corp.net'\n"
                "VPN_USER='svc_admin'\n"
                "VPN_PASS='Vpn_Adm1n_2025!'\n"
                "openconnect --user=$VPN_USER --passwd-on-stdin $VPN_SERVER <<< $VPN_PASS\n"
            )
        },
        "exfil_prep": {
            "filename": "backup_march2025.tar.gz",
            "content": "[Binary compressed archive data — backup of /home/user/Documents]\n"
        }
    }

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("✓ Breadcrumb Agent initialized (Groq)")
            except ImportError:
                logger.warning("⚠ Groq not available — breadcrumbs will use fallback templates")
        else:
            logger.warning("⚠ No GROQ_API_KEY — breadcrumbs will use fallback templates")

        # Rate limiting: {session_id: {"count": N, "cmd_since_last": N, "total": N}}
        self._session_state: Dict[str, Dict] = {}

    def _get_session_state(self, session_id: str) -> Dict:
        if session_id not in self._session_state:
            self._session_state[session_id] = {
                "cmds_since_plant": 0,
                "total_planted": 0,
                "last_intent": "none"
            }
        return self._session_state[session_id]

    def should_plant(self, session_id: str) -> bool:
        """Rate limiter: max 1 breadcrumb per 3 commands, max 5 total per session."""
        state = self._get_session_state(session_id)
        if state["total_planted"] >= 5:
            return False
        if state["cmds_since_plant"] < 3:
            return False
        return True

    def increment_cmd(self, session_id: str):
        """Call after every command to track rate limiting."""
        state = self._get_session_state(session_id)
        state["cmds_since_plant"] += 1

    def record_plant(self, session_id: str):
        """Call after successfully planting a breadcrumb."""
        state = self._get_session_state(session_id)
        state["cmds_since_plant"] = 0
        state["total_planted"] += 1

    def detect_intent(self, command: str, history: list) -> Tuple[str, float]:
        """
        Detect attacker intent from current command + command history.
        Returns (intent_type, confidence).
        """
        # Fast local detection first (no API needed for obvious cases)
        local_intent = self._local_intent_check(command)
        if local_intent != "none":
            return local_intent, 0.85

        # If Groq is available, do deeper analysis
        if self.client and len(history) >= 3:
            try:
                return self._groq_intent_check(command, history)
            except Exception as e:
                logger.debug(f"Groq intent detection failed: {e}")

        return "none", 0.0

    def _local_intent_check(self, command: str) -> str:
        """Fast pattern matching for obvious intents (no API call needed)."""
        cmd_lower = command.lower().strip()

        # Credential hunting
        cred_patterns = [
            "cat .bash_history", "cat .bashrc", "cat .profile",
            "find / -name *.conf", "find / -name *.cfg",
            "cat /etc/shadow", "cat config", "cat .env",
            "grep -r password", "grep -r secret", "grep -r api_key"
        ]
        for pattern in cred_patterns:
            if pattern in cmd_lower:
                return "credential_hunt"

        # SSH key hunting
        ssh_patterns = [
            "ls .ssh", "ls -la .ssh", "cat .ssh",
            "find / -name id_rsa", "find / -name *.key",
            "find / -name *.pem", "cat id_rsa", "cat authorized_keys"
        ]
        for pattern in ssh_patterns:
            if pattern in cmd_lower:
                return "ssh_key_hunt"

        # Database hunting
        db_patterns = [
            "mysql", "psql", "mongo", "redis-cli",
            "cat .my.cnf", "cat my.cnf",
            "find / -name *.sql"
        ]
        for pattern in db_patterns:
            if pattern in cmd_lower:
                return "database_hunt"

        # Lateral movement
        lateral_patterns = [
            "ssh ", "scp ", "cat /etc/hosts", "arp",
            "ip route", "nmap", "ping 10.", "ping 192."
        ]
        for pattern in lateral_patterns:
            if pattern in cmd_lower:
                return "lateral_movement"

        # Exfiltration prep
        exfil_patterns = [
            "tar ", "zip ", "gzip ", "find / -size",
            "dd if=", "nc ", "curl -X POST"
        ]
        for pattern in exfil_patterns:
            if pattern in cmd_lower:
                return "exfil_prep"

        return "none"

    def _groq_intent_check(self, command: str, history: list) -> Tuple[str, float]:
        """Use Groq to analyze deeper intent patterns."""
        history_text = "\n".join([f"  {cmd}" for cmd in history[-8:]])

        prompt = f"""Analyze this attacker session on a honeypot SSH server.

Recent commands:
{history_text}
Current command: {command}

Classify the attacker's CURRENT intent as exactly one of:
- credential_hunt (looking for passwords, API keys, config files)
- ssh_key_hunt (looking for SSH keys, certificates)
- database_hunt (looking for database access)
- lateral_movement (trying to reach other systems)
- exfil_prep (preparing to extract data)
- none (general exploration)

Respond in JSON only: {{"intent": "...", "confidence": 0.0-1.0}}"""

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=60
        )

        result = json.loads(response.choices[0].message.content)
        intent = result.get("intent", "none")
        confidence = float(result.get("confidence", 0.0))

        # Validate intent
        if intent not in self.INTENT_CATEGORIES:
            intent = "none"

        return intent, confidence

    def generate_breadcrumb(self, intent: str, cwd_path: str) -> Tuple[str, str]:
        """
        Generate a convincing fake file for the detected intent.
        Returns (filename, content).
        """
        # Try Groq generation first
        if self.client and intent != "none":
            try:
                return self._groq_generate(intent, cwd_path)
            except Exception as e:
                logger.debug(f"Groq breadcrumb generation failed, using fallback: {e}")

        # Fallback to templates
        if intent in self.FALLBACK_BREADCRUMBS:
            template = self.FALLBACK_BREADCRUMBS[intent]
            return template["filename"], template["content"]

        return None, None

    def _groq_generate(self, intent: str, cwd_path: str) -> Tuple[str, str]:
        """Use Groq to generate a realistic fake file."""
        intent_descriptions = {
            "credential_hunt": "a configuration file with fake database credentials and API keys",
            "ssh_key_hunt": "a fake SSH private key file (OpenSSH format)",
            "database_hunt": "a MySQL/PostgreSQL config file with fake credentials",
            "lateral_movement": "a VPN or internal network connection script with fake credentials",
            "exfil_prep": "a fake file manifest listing important-looking documents"
        }

        description = intent_descriptions.get(intent, "a generic decoy file")

        prompt = f"""Generate {description} for a honeypot system.
The file should look completely realistic to fool an attacker.
Current directory: {cwd_path}

Rules:
- Use realistic-looking but FAKE credentials (IP addresses like 10.x.x.x, passwords with special chars)
- Include comments that make it look like a real production file
- Keep it under 20 lines

Respond in JSON only: {{"filename": "...", "content": "..."}}"""

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        result = json.loads(response.choices[0].message.content)
        return result["filename"], result["content"]
