import subprocess
import threading
import time
import requests
from requests.exceptions import ProxyError, ConnectTimeout
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
proxies_collection = client["wireguard_db"]["proxies"]

def generate_wireguard_keys():
    try:
        private_key = subprocess.check_output("wg genkey", shell=True).strip()
        public_key = subprocess.check_output(f"echo {private_key.decode('utf-8')} | wg pubkey", shell=True).strip()
        return private_key.decode('utf-8'), public_key.decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error generating WireGuard keys: {e}")
        raise e
    
def generate_wireguard_config(client_id: str, private_key: str):
    server_public_key = os.getenv("SERVER_PUBLIC_KEY", "your_server_public_key")
    allowed_ips = "0.0.0.0/0"
    endpoint = os.getenv("SERVER_ENDPOINT", "server_ip:51820")
    config = f"""
    [Interface]
    PrivateKey = {private_key}
    Address = 10.0.0.{client_id}/24

    [Peer]
    PublicKey = {server_public_key}
    AllowedIPs = {allowed_ips}
    Endpoint = {endpoint}
    PersistentKeepalive = 25
    """
    return config.strip()

def test_proxy(proxy):
    try:
        proxies = {
            "http": proxy["proxy"],
            "https": proxy["proxy"]
        }
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
        if response.status_code == 200:
            return "good"
    except (ProxyError, ConnectTimeout):
        return "bad"
    return "bad"

def periodic_proxy_testing():
    while True:
        proxies = list(proxies_collection.find({"status": {"$ne": "bad"}}))
        for proxy in proxies:
            status = test_proxy(proxy)
            proxies_collection.update_one(
                {"ip_address": proxy["ip_address"]},
                {"$set": {"status": status}}
            )
        time.sleep(300)  # Sleep for 5 minutes

def start_periodic_testing():
    thread = threading.Thread(target=periodic_proxy_testing)
    thread.start()
