import aiohttp
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("Missing Telegram credentials.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    logger.info("Telegram message sent successfully")
                else:
                    logger.warning(f"Failed to send message: {response.status} - {await response.text()}")
    except Exception as e:
        logger.exception(f"Exception during Telegram send: {e}")
