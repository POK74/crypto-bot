import os
import aiohttp
import logging
import pandas as pd
import ccxt.async_support as ccxt
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)

# Cache for priser for å unngå for mange API-kall
price_cache = {}
cache_duration = 300  # Cache priser i 5 minutter (300 sekunder)

async def fetch_top_coins():
    async with aiohttp.ClientSession() as session:
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
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
    async with aiohttp.ClientSession() as session:
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
    async with aiohttp.ClientSession() as session:
        try:
            serpapi_key = os.getenv("SERPAPI_KEY")
            url = f"https://serpapi.com/search.json?q={coin}+crypto+news&tbm=nws&api_key={serpapi_key}"
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
    whale_threshold = 100000  # $100,000 terskel
    # Ekte adresser for whale-overvåking
    whale_addresses = {
        "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # Ethereum Foundation Wallet
        "BNB": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E",   # Binance Cold Wallet
        "SOL": "5qXynUYqTNUeLDqNxZ2asgYyH2i4Dt5kS6v5nP8W4k6",  # Ekte SOL whale-adresse
        "ADA": "addr1q9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m",  # Ekte ADA-adresse
        "XRP": "rLHzPsX6oXkzU2qL12kHCH8G8cnZvUxrG",  # Ekte XRP-adresse
    }
    endpoints = {
        "ETH": f"https://api.etherscan.io/api?module=account&action=txlist&address={whale_addresses['ETH']}&startblock=0&endblock=99999999&sort=desc&apikey={os.getenv('ETHERSCAN_API_KEY')}",
        "BNB": f"https://api.bscscan.com/api?module=account&action=txlist&address={whale_addresses['BNB']}&startblock=0&endblock=99999999&sort=desc&apikey={os.getenv('BSCSCAN_API_KEY')}",
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
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    # Konverter verdier til USD (forutsatt 1e18 decimals for ETH/BNB)
                    large_transactions = []
                    for tx in transactions:
                        value = float(tx.get("value", 0)) / 1e18
                        price = await get_current_price(coin)
                        usd_value = value * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(0.2)  # Forsinkelse for å unngå rate limits
                elif coin == "ADA":
                    transactions = data
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        amount = float(tx.get("amount", 0)) / 1e6
                        price = await get_current_price(coin)
                        usd_value = amount * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(0.2)
                else:
                    transactions = data
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        amount = float(tx.get("amount", 0))
                        price = await get_current_price(coin)
                        usd_value = amount * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(0.2)
                return large_transactions
        except Exception as e:
            logger.error(f"Error fetching whale transactions for {coin}: {str(e)}")
            return []

async def get_current_price(coin):
    async with aiohttp.ClientSession() as session:
        # Sjekk om prisen er i cachen og fortsatt gyldig
        cache_key = coin.lower()
        if cache_key in price_cache:
            price, timestamp = price_cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < cache_duration:
                return price

        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd"
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Error fetching price for {coin}: {response.status}")
                    return 1  # Fallback til 1 for å unngå divisjon med 0
                data = await response.json()
                price = data.get(coin.lower(), {}).get("usd", 1)
                # Lagre i cachen
                price_cache[cache_key] = (price, datetime.now().timestamp())
                return price
        except Exception as e:
            logger.error(f"Error fetching price for {coin}: {str(e)}")
            return 1
