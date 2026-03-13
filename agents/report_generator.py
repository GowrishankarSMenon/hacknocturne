"""
AeroGhost Session Report Generator - PDF Export.
Generates a detailed PDF report when an attacker session ends.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fpdf import FPDF

logger = logging.getLogger(__name__)

REPORTS_DIR = "logs/reports"


def _s(text) -> str:
    """Sanitize text for PDF: strip non-latin1 chars and limit length."""
    if text is None:
        return "N/A"
    t = str(text)
    return t.encode("latin-1", errors="replace").decode("latin-1")


class SessionReportPDF(FPDF):
    """Custom PDF with AeroGhost branding."""

    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(180, 40, 40)
        self.cell(0, 8, "AEROGHOST - Session Intelligence Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180, 40, 40)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"AeroGhost Report  |  Page {self.page_no()}/{{nb}}", align="C")

    def section(self, title: str):
        """Section heading."""
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(60, 60, 80)
        self.cell(0, 7, f"  {_s(title)}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(30, 30, 30)

    def field(self, label: str, value):
        """Key-value pair on one line."""
        self.set_font("Helvetica", "B", 9)
        self.cell(45, 5, _s(label))
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, _s(value), new_x="LMARGIN", new_y="NEXT")

    def row(self, cells: list, widths: list, bold=False, fill_color=None):
        """Simple table row. Each cell is truncated to fit its width."""
        if fill_color:
            self.set_fill_color(*fill_color)
        self.set_font("Helvetica", "B" if bold else "", 8)
        for text, w in zip(cells, widths):
            safe = _s(text)
            # Truncate based on approx char width (2mm per char at 8pt)
            max_chars = max(w // 2, 2)
            truncated = safe[:max_chars]
            self.cell(w, 5, truncated, border=1,
                      fill=bool(fill_color), new_x="RIGHT")
        self.ln()


class SessionReportGenerator:
    """Generates PDF reports from session data."""

    DANGEROUS_KEYWORDS = {
        "sudo", "su", "passwd", "shadow", "id_rsa", "curl", "wget",
        "nmap", "ssh", "scp", "mysql", "mysqldump", "cat /etc",
        "find / ", "chmod 777", "nc ", "netcat", "python -c",
    }

    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def _is_dangerous(self, cmd_text: str) -> bool:
        lower = cmd_text.lower()
        return any(kw in lower for kw in self.DANGEROUS_KEYWORDS)

    def generate(self, session_id: str, session_info: dict,
                 session_db, global_db) -> Optional[str]:
        """
        Generate a full PDF report for a closed session.
        Returns the path to the generated PDF, or None on failure.
        """
        try:
            pdf = SessionReportPDF()
            pdf.alias_nb_pages()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # -- Session Metadata --
            pdf.section("Session Metadata")
            pdf.field("Session ID:", session_id)
            pdf.field("Attacker IP:", session_info.get("client_ip", "unknown"))
            pdf.field("Username:", session_info.get("username", "user"))
            pdf.field("Start Time:", session_info.get("start_time", "N/A"))
            pdf.field("End Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # HASSH
            hassh = None
            try:
                hassh = global_db.get_session_hassh(session_id)
            except Exception:
                pass
            pdf.field("HASSH:", hassh or "Not captured")

            # Duration
            start = session_info.get("start_time")
            if start:
                try:
                    if isinstance(start, str):
                        start = datetime.fromisoformat(start)
                    dur = datetime.now() - start
                    m, s = divmod(int(dur.total_seconds()), 60)
                    pdf.field("Duration:", f"{m}m {s}s")
                except Exception:
                    pass

            # -- Command Log --
            commands = session_db.get_commands()
            pdf.section(f"Command Log  ({len(commands)} commands)")

            if commands:
                W = [28, 82, 18, 22, 40]  # Time, Command, ms, Flag, Response
                pdf.row(["Time", "Command", "ms", "Flag", "Response"], W,
                        bold=True, fill_color=(50, 50, 70))
                pdf.set_text_color(255, 255, 255)
                pdf.set_text_color(30, 30, 30)

                for cmd in commands:
                    ts = str(cmd.get("timestamp", ""))[-8:]
                    cmd_text = cmd.get("command", "")
                    ms = str(cmd.get("execution_time_ms", 0))
                    danger = self._is_dangerous(cmd_text)
                    flag = "DANGER" if danger else ""
                    resp = str(cmd.get("response", ""))[:40].replace("\n", " ")
                    if danger:
                        pdf.row([ts, cmd_text, ms, flag, resp], W,
                                fill_color=(255, 230, 230))
                    else:
                        pdf.row([ts, cmd_text, ms, flag, resp], W)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, "No commands recorded.", new_x="LMARGIN", new_y="NEXT")

            # -- Detected Intents --
            intents = session_db.get_intents()
            pdf.section(f"Detected Intents  ({len(intents)})")

            if intents:
                W = [30, 50, 25, 55]
                pdf.row(["Time", "Intent", "Confidence", "Trigger"], W,
                        bold=True, fill_color=(50, 50, 70))
                pdf.set_text_color(30, 30, 30)

                for intent in intents:
                    ts = str(intent.get("timestamp", ""))[-8:]
                    itype = intent.get("intent_type", "")
                    conf = f"{intent.get('confidence', 0):.0%}"
                    trigger = intent.get("trigger_command", "")
                    pdf.row([ts, itype, conf, trigger], W)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, "No intents detected.", new_x="LMARGIN", new_y="NEXT")

            # -- Canary Files --
            canaries = session_db.get_all_canaries()
            pdf.section(f"Canary Tripwires  ({len(canaries)})")

            if canaries:
                W = [55, 35, 35, 35]
                pdf.row(["File", "Intent", "Planted", "Triggered"], W,
                        bold=True, fill_color=(50, 50, 70))
                pdf.set_text_color(30, 30, 30)

                for c in canaries:
                    fp = c.get("filepath", "")
                    intent = c.get("intent", "")
                    planted = str(c.get("planted_at", ""))[-8:]
                    triggered = str(c.get("triggered_at", ""))[-8:] if c.get("triggered") else "No"
                    hit = bool(c.get("triggered"))
                    if hit:
                        pdf.row([fp, intent, planted, triggered], W,
                                fill_color=(255, 220, 220))
                    else:
                        pdf.row([fp, intent, planted, triggered], W)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, "No canaries planted.", new_x="LMARGIN", new_y="NEXT")

            # -- Threat Events --
            events = session_db.get_threat_events()
            pdf.section(f"Threat Events  ({len(events)})")

            if events:
                W = [28, 40, 22, 70]
                pdf.row(["Time", "Type", "Severity", "Details"], W,
                        bold=True, fill_color=(50, 50, 70))
                pdf.set_text_color(30, 30, 30)

                for ev in events:
                    ts = str(ev.get("timestamp", ""))[-8:]
                    etype = ev.get("event_type", "")
                    sev = ev.get("severity", "").upper()
                    data = ev.get("data", "{}")
                    try:
                        details = json.loads(data) if isinstance(data, str) else data
                        detail_str = details.get("message", details.get("check", str(details)))
                    except Exception:
                        detail_str = str(data)
                    crit = sev == "CRITICAL"
                    if crit:
                        pdf.row([ts, etype, sev, detail_str], W,
                                fill_color=(255, 210, 210))
                    else:
                        pdf.row([ts, etype, sev, detail_str], W)
            else:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, "No threat events recorded.", new_x="LMARGIN", new_y="NEXT")

            # -- Threat Score --
            pdf.section("Threat Assessment")
            score = self._compute_threat_score(commands, intents, canaries, events)
            level = ("CRITICAL" if score >= 75 else "HIGH" if score >= 50
                     else "MEDIUM" if score >= 25 else "LOW")

            pdf.set_font("Helvetica", "B", 14)
            if score >= 75:
                pdf.set_text_color(200, 30, 30)
            elif score >= 50:
                pdf.set_text_color(200, 120, 0)
            elif score >= 25:
                pdf.set_text_color(180, 180, 0)
            else:
                pdf.set_text_color(0, 140, 0)
            pdf.cell(0, 10, f"Threat Score: {score}/100  ({level})",
                     new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_text_color(30, 30, 30)

            pdf.ln(4)
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(130, 130, 130)
            pdf.cell(0, 5, f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                     align="C")

            # Save
            filepath = os.path.join(REPORTS_DIR, f"{session_id}.pdf")
            pdf.output(filepath)
            logger.info(f"Session report saved: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to generate PDF report for {session_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _compute_threat_score(self, commands, intents, canaries, events) -> int:
        score = 0
        score += min(len(commands) * 2, 20)
        danger_count = sum(1 for c in commands if self._is_dangerous(c.get("command", "")))
        score += min(danger_count * 5, 30)
        score += min(len(intents) * 5, 20)
        hits = sum(1 for c in canaries if c.get("triggered"))
        score += min(hits * 15, 15)
        crit = sum(1 for e in events if e.get("severity") == "critical")
        score += min(crit * 10 + len(events) * 2, 15)
        return min(score, 100)
