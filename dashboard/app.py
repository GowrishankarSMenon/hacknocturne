import streamlit as st
import pandas as pd
import json
import os
import html
import sys
import math
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state_manager.database import GhostNetDatabase, SessionDatabase
from streamlit_autorefresh import st_autorefresh
from agents.geo_lookup import lookup_ip
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px

# ─── Threat Score Engine ───
DANGEROUS_KEYWORDS = [
    "sudo", "su ", "passwd", "shadow", "wget", "curl", "nc ", "ncat",
    "nmap", "chmod", "rm -rf", "rm -r", "mkfifo", "bash -i",
    "/etc/passwd", "/etc/shadow", ".ssh", "id_rsa", "authorized_keys",
    "iptables", "crontab", "base64", "python -c", "perl -e",
    "netcat", "reverse", "bind", "exploit", "payload",
]

def compute_threat_score(commands: list) -> int:
    """Compute a 0-100 threat score from a list of command dicts."""
    if not commands:
        return 0
    score = 0
    score += min(len(commands) * 2, 20)  # Volume: up to 20 pts
    dangerous_count = 0
    for cmd in commands:
        cmd_text = cmd.get('command', '').lower()
        for kw in DANGEROUS_KEYWORDS:
            if kw in cmd_text:
                dangerous_count += 1
                break
    score += min(dangerous_count * 10, 60)  # Danger keywords: up to 60 pts
    # Session duration bonus
    if len(commands) >= 10:
        score += 10
    if len(commands) >= 20:
        score += 10
    return min(score, 100)

def threat_color(score: int) -> str:
    if score <= 30:
        return "#27c93f"  # green
    elif score <= 60:
        return "#ffbd2e"  # yellow
    elif score <= 80:
        return "#f97316"  # orange
    else:
        return "#ef4444"  # red

def threat_label(score: int) -> str:
    if score <= 30:
        return "LOW"
    elif score <= 60:
        return "MEDIUM"
    elif score <= 80:
        return "HIGH"
    else:
        return "CRITICAL"

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

# ─── Aggregate all commands for threat scoring ───
all_commands_flat = []
for sdb in session_dbs.values():
    all_commands_flat.extend(sdb.get_commands())
total_cmds = len(all_commands_flat)
global_threat_score = compute_threat_score(all_commands_flat)

# Top metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Sessions", len(active_sessions), delta="Real-time")
with col2:
    st.metric("Total Commands", total_cmds)
with col3:
    t_label = threat_label(global_threat_score)
    t_color = threat_color(global_threat_score)
    st.metric("Threat Score", f"{global_threat_score}/100 ({t_label})")
with col4:
    total_canaries = sum(len(sdb.get_all_canaries()) for sdb in session_dbs.values())
    st.metric("Canaries Planted", total_canaries)

st.divider()

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Live Terminal", "Live Activity", "Sessions", "Intelligence", "Geo-Intelligence", "Analytics"])

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

