"""
AeroGhost Network Simulation — Lateral Movement Trap.
Defines fake internal network nodes that attackers can 'pivot' into
via ssh commands, keeping them in the honeypot while capturing
their lateral movement tactics.
"""

import logging
import random
from datetime import datetime
from state_manager.file_system import VirtualFileSystem, FSNode

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────
# Internal Network Node definitions
# ──────────────────────────────────────────────────

NETWORK_NODES = {
    # Node 1: Production Database
    "prod-db-01": {
        "ip": "10.0.1.50",
        "hostname": "prod-db-01",
        "os": "Ubuntu 22.04.3 LTS",
        "kernel": "5.15.0-91-generic",
        "role": "Production MySQL Database",
        "username": "dbadmin",
        "services": ["mysql", "sshd", "node_exporter"],
        "files": {
            "/home/dbadmin/.bash_history": (
                "mysql -u root -p\n"
                "mysqldump --all-databases > /tmp/full_backup.sql\n"
                "cat /etc/mysql/debian.cnf\n"
                "systemctl restart mysql\n"
                "tail -f /var/log/mysql/error.log\n"
            ),
            "/etc/mysql/debian.cnf": (
                "[client]\n"
                "host     = localhost\n"
                "user     = debian-sys-maint\n"
                "password = aF7kP2mN9xQ4wR1t\n"
                "socket   = /var/run/mysqld/mysqld.sock\n"
            ),
            "/var/log/mysql/error.log": (
                "2024-01-15T03:21:44.123456Z 0 [Warning] Changed limits: max_open_files: 1024\n"
                "2024-01-15T03:21:44.456789Z 0 [Note] /usr/sbin/mysqld: ready for connections.\n"
                "2024-01-15T08:15:33.789012Z 142 [Warning] Aborted connection 142 to db: 'users_prod'\n"
            ),
            "/tmp/full_backup.sql": (
                "-- MySQL dump 8.0.35\n"
                "-- Host: localhost    Database: users_prod\n"
                "CREATE TABLE `customers` (\n"
                "  `id` int NOT NULL AUTO_INCREMENT,\n"
                "  `email` varchar(255),\n"
                "  `ssn` varchar(11),\n"
                "  `credit_card` varchar(19),\n"
                "  PRIMARY KEY (`id`)\n"
                ") ENGINE=InnoDB;\n"
                "INSERT INTO `customers` VALUES (1,'john@example.com','123-45-6789','4111-1111-1111-1111');\n"
                "INSERT INTO `customers` VALUES (2,'jane@corp.io','987-65-4321','5500-0000-0000-0004');\n"
            ),
        }
    },

    # Node 2: Dev API Server
    "dev-api-02": {
        "ip": "10.0.1.51",
        "hostname": "dev-api-02",
        "os": "Ubuntu 22.04.3 LTS",
        "kernel": "5.15.0-88-generic",
        "role": "Development API Server",
        "username": "deploy",
        "services": ["nginx", "node", "sshd", "redis-server"],
        "files": {
            "/home/deploy/.bash_history": (
                "cd /opt/api\n"
                "npm run build\n"
                "pm2 restart all\n"
                "cat .env.production\n"
                "redis-cli KEYS '*session*'\n"
            ),
            "/opt/api/.env.production": (
                "NODE_ENV=production\n"
                "DATABASE_URL=mysql://root:aF7kP2mN9xQ4wR1t@10.0.1.50:3306/users_prod\n"
                "REDIS_URL=redis://localhost:6379\n"
                "JWT_SECRET=hp_jwt_7f3d2c1b9e4a8f6e2d5c8b1a4e7f0d3c\n"
                "CLOUD_KEY_ID=HONEYPOT-ACCESS-KEY-ID-DEMO12\n"
                "CLOUD_KEY_SECRET=Hp0nEyP0t+CloudKeyExampleDemoSecretVal2024\n"
                "PAYMENT_KEY=honeypot_payment_key_51Hx8vP2eZvKY_demo\n"
            ),
            "/opt/api/package.json": (
                '{"name": "aeroghost-api", "version": "2.1.0", '
                '"scripts": {"start": "node server.js", "build": "tsc"}, '
                '"dependencies": {"express": "^4.18.2", "mysql2": "^3.6.0"}}\n'
            ),
            "/var/log/nginx/access.log": (
                '10.0.1.1 - - [15/Jan/2024:08:23:11 +0000] "GET /api/users HTTP/1.1" 200 1234\n'
                '10.0.1.1 - - [15/Jan/2024:08:23:15 +0000] "POST /api/auth/login HTTP/1.1" 200 89\n'
                '185.234.72.11 - - [15/Jan/2024:09:45:02 +0000] "GET /api/admin HTTP/1.1" 403 12\n'
            ),
        }
    },

    # Node 3: Monitoring Server
    "monitoring": {
        "ip": "10.0.1.52",
        "hostname": "monitoring",
        "os": "Debian 12",
        "kernel": "6.1.0-13-amd64",
        "role": "Monitoring & Alerting",
        "username": "monitor",
        "services": ["grafana-server", "prometheus", "sshd", "alertmanager"],
        "files": {
            "/home/monitor/.bash_history": (
                "systemctl status grafana-server\n"
                "curl localhost:9090/api/v1/targets\n"
                "cat /etc/grafana/grafana.ini\n"
            ),
            "/etc/grafana/grafana.ini": (
                "[security]\n"
                "admin_user = admin\n"
                "admin_password = Gr4f4n4_Pr0d_2024!\n"
                "\n[database]\n"
                "type = sqlite3\n"
                "path = grafana.db\n"
                "\n[server]\n"
                "http_port = 3000\n"
                "domain = monitoring.internal\n"
            ),
            "/etc/prometheus/prometheus.yml": (
                "global:\n"
                "  scrape_interval: 15s\n\n"
                "scrape_configs:\n"
                "  - job_name: 'prod-db'\n"
                "    static_configs:\n"
                "      - targets: ['10.0.1.50:9100']\n"
                "  - job_name: 'dev-api'\n"
                "    static_configs:\n"
                "      - targets: ['10.0.1.51:9100']\n"
            ),
        }
    },

    # Node 4: Backup Server
    "backup-srv": {
        "ip": "10.0.1.53",
        "hostname": "backup-srv",
        "os": "Ubuntu 20.04.6 LTS",
        "kernel": "5.4.0-169-generic",
        "role": "Backup & Archive Server",
        "username": "backup",
        "services": ["sshd", "rsync", "cron"],
        "files": {
            "/home/backup/.bash_history": (
                "rsync -avz dbadmin@10.0.1.50:/tmp/full_backup.sql /backups/db/\n"
                "tar czf /backups/archive_2024-01-15.tar.gz /backups/db/\n"
                "ls -la /backups/\n"
                "gpg --decrypt /backups/keys/master.key.gpg\n"
            ),
            "/backups/db/full_backup.sql": (
                "-- Backup from prod-db-01 on 2024-01-15\n"
                "CREATE TABLE `credentials` (\n"
                "  `service` varchar(64),\n"
                "  `username` varchar(64),\n"
                "  `password` varchar(255)\n"
                ");\n"
                "INSERT INTO `credentials` VALUES ('aws-console','admin@corp.io','CloudP@ss2024!');\n"
                "INSERT INTO `credentials` VALUES ('github','devops-bot','ghp_FAKE_TOKEN_xxxxxxxxxxxx');\n"
            ),
            "/backups/keys/id_rsa": (
                "-----BEGIN OPENSSH PRIVATE KEY-----\n"
                "b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW\n"
                "QyNTUxOQAAACCFAKEKEYDATA1234567890abcdefghijklmnopqrstuvwxyz\n"
                "AAAANkZha2Uga2V5IGRhdGEgZm9yIGhvbmV5cG90AAAAAAAAAA==\n"
                "-----END OPENSSH PRIVATE KEY-----\n"
            ),
            "/backups/keys/master.key.gpg": (
                "[binary GPG encrypted data - use gpg --decrypt to access]\n"
            ),
        }
    },
}

