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
from sklearn.ensemble import RandomForestClassifier
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
            # Hent fra RSS-kilder
            for source in news_sources:
                feed = feedparser.parse(source)
                for entry in feed.entries[:10]:
                    headline = entry.title
                    news_headlines.append(headline)
            
            # Hent fra X
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
            
            # Analyser sentiment og regulatorisk påvirkning
            for idx, ticker in enumerate(coin_tickers):
                coin = coins[idx]
                ticker_headlines = [h for h in news_headlines if ticker in h.lower()]
                if not ticker_headlines:
                    continue
                
                # Sentiment-analyse
                sentiment_score = 0
                regulatory_impact = False
                for headline in ticker_headlines:
                    analysis = TextBlob(headline)
                    sentiment_score += analysis.sentiment.polarity
                    # Sjekk for regulatorisk påvirkning
                    if any(keyword in headline.lower() for keyword in regulatory_keywords):
                        regulatory_impact = True
                        await bot.send_message(chat_id=chat_id, text=f"⚠️ Regulatory Alert for {coin}: {headline}")
                        logger.info(f"Regulatory alert sent for {coin}: {headline}")
                
                if ticker_headlines:
                    avg_sentiment = sentiment_score / len(ticker_headlines)
                    logger.info(f"Sentiment for {coin}: {avg_sentiment:.2f} (based on {len(ticker_headlines)} headlines)")
                    if avg_sentiment > 0.5:
                        message = f"Forventer sterk prisstigning for {coin} basert på nyheter i markedet (sentiment: {avg_sentiment:.2f})"
                        await bot.send_message(chat_id=chat_id, text=message)
                        logger.info(f"Prediction sent for {coin}: {message}")
            
            logger.info("Completed one news scan cycle. Waiting 5 minutes...")
            await asyncio.sleep(300)
    
    except Exception as e:
        logger.error(f"Error in news analysis: {str(e)}")

# Funksjon for å hente whale-aktivitet fra Etherscan
async def fetch_whale_activity(bot, chat_id):
    try:
        etherscan_api_url = "https://api.etherscan.io/api?module=account&action=txlist&address=0x0000000000000000000000000000000000000000&sort=desc&apikey=YOUR_API_KEY"
        whale_threshold = 1000  # 1000 ETH
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        while True:
            async with aiohttp.ClientSession() as session:
                async with session.get(etherscan_api_url, headers=headers) as resp:
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
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 Bot started, scanning 30 coins, news, and whale activity...")
        logger.info("Connected to Telegram.")

        # Koble til live Binance API
        logger.info("Connecting to Binance...")
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'adjustForTimeDifference': True
        })
        logger.info("Connected to Binance.")

        # Last ML-modell
        try:
            model = joblib.load("rf_model.pkl")
            logger.info("ML model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load ML model: {str(e)}. Starting with a fresh model.")
            model = RandomForestClassifier(n_estimators=100, warm_start=True)

        # Myntliste
        coins = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "SHIB/USDT", "ADA/USDT", 
                 "XRP/USDT", "JASMY/USDT", "FLOKI/USDT", "PEPE/USDT", "API3/USDT", 
                 "BONK/USDT", "WIF/USDT", "POPCAT/USDT", "NEIRO/USDT", "TURBO/USDT", 
                 "MEME/USDT", "BOME/USDT", "TON/USDT", "SUI/USDT", "APT/USDT", 
                 "LINK/USDT", "DOT/USDT", "MATIC/USDT", "NEAR/USDT", "RUNE/USDT", 
                 "INJ/USDT", "FTM/USDT", "GALA/USDT", "HBAR/USDT", "ORDI/USDT"]

        # Dictionary for å holde styr på cooldown for hver mynt
        signal_cooldown = {coin: None for coin in coins}
        COOLDOWN_MINUTES = 60

        # Start nyhetsanalyse og whale-aktivitet i parallelle oppgaver
        news_task = asyncio.create_task(fetch_and_analyze_news(coins, bot, TELEGRAM_CHAT_ID))
        whale_task = asyncio.create_task(fetch_whale_activity(bot, TELEGRAM_CHAT_ID))

        # Data for online læring
        training_data = []
        training_labels = []

        # Hovedløkke for pris-skanning
        while True:
            for coin in coins:
                try:
                    # Sjekk om mynten er i cooldown
                    if signal_cooldown[coin]:
                        time_since_signal = (datetime.utcnow() - signal_cooldown[coin]).total_seconds() / 60
                        if time_since_signal < COOLDOWN_MINUTES:
                            logger.info(f"{coin}: In cooldown, {COOLDOWN_MINUTES - time_since_signal:.1f} minutes remaining")
                            continue
                        else:
                            signal_cooldown[coin] = None

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
                    
                    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                    rsi = df['rsi'].iloc[-1]
                    
                    if rsi <= 0 or rsi >= 100:
                        logger.warning(f"{coin}: Invalid RSI value {rsi:.2f}, skipping signal")
                        continue
                    
                    logger.info(f"{coin}: Price change from start {price_change:.2f}% over {time_diff_minutes:.1f} minutes, RSI {rsi:.2f}")
                    
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
                        async with session.get(etherscan_api_url) as resp:
                            data = await resp.json()
                            if data["status"] == "1":
                                transactions = data["result"][:10]
                                whale_txs = len([tx for tx in transactions if int(tx["value"]) / 10**18 > 1000])

                    # ML-prediksjon
                    features = np.array([[sentiment_score, whale_txs, rsi]])
                    prediction = model.predict(features)[0]  # 1 = opp, 0 = ned
                    confidence = model.predict_proba(features)[0].max()
                    logger.info(f"ML Prediction for {coin}: {'Up' if prediction == 1 else 'Down'} with confidence {confidence:.2f}")

                    # Kombiner breakout og ML-prediksjon
                    if price_change >= 2.5 and time_diff_minutes <= 15 and rsi < 80 and prediction == 1:
                        entry = current_price
                        target = entry * 1.08
                        stop = entry * 0.96
                        message = (f"Buy {coin.split('/')[0]}, 2.5% breakout at ${entry:.2f} over {time_diff_minutes:.1f} minutes\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}\n"
                                   f"ML Confidence: {confidence:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Signal sent for {coin}: {message}")
                        signal_cooldown[coin] = datetime.utcnow()

                        # Legg til data for online læring
                        training_data.append([sentiment_score, whale_txs, rsi])
                        training_labels.append(1 if price_change > 0 else 0)

                    # Online læring: Oppdater modellen daglig hvis vi har nok data
                    if len(training_data) >= 10:
                        model.n_estimators += 10
                        model.fit(training_data, training_labels)
                        joblib.dump(model, "rf_model.pkl")
                        logger.info("ML model updated with new data.")
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
