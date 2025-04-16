import aiohttp
import logging
import math
import json
import pathlib
from datetime import datetime

logger = logging.getLogger(__name__)
LEARN_CACHE_PATH = pathlib.Path("logs/volume_cache.json")
LEARN_CACHE_PATH.parent.mkdir(exist_ok=True)

# 🌊 Versjon 2.2 – med læringslogg og trendcache
async def get_volume_boost(coin_id: str) -> float:
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Volume data fetch failed for {coin_id}: {resp.status}")
                    return 0.0

                data = await resp.json()
                market_data = data.get("market_data", {})
                volume = market_data.get("total_volume", {}).get("usd", 0)
                market_cap = market_data.get("market_cap", {}).get("usd", 1)

                if volume == 0 or market_cap == 0:
                    return 0.0

                ratio = volume / market_cap
                boost = 0.0

                if ratio > 0.8:
                    boost = 6.0
                elif ratio > 0.4:
                    boost = 4.0
                elif ratio > 0.2:
                    boost = 2.0
                elif ratio > 0.1:
                    boost = 1.0

                # Meme coins awareness
                meme_coins = ["dogecoin", "shiba", "pepe"]
                if coin_id in meme_coins and ratio > 0.3:
                    boost *= 1.2

                # Læringsbasert boostforsterker (cache og logg)
                historical_boost = 0
                cache_data = {}
                if LEARN_CACHE_PATH.exists():
                    with open(LEARN_CACHE_PATH, "r") as f:
                        try:
                            cache_data = json.load(f)
                            if coin_id in cache_data:
                                history = cache_data[coin_id][-3:]
                                changes = [entry["volume"] for entry in history]
                                if len(changes) >= 2 and changes[-1] > changes[0] * 1.5:
                                    historical_boost += 2.0
                        except json.JSONDecodeError:
                            cache_data = {}

                # Lagre nåværende volum for fremtidig læring
                timestamp = datetime.utcnow().isoformat()
                entry = {"timestamp": timestamp, "volume": volume}
                if coin_id not in cache_data:
                    cache_data[coin_id] = []
                cache_data[coin_id].append(entry)
                cache_data[coin_id] = cache_data[coin_id][-10:]

                with open(LEARN_CACHE_PATH, "w") as f:
                    json.dump(cache_data, f, indent=2)

                final_boost = round(min(boost + math.log(boost + 1) + historical_boost, 10.0), 2)
                logger.info(f"Volume boost for {coin_id}: {final_boost} (ratio {ratio:.2f})")
                return final_boost

    except Exception as e:
        logger.warning(f"Volume analysis error for {coin_id}: {e}")
        return 0.0