# TAB 4: INTELLIGENCE (Threat Score + Timeline + GIA Monitoring)
# ═══════════════════════════════════════
with tab4:
    st.subheader("Attack Intelligence & GIA Monitoring")

    if not active_sessions:
        st.info("No active sessions — intelligence will populate when an attacker connects")
    else:
        selected_session = st.selectbox(
            "Select Session",
            [f"{s['client_ip']} ({s['username']})" for s in active_sessions],
            key="session_select"
        )

        selected_ip = selected_session.split()[0]
        selected_session_obj = next((s for s in active_sessions if s['client_ip'] == selected_ip), None)

        if selected_session_obj:
            sid = selected_session_obj['session_id']
            sdb = session_dbs.get(sid)
            commands = sdb.get_commands() if sdb else []
            intents = sdb.get_intents() if sdb else []
            canaries = sdb.get_all_canaries() if sdb else []
            triggered = sdb.get_canary_events() if sdb else []
            threat_events = sdb.get_threat_events() if sdb else []

            # ─── Top Metrics Row ───
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Commands", len(commands))
            c2.metric("Intents Detected", len(intents))
            c3.metric("Canaries Planted", len(canaries))
            c4.metric("Canaries Triggered", len(triggered))

            # ─── Threat Score Gauge ───
            session_score = compute_threat_score(commands)
            s_color = threat_color(session_score)
            s_label = threat_label(session_score)

            st.markdown("#### Threat Score")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=session_score,
                title={"text": f"Session Threat Level: {s_label}"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": s_color},
                    "steps": [
                        {"range": [0, 30], "color": "#1a2e1a"},
                        {"range": [30, 60], "color": "#2e2a1a"},
                        {"range": [60, 80], "color": "#2e1e1a"},
                        {"range": [80, 100], "color": "#2e1a1a"},
                    ],
                    "threshold": {
                        "line": {"color": "white", "width": 2},
                        "thickness": 0.8,
                        "value": session_score,
                    },
                },
            ))
            fig_gauge.update_layout(
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#c9d1d9"},
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # ─── Command Timeline ───
            if commands:
                st.markdown("#### Command Timeline")
                timeline_data = []
                for cmd in commands:
                    cmd_text = cmd.get('command', '')
                    is_dangerous = any(kw in cmd_text.lower() for kw in DANGEROUS_KEYWORDS)
                    weight = 8 if is_dangerous else 3
                    timeline_data.append({
                        "timestamp": cmd.get('timestamp', ''),
                        "command": cmd_text[:40],
                        "weight": weight,
                        "category": "Dangerous" if is_dangerous else "Benign",
                    })

                df_timeline = pd.DataFrame(timeline_data)
                df_timeline['timestamp'] = pd.to_datetime(df_timeline['timestamp'])

                fig_timeline = px.scatter(
                    df_timeline,
                    x="timestamp",
                    y="weight",
                    color="category",
                    size="weight",
                    hover_data=["command"],
                    color_discrete_map={"Dangerous": "#ef4444", "Benign": "#27c93f"},
                    labels={"timestamp": "Time", "weight": "Threat Weight", "category": "Type"},
                )
                fig_timeline.update_layout(
                    height=350,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#c9d1d9"},
                    xaxis={"gridcolor": "#30363d"},
                    yaxis={"gridcolor": "#30363d"},
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

            # ─── Intent Progression ───
            if intents:
                st.markdown("**Intent Progression:**")
                intent_html = ""
                for i, intent in enumerate(intents):
                    itype = intent['intent_type']
                    intent_html += f'<span class="intent-badge intent-{itype}">{itype.replace("_", " ").title()}</span>'
                    if i < len(intents) - 1:
                        intent_html += " → "
                st.markdown(intent_html, unsafe_allow_html=True)

            # ─── Canary Status ───
            if canaries:
                st.markdown("**Canary Tripwires:**")
                for c in canaries:
                    status = "TRIGGERED" if c['triggered'] else "Planted"
                    st.markdown(f"- `{c['filepath']}` — Intent: *{c['intent']}* — {status}")

            # ─── GIA Alerts ───
            gia_warnings = [e for e in threat_events if e.get('event_type') == 'gia_warning']
            if gia_warnings:
                st.markdown("**GIA Alerts:**")
                for warning in gia_warnings:
                    try:
                        data = json.loads(warning.get('data', '{}')) if isinstance(warning.get('data'), str) else warning.get('data', {})
                    except Exception:
                        data = {}
                    check = data.get('check', 'unknown')
                    message = data.get('message', 'No details')
                    severity = warning.get('severity', 'medium')

                    if check == 'bot_detected':
                        color = '#d29922'
                        icon = 'BOT'
                    elif check == 'suspicious_behavior':
                        color = '#e3b341'
                        icon = 'SUSPICIOUS'
                    elif check == 'realism_check_failed':
                        color = '#da3633'
                        icon = 'TIMING'
                    else:
                        color = '#8b949e'
                        icon = 'ALERT'

                    st.markdown(
                        f'<div style="background:{color}22;border-left:4px solid {color};padding:8px 12px;margin:4px 0;border-radius:4px;">'
                        f'<b>[{icon}] {check.replace("_", " ").title()}</b> ({severity.upper()}) — {html.escape(message)}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            # ─── Recent Commands ───
            st.markdown("#### Recent Commands")
            for cmd in commands[-5:]:
                with st.expander(f"{cmd['command']}", expanded=False):
                    st.write(f"**Timestamp:** {cmd['timestamp']}")
                    st.write(f"**Execution Time:** {cmd.get('execution_time_ms', 0)}ms")
                    st.text(str(cmd.get('response', ''))[:500])

            # ─── Threat Report ───
            if st.button("Generate Threat Report", key=f"report_{sid}"):
                report_data = sdb.generate_report_data()
                report = _generate_threat_report(report_data, selected_session_obj)
                if report:
                    st.markdown(f'<div class="threat-report">{report}</div>', unsafe_allow_html=True)
                else:
                    st.warning("Could not generate report — Groq API may not be available")

# ═══════════════════════════════════════
# TAB 5: GEO-INTELLIGENCE (Folium Map)
# ═══════════════════════════════════════
with tab5:
    st.subheader("Geo-Intelligence")
    st.markdown("IP geolocation of connected attackers")

    # Gather geo data for all active sessions
    geo_data = []
    for session in active_sessions:
        ip = session['client_ip']
        geo = lookup_ip(ip)
        if geo:
            geo['session_id'] = session['session_id']
            geo['username'] = session.get('username', 'user')
            geo['start_time'] = session.get('start_time', '')
            geo_data.append(geo)

    if geo_data:
        # Build Folium map
        avg_lat = sum(g['lat'] for g in geo_data) / len(geo_data)
        avg_lon = sum(g['lon'] for g in geo_data) / len(geo_data)
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=3, tiles="CartoDB dark_matter")

        for g in geo_data:
            popup_html = f"""
            <b>IP:</b> {g.get('query', 'N/A')}<br>
            <b>City:</b> {g.get('city', 'N/A')}<br>
            <b>Country:</b> {g.get('country', 'N/A')}<br>
            <b>ISP:</b> {g.get('isp', 'N/A')}<br>
            <b>Session:</b> {g.get('session_id', '')[:8]}...<br>
            <b>Started:</b> {g.get('start_time', 'N/A')}
            """
            folium.Marker(
                location=[g['lat'], g['lon']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
            ).add_to(m)

            # Add a pulsing circle around the marker
            folium.CircleMarker(
                location=[g['lat'], g['lon']],
                radius=20,
                color="#ef4444",
                fill=True,
                fill_opacity=0.15,
                weight=2,
            ).add_to(m)

        st_folium(m, width=None, height=500, use_container_width=True)

        # Geo table below the map
        st.markdown("#### Attacker Origins")
        geo_table = []
        for g in geo_data:
            geo_table.append({
                "IP": g.get('query', 'N/A'),
                "City": g.get('city', 'N/A'),
                "Country": g.get('country', 'N/A'),
                "ISP": g.get('isp', 'N/A'),
                "Organization": g.get('org', 'N/A'),
            })
        st.dataframe(pd.DataFrame(geo_table), use_container_width=True)
    else:
        # Show empty dark map
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        st_folium(m, width=None, height=400, use_container_width=True)
        st.info("No active sessions to geolocate. Waiting for connections...")

# ═══════════════════════════════════════
# TAB 6: ANALYTICS (Session Heatmap)
# ═══════════════════════════════════════
with tab6:
    st.subheader("Historical Analytics")

    all_sessions = db.get_all_sessions()

    if all_sessions:
        # ─── Session Activity Heatmap ───
        st.markdown("#### Session Activity Heatmap (Hour vs Day of Week)")
        heatmap_data = []
        for s in all_sessions:
            try:
                st_time = pd.to_datetime(s.get('start_time', ''))
                heatmap_data.append({
                    "hour": st_time.hour,
                    "day": st_time.day_name(),
                })
            except Exception:
                pass

        if heatmap_data:
            df_heat = pd.DataFrame(heatmap_data)
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            pivot = df_heat.groupby(["day", "hour"]).size().reset_index(name="count")
            pivot_table = pivot.pivot(index="day", columns="hour", values="count").fillna(0)
            # Reindex
            pivot_table = pivot_table.reindex(day_order, fill_value=0)

            fig_heat = px.imshow(
                pivot_table,
                labels={"x": "Hour of Day", "y": "Day of Week", "color": "Sessions"},
                color_continuous_scale="Reds",
                aspect="auto",
            )
            fig_heat.update_layout(
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "#c9d1d9"},
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        # ─── Summary Stats ───
        st.markdown("#### Summary")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sessions (All Time)", len(all_sessions))
        with col2:
            active_count = sum(1 for s in all_sessions if s.get('status') == 'active')
            st.metric("Currently Active", active_count)
        with col3:
            unique_ips = len(set(s.get('client_ip', '') for s in all_sessions))
            st.metric("Unique Attacker IPs", unique_ips)
    else:
        st.info("No session history available yet. Start the honeypot and wait for connections.")

st.divider()
st.markdown("""
---
**AeroGhost** | Autonomous AI Cyber-Deception System
Status: Online | Last Updated: {} | Version: 0.3.0
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
