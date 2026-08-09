import asyncio
import logging
import traceback
from telethon import TelegramClient
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from database import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = TelegramClient("session_periodic", config.API_ID, config.API_HASH)
scheduler = AsyncIOScheduler()

async def main():
    print("⚡ Menginisialisasi Database...")
    init_db()

    print("📦 Dynamic Loading Plugins...")
    import plugins

    print("🚀 Menghubungkan Bot Telethon...")
    await bot.start(bot_token=config.BOT_TOKEN)
    
    me = await bot.get_me()
    print(f"\n==========================================")
    print(f"✅ BOT AKTIF! Logged in as: @{me.username} (ID: {me.id})")
    print(f"==========================================\n")

    scheduler.start()
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("\n❌ TERJADI ERROR PADA BOT:")
        traceback.print_exc()
