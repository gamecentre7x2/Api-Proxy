from pydantic import BaseModel
from enum import Enum
from typing import Optional

class Protocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

class Anonymity(str, Enum):
    ELITE = "elite"
    ANONYMOUS = "anonymous"
    TRANSPARENT = "transparent"

class ProxyEntry(BaseModel):
    ip: str
    port: int
    protocol: Protocol
    anonymity: Optional[Anonymity] = None
    response_time: Optional[float] = None  # milliseconds
    last_checked: Optional[str] = None     # ISO timestamp

# Schema for API response
class ProxyResponse(BaseModel):
    proxy: str  # e.g., "socks5://127.0.0.1:1080"
    protocol: Protocol
    anonymity: Anonymity
    response_time: float
