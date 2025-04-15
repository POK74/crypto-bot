import asyncio
import aiohttp
import logging
import time
import re
from textblob import TextBlob
import pandas as pd
import os
import feedparser
from telegram_handler import send_telegram_message

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for mentions (24-hour window)
mentions_cache = {}

# List of 5 coins for testing
COINS = ["BTC", "ETH", "BNB", "SOL", "ADA"]

# GitHub repo mapping for the 5 coins
REPO_MAPPING = {
    "BTC": "bitcoin/bitcoin",
    "ETH": "ethereum/go-ethereum",
    "BNB": "binance-chain/bsc",
    "SOL": "solana-labs/solana",
    "ADA": "input-output-hk/cardano-sl",
}

async def fetch_google_trends(coin, session):
    try:
        api_key = os.getenv("SERPAPI_KEY")
        url = f"https://serpapi.com/search.json?engine=google_trends&q={coin}&date=now 1-d&api_key={api_key}"
        async with session.get(url) as resp:
            data = await resp.json()
            interest = data.get("interest_over_time", {}).get("timeline_data", [{}])[-1].get("value", 0)
            return int(interest)
    except Exception as e:
        logger.error(f"Failed to fetch Google Trends for {coin}: {e}")
        return 0

async def fetch_reddit(coin, session):
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent=os.getenv("REDDIT_USER_AGENT")
        )
        subreddit = reddit.subreddit("CryptoCurrency")
        posts = subreddit.search(coin, limit=10)
        text = " ".join([post.title + " " + post.selftext for post in posts])
        return text
    except Exception as e:
        logger.error(f"Failed to fetch Reddit data for {coin}: {e}")
        return ""

async def fetch_rss(session):
    try:
        url = "https://cointelegraph.com/rss"
        async with session.get(url) as resp:
            text = await resp.text()
            feed = feedparser.parse(text)
            entries = [entry.title + " " + entry.summary for entry in feed.entries]
            return " ".join(entries)
    except Exception as e:
        logger.error(f"Failed to fetch RSS data: {e}")
        return ""

async def fetch_coinmarketcal(coin, session):
    try:
        api_key = os.getenv("COINMARKETCAL_API_KEY")
        url = f"https://api.coinmarketcal.com/v1/events?access_token={api_key}&coins={coin}"
        async with session.get(url) as resp:
            data = await resp.json()
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"Failed to fetch CoinMarketCal data for {coin}: {e}")
        return []

async def fetch_github(coin, session):
    repo = REPO_MAPPING.get(coin)
    if not repo:
        logger.warning(f"No GitHub repo mapped for {coin}")
        return 0
    try:
        headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
        url = f"https://api.github.com/repos/{repo}/commits"
        async with session.get(url, headers=headers) as resp:
            if resp.status == 404:
                logger.warning(f"GitHub repo {repo} not found for {coin}")
                return 0
            if resp.status == 403:
                logger.error("GitHub rate limit exceeded")
                return 0
            data = await resp.json()
            return len(data)  # Antall commits
    except Exception as e:
        logger.error(f"Failed to fetch GitHub data for {coin}: {e}")
        return 0

def calculate_spike(coin, social_data):
    current_time = int(time.time())
    new_mentions = sum([len(re.findall(rf"\b{coin}\b", data, re.IGNORECASE)) for data in social_data])
    
    if coin not in mentions_cache:
        mentions_cache[coin] = []
    mentions_cache[coin].append({"timestamp": current_time, "count": new_mentions})
    
    mentions_cache[coin] = [entry for entry in mentions_cache[coin] if current_time - entry["timestamp"] < 24 * 3600]
    
    if len(mentions_cache[coin]) < 2:
        return 0
    recent_mentions = sum(entry["count"] for entry in mentions_cache[coin][-2:])
    avg_mentions = sum(entry["count"] for entry in mentions_cache[coin][:-2]) / max(1, len(mentions_cache[coin]) - 2)
    if avg_mentions == 0:
        return 0
    spike = (recent_mentions / avg_mentions - 1) * 100
    return max(0, min(spike, 500))

def calculate_sentiment(data):
    if not data:
        return 0
    text = " ".join([str(d) for d in data if d])
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    return max(0, sentiment)

def calculate_trends_score(trends_data):
    return min(trends_data, 100)

def calculate_event_score(events):
    if not events:
        return 0
    return min(len(events) * 10, 30)

async def run_analysis(coins):
    async with aiohttp.ClientSession() as session:
        for coin in coins:
            if coin not in COINS:
                continue

            trends_data, reddit_data, rss_data, events, github_activity = await asyncio.gather(
                fetch_google_trends(coin, session),
                fetch_reddit(coin, session),
                fetch_rss(session),
                fetch_coinmarketcal(coin, session),
                fetch_github(coin, session)
            )

            social_data = [reddit_data, rss_data]

            mentions_spike = calculate_spike(coin, social_data)
            sentiment = calculate_sentiment(social_data)
            trends_score = calculate_trends_score(trends_data)
            event_score = calculate_event_score(events)
            github_score = min(github_activity, 20)

            total_score = (
                (mentions_spike / 500) * 30 +
                (sentiment * 20) +
                (trends_score * 0.2) +
                event_score +
                github_score
            )

            if total_score > 70:
                event_title = events[0]["title"] if events else "N/A"
                message = (
                    f"🚨 COIN ALERT: ${coin}\n"
                    f"Mentions spike: +{mentions_spike:.0f}% (Reddit)\n"
                    f"Sentiment: 🔥 Positive ({sentiment:.2f})\n"
                    f"Google Trends: +{trends_score:.0f}% siste 24t\n"
                    f"Event: {event_title} (CoinMarketCal)\n"
                    f"GitHub Activity: {github_activity} commits\n"
                    f"→ Potensielt bullish bevegelse innen 1–48 timer"
                )
                await send_telegram_message(message)
                logger.info(f"Alert sent for {coin}: score={total_score:.1f}")
