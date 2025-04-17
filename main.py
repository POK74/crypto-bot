import asyncio
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

from telegram_handler import send_telegram_message
from data_collector import fetch_top_coins
from price_tracker import fetch_realtime_price
from analyse_motor import analyze_signals_realtime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Asynkron hovedmotor for sanntidssignaler
async def run_realtime_scan():
    logger.info("🚀 Starter sanntidsscan (kun prisbasert)")

    await send_telegram_message(
        f"⚡ *Sanntidsscan startet!*
🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n🤖 MenBreakthrough AI-Bot overvåker markedet live!"
    )

    coin_limit = int(os.getenv("COIN_LIMIT", 20))
    coins = await fetch_top_coins(limit=coin_limit)
    logger.info(f"Hentet topp {len(coins)} coins: {coins}")

    valid_signals = []

    for coin in coins:
        price_info = await fetch_realtime_price(coin)
        if not price_info:
            logger.warning(f"Mangler sanntidsdata for {coin}, hopper over.")
            continue

        score, details = analyze_signals_realtime(price_info, coin)

        if score >= 70:
            valid_signals.append((coin, score, details))

    if not valid_signals:
        logger.info("Ingen sterke bevegelser funnet.")
        await send_telegram_message("📭 *Ingen prisbaserte signaler funnet akkurat nå.*")
        return

    valid_signals.sort(key=lambda x: x[1], reverse=True)

    for coin, score, details in valid_signals[:10]:
        message = f"📈 *PRISVARSEL* - {coin.upper()}/USDT\n"
        message += f"🔥 Endring-score: *{score}*\n"
        message += details
        await send_telegram_message(message)

# Start kun sanntids-scan
async def main():
    await run_realtime_scan()

if __name__ == "__main__":
    asyncio.run(main())
