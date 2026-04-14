import asyncio
import schedule
import time
from scraper import scrape_all_sources
from checker import check_batch
from database import init_db, insert_proxy
from models import ProxyEntry

async def job():
    print("Starting proxy refresh...")
    await init_db()
    
    # 1. Scrape
    print("Scraping proxies...")
    raw_proxies = await scrape_all_sources()
    print(f"Scraped {len(raw_proxies)} raw proxies.")
    
    # 2. Check
    print("Checking proxies (timeout 3s)...")
    valid = await check_batch(list(raw_proxies), concurrency=200)
    print(f"Valid proxies: {len(valid)}")
    
    # 3. Save to DB
    for entry in valid:
        await insert_proxy(entry)
    print("Database updated.")

def run_async_job():
    asyncio.run(job())

def start_scheduler():
    # Chạy ngay lần đầu
    run_async_job()
    # Lên lịch mỗi giờ
    schedule.every(1).hours.do(run_async_job)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    start_scheduler()
