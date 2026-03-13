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

## What Is GhostNet/AeroGhost?

AeroGhost is an **AI-powered SSH honeypot** that simulates a realistic Ubuntu Linux server. When an attacker connects, instead of blocking them, AeroGhost:

1. **Lets them in** — with a convincing fake Ubuntu shell.
2. **Watches their every move** — logging commands, keystroke timings, and detecting intent.
3. **Fingerprints them** — computing SSH HASSH fingerprints for cross-IP campaign tracking.
4. **Detects anomalies** — identifying Random Segment Assessment attempts (burst & slow-drip) and automated bots vs. human typists.
5. **Adapts in real-time** — planting fake "breadcrumb" files tailored to what the attacker is hunting for.
6. **Trips canary wires** — alerting you instantly when the attacker interacts with planted bait.
7. **Generates actionable intelligence** — providing interactive dashboards, threat reports, geo-maps, and attack timelines.

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
│                          ┌──────────┼──────────┐                  │
│                          ▼          ▼          ▼                  │
│              ┌─────────────────┐ ┌─────────┐ ┌──────────────────┐ │
│              │ Command Handler │ │ Random Segment Assessment &  │ │ Breadcrumb Agent │ │
│              │ (50+ commands)  │ │ HASSH   │ │ (AI Deception)   │ │
│              └────────┬────────┘ └─────────┘ └────────┬─────────┘ │
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
- Simulates **Ubuntu 22.04 LTS** (`uname`, `cat /etc/os-release`).
- 50+ working commands: `ls`, `cd`, `cat`, `grep`, `find`, `ps`, `netstat`, `curl`, `wget`, `history`, `sudo`, `ssh`, and more.
- Per-session isolated **virtual filesystem** with realistic directory trees (`Documents`, `Downloads`, `.ssh`, `/etc/passwd`, `/var/log/`, etc.).
- Fully functional piped commands, background jobs, and subshells.

### 🎣 AI-Generated Adaptive Breadcrumbs
The core deception engine detects **attacker intent** and plants convincing fake files as canary tripwires:

| Intent Detected | Planted File | Contains |
|---|---|---|
| `credential_hunt` | `config.php` | Fake DB passwords, API keys |
| `ssh_key_hunt` | `.ssh/id_rsa` | Fake OpenSSH private key |
| `database_hunt` | `.my.cnf` | Fake MySQL root credentials |
| `lateral_movement` | `vpn_connect.sh` | Fake internal VPN script |
| `exfil_prep` | `backup_march2025.tar.gz` | Fake backup manifest |

Files are planted **3–10 seconds after** the triggering command (so they look like they were always there) with realistic timestamps (5–60 days old). When the attacker opens a planted file, a **CRITICAL ALERT** fires.

### 🕵️ General Intelligence Agency (GIA)
A background watchdog that monitors sessions every 5 seconds for anomalies:

| Check | What It Catches |
|---|---|
| 🌱 **Intent Progression** | Follows the attacker's path from recon to exfil |
| 🔍 **Suspicion Scorer** | Detects `ls` spam, timestamp checking (`stat`, `find -newer`) |
| ⏰ **Realism Validator** | Ensures breadcrumb files don't have unrealistic, too-recent timestamps |
| 🧹 **Session Integrity** | Identifies and cleans zombie sessions |

### 🤖 Advanced Threat Identification

#### Bot vs. Human Detection
- Real-time **TimingAnalyzer** evaluates keystroke latency to distinguish between automated scripts and human typists.
- Fast, mathematically precise detection of scanning tools and bruteforce scripts.

#### HASSH Fingerprinting
- Computes MD5 hash of SSH client algorithm preferences during the handshake.
- Detects known attack tools out-of-the-box (OpenSSH, PuTTY, Hydra, Nmap, Go SSH).
- **Cross-IP Correlation:** Automatically flags if the exact same attacker client tries to connect from multiple IP addresses.

#### Random Segment Assessment Detection & Triage
- Detects **Volumetric Bursts** (e.g., ≥10 connections in 30 seconds).
- Detects **Slow-Drip Attacks** designed to evade standard rate limits (e.g., sequential gaps < 2s).
- Employs a complex **Similarity Scoring** algorithm (0-100) weighing HASSH matches, timing regularity, and username repetition.
- Central **Cyber Team Action Panel** in the dashboard allows you to Monitor, Block, Quarantine, or Dismiss active attacks.

