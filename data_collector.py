async def fetch_top_coins(limit: int = None) -> list:
    try:
        raw_limit = os.getenv("COIN_LIMIT")
        limit = limit or int(raw_limit) if raw_limit and raw_limit.isdigit() else 20
    except Exception as e:
        logger.error(f"Feil ved lasting av COIN_LIMIT: {e}")
        limit = 20

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
