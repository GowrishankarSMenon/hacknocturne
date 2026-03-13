<br><div align="center">

```
 ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗███╗   ██╗███████╗████████╗
██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝████╗  ██║██╔════╝╚══██╔══╝
██║  ███╗███████║██║   ██║███████╗   ██║   ██╔██╗ ██║█████╗     ██║
██║   ██║██╔══██║██║   ██║╚════██║   ██║   ██║╚██╗██║██╔══╝     ██║
╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   ██║ ╚████║███████╗   ██║
 ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═══╝╚══════╝   ╚═╝
```

**AeroGhost · Autonomous AI Cyber-Deception System v2.0**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/dashboard-streamlit-FF4B4B.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Groq AI](https://img.shields.io/badge/AI-Groq%20LLaMA--3.3--70b-orange.svg)](https://groq.com)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

*A next-generation SSH honeypot that doesn't just trap attackers — it actively deceives them.*

</div>

---

## Why AeroGhost?

AeroGhost is a **free, open-source SSH honeypot** that turns 
your attackers' tools against them. Instead of blocking 
intrusions, it welcomes them into a convincing fake Ubuntu 
server — fingerprinting their tools, watching every command, 
and delivering actionable threat intelligence to your security 
team in real time. Deployable by any IT team in 60 seconds. 
No enterprise budget required.

## What Is GhostNet / AeroGhost?

AeroGhost is an **AI-powered SSH honeypot** that simulates a realistic Ubuntu Linux server. When an attacker connects, instead of blocking them, AeroGhost:

1. **Lets them in** — with a convincing fake Ubuntu 22.04 LTS shell, complete with a real-feeling filesystem.
2. **Watches their every move** — logging every command, keystroke timing, and intent in an isolated per-session SQLite database.
3. **Fingerprints them** — computing SSH HASSH fingerprints during the SSH handshake for cross-IP campaign tracking.
4. **Classifies them** — distinguishing automated bots from human attackers using real-time keystroke timing analysis.
5. **Detects anomalies** — identifying volumetric burst attacks and slow-drip RSA (Random Segment Assessment) scans.
6. **Simulates an internal network** — trapping attackers in endless lateral movement loops within elaborately faked subnets.
7. **Adapts in real time** — planting AI-generated fake "breadcrumb" files tailored to exactly what the attacker is hunting for.
8. **Trips canary wires** — alerting you the instant an attacker opens a planted bait file.
9. **Generates SOC-grade reports** — producing a full PDF report for every closed session, and providing a REST API for SIEM integration.

> **Hackathon Project** built for [HackNocturne 2026] by [@GowrishankarSMenon](https://github.com/GowrishankarSMenon)

---

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                         AEROGHOST SYSTEM v2.0                          │
│                                                                         │
│  ┌──────────────┐    ┌─────────────────────────────────────────────┐   │
│  │  SSH Listener│    │             Main Orchestrator                │   │
│  │  (Paramiko)  │───▶│           GhostNetHoneypot                   │   │
│  │  Port: 2222  │    └────────────────┬────────────────────────────┘   │
│  └──────────────┘                     │                                 │
│                         ┌─────────────┼──────────────┐                 │
│                         ▼             ▼              ▼                  │
│            ┌───────────────────┐ ┌────────────┐ ┌───────────────────┐  │
│            │  Command Handler  │ │ HASSH      │ │  Breadcrumb Agent │  │
│            │  (50+ commands)   │ │ Fingerprint│ │  (AI Deception)   │  │
│            │  Tab Autocomplete │ │ + RSA Det. │ │  Background Thread│  │
│            └─────────┬─────────┘ └────────────┘ └─────────┬─────────┘  │
│                      │                                     │            │
│            ┌─────────▼─────────┐            ┌─────────────▼──────────┐ │
│            │  Virtual FS Tree  │            │  General Intel. Agency  │ │
│            │  (per session)    │            │  (GIA — bg watchdog 5s) │ │
│            └─────────┬─────────┘            └─────────────┬──────────┘ │
│                      │                                     │            │
│            ┌─────────▼─────────────────────────────────────▼──────┐    │
│            │              Per-Session SQLite DB                    │    │
│            │        logs/sessions/<session_id>.db                  │    │
│            └──────────────────────┬────────────────────────────────┘    │
│                                   │                                     │
│            ┌──────────────────────▼──────────────┐                     │
│            │     Streamlit Dashboard (Port 8501)  │                     │
│            │  Live Feed │ Intel │ Geo-Map │ RSA   │                     │
│            └──────────────────────┬───────────────┘                     │
│                                   │                                     │
│            ┌──────────────────────▼──────────────┐                     │
│            │     FastAPI REST API (Port 8000)     │                     │
│            │  /api/sessions │ /api/alerts │ /docs │                     │
│            └──────────────────────┬───────────────┘                     │
│                                   │                                     │
│            ┌──────────────────────▼──────────────┐                     │
│            │  Session Report Generator (PDF)      │                     │
│            │  logs/reports/<session_id>.pdf        │                     │
│            └──────────────────────────────────────┘                     │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Feature Overview

### 🖥️ Realistic SSH Shell

- Simulates **Ubuntu 22.04 LTS** (correct `uname`, `cat /etc/os-release`, `lsb_release`, etc.)
- **50+ working commands**: `ls`, `cd`, `cat`, `grep`, `find`, `ps`, `netstat`, `curl`, `wget`, `history`, `sudo`, `ssh`, `nmap`, `mysql`, `python3`, `pip3`, `git`, `env`, `export`, `chmod`, `chown`, `rm`, `cp`, `mv`, `mkdir`, `touch`, `echo`, `stat`, `df`, `du`, `free`, `uptime`, `whoami`, `id`, `uname`, and more.
- Per-session isolated **virtual filesystem** with realistic directory trees (`Documents`, `Downloads`, `.ssh`, `/etc/passwd`, `/var/log/`, `/home/user/`, etc.).
- Full support for **piped commands**, background jobs, and subshells.
- **MySQL simulator** — `mysql -u root -p` drops the attacker into a convincing MariaDB-style interactive session.
- **Tab autocomplete** — pressing `Tab` in the shell auto-completes commands and filesystem paths based on the session's virtual tree.

### 🕸️ Endless Lateral Movement Trap

AeroGhost contains an **internal network simulator** (`agents/network_sim.py`) that traps attackers attempting to pivot:

- **Fake `nmap` scans** reveal an internal subnet (`10.0.1.x`) with machines like `prod-db-01`, `dev-api-02`, `backup-srv`, `grafana-monitor`, and `staging-web`.
- Attackers can **`ssh` into these fake nodes** directly from the shell prompt.
- Each fake node has its own isolated OS, simulating its role — MySQL databases, Node.js APIs, Grafana dashboards, and backup servers stuffed with fake PII, source code, and configuration secrets.
- The shell prompt dynamically updates per node (e.g., `dbadmin@prod-db-01:~$`).
- The trap is **entirely software-defined** — no secondary containers or VMs needed.

### 🎣 AI-Generated Adaptive Breadcrumbs

The deception engine detects **attacker intent** from executed commands and plants convincing fake files as canary tripwires.

| Intent Detected | Planted File | Contains |
|---|---|---|
| `credential_hunt` | `config.php` / `.env` | Fake DB passwords, API keys |
| `ssh_key_hunt` | `.ssh/id_rsa` | Fake OpenSSH RSA private key |
| `database_hunt` | `.my.cnf` | Fake MySQL root credentials |
| `lateral_movement` | `vpn_connect.sh` | Fake internal VPN script |
| `exfil_prep` | `backup_march2025.tar.gz` | Fake backup manifest |
| `recon` | `network_map.txt` | Fake internal IP map |

- Files are planted **3–10 seconds after** the triggering command (so they look like they were always there).
- Planted files get **realistic timestamps** — 5 to 60 days in the past — so `ls -la` doesn't reveal them as bait.
- Only planted in directories with existing files to preserve plausibility.
- When an attacker opens a planted canary file, a **CRITICAL ALERT** fires and is recorded immediately.

### 🕵️ General Intelligence Agency (GIA)

A background watchdog (`agents/intelligence_agency.py`) that monitors sessions every 5 seconds:

| Check | What It Catches |
|---|---|
| 🌱 **Intent Progression** | Tracks the attacker's kill chain: `recon → credential_hunt → lateral_movement → exfil_prep` |
| 🔍 **Suspicion Scorer** | Detects `ls` spam, timestamp checking (`stat`, `find -newer`), suspicious command bursts |
| ⏰ **Realism Validator** | Validates breadcrumb timestamps remain believable over time |
| 🤖 **Bot Detection** | Flags sessions with suspiciously fast or perfectly uniform inter-command timing |
| 🧹 **Session Integrity** | Identifies and cleans zombie sessions that are stale or disconnected |

### 🤖 Advanced Threat Identification

#### Bot vs. Human Detection (`agents/timing_analyzer.py`)
- Real-time **TimingAnalyzer** records inter-keystroke intervals (IPDs).
- Classifies sessions as `human`, `suspicious`, or `bot` based on statistical variance and average IPD.
- Detects **reconnaissance bursts** — rapid-fire sequences of recon commands (`ls`, `cat /etc/passwd`, `id`, etc.) within a short window.
- Threat events for both bot classification and recon bursts are stored in the per-session DB.

#### HASSH Fingerprinting (`agents/hassh_fingerprinter.py`)
- Computes the **MD5 hash of the SSH client's algorithm preference list** during the handshake.
- Detects known attack tool signatures out-of-the-box: `OpenSSH`, `PuTTY`, `Hydra`, `Nmap`, `Metasploit`, `AsyncSSH`, `Paramiko`, `Masscan-SSH`, `Go SSH`.
- **Cross-IP Correlation**: Automatically flags if the exact same attacker client fingerprint appears from multiple IP addresses — exposing multi-hop VPN or botnet campaigns.

#### Random Segment Assessment (RSA) Detection (`agents/rsa_detector.py`)
- Detects **Volumetric Bursts** (≥10 connections in 30 seconds from one IP).
- Detects **Slow-Drip Attacks** engineered to evade standard rate limits (sequential gaps < 2s).
- Uses a **Similarity Scoring** algorithm (0–100) weighing HASSH matches, inter-connection timing regularity, and username/password repetition.
- Central **Cyber Team Action Panel** in the dashboard lets you: Monitor, Block, Quarantine, or Dismiss active RSA alerts.

### 📄 Automated PDF Session Reports (`agents/report_generator.py`)

When an attacker session closes, a **branded PDF report** is automatically generated at `logs/reports/<session_id>.pdf`. It contains:

- **Session Metadata** — IP address, username, start/end time, duration, HASSH fingerprint.
- **Command Log** — Full timestamped table of all executed commands with execution time (ms) and a `DANGER` flag for high-risk commands (highlighted in red).
- **Detected Intents** — Timeline of attacker intent classification with confidence scores.
- **Canary Tripwires** — All planted breadcrumb files, whether they were triggered, and when.
- **Threat Events** — All GIA and timing alerts, classified by severity (CRITICAL, HIGH, MEDIUM).
- **Threat Score** — An aggregated score (0–100) with a `LOW` / `MEDIUM` / `HIGH` / `CRITICAL` verdict, color-coded by severity.

### 🌐 REST API (`api/server.py`)

A full **FastAPI REST API** runs on port `8000` for SIEM integration, external dashboards, and third-party tooling.

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/sessions` | List all sessions (filterable by `?status=active`) |
| `GET /api/sessions/{id}` | Full session detail including command log |
| `GET /api/sessions/{id}/commands` | All commands for a specific session |
| `GET /api/alerts` | All threat events across all sessions (filterable by `?severity=critical`) |
| `GET /api/stats` | Summary stats: total sessions, unique IPs, top passwords, top SSH clients |
| `GET /api/docs` | Interactive Swagger UI |
| `GET /api/redoc` | ReDoc API documentation |

### 🗺️ Geo-Intelligence Map

- IP geolocation of all connected attackers via `ip-api.com`.
- Interactive **Folium dark map** embedded in the Streamlit dashboard.
- Pulsing red circles with popups showing: city, country, ISP/organization, and live session ID.

### 📊 Streamlit Intelligence Dashboard (Port 8501)

A multi-tab real-time dashboard with auto-refresh:

| Tab | Contents |
|---|---|
| **Live Feed** | Watch attacker keystrokes in real time as they type; shows the live buffer |
| **Session Intel** | Per-session command log, breadcrumbs, canary events, and threat timeline scatter plot |
| **Threat Events** | Aggregated events across all sessions, severity distribution chart |
| **Geo Map** | Folium dark map with attacker IP geolocation |
| **RSA Monitor** | Active RSA (burst/drip) alerts, similarity scores, and the Cyber Team Action Panel |
| **Reports** | Browse and download generated PDF session reports |

---

## Quick Start

### Option A — Local (Python venv)

#### 1. Clone & Setup
```bash
git clone https://github.com/GowrishankarSMenon/hacknocturne.git
cd hacknocturne

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment
```bash
# Windows
copy .env .env.local
# Linux/macOS
cp .env .env.local
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here   # Free at console.groq.com
SSH_PORT=2222
```

> **Note:** `GROQ_API_KEY` is **optional**. Without it, breadcrumbs use offline fallback templates and LLM features are skipped. The full honeypot shell, dashboard, and PDF reports all work without a key.

#### 3. Run All Services (Recommended)

The unified cross-platform launcher starts the SSH honeypot, Streamlit dashboard, and REST API in a single command:

```bash
python run.py          # Start all 3 services
python run.py --no-api # Start without REST API
```

Or manually in separate terminals:
```bash
# Terminal 1 — SSH honeypot server
python main.py

# Terminal 2 — Streamlit dashboard
streamlit run dashboard/app.py

# Terminal 3 — FastAPI REST API (optional)
uvicorn api.server:app --host 0.0.0.0 --port 8000
```

**Windows convenience scripts:**
```cmd
start.bat   # Starts SSH server + Dashboard
stop.bat    # Kills both processes
```

#### 4. Connect as an Attacker (Testing)
```bash
ssh user@localhost -p 2222
# Password: anything — all passwords accepted
```

Then open your browser:
- **Dashboard**: [http://localhost:8501](http://localhost:8501)
- **REST API docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

---

### Option B — Docker (Recommended for Production)

Docker **is fully implemented**. A `Dockerfile` and `docker-compose.yml` are both included. The container runs all three services (`main.py`, Streamlit, FastAPI) via `run.py`.

#### Using Docker Compose (easiest)
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The compose file:
- Exposes ports `2222` (SSH), `8501` (dashboard), `8000` (REST API).
- Reads `GROQ_API_KEY` from your host `.env` file automatically.
- Mounts named volumes `aeroghost-logs` and `aeroghost-data` so logs and session databases persist across restarts.
- Restarts the container automatically unless you stop it manually (`restart: unless-stopped`).
- Runs a **health check** every 30 seconds (pings port 2222).

#### Using Docker directly
```bash
# Build the image
docker build -t aeroghost .

# Run the container
docker run -d \
  --name aeroghost-honeypot \
  -p 2222:2222 \
  -p 8501:8501 \
  -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  -v aeroghost-logs:/app/logs \
  aeroghost
```

> **Security Note:** When deploying publicly, consider binding the dashboard and REST API to `localhost` only and using a reverse proxy (nginx/Caddy) with authentication. The SSH port `2222` should be publicly accessible for the honeypot to function.

---

## Project Structure

```
ghostnet/
│
├── main.py                       # Main orchestrator — wires all components together
├── run.py                        # Cross-platform unified launcher (Windows/Linux/macOS)
├── setup.py                      # Environment setup helper
├── rsa_tester.py                 # Utility: test Burst & Slow-Drip RSA attack detection
├── test_components.py            # Component initialization tests
├── test_filesystem.py            # VirtualFileSystem unit tests
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Docker Compose (single-command deployment)
├── start.bat / stop.bat          # Windows convenience launchers
│
├── agents/
│   ├── command_handler.py        # 50+ shell command simulations + tab autocomplete
│   ├── breadcrumbs.py            # AI deception engine (intent detection → fake file generation)
│   ├── intelligence_agency.py    # GIA background watchdog (5s monitoring loop)
│   ├── geo_lookup.py             # IP geolocation via ip-api.com
│   ├── os_simulator.py           # Groq-powered fallback AI response (Orchestrator + Profiler)
│   ├── rsa_detector.py           # RSA anomaly detection (burst + slow-drip + similarity scoring)
│   ├── hassh_fingerprinter.py    # SSH HASSH fingerprinting + cross-IP correlation
│   ├── timing_analyzer.py        # Bot vs. human keystroke timing classification
│   ├── network_sim.py            # Fake internal subnet simulator for lateral movement trapping
│   ├── report_generator.py       # Automatic PDF session report generation (fpdf2)
│   └── ddos_detector.py          # DDoS / high-rate connection detection
│
├── ssh_listener/
│   └── server.py                 # Paramiko SSH server (AeroGhostSSHServer)
│                                 # Handles: auth, HASSH capture, Tab autocomplete, live feed
│
├── api/
│   └── server.py                 # FastAPI REST API (7 endpoints + Swagger UI)
│
├── state_manager/
│   ├── database.py               # GhostNetDatabase (global) + SessionDatabase (per-session)
│   └── file_system.py            # Isolated VirtualFileSystem + FSNode tree
│
├── dashboard/
│   └── app.py                    # Streamlit dashboard (multi-tab intelligence UI)
│
└── logs/                         # Auto-created at runtime
    ├── ghostnet.log              # Main system log
    ├── ghostnet.db               # Global tracking DB (sessions index, HASSH, RSA state)
    ├── sessions/
    │   └── <session_id>.db       # One isolated SQLite DB per attacker session
    └── reports/
        └── <session_id>.pdf      # Auto-generated PDF reports for closed sessions
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(none)* | Groq API key for AI features (breadcrumbs, LLM responses). Optional. |
| `SSH_PORT` | `2222` | Port the SSH honeypot listens on |
| `SSH_HOST` | `0.0.0.0` | Bind address for the SSH server |
| `DATABASE_FILE` | `logs/ghostnet.db` | Path to the global SQLite database |
| `LOG_FILE` | `logs/ghostnet.log` | Path to the main log file |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`) |
| `ENABLE_LATENCY_INJECTION` | `true` | Inject realistic command latency to fool timing analysis tools |
| `LATENCY_MS` | `500` | Base latency in milliseconds (randomized around this value) |
| `COMMAND_FAILURE_RATE` | `0.05` | Probability (0–1) of a command returning a plausible failure message |
| `GEOIP_DB_PATH` | *(none)* | Optional local MaxMind GeoIP database path (falls back to `ip-api.com` if not set) |

---

## Key Design Decisions

### Per-Session SQLite Isolation
Each attacker gets **their own SQLite database** at `logs/sessions/<session_id>.db`. This prevents cross-session data leakage, eliminates write-lock contention under concurrent sessions, and means sessions can be analysed in full isolation. Global data (HASSH records, RSA alerts, session index) lives in `logs/ghostnet.db`.

### Async Breadcrumb Pipeline
The entire intent-detection → file-generation → planting pipeline runs in a **daemon background thread** per command, with a random 3–10 second delay. This ensures the attacker's terminal feels instant and planted files don't appear suspiciously fast relative to the triggering command.

### Local Network Inception
The fake lateral movement network is **entirely software-simulated** inside `command_handler.py`'s `node_stack`. AeroGhost can present the attacker with multiple believable "machines" to pivot through without deploying a single container, VM, or network namespace.

### Graceful Degradation
The entire system degrades gracefully when `GROQ_API_KEY` is absent. The SSH shell, virtual filesystem, bot detection, HASSH fingerprinting, RSA detection, canary system, PDF reports, REST API, and dashboard all function fully offline. AI-powered features (LLM-generated breadcrumb content, OS simulator fallback responses) are simply skipped or replaced with pre-written templates.

### PDF Report Auto-Generation
When a session closes (either via `exit`/`quit` or a disconnect), `SessionReportGenerator.generate()` is called synchronously before the session is deleted from memory, ensuring no data is lost even on abrupt disconnects. Reports are saved to `logs/reports/`.

---

## Tech Stack

| Component | Technology |
|---|---|
| SSH Server | `paramiko >= 3.4.0` |
| REST API | `fastapi >= 0.104.0` + `uvicorn >= 0.24.0` |
| AI / LLM | `groq >= 0.4.0` (LLaMA-3.3-70b-versatile) |
| Dashboard | `streamlit >= 1.28.0` + `streamlit-autorefresh` |
| Visualizations | `plotly >= 5.18.0` |
| Geo Map | `folium >= 0.15.0` + `streamlit-folium >= 0.22.0` |
| PDF Reports | `fpdf2 >= 2.7.0` |
| Database | `sqlite3` (stdlib — zero external DB dependency) |
| Crypto | `cryptography >= 41.0.7` |
| Env Config | `python-dotenv >= 1.0.0` |
| HTTP Client | `requests >= 2.31.0` |
| Container | `Docker` + `docker-compose` (v3.9) |

---

## Testing & Utilities

### Component Tests
```bash
# Verify all core components initialize correctly
python test_components.py
# Expected output: All components passed ✓

# Test VirtualFileSystem: path resolution, dotfiles, permissions
python test_filesystem.py
```

### RSA Attack Simulation
Test the RSA detector's burst and slow-drip detection:
```bash
# Simulate a volumetric connection burst (≥10 connections in 30s)
python rsa_tester.py burst

# Simulate a slow-drip evasion attack (connections spaced < 2s apart)
python rsa_tester.py drip
```

---

## Security Considerations

> **This system is designed to be deployed as a decoy.** Do not run it on a machine with sensitive data or alongside production workloads without proper network isolation.

- **Port 2222** should be publicly exposed so real attackers can find and connect to the honeypot.
- **Port 8501** (dashboard) and **Port 8000** (REST API) should be firewalled from public internet access. Use a VPN or reverse proxy with authentication.
- The `.env` file contains your `GROQ_API_KEY` — do not commit it to a public repository (it is already in `.gitignore`).
- All attacker passwords are accepted by design. Do not run on a port that real services use.
- Session databases in `logs/sessions/` may contain sensitive attacker-provided data (passwords attempted, commands run). Protect this directory accordingly.

---

<div align="center">

**AeroGhost** — Built for HackNocturne 2026

*"The best trap is one the target walks into willingly."*

</div>
