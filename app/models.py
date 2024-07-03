from pydantic import BaseModel

class ClientRegistration(BaseModel):
    client_id: str
    geo_location: str
    internet_speed: str

class ClientInfo(BaseModel):
    client_id: str
    ip_address: str = None
    geo_location: str
    internet_speed: str
    proxy_port: int

class Proxy(BaseModel):
    ip_address: str
    proxy: str
    proxy_type: str = "all"

class ProxyUpdate(BaseModel):
    status: str

class ProxyList(BaseModel):
    proxies: list[Proxy]
