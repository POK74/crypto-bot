import os
import logging
import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

async def send_telegram_alert(signal: dict):
    try:
        symbol = signal.get("symbol", "?").upper()
        score = signal.get("score", 0)
        note = signal.get("note", "")
        price = signal.get("price", 0)
        change = signal.get("change", 0)

        message = (
            f"\u26a1 Signal Alert: *{symbol}*\n"
            f"Score: *{score}/100* ({note})\n"
            f"Price: ${price:.4f}\n"
            f"24h Change: {change:.2f}%"
        )

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload) as resp:
                if resp.status != 200:
                    logger.warning(f"Telegram-feil ({resp.status}): {await resp.text()}")
                else:
                    logger.info(f"Telegram-varsling sendt for {symbol}")
    except Exception as e:
        logger.error(f"Feil i send_telegram_alert: {e}")
