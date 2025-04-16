# analyse_motor.py

import numpy as np
import logging
from datetime import datetime, timedelta

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