# Map IPs to hostnames for quick lookup
IP_TO_NODE = {node["ip"]: name for name, node in NETWORK_NODES.items()}
# Also allow hostname-based lookups
HOSTNAME_TO_NODE = {name: name for name in NETWORK_NODES}


def build_node_filesystem(node_name: str) -> VirtualFileSystem:
    """
    Build a VirtualFileSystem for a network node,
    populated with its role-specific files.
    """
    if node_name not in NETWORK_NODES:
        return None

    node = NETWORK_NODES[node_name]
    fs = VirtualFileSystem()

    # Override home directory user
    username = node["username"]

    # Update hostname in /etc/hostname
    hostname_file = fs.resolve_path("/etc/hostname")
    if hostname_file:
        hostname_file.content = node["hostname"] + "\n"

    # Add node-specific files
    for filepath, content in node["files"].items():
        parts = filepath.strip("/").split("/")
        current = fs.root

        # Create intermediate directories
        for i, part in enumerate(parts[:-1]):
            child = current.get_child(part)
            if child is None:
                new_dir = FSNode(part, "dir", owner="root", group="root")
                current.add_child(new_dir)
                current = new_dir
            else:
                current = child

        # Create the file
        filename = parts[-1]
        file_node = FSNode(
            filename, "file",
            owner=username, group=username,
            permissions="rw-r-----",
            content=content,
            size=len(content.encode("utf-8"))
        )
        current.add_child(file_node)

    return fs


def get_node_info(node_name: str) -> dict:
    """Get metadata about a network node."""
    return NETWORK_NODES.get(node_name)


def resolve_target(target: str) -> str:
    """
    Resolve an SSH target to a node name.
    Accepts: IP address, hostname, or user@host format.
    Returns node name or None.
    """
    # Strip user@ prefix if present
    if "@" in target:
        target = target.split("@", 1)[1]

    # Check by IP
    if target in IP_TO_NODE:
        return IP_TO_NODE[target]

    # Check by hostname
    if target in HOSTNAME_TO_NODE:
        return HOSTNAME_TO_NODE[target]

    return None
