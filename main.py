# main.py - FULLVERSJON 100% KOMPLETT

import asyncio
import logging
from telegram_handler import send_telegram_message
from data_collector import fetch_top_coins, fetch_historical_data_for_training
from analyse_motor import analyze_signals
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hovedfunksjon som analyserer og sender kjøpssignaler
async def run_signal_scan():
    logger.info("🚀 Starter signal scan")
    await send_telegram_message(
        f"🚀 *Starter ny signal-scan...*\n🕒 Tid: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n🤖 Kilde: MenBreakthrough AI-Bot"
    )

    coins = await fetch_top_coins(limit=20)
    logger.info(f"Topp coins hentet: {coins[:10]}...")

    valid_signals = []
    for coin in coins:
        data = await fetch_historical_data_for_training(coin)
        if data is None:
            continue

        score, details = analyze_signals(data, coin)
        if score >= 70:
            valid_signals.append((coin, score, details))

    if not valid_signals:
        logger.info("Fant ingen gode signaler.")
        await send_telegram_message("📭 *Ingen kjøpssignaler funnet i denne runden.*")
        return

    valid_signals.sort(key=lambda x: x[1], reverse=True)

    for coin, score, details in valid_signals[:10]:
        message = f"🔥 *KJØPSSIGNAL* - {coin.upper()}/USDT\n"
        message += f"📊 Score: *{score}*\n{details}"
        await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(run_signal_scan())
