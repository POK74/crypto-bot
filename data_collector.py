import aiohttp
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# Midlertidig cache for top coins
_top_coins_cache = None

# Henter topp coins etter market cap med cache
async def fetch_top_coins(limit: int = 20) -> list:
    global _top_coins_cache
    if _top_coins_cache:
        return _top_coins_cache

    url = f"{COINGECKO_API_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch top coins: {resp.status}")
                    return []
                data = await resp.json()
                _top_coins_cache = [coin["id"] for coin in data]
                return _top_coins_cache
    except Exception as e:
        logger.error(f"Exception in fetch_top_coins: {e}")
        return []

# Henter historiske priser, med fallback og strukturert format
async def fetch_historical_data_for_training(coin_id: str, hours: int = 48, days: int = 2, interval: str = "hourly") -> list:
    url = f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": interval
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch data for {coin_id}: {resp.status}. Using fallback.")
                    try:
                        with open("mock_prices.json") as f:
                            return json.load(f)
                    except Exception as fallback_error:
                        logger.error(f"Fallback failed for {coin_id}: {fallback_error}")
                        return []

                data = await resp.json()
                prices = data.get("prices", [])
                formatted_prices = [
                    {"timestamp": datetime.utcfromtimestamp(p[0] / 1000).isoformat(), "price": p[1]}
                    for p in prices
                ]

                if len(formatted_prices) < hours:
                    logger.warning(f"Insufficient data points for {coin_id}. Got {len(formatted_prices)}, expected {hours}.")
                    return []

                logger.info(f"{coin_id} – siste datapunkt: {formatted_prices[-1]['timestamp']}")
                return formatted_prices[-hours:]

    except Exception as e:
        logger.error(f"API error fetching prices for {coin_id}: {e}")
        return []
