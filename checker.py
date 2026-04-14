import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from typing import Tuple, Optional, List
from models import ProxyEntry, Protocol, Anonymity
import time
from datetime import datetime

TEST_URL = "http://httpbin.org/get"
TIMEOUT_SEC = 3

async def check_proxy(proxy_str: str) -> Optional[ProxyEntry]:
    """
    proxy_str format: protocol://ip:port
    """
    try:
        parts = proxy_str.split("://")
        if len(parts) != 2:
            return None
        proto_str, addr = parts
        ip, port_str = addr.split(":")
        port = int(port_str)
        
        # Map protocol string to ProxyType
        proto_map = {
            "http": ProxyType.HTTP,
            "https": ProxyType.HTTP,  # aiohttp_socks dùng HTTP cho cả http/https proxy
            "socks4": ProxyType.SOCKS4,
            "socks5": ProxyType.SOCKS5
        }
        if proto_str not in proto_map:
            return None
        
        connector = ProxyConnector(
            proxy_type=proto_map[proto_str],
            host=ip,
            port=port,
            rdns=True  # resolve DNS qua proxy để kiểm tra anonymity đúng hơn
        )
        
        start = time.time()
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(TEST_URL, timeout=aiohttp.ClientTimeout(total=TIMEOUT_SEC)) as resp:
                data = await resp.json()
                response_time = (time.time() - start) * 1000  # ms
                
                # Lấy IP mà httpbin nhận được
                origin = data.get("origin", "")
                # Xác định anonymity
                anonymity = classify_anonymity(data.get("headers", {}), origin)
                
                # Chỉ giữ elite và anonymous
                if anonymity in (Anonymity.ELITE, Anonymity.ANONYMOUS):
                    protocol_enum = Protocol(proto_str)
                    return ProxyEntry(
                        ip=ip,
                        port=port,
                        protocol=protocol_enum,
                        anonymity=anonymity,
                        response_time=response_time,
                        last_checked=datetime.utcnow().isoformat()
                    )
    except Exception as e:
        # print(f"Check failed {proxy_str}: {e}")
        pass
    return None

def classify_anonymity(headers: dict, origin_ip: str) -> Anonymity:
    """
    Phân loại dựa trên headers và IP nhận được.
    Elite: Không có header proxy-related, IP != thật (nhưng ở đây ta chỉ có IP proxy, ko có IP thật client)
    Ta kiểm tra các header phổ biến: X-Forwarded-For, Via, Proxy-Connection, X-Real-IP
    """
    proxy_headers = ["X-Forwarded-For", "Via", "Proxy-Connection", "X-Real-IP", "Forwarded"]
    has_proxy_header = any(h in headers for h in proxy_headers)
    
    if not has_proxy_header:
        return Anonymity.ELITE
    else:
        return Anonymity.ANONYMOUS
    # Không có trường hợp transparent ở đây vì ta không có IP thật để so sánh
    # Transparent sẽ bị loại

async def check_batch(proxy_list: List[str], concurrency: int = 200) -> List[ProxyEntry]:
    semaphore = asyncio.Semaphore(concurrency)
    
    async def bounded_check(p):
        async with semaphore:
            return await check_proxy(p)
    
    tasks = [bounded_check(p) for p in proxy_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    valid = [r for r in results if isinstance(r, ProxyEntry)]
    return valid
