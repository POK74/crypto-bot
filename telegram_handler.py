import os
from telegram import Bot

async def send_telegram_message(message):
    try:
        bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"Message sent to Telegram: {message}")
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
