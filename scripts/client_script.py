import os
import json
import requests
import subprocess

# Replace these variables with appropriate values
API_URL = "http://localhost:8000"
CLIENT_ID = "client_id"
GEO_LOCATION = "geo_location"
INTERNET_SPEED = "20Mbps"
WG_CONF_PATH = "/etc/wireguard/wg0.conf"

def register_client():
    payload = {
        "client_id": CLIENT_ID,
        "geo_location": GEO_LOCATION,
        "internet_speed": INTERNET_SPEED
    }
    response = requests.post(f"{API_URL}/register", json=payload)
    response.raise_for_status() 
    return response.json()

def write_wireguard_config(config, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(config)

def setup_wireguard():
    subprocess.run(["wg-quick", "up", "wg0"], check=True)

def install_tinyproxy():
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "tinyproxy"], check=True)

def configure_tinyproxy(port):
    conf_path = "/etc/tinyproxy/tinyproxy.conf"
    with open(conf_path, 'r') as file:
        conf = file.readlines()
    with open(conf_path, 'w') as file:
        for line in conf:
            if line.startswith("Port "):
                file.write(f"Port {port}\n")
            else:
                file.write(line)
    subprocess.run(["systemctl", "restart", "tinyproxy"], check=True)

def enable_ip_forwarding():
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

def setup_iptables(proxy_port):
    subprocess.run(["iptables", "-t", "nat", "-A", "PREROUTING", "-i", "wg0", "-p", "tcp", "--dport", "8888", "-j", "REDIRECT", "--to-port", str(proxy_port)], check=True)

def main():
    # Register the client and get the WireGuard configuration
    client_info = register_client()
    wireguard_config = client_info["wireguard_config"]
    proxy_port = client_info["proxy_port"]

    # Write the WireGuard configuration to the file
    write_wireguard_config(wireguard_config, WG_CONF_PATH)

    # Set up WireGuard
    setup_wireguard()

    # Install TinyProxy if not already installed
    if subprocess.run(["which", "tinyproxy"], capture_output=True).returncode != 0:
        install_tinyproxy()

    # Configure TinyProxy
    configure_tinyproxy(proxy_port)

    # Enable IP forwarding
    enable_ip_forwarding()

    # Set up IP tables for TinyProxy
    setup_iptables(proxy_port)

    print("WireGuard and TinyProxy setup completed.")

if __name__ == "__main__":
    main()
