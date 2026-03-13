# Live Terminal Feed — Implementation Plan

Show attackers' keystrokes **in real-time** inside the Streamlit dashboard, including the characters they're currently typing (before they hit Enter), exactly like watching someone hack live.

## Architecture

```
Attacker types 'c' 'a' 't' ' ' '/' 'e' 't' 'c' Enter
       ↓
server.py._handle_shell() — updates live_typing in DB after each char
       ↓
SQLite: live_typing table → { session_id, buffer, last_updated }
SQLite: commands table    → completed commands (already exists)
       ↓
dashboard/app.py polls DB every 1 second using st_autorefresh
       ↓
Shows: completed commands + "cat /etc▌" (blinking cursor for in-progress)
```

---

## Proposed Changes

### Database Layer

#### [MODIFY] [database.py](file:///d:/just%20learning/ghostnet/state_manager/database.py)

Add a `live_typing` table:
```sql
CREATE TABLE live_typing (
    session_id TEXT PRIMARY KEY,
    buffer     TEXT,
    updated_at TIMESTAMP
)
```

Add 3 new methods:
- `upsert_live_typing(session_id, buffer)` — called on every keystroke
- `clear_live_typing(session_id)` — called when Enter is pressed
- `get_all_live_typing()` — called by dashboard

---

### SSH Server Layer

#### [MODIFY] [server.py](file:///d:/just%20learning/ghostnet/ssh_listener/server.py)

In [_handle_shell](file:///d:/just%20learning/ghostnet/ssh_listener/server.py#160-239), pass a `live_feed_callback` down from [SSHServerSocket](file:///d:/just%20learning/ghostnet/ssh_listener/server.py#60-246).

After every printable character is added to `command_buffer`:
```python
if self.live_feed_callback:
    self.live_feed_callback(session_id, command_buffer)
```

After Enter is pressed (command dispatched):
```python
if self.live_feed_callback:
    self.live_feed_callback(session_id, "")  # clear the buffer
```

---

### Main Entry Point

#### [MODIFY] [main.py](file:///d:/just%20learning/ghostnet/main.py)

Pass the `live_feed_callback` to [SSHServerSocket](file:///d:/just%20learning/ghostnet/ssh_listener/server.py#60-246):
```python
self.ssh_server = SSHServerSocket(
    host="0.0.0.0",
    port=self.port,
    command_handler=self._handle_command,
    live_feed_callback=self._update_live_typing   # ← new
)
```

Add `_update_live_typing(session_id, buffer)` method that calls `self.database.upsert_live_typing(...)`.

---

### Dashboard

#### [MODIFY] [app.py](file:///d:/just%20learning/ghostnet/dashboard/app.py)

**New package needed:** `streamlit-autorefresh` (auto-polls every 1s without user interaction)

**New "👁 Live Terminal" tab** (first tab, most prominent):
- Dark terminal-style CSS (green text on black background)
- Shows each active session in its own terminal panel
- Completed commands shown with `user@ghostnet:~$` prompt
- Current typing buffer shown with a blinking `▌` cursor character
- Auto-refreshes every **1000ms**

**Terminal CSS:**
```css
.terminal {
    background: #0d1117;
    color: #39ff14;  /* neon green */
    font-family: 'Courier New', monospace;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #30363d;
    min-height: 300px;
}
```

---

## New Package

#### [MODIFY] [requirements.txt](file:///d:/just%20learning/ghostnet/requirements.txt)

```diff
+streamlit-autorefresh>=0.0.1
```

---

## Verification Plan

### Manual Test
1. `python main.py`
2. `streamlit run dashboard/app.py`
3. `ssh user@localhost -p 2222`
4. Slowly type `l`, `s`, ` `, `-`, `l`, `a` → watch each letter appear in dashboard before Enter
5. Press Enter → command disappears from live buffer, appears in history
