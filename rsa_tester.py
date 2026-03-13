import time
import threading
import paramiko
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("RSATester")

def ssh_connect(host, port, username, password, timeout=5):
    """Attempts an SSH connection. We don't care if it succeeds or fails, 
    just that the handshake happens so the honeypot catches the HASSH and connection."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # We just need to hit the server to trigger the RSA Detector
        client.connect(host, port=port, username=username, password=password, timeout=timeout)
        client.close()
        return True
    except Exception as e:
        # It might fail or aggressively close by the server, which is fine
        return False
    finally:
        client.close()

def simulate_burst_attack(host="127.0.0.1", port=2222, connections=12):
    """
    Simulates a Volumetric Burst Random Segment Assessment Attack.
    By default, GhostNet triggers at 10 connections within 30 seconds.
    We launch `connections` concurrently.
    """
    logger.info(f"🔥 Launching BURST ATTACK on {host}:{port} with {connections} concurrent connections...")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=connections) as executor:
        futures = []
        for i in range(connections):
            # Same username to increase similarity score
            futures.append(executor.submit(ssh_connect, host, port, "root", "password"))
            
        # Wait for all to complete
        for future in futures:
            future.result()
            
    elapsed = time.time() - start_time
    logger.info(f"✅ Burst attack completed in {elapsed:.2f} seconds.")
    logger.info("Check Streamlit Dashboard -> Intelligence -> RSA Alerts (Should be CRITICAL)")

def simulate_slow_drip_attack(host="127.0.0.1", port=2222, connections=22, delay=1.0):
    """
    Simulates a Slow-Drip Random Segment Assessment Attack.
    By default, GhostNet triggers if gaps are < 2.0s or hits 20 connections in 5 minutes.
    We loop and connect one-by-one with a `delay` gap.
    """
    logger.info(f"💧 Launching SLOW-DRIP ATTACK on {host}:{port}. {connections} connections, {delay}s delay between each...")
    
    start_time = time.time()
    
    for i in range(connections):
        logger.info(f"   [Slow-Drip] Connection {i+1}/{connections}...")
        ssh_connect(host, port, "root", "password")
        if i < connections - 1:
            time.sleep(delay)
            
    elapsed = time.time() - start_time
    logger.info(f"✅ Slow-drip attack completed in {elapsed:.2f} seconds.")
    logger.info("Check Streamlit Dashboard -> Intelligence -> RSA Alerts (Should be HIGH/MEDIUM)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GhostNet Random Segment Assessment Testing Utility")
    parser.add_argument("attack_type", choices=["burst", "drip"], help="Type of attack to simulate: 'burst' or 'drip'")
    parser.add_argument("--host", default="127.0.0.1", help="Target IP address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=2222, help="Target SSH port (default: 2222)")
    parser.add_argument("--count", type=int, help="Number of connections (default: 12 for burst, 22 for drip)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds for slow-drip attack (default: 1.0)")
    
    args = parser.parse_args()
    
    if args.attack_type == "burst":
        count = args.count if args.count else 12
        simulate_burst_attack(host=args.host, port=args.port, connections=count)
    elif args.attack_type == "drip":
        count = args.count if args.count else 22
        simulate_slow_drip_attack(host=args.host, port=args.port, connections=count, delay=args.delay)
