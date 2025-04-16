import asyncio
from dotenv import load_dotenv
load_dotenv()
import logging
from datetime import datetime

from telegram_handler import send_telegram_message
from data_collector import fetch_top_coins, fetch_historical_data_for_training
from analyse_motor import analyze_signals
from whale_tracker import run_whale_tracker  # 🐋 Ny linje

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Asynkron hovedmotor for signalanalyse
async def run_signal_scan():
    logger.info("🚀 Starter signal-scan")

    await send_telegram_message(
        f"🚀 *Ny signal-scan aktivert!*\n🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n🤖 MenBreakthrough AI-Bot er i gang!"
    )

    coins = await fetch_top_coins(limit=20)
    logger.info(f"Hentet topp {len(coins)} coins: {coins}")

    valid_signals = []

    for coin in coins:
        data = await fetch_historical_data_for_training(coin)
        if not data:
            logger.warning(f"Mangler historiske data for {coin}, hopper over.")
            continue

        score, details = analyze_signals(data, coin)

        if score >= 70:
            valid_signals.append((coin, score, details))

    if not valid_signals:
        logger.info("Ingen signaler over terskelen ble funnet.")
        await send_telegram_message("📭 *Ingen kjøpssignaler funnet i denne scanningen.*")
        return

    valid_signals.sort(key=lambda x: x[1], reverse=True)

    for coin, score, details in valid_signals[:10]:  # maks 10 meldinger
        message = f"📈 *KJØPSSIGNAL* - {coin.upper()}/USDT\n"
        message += f"⭐ Score: *{score}*\n"
        message += details
        await send_telegram_message(message)

# Kjør både signal-scan og whale-tracking samtidig
async def main():
    await asyncio.gather(
        run_signal_scan(),
        run_whale_tracker()
    )

if __name__ == "__main__":
    asyncio.run(main())

