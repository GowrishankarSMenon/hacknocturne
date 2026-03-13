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
        etc.add_child(FSNode("hosts", "file", permissions="rw-r--r--", owner="root", group="root", size=221,
            content="127.0.0.1\tlocalhost\n127.0.1.1\tghostnet\n\n# The following lines are desirable for IPv6 capable hosts\n::1     ip6-localhost ip6-loopback\nfe00::0 ip6-localnet\nff00::0 ip6-mcastprefix\nff02::1 ip6-allnodes\nff02::2 ip6-allrouters\n"))
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

        # Randomized content pools
        doc_files = [
            ("report_2025.pdf", 245760, "rw-r--r--"),
            ("budget.xlsx", 67584, "rw-r--r--"),
            ("notes.txt", 1247, "rw-r--r--"),
            ("project_plan.docx", 189440, "rw-r--r--"),
            ("meeting_notes.md", 3521, "rw-r--r--"),
            ("invoice_march.pdf", 156672, "rw-r--r--"),
        ]
        desktop_files = [
            ("screenshot.png", 524288, "rw-r--r--"),
            ("todo.txt", 312, "rw-r--r--"),
            ("wallpaper.jpg", 2097152, "rw-r--r--"),
            ("shortcut.desktop", 245, "rw-r--r--"),
        ]
        download_files = [
            ("setup.sh", 4096, "rwxr-xr-x"),
            ("archive.tar.gz", 10485760, "rw-r--r--"),
            ("installer.deb", 52428800, "rw-r--r--"),
            ("config_backup.zip", 2097152, "rw-r--r--"),
            ("script.py", 2048, "rwxr-xr-x"),
        ]

        # Pick random subsets
        chosen_docs = random.sample(doc_files, k=random.randint(2, 4))
        chosen_desktop = random.sample(desktop_files, k=random.randint(1, 3))
        chosen_downloads = random.sample(download_files, k=random.randint(2, 4))

        # Create user directories
        documents = user_home.add_child(FSNode("Documents", "dir", owner="user", group="user"))
        desktop = user_home.add_child(FSNode("Desktop", "dir", owner="user", group="user"))
        downloads = user_home.add_child(FSNode("Downloads", "dir", owner="user", group="user"))
        pictures = user_home.add_child(FSNode("Pictures", "dir", owner="user", group="user"))
        music = user_home.add_child(FSNode("Music", "dir", owner="user", group="user"))
        videos = user_home.add_child(FSNode("Videos", "dir", owner="user", group="user"))

        for fname, fsize, fperm in chosen_docs:
            documents.add_child(FSNode(fname, "file", permissions=fperm, owner="user", group="user", size=fsize,
                                       content=f"[Binary content of {fname}]" if not fname.endswith('.txt') and not fname.endswith('.md') else self._random_text_content(fname)))
        for fname, fsize, fperm in chosen_desktop:
            desktop.add_child(FSNode(fname, "file", permissions=fperm, owner="user", group="user", size=fsize,
                                     content=f"[Binary content of {fname}]" if not fname.endswith('.txt') else self._random_text_content(fname)))
        for fname, fsize, fperm in chosen_downloads:
            downloads.add_child(FSNode(fname, "file", permissions=fperm, owner="user", group="user", size=fsize,
                                       content=f"[Binary content of {fname}]" if not fname.endswith('.sh') and not fname.endswith('.py') else self._random_text_content(fname)))

        # Dot files
        user_home.add_child(FSNode(".bashrc", "file", owner="user", group="user", permissions="rw-r--r--", size=3771,
            content='# ~/.bashrc: executed by bash(1) for non-login shells.\n\n# If not running interactively, don\'t do anything\ncase $- in\n    *i*) ;;\n      *) return;;\nesac\n\n# append to the history file\nshopt -s histappend\n\nHISTSIZE=1000\nHISTFILESIZE=2000\n\n# check the window size after each command\nshopt -s checkwinsize\n\n# set a fancy prompt\nPS1=\'${debian_chroot:+($debian_chroot)}\\u@\\h:\\w\\$ \'\n\n# enable color support of ls\nalias ls=\'ls --color=auto\'\nalias ll=\'ls -alF\'\nalias la=\'ls -A\'\nalias l=\'ls -CF\'\n'))
        user_home.add_child(FSNode(".bash_history", "file", owner="user", group="user", permissions="rw-------", size=2048,
            content="sudo apt update\nsudo apt upgrade -y\nls -la\ncd Documents\ncat notes.txt\npwd\nssh admin@192.168.1.1\npython3 script.py\nnmap -sV 10.0.0.0/24\ncurl https://api.example.com/data\nhistory\nwhoami\nifconfig\nnetstat -tlnp\n"))
        user_home.add_child(FSNode(".profile", "file", owner="user", group="user", permissions="rw-r--r--", size=807,
            content='# ~/.profile: executed by the command interpreter for login shells.\n\nif [ -n "$BASH_VERSION" ]; then\n    if [ -f "$HOME/.bashrc" ]; then\n        . "$HOME/.bashrc"\n    fi\nfi\n\nif [ -d "$HOME/bin" ] ; then\n    PATH="$HOME/bin:$PATH"\nfi\n'))
        user_home.add_child(FSNode(".ssh", "dir", owner="user", group="user", permissions="rwx------"))

        return root

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
