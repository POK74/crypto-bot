import json
import os
from datetime import datetime

CACHE_FILE = "price_cache.json"

# Laster eksisterende cache eller lager en ny

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

# Lagre hele cache-strukturen

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

# Oppdater en coin med ny prisverdi og timestamp

def update_price_cache(coin: str, price: float):
    cache = load_cache()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    if coin not in cache:
        cache[coin] = []

    # Unngå å legge inn identisk pris/tid rett etter hverandre
    if cache[coin] and cache[coin][-1]["price"] == price:
        return

    cache[coin].append({"price": price, "timestamp": timestamp})

    # Begrens til de siste 500 datapunktene for hver coin
    cache[coin] = cache[coin][-500:]
    
    save_cache(cache)

# Hent historikk for en coin

def get_price_history(coin: str):
    cache = load_cache()
    return cache.get(coin, [])
