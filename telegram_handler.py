import os
import logging
import aiohttp

# Hent Telegram API-data fra miljøvariabler
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sjekk at begge finnes, ellers stopp
if not TOKEN or not CHAT_ID:
    error_msg = "Environment variables TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set"
    logging.error(error_msg)
    raise RuntimeError(error_msg)

# Telegram API URL
API_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Asynkron sendefunksjon
async def send_message(text: str):
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logging.error(f"Failed to send Telegram message. Status code: {resp.status}, response: {error_text}")
                else:
                    logging.info(f"Telegram message sent successfully: {text}")
    except Exception as e:
        logging.error(f"Error sending message to Telegram: {e}")
