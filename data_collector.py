import aiohttp
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
load_dotenv()

CMC_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
CMC_API_BASE = "https://pro-api.coinmarketcap.com/v1"

HEADERS = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": CMC_API_KEY
}

COIN_ID_OVERRIDES = {
    "ripple": "XRP",
    "binancecoin": "BNB",
    # legg til flere hvis nødvendig
}

CACHE_PATH = Path("cache")
CACHE_PATH.mkdir(exist_ok=True)

async def fetch_top_coins(limit: int = None) -> list:
    try:
        env_limit_raw = os.getenv("COIN_LIMIT", "20")
        logger.info(f"Leser COIN_LIMIT fra .env: {env_limit_raw} (type: {type(env_limit_raw)})")

        if limit is None:
            try:
                limit = int(env_limit_raw)
            except ValueError:
                logger.warning(f"Ugyldig COIN_LIMIT-verdi i .env: '{env_limit_raw}', bruker 20 i stedet.")
                limit = 20

        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Limit må være et positivt heltall, men fikk: {limit} (type: {type(limit)})")

        url = f"{CMC_API_BASE}/cryptocurrency/listings/latest"
        params = {
            "start": "1",
            "limit": str(limit),
            "convert": "USD"
        }

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Feil ved henting av topp coins: HTTP {resp.status}")
                    return []
                data = await resp.json()
                return [coin["symbol"].lower() for coin in data["data"]]

    except Exception as e:
        logger.warning(f"Feil i fetch_top_coins(): {e}")
        return []

async def fetch_historical_data_for_training(coin_symbol: str, days: int = 2) -> list:
    # CoinMarketCap tilbyr ikke historiske data på gratisnivå, så vi cacher tomme data
    logger.warning(f"fetch_historical_data_for_training ikke støttet for symbol '{coin_symbol}' med gratis CoinMarketCap API.")

    cache_file = CACHE_PATH / f"{coin_symbol}_historical.json"
    if cache_file.exists():
        try:
            with cache_file.open("r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Kunne ikke lese fra cache for {coin_symbol}: {e}")

    dummy_data = [(datetime.utcnow().isoformat(), 0.0)]
    try:
        with cache_file.open("w") as f:
            json.dump(dummy_data, f)
    except Exception as e:
        logger.warning(f"Kunne ikke skrive til cache for {coin_symbol}: {e}")

    return dummy_data
