import pandas as pd
import logging
import sys
import os
import ccxt
import ta
import time
import asyncio
from telegram import Bot
from datetime import datetime, timedelta
import feedparser
import requests
import aiohttp
from bs4 import BeautifulSoup
from textblob import TextBlob
import xgboost as xgb
import joblib
import numpy as np

# Sett opp logging først
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting bot...")

# Global variabel for Etherscan API URL
ETHSCAN_API_URL = "https://api.etherscan.io/api?module=account&action=txlist&address=0x0000000000000000000000000000000000000000&sort=desc&apikey=XUKZ1QH46941VJNH9U8CSQN7XVNTRNYKV7"

# Funksjon for å hente nyheter og reguleringsdata fra RSS og X
async def fetch_and_analyze_news(coins, bot, chat_id):
    try:
        coin_tickers = [coin.split('/')[0].lower() for coin in coins]
        news_sources = [
            "https://cointelegraph.com/rss",
            "https://www.reddit.com/r/cryptocurrency/new/.rss"
        ]
        regulatory_keywords = ["ban", "regulation", "legislation", "sec", "lawsuit"]
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        while True:
            news_headlines = []
            for source in news_sources:
                feed = feedparser.parse(source)
                for entry in feed.entries[:10]:
                    headline = entry.title
                    news_headlines.append(headline)
            
            for ticker in coin_tickers:
                try:
                    url = f"https://x.com/search?q=%23{ticker}&src=typed_query&f=live"
                    response = requests.get(url, headers=headers)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    tweets = soup.find_all('div', {'data-testid': 'tweetText'}, limit=5)
                    for tweet in tweets:
                        news_headlines.append(tweet.get_text())
                except Exception as e:
                    logger.error(f"Error fetching X posts for {ticker}: {str(e)}")
            
            for idx, ticker in enumerate(coin_tickers):
                coin = coins[idx]
                ticker_headlines = [h for h in news_headlines if ticker in h.lower()]
                if not ticker_headlines:
                    continue
                
                sentiment_score = 0
                regulatory_impact = False
                for headline in ticker_headlines:
                    analysis = TextBlob(headline)
                    sentiment_score += analysis.sentiment.polarity
                    if any(keyword in headline.lower() for keyword in regulatory_keywords):
                        regulatory_impact = True
                        await bot.send_message(chat_id=chat_id, text=f"⚠️ Regulatory Alert for {coin}: {headline}")
                        logger.info(f"Regulatory alert sent for {coin}: {headline}")
                
                if ticker_headlines:
                    avg_sentiment = sentiment_score / len(ticker_headlines)
                    logger.info(f"Sentiment for {coin}: {avg_sentiment:.2f} (based on {len(ticker_headlines)} headlines)")
                    if avg_sentiment > 0.3:
                        message = f"📈 Potential Buy Signal for {coin}: Positive sentiment ({avg_sentiment:.2f}) based on recent news"
                        await bot.send_message(chat_id=chat_id, text=message)
                        logger.info(f"News-based prediction sent for {coin}: {message}")
            
            logger.info("Completed one news scan cycle. Waiting 5 minutes...")
            await asyncio.sleep(300)
    
    except Exception as e:
        logger.error(f"Error in news analysis: {str(e)}")

# Funksjon for å hente whale-aktivitet fra Etherscan
async def fetch_whale_activity(coins, bot, chat_id):
    try:
        whale_threshold = 1000
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(ETHSCAN_API_URL, headers=headers) as resp:
                    data = await resp.json()
                    if data["status"] != "1":
                        logger.error(f"Etherscan API error: {data['message']}")
                        await asyncio.sleep(300)
                        continue
                    
                    transactions = data["result"][:10]
                    for tx in transactions:
                        value_eth = int(tx["value"]) / 10**18
                        if value_eth > whale_threshold:
                            message = f"🐳 Whale Alert: Large ETH transfer detected - {value_eth:.2f} ETH (Tx Hash: {tx['hash']})"
                            await bot.send_message(chat_id=chat_id, text=message)
                            logger.info(f"Whale alert sent: {message}")
            
            logger.info("Completed one whale scan cycle. Waiting 5 minutes...")
            await asyncio.sleep(300)
    
    except Exception as e:
        logger.error(f"Error in whale activity tracking: {str(e)}")

