"""
GhostNet Virtual Filesystem - Tree-based directory structure.
Each directory is a node with children (subdirs) and files.
Each session gets its own independent filesystem tree.
"""

import json
import os
import random
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


class FSNode:
    """
    A single node in the virtual filesystem tree.
    Can be either a directory (has children) or a file (has content).
    """

    def __init__(self, name: str, node_type: str = "dir", parent=None,
                 content: str = "", permissions: str = "rwxr-xr-x",
                 owner: str = "user", group: str = "user", size: int = 0):
        self.name = name
        self.node_type = node_type  # "dir" or "file"
        self.parent = parent
        self.content = content  # file content (files only)
        self.children: Dict[str, 'FSNode'] = {}  # name -> FSNode (dirs only)
        self.permissions = permissions
        self.owner = owner
        self.group = group
        self.size = size if size else len(content.encode('utf-8'))
        self.modified = datetime.now() - timedelta(
            days=random.randint(1, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

    def is_dir(self) -> bool:
        return self.node_type == "dir"

    def is_file(self) -> bool:
        return self.node_type == "file"

    def add_child(self, child: 'FSNode') -> 'FSNode':
        """Add a child node to this directory."""
        child.parent = self
        self.children[child.name] = child
        return child

    def remove_child(self, name: str) -> bool:
        """Remove a child node by name."""
        if name in self.children:
            del self.children[name]
            return True
        return False

    def get_child(self, name: str) -> Optional['FSNode']:
        """Get a child node by name."""
        return self.children.get(name)

    def get_path(self) -> str:
        """Walk up the tree to build the full path string."""
        if self.parent is None:
            return "/"  # This is the root node
        parts = []
        node = self
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def format_permissions(self) -> str:
        """Format permissions for ls -l output."""
        prefix = "d" if self.is_dir() else "-"
        return prefix + self.permissions

    def format_ls_long(self) -> str:
        """Format a single ls -l line for this node."""
        perm = self.format_permissions()
        links = str(len(self.children) + 2) if self.is_dir() else "1"
        size = str(self.size) if self.is_file() else str(4096)
        date_str = self.modified.strftime("%b %d %H:%M")
        return f"{perm} {links:>3} {self.owner:>6} {self.group:>6} {size:>8} {date_str} {self.name}"


class VirtualFileSystem:
    """
    Tree-based virtual filesystem for GhostNet.
    Provides a realistic Linux filesystem simulation.
    """

    def __init__(self):
        self.root = self._build_tree()
        # Set cwd to /home/user
        self.cwd = self.root.get_child("home").get_child("user")
        self.home_dir = self.cwd  # reference for cd ~

    def _build_tree(self) -> FSNode:
        """Build a realistic randomized Linux filesystem tree."""
        root = FSNode("/", "dir", permissions="rwxr-xr-x", owner="root", group="root")

        # --- Standard system directories ---
        etc = root.add_child(FSNode("etc", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        var = root.add_child(FSNode("var", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        tmp = root.add_child(FSNode("tmp", "dir", permissions="rwxrwxrwt", owner="root", group="root"))
        usr = root.add_child(FSNode("usr", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        home = root.add_child(FSNode("home", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("bin", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("sbin", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("dev", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("proc", "dir", permissions="r-xr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("opt", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("srv", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        root.add_child(FSNode("boot", "dir", permissions="rwxr-xr-x", owner="root", group="root"))

        # /etc files
        etc.add_child(FSNode("hostname", "file", content="ghostnet\n", permissions="rw-r--r--", owner="root", group="root", size=9))
        etc.add_child(FSNode("passwd", "file", permissions="rw-r--r--", owner="root", group="root", size=1847,
            content="root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nbin:x:2:2:bin:/bin:/usr/sbin/nologin\nsys:x:3:3:sys:/dev:/usr/sbin/nologin\nsync:x:4:65534:sync:/bin:/bin/sync\ngames:x:5:60:games:/usr/games:/usr/sbin/nologin\nman:x:6:12:man:/var/cache/man:/usr/sbin/nologin\nlp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin\nmail:x:8:8:mail:/var/mail:/usr/sbin/nologin\nnews:x:9:9:news:/var/spool/news:/usr/sbin/nologin\nuser:x:1000:1000:user:/home/user:/bin/bash\n"))
        etc.add_child(FSNode("shadow", "file", content="", permissions="rw-------", owner="root", group="shadow", size=1203))
        etc.add_child(FSNode("hosts", "file", permissions="rw-r--r--", owner="root", group="root", size=420,
            content=(
                "127.0.0.1\tlocalhost\n"
                "127.0.1.1\taeroghost\n\n"
                "# Internal network\n"
                "10.0.1.50\tprod-db-01 prod-db-01.internal\n"
                "10.0.1.51\tdev-api-02 dev-api-02.internal\n"
                "10.0.1.52\tmonitoring monitoring.internal\n"
                "10.0.1.53\tbackup-srv backup-srv.internal\n\n"
                "# IPv6\n"
                "::1     ip6-localhost ip6-loopback\n"
                "fe00::0 ip6-localnet\n"
                "ff02::1 ip6-allnodes\n"
            )))
        etc.add_child(FSNode("os-release", "file", permissions="rw-r--r--", owner="root", group="root", size=393,
            content='PRETTY_NAME="Ubuntu 22.04.3 LTS"\nNAME="Ubuntu"\nVERSION_ID="22.04"\nVERSION="22.04.3 LTS (Jammy Jellyfish)"\nVERSION_CODENAME=jammy\nID=ubuntu\nID_LIKE=debian\nHOME_URL="https://www.ubuntu.com/"\nSUPPORT_URL="https://help.ubuntu.com/"\nBUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"\nPRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"\nUBUNTU_CODENAME=jammy\n'))
        etc.add_child(FSNode("resolv.conf", "file", content="nameserver 8.8.8.8\nnameserver 8.8.4.4\n", permissions="rw-r--r--", owner="root", group="root", size=50))

        # /var/log
        var_log = var.add_child(FSNode("log", "dir", permissions="rwxr-xr-x", owner="root", group="syslog"))
        var_log.add_child(FSNode("syslog", "file", content="", permissions="rw-r-----", owner="syslog", group="adm", size=524288))
        var_log.add_child(FSNode("auth.log", "file", content="", permissions="rw-r-----", owner="syslog", group="adm", size=131072))
        var_log.add_child(FSNode("kern.log", "file", content="", permissions="rw-r-----", owner="syslog", group="adm", size=65536))

        # /usr
        usr_bin = usr.add_child(FSNode("bin", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        usr.add_child(FSNode("lib", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        usr.add_child(FSNode("share", "dir", permissions="rwxr-xr-x", owner="root", group="root"))
        usr.add_child(FSNode("local", "dir", permissions="rwxr-xr-x", owner="root", group="root"))

        # --- /home/user ---
        user_home = home.add_child(FSNode("user", "dir", permissions="rwxr-xr-x", owner="user", group="user"))

        # Generate Deep Thematic Networks
        self._generate_themed_network(user_home, "Documents", max_depth=5)
        self._generate_themed_network(user_home, "Desktop", max_depth=3)
        self._generate_themed_network(user_home, "Downloads", max_depth=4)
        self._generate_themed_network(user_home, "Pictures", max_depth=5)
        self._generate_themed_network(user_home, "Music", max_depth=5)
        self._generate_themed_network(user_home, "Videos", max_depth=4)

        # Inject dotfiles LAST — guarantees they can't be overwritten by themed generation
        self._inject_dotfiles(user_home)

        return root

    def _inject_dotfiles(self, user_home: FSNode):
        """
        Create dotfiles (.bashrc, .bash_history, .profile, .ssh) in user's home.
        Called LAST in _build_tree to ensure these files are always present.
        """
        user_home.add_child(FSNode(".bashrc", "file", owner="user", group="user", permissions="rw-r--r--", size=3771,
            content='# ~/.bashrc: executed by bash(1) for non-login shells.\n\n# If not running interactively, don\'t do anything\ncase $- in\n    *i*) ;;\n      *) return;;\nesac\n\n# append to the history file\nshopt -s histappend\n\nHISTSIZE=1000\nHISTFILESIZE=2000\n\n# check the window size after each command\nshopt -s checkwinsize\n\n# set a fancy prompt\nPS1=\'${debian_chroot:+($debian_chroot)}\\u@\\h:\\w\\$ \'\n\n# enable color support of ls\nalias ls=\'ls --color=auto\'\nalias ll=\'ls -alF\'\nalias la=\'ls -A\'\nalias l=\'ls -CF\'\n'))
        user_home.add_child(FSNode(".bash_history", "file", owner="user", group="user", permissions="rw-------", size=2048,
            content=(
                "sudo apt update\n"
                "sudo apt upgrade -y\n"
                "ls -la\n"
                "cat /etc/hosts\n"
                "ping prod-db-01\n"
                "ssh dbadmin@10.0.1.50\n"
                "mysql -h 10.0.1.50 -u root -p\n"
                "ssh deploy@dev-api-02\n"
                "cat /opt/api/.env.production\n"
                "ssh monitor@10.0.1.52\n"
                "ssh backup@backup-srv\n"
                "scp backup@10.0.1.53:/backups/db/full_backup.sql /tmp/\n"
                "nmap -sV 10.0.1.0/24\n"
                "arp -a\n"
                "netstat -tlnp\n"
                "whoami\n"
                "ifconfig\n"
                "history\n"
            )))
        # SSH known_hosts — attackers find pivot targets by reading this
        ssh_dir = user_home.add_child(FSNode(".ssh", "dir", owner="user", group="user", permissions="rwx------"))
        ssh_dir.add_child(FSNode("known_hosts", "file", owner="user", group="user", permissions="rw-------",
            content=(
                "prod-db-01,10.0.1.50 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTIt...prod\n"
                "dev-api-02,10.0.1.51 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTIt...dev\n"
                "monitoring,10.0.1.52 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTIt...mon\n"
                "backup-srv,10.0.1.53 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTIt...bak\n"
            )))

    def _generate_binary_rubbish(self, size: int = 500) -> str:
        """Generate random unprintable ascii and hex bytes to simulate opening a binary file."""
        # Mix of standard ascii, extended ascii, and control characters to create that classic terminal 'rubbish' look
        chars = [chr(random.randint(1, 255)) for _ in range(size)]
        return "".join(chars)

    def _generate_themed_network(self, parent_node: FSNode, theme: str, max_depth: int, current_depth: int = 1):
        """Recursively generate a directory tree with thematic subfolders and files."""
        if current_depth > max_depth:
            return

        # Create the directory for this level
        if current_depth == 1:
            dir_name = theme
        else:
            # Theme-appropriate subfolder names
            subfolders = {
                "Documents": ["2024", "2025", "Projects", "Confidential", "Financials", "Drafts", "Archives", "Meetings"],
                "Desktop": ["Shortcuts", "Temp", "Work", "ToOrganize"],
                "Downloads": ["Software", "Torrents", "PDFs", "ISOs", "Updates"],
                "Pictures": ["Vacation", "Family", "Screenshots", "Wallpapers", "Camera_Roll", "2024_Trip", "Memes"],
                "Music": ["Playlists", "Mixes", "Albums", "Podcasts", "Workout", "Chill", "Live_Sets"],
                "Videos": ["Movies", "Clips", "Recordings", "Tutorials", "CCTV", "Exports"]
            }
            dir_name = random.choice(subfolders.get(theme, ["Misc", "Data", "Old"]))

        # Check if dir already exists (can happen at root depth), if so just use it
        existing = parent_node.get_child(dir_name)
        if existing and existing.is_dir():
            current_dir = existing
        else:
            current_dir = parent_node.add_child(FSNode(dir_name, "dir", owner="user", group="user"))

        # Decide how many files to generate in this directory (fewer at deeper levels usually)
        num_files = random.randint(0, 5) if current_depth > 1 else random.randint(2, 6)
        
        # Themed file generation
        for i in range(num_files):
            file_configs = {
                "Documents": [
                    ("report_{}.pdf", [2024, 2025, "Q1", "final"]),
                    ("budget_{}.xlsx", ["draft", "final", "2025"]),
                    ("notes_{}.txt", ["meeting", "project", "urgent"]),
                    ("plan_{}.docx", ["draft", "Q4", "strategy"])
                ],
                "Desktop": [
                    ("screenshot_{}.png", [random.randint(100, 999), "login", "error"]),
                    ("shortcut_{}.desktop", ["app", "game", "tool"]),
                    ("todo_{}.txt", ["work", "personal"])
                ],
                "Downloads": [
                    ("installer_v{}.deb", ["1.0", "2.4", "beta"]),
                    ("archive_{}.tar.gz", ["backup", "src", "data"]),
                    ("setup_{}.sh", ["env", "db", "tools"]),
                    ("manual_{}.pdf", ["v1", "v2", "english"])
                ],
                "Pictures": [
                    ("IMG_{}.jpg", [random.randint(1000, 9999)]),
                    ("DSC_{}.png", [random.randint(1000, 9999)]),
                    ("wallpaper_{}.jpg", ["nature", "dark", "abstract"])
                ],
                "Music": [
                    ("track_{}.mp3", [random.randint(1, 20), "intro", "outro"]),
                    ("mix_{}.wav", ["summer", "workout", "chill"]),
                    ("podcast_ep_{}.mp3", [random.randint(1, 150)])
                ],
                "Videos": [
                    ("vid_{}.mp4", [random.randint(1000, 9999)]),
                    ("movie_{}.mkv", ["rip", "hd", "cam"]),
                    ("recording_{}.mp4", ["zoom", "meet", "cctv"])
                ]
            }

            theme_configs = file_configs.get(theme, file_configs["Documents"])
            chosen_template, chosen_args = random.choice(theme_configs)
            fname = chosen_template.format(random.choice(chosen_args))

            # File attributes
            fsize = random.randint(1024, 52428800)  # Random size 1KB - 50MB
            
            # Executables get execute permissions
            fperm = "rwxr-xr-x" if fname.endswith(('.sh', '.py')) else "rw-r--r--"

            # Is it a text file?
            is_text = fname.endswith(('.txt', '.md', '.sh', '.py'))
            if is_text:
                content = self._random_text_content(fname)
            else:
                # Generate binary rubbish for non-text files, keep length reasonable to not lag the browser
                content = self._generate_binary_rubbish(size=random.randint(2000, 5000))

            current_dir.add_child(FSNode(fname, "file", permissions=fperm, owner="user", group="user", size=fsize, content=content))

        # Recursively create subdirectories 
        # (Lower probability of branching at deeper levels to prevent exploding trees)
        if current_depth < max_depth:
            num_subdirs = random.randint(0, 3) if current_depth > 2 else random.randint(1, 4)
            for _ in range(num_subdirs):
                self._generate_themed_network(current_dir, theme, max_depth, current_depth + 1)

    def _random_text_content(self, filename: str) -> str:
        """Generate random text content for text files."""
        contents = {
            "notes.txt": "Meeting at 3pm tomorrow\nRemember to update the server configs\nCheck backup status\nCall vendor about renewal\n",
            "todo.txt": "- Finish project report\n- Update server packages\n- Review security logs\n- Backup database\n- Schedule maintenance window\n",
            "meeting_notes.md": "# Team Meeting Notes\n\n## Date: 2025-03-01\n\n### Action Items\n- Deploy staging environment\n- Run security audit\n- Update firewall rules\n\n### Notes\n- Server migration scheduled for next week\n- New monitoring tools to be evaluated\n",
            "setup.sh": "#!/bin/bash\n# Server setup script\napt-get update && apt-get upgrade -y\napt-get install -y nginx postgresql python3-pip\nsystemctl enable nginx\nsystemctl start nginx\necho 'Setup complete'\n",
            "script.py": "#!/usr/bin/env python3\nimport os\nimport sys\n\ndef main():\n    print('Running system check...')\n    os.system('df -h')\n    os.system('free -m')\n    print('Check complete.')\n\nif __name__ == '__main__':\n    main()\n",
        }
        return contents.get(filename, f"Contents of {filename}\n")

    def resolve_path(self, path: str) -> Optional[FSNode]:
        """
        Resolve a path string to an FSNode.
        Supports absolute paths, relative paths, ~, .., and .
        """
        if not path:
            return self.cwd

        # Handle ~
        if path == "~" or path == "~/" :
            return self.home_dir
        if path.startswith("~/"):
            path = path[2:]
            current = self.home_dir
        elif path.startswith("/"):
            current = self.root
            path = path[1:]  # strip leading /
        else:
            current = self.cwd

        if not path:
            return current

        parts = path.split("/")
        for part in parts:
            if not part or part == ".":
                continue
            elif part == "..":
                current = current.parent if current.parent else current
            else:
                child = current.get_child(part)
                if child is None:
                    return None
                current = child

        return current

    def get_pwd(self) -> str:
        """Get the current working directory path."""
        path = self.cwd.get_path()
        # Replace /home/user with ~ in display? No, pwd should show full path
        return path

    def save_to_json(self, filepath: str):
        """Serialize filesystem to JSON."""
        def _serialize(node: FSNode) -> dict:
            data = {
                "name": node.name,
                "type": node.node_type,
                "permissions": node.permissions,
                "owner": node.owner,
                "group": node.group,
                "size": node.size,
                "modified": node.modified.isoformat(),
            }
            if node.is_file():
                data["content"] = node.content
            if node.is_dir():
                data["children"] = {name: _serialize(child) for name, child in node.children.items()}
            return data

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(_serialize(self.root), f, indent=2)

    def load_from_json(self, filepath: str):
        """Deserialize filesystem from JSON."""
        def _deserialize(data: dict, parent: Optional[FSNode] = None) -> FSNode:
            node = FSNode(
                name=data["name"],
                node_type=data["type"],
                parent=parent,
                content=data.get("content", ""),
                permissions=data.get("permissions", "rwxr-xr-x"),
                owner=data.get("owner", "user"),
                group=data.get("group", "user"),
                size=data.get("size", 0)
            )
            node.modified = datetime.fromisoformat(data["modified"])
            if "children" in data:
                for name, child_data in data["children"].items():
                    child = _deserialize(child_data, node)
                    node.children[name] = child
            return node

        with open(filepath, 'r') as f:
            data = json.load(f)
        self.root = _deserialize(data)
        # Re-resolve home
        home_node = self.root.get_child("home")
        if home_node:
            user_node = home_node.get_child("user")
            if user_node:
                self.cwd = user_node
                self.home_dir = user_node
