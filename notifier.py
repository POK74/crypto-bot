import aiohttp
import os
import logging

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.warning("Telegram-varsling er ikke konfigurert riktig.")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

async def send_telegram_alert(signal: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    message = (
        f"🚀 *SIGNAL DETEKTERT!*\n\n"
        f"*Symbol:* `{signal['symbol'].upper()}`\n"
        f"*Score:* {signal['score']}/100\n"
        f"*Pris:* ${round(signal['price'], 4)}\n"
        f"*Endring:* {signal['change']}%\n"
        f"_Type:_ `{signal['note']}`"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BASE_URL, data=payload) as response:
                if response.status != 200:
                    logger.warning(f"❌ Feil ved sending av Telegram-varsel: {response.status}")
    except Exception as e:
        logger.error(f"❌ send_telegram_alert-feil: {e}")
