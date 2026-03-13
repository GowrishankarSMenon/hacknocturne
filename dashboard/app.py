import streamlit as st
import pandas as pd
import json
import os
import html
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_manager.database import GhostNetDatabase, SessionDatabase
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(
    page_title="AeroGhost Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    .terminal-container {
        background: #0d1117;
        border: 1px solid #30363d;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 16px;
    }
    .terminal-header {
        background: #161b22;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid #30363d;
    }
    .terminal-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }
    .terminal-title {
        color: #8b949e;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin-left: 8px;
    }
    .terminal-body {
        padding: 16px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: #c9d1d9;
        max-height: 500px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .terminal-body .prompt { color: #39ff14; font-weight: bold; }
    .terminal-body .command { color: #f0f6fc; }
    .terminal-body .output { color: #8b949e; }
    .terminal-body .typing { color: #58a6ff; }
    .terminal-body .cursor { color: #39ff14; animation: blink 1s step-end infinite; }
    @keyframes blink { 50% { opacity: 0; } }
    .live-badge {
        background: #da3633; color: white;
        padding: 2px 8px; border-radius: 10px;
        font-size: 11px; font-weight: bold;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .metric-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px;
        border-radius: 10px;
        padding: 16px 20px;
        color: white;
        margin-bottom: 16px;
        animation: alertPulse 1.5s ease-in-out infinite;
    }
    @keyframes alertPulse {
        0%, 100% { box-shadow: 0 0 5px rgba(218, 54, 51, 0.5); }
        50% { box-shadow: 0 0 20px rgba(218, 54, 51, 0.9); }
    }
    .critical-alert h3 { margin: 0 0 8px 0; font-size: 16px; }
    .critical-alert .detail { opacity: 0.9; font-size: 13px; }
    .intent-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px 4px;
    }
    .intent-credential_hunt { background: #da3633; color: white; }
    .intent-ssh_key_hunt { background: #d29922; color: black; }
    .intent-database_hunt { background: #8957e5; color: white; }
    .intent-lateral_movement { background: #f85149; color: white; }
    .intent-exfil_prep { background: #388bfd; color: white; }
    .intent-none { background: #30363d; color: #8b949e; }
    .threat-report {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        color: #c9d1d9;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize databases
@st.cache_resource
def get_database():
    return GhostNetDatabase()

db = get_database()

# Clean stale sessions on first load
if "sessions_cleaned" not in st.session_state:
    closed_count = db.close_all_active_sessions()
    st.session_state.sessions_cleaned = True
    if closed_count > 0:
        st.toast(f"🧹 Cleaned {closed_count} stale session(s)")

# Auto-refresh every 1 second
st_autorefresh(interval=1000, limit=None, key="live_refresh")

# Main dashboard
st.title("AeroGhost Intelligence Dashboard")
st.markdown("**Real-time Cyber-Deception Monitoring & Attack Analysis**")

col_refresh, col_clear, _ = st.columns([1, 1, 6])
with col_refresh:
    if st.button("Refresh", key="refresh_main"):
        st.rerun()
with col_clear:
    if st.button("Clear Old Sessions", key="clear_sessions"):
        closed = db.close_all_active_sessions()
        st.toast(f"Closed {closed} stale session(s)")
        st.rerun()

st.divider()

# ─── Gather session data ───
active_sessions = db.get_active_sessions()
live_typing = db.get_all_live_typing()

# Load per-session databases for active sessions
session_dbs = {}
for s in active_sessions:
    sid = s['session_id']
    db_path = os.path.join("logs", "sessions", f"{sid}.db")
    if os.path.exists(db_path):
        session_dbs[sid] = SessionDatabase(sid)

# ─── Check for critical alerts ───
all_canary_events = []
for sid, sdb in session_dbs.items():
    events = sdb.get_canary_events()
    for e in events:
        e['session_id'] = sid
        all_canary_events.append(e)

# Show critical alert banner at the very top
if all_canary_events:
    for event in all_canary_events[:3]:
        st.markdown(f"""
        <div class="critical-alert">
            <h3>🚨 CRITICAL — Canary Tripwire Triggered</h3>
            <div class="detail"><b>Session:</b> {html.escape(str(event.get('session_id', ''))[:12])}...</div>
            <div class="detail"><b>File:</b> {html.escape(str(event.get('filepath', 'unknown')))}</div>
            <div class="detail"><b>Revealed Intent:</b> {html.escape(str(event.get('intent', 'unknown')).replace('_', ' ').title())}</div>
            <div class="detail"><b>Time:</b> {html.escape(str(event.get('triggered_at', 'unknown')))}</div>
        </div>
        """, unsafe_allow_html=True)

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Sessions", len(active_sessions), delta="Real-time")
with col2:
    total_cmds = sum(len(sdb.get_commands()) for sdb in session_dbs.values())
    st.metric("Total Commands", total_cmds)
with col3:
    threat = "🔴 CRITICAL" if all_canary_events else ("🟡 MEDIUM" if active_sessions else "🟢 SAFE")
    st.metric("Threat Level", threat)
with col4:
    total_canaries = sum(len(sdb.get_all_canaries()) for sdb in session_dbs.values())
    st.metric("Canaries Planted", total_canaries)

st.divider()

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Live Terminal", "Live Activity", "Sessions", "Intelligence", "Analytics"])

# ═══════════════════════════════════════
# TAB 1: LIVE TERMINAL
# ═══════════════════════════════════════
with tab1:
    if not active_sessions:
        st.markdown("""
        <div class="terminal-container">
            <div class="terminal-header">
                <span class="terminal-dot red"></span>
                <span class="terminal-dot yellow"></span>
                <span class="terminal-dot green"></span>
                <span class="terminal-title">aeroghost — waiting for connections...</span>
            </div>
            <div class="terminal-body">
                <span class="prompt">system@aeroghost:~$</span> <span class="typing">Waiting for attacker to connect on port 2222...</span><span class="cursor">▌</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for session in active_sessions:
            sid = session['session_id']
            ip = session['client_ip']
            sdb = session_dbs.get(sid)
            commands = sdb.get_commands() if sdb else []
            current_buffer = live_typing.get(sid, "")

            # Get intents for this session
            intents = sdb.get_intents() if sdb else []
            latest_intent = intents[-1]['intent_type'] if intents else "none"

            terminal_lines = []
            for cmd in commands:
                cmd_text = html.escape(cmd['command'])
                resp_text = html.escape(cmd['response']) if cmd['response'] else ""
                terminal_lines.append(
                    f'<span class="prompt">user@aeroghost:~$</span> <span class="command">{cmd_text}</span>'
                )
                if resp_text:
                    terminal_lines.append(f'<span class="output">{resp_text}</span>')

            if current_buffer:
                escaped_buffer = html.escape(current_buffer)
                terminal_lines.append(
                    f'<span class="prompt">user@aeroghost:~$</span> <span class="typing">{escaped_buffer}</span><span class="cursor">▌</span>'
                )
            else:
                terminal_lines.append(
                    f'<span class="prompt">user@aeroghost:~$</span> <span class="cursor">▌</span>'
                )

            terminal_content = "\n".join(terminal_lines)

            is_typing = bool(current_buffer)
            badge = '<span class="live-badge">● LIVE</span>' if is_typing else '<span class="live-badge" style="background:#238636;">● CONNECTED</span>'
            intent_badge = f'<span class="intent-badge intent-{latest_intent}">{latest_intent.replace("_", " ").title()}</span>' if latest_intent != "none" else ""

            st.markdown(f"""
            <div class="terminal-container">
                <div class="terminal-header">
                    <span class="terminal-dot red"></span>
                    <span class="terminal-dot yellow"></span>
                    <span class="terminal-dot green"></span>
                    <span class="terminal-title">{html.escape(ip)} — {html.escape(session.get('username', 'user'))}@aeroghost (Session: {sid[:8]}...)</span>
                    {badge}
                </div>
                <div class="terminal-body">{terminal_content}</div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════
# TAB 2: INTELLIGENCE
# ═══════════════════════════════════════
with tab2:
    st.subheader("🧠 Attack Intelligence")

    if not active_sessions:
        st.info("No active sessions")
    else:
        for session in active_sessions:
            sid = session['session_id']
            sdb = session_dbs.get(sid)
            with st.expander(f"{session['client_ip']} - {session['username']}@aeroghost (ID: {sid[:8]}...)", expanded=False):
                commands = sdb.get_commands() if sdb else []
                
                if commands:
                    for cmd in commands:
                        st.write(f"**{cmd['timestamp']}**")
                        st.code(cmd['command'], language="bash")
                        resp = str(cmd.get('response', ''))
                        st.text(resp[:200] + ("..." if len(resp) > 200 else ""))
                        st.divider()
                else:
                    st.write("No commands logged yet")

# ═══════════════════════════════════════
# TAB 3: SESSIONS
# ═══════════════════════════════════════
with tab3:
    st.subheader("Session Overview")
    if active_sessions:
        rows = []
        for s in active_sessions:
            sid = s['session_id']
            sdb = session_dbs.get(sid)
            cmd_count = len(sdb.get_commands()) if sdb else 0
            canary_count = len(sdb.get_canary_events()) if sdb else 0
            rows.append({
                "IP": s['client_ip'],
                "User": s.get('username', 'user'),
                "Start": s['start_time'],
                "Commands": cmd_count,
                "Canaries Hit": canary_count,
                "Status": s['status']
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No active sessions")

# ═══════════════════════════════════════
# TAB 4: ANALYTICS
# ═══════════════════════════════════════
with tab4:
    st.subheader("Attack Intelligence")
    
    if active_sessions:
        selected_session = st.selectbox(
            "Select Session",
            [f"{s['client_ip']} ({s['username']})" for s in active_sessions],
            key="session_select"
        )
        
        selected_ip = selected_session.split()[0]
        selected_session_obj = next((s for s in active_sessions if s['client_ip'] == selected_ip), None)
        
        if selected_session_obj:
            session_id = selected_session_obj['session_id']
            sdb = session_dbs.get(session_id)
            commands = sdb.get_commands() if sdb else []
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Commands Executed", len(commands))
                st.metric("Session Duration", "< 1 minute")
            
            with col2:
                st.metric("Attack Type", "Reconnaissance")
                st.metric("Skill Level", "Intermediate")
            
            st.subheader("Command Analysis")
            for cmd in commands[-5:]:
                with st.expander(f"{cmd['command']}", expanded=False):
                    st.write(f"**Timestamp:** {cmd['timestamp']}")
                    st.write(f"**Execution Time:** {cmd.get('execution_time_ms', 0)}ms")
                    st.text(str(cmd.get('response', ''))[:500])

# TAB 5: Analytics
with tab5:
    st.subheader("Historical Analytics")
    
    st.write("Attack trends, geographic distribution, and technique analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Top Attack Origins**")
        st.write("- 🇷🇺 Russia: 35%\n- 🇨🇳 China: 28%\n- 🇰🇵 North Korea: 15%\n- Others: 22%")
    with col2:
        st.write("**Common Techniques**")
        st.write("- Privilege Escalation: 42%\n- Data Exfiltration: 28%\n- Malware Deployment: 18%\n- Reconnaissance: 12%")

st.divider()
st.markdown("""
---
**AeroGhost** | Autonomous AI Cyber-Deception System
Status: Online | Last Updated: {} | Version: 0.2.0
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))


# ─── Helper: Groq Threat Report Generation ───
def _generate_threat_report(report_data: dict, session: dict) -> str:
    """Generate a full threat report using Groq."""
    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        client = Groq(api_key=api_key)

        # Build prompt
        commands_text = "\n".join([f"  [{c['timestamp']}] {c['command']}" for c in report_data['commands'][-20:]])
        intents_text = "\n".join([f"  - {i['intent_type']} (confidence: {i['confidence']}, trigger: {i['trigger_command']})" for i in report_data['intents']])
        canaries_text = "\n".join([f"  - {c['filepath']} (intent: {c['intent']}, triggered: {bool(c['triggered'])})" for c in report_data['canaries']])

        prompt = f"""Generate a concise Threat Intelligence Report in markdown for this honeypot session:

Session ID: {report_data['session_id']}
Attacker IP: {session.get('client_ip', 'unknown')}

Commands executed:
{commands_text}

Intent detections:
{intents_text if intents_text else '  None detected'}

Canary files:
{canaries_text if canaries_text else '  None planted'}

Generate a professional report with:
1. Executive Summary (2-3 sentences)
2. Intent Progression (numbered list)
3. Canary Tripwire Results
4. Risk Assessment (LOW/MEDIUM/HIGH/CRITICAL)
5. Recommended Actions (bullet list)

Keep it concise. Use markdown formatting."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=800
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating report: {e}"
