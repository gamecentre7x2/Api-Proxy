from fastapi import FastAPI, Query, HTTPException
from typing import Optional
from database import init_db, count_proxies, get_proxies
from models import Protocol, Anonymity, ProxyResponse
import uvicorn

app = FastAPI(title="Advanced Proxy API", version="1.0.0")

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    counts = await count_proxies()
    return {
        "message": "Proxy Service is running",
        "proxies_count": counts
    }

@app.get("/get")
async def get_proxy(
    protocol: Optional[Protocol] = Query(None),
    anonymity: Optional[Anonymity] = Query(None),
    limit: int = Query(1, ge=1, le=100)
):
    proxies = await get_proxies(protocol=protocol, anonymity=anonymity, limit=limit)
    if not proxies:
        raise HTTPException(status_code=404, detail="No proxies found matching criteria")
    
    response = []
    for p in proxies:
        response.append(ProxyResponse(
            proxy=f"{p.protocol.value}://{p.ip}:{p.port}",
            protocol=p.protocol,
            anonymity=p.anonymity,
            response_time=p.response_time
        ))
    return {"proxies": response}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
