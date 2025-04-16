import numpy as np
import logging

logger = logging.getLogger(__name__)

def analyze_signals(prices: list, coin: str):
    if not prices or len(prices) < 48:
        logger.warning(f"Not enough data to analyze {coin}")
        return 0, "❌ Not enough data"

    if not all(isinstance(p, dict) and "price" in p for p in prices):
        logger.error(f"Malformed price data for {coin}!")
        return 0, "❌ Invalid price format"

    try:
        prices_array = np.array([p["price"] for p in prices[-48:]])

        # Prisendringer
        change_24h = (prices_array[-1] - prices_array[0]) / prices_array[0] * 100
        change_6h = (prices_array[-1] - prices_array[-7]) / prices_array[-7] * 100
        change_1h = (prices_array[-1] - prices_array[-2]) / prices_array[-2] * 100

        # Score-beregning
        score = 0
        if change_24h > 3:
            score += 30
        if change_6h > 1:
            score += 25
        if change_1h > 0.5:
            score += 25

        # Volatilitet
        volatility = np.std(prices_array[-12:])
        if volatility < 0.01:
            score -= 20
            vol_text = "🔸 Low volatility"
        else:
            score += 10
            vol_text = "📈 Normal volatility"

        # Trendmomentum
        momentum = prices_array[-1] - np.mean(prices_array[-12:])
        if momentum > 0:
            score += 5
            trend_text = "📈 Oppadgående momentum"
        else:
            trend_text = "➖ Ingen momentumbonus"

        # Glidende snitt trend
        ma_24 = np.mean(prices_array[-24:])
        ma_48 = np.mean(prices_array)
        if ma_24 > ma_48:
            score += 5
            sma_text = "🟢 Kort trend over lang trend"
        else:
            sma_text = "🔸 Kort trend under lang trend"

        # Sammensatt Telegram-detaljtekst
        details = (
            f"24h: {change_24h:.2f}%, 6h: {change_6h:.2f}%, 1h: {change_1h:.2f}%\n"
            f"{vol_text} | {trend_text} | {sma_text}\n"
            f"📊 Basisscore: {score}/100 (uten boosters)"
        )

        logger.info(f"{coin.upper()} → Score: {score}, Volatility: {volatility:.5f}, Momentum: {momentum:.4f}")
        return score, details

    except Exception as e:
        logger.exception(f"Error analyzing {coin}: {e}")
        return 0, "❌ Error in analysis"
