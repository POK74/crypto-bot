import asyncio
from data_collector import fetch_historical_data_for_training
from analysemotor import analyze_market_conditions
from telegram_handler import send_telegram_message
import logging

logging.basicConfig(level=logging.INFO)

async def run_signal_scan():
    coins = ["BTC", "ETH"]
    tasks = []

    for coin in coins:
        tasks.append(analyze_and_send_signal(coin))

    await asyncio.gather(*tasks)

async def analyze_and_send_signal(coin):
    df = await fetch_historical_data_for_training(coin)
    if df is None or df.empty:
        return

    result = analyze_market_conditions(df)
    entry_price = df["close"].iloc[-1]

    message = (
        f"🔥 BUY SIGNAL - {coin}/USDT\n"
        f"Entry: ${entry_price:,.2f}\n"
        f"Confidence: {'🔵' * result['confidence'] + '⚪' * (5 - result['confidence'])}\n"
        f"Trend: {result['bias']}\n"
        f"Volume: {result['volume']:,.0f}\n"
    )
    await send_telegram_message(message)

if __name__ == "__main__":
    asyncio.run(run_signal_scan())
