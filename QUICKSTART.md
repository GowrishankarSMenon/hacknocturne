# GhostNet Quick Start Guide

## Installation (5 minutes)

### 1. Install Dependencies

```bash
cd ghostnet
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Google Gemini API

Create a `.env` file (or update the template):

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your Google Gemini API key
# GEMINI_API_KEY=your-actual-gemini-key-here
```

Get your API key from: https://ai.google.dev/

### 3. Test Installation

```bash
python test_components.py
```

Expected output:
```
✓ SSH Listener
✓ State Manager - Filesystem
✓ State Manager - Database
✓ OS Simulator
✅ All components loaded successfully!
```

---

## Running GhostNet

### Terminal 1: Start SSH Honeypot

```bash
python main.py
```

Output:
```
🎭 GhostNet is now running...
📡 SSH Server listening on 0.0.0.0:2222
🚀 Waiting for attackers...
```

### Terminal 2: Start Intelligence Dashboard

```bash
streamlit run dashboard/app.py
```

Opens browser at: http://localhost:8501

---

## Testing the Honeypot (Manually)

### Option 1: SSH from Another Terminal

```bash
ssh user@localhost -p 2222
# Password: (anything works)
# Type commands:
# > whoami
# > ls
# > pwd
# > exit
```

### Option 2: Using Python SSH Client

```python
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('localhost', port=2222, username='test', password='test')

channel = ssh.invoke_shell()
channel.send('whoami\n')
print(channel.recv(1024).decode())
```

---

## How It Works

### Phase 1: SSH Parrot (Currently Implemented ✓)

1. **SSH Listener** (`ssh_listener/server.py`)
   - Listens on port 2222
   - Accepts any username/password
   - Spawns shell session

2. **OS Simulator** (`agents/os_simulator.py`)
   - Sends command to GPT-4o-mini
   - Receives realistic terminal output
   - Returns response to attacker

3. **Logging** (`state_manager/database.py`)
   - Stores every command
   - Tracks session metadata
   - Records threat events

### Phase 2: Memory Layer (Foundation Ready)

The `VirtualFileSystem` class (`state_manager/file_system.py`) stores the fake filesystem. Next step: integrate with OS Simulator to make responses stateful.

### Phase 3 & 4: Dashboard & Polish

Dashboard (`dashboard/app.py`) already shows:
- Active sessions
- Command feed
- Session details
- Intelligence tabs

---

## Architecture Overview

```
┌─────────────────────────────────┐
│   Attacker (SSH Client)         │
│   ssh user@localhost -p 2222    │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   SSH Server (Paramiko)         │
│   Listens on 0.0.0.0:2222      │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│   Command Handler               │
│   (Routes to AI)                │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌───────────────┐
│Orchestrator │  │OS Simulator   │
│(Intent)     │  │(LLM Response) │
└─────────────┘  └───────────────┘
       │                │
       └───────┬────────┘
               ▼
        ┌─────────────────┐
        │State Manager    │
        │& Database       │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │Streamlit        │
        │Dashboard        │
        └─────────────────┘
```

---

## Common Issues & Fixes

### "GEMINI_API_KEY not set"

```bash
# Check .env exists and has your key
cat .env | grep GEMINI_API_KEY

# Or set environment variable
export GEMINI_API_KEY=your-key-here
```

### "Port 2222 already in use"

```bash
# Find process using port 2222
lsof -i :2222  # macOS/Linux
netstat -ano | findstr :2222  # Windows

# Change port in .env
SSH_PORT=2223
```

### "OpenAI API rate limit"

GPT-4o-mini is cheap but has rate limits:
- 3,500 requests/min for paid accounts
- If hitting limit, add sleep: `time.sleep(0.5)` in command handler

---

## Next Steps (For Phases 2-4)

### Phase 2: Persistent State

Make filesystem state persistent and update OS Simulator:

```python
# In main.py command handler:
# 1. Parse command (touch, mkdir, rm, etc)
# 2. Update filesystem state
# 3. Include state in LLM prompt
# 4. Commands like 'ls' will show files user created
```

### Phase 3: Dashboard Features

Add to dashboard:
- Real-time log streaming
- IP geolocation on map
- Threat level indicators
- Time series attack patterns

### Phase 4: Realism

```python
# Add latency injection
import time
time.sleep(random.uniform(0.2, 1.0))

# Add random failures
if random.random() < 0.05:  # 5% failure rate
    return "command timed out"

# Add believable errors
if command.startswith('sudo'):
    return "[sudo] password for user: access denied"
```

---

## File Structure

```
ghostnet/
├── main.py                    # Main entry point
├── setup.py                   # Setup wizard
├── test_components.py         # Component tests
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .env                      # Your configuration (create this)
├── README.md                 # Project documentation
│
├── ssh_listener/
│   ├── __init__.py
│   └── server.py            # SSH server using Paramiko
│
├── agents/
│   ├── __init__.py
│   ├── os_simulator.py      # LLM-based terminal emulator
│   ├── orchestrator.py      # Intent analyzer (TODO)
│   └── profiler.py          # Attacker profiler (TODO)
│
├── state_manager/
│   ├── __init__.py
│   ├── file_system.py       # Virtual filesystem
│   └── database.py          # SQLite activity logs
│
├── dashboard/
│   ├── __init__.py
│   └── app.py              # Streamlit UI
│
└── logs/                    # Auto-created on first run
    ├── ghostnet.log        # Application logs
    ├── ghostnet.db         # SQLite database
    └── filesystem_state.json # Virtual filesystem state
```

---

## Testing Scenarios

### Scenario 1: Basic Reconnaissance

```bash
ssh attacker@localhost -p 2222
> whoami
> pwd
> ls -la
> cat /etc/passwd
> id
```

### Scenario 2: Privilege Escalation Attempt

```bash
> sudo su
> sudo whoami
> sudo -l
```

### Scenario 3: File Operations

```bash
> touch malware.sh
> echo "payload" > malware.sh
> chmod +x malware.sh
> ls -la
> rm malware.sh
```

---

## Performance Tips

- **Gemini API**: Free tier available with rate limits
- **Latency**: ~1-2 seconds for Gemini responses (slower than GPT-4o-mini but free)
- **Cost**: No cost for free tier, unlimited requests within daily limits
- Cache filesystem state to avoid JSON parsing overhead
- Batch threat intelligence queries (every 5 commands)

---

## Security Considerations

1. **Run in isolated network/VM** - Don't run on production systems
2. **Monitor outbound traffic** - LLM calls go to OpenAI
3. **Log retention** - SQLite logs grow over time
4. **Rate limiting** - LLM APIs have rate limits
5. **No real credentials** - This is a honeypot, not a real system

---

## Getting Help

Check logs:
```bash
tail -f logs/ghostnet.log
```

Test SSH connection:
```bash
ssh -vv user@localhost -p 2222
```

---

**Good luck! 🎭**
