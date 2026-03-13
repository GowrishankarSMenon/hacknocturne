"""
GhostNet Command Handler - Pure Python command interpreter.
Handles all standard Linux commands deterministically using the VirtualFileSystem.
No LLM needed for command responses.
"""

import re
import logging
import random
from datetime import datetime
from typing import Optional, Tuple

from state_manager.file_system import VirtualFileSystem, FSNode

logger = logging.getLogger(__name__)

# Fake system info constants
KERNEL_VERSION = "5.15.0-91-generic"
OS_VERSION = "Ubuntu 22.04.3 LTS"
HOSTNAME = "ghostnet"
USERNAME = "user"
UPTIME_STR = None  # generated at init


class CommandHandler:
    """
    Deterministic command interpreter for the GhostNet honeypot.
    Executes commands against a VirtualFileSystem instance.
    """

    def __init__(self, filesystem: VirtualFileSystem):
        self.fs = filesystem
        self._boot_time = datetime.now().replace(
            hour=random.randint(0, 6),
            minute=random.randint(0, 59),
            second=0
        )
        # Map of command name -> handler function
        self._commands = {
            "pwd": self._cmd_pwd,
            "ls": self._cmd_ls,
            "cd": self._cmd_cd,
            "mkdir": self._cmd_mkdir,
            "touch": self._cmd_touch,
            "rm": self._cmd_rm,
            "rmdir": self._cmd_rmdir,
            "cat": self._cmd_cat,
            "echo": self._cmd_echo,
            "whoami": self._cmd_whoami,
            "hostname": self._cmd_hostname,
            "uname": self._cmd_uname,
            "id": self._cmd_id,
            "ps": self._cmd_ps,
            "ifconfig": self._cmd_ifconfig,
            "ip": self._cmd_ip,
            "history": self._cmd_history,
            "clear": self._cmd_clear,
            "date": self._cmd_date,
            "uptime": self._cmd_uptime,
            "df": self._cmd_df,
            "free": self._cmd_free,
            "which": self._cmd_which,
            "file": self._cmd_file,
            "head": self._cmd_head,
            "tail": self._cmd_tail,
            "wc": self._cmd_wc,
            "cp": self._cmd_cp,
            "mv": self._cmd_mv,
            "chmod": self._cmd_chmod,
            "stat": self._cmd_stat,
            "find": self._cmd_find,
            "grep": self._cmd_grep,
            "env": self._cmd_env,
            "export": self._cmd_export,
            "sudo": self._cmd_sudo,
            "su": self._cmd_su,
            "wget": self._cmd_wget,
            "curl": self._cmd_curl,
            "ping": self._cmd_ping,
            "netstat": self._cmd_netstat,
            "ss": self._cmd_ss,
            "apt": self._cmd_apt,
            "apt-get": self._cmd_apt,
            "man": self._cmd_man,
            "less": self._cmd_less,
            "more": self._cmd_more,
            "nano": self._cmd_nano,
            "vi": self._cmd_vi,
            "vim": self._cmd_vim,
        }

    def execute(self, command_str: str) -> str:
        """
        Parse and execute a command string. Returns the output.
        """
        command_str = command_str.strip()
        if not command_str:
            return ""

        # Handle pipes (just take the first command for now)
        if "|" in command_str:
            parts = command_str.split("|")
            command_str = parts[0].strip()

        # Handle echo with redirect (special case)
        if command_str.startswith("echo ") and (">>" in command_str or ">" in command_str):
            return self._cmd_echo_redirect(command_str)

        # Parse command and args
        parts = self._parse_command(command_str)
        if not parts:
            return ""

        cmd = parts[0]
        args = parts[1:]

        # Look up handler
        handler = self._commands.get(cmd)
        if handler:
            try:
                return handler(args)
            except Exception as e:
                logger.error(f"Error executing command '{cmd}': {e}")
                return f"bash: {cmd}: unexpected error"
        else:
            return f"bash: {cmd}: command not found"

    def _parse_command(self, command_str: str) -> list:
        """Parse a command string into parts, respecting quotes."""
        parts = []
        current = ""
        in_single_quote = False
        in_double_quote = False

        for char in command_str:
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == " " and not in_single_quote and not in_double_quote:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char

        if current:
            parts.append(current)

        return parts

    # ──────────────────────────────────────────────
    # File system commands
    # ──────────────────────────────────────────────

    def _cmd_pwd(self, args: list) -> str:
        return self.fs.get_pwd()

    def _cmd_ls(self, args: list) -> str:
        show_long = False
        show_all = False
        target_path = None

        for arg in args:
            if arg.startswith("-"):
                if "l" in arg:
                    show_long = True
                if "a" in arg:
                    show_all = True
            else:
                target_path = arg

        target = self.fs.resolve_path(target_path) if target_path else self.fs.cwd

        if target is None:
            return f"ls: cannot access '{target_path}': No such file or directory"

        if target.is_file():
            if show_long:
                return target.format_ls_long()
            return target.name

        # List directory contents
        items = list(target.children.values())

        if not show_all:
            items = [i for i in items if not i.name.startswith(".")]

        if not items and not show_all:
            return ""

        items.sort(key=lambda x: x.name)

        if show_long:
            lines = [f"total {len(items) * 4}"]
            if show_all:
                # Add . and ..
                lines.append(f"drwxr-xr-x   {len(target.children)+2:>3} {target.owner:>6} {target.group:>6}     4096 {target.modified.strftime('%b %d %H:%M')} .")
                parent = target.parent if target.parent else target
                lines.append(f"drwxr-xr-x   {len(parent.children)+2:>3} {parent.owner:>6} {parent.group:>6}     4096 {parent.modified.strftime('%b %d %H:%M')} ..")
            for item in items:
                lines.append(item.format_ls_long())
            return "\n".join(lines)
        else:
            return "  ".join([item.name for item in items])

    def _cmd_cd(self, args: list) -> str:
        if not args:
            self.fs.cwd = self.fs.home_dir
            return ""

        path = args[0]

        if path == "-":
            # Just go home for simplicity
            self.fs.cwd = self.fs.home_dir
            return ""

        target = self.fs.resolve_path(path)

        if target is None:
            return f"bash: cd: {path}: No such file or directory"

        if not target.is_dir():
            return f"bash: cd: {path}: Not a directory"

        self.fs.cwd = target
        return ""

    def _cmd_mkdir(self, args: list) -> str:
        if not args:
            return "mkdir: missing operand"

        parents = False
        dirs_to_create = []

        for arg in args:
            if arg == "-p":
                parents = True
            elif arg.startswith("-"):
                continue
            else:
                dirs_to_create.append(arg)

        output_lines = []
        for dir_name in dirs_to_create:
            if parents:
                # Create intermediate directories
                parts = dir_name.strip("/").split("/")
                current = self.fs.cwd if not dir_name.startswith("/") else self.fs.root
                for part in parts:
                    child = current.get_child(part)
                    if child is None:
                        new_dir = FSNode(part, "dir", owner=USERNAME, group=USERNAME)
                        new_dir.modified = datetime.now()
                        current.add_child(new_dir)
                        current = new_dir
                    elif child.is_dir():
                        current = child
                    else:
                        return f"mkdir: cannot create directory '{dir_name}': Not a directory"
            else:
                # Resolve parent path
                if "/" in dir_name:
                    parent_path = "/".join(dir_name.split("/")[:-1])
                    name = dir_name.split("/")[-1]
                    parent = self.fs.resolve_path(parent_path)
                    if parent is None:
                        return f"mkdir: cannot create directory '{dir_name}': No such file or directory"
                else:
                    parent = self.fs.cwd
                    name = dir_name

                if parent.get_child(name):
                    return f"mkdir: cannot create directory '{name}': File exists"

                new_dir = FSNode(name, "dir", owner=USERNAME, group=USERNAME)
                new_dir.modified = datetime.now()
                parent.add_child(new_dir)

        return ""

    def _cmd_touch(self, args: list) -> str:
        if not args:
            return "touch: missing file operand"

        for fname in args:
            if fname.startswith("-"):
                continue

            # Check if file already exists (just update timestamp)
            existing = self.fs.resolve_path(fname)
            if existing:
                existing.modified = datetime.now()
                continue

            # Resolve parent
            if "/" in fname:
                parent_path = "/".join(fname.split("/")[:-1])
                name = fname.split("/")[-1]
                parent = self.fs.resolve_path(parent_path)
                if parent is None:
                    return f"touch: cannot touch '{fname}': No such file or directory"
            else:
                parent = self.fs.cwd
                name = fname

            new_file = FSNode(name, "file", owner=USERNAME, group=USERNAME,
                              permissions="rw-r--r--", content="")
            new_file.modified = datetime.now()
            parent.add_child(new_file)

        return ""

    def _cmd_rm(self, args: list) -> str:
        if not args:
            return "rm: missing operand"

        recursive = False
        force = False
        targets = []

        for arg in args:
            if arg.startswith("-"):
                if "r" in arg or "R" in arg:
                    recursive = True
                if "f" in arg:
                    force = True
            else:
                targets.append(arg)

        for target_path in targets:
            target = self.fs.resolve_path(target_path)
            if target is None:
                if not force:
                    return f"rm: cannot remove '{target_path}': No such file or directory"
                continue

            if target.is_dir() and not recursive:
                return f"rm: cannot remove '{target_path}': Is a directory"

            # Don't allow removing root or critical paths
            if target == self.fs.root or target.get_path() in ["/", "/home", "/home/user"]:
                return f"rm: it is dangerous to operate recursively on '{target.get_path()}'"

            parent = target.parent
            if parent:
                parent.remove_child(target.name)

        return ""

    def _cmd_rmdir(self, args: list) -> str:
        if not args:
            return "rmdir: missing operand"

        for dir_path in args:
            target = self.fs.resolve_path(dir_path)
            if target is None:
                return f"rmdir: failed to remove '{dir_path}': No such file or directory"
            if not target.is_dir():
                return f"rmdir: failed to remove '{dir_path}': Not a directory"
            if target.children:
                return f"rmdir: failed to remove '{dir_path}': Directory not empty"

            parent = target.parent
            if parent:
                parent.remove_child(target.name)

        return ""

    def _cmd_cat(self, args: list) -> str:
        if not args:
            return ""

        output = []
        for fname in args:
            if fname.startswith("-"):
                continue
            target = self.fs.resolve_path(fname)
            if target is None:
                output.append(f"cat: {fname}: No such file or directory")
            elif target.is_dir():
                output.append(f"cat: {fname}: Is a directory")
            else:
                output.append(target.content)

        return "\n".join(output)

    def _cmd_echo(self, args: list) -> str:
        return " ".join(args)

    def _cmd_echo_redirect(self, command_str: str) -> str:
        """Handle echo ... > file or echo ... >> file"""
        append = ">>" in command_str

        if append:
            parts = command_str.split(">>", 1)
        else:
            parts = command_str.split(">", 1)

        text_part = parts[0].strip()
        file_path = parts[1].strip() if len(parts) > 1 else ""

        if not file_path:
            return "bash: syntax error near unexpected token `newline'"

        # Extract the text from echo
        text = text_part[5:].strip()  # Remove "echo "
        # Remove surrounding quotes
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]

        # Find or create the file
        target = self.fs.resolve_path(file_path)
        if target and target.is_dir():
            return f"bash: {file_path}: Is a directory"

        if target is None:
            # Create new file
            if "/" in file_path:
                parent_path = "/".join(file_path.split("/")[:-1])
                name = file_path.split("/")[-1]
                parent = self.fs.resolve_path(parent_path)
                if parent is None:
                    return f"bash: {file_path}: No such file or directory"
            else:
                parent = self.fs.cwd
                name = file_path

            target = FSNode(name, "file", owner=USERNAME, group=USERNAME,
                            permissions="rw-r--r--", content="")
            parent.add_child(target)

        if append:
            target.content += text + "\n"
        else:
            target.content = text + "\n"

        target.size = len(target.content.encode('utf-8'))
        target.modified = datetime.now()
        return ""

    def _cmd_head(self, args: list) -> str:
        n = 10
        fname = None
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    n = int(args[i+1])
                except ValueError:
                    return f"head: invalid number of lines: '{args[i+1]}'"
                i += 2
            elif args[i].startswith("-"):
                i += 1
            else:
                fname = args[i]
                i += 1

        if not fname:
            return "head: missing file operand"
        target = self.fs.resolve_path(fname)
        if target is None:
            return f"head: cannot open '{fname}' for reading: No such file or directory"
        if target.is_dir():
            return f"head: error reading '{fname}': Is a directory"
        lines = target.content.split("\n")
        return "\n".join(lines[:n])

    def _cmd_tail(self, args: list) -> str:
        n = 10
        fname = None
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    n = int(args[i+1])
                except ValueError:
                    return f"tail: invalid number of lines: '{args[i+1]}'"
                i += 2
            elif args[i].startswith("-"):
                i += 1
            else:
                fname = args[i]
                i += 1

        if not fname:
            return "tail: missing file operand"
        target = self.fs.resolve_path(fname)
        if target is None:
            return f"tail: cannot open '{fname}' for reading: No such file or directory"
        if target.is_dir():
            return f"tail: error reading '{fname}': Is a directory"
        lines = target.content.split("\n")
        return "\n".join(lines[-n:])

    def _cmd_wc(self, args: list) -> str:
        fname = None
        for a in args:
            if not a.startswith("-"):
                fname = a
                break
        if not fname:
            return "wc: missing file operand"
        target = self.fs.resolve_path(fname)
        if target is None:
            return f"wc: {fname}: No such file or directory"
        if target.is_dir():
            return f"wc: {fname}: Is a directory"
        lines = target.content.count("\n")
        words = len(target.content.split())
        chars = len(target.content)
        return f"  {lines}  {words} {chars} {fname}"

    def _cmd_cp(self, args: list) -> str:
        real_args = [a for a in args if not a.startswith("-")]
        if len(real_args) < 2:
            return "cp: missing file operand"
        src_path = real_args[0]
        dst_path = real_args[1]
        src = self.fs.resolve_path(src_path)
        if src is None:
            return f"cp: cannot stat '{src_path}': No such file or directory"
        if src.is_dir():
            return f"cp: -r not specified; omitting directory '{src_path}'"

        # Resolve destination
        dst = self.fs.resolve_path(dst_path)
        if dst and dst.is_dir():
            new_file = FSNode(src.name, "file", owner=USERNAME, group=USERNAME,
                              permissions=src.permissions, content=src.content, size=src.size)
            new_file.modified = datetime.now()
            dst.add_child(new_file)
        else:
            # Copy as new filename
            if "/" in dst_path:
                parent_path = "/".join(dst_path.split("/")[:-1])
                name = dst_path.split("/")[-1]
                parent = self.fs.resolve_path(parent_path)
                if parent is None:
                    return f"cp: cannot create regular file '{dst_path}': No such file or directory"
            else:
                parent = self.fs.cwd
                name = dst_path
            new_file = FSNode(name, "file", owner=USERNAME, group=USERNAME,
                              permissions=src.permissions, content=src.content, size=src.size)
            new_file.modified = datetime.now()
            parent.add_child(new_file)
        return ""

    def _cmd_mv(self, args: list) -> str:
        real_args = [a for a in args if not a.startswith("-")]
        if len(real_args) < 2:
            return "mv: missing file operand"
        src_path = real_args[0]
        dst_path = real_args[1]
        src = self.fs.resolve_path(src_path)
        if src is None:
            return f"mv: cannot stat '{src_path}': No such file or directory"

        # Remove from old location
        if src.parent:
            src.parent.remove_child(src.name)

        # Add to new location
        dst = self.fs.resolve_path(dst_path)
        if dst and dst.is_dir():
            dst.add_child(src)
        else:
            if "/" in dst_path:
                parent_path = "/".join(dst_path.split("/")[:-1])
                name = dst_path.split("/")[-1]
                parent = self.fs.resolve_path(parent_path)
                if parent is None:
                    return f"mv: cannot move '{src_path}' to '{dst_path}': No such file or directory"
            else:
                parent = self.fs.cwd
                name = dst_path
            src.name = name
            parent.add_child(src)
        return ""

    def _cmd_chmod(self, args: list) -> str:
        if len(args) < 2:
            return "chmod: missing operand"
        # Just acknowledge
        return ""

    def _cmd_stat(self, args: list) -> str:
        fname = None
        for a in args:
            if not a.startswith("-"):
                fname = a
                break
        if not fname:
            return "stat: missing operand"
        target = self.fs.resolve_path(fname)
        if target is None:
            return f"stat: cannot statx '{fname}': No such file or directory"
        ftype = "directory" if target.is_dir() else "regular file"
        return (
            f"  File: {target.name}\n"
            f"  Size: {target.size}\t\tBlocks: {(target.size // 512) + 1}\t\tIO Block: 4096   {ftype}\n"
            f"Access: ({target.format_permissions()})\tUid: ( 1000/   {target.owner})\tGid: ( 1000/   {target.group})\n"
            f"Modify: {target.modified.strftime('%Y-%m-%d %H:%M:%S.000000000 +0000')}\n"
            f"Change: {target.modified.strftime('%Y-%m-%d %H:%M:%S.000000000 +0000')}\n"
            f" Birth: -"
        )

    def _cmd_find(self, args: list) -> str:
        start_path = "."
        name_pattern = None
        i = 0
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                name_pattern = args[i+1]
                i += 2
            elif not args[i].startswith("-"):
                start_path = args[i]
                i += 1
            else:
                i += 1

        start = self.fs.resolve_path(start_path)
        if start is None:
            return f"find: '{start_path}': No such file or directory"

        results = []
        def _walk(node: FSNode, prefix: str):
            path = prefix + "/" + node.name if prefix else node.name
            if name_pattern:
                pattern = name_pattern.replace("*", "")
                if pattern in node.name:
                    results.append(path)
            else:
                results.append(path)
            if node.is_dir():
                for child in node.children.values():
                    _walk(child, path)

        if start.is_dir():
            results.append(start_path)
            for child in start.children.values():
                _walk(child, start_path)
        else:
            results.append(start_path)

        return "\n".join(results[:50])  # Cap output

    def _cmd_grep(self, args: list) -> str:
        if len(args) < 2:
            return "Usage: grep [OPTION]... PATTERNS [FILE]..."
        pattern = args[0]
        fname = args[1]
        target = self.fs.resolve_path(fname)
        if target is None:
            return f"grep: {fname}: No such file or directory"
        if target.is_dir():
            return f"grep: {fname}: Is a directory"
        matches = []
        for line in target.content.split("\n"):
            if pattern in line:
                matches.append(line)
        return "\n".join(matches ) if matches else ""

    # ──────────────────────────────────────────────
    # System info commands
    # ──────────────────────────────────────────────

    def _cmd_whoami(self, args: list) -> str:
        return USERNAME

    def _cmd_hostname(self, args: list) -> str:
        return HOSTNAME

    def _cmd_uname(self, args: list) -> str:
        if not args:
            return "Linux"
        if "-a" in args:
            return f"Linux {HOSTNAME} {KERNEL_VERSION} #1 SMP PREEMPT_DYNAMIC x86_64 x86_64 x86_64 GNU/Linux"
        if "-r" in args:
            return KERNEL_VERSION
        if "-n" in args:
            return HOSTNAME
        return "Linux"

    def _cmd_id(self, args: list) -> str:
        return "uid=1000(user) gid=1000(user) groups=1000(user),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev)"

    def _cmd_ps(self, args: list) -> str:
        if args and ("aux" in " ".join(args) or "ef" in " ".join(args)):
            return (
                "USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\n"
                "root           1  0.0  0.1 168940 11680 ?        Ss   00:01   0:03 /sbin/init\n"
                "root           2  0.0  0.0      0     0 ?        S    00:01   0:00 [kthreadd]\n"
                "root          47  0.0  0.0      0     0 ?        S    00:01   0:00 [kworker/0:1H]\n"
                "syslog       543  0.0  0.0 224344  5184 ?        Ssl  00:01   0:00 /usr/sbin/rsyslogd\n"
                "root         621  0.0  0.1  72308  6224 ?        Ss   00:01   0:00 /usr/sbin/sshd -D\n"
                "root         744  0.0  0.0   5600  1028 tty1     Ss+  00:01   0:00 /sbin/agetty -o -p -- \\u\n"
                f"user        1234  0.0  0.0  10072  3456 pts/0    Ss   {datetime.now().strftime('%H:%M')}   0:00 -bash\n"
                f"user        1301  0.0  0.0  10612  1232 pts/0    R+   {datetime.now().strftime('%H:%M')}   0:00 ps aux"
            )
        return (
            "    PID TTY          TIME CMD\n"
            f"   1234 pts/0    00:00:00 bash\n"
            f"   1301 pts/0    00:00:00 ps"
        )

    def _cmd_ifconfig(self, args: list) -> str:
        return (
            "eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
            "        inet 10.0.2.15  netmask 255.255.255.0  broadcast 10.0.2.255\n"
            "        inet6 fe80::a00:27ff:fea4:1b3c  prefixlen 64  scopeid 0x20<link>\n"
            "        ether 08:00:27:a4:1b:3c  txqueuelen 1000  (Ethernet)\n"
            "        RX packets 15234  bytes 12847392 (12.8 MB)\n"
            "        TX packets 8721  bytes 1284738 (1.2 MB)\n"
            "\n"
            "lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n"
            "        inet 127.0.0.1  netmask 255.0.0.0\n"
            "        inet6 ::1  prefixlen 128  scopeid 0x10<host>\n"
            "        loop  txqueuelen 1000  (Local Loopback)\n"
            "        RX packets 1024  bytes 102400 (102.4 KB)\n"
            "        TX packets 1024  bytes 102400 (102.4 KB)"
        )

    def _cmd_ip(self, args: list) -> str:
        if args and args[0] in ("a", "addr"):
            return (
                "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000\n"
                "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00\n"
                "    inet 127.0.0.1/8 scope host lo\n"
                "       valid_lft forever preferred_lft forever\n"
                "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000\n"
                "    link/ether 08:00:27:a4:1b:3c brd ff:ff:ff:ff:ff:ff\n"
                "    inet 10.0.2.15/24 brd 10.0.2.255 scope global dynamic eth0\n"
                "       valid_lft 86123sec preferred_lft 86123sec"
            )
        return f"Usage: ip [ OPTIONS ] OBJECT {{ COMMAND | help }}"

    def _cmd_history(self, args: list) -> str:
        hist_file = self.fs.resolve_path("~/.bash_history")
        if hist_file and hist_file.is_file():
            lines = hist_file.content.strip().split("\n")
            return "\n".join([f"  {i+1}  {line}" for i, line in enumerate(lines)])
        return ""

    def _cmd_clear(self, args: list) -> str:
        return "\033[2J\033[H"

    def _cmd_date(self, args: list) -> str:
        return datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")

    def _cmd_uptime(self, args: list) -> str:
        now = datetime.now()
        delta = now - self._boot_time
        hours = int(delta.total_seconds() // 3600)
        mins = int((delta.total_seconds() % 3600) // 60)
        return f" {now.strftime('%H:%M:%S')} up {hours}:{mins:02d},  1 user,  load average: 0.08, 0.03, 0.01"

    def _cmd_df(self, args: list) -> str:
        return (
            "Filesystem     1K-blocks    Used Available Use% Mounted on\n"
            "udev             1987432       0   1987432   0% /dev\n"
            "tmpfs             401784    1160    400624   1% /run\n"
            "/dev/sda1       30832636 8547312  20694888  30% /\n"
            "tmpfs            2008916       0   2008916   0% /dev/shm\n"
            "tmpfs               5120       4      5116   1% /run/lock\n"
            "/dev/sda15        106858    6186    100672   6% /boot/efi"
        )

    def _cmd_free(self, args: list) -> str:
        if args and "-h" in args:
            return (
                "              total        used        free      shared  buff/cache   available\n"
                "Mem:          3.9Gi       742Mi       2.4Gi        12Mi       780Mi       2.9Gi\n"
                "Swap:         2.0Gi          0B       2.0Gi"
            )
        return (
            "              total        used        free      shared  buff/cache   available\n"
            "Mem:        4017832      760288     2517120      12844     740424     2990116\n"
            "Swap:       2097148           0     2097148"
        )

    def _cmd_which(self, args: list) -> str:
        if not args:
            return ""
        known = {
            "ls": "/usr/bin/ls", "cat": "/usr/bin/cat", "grep": "/usr/bin/grep",
            "find": "/usr/bin/find", "bash": "/usr/bin/bash", "python3": "/usr/bin/python3",
            "ssh": "/usr/bin/ssh", "scp": "/usr/bin/scp", "curl": "/usr/bin/curl",
            "wget": "/usr/bin/wget", "nano": "/usr/bin/nano", "vim": "/usr/bin/vim",
            "git": "/usr/bin/git", "sudo": "/usr/bin/sudo", "apt": "/usr/bin/apt",
        }
        cmd = args[0]
        return known.get(cmd, f"{cmd} not found")

    def _cmd_file(self, args: list) -> str:
        if not args:
            return "Usage: file [-bchikLlNnprsvz0] [file ...]"
        target = self.fs.resolve_path(args[0])
        if target is None:
            return f"{args[0]}: cannot open (No such file or directory)"
        if target.is_dir():
            return f"{args[0]}: directory"
        name = target.name.lower()
        if name.endswith('.txt') or name.endswith('.md'):
            return f"{args[0]}: ASCII text"
        elif name.endswith('.py') or name.endswith('.sh'):
            return f"{args[0]}: Python/shell script, ASCII text executable"
        elif name.endswith('.pdf'):
            return f"{args[0]}: PDF document, version 1.7"
        elif name.endswith('.png') or name.endswith('.jpg'):
            return f"{args[0]}: image data"
        elif name.endswith('.zip') or name.endswith('.tar.gz') or name.endswith('.deb'):
            return f"{args[0]}: compressed data"
        return f"{args[0]}: data"

    def _cmd_env(self, args: list) -> str:
        return (
            f"USER={USERNAME}\n"
            f"HOME=/home/{USERNAME}\n"
            f"HOSTNAME={HOSTNAME}\n"
            "SHELL=/bin/bash\n"
            f"PWD={self.fs.get_pwd()}\n"
            "LANG=en_US.UTF-8\n"
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n"
            "TERM=xterm-256color\n"
            "LOGNAME=user\n"
            "SHLVL=1"
        )

    def _cmd_export(self, args: list) -> str:
        return ""

    # ──────────────────────────────────────────────
    # Network commands
    # ──────────────────────────────────────────────

    def _cmd_netstat(self, args: list) -> str:
        return (
            "Active Internet connections (servers and established)\n"
            "Proto Recv-Q Send-Q Local Address           Foreign Address         State\n"
            "tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN\n"
            "tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN\n"
            "tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN\n"
            "tcp        0      0 10.0.2.15:22            10.0.2.2:54312          ESTABLISHED\n"
            "tcp6       0      0 :::443                  :::*                    LISTEN\n"
            "udp        0      0 0.0.0.0:68              0.0.0.0:*"
        )

    def _cmd_ss(self, args: list) -> str:
        return (
            "Netid  State   Recv-Q  Send-Q    Local Address:Port     Peer Address:Port\n"
            "tcp    LISTEN  0       128       0.0.0.0:22              0.0.0.0:*\n"
            "tcp    LISTEN  0       511       0.0.0.0:80              0.0.0.0:*\n"
            "tcp    ESTAB   0       0         10.0.2.15:22            10.0.2.2:54312\n"
            "tcp    LISTEN  0       128       [::]:443                [::]:*"
        )

    def _cmd_ping(self, args: list) -> str:
        if not args:
            return "ping: usage error: Destination address required"
        host = args[-1]
        ip = f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        lines = [f"PING {host} ({ip}) 56(84) bytes of data."]
        for i in range(4):
            ms = round(random.uniform(5, 50), 1)
            lines.append(f"64 bytes from {ip}: icmp_seq={i+1} ttl=64 time={ms} ms")
        lines.append(f"\n--- {host} ping statistics ---")
        lines.append(f"4 packets transmitted, 4 received, 0% packet loss, time 3004ms")
        return "\n".join(lines)

    def _cmd_wget(self, args: list) -> str:
        url = args[-1] if args else ""
        return f"--{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}--  {url}\nResolving {url}... failed: Name or service not known.\nwget: unable to resolve host address '{url}'"

    def _cmd_curl(self, args: list) -> str:
        url = args[-1] if args else ""
        return f"curl: (6) Could not resolve host: {url}"

    # ──────────────────────────────────────────────
    # Privileged / dangerous commands (honeypot traps)
    # ──────────────────────────────────────────────

    def _cmd_sudo(self, args: list) -> str:
        if not args:
            return "usage: sudo [-AbEHnPS] [-C num] [-g group] [-h host] [-p prompt] [-u user] [command [args]]"
        subcmd = " ".join(args)
        if args[0] == "su":
            return "[sudo] password for user: \nuser is not in the sudoers file. This incident will be reported."
        return f"[sudo] password for user: \nSorry, user is not allowed to execute '{subcmd}' as root on {HOSTNAME}."

    def _cmd_su(self, args: list) -> str:
        return "Password: \nsu: Authentication failure"

    def _cmd_apt(self, args: list) -> str:
        if not args:
            return "apt 2.4.10 (amd64)"
        if args[0] in ("update", "upgrade", "install"):
            return f"E: Could not open lock file /var/lib/dpkg/lock-frontend - open (13: Permission denied)\nE: Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), are you root?"
        return f"apt 2.4.10 (amd64)"

    def _cmd_man(self, args: list) -> str:
        if not args:
            return "What manual page do you want?"
        return f"No manual entry for {args[0]}"

    def _cmd_less(self, args: list) -> str:
        return self._cmd_cat(args)

    def _cmd_more(self, args: list) -> str:
        return self._cmd_cat(args)

    def _cmd_nano(self, args: list) -> str:
        return "Error opening terminal: unknown."

    def _cmd_vi(self, args: list) -> str:
        return "Error opening terminal: unknown."

    def _cmd_vim(self, args: list) -> str:
        return "Error opening terminal: unknown."
