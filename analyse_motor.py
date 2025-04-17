import json
import logging
from datetime import datetime
from pathlib import Path
import numpy as np
from data_collector import fetch_historical_data_for_training, fetch_realtime_price
from notifier import send_telegram_alert  # Ny integrasjon

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CACHE_PATH = Path("cache")
CACHE_PATH.mkdir(exist_ok=True)


def calculate_score(data: list) -> int:
    try:
        prices = [price for _, price in data if price > 0]
        if len(prices) < 2:
            return 50

        returns = np.diff(prices) / prices[:-1] * 100
        avg_return = np.mean(returns)

        score = int(min(max(avg_return, -50), 50) + 50)
        return score
    except Exception as e:
        logger.warning(f"Feil i calculate_score: {e}")
        return 50


async def analyze_signals(symbol: str) -> dict:
    data = await fetch_historical_data_for_training(symbol)

    if not data or len(data) < 2:
        price_now = await fetch_realtime_price(symbol)
        cache_file = CACHE_PATH / f"{symbol}_last_price.json"

        last_price = 0.0
        if cache_file.exists():
            try:
                with cache_file.open("r") as f:
                    cached = json.load(f)
                    last_price = cached.get("price", 0.0)
            except Exception as e:
                logger.warning(f"Kunne ikke lese cache for {symbol}: {e}")

        if last_price:
            change_pct = (price_now - last_price) / last_price * 100
            score = int(min(max(change_pct, -50), 50) + 50)
        else:
            score = 50

        try:
            with cache_file.open("w") as f:
                json.dump({"price": price_now, "timestamp": datetime.utcnow().isoformat()}, f)
        except Exception as e:
            logger.warning(f"Kunne ikke skrive cache for {symbol}: {e}")

        logger.info(f"🟡 {symbol.upper()} fallback-score basert på sanntidspris: {score}")
    
        result = {
            "symbol": symbol,
            "score": score,
            "note": "fallback",
            "price": price_now,
            "change": round(change_pct, 2) if last_price else 0
        }
    else:
        score = calculate_score(data)
        logger.info(f"🟢 {symbol.upper()} full analyse-score: {score}")

        result = {
            "symbol": symbol,
            "score": score,
            "note": "historical",
            "price": data[-1][1] if data else 0.0,
            "change": 0.0
        }

    # Send Telegram-varsel hvis score er høy
    if result["score"] >= 75:
        await send_telegram_alert(result)

    return result
