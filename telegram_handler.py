import os
import aiohttp
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_message(message: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.warning("Mangler TELEGRAM_BOT_TOKEN eller TELEGRAM_CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status != 200:
                    logger.error(f"Telegram-feil: HTTP {response.status}")
    except Exception as e:
        logger.error(f"Feil ved sending til Telegram: {e}")
