import aiosqlite
import asyncio
from typing import List, Optional
from models import ProxyEntry, Protocol, Anonymity
from datetime import datetime

DB_PATH = "proxies.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS proxies (
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                protocol TEXT NOT NULL,
                anonymity TEXT,
                response_time REAL,
                last_checked TEXT,
                PRIMARY KEY (ip, port, protocol)
            )
        ''')
        await db.commit()

async def insert_proxy(entry: ProxyEntry):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO proxies 
                (ip, port, protocol, anonymity, response_time, last_checked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (entry.ip, entry.port, entry.protocol.value,
                  entry.anonymity.value if entry.anonymity else None,
                  entry.response_time, entry.last_checked))
            await db.commit()
    except Exception as e:
        print(f"DB insert error: {e}")

async def get_proxies(
    protocol: Optional[Protocol] = None,
    anonymity: Optional[Anonymity] = None,
    limit: int = 100
) -> List[ProxyEntry]:
    query = "SELECT ip, port, protocol, anonymity, response_time, last_checked FROM proxies WHERE 1=1"
    params = []
    if protocol:
        query += " AND protocol = ?"
        params.append(protocol.value)
    if anonymity:
        query += " AND anonymity = ?"
        params.append(anonymity.value)
    query += " ORDER BY response_time ASC LIMIT ?"
    params.append(limit)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [
                ProxyEntry(
                    ip=row['ip'],
                    port=row['port'],
                    protocol=Protocol(row['protocol']),
                    anonymity=Anonymity(row['anonymity']) if row['anonymity'] else None,
                    response_time=row['response_time'],
                    last_checked=row['last_checked']
                ) for row in rows
            ]

async def count_proxies() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM proxies")
        total = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE anonymity = 'elite'")
        elite = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM proxies WHERE anonymity = 'anonymous'")
        anon = (await cursor.fetchone())[0]
        return {"total": total, "elite": elite, "anonymous": anon}
