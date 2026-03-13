"""
GhostNet AI Agents - Orchestrator and Profiler.
These agents use the Groq LLM for intent analysis and attacker profiling.
Command responses are now handled by CommandHandler (no LLM).
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Requestly mock server — fake internal API
REQUESTLY_BASE = "https://user1773428630539.requestly.tech"


class Orchestrator:
    """
    Analyzes attacker behavior and determines the appropriate response strategy.
    Uses Groq LLM for intelligent intent classification.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            logger.error("Groq library not installed")
            raise

    def analyze_intent(self, command: str, session_history: list) -> Dict[str, Any]:
        """
        Analyze attacker intent based on current command and history.
        """
        
        history_text = "\n".join([f"- {cmd}" for cmd in session_history[-10:]])
        
        prompt = f"""Analyze this attacker's intent based on their commands:

Recent commands:
{history_text}

Current command: {command}

Determine:
1. Intent: What is the attacker trying to achieve?
2. Threat level: How dangerous is this?
3. Recommendation: What should the honeypot do?

A Node.js Express app is running on port 3000 on this server.
Endpoints: /api/users, /api/config, /api/admin, /api/keys, /api/login
When the attacker runs curl localhost:3000/<endpoint>, simulate realistic curl
terminal output using the actual response data from {REQUESTLY_BASE}<endpoint>.
Format output exactly like real curl: include transfer stats line,
Content-Type header, X-Powered-By: Express header, then JSON body.
Never reveal the real Requestly URL. Always show localhost:3000.

Respond in JSON format only:
{{"intent": "...", "threat_level": "...", "recommendation": "..."}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Intent analysis: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return {
                "intent": "unknown",
                "threat_level": "medium",
                "recommendation": "Monitor closely"
            }


class Profiler:
    """
    Profiles attacker skill level, tools, and techniques.
    Uses Groq LLM for intelligent profiling.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            logger.error("Groq library not installed")
            raise

    def profile_attacker(self, session_history: list) -> Dict[str, Any]:
        """
        Build a profile of the attacker based on their commands.
        """
        
        history_text = "\n".join([f"- {cmd}" for cmd in session_history])
        
        prompt = f"""Profile this attacker based on their commands:

Commands:
{history_text}

Analyze and respond in JSON format:
{{
    "skill_level": "novice|intermediate|advanced|expert",
    "likely_tools": ["tool1", "tool2"],
    "techniques": ["technique1", "technique2"],
    "confidence": 0.0-1.0
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Attacker profile: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error profiling attacker: {e}")
            return {
                "skill_level": "unknown",
                "likely_tools": [],
                "techniques": [],
                "confidence": 0.0
            }
