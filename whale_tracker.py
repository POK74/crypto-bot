import logging
import aiohttp
from datetime import datetime, timedelta
import os
import math
import json
import pathlib

logger = logging.getLogger(__name__)

BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
BLOCKFROST_API_KEY = os.getenv("BLOCKFROST_API_KEY")

LOG_PATH = pathlib.Path("logs/whale_activity.log")
LOG_PATH.parent.mkdir(exist_ok=True)

# Dynamisk whale-analyse for flere toppcoins
async def get_whale_activity_score(coin_symbol: str) -> float:
    try:
        coin_symbol = coin_symbol.lower()
        score = 0.0
        confidence = 1.0
        trigger_info = ""

        async with aiohttp.ClientSession() as session:
            if coin_symbol == "btc":
                url = "https://api.blockchain.info/charts/trade-volume?timespan=1days&format=json"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        values = data.get("values", [])
                        if len(values) >= 6:
                            last_4h_vol = sum([v["y"] for v in values[-1:]])
                            total_24h = sum([v["y"] for v in values])
                            ratio_4h = last_4h_vol / total_24h if total_24h else 0
                            confidence = 0.95
                            if total_24h > 800_000_000 and ratio_4h > 0.25:
                                score += 4.0
                                trigger_info = f"BTC | 4h: {last_4h_vol:.2f} / 24h: {total_24h:.2f}"

            elif coin_symbol == "eth":
                url = "https://api.blockchair.com/ethereum/stats"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tx_count = data.get("data", {}).get("transactions", 0)
                        if tx_count > 1_500_000:
                            score += 3.0
                            confidence = 0.9
                            trigger_info = f"ETH | TX count: {tx_count}"

            elif coin_symbol == "bnb":
                url = f"https://api.bscscan.com/api?module=stats&action=bnbprice&apikey={BSCSCAN_API_KEY}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        price = float(data.get("result", {}).get("ethusd", 0))
                        if price > 550:
                            score += 2.5
                            confidence = 0.8
                            trigger_info = f"BNB | Price: {price}"

            elif coin_symbol == "ada":
                url = "https://cardano-mainnet.blockfrost.io/api/v0/epochs/latest"
                headers = {"project_id": BLOCKFROST_API_KEY}
                async with aiohttp.ClientSession(headers=headers) as session2:
                    async with session2.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            active_stake = int(data.get("active_stake", 0))
                            if active_stake > 25_000_000_000_000_000:
                                score += 3.0
                                confidence = 0.8
                                trigger_info = f"ADA | Stake: {active_stake}"

            elif coin_symbol in ["sol", "xrp", "matic", "doge"]:
                cg_id = {
                    "sol": "solana",
                    "xrp": "ripple",
                    "matic": "polygon",
                    "doge": "dogecoin"
                }.get(coin_symbol)

                url = f"https://api.coingecko.com/api/v3/coins/{cg_id}"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        market_data = data.get("market_data", {})
                        volume = market_data.get("total_volume", {}).get("usd", 0)
                        cap = market_data.get("market_cap", {}).get("usd", 1)
                        ratio = volume / cap if cap else 0
                        avg_7d_vol = market_data.get("total_volume", {}).get("usd", 0) / 7

                        if volume > 2 * avg_7d_vol:
                            score += 2.5
                        if ratio > 0.5:
                            score += 1.5
                        elif ratio > 0.2:
                            score += 1.0

                        confidence = 0.7
                        trigger_info = f"{coin_symbol.upper()} | Volume: {volume}, Ratio: {ratio:.2f}"

        final_score = round(min(score + math.log(score + 1) * 0.5, 10.0) * confidence, 2)

        if trigger_info:
            with open(LOG_PATH, "a") as logf:
                logf.write(f"[{datetime.utcnow()}] {coin_symbol.upper()} – score: {final_score} – Trigger: {trigger_info}\n")

        return final_score

    except Exception as e:
        logger.warning(f"Whale tracker error for {coin_symbol}: {e}")
        return 0.0
