import aiohttp
import os
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CMC_API_KEY = os.getenv("COINMARKETCAL_API_KEY")
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY,
}

async def fetch_realtime_price(symbol: str) -> float:
    url = f"{CMC_BASE_URL}/cryptocurrency/quotes/latest"
    params = {"symbol": symbol.upper()}

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"🚫 Klarte ikke hente sanntidspris for {symbol}: HTTP {response.status}")
                    return 0.0
                data = await response.json()
                return data["data"][symbol.upper()]["quote"]["USD"]["price"]
    except Exception as e:
        logger.error(f"❌ Feil i fetch_realtime_price({symbol}): {e}")
        return 0.0
