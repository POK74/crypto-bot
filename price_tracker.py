import aiohttp
import logging
import os
from dotenv import load_dotenv

from cache_utils import update_price_in_cache, get_recent_prices

load_dotenv()
logger = logging.getLogger(__name__)

CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

async def fetch_realtime_price(symbol: str):
    params = {"symbol": symbol.upper()}

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(CMC_API_URL, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"⚠️ Klarte ikke hente pris for {symbol}: HTTP {resp.status}")
                    return None

                data = await resp.json()
                quote = data["data"][symbol.upper()]["quote"]["USD"]
                price = quote["price"]

                update_price_in_cache(symbol, price)
                cached = get_recent_prices(symbol, minutes=5)

                return {"price": price, "cached": cached}

    except Exception as e:
        logger.error(f"❌ Feil ved henting av pris for {symbol}: {e}")
        return None