# Klasse for å spore ytelse
class PerformanceTracker:
    def __init__(self):
        self.trades = []
        self.ml_trades = []
        self.total_trades = 0
        self.winning_trades = 0
        self.ml_total_trades = 0
        self.ml_winning_trades = 0
        self.returns = []
        self.max_losing_streak = 0
        self.current_losing_streak = 0

    def add_trade(self, coin, entry_price, target_price, stop_price, result, trade_type="breakout"):
        if trade_type == "breakout" or trade_type == "short":
            self.total_trades += 1
            if result == "win":
                self.winning_trades += 1
                return_percent = (target_price / entry_price - 1) * 100 if trade_type == "breakout" else (entry_price / target_price - 1) * 100
                self.returns.append(return_percent)
                self.current_losing_streak = 0
            else:
                self.returns.append(-4.0)  # Antatt tap basert på stop-loss
                self.current_losing_streak += 1
                self.max_losing_streak = max(self.max_losing_streak, self.current_losing_streak)
            self.trades.append({
                "coin": coin,
                "entry_price": entry_price,
                "target_price": target_price,
                "stop_price": stop_price,
                "result": result,
                "type": trade_type
            })
        elif trade_type == "ml":
            self.ml_total_trades += 1
            if result == "win":
                self.ml_winning_trades += 1
            self.ml_trades.append({
                "coin": coin,
                "entry_price": entry_price,
                "result": result
            })

    def get_stats(self):
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        ml_win_rate = (self.ml_winning_trades / self.ml_total_trades * 100) if self.ml_total_trades > 0 else 0
        avg_return = np.mean(self.returns) if self.returns else 0
        return (f"Performance: Total Trades: {self.total_trades}, Win Rate: {win_rate:.2f}%, "
                f"Avg Return: {avg_return:.2f}%, Max Losing Streak: {self.max_losing_streak}\n"
                f"ML Signals: Total: {self.ml_total_trades}, Win Rate: {ml_win_rate:.2f}%")

