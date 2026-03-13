import paramiko
import threading
import socket
import logging
from datetime import datetime
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AeroGhostSSHServer(paramiko.ServerInterface):
    """
    Custom SSH Server that accepts any username/password
    and forwards commands to the AI backend.
    """

    def __init__(self, client_ip, log_callback=None):
        self.client_ip = client_ip
        self.username = None
        self.log_callback = log_callback
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def check_auth_password(self, username, password):
        """Accept any password"""
        self.username = username
        logger.info(f"[{self.session_id}] Auth attempt - User: {username} | IP: {self.client_ip}")
        
        if self.log_callback:
            self.log_callback({
                "timestamp": datetime.now().isoformat(),
                "event": "auth_attempt",
                "username": username,
                "ip": self.client_ip,
                "session_id": self.session_id
            })
        
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        """Accept shell channel requests"""
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        """Accept PTY requests"""
        return True

    def check_channel_shell_request(self, channel):
        """Accept shell requests"""
        return True

    def get_allowed_auths(self, username):
        """Tell client what auth methods are available"""
        return "password"


class SSHServerSocket:
    """
    SSH Server socket that listens for connections
    and spawns handler threads.
    """

    def __init__(self, host="0.0.0.0", port=2222, command_handler=None, live_feed_callback=None):
        self.host = host
        self.port = port
        self.command_handler = command_handler
        self.live_feed_callback = live_feed_callback
        self.running = False
        self.server_socket = None
        self.key_file = "logs/ssh_host_key"

    def _get_host_key(self):
        """Load or generate persistent SSH host key"""
        import os
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Try to load existing key
        if os.path.exists(self.key_file):
            logger.info("Loading existing SSH host key...")
            return paramiko.RSAKey(filename=self.key_file)
        
        # Generate new key and save it
        logger.info("Generating new SSH host key (will be reused)...")
        host_key = paramiko.RSAKey.generate(2048)
        host_key.write_private_key_file(self.key_file)
        logger.info(f"SSH host key saved to {self.key_file}")
        return host_key

    def start(self):
        """Start listening for SSH connections"""
        self.running = True
        
        # Load or generate persistent RSA key
        host_key = self._get_host_key()
        
        # Create socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(100)
            logger.info(f"SSH Server listening on {self.host}:{self.port}")
        except OSError as e:
            logger.error(f"Failed to bind to port {self.port}: {e}")
            raise

        # Accept connections in a loop
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_ip = addr[0]
                logger.info(f"Incoming connection from {client_ip}:{addr[1]}")
                
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_ip, host_key),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")

    def _handle_client(self, client_socket, client_ip, host_key):
        """Handle individual SSH client connection"""
        try:
            # Create SSH transport
            transport = paramiko.Transport(client_socket)
            transport.add_server_key(host_key)
            
            # Create server interface
            server = AeroGhostSSHServer(client_ip)
            transport.start_server(server=server)
            
            # Get the channel
            channel = transport.accept(20)
            if channel is None:
                logger.warning(f"SSH negotiation timeout for {client_ip}")
                return
            
            logger.info(f"SSH channel opened for {client_ip} (User: {server.username})")
            
            # Handle shell interaction
            self._handle_shell(channel, server.session_id, client_ip)
            
        except Exception as e:
            logger.error(f"Error handling SSH client {client_ip}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _handle_shell(self, channel, session_id, client_ip):
        """Handle interactive shell communication with proper keystroke buffering"""
        channel.send("user@aeroghost:~$ ")
        
        command_buffer = ""
        
        try:
            while True:
                # Read data from client (may be single keystrokes in PTY mode)
                data = channel.recv(1024)
                if not data:
                    break
                
                # Process each byte/character individually
                for byte in data:
                    char = chr(byte)
                    
                    # Handle Enter key (CR or LF)
                    if char in ("\r", "\n"):
                        channel.send("\r\n")
                        
                        command = command_buffer.strip()
                        command_buffer = ""
                        
                        # Clear live typing feed
                        if self.live_feed_callback:
                            self.live_feed_callback(session_id, "")
                        
                        if not command:
                            channel.send("user@aeroghost:~$ ")
                            continue
                        
                        # Handle exit — notify command_handler so DB session is closed
                        if command.lower() in ("exit", "quit"):
                            channel.send("logout\r\n")
                            # Clear live typing feed first
                            if self.live_feed_callback:
                                self.live_feed_callback(session_id, "")
                            # Notify main handler so it closes the DB session
                            if self.command_handler:
                                self.command_handler("exit", session_id, client_ip)
                            return
                        
                        logger.info(f"[{session_id}] Command: {command}")
                        
                        # Route command to LLM handler
                        if self.command_handler:
                            response = self.command_handler(command, session_id, client_ip)
                        else:
                            response = f"bash: {command.split()[0]}: command not found"
                        
                        # Send response
                        if response:
                            # Ensure proper line endings for terminal
                            response = response.replace("\n", "\r\n")
                            channel.send(response + "\r\n")
                        
                        channel.send("user@ghostnet:~$ ")
                    
                    # Handle Backspace (0x7f or 0x08)
                    elif byte in (0x7f, 0x08):
                        if command_buffer:
                            command_buffer = command_buffer[:-1]
                            # Update live feed
                            if self.live_feed_callback:
                                self.live_feed_callback(session_id, command_buffer)
                            # Erase character on client terminal
                            channel.send("\b \b")
                    
                    # Handle Ctrl+C
                    elif byte == 0x03:
                        command_buffer = ""
                        channel.send("^C\r\n")
                        channel.send("user@aeroghost:~$ ")
                        # Clear live feed
                        if self.live_feed_callback:
                            self.live_feed_callback(session_id, "")
                    
                    # Handle Ctrl+D (EOF)
                    elif byte == 0x04:
                        if not command_buffer:
                            channel.send("logout\r\n")
                            return
                    
                    # Handle regular printable characters
                    elif 32 <= byte < 127:
                        command_buffer += char
                        # Echo character back to client
                        channel.send(char)
                        # Update live feed with current buffer
                        if self.live_feed_callback:
                            self.live_feed_callback(session_id, command_buffer)
                    
                    # Ignore other control characters (arrow keys, etc.)
                    
        except Exception as e:
            logger.error(f"Error in shell handler for {session_id}: {e}")

    def stop(self):
        """Stop the SSH server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("SSH server stopped")


# Placeholder function for testing
def default_command_handler(command, session_id, client_ip):
    """Default command handler (to be replaced by AI handler)"""
    if command.lower() == "whoami":
        return "user"
    elif command.lower() == "pwd":
        return "/home/user"
    elif command.lower() == "ls":
        return "Documents  Downloads  Desktop"
    else:
        return f"bash: {command.split()[0]}: command not found"


if __name__ == "__main__":
    # Test the SSH server
    server = SSHServerSocket(port=2222, command_handler=default_command_handler)
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        server.stop()
