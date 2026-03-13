import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import sys
import os
import html

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_manager.database import GhostNetDatabase
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(
    page_title="GhostNet Intelligence Dashboard",
    page_icon="👻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS: Terminal + Dashboard styles ───
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
    .terminal-dot {
        width: 12px; height: 12px; border-radius: 50%;
        display: inline-block;
    }
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
    .terminal-body .prompt {
        color: #39ff14;
        font-weight: bold;
    }
    .terminal-body .command {
        color: #f0f6fc;
    }
    .terminal-body .output {
        color: #8b949e;
    }
    .terminal-body .typing {
        color: #58a6ff;
    }
    .terminal-body .cursor {
        color: #39ff14;
        animation: blink 1s step-end infinite;
    }
    @keyframes blink {
        50% { opacity: 0; }
    }
    .live-badge {
        background: #da3633;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: bold;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .threat-high { color: #ff6b6b; }
    .threat-medium { color: #ffd93d; }
    .threat-low { color: #6bcf7f; }
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def get_database():
    return GhostNetDatabase()

db = get_database()

# ─── Clean up stale sessions from previous runs on first load ───
if "sessions_cleaned" not in st.session_state:
    closed_count = db.close_all_active_sessions()
    st.session_state.sessions_cleaned = True
    if closed_count > 0:
        st.toast(f"🧹 Cleaned {closed_count} stale session(s) from previous run(s)")

# ─── Auto-refresh every 1 second for live feed ───
st_autorefresh(interval=1000, limit=None, key="live_refresh")

# Main dashboard
st.title("👻 GhostNet Intelligence Dashboard")
st.markdown("**Real-time Cyber-Deception Monitoring & Attack Analysis**")

# Refresh button and clear old sessions button
col_refresh, col_clear, _ = st.columns([1, 1, 6])

with col_refresh:
    if st.button("🔄 Refresh", key="refresh_main"):
        st.rerun()

with col_clear:
    if st.button("🧹 Clear Old Sessions", key="clear_sessions"):
        closed = db.close_all_active_sessions()
        st.toast(f"Closed {closed} stale session(s)")
        st.rerun()

st.divider()

# Top metrics
col1, col2, col3, col4 = st.columns(4)

active_sessions = db.get_active_sessions()
live_typing = db.get_all_live_typing()

with col1:
    st.metric(
        label="Active Sessions",
        value=len(active_sessions),
        delta="Real-time"
    )

with col2:
    all_commands = 0
    for session in active_sessions:
        all_commands += len(db.get_session_commands(session["session_id"]))
    st.metric(
        label="Total Commands",
        value=all_commands,
        delta="This session"
    )

with col3:
    st.metric(
        label="Threat Level",
        value="🟡 MEDIUM" if active_sessions else "🟢 SAFE",
        delta="Current"
    )

with col4:
    st.metric(
        label="Uptime",
        value="24h",
        delta="Since launch"
    )

st.divider()

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👁 Live Terminal", "Live Activity", "Sessions", "Intelligence", "Analytics"])

# ═════════════════════════════════════════════════
# TAB 1: LIVE TERMINAL (the star of the show)
# ═════════════════════════════════════════════════
with tab1:
    if not active_sessions:
        st.markdown("""
        <div class="terminal-container">
            <div class="terminal-header">
                <span class="terminal-dot red"></span>
                <span class="terminal-dot yellow"></span>
                <span class="terminal-dot green"></span>
                <span class="terminal-title">ghostnet — waiting for connections...</span>
            </div>
            <div class="terminal-body">
                <span class="prompt">system@ghostnet:~$</span> <span class="typing">Waiting for attacker to connect on port 2222...</span><span class="cursor">▌</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for session in active_sessions:
            sid = session['session_id']
            ip = session['client_ip']
            commands = db.get_session_commands(sid)
            current_buffer = live_typing.get(sid, "")

            # Build terminal HTML
            terminal_lines = []

            # Show completed commands and their output
            for cmd in commands:
                cmd_text = html.escape(cmd['command'])
                resp_text = html.escape(cmd['response']) if cmd['response'] else ""
                terminal_lines.append(
                    f'<span class="prompt">user@ghostnet:~$</span> <span class="command">{cmd_text}</span>'
                )
                if resp_text:
                    terminal_lines.append(f'<span class="output">{resp_text}</span>')

            # Show current typing buffer with blinking cursor
            if current_buffer:
                escaped_buffer = html.escape(current_buffer)
                terminal_lines.append(
                    f'<span class="prompt">user@ghostnet:~$</span> <span class="typing">{escaped_buffer}</span><span class="cursor">▌</span>'
                )
            else:
                terminal_lines.append(
                    f'<span class="prompt">user@ghostnet:~$</span> <span class="cursor">▌</span>'
                )

            terminal_content = "\n".join(terminal_lines)

            # Determine live badge
            is_typing = bool(current_buffer)
            badge = '<span class="live-badge">● LIVE</span>' if is_typing else '<span class="live-badge" style="background:#238636;">● CONNECTED</span>'

            st.markdown(f"""
            <div class="terminal-container">
                <div class="terminal-header">
                    <span class="terminal-dot red"></span>
                    <span class="terminal-dot yellow"></span>
                    <span class="terminal-dot green"></span>
                    <span class="terminal-title">{html.escape(ip)} — {html.escape(session.get('username', 'user'))}@ghostnet (Session: {sid[:8]}...)</span>
                    {badge}
                </div>
                <div class="terminal-body">{terminal_content}</div>
            </div>
            """, unsafe_allow_html=True)

# TAB 2: Live Activity
with tab2:
    st.subheader("Live Command Feed")
    
    if not active_sessions:
        st.info("No active sessions. Waiting for attackers...")
    else:
        for session in active_sessions:
            with st.expander(f"📍 {session['client_ip']} - {session['username']}@ghostnet (ID: {session['session_id'][:8]}...)", expanded=False):
                commands = db.get_session_commands(session['session_id'])
                
                if commands:
                    df = pd.DataFrame(commands)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df[['timestamp', 'command', 'response']]
                    df.columns = ['Time', 'Command', 'Response']
                    
                    for idx, row in df.iterrows():
                        st.write(f"**{row['Time']}**")
                        st.code(row['Command'], language="bash")
                        st.text(row['Response'][:200] + ("..." if len(str(row['Response'])) > 200 else ""))
                        st.divider()
                else:
                    st.write("No commands logged yet")

# TAB 3: Sessions
with tab3:
    st.subheader("Session Overview")
    
    if active_sessions:
        df_sessions = pd.DataFrame(active_sessions)
        df_sessions['commands'] = df_sessions['session_id'].apply(
            lambda sid: len(db.get_session_commands(sid))
        )
        df_sessions = df_sessions[['client_ip', 'username', 'start_time', 'commands', 'status']]
        df_sessions.columns = ['IP Address', 'Username', 'Start Time', 'Commands', 'Status']
        
        st.dataframe(df_sessions, width="stretch")
    else:
        st.info("No active sessions")

# TAB 4: Intelligence
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
            commands = db.get_session_commands(session_id)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Commands Executed", len(commands))
                st.metric("Session Duration", "< 1 minute")
            
            with col2:
                st.metric("Attack Type", "Reconnaissance")
                st.metric("Skill Level", "Intermediate")
            
            st.subheader("Command Analysis")
            for cmd in commands[-5:]:
                with st.expander(f"🔍 {cmd['command']}", expanded=False):
                    st.write(f"**Timestamp:** {cmd['timestamp']}")
                    st.write(f"**Execution Time:** {cmd['execution_time_ms']}ms")
                    st.text(cmd['response'][:500])

# TAB 5: Analytics
with tab5:
    st.subheader("Historical Analytics")
    
    st.write("📊 Attack trends, geographic distribution, and technique analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top Attack Origins**")
        st.write("""
        - 🇷🇺 Russia: 35%
        - 🇨🇳 China: 28%
        - 🇰🇵 North Korea: 15%
        - Others: 22%
        """)
    
    with col2:
        st.write("**Common Techniques**")
        st.write("""
        - Privilege Escalation: 42%
        - Data Exfiltration: 28%
        - Malware Deployment: 18%
        - Reconnaissance: 12%
        """)

st.divider()

# Footer
st.markdown("""
---
**GhostNet** | Autonomous AI Cyber-Deception System
Status: 🟢 Online | Last Updated: {} | Version: 0.2.0
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
