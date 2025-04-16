import aiohttp
import logging
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()

# 🚀 v2.3 Elite – Multikilde sentimentanalyse
async def get_sentiment_score(coin_id: str) -> float:
    try:
        score_total = 0.0
        sources_used = []

        # 1. Google Trends via SerpAPI (simulert med vanlig søk)
        google_trend_score = 0.0
        url = f"https://serpapi.com/search.json?q={coin_id}+crypto&engine=google_trends&api_key={SERPAPI_KEY}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    interest = data.get("interest_over_time", [])
                    if interest:
                        latest = interest[-1].get("value", 0)
                        if latest > 75:
                            google_trend_score = 3.0
                        elif latest > 50:
                            google_trend_score = 2.0
                        elif latest > 25:
                            google_trend_score = 1.0
                        sources_used.append("Google Trends")

        # 2. Reddit sentiment
        reddit_score = 0.0
        reddit_url = f"https://www.reddit.com/search.json?q={coin_id}&sort=new"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(reddit_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                posts = data.get("data", {}).get("children", [])
                sentiment_sum = 0
                for post in posts[:10]:
                    title = post.get("data", {}).get("title", "")
                    sentiment = analyzer.polarity_scores(title)
                    sentiment_sum += sentiment["compound"]
                reddit_score = max(0, min(3.0, sentiment_sum))
                sources_used.append("Reddit")

        # 3. Twitter/X sentiment via SerpAPI
        x_score = 0.0
        x_url = f"https://serpapi.com/search.json?engine=google&q=site:twitter.com+{coin_id}+crypto&api_key={SERPAPI_KEY}"
        async with session.get(x_url) as resp:
            if resp.status == 200:
                data = await resp.json()
                tweets = data.get("organic_results", [])
                x_sum = 0
                for tweet in tweets[:5]:
                    text = tweet.get("title", "")
                    score = analyzer.polarity_scores(text)
                    x_sum += score["compound"]
                x_score = max(0, min(3.0, x_sum))
                sources_used.append("X / Twitter")

        # Endelig poengsummering
        score_total = google_trend_score + reddit_score + x_score
        final_score = round(min(score_total, 10.0), 2)

        # Logging
        logger.info(f"Sentiment for {coin_id}: {final_score} via {sources_used}")
        return final_score

    except Exception as e:
        logger.warning(f"Sentiment error for {coin_id}: {e}")
        return 0.0
