import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup
from typing import List, Set
from models import Protocol

# Danh sách nguồn proxy (có thể mở rộng)
SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    # Có thể thêm nguồn scrape HTML ở dưới
]

# Pattern regex cho IP:PORT
IP_PORT_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}\b')

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            return await resp.text()
    except:
        return ""

def extract_proxies_from_text(text: str, protocol: Protocol) -> Set[str]:
    proxies = set()
    for match in IP_PORT_REGEX.findall(text):
        proxies.add(f"{protocol.value}://{match}")
    return proxies

async def scrape_source(session: aiohttp.ClientSession, url: str) -> Set[str]:
    content = await fetch(session, url)
    if not content:
        return set()
    
    # Xác định loại protocol dựa vào url hoặc nội dung
    # Mặc định quy ước: nếu url chứa socks4 -> socks4, socks5 -> socks5, còn lại http
    if "socks4" in url.lower():
        proto = Protocol.SOCKS4
    elif "socks5" in url.lower():
        proto = Protocol.SOCKS5
    else:
        proto = Protocol.HTTP  # có thể là https nhưng ta kiểm tra sau

    proxies = extract_proxies_from_text(content, proto)
    
    # Nếu là HTML, thử parse thêm bằng BeautifulSoup (nếu cần)
    if "html" in content[:200].lower() or url.endswith((".html", ".php")):
        soup = BeautifulSoup(content, 'lxml')
        for pre in soup.find_all('pre'):
            proxies.update(extract_proxies_from_text(pre.get_text(), proto))
    
    return proxies

async def scrape_all_sources() -> Set[str]:
    all_proxies = set()
    async with aiohttp.ClientSession() as session:
        tasks = [scrape_source(session, url) for url in SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, set):
                all_proxies.update(res)
    return all_proxies
