# data_collector.py

import aiohttp
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

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

async def fetch_historical_data_for_training(coin_id: str, days: int = 30) -> list:
    url = f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart"
    params = {

