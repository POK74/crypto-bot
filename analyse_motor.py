import logging
import numpy as np

logger = logging.getLogger(__name__)

# Enkel sanntids scoringsmodell basert på prisdynamikk (placeholder)
def analyze_signals(data: list, coin_name: str):
    try:
        if not data or len(data) < 3:
            logger.warning(f"Not enough data to analyze {coin_name}")
            return 0, "❌ Not enough data"

        prices = np.array([price for _, price in data])
        momentum = (prices[-1] - prices[0]) / prices[0]
        score = min(max(int(momentum * 100), 0), 100)

        summary = f"📊 Prisendring: {momentum:.2%}\n"
        summary += f"📍 Pris start: {prices[0]:.2f} → Slutt: {prices[-1]:.2f}\n"

        if score >= 70:
            summary += "🚀 Momentum ser sterkt ut!"
        elif score >= 50:
            summary += "📈 Positiv trend observert."
        else:
            summary += "🔍 Svak eller ingen tydelig oppgang."

        return score, summary

    except Exception as e:
        logger.error(f"analyse_signals-feil for {coin_name}: {e}")
        return 0, "❌ Analysefeil"
