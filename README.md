<br><div align="center">

```
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗███╗   ██╗███████╗████████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝████╗  ██║██╔════╝╚══██╔══╝
██║  ███╗███████║██║   ██║███████╗   ██║   ██╔██╗ ██║█████╗     ██║
██║   ██║██╔══██║██║   ██║╚════██║   ██║   ██║╚██╗██║██╔══╝     ██║
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██║ ╚████║███████╗   ██║
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝
```

**AeroGhost · Autonomous AI Cyber-Deception System**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/dashboard-streamlit-FF4B4B.svg)](https://streamlit.io)
[![Groq AI](https://img.shields.io/badge/AI-Groq-orange.svg)](https://groq.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*A next-generation SSH honeypot that doesn't just trap attackers — it actively deceives them.*

</div>

---

## What Is GhostNet?

GhostNet is an **AI-powered SSH honeypot** that simulates a realistic Ubuntu Linux server. When an attacker connects, instead of blocking them, GhostNet:

1. **Lets them in** — with a convincing fake Ubuntu shell
2. **Watches their every move** — logging commands, detecting intent
3. **Adapts in real-time** — planting fake "breadcrumb" files tailored to what the attacker is hunting for
4. **Trips canary wires** — alerts when the attacker interacts with planted bait
5. **Generates intelligence** — threat reports, geo-maps, attack timelines

> **Hackathon Project** built for [HackNocturne] by [@GowrishankarSMenon](https://github.com/GowrishankarSMenon)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AEROGHOST SYSTEM                          │
│                                                                   │
│  ┌──────────────┐    ┌───────────────────────────────────────┐   │
│  │  SSH Listener│    │           Main Orchestrator            │   │
│  │  (Paramiko)  │───▶│         GhostNetHoneypot              │   │
│  │  Port: 2222  │    └──────────────┬────────────────────────┘   │
│  └──────────────┘                   │                             │
│                          ┌──────────┴──────────┐                  │
│                          ▼                     ▼                  │
│              ┌─────────────────┐   ┌──────────────────┐          │
│              │  Command Handler│   │  Breadcrumb Agent│          │
│              │  (50+ commands) │   │  (AI Deception)  │          │
│              └────────┬────────┘   └────────┬─────────┘          │
│                       │                     │                     │
│              ┌────────▼────────┐   ┌────────▼─────────┐          │
│              │ Virtual FS Tree │   │  General Intel.  │          │
│              │  (per session)  │   │  Agency (GIA)    │          │
│              └────────┬────────┘   └────────┬─────────┘          │
│                       │                     │                     │
│              ┌────────▼─────────────────────▼──────────┐         │
│              │        Per-Session SQLite DB             │         │
│              │   logs/sessions/<session_id>.db          │         │
│              └──────────────────────┬───────────────────┘         │
│                                     │                             │
│              ┌──────────────────────▼───────────────────┐         │
│              │     Streamlit Dashboard (Port 8501)       │         │
│              │  Live Terminal │ Intelligence │ Geo-Map   │         │
│              └───────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Overview

### 🖥️ Realistic SSH Shell
- Simulates **Ubuntu 22.04 LTS** (`uname`, `cat /etc/os-release`)
- 50+ working commands: `ls`, `cd`, `cat`, `grep`, `find`, `ps`, `netstat`, `curl`, `wget`, `history`, `sudo`, `ssh`, and more
- Per-session isolated **virtual filesystem** with realistic directory trees (Documents, Downloads, .ssh, /etc/passwd, /var/log/, etc.)
- Shell prompt: `user@aeroghost:~$`

### 🎣 AI-Generated Adaptive Breadcrumbs
The core deception engine. Detects **attacker intent** and plants convincing fake files as canary tripwires:

| Intent Detected | Planted File | Contains |
|---|---|---|
| `credential_hunt` | `config.php` | Fake DB passwords, API keys |
| `ssh_key_hunt` | `.ssh/id_rsa` | Fake OpenSSH private key |
| `database_hunt` | `.my.cnf` | Fake MySQL root credentials |
| `lateral_movement` | `vpn_connect.sh` | Fake internal VPN script |
| `exfil_prep` | `backup_march2025.tar.gz` | Fake backup manifest |

Files are planted **3–10 seconds after** the triggering command (so they look like they were always there) with realistic timestamps (5–60 days old).

When the attacker opens a planted file → **CRITICAL ALERT** fires on the dashboard.

### 🕵️ General Intelligence Agency (GIA)
A background watchdog that monitors sessions every 5 seconds for:

| Check | What It Catches |
|---|---|
| 🤖 **Bot Detector** | Commands arriving < 200ms apart (automated scanner) |
| 🔍 **Suspicion Scorer** | `ls` spam, timestamp checking (`stat`, `find -newer`) |
| ⏰ **Realism Validator** | Breadcrumb files with too-recent timestamps |
| 🧹 **Session Integrity** | Zombie sessions in DB not in memory |

### 🗺️ Geo-Intelligence Map
- IP geolocation of connected attackers via `ip-api.com`
- Interactive **Folium dark map** with attacker markers
- Pulsing red circles + popup with city, ISP, org, session ID

### 📊 Threat Score Engine
Computes a **0–100 threat score** per session based on:
- Volume of commands (up to 20 pts)
- Dangerous keywords (`sudo`, `shadow`, `curl`, `nmap`, etc.) — up to 60 pts
- Session duration (up to 20 pts)
- Displayed as a **Plotly gauge chart**

### 📈 Command Timeline
Scatter-plot of all commands over time, color-coded:
- 🔴 **Dangerous** — commands matching known threat patterns
- 🟢 **Benign** — normal recon/exploration

---

## Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/GowrishankarSMenon/hacknocturne.git
cd hacknocturne
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy the example .env
copy .env.example .env   # Windows
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here   # Get free at console.groq.com
SSH_PORT=2222
```

> **Note:** `GROQ_API_KEY` is optional. Without it, breadcrumbs use fallback templates and threat reports are unavailable. Everything else works fully.

### 3. Run the Honeypot
```bash
# Terminal 1 — SSH server
python main.py

# Terminal 2 — Dashboard
streamlit run dashboard/app.py
```

Or use the provided batch files:
```bash
start.bat   # Starts both
stop.bat    # Kills both
```

### 4. Connect as an Attacker (Testing)
```bash
ssh user@localhost -p 2222
# Password: anything (all passwords accepted)
```

---

## Project Structure

```
ghostnet/
│
├── main.py                     # Main orchestrator — wires everything together
├── requirements.txt            # Python dependencies
├── start.bat / stop.bat        # Windows convenience launchers
│
├── agents/
│   ├── command_handler.py      # 50+ shell command simulations
│   ├── breadcrumbs.py          # AI deception engine (intent → fake files)
│   ├── intelligence_agency.py  # GIA background watchdog
│   ├── geo_lookup.py           # IP geolocation via ip-api.com
│   └── os_simulator.py         # Groq-powered AI response fallback
│
├── ssh_listener/
│   └── server.py               # Paramiko SSH server (AeroGhostSSHServer)
│
├── state_manager/
│   ├── database.py             # GhostNetDatabase (session index) + SessionDatabase (per-session)
│   └── file_system.py          # VirtualFileSystem tree (FSNode)
│
├── dashboard/
│   └── app.py                  # Streamlit dashboard (6 tabs)
│
└── logs/
    ├── ghostnet.log            # Main system log
    ├── ghostnet.db             # Session index (SQLite)
    └── sessions/
        └── <session_id>.db     # Per-session isolated database
```

---

## Dashboard Tabs

| Tab | Description |
|---|---|
| **Live Terminal** | Real-time command output per session with live typing feed |
| **Live Activity** | Scrollable command history across all sessions |
| **Sessions** | Table of active/recent sessions with IP, username, command count, canary hits |
| **Intelligence & GIA** | Threat gauge, command timeline, intent progression, canary status, GIA alerts, threat report |
| **Geo-Intelligence** | Interactive world map of attacker origins |
| **Analytics** | Session activity heatmap (hour × day of week), historical stats |

---

## Key Design Decisions

### Per-Session SQLite Isolation
Each attacker gets **their own SQLite database** at `logs/sessions/<session_id>.db`. This prevents:
- Cross-session data leakage
- Race conditions between concurrent attackers
- Compromise of one session's data affecting others

```
Session A → logs/sessions/abc123.db  (commands, intents, canaries)
Session B → logs/sessions/def456.db  (completely isolated)
Global   → logs/ghostnet.db          (session index only)
```

### Async Breadcrumb Pipeline
The deception pipeline runs in a **background thread** with a 3–10 second delay so:
- The attacker's terminal feels instant (no lag)
- Files don't appear suspiciously fast after commands
- A smart attacker won't notice the correlation

### Canary Tripwire Flow
```
Attacker types "cat .bash_history"
       ↓
BreadcrumbAgent detects: credential_hunt (confidence 0.85)
       ↓ (background thread, 5s delay)
Plants config.php with fake DB credentials
Registers as canary in SessionDB
       ↓
Attacker types "cat config.php"
       ↓
CommandHandler.`_cmd_cat` checks canary registry → HIT
       ↓
SessionDB.trigger_canary() → logs threat_event
       ↓
Dashboard shows pulsing red ⚠️ CRITICAL ALERT
```

---

## Tech Stack

| Component | Technology |
|---|---|
| SSH Server | `paramiko` |
| AI / LLM | `groq` (llama-3.3-70b-versatile) |
| Dashboard | `streamlit` + `streamlit-autorefresh` |
| Visualizations | `plotly` |
| Geo Map | `folium` + `streamlit-folium` |
| Database | `sqlite3` (stdlib — no external DB needed) |
| Geolocation | `ip-api.com` (free, no key required) |

---

## Testing

### Run component tests
```bash
python test_components.py
# Expected: 4 passed, 0 failed

python test_filesystem.py
# Tests VirtualFileSystem, dotfiles, path resolution
```

### Manual attack paths

| Scenario | Commands | Expected Result |
|---|---|---|
| Credential Hunt | `cat .bash_history` → wait 10s → `ls` → `cat config.php` | CRITICAL alert on dashboard |
| SSH Key Hunt | `ls .ssh` → `find / -name id_rsa` | `id_rsa` planted in `.ssh/` |
| Lateral Movement | `cat /etc/hosts` → `ssh admin@10.0.0.5` | `vpn_connect.sh` planted |
| Database Hunt | `cat .my.cnf` → `mysql` | `.my.cnf` planted |
| Bot Detection | Paste 10 commands rapidly | GIA flags `bot_detected` in dashboard |
| Suspicion Alert | Type `ls` 4+ times | GIA flags `ls_spam` |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Optional | Groq API key for AI intent detection and threat reports |
| `SSH_PORT` | Optional | SSH server port (default: `2222`) |

---

## Contributing

Pull requests welcome. Key areas for improvement:
- More command implementations in `command_handler.py`
- Additional intent categories in `breadcrumbs.py`
- More GIA checks in `intelligence_agency.py`
- Enhanced dashboard analytics

---

<div align="center">

**AeroGhost** — Built for HackNocturne 2026

*"The best trap is one the target walks into willingly."*

</div>
