import json
import os
from datetime import datetime
from pathlib import Path

PRICE_CACHE_FILE = Path("cache/price_cache.json")
PRICE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_price_cache() -> dict:
    if not PRICE_CACHE_FILE.exists():
        return {}
    try:
        with open(PRICE_CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_price_cache(cache: dict) -> None:
    try:
        with open(PRICE_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Feil ved lagring av pris-cache: {e}")

def update_price_in_cache(cache: dict, symbol: str, price: float) -> dict:
    timestamp = datetime.utcnow().isoformat()
    if symbol not in cache:
        cache[symbol] = []
    cache[symbol].append({"timestamp": timestamp, "price": price})

    # Behold bare de siste 100 datapunktene per coin
    if len(cache[symbol]) > 100:
        cache[symbol] = cache[symbol][-100:]

    return cache
