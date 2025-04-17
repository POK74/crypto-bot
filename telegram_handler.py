import os
import logging
import aiohttp

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_telegram_message(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("Telegram BOT_TOKEN or CHAT_ID not set.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to send Telegram message: {resp.status} - {await resp.text()}")
                else:
                    logger.info("Telegram message sent successfully.")
    except Exception as e:
        logger.exception(f"Error sending Telegram message: {e}")

async def notify_signal(signal_summary: str):
    if signal_summary and "KJØPSSIGNAL" in signal_summary:
        await send_telegram_message(signal_summary)
    else:
        logger.info("Ingen kjøpssignal å sende til Telegram.")
