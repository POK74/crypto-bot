import aiohttp
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
load_dotenv()

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
API_KEY = os.getenv("COINGECKO_API_KEY")

HEADERS = {
    "accept": "application/json"
}
if API_KEY:
    HEADERS["x-cg-pro-api-key"] = API_KEY

COIN_ID_OVERRIDES = {
    "ripple": "xrp",
    "binancecoin": "bnb",
    # legg til flere hvis nødvendig
}

async def fetch_top_coins(limit: int = None) -> list:
    try:
        env_limit_raw = os.getenv("COIN_LIMIT", "20")
        logger.info(f"Leser COIN_LIMIT fra .env: {env_limit_raw} (type: {type(env_limit_raw)})")

        # Håndter konvertering og fallback
        if limit is None:
            try:
                limit = int(env_limit_raw)
            except ValueError:
                logger.warning(f"Ugyldig COIN_LIMIT-verdi i .env: '{env_limit_raw}', bruker 20 i stedet.")
                limit = 20

        # Sjekk at limit er gyldig type
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Limit må være et positivt heltall, men fikk: {limit} (type: {type(limit)})")

        url = f"{COINGECKO_API_BASE}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false"
        }

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"Feil ved henting av topp coins: HTTP {resp.status}")
                    return []
                data = await resp.json()
                return [coin["id"] for coin in data]

    except Exception as e:
        logger.warning(f"Feil i fetch_top_coins(): {e}")
        return []

async def fetch_historical_data_for_training(coin_id: str, days: int = 2) -> list:
    # Override kjent navn hvis nødvendig
    original_id = coin_id
    coin_id = COIN_ID_OVERRIDES.get(coin_id, coin_id)

    url = f"{COINGECKO_API_BASE}/coins/{coin_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": str(days),
        "interval": "hourly"
    }

    try:
        logger.debug(f"Henter historiske data for {original_id} → {coin_id}: {url} med params {params}")
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    logger.error(f"Feil ved henting av historiske data for {original_id} (som {coin_id}): HTTP {resp.status} - {err_text}")
                    return []
                data = await resp.json()
                prices = data.get("prices", [])
                return [(datetime.utcfromtimestamp(p[0] / 1000), p[1]) for p in prices]
    except Exception as e:
        logger.error(f"Feil i fetch_historical_data_for_training({coin_id}): {e}")
        return []
