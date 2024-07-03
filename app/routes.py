from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from .models import ClientRegistration, ClientInfo, Proxy, ProxyUpdate, ProxyList
from .utils import generate_wireguard_keys, generate_wireguard_config, start_periodic_testing
import os

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["wireguard_db"]
clients_collection = db["clients"]
proxies_collection = db["proxies"]


@router.post("/register", response_model=ClientInfo)
def register_client(client: ClientRegistration):
    private_key, public_key = generate_wireguard_keys()
    wireguard_config = generate_wireguard_config(client.client_id, private_key)
    proxy_port = 8080  # Placeholder for proxy port

    new_client = {
        "client_id": client.client_id,
        "ip_address": None,
        "geo_location": client.geo_location,
        "internet_speed": client.internet_speed,
        "proxy_port": proxy_port,
        "last_connected": None,
        "wireguard_config": wireguard_config,
        "private_key": private_key,
        "public_key": public_key
    }
    clients_collection.insert_one(new_client)

    return {
        "client_id": client.client_id,
        "ip_address": None,
        "geo_location": client.geo_location,
        "internet_speed": client.internet_speed,
        "proxy_port": proxy_port,
        "wireguard_config": wireguard_config
    }

@router.post("/start_vpn/{client_id}")
def start_vpn(client_id: str):
    client = clients_collection.find_one({"client_id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    with open(f"/etc/wireguard/{client_id}.conf", "w") as f:
        f.write(client["wireguard_config"])

    os.system(f"wg-quick up /etc/wireguard/{client_id}.conf")
    return {"message": "VPN started"}

@router.post("/stop_vpn/{client_id}")
def stop_vpn(client_id: str):
    client = clients_collection.find_one({"client_id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    os.system(f"wg-quick down /etc/wireguard/{client_id}.conf")
    return {"message": "VPN stopped"}

@router.post("/proxy", response_model=dict)
def add_proxy(proxy: Proxy):
    new_proxy = {
        "ip_address": proxy.ip_address,
        "proxy": proxy.proxy,
        "proxy_type": proxy.proxy_type,
        "status": "unknown"
    }
    proxies_collection.insert_one(new_proxy)
    return {"message": "Proxy added successfully"}

@router.post("/proxies", response_model=dict)
def add_proxy_list(proxy_list: ProxyList):
    proxies = [
        {
            "ip_address": proxy.ip_address,
            "proxy": proxy.proxy,
            "proxy_type": proxy.proxy_type,
            "status": "unknown"
        } for proxy in proxy_list.proxies
    ]
    proxies_collection.insert_many(proxies)
    return {"message": "Proxy list added successfully"}

@router.put("/proxy/{ip_address}", response_model=dict)
def update_proxy(ip_address: str, proxy_update: ProxyUpdate):
    update_result = proxies_collection.update_one(
        {"ip_address": ip_address},
        {"$set": {"status": proxy_update.status}}
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"message": "Proxy status updated successfully"}

@router.delete("/proxy/{ip_address}", response_model=dict)
def delete_proxy(ip_address: str):
    delete_result = proxies_collection.delete_one({"ip_address": ip_address})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proxy not found")
    return {"message": "Proxy deleted successfully"}

@router.get("/proxies", response_model=list[Proxy])
def get_proxy_list():
    proxies = list(proxies_collection.find({}, {"_id": 0}))
    return proxies

start_periodic_testing()
