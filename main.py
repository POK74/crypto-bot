import asyncio
import logging
import aiohttp
import ccxt.async_support as ccxt
from textblob import TextBlob
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from telegram_handler import send_telegram_message
from data_collector import get_top_100_coins
import analysemotor
import os

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
BSCSCAN_API_KEY = os.getenv("BSCSCAN_API_KEY")
BLOCKFROST_API_KEY = os.getenv("BLOCKFROST_API_KEY")

# ML Model Setup (XGBoost)
scaler = StandardScaler()
dtrain = xgb.DMatrix(np.array([[0, 0, 0]]), label=[0])  # Placeholder for initial model
model = xgb.train({"eta": 0.1, "max_depth": 6}, dtrain, num_boost_round=10)

# In-memory cache for ML training data
ml_data = []

# In-memory cache for mentions and sentiment (for analysemotor integration)
mentions_cache = {}

async def fetch_binance_data(exchange, symbol):
    try:
        ticker = await exchange.fetch_ticker(symbol)
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='15m', limit=50)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = compute_rsi(df['close'], 14)
        df['macd'], df['signal'] = compute_macd(df['close'])
        return ticker, df
    except Exception as e:
        logger.error(f"Error fetching Binance data for {symbol}: {e}")
        return None, None

def compute_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

async def fetch_news():
    async with aiohttp.ClientSession() as session:
        news_data = []
        sources = [
            ("Cointelegraph", "https://cointelegraph.com/rss"),
            ("Reddit", "https://www.reddit.com/r/CryptoCurrency/.rss"),
            ("X", "https://api.example.com/x_posts")  # Placeholder for X API
        ]
        for source_name, url in sources:
            try:
                async with session.get(url) as response:
                    text = await response.text()
                    news_data.append({"source": source_name, "content": text})
            except Exception as e:
                logger.error(f"Error fetching news from {source_name}: {e}")
        return news_data

async def fetch_whale_transactions(coin):
    whale_threshold = 500000  # $500,000
    endpoints = {
        "ETH": f"https://api.etherscan.io/api?module=account&action=txlist&address=0xWhaleAddress&apiKey={ETHERSCAN_API_KEY}",
        "BNB": f"https://api.bscscan.com/api?module=account&action=txlist&address=0xWhaleAddress&apiKey={BSCSCAN_API_KEY}",
        "SOL": "https://public-api.solscan.io/account/transactions?account=WhaleAddress",
        "ADA": f"https://cardano-mainnet.blockfrost.io/api/v0/addresses/WhaleAddress/transactions?apiKey={BLOCKFROST_API_KEY}",
        "XRP": "https://api.xrpldata.com/v1/addresses/WhaleAddress/transactions"
    }
    async with aiohttp.ClientSession() as session:
        url = endpoints.get(coin, "")
        if not url:
            return []
        try:
            async with session.get(url) as response:
                data = await response.json()
                transactions = data.get("result", [])
                large_txs = [tx for tx in transactions if float(tx.get("value", 0)) / 1e18 > whale_threshold]
                return large_txs
        except Exception as e:
            logger.error(f"Error fetching whale transactions for {coin}: {e}")
            return []

async def train_ml_model():
    global ml_data, model
    if len(ml_data) < 10:
        return
    features = np.array([[d["rsi"], d["macd"], d["volume"]] for d in ml_data])
    labels = np.array([1 if d["price_change"] > 0 else 0 for d in ml_data])
    scaled_features = scaler.fit_transform(features)
    dtrain = xgb.DMatrix(scaled_features, label=labels)
    model = xgb.train({"eta": 0.1, "max_depth": 6}, dtrain, num_boost_round=10)
    ml_data = []  # Reset after training

async def main():
    exchange = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
    })
    
    # Teller for å kjøre analysemotoren kun hver 48. time
    analysemotor_counter = 0
    
    while True:
        try:
            # Fetch top 100 coins
            top_100_coins = await get_top_100_coins()
            logger.info(f"Fetched top 100 coins: {top_100_coins}")

            # Breakout and ML signals
            for coin in top_100_coins:
                symbol = f"{coin}/USDT"
                ticker, df = await fetch_binance_data(exchange, symbol)
                if ticker is None or df is None:
                    continue

                # Breakout signal: Price increase > 2% with 30% volume increase
                price_change = (ticker['last'] / ticker['open'] - 1) * 100
                avg_volume = df['volume'].iloc[-50:-1].mean()
                current_volume = df['volume'].iloc[-1]
                volume_increase = (current_volume / avg_volume - 1) * 100

                if price_change > 2 and volume_increase > 30:
                    message = f"🚨 Breakout Signal: {symbol}\nPrice Increase: {price_change:.2f}%\nVolume Increase: {volume_increase:.2f}%"
                    await send_telegram_message(message)
                    logger.info(f"Breakout signal sent for {symbol}")

                # ML Signal
                features = np.array([[df['rsi'].iloc[-1], df['macd'].iloc[-1], volume_increase]])
                scaled_features = scaler.transform(features)
                dmatrix = xgb.DMatrix(scaled_features)
                prediction = model.predict(dmatrix)[0]
                # Using 0.50 as threshold, but can increase to 0.70 temporarily if model is unreliable
                if prediction > 0.50:
                    message = f"🚀 ML Signal: {symbol}\nConfidence: {prediction:.2f}\nPotential Uptrend Detected"
                    await send_telegram_message(message)
                    logger.info(f"ML signal sent for {symbol}")

                # Collect data for ML training
                ml_data.append({
                    "rsi": df['rsi'].iloc[-1],
                    "macd": df['macd'].iloc[-1],
                    "volume": volume_increase,
                    "price_change": price_change
                })

            # Train ML model if enough data
            await train_ml_model()

            # News Sentiment Analysis
            news_data = await fetch_news()
            for news in news_data:
                blob = TextBlob(news["content"])
                sentiment = blob.sentiment.polarity
                if sentiment > 0.2:
                    for coin in top_100_coins:
                        if coin in news["content"]:
                            message = f"📰 News Signal: {coin}\nSource: {news['source']}\nSentiment: Positive ({sentiment:.2f})"
                            await send_telegram_message(message)
                            logger.info(f"News signal sent for {coin} from {news['source']}")

            # Whale Activity
            whale_coins = ["ETH", "BNB", "SOL", "ADA", "XRP"]
            for coin in whale_coins:
                large_txs = await fetch_whale_transactions(coin)
                if large_txs:
                    message = f"🐳 Whale Alert: {coin}\nLarge Transactions Detected: {len(large_txs)} over $500,000"
                    await send_telegram_message(message)
                    logger.info(f"Whale alert sent for {coin}")

            # Run Analysemotor (for advanced news analysis) every 48 hours
            analysemotor_counter += 1
            if analysemotor_counter >= 192:  # 192 * 15 min = 48 hours
                await analysemotor.run_analysis(top_100_coins)
                analysemotor_counter = 0

        except Exception as e:
            logger.error(f"Error in main loop: {e}")

        # Wait 15 minutes before next cycle
        await asyncio.sleep(15 * 60)

if __name__ == "__main__":
    asyncio.run(main())
