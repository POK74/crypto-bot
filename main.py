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
from bs4 import BeautifulSoup
from textblob import TextBlob

# Sett opp logging først
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting bot...")

# Funksjon for å hente nyheter fra RSS og X
async def fetch_and_analyze_news(coins, bot, chat_id):
    try:
        # Mynt-tickers for nyhetssøk (fjerner /USDT)
        coin_tickers = [coin.split('/')[0].lower() for coin in coins]
        # Kilder: CoinTelegraph RSS og Reddit r/cryptocurrency RSS
        news_sources = [
            "https://cointelegraph.com/rss",  # CoinTelegraph RSS
            "https://www.reddit.com/r/cryptocurrency/new/.rss"  # Reddit r/cryptocurrency
        ]
        headers = {'User-Agent': 'Mozilla/5.0'}  # For å unngå blokkering ved scraping
        
        while True:
            news_headlines = []
            # Hent fra RSS-kilder
            for source in news_sources:
                feed = feedparser.parse(source)
                for entry in feed.entries[:10]:  # Begrens til 10 nyeste
                    headline = entry.title
                    news_headlines.append(headline)
            
            # Hent fra X (enkel scraper, vær forsiktig med rate limits)
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
            
            # Analyser sentiment for hver mynt
            for idx, ticker in enumerate(coin_tickers):
                coin = coins[idx]
                ticker_headlines = [h for h in news_headlines if ticker in h.lower()]
                if not ticker_headlines:
                    continue
                
                # Sentiment-analyse
                sentiment_score = 0
                for headline in ticker_headlines:
                    analysis = TextBlob(headline)
                    sentiment_score += analysis.sentiment.polarity  # Score fra -1 (negativ) til 1 (positiv)
                
                # Gjennomsnittlig sentiment
                if ticker_headlines:
                    avg_sentiment = sentiment_score / len(ticker_headlines)
                    logger.info(f"Sentiment for {coin}: {avg_sentiment:.2f} (based on {len(ticker_headlines)} headlines)")
                    
                    # Hvis sterkt positivt sentiment, send prediksjon
                    if avg_sentiment > 0.5:  # Terskel for "sterkt positivt"
                        message = f"Forventer sterk prisstigning for {coin} basert på nyheter i markedet (sentiment: {avg_sentiment:.2f})"
                        await bot.send_message(chat_id=chat_id, text=message)
                        logger.info(f"Prediction sent for {coin}: {message}")
            
            # Vent 5 minutter før neste nyhetsskanning
            logger.info("Completed one news scan cycle. Waiting 5 minutes...")
            await asyncio.sleep(300)
    
    except Exception as e:
        logger.error(f"Error in news analysis: {str(e)}")

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
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 Bot started, scanning 12 coins and news...")
        logger.info("Connected to Telegram.")

        # Koble til live Binance API
        logger.info("Connecting to Binance...")
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'adjustForTimeDifference': True
        })
        logger.info("Connected to Binance.")

        # Myntliste
        coins = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "SHIB/USDT", "ADA/USDT", 
                 "XRP/USDT", "JASMY/USDT", "FLOKI/USDT", "PEPE/USDT", "API3/USDT",
                 "BONK/USDT", "WIF/USDT"]

        # Dictionary for å holde styr på cooldown for hver mynt
        signal_cooldown = {coin: None for coin in coins}
        COOLDOWN_MINUTES = 60

        # Start nyhetsanalyse i en parallell oppgave
        news_task = asyncio.create_task(fetch_and_analyze_news(coins, bot, TELEGRAM_CHAT_ID))

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

                    # Hent OHLCV-data for siste 30 minutter
                    ohlcv = exchange.fetch_ohlcv(coin, timeframe='1m', limit=30)
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
                    
                    if price_change >= 2 and time_diff_minutes <= 30 and rsi < 80:
                        entry = current_price
                        target = entry * 1.08
                        stop = entry * 0.96
                        message = (f"Buy {coin.split('/')[0]}, 2% breakout at ${entry:.2f} over {time_diff_minutes:.1f} minutes\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Signal sent for {coin}: {message}")
                        signal_cooldown[coin] = datetime.utcnow()
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

if __name__ == "__main__":
    asyncio.run(main())
