import asyncio
import logging
from datetime import datetime
import numpy as np

from data_collector import fetch_prices
from telegram_handler import send_telegram_message

logger = logging.getLogger(__name__)

def analyze_signals(prices, coin):
    if not prices or len(prices) < 48:
        logger.warning(f"Not enough data to analyze {coin}")
        return 0, "❌ Not enough data"

    timestamps, values = zip(*prices[-48:])
    prices_array = np.array(values)

    change_24h = (prices_array[-1] - prices_array[0]) / prices_array[0] * 100
    change_6h = (prices_array[-1] - prices_array[-7]) / prices_array[-7] * 100
    change_1h = (prices_array[-1] - prices_array[-2]) / prices_array[-2] * 100

    score = 0
    if change_24h > 3: score += 30
    if change_6h > 1: score += 25
    if change_1h > 0.5: score += 25

    volatility = np.std(prices_array[-12:])
    if volatility < 0.01:
        score -= 20
        vol_text = "🔸 Low volatility"
    else:
        score += 10
        vol_text = "📈 Normal volatility"

    details = f"24h: {change_24h:.2f}%, 6h: {change_6h:.2f}%, 1h: {change_1h:.2f}%\n{vol_text}"

    return score, details

async def run_signal_scan():
    coins = ["bitcoin", "ethereum", "solana", "avalanche-2"]
    signals_found = 0

    for coin in coins:
        try:
            prices = await fetch_prices(coin, hours=48)
            score, details = analyze_signals(prices, coin)

            if score >= 60:
                signals_found += 1
                message = (
                    f"🚀 **Buy Signal!**\n\n"
                    f"📌 **Coin:** {coin.capitalize()}\n"
                    f"📅 **Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
                    f"💯 **Score:** {score}/100\n"
                    f"---\n"
                    f"{details}"
                )
                await send_telegram_message(message)
                logger.info(f"Signal sent for {coin}: Score {score}")
            else:
                logger.info(f"No strong signal for {coin}: Score {score}")

        except Exception as e:
            logger.error(f"Error analyzing {coin}: {e}")

    if signals_found == 0:
        logger.info("No signals found this round.")
    else:
        logger.info(f"Total signals sent: {signals_found}")

if __name__ == "__main__":
    asyncio.run(run_signal_scan())
