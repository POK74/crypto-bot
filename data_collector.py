import os
import ccxt.async_support as ccxt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

async def fetch_historical_data_for_training(coin, days=7):
    try:
        exchange = ccxt.binance({
            "apiKey": os.getenv("BINANCE_API_KEY"),
            "secret": os.getenv("BINANCE_API_SECRET"),
            "enableRateLimit": True,
        })
        symbol = f"{coin}/USDT"
        since = exchange.milliseconds() - days * 24 * 60 * 60 * 1000
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe="1h", since=since)
        await exchange.close()

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {coin}: {str(e)}")
        return None
