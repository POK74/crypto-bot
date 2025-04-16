import os
import aiohttp
import logging
import pandas as pd
import ccxt.async_support as ccxt
from datetime import datetime, timedelta
import asyncio
import numpy as np

logger = logging.getLogger(__name__)

# Cache for priser for å unngå for mange API-kall
price_cache = {}
cache_duration = 300  # Cache priser i 5 minutter (300 sekunder)

# Begrens gjentatte feilmeldinger i loggen
error_log_counter = {}
error_log_limit = 5  # Maks antall ganger vi logger samme feil

async def fetch_top_coins():
    max_retries = 3
    retry_delay = 10
    for attempt in range(max_retries):
        async with aiohttp.ClientSession() as session:
            try:
                url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
                params = {"x_cg_demo_api_key": os.getenv("COINGECKO_API_KEY")}
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        error_key = "fetch_top_coins_429"
                        if error_log_counter.get(error_key, 0) < error_log_limit:
                            logger.error(f"Error fetching top coins: {response.status}")
                            error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (2 ** attempt))
                            continue
                        return []
                    elif response.status != 200:
                        error_key = f"fetch_top_coins_{response.status}"
                        if error_log_counter.get(error_key, 0) < error_log_limit:
                            logger.error(f"Error fetching top coins: {response.status}")
                            error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                        return []
                    data = await response.json()
                    return [coin["symbol"].upper() for coin in data]
            except Exception as e:
                error_key = "fetch_top_coins_exception"
                if error_log_counter.get(error_key, 0) < error_log_limit:
                    logger.error(f"Error fetching top coins: {str(e)}")
                    error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                return []
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
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1h", limit=168)
            await exchange.close()
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df
        except Exception as e:
            logger.error(f"Error fetching Binance data for {coin}/USDT: {str(e)}")
            return None

async def fetch_historical_data_for_training(coin, days=90):
    """
    Henter historiske data for trening av ML-modellen fra Binance.
    """
    logger.info(f"Fetching historical training data for {coin} from Binance")
    try:
        exchange = ccxt.binance({
            "apiKey": os.getenv("BINANCE_API_KEY"),
            "secret": os.getenv("BINANCE_API_SECRET"),
            "enableRateLimit": True,
        })
        symbol = f"{coin}/USDT"
        logger.info(f"Requesting OHLCV for {symbol} with timeframe=1h, days={days}")
        since = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1h", since=since, limit=days * 24)
        await exchange.close()
        if not ohlcv:
            logger.error(f"No historical data returned for {coin} from Binance")
            return None
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["next_close"] = df["close"].shift(-1)
        df["label"] = np.where(df["next_close"] > df["close"], 1, 0)
        df = df.dropna()
        logger.info(f"Fetched {len(df)} historical data points for {coin} from Binance")
        return df
    except Exception as e:
        logger.error(f"Error fetching historical training data for {coin} from Binance: {str(e)}")
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
    whale_threshold = 100000
    whale_addresses = {
        "BTC": "3E5Kz9J4LmxmyW5t3xEuL9eS5nA3kK1Kq",
        "ETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "BNB": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E",
        "SOL": "5qXynUYqTNUeLDqNxZ2asgYyH2i4Dt5kS6v5nP8W4k6",
        "ADA": "addr1q9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m9v2r4nq7v5k6m",
        "XRP": "rLHzPsX6oXkzU2qL12kHCH8G8cnZvUxrG",
    }
    endpoints = {
        "BTC": f"https://api.blockchain.com/v3/exchange/btc/address/{whale_addresses['BTC']}?api_key={os.getenv('BLOCKCHAIN_API_KEY')}",
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
                    error_text = await response.text()
                    logger.error(f"Error fetching whale transactions for {coin}: {response.status} - {error_text}")
                    return []
                data = await response.json()
                price = await get_current_price(coin)
                if coin == "BTC":
                    transactions = data.get("txs", [])  # Blockchain.com API returnerer transaksjoner under 'txs'
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        total_value = 0
                        outputs = tx.get("out", [])  # Blockchain.com bruker 'out' for outputs
                        for output in outputs:
                            value = int(output.get("value", 0))  # Verdi i satoshis
                            total_value += value
                        value_btc = total_value / 1e8
                        usd_value = value_btc * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(1.0)
                    logger.info(f"Found {len(large_transactions)} large transactions for {coin}")
                    return large_transactions
                elif coin in ["ETH", "BNB"]:
                    if data.get("status") != "1":
                        logger.error(f"Error fetching whale transactions for {coin}: {data.get('message')}")
                        return []
                    transactions = data.get("result", [])
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        value = float(tx.get("value", 0)) / 1e18
                        usd_value = value * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(1.0)
                    logger.info(f"Found {len(large_transactions)} large transactions for {coin}")
                    return large_transactions
                elif coin == "ADA":
                    transactions = data
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        amount = float(tx.get("amount", 0)) / 1e6
                        usd_value = amount * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(1.0)
                    logger.info(f"Found {len(large_transactions)} large transactions for {coin}")
                    return large_transactions
                else:
                    transactions = data
                    if not transactions:
                        logger.error(f"Error fetching whale transactions for {coin}: No transactions found")
                        return []
                    large_transactions = []
                    for tx in transactions:
                        amount = float(tx.get("amount", 0))
                        usd_value = amount * price
                        if usd_value > whale_threshold:
                            large_transactions.append(tx)
                        await asyncio.sleep(1.0)
                    logger.info(f"Found {len(large_transactions)} large transactions for {coin}")
                    return large_transactions
        except Exception as e:
            logger.error(f"Error fetching whale transactions for {coin}: {str(e)}")
            return []

async def get_current_price(coin):
    async with aiohttp.ClientSession() as session:
        cache_key = coin.lower()
        if cache_key in price_cache:
            price, timestamp = price_cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < cache_duration:
                return price

        max_retries = 3
        retry_delay = 10
        for attempt in range(max_retries):
            try:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd"
                params = {"x_cg_demo_api_key": os.getenv("COINGECKO_API_KEY")}
                async with session.get(url, params=params) as response:
                    if response.status == 429:
                        error_key = f"fetch_price_{coin}_429"
                        if error_log_counter.get(error_key, 0) < error_log_limit:
                            logger.error(f"Error fetching price for {coin}: {response.status}")
                            error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay * (2 ** attempt))
                            continue
                        else:
                            return 1
                    elif response.status != 200:
                        error_key = f"fetch_price_{coin}_{response.status}"
                        if error_log_counter.get(error_key, 0) < error_log_limit:
                            logger.error(f"Error fetching price for {coin}: {response.status}")
                            error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                        return 1
                    data = await response.json()
                    price = data.get(coin.lower(), {}).get("usd", 1)
                    price_cache[cache_key] = (price, datetime.now().timestamp())
                    return price
            except Exception as e:
                error_key = f"fetch_price_{coin}_exception"
                if error_log_counter.get(error_key, 0) < error_log_limit:
                    logger.error(f"Error fetching price for {coin}: {str(e)}")
                    error_log_counter[error_key] = error_log_counter.get(error_key, 0) + 1
                return 1
        return 1
