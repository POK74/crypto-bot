import asyncio
import logging
import sys
from datetime import datetime
from analyse_motor import analyze_signals
from data_collector import fetch_top_coins, fetch_historical_data_for_training

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test(selected_coins=None):
    logger.info("🔍 Kjører test av signalmotoren...")
    start = datetime.utcnow()

    coins = selected_coins or await fetch_top_coins(limit=5)
    logger.info(f"Tester følgende coins: {coins}")

    results = []

    for coin in coins:
        prices = await fetch_historical_data_for_training(coin)
        score, details = analyze_signals(prices, coin)

        result = f"\n🧪 {coin.upper()}\n✅ Score: {score}/100\n{details}"
        print(result)
        results.append(result)

    end = datetime.utcnow()
    total_time = (end - start).total_seconds()
    print(f"\n🕒 Ferdig. Kjoringstid: {total_time:.2f} sekunder.")

    with open("test_run_output.log", "w", encoding="utf-8") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    coins = sys.argv[1:] if len(sys.argv) > 1 else None
    asyncio.run(run_test(coins))
