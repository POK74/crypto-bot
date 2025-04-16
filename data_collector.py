import aiohttp
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

async def fetch_top_coins(limit: int = None) -> list:
    try:
        env_limit = os.getenv("COIN_LIMIT", "20")
        limit = limit or int(env_limit)
        url = f"{COINGECKO_API_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch top coins: {resp.status}")
                    return []
                data = await resp.json()
                return [coin["id"] for coin in data]

    except Exception as e:
        logger.warning(f"COIN_LIMIT-feil: {e}")
        return []

async def fetch_historical_data_for_training(coin_id: str, days: int = 2) -> list:
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
                    logger.error(f"Failed to fetch historical data for {coin_id}: HTTP {resp.status}")
                    return []
                data = await resp.json()
                prices = data.get("prices", [])
                return [(datetime.utcfromtimestamp(p[0] / 1000), p[1]) for p in prices]
    except Exception as e:
        logger.error(f"Error in fetch_historical_data_for_training({coin_id}): {e}")
        return []
