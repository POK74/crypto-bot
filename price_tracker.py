import aiohttp
import os
import logging
from dotenv import load_dotenv
from price_cache import load_price_cache, save_price_cache, update_price_in_cache

load_dotenv()
logger = logging.getLogger(__name__)

COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CMC_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

HEADERS = {
    "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
    "Accept": "application/json"
}

async def fetch_realtime_price(symbol: str) -> dict:
    try:
        params = {"symbol": symbol.upper(), "convert": "USD"}
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(CMC_API_URL, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"❌ API-feil for {symbol}: HTTP {resp.status}")
                    return None
                data = await resp.json()
                price = data["data"][symbol.upper()]["quote"]["USD"]["price"]

                cache = load_price_cache()
                updated = update_price_in_cache(cache, symbol, price)
                save_price_cache(updated)

                return {
                    "symbol": symbol,
                    "price": price,
                    "cached": updated.get(symbol, [])
                }

    except Exception as e:
        logger.error(f"❌ Exception i fetch_realtime_price({symbol}): {e}")
        return None
