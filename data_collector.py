import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# 🔹 1. Hent topp coins etter market cap
async def fetch_top_coins(limit: int = 20) -> list:
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
                return [coin["id"] for coin in data]
    except Exception as e:
        logger.error(f"Exception in fetch_top_coins: {e}")
        return []

# 🔹 2. Hent historiske prisdata for analyse (f.eks. 30 dager – brukes i main.py)
async def fetch_historical_data_for_training(coin_id: str, days: int = 30) -> list:
    url = f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": "hourly"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch historical data for {coin_id}: {resp.status}")
                    return []
                data = await resp.json()
                prices = data.get("prices", [])
                return [(datetime.utcfromtimestamp(p[0] / 1000), p[1]) for p in prices]
    except Exception as e:
        logger.error(f"Error fetching historical data for {coin_id}: {e}")
        return []

# 🔹 3. Enkel pris-henting for analyse_motor (siste 48 timer)
async def fetch_prices(coin, hours=48):
    url = f"{COINGECKO_API_BASE}/coins/{coin}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': '2',
        'interval': 'hourly'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch data for {coin}: HTTP {resp.status}")
                    return []

                data = await resp.json()
                prices = data.get('prices', [])
                formatted_prices = [(datetime.utcfromtimestamp(p[0] / 1000), p[1]) for p in prices]

                if len(formatted_prices) < hours:
                    logger.warning(f"Insufficient data points received for {coin}. Got {len(formatted_prices)}, expected {hours}.")
                    return []

                return formatted_prices[-hours:]

    except Exception as e:
        logger.error(f"API error fetching prices for {coin}: {e}")
        return []
