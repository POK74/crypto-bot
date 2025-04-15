import os
import aiohttp
import logging
import pandas as pd
import ccxt.async_support as ccxt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def fetch_top_coins():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching top coins: {response.status}")
                    return []
                data = await response.json()
                return [coin["symbol"].upper() for coin in data]
    except Exception as e:
        logger.error(f"Error fetching top coins: {str(e)}")
        return []

async def fetch_price_data(coin):
    try:
        exchange = ccxt.binance({
            "apiKey": os.getenv("BINANCE_API_KEY"),
            "secret": os.getenv("BINANCE_API_SECRET"),
            "enableRateLimit": True,
        })
        symbol = f"{coin}/USDT"
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1h", limit=168)  # 1 uke med 1-times data
        await exchange.close()
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        logger.error(f"Error fetching Binance data for {coin}/USDT: {str(e)}")
        return None

async def fetch_news(coin):
    try:
        serpapi_key = os.getenv("SERPAPI_KEY")
        url = f"https://serpapi.com/search.json?q={coin}+crypto+news&tbm=nws&api_key={serpapi_key}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching news for {coin}: {response.status}")
                    return []
                data = await response.json()
                news_results = data.get("news_results", [])
                return [{"title": news["title"], "link": news["link"]} for news in news_results[:3]]
    except Exception as e:
        logger.error(f"Error fetching news for {coin}: {str(e)}")
        return []

async def fetch_whale_transactions(coin):
    whale_threshold = 500000  # $500,000
    # Ekte adresser for whale-overvåking
    whale_addresses = {
        "ETH": "0x742d35Cc6634C0532925a3b844Bc454e4438f44",  # Vitalik Buterin's adresse (eksempel)
        "BNB": "0xF977814e90dA44bFA03b6295A0616a897441ace",  # Binance Hot Wallet (eksempel)
        "SOL": "5qXynUYqTNUeLDqNxZ2asgYyH2i4Dt5kS6v5nP8W4k6",  # Ekte SOL whale-adresse (eksempel)
        "ADA": "addr1q9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m",  # Ekte ADA-adresse (eksempel)
        "XRP": "rH1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ1vJ",  # Placeholder, må erstattes
    }
    endpoints = {
        "ETH": f"https://api.etherscan.io/api?module=account&action=txlist&address={whale_addresses['ETH']}&apiKey={os.getenv('ETHERSCAN_API_KEY')}",
        "BNB": f"https://api.bscscan.com/api?module=account&action=txlist&address={whale_addresses['BNB']}&apiKey={os.getenv('BSCSCAN_API_KEY')}",
        "SOL": f"https://public-api.solscan.io/account/transactions?account={whale_addresses['SOL']}",
        "ADA": f"https://cardano-mainnet.blockfrost.io/api/v0/addresses/{whale_addresses['ADA']}/transactions",
        "XRP": f"https://api.xrpldata.com/v1/addresses/{whale_addresses['XRP']}/transactions",
    }
    headers = {
        "ADA": {"project_id": os.getenv("BLOCKFROST_API_KEY")},
    }

    url = endpoints.get(coin)
    if not url:
        logger.error(f"No endpoint defined for coin {coin}")
        return []

    async with aiohttp.ClientSession() as session:
        try:
            header = headers.get(coin, {})
            async with session.get(url, headers=header) as response:
                if response.status != 200:
                    logger.error(f"Error fetching whale transactions for {coin}: {response.status}")
                    return []
                data = await response.json()
                if coin in ["ETH", "BNB"]:
                    if data.get("status") != "1":
                        logger.error(f"Error fetching whale transactions for {coin}: {data.get('message')}")
                        return []
                    transactions = data.get("result", [])
                    # Konverter verdier til USD (forutsatt 1e18 decimals for ETH/BNB)
                    large_transactions = [
                        tx for tx in transactions
                        if float(tx.get("value", 0)) / 1e18 * await get_current_price(coin) > whale_threshold
                    ]
                elif coin == "ADA":
                    transactions = data
                    large_transactions = [
                        tx for tx in transactions
                        if float(tx.get("amount", 0)) / 1e6 * await get_current_price(coin) > whale_threshold
                    ]
                else:
                    transactions = data
                    large_transactions = [
                        tx for tx in transactions
                        if float(tx.get("amount", 0)) * await get_current_price(coin) > whale_threshold
                    ]
                return large_transactions
        except Exception as e:
            logger.error(f"Error fetching whale transactions for {coin}: {str(e)}")
            return []

async def get_current_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching price for {coin}: {response.status}")
                    return 1  # Fallback til 1 for å unngå divisjon med 0
                data = await response.json()
                return data.get(coin.lower(), {}).get("usd", 1)
    except Exception as e:
        logger.error(f"Error fetching price for {coin}: {str(e)}")
        return 1
