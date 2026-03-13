# Implementation Plan: Bug Fixes + General Intelligence Agency

## Overview

Three items: two bug fixes to make the honeypot behave consistently, and a new **General Intelligence Agency (GIA)** — a real-time monitoring agent that watches for behavioral anomalies and inconsistencies in the honeypot session.

---

## Bug 1: `.bash_history` — "No Such File"

**Root Cause:** The [_generate_themed_network](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#170-263) function creates the `Documents`, `Desktop`, etc. dirs by calling `user_home.add_child(...)`. The children dict is keyed by name. The dot files (`.bash_history`, `.bashrc`, etc.) are added AFTER [_generate_themed_network](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#170-263). This is fine — BUT the generation function also has a random chance to call itself recursively and overwrite existing dirs via the `existing`-check path.

**Actual bug:** [_generate_themed_network](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#170-263) at `current_depth == 1` does `dir_name = theme`. Then checks `existing = parent_node.get_child(dir_name)`. For `Documents`, this creates a new [FSNode("Documents")](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#17-87). But there's actually a deeper issue: [_build_tree](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#101-163) calls [_generate_themed_network(user_home, "Documents", ...)](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#170-263) — which adds `Documents` as a child of `user_home`. It does NOT touch `.bash_history`. However, it generates the directories **before** the dotfiles are added. `.bash_history` is added last and should survive.

**The real issue:** `cat .bash_history` — the [_local_intent_check](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#166-220) in [BreadcrumbAgent](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#21-309) matches `"cat .bash_history"` → `credential_hunt` (confidence 0.85) → breadcrumb pipeline fires in a background thread → BEFORE [should_plant](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#127-135) check, [increment_cmd](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#136-140) is called → the FIRST `cat .bash_history` call triggers a breadcrumb (since `cmds_since_plant` starts at 0 and was incremented *before* the background thread checked it). Additionally the path `"cat .bash_history"` might be failing because [cat](file:///d:/just%20learning/ghostnet/agents/command_handler.py#373-396) is checking if the literal string `.bash_history` is passed from a session where `command_buffer` includes the prompt.

**Fix:** Add debug logging. The actual fix is twofold:
1. In [file_system.py](file:///d:/just%20learning/ghostnet/state_manager/file_system.py): Add `inject_dotfiles` as a separate method called **last** in [_build_tree](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#101-163) — ensures dotfiles can't be stomped.
2. In [main.py](file:///d:/just%20learning/ghostnet/main.py): Call [increment_cmd](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#136-140) **after** the background thread result, not before.

---

## Bug 2: Breadcrumb Appears After "Failed" [cat](file:///d:/just%20learning/ghostnet/agents/command_handler.py#373-396)

**Root Cause:** This is a **timing + logic** bug:

1. Attacker types `cat .bash_history` — even if [cat](file:///d:/just%20learning/ghostnet/agents/command_handler.py#373-396) returns "not found", it's still a valid command that gets logged + runs the breadcrumb pipeline
2. [increment_cmd](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#136-140) is called in the **main thread before** the background thread starts
3. The background thread finishes ~50ms later → plants `config.php`
4. Attacker types [ls](file:///d:/just%20learning/ghostnet/agents/command_handler.py#161-208) → sees the new file "magically appear"

This is suspicious to a smart attacker — a file wouldn't appear mid-session.

**Fix:**
- Move [increment_cmd](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#136-140) call to **inside** the [_breadcrumb_pipeline](file:///d:/just%20learning/ghostnet/main.py#187-247) background thread
- Add a **plausibility check**: only plant breadcrumbs in directories that have other files already (not an empty dir)
- Add a **minimum delay** of `random.uniform(2, 8)` seconds inside the pipeline before planting, so the file appears to have "always been there" if they navigate away and come back

---

## New Feature: General Intelligence Agency (GIA)

A monitoring watchdog that continuously validates session realism and flags anomalies.

**Concept:** The GIA runs as a background thread and watches ALL active sessions. It checks questions like:
- "Does this session look real?" — e.g., if the filesystem changes in a way that's physically impossible
- "Is the attacker behaving suspiciously aware?" — e.g., typing [ls](file:///d:/just%20learning/ghostnet/agents/command_handler.py#161-208) repeatedly fast (bot?), or checking file timestamps

### Proposed Changes

---

### New File: `agents/intelligence_agency.py`

A new `GeneralIntelligenceAgency` class with:

| Check | Description |
|-------|-------------|
| **Realism Validator** | After each breadcrumb plant, verifies the file's timestamps are realistic (not `datetime.now()` — should look older) |
| **Bot Detector** | Detects if commands are being typed faster than humanly possible (<200ms between commands) → flags as automated scanner |
| **Suspicion Scorer** | Scores attacker suspicion level based on: repeated [ls](file:///d:/just%20learning/ghostnet/agents/command_handler.py#161-208) after each command (checking for new files), running `find / -newer`, checking file mtimes via [stat](file:///d:/just%20learning/ghostnet/agents/command_handler.py#597-617) |
| **Honeypot Consistency Check** | Periodically verifies responses are self-consistent — e.g., [whoami](file:///d:/just%20learning/ghostnet/agents/command_handler.py#678-680) always returns `user`, hostname always `ghostnet`/`aeroghost` |
| **Session Integrity Monitor** | Detects if [active_sessions](file:///d:/just%20learning/ghostnet/state_manager/database.py#75-83) dict desync'd from the DB (stale sessions or missing session DBs) |

```
Runs every 5 seconds in background:
   for each session:
       → check bot speed (time between commands)
       → check suspicion score (ls-after-ls patterns)
       → validate breadcrumb file timestamps
       → report anomalies to SessionDB as "gia_warning" threat_events
```

---

### Modified: [main.py](file:///d:/just%20learning/ghostnet/main.py)

- Instantiate `GeneralIntelligenceAgency(active_sessions)`  
- Start it as a daemon thread in `GhostNetHoneypot.__init__`
- Inject `gia.record_command_time(session_id)` in [_handle_command](file:///d:/just%20learning/ghostnet/main.py#144-186) for bot detection

---

### Modified: [dashboard/app.py](file:///d:/just%20learning/ghostnet/dashboard/app.py) — Intelligence Tab

Add a **GIA Alerts** section in the Intelligence tab:
- Shows all `gia_warning` threat events per session
- Color coded: `bot_detected` = orange, `suspicious_behavior` = yellow, `realism_check_failed` = red

---

### Modified: [agents/breadcrumbs.py](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py)

- Move [increment_cmd](file:///d:/just%20learning/ghostnet/agents/breadcrumbs.py#136-140) call to inside [_breadcrumb_pipeline](file:///d:/just%20learning/ghostnet/main.py#187-247) thread
- Add `random.uniform(3, 10)` second delay before planting
- Add `_set_realistic_timestamp` helper: sets `node.modified` to `datetime.now() - timedelta(days=random.randint(1, 30))` so the planted file looks old

---

### Modified: [state_manager/file_system.py](file:///d:/just%20learning/ghostnet/state_manager/file_system.py)

- Move dotfile creation into a dedicated `_inject_dotfiles(user_home)` method called at the very end of [_build_tree](file:///d:/just%20learning/ghostnet/state_manager/file_system.py#101-163)
- Guarantees dotfiles can never be overwritten by the themed generation

---

## Verification Plan

### Automated Tests
```bash
python -c "
from state_manager.file_system import VirtualFileSystem
fs = VirtualFileSystem()
home = fs.root.get_child('home').get_child('user')
assert home.get_child('.bash_history') is not None, 'dotfile missing!'
print('✓ .bash_history exists')
node = fs.resolve_path('.bash_history')
assert node is not None, 'resolve_path failed!'
print('✓ resolve_path works')
"
```

### Manual Verification
1. SSH in → `cat .bash_history` → should return the history content, NOT "no such file"
2. Wait 5–10 seconds after `cat .bash_history` → [ls](file:///d:/just%20learning/ghostnet/agents/command_handler.py#161-208) → config file should appear only after a delay
3. Type 20 commands in <2 seconds using a script → GIA should flag `bot_detected` in dashboard
4. Check Intelligence tab → GIA alerts should appear as a new section
