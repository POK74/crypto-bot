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
        etherscan_api_url = "https://api.etherscan.io/api?module=account&action=txlist&address=0x0000000000000000000000000000000000000000&sort=desc&apikey=XUKZ1QH46941VJNH9U8CSQN7XVNTRNYKV7"
        whale_threshold = 1000
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
                 "INJ/USDT", "FTM/USDT", "GALA/USDT", "HB Search for more...AR/USDT", "ORDI/USDT"]

        # Dictionary for å holde styr på cooldown for hver mynt
        signal_cooldown = {coin: None for coin in coins}
        COOLDOWN_MINUTES = 60

        # Start nyhetsanalyse og whale-aktivitet i parallelle oppgaver
        news_task = asyncio.create_task(fetch_and_analyze_news(coins, bot, TELEGRAM_CHAT_ID))
        whale_task = asyncio.create_task(fetch_whale_activity(bot, TELEGRAM_CHAT_ID))

        # Data for online læring
        training_data = []
        training_labels = []

        # Hovedløk