### 🗺️ Geo-Intelligence Map
- IP geolocation of connected attackers via `ip-api.com`.
- Interactive **Folium dark map** with living metrics.
- Pulsing red circles + popup with city, ISP, organization, and live session IDs.

### 📊 Comprehensive Dashboard & Reporting
- **Live Terminal & Keystrokes:** Watch the attackers type in real time.
- **Timeline Scatter-Plot:** Visualize commands categorized as Dangerous (red) or Benign (green).
- **Threat Score Engine:** Computes an aggregated Threat Score per session (0–100) using command volume, payload danger, and duration.
- **Automated Threat Reports:** Gathers session data and queries Groq's LLM to generate a plain-English, SOC-ready summary of the attack.

---

## Quick Start

### 1. Clone & Setup
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

### 2. Configure Environment
```bash
# Copy the example .env
cp .env.example .env   # Linux/macOS
copy .env.example .env # Windows
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key_here   # Get free at console.groq.com
SSH_PORT=2222
```

> **Note:** `GROQ_API_KEY` is optional. Without it, breadcrumbs use fallback templates and threat reports are unavailable. Everything else works fully.

### 3. Run the System
```bash
# Terminal 1 — SSH server
python main.py

# Terminal 2 — Dashboard
streamlit run dashboard/app.py
```

Or use the provided batch files (Windows):
```cmd
start.bat   # Starts both
stop.bat    # Kills both
```

### 4. Connect as an Attacker (Testing)
```bash
ssh user@localhost -p 2222
# Password: anything (all passwords accepted)
```

You can also use the included Random Segment Assessment testing tool to test defense triggers:
```bash
python rsa_tester.py burst
python rsa_tester.py drip
```

---

## Project Structure

```
ghostnet/
│
├── main.py                     # Main orchestrator — wires everything together
├── rsa_tester.py              # Utility for testing Burst & Slow-Drip Random Segment Assessment attacks
├── requirements.txt            # Python dependencies
├── start.bat / stop.bat        # Windows convenience launchers
│
├── agents/
│   ├── command_handler.py      # 50+ shell command simulations
│   ├── breadcrumbs.py          # AI deception engine (intent → fake files)
│   ├── intelligence_agency.py  # GIA background watchdog
│   ├── geo_lookup.py           # IP geolocation via ip-api.com
│   ├── os_simulator.py         # Groq-powered AI response fallback
│   ├── rsa_detector.py        # Anomaly detection for bursts & slow-drips
│   ├── hassh_fingerprinter.py  # SSH fingerprinting & cross-IP tracking
│   └── timing_analyzer.py      # Bot vs human keystroke pattern analysis
│
├── ssh_listener/
│   └── server.py               # Paramiko SSH server (AeroGhostSSHServer)
│
├── state_manager/
│   ├── database.py             # Global indexing, real-time metrics, HASSH/Random Segment Assessment state
│   └── file_system.py          # Isolated VirtualFileSystem tree (FSNode)
│
├── dashboard/
│   └── app.py                  # Extensive Streamlit dashboard (6 tabs)
│
└── logs/
    ├── ghostnet.log            # Main system log
    ├── ghostnet.db             # Global tracking DB
    └── sessions/
        └── <session_id>.db     # Per-session isolated databases
```

---

## Key Design Decisions

### Per-Session SQLite Isolation
Each attacker gets **their own SQLite database** at `logs/sessions/<session_id>.db`. This prevents cross-session data leakage and race conditions. Global data (HASSH, RSA Alerts) remains in `logs/ghostnet.db`.

### Async Breadcrumb Pipeline
The deception pipeline runs in a **background thread** with a 3–10 second delay so the attacker's terminal feels instant and files don't appear suspiciously fast.

### Security and Fingerprinting First
By tracking the exact fingerprint (HASSH) of the SSH negotiation before the shell even spawns, AeroGhost correlates tools and actors even if they hide behind different proxies and IP spaces.

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

---

## Testing

Run component tests to ensure everything is initialized correctly:
```bash
python test_components.py
# Expected: All components passed

python test_filesystem.py
# Tests VirtualFileSystem, dotfiles, path resolution
```

---

<div align="center">

**AeroGhost** — Built for HackNocturne 2026

*"The best trap is one the target walks into willingly."*

</div>
