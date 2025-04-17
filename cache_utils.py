import json
import os
from datetime import datetime, timedelta

CACHE_FILE = "price_cache.json"

def load_price_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_price_cache(data: dict):
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Feil ved lagring av cache: {e}")

def update_price_in_cache(symbol: str, price: float):
    data = load_price_cache()
    timestamp = datetime.utcnow().isoformat()
    history = data.get(symbol, [])

    # Fjern gamle data eldre enn 2 timer
    cutoff = datetime.utcnow() - timedelta(hours=2)
    history = [
        entry for entry in history
        if datetime.fromisoformat(entry["timestamp"]) > cutoff
    ]

    # Legg til ny pris
    history.append({"timestamp": timestamp, "price": price})
    data[symbol] = history

    save_price_cache(data)

def get_recent_prices(symbol: str, minutes: int = 5):
    data = load_price_cache()
    history = data.get(symbol, [])

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return [
        entry for entry in history
        if datetime.fromisoformat(entry["timestamp"]) > cutoff
    ]
