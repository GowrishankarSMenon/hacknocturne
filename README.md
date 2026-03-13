# GhostNet: Autonomous AI Cyber-Deception System

A multi-agent AI honeypot that generates realistic, dynamic Linux environments in real-time to trap and profile attackers.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      SSH Listener (Port 2222)                   │
│                    (Paramiko SSH Server)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                            │
│              (Analyzes attacker intent/behavior)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
     ┌──────────────┐ ┌──────────┐ ┌────────────┐
     │   OS Sim     │ │Profiler  │ │ Breadcrumb│
     │  (LLM)       │ │Agent     │ │Generator  │
     └──────┬───────┘ └──────────┘ └────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│              State Manager (SQLite + Filesystem JSON)            │
│                    (Persistent State)                           │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│         Streamlit Dashboard (Intelligence & Analytics)          │
│              (Live Logs, IP Geo, Threat Analysis)               │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: SSH Parrot (Basic SSH Listener)
- SSH listener on port 2222 using Paramiko
- Accept any password
- Forward commands to LLM
- Return terminal output

### Phase 2: Memory Layer (Persistent State)
- SQLite/JSON filesystem state
- Maintain file/folder structure
- Persist commands across session

### Phase 3: Intelligence Dashboard
- Streamlit frontend
- Live command logs
- IP geolocation
- Attacker behavior analysis

### Phase 4: Realism Polish
- Response latency injection
- Random command failures
- Honeypot breadcrumbs (decoy files)
- Realistic error messages

## Quick Start

1. **Setup environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   ```bash
   # Create .env file
   OPENAI_API_KEY=your_key_here
   ```

3. **Run SSH honeypot:**
   ```bash
   python main.py
   ```

4. **Run dashboard (in another terminal):**
   ```bash
   streamlit run dashboard/app.py
   ```

## Project Structure

```
ghostnet/
├── ssh_listener/           # Paramiko SSH server
│   ├── __init__.py
│   └── server.py
├── agents/                 # LangGraph agents
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── os_simulator.py
│   └── profiler.py
├── state_manager/          # Filesystem state & database
│   ├── __init__.py
│   ├── file_system.py
│   └── database.py
├── dashboard/              # Streamlit UI
│   ├── __init__.py
│   └── app.py
├── logs/                   # Activity logs
├── main.py                 # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Environment Variables

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-gemini-api-key-here
SSH_PORT=2222
LOG_FILE=logs/ghostnet.log
DATABASE_FILE=logs/ghostnet.db
```

## Technologies Used

- **SSH Server:** Paramiko
- **AI/LLM:** Google Gemini API (gemini-pro)
- **Agent Framework:** LangGraph
- **Database:** SQLite
- **Frontend:** Streamlit
- **Geolocation:** Folium + GeoIP2

## Status

🚀 In Development - Phase 1 (SSH Parrot)
