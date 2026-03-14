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
[![Next.js](https://img.shields.io/badge/dashboard-Next.js-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Groq AI](https://img.shields.io/badge/AI-Groq%20LLaMA--3.3--70b-orange.svg)](https://groq.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*A next-generation SSH honeypot that doesn't just trap attackers — it actively deceives them.*

</div>

---

## What Is AeroGhost?

AeroGhost is an **AI-powered SSH honeypot** that simulates a realistic Ubuntu Linux server. When an attacker connects, instead of blocking them, AeroGhost:

1. **Lets them in** — with a convincing fake Ubuntu 22.04 LTS shell and real-feeling filesystem
2. **Watches every move** — logging every command, keystroke timing, and intent
3. **Fingerprints them** — computing SSH HASSH fingerprints for cross-IP campaign tracking
4. **Classifies them** — distinguishing automated bots from humans via keystroke timing
5. **Detects anomalies** — identifying volumetric burst attacks and slow-drip RSA scans
6. **Simulates an internal network** — trapping attackers in lateral movement loops
7. **Plants bait files** — AI-generated canary tripwires tailored to attacker intent
8. **Reports in real time** — through a live Next.js intelligence dashboard and REST API

> **Hackathon Project** — Built for HackNocturne 2026 by [@GowrishankarSMenon](https://github.com/GowrishankarSMenon)

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      AEROGHOST SYSTEM                             │
│                                                                    │
│  ┌────────────────┐    ┌─────────────────────────────────────┐   │
│  │  SSH Listener  │───▶│         Main Orchestrator            │   │
│  │  (Paramiko)    │    │       GhostNetHoneypot               │   │
│  │  Port: 2222    │    └──────┬─────────┬────────────┬───────┘   │
│  └────────────────┘          │         │            │            │
│                    ┌─────────┘    ┌────┘     ┌──────┘           │
│                    ▼              ▼           ▼                   │
│            ┌──────────────┐ ┌──────────┐ ┌──────────────────┐   │
│            │ Command      │ │ HASSH    │ │ Breadcrumb Agent │   │
│            │ Handler      │ │ Finger-  │ │ (AI Deception)   │   │
│            │ (50+ cmds)   │ │ printing │ │ Background Thread│   │
│            │ Tab Complete │ │ RSA Det. │ └────────┬─────────┘   │
│            └──────┬───────┘ └──────────┘          │             │
│                   │                                │             │
│            ┌──────▼────────────────────────────────▼───────┐    │
│            │            Per-Session SQLite DB               │    │
│            │         logs/sessions/<session_id>.db           │    │
│            └─────────────────────┬─────────────────────────┘    │
│                                  │                               │
│          ┌───────────────────────┼────────────────────────┐     │
│          ▼                       ▼                         ▼     │
│  ┌──────────────┐     ┌─────────────────┐     ┌──────────────┐  │
│  │  FastAPI     │     │  Next.js         │     │  Auto PDF    │  │
│  │  REST API    │     │  Dashboard       │     │  Reports     │  │
│  │  Port 8000   │     │  Port 3000       │     │  (on close)  │  │
│  └──────────────┘     └─────────────────┘     └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## What's Actually Implemented

### 🖥️ Realistic SSH Shell

- Simulates **Ubuntu 22.04 LTS** — correct `uname`, `cat /etc/os-release`, `lsb_release`
- **50+ working commands**: `ls`, `cd`, `cat`, `grep`, `find`, `ps`, `netstat`, `curl`, `wget`, `history`, `sudo`, `ssh`, `nmap`, `mysql`, `python3`, `pip3`, `git`, `env`, `chmod`, `rm`, `cp`, `mv`, `mkdir`, `touch`, `echo`, `stat`, `df`, `du`, `free`, `uptime`, `whoami`, `id`, and more
- Per-session isolated **virtual filesystem** with realistic directory trees (`.ssh`, `/etc/passwd`, `/var/log/`, `/home/user/`)
- **Piped commands**, background jobs, and subshells
- **MySQL simulator** — `mysql -u root -p` drops into a convincing MariaDB-style session
- **Tab autocomplete** — auto-completes commands and filesystem paths from the session's virtual tree

### 🕸️ Endless Lateral Movement Trap

- **Fake `nmap` scans** reveal an internal subnet (`10.0.1.x`) with machines like `prod-db-01`, `dev-api-02`, `backup-srv`
- Attackers can **`ssh` into these fake nodes** from the shell prompt
- Each fake node has its own simulated OS, role, and fake data
- Shell prompt dynamically updates per node (e.g., `dbadmin@prod-db-01:~$`)
- Entirely software-defined — no containers or VMs

### 🎣 AI-Generated Adaptive Breadcrumbs

Intent-triggered bait files are planted as canary tripwires:

| Intent Detected | Planted File | Contains |
|---|---|---|
| `credential_hunt` | `config.php` / `.env` | Fake DB passwords, API keys |
| `ssh_key_hunt` | `.ssh/id_rsa` | Fake OpenSSH RSA private key |
| `database_hunt` | `.my.cnf` | Fake MySQL root credentials |
| `lateral_movement` | `vpn_connect.sh` | Fake internal VPN script |
| `exfil_prep` | `backup_march2025.tar.gz` | Fake backup manifest |
| `recon` | `network_map.txt` | Fake internal IP map |

- Planted 3–10 seconds after the triggering command with realistic past timestamps
- Canary triggers fire a **CRITICAL ALERT** recorded instantly to the dashboard

### 🕵️ General Intelligence Agency (GIA)

Background watchdog that monitors sessions every 5 seconds:

| Check | What It Catches |
|---|---|
| **Intent Progression** | Tracks kill chain: `recon → credential_hunt → lateral_movement → exfil_prep` |
| **Suspicion Scorer** | Detects `ls` spam, timestamp checking, suspicious command bursts |
| **Realism Validator** | Validates breadcrumb timestamps remain believable |
| **Bot Detection** | Flags suspiciously fast or uniform inter-command timing |

### 🤖 Threat Identification

**Bot vs. Human Detection** (`agents/timing_analyzer.py`):
- Records inter-keystroke intervals (IPDs) in real time
- Classifies sessions as `human`, `suspicious`, or `bot`
- Detects reconnaissance bursts

**HASSH Fingerprinting** (`agents/hassh_fingerprinter.py`):
- MD5 hash of the SSH client's algorithm preference list during handshake
- Detects known attack tool signatures: OpenSSH, PuTTY, Hydra, Nmap, Metasploit, Paramiko, etc.
- **Cross-IP Correlation** — flags when the same fingerprint appears from multiple IPs

**RSA Detection** (`agents/rsa_detector.py`):
- Detects **Volumetric Bursts** (≥10 connections in 30 seconds)
- Detects **Slow-Drip Attacks** (sequential gaps < 2s)
- Similarity scoring algorithm (0–100) based on HASSH, timing, and username patterns

### 📄 Automated PDF Session Reports

When a session closes, a PDF is automatically generated at `logs/reports/<session_id>.pdf`:
- Session metadata (IP, username, start/end time, HASSH)
- Full timestamped command log with danger flags
- Detected intents with confidence scores
- Canary tripwire events
- All GIA and timing alerts
- Aggregate threat score (0–100) with CRITICAL/HIGH/MEDIUM/LOW verdict

### 🌐 REST API (`api/server.py`)

FastAPI on port `8000` — Swagger UI at `/api/docs`:

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/sessions` | List sessions (filterable by `?status=active`) |
| `GET /api/sessions/{id}` | Full session detail |
| `GET /api/sessions/{id}/commands` | All commands for a session |
| `GET /api/sessions/{id}/intents` | Detected intents for a session |
| `GET /api/sessions/{id}/canaries` | Canary file status for a session |
| `GET /api/sessions/{id}/hassh` | HASSH fingerprint for a session |
| `POST /api/sessions/{id}/report` | Generate Groq-powered threat report |
| `GET /api/alerts` | All threat events (filterable by `?severity=critical`) |
| `GET /api/stats` | Summary stats |
| `GET /api/rsa-alerts` | Current RSA/fingerprint alerts |
| `POST /api/rsa-alerts/{id}/action` | Record cyber team action on an alert |
| `GET /api/hassh` | All HASSH fingerprints + cross-IP correlations |
| `GET /api/live-typing` | Real-time attacker keystroke buffer |

### 📊 Next.js Intelligence Dashboard (Port 3000)

A glassmorphism, bento-grid UI with 5 tabs:

| Tab | Contents |
|---|---|
| **Overview** | Live stats (total sessions, active intruders, unique IPs, threat alerts), session table with HASSH column and cross-IP correlation, live clickable threat feed |
| **Live Terminal** | Compact macOS-style terminal per active session — shows live keystroke buffer and command history, scrollable |
| **Intelligence** | Per-session attacker profile, threat score gauge, geo map, intent progression flow, command timeline, canary status, GIA alerts, Groq-powered threat report generation, and RSA alert panel |
| **Geo-Intelligence** | Global dark Leaflet map of all attacker IPs with session popups, plus origins table |
| **Analytics** | Session activity heatmap (day vs. hour), session ledger with IPD data |

**Session Detail Page** (`/dashboard/<session_id>`):
- Full 3-panel bento layout: attacker profile + geo map / command terminal / alerts + canaries
- Intent flow visualization
- All data auto-refreshes every 3 seconds

---

## Quick Start

### Local (Python venv + Node.js)

```bash
git clone https://github.com/GowrishankarSMenon/hacknocturne.git
cd hacknocturne

# Backend — create venv and install
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

# Configure
# Edit .env and set GROQ_API_KEY (free at console.groq.com)

# Start all services (Windows)
.\start.bat
```

Or manually in three terminals:
```bash
# Terminal 1 — SSH honeypot
python main.py

# Terminal 2 — REST API
uvicorn api.server:app --port 8000

# Terminal 3 — Next.js dashboard
cd website && npm install && npm run dev
```

**Ports:**
- `:2222` — SSH honeypot (publicly expose this)
- `:8000` — REST API + Swagger at `/api/docs`
- `:3000` — Next.js dashboard

### Docker

```bash
docker-compose up -d
```

Exposes ports 2222, 8000. Reads `GROQ_API_KEY` from `.env`. Persists logs across restarts.

> **Note:** The Docker setup runs the Python backend only (SSH server + API). The Next.js dashboard is intended to run locally or behind a reverse proxy.

---

## RSA Attack Simulation

```bash
# Activate venv
.\venv\Scripts\activate

# Burst attack — 12 concurrent connections (triggers CRITICAL)
python rsa_tester.py burst

# Slow-drip attack — 22 connections, 1s apart (triggers HIGH)
python rsa_tester.py drip

# Custom parameters
python rsa_tester.py burst --count 30
python rsa_tester.py drip --delay 0.5 --count 25
```

---

## Project Structure

```
ghostnet/
│
├── main.py                       # Main orchestrator
├── run.py                        # Cross-platform unified launcher
├── rsa_tester.py                 # RSA burst/drip attack simulation utility
├── requirements.txt              # Python dependencies
├── Dockerfile / docker-compose.yml
├── start.bat / stop.bat          # Windows launchers
│
├── agents/
│   ├── command_handler.py        # 50+ shell commands + tab autocomplete
│   ├── breadcrumbs.py            # AI deception engine (intent → fake file generation)
│   ├── intelligence_agency.py    # GIA background watchdog
│   ├── geo_lookup.py             # IP geolocation via ip-api.com
│   ├── os_simulator.py           # Groq-powered AI response generation
│   ├── rsa_detector.py           # RSA burst/drip detection + similarity scoring
│   ├── hassh_fingerprinter.py    # HASSH fingerprinting + cross-IP correlation
│   ├── timing_analyzer.py        # Bot vs. human keystroke classification
│   ├── network_sim.py            # Fake internal subnet simulator
│   └── report_generator.py       # Auto PDF report on session close
│
├── ssh_listener/
│   └── server.py                 # Paramiko SSH server
│
├── api/
│   └── server.py                 # FastAPI REST API (14 endpoints)
│
├── state_manager/
│   ├── database.py               # GhostNetDatabase + SessionDatabase
│   └── file_system.py            # Isolated VirtualFileSystem per session
│
├── website/                      # Next.js dashboard
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Landing page
│       │   ├── dashboard/page.tsx # Dashboard (5 tabs)
│       │   └── dashboard/[id]/   # Session detail page
│       └── components/            # All UI components
│
└── logs/                         # Auto-created at runtime
    ├── ghostnet.db               # Global tracking DB
    ├── sessions/<id>.db          # One SQLite DB per attacker session
    └── reports/<id>.pdf          # Auto-generated PDF per closed session
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(none)* | Groq API key — required for breadcrumb AI content and threat report generation |
| `SSH_PORT` | `2222` | SSH honeypot port |
| `SSH_HOST` | `0.0.0.0` | SSH bind address |
| `DATABASE_FILE` | `logs/ghostnet.db` | Global SQLite database path |
| `LOG_FILE` | `logs/ghostnet.log` | Main log file |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ENABLE_LATENCY_INJECTION` | `true` | Inject realistic command latency |
| `LATENCY_MS` | `500` | Base latency (ms) |
| `COMMAND_FAILURE_RATE` | `0.05` | Probability of a plausible command failure |
| `GEOIP_DB_PATH` | *(none)* | Optional local MaxMind DB (falls back to `ip-api.com`) |

---

## Tech Stack

| Component | Technology |
|---|---|
| SSH Server | `paramiko >= 3.4.0` |
| REST API | `fastapi` + `uvicorn` |
| AI / LLM | `groq` (LLaMA-3.3-70b-versatile) |
| PDF Reports | `fpdf2` |
| Database | `sqlite3` (stdlib) |
| Crypto | `cryptography >= 41.0.7` |
| Env Config | `python-dotenv` |
| HTTP Client | `requests` |
| Frontend | `Next.js 16` + `React 19` |
| UI Animations | `framer-motion` |
| Charts | `chart.js` + `react-chartjs-2` |
| Maps | `Leaflet` + `react-leaflet` |
| Container | Docker + docker-compose |

---

## Security Notes

> **This system is a decoy.** Do not run alongside production workloads without network isolation.

- Port `2222` (SSH) — expose publicly so real attackers can find it
- Port `8000` (API) and `3000` (dashboard) — firewall from public internet
- `.env` contains your `GROQ_API_KEY` — do not commit to a public repo (already in `.gitignore`)
- Session databases in `logs/sessions/` may contain attacker passwords and commands — protect accordingly

---

<div align="center">

**AeroGhost** — Built for HackNocturne 2026

*"The best trap is one the target walks into willingly."*

</div>