async def main():
    try:
        # Hent miljøvariabler
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

        # Valider miljøvariabler
        if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
            missing = [var for var, val in [
                ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
                ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
            ] if not val]
            logger.error(f"Missing environment variables: {missing}")
            sys.exit(1)

        logger.info("Environment variables loaded successfully.")

        # Koble til Telegram
        logger.info("Connecting to Telegram...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 Bot started, scanning 100 coins, news, and whale activity...")
        logger.info("Connected to Telegram.")

        # Koble til live Binance API
        logger.info("Connecting to Binance...")
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'adjustForTimeDifference': True
        })
        logger.info("Connected to Binance.")

        # Hent topp 100 mynter basert på volum
        logger.info("Fetching top 100 coins by volume...")
        markets = exchange.fetch_tickers()
        sorted_markets = sorted(
            [(symbol, market['quoteVolume']) for symbol, market in markets.items() if symbol.endswith('/USDT')],
            key=lambda x: x[1],
            reverse=True
        )
        coins = [symbol for symbol, _ in sorted_markets[:100]]
        logger.info(f"Top 100 coins: {coins}")

        # Last ML-modell (XGBoost)
        try:
            model = joblib.load("xgb_model.pkl")
            logger.info("XGBoost model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {str(e)}. Starting with a fresh model.")
            model = xgb.XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric='logloss')

        # Dictionary for å holde styr på cooldown for hver mynt
        breakout_cooldown = {coin: None for coin in coins}
        short_cooldown = {coin: None for coin in coins}
        ml_cooldown = {coin: None for coin in coins}
        COOLDOWN_MINUTES = 60

        # Start nyhetsanalyse og whale-aktivitet i parallelle oppgaver
        news_task = asyncio.create_task(fetch_and_analyze_news(coins, bot, TELEGRAM_CHAT_ID))
        whale_task = asyncio.create_task(fetch_whale_activity(coins, bot, TELEGRAM_CHAT_ID))

        # Data for online læring
        training_data = []
        training_labels = []

        # Ytelsesporing
        tracker = PerformanceTracker()

        # Markedsregime-analyse basert på BTC/USDT
        btc_ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe='1h', limit=50)
        btc_df = pd.DataFrame(btc_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        btc_df['ma50'] = btc_df['close'].rolling(window=50).mean()
        btc_current_price = btc_df['close'].iloc[-1]
        btc_ma50 = btc_df['ma50'].iloc[-1]
        market_regime = "bull" if btc_current_price > btc_ma50 else "bear"
        logger.info(f"Market regime: {market_regime}")

        # Hovedløkke for pris-skanning
        while True:
            # Oppdater markedsregime hver time
            btc_ohlcv = exchange.fetch_ohlcv("BTC/USDT", timeframe='1h', limit=50)
            btc_df = pd.DataFrame(btc_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            btc_df['ma50'] = btc_df['close'].rolling(window=50).mean()
            btc_current_price = btc_df['close'].iloc[-1]
            btc_ma50 = btc_df['ma50'].iloc[-1]
            market_regime = "bull" if btc_current_price > btc_ma50 else "bear"
            logger.info(f"Market regime updated: {market_regime}")

            for coin in coins:
                try:
                    # Hent OHLCV-data for siste 15 minutter
                    ohlcv = exchange.fetch_ohlcv(coin, timeframe='1m', limit=15)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    start_price = df['close'].iloc[0]
                    start_timestamp = df['timestamp'].iloc[0]
                    current_price = df['close'].iloc[-1]
                    current_timestamp = df['timestamp'].iloc[-1]
                    
                    price_change = (current_price / start_price - 1) * 100
                    time_diff_minutes = (current_timestamp - start_timestamp).total_seconds() / 60
                    
                    # Teknisk analyse
                    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                    rsi = df['rsi'].iloc[-1]
                    
                    if rsi <= 0 or rsi >= 100:
                        logger.warning(f"{coin}: Invalid RSI value {rsi:.2f}, skipping signal")
                        continue
                    
                    # Volumanalyse
                    avg_volume = df['volume'].mean()
                    current_volume = df['volume'].iloc[-1]
                    volume_increase = (current_volume / avg_volume - 1) * 100 if avg_volume > 0 else 0
                    
                    # MACD
                    macd = ta.trend.MACD(df['close'])
                    macd_line = macd.macd().iloc[-1]
                    signal_line = macd.macd_signal().iloc[-1]
                    
                    # Bollinger Bands
                    bb = ta.volatility.BollingerBands(df['close'])
                    bb_upper = bb.bollinger_hband().iloc[-1]
                    bb_lower = bb.bollinger_lband().iloc[-1]
                    
                    # ATR for dynamiske terskler
                    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range().iloc[-1]
                    breakout_threshold = max(2.0, (atr / current_price * 100) * 2)  # Minimum 2%, eller ATR-basert
                    if market_regime == "bull":
                        breakout_threshold *= 1.2  # Øk terskel i bullmarked
                    elif market_regime == "bear":
                        breakout_threshold *= 0.8  # Reduser terskel i bearmarked
                    tp_multiplier = 2.0 * (atr / current_price)
                    sl_multiplier = 1.0 * (atr / current_price)
                    
                    logger.info(f"{coin}: Price change from start {price_change:.2f}% over {time_diff_minutes:.1f} minutes, RSI {rsi:.2f}, Volume increase {volume_increase:.2f}%, ATR {atr:.4f}")
                    
                    # Hent nyhetssentiment for denne mynten
                    ticker = coin.split('/')[0].lower()
                    sentiment_score = 0
                    news_headlines = []
                    for source in ["https://cointelegraph.com/rss", "https://www.reddit.com/r/cryptocurrency/new/.rss"]:
                        feed = feedparser.parse(source)
                        for entry in feed.entries[:5]:
                            headline = entry.title
                            if ticker in headline.lower():
                                news_headlines.append(headline)
                    if news_headlines:
                        sentiment_score = sum(TextBlob(h).sentiment.polarity for h in news_headlines) / len(news_headlines)

                    # Hent whale-aktivitet (for enkelhet, bare for ETH som en proxy)
                    whale_txs = 0
                    async with aiohttp.ClientSession() as session:
                        async with session.get(ETHSCAN_API_URL) as resp:
                            data = await resp.json()
                            if data["status"] == "1":
                                transactions = data["result"][:10]
                                whale_txs = len([tx for tx in transactions if int(tx["value"]) / 10**18 > 1000])

                    # Prisavvik
                    price_deviation = (current_price - df['close'].mean()) / df['close'].std() if df['close'].std() > 0 else 0

                    # ML-prediksjon (XGBoost)
                    features = pd.DataFrame([[sentiment_score, whale_txs, rsi, current_volume, macd_line - signal_line, price_deviation]],
                                          columns=['sentiment', 'whale_txs', 'rsi', 'volume', 'macd_diff', 'price_deviation'])
                    prediction = model.predict(features)[0]
                    confidence = model.predict_proba(features)[0].max()
                    logger.info(f"ML Prediction for {coin}: {'Up' if prediction == 1 else 'Down'} with confidence {confidence:.2f}")

                    # Breakout-signal (kjøp)
                    if breakout_cooldown[coin]:
                        time_since_breakout = (datetime.utcnow() - breakout_cooldown[coin]).total_seconds() / 60
                        if time_since_breakout < COOLDOWN_MINUTES:
                            logger.info(f"{coin}: Breakout signal in cooldown, {COOLDOWN_MINUTES - time_since_breakout:.1f} minutes remaining")
                        else:
                            breakout_cooldown[coin] = None

                    if (not breakout_cooldown[coin] and price_change >= breakout_threshold and time_diff_minutes <= 15 and
                        volume_increase >= 50):
                        entry = current_price
                        target = entry * (1 + tp_multiplier)
                        stop = entry * (1 - sl_multiplier)
                        message = (f"📈 Breakout Buy Signal for {coin.split('/')[0]}: {price_change:.2f}% increase at ${entry:.2f} over {time_diff_minutes:.1f} minutes\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Breakout signal sent for {coin}: {message}")
                        breakout_cooldown[coin] = datetime.utcnow()

                        # Spor trade for ytelsesanalyse
                        await asyncio.sleep(3600)  # Vent 1 time
                        ohlcv_check = exchange.fetch_ohlcv(coin, timeframe='1m', limit=1)
                        current_price_check = ohlcv_check[0][4]
                        result = "win" if current_price_check >= target else "loss"
                        tracker.add_trade(coin, entry, target, stop, result, trade_type="breakout")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=tracker.get_stats())

                    # Short-signal basert på ML-prediksjon
                    if short_cooldown[coin]:
                        time_since_short = (datetime.utcnow() - short_cooldown[coin]).total_seconds() / 60
                        if time_since_short < COOLDOWN_MINUTES:
                            logger.info(f"{coin}: Short signal in cooldown, {COOLDOWN_MINUTES - time_since_short:.1f} minutes remaining")
                        else:
                            short_cooldown[coin] = None

                    if not short_cooldown[coin] and prediction == 0 and confidence >= 0.55 and time_diff_minutes <= 15:
                        entry = current_price
                        target = entry * (1 - tp_multiplier)
                        stop = entry * (1 + sl_multiplier)
                        message = (f"📉 Short Signal for {coin.split('/')[0]}: Model predicts price decrease with confidence {confidence:.2f}\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Short signal sent for {coin}: {message}")
                        short_cooldown[coin] = datetime.utcnow()

                        # Spor trade for ytelsesanalyse
                        await asyncio.sleep(3600)  # Vent 1 time
                        ohlcv_check = exchange.fetch_ohlcv(coin, timeframe='1m', limit=1)
                        current_price_check = ohlcv_check[0][4]
                        result = "win" if current_price_check <= target else "loss"
                        tracker.add_trade(coin, entry, target, stop, result, trade_type="short")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=tracker.get_stats())

                    # ML-signal (kjøp)
                    if ml_cooldown[coin]:
                        time_since_ml = (datetime.utcnow() - ml_cooldown[coin]).total_seconds() / 60
                        if time_since_ml < COOLDOWN_MINUTES:
                            logger.info(f"{coin}: ML signal in cooldown, {COOLDOWN_MINUTES - time_since_ml:.1f} minutes remaining")
                        else:
                            ml_cooldown[coin] = None

                    if not ml_cooldown[coin] and prediction == 1 and confidence >= 0.55:
                        message = f"📈 ML Buy Signal for {coin.split('/')[0]}: Model predicts price increase with confidence {confidence:.2f}"
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"ML signal sent for {coin}: {message}")
                        ml_cooldown[coin] = datetime.utcnow()

                        # Spor ML-signal for ytelsesanalyse (forenklet: antar treff hvis pris øker innen 1 time)
                        await asyncio.sleep(3600)  # Vent 1 time
                        ohlcv_check = exchange.fetch_ohlcv(coin, timeframe='1m', limit=1)
                        current_price_check = ohlcv_check[0][4]
                        result = "win" if current_price_check > current_price else "loss"
                        tracker.add_trade(coin, current_price, None, None, result, trade_type="ml")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=tracker.get_stats())

                    # Legg til data for online læring
                    training_data.append([sentiment_score, whale_txs, rsi, current_volume, macd_line - signal_line, price_deviation])
                    training_labels.append(1 if price_change > 0 else 0)

                    # Online læring: Oppdater modellen daglig hvis vi har nok data
                    if len(training_data) >= 10:
                        model.n_estimators += 10
                        model.fit(training_data, training_labels)
                        joblib.dump(model, "xgb_model.pkl")
                        logger.info("XGBoost model updated with new data.")
                        training_data = []
                        training_labels = []

                except Exception as e:
                    logger.error(f"Error scanning {coin}: {str(e)}")
                
                await asyncio.sleep(0.5)
            
            logger.info("Completed one scan cycle. Waiting 30 seconds...")
            await asyncio.sleep(30)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        news_task.cancel()
        whale_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
