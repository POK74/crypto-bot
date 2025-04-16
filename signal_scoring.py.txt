import asyncio
import logging
from analyse_motor import analyze_signals
from volume_analyzer import get_volume_boost
from whale_tracker import get_whale_activity_score
from sentiment_scraper import get_sentiment_score
from data_collector import fetch_prices
import json
from datetime import datetime
import pathlib

logger = logging.getLogger(__name__)
SIGNAL_LOG_PATH = pathlib.Path("logs/signal_history.json")
SIGNAL_LOG_PATH.parent.mkdir(exist_ok=True)

recent_signals = []

# Dynamisk, vektet og adaptiv signal scoring
async def calculate_total_score(coin_id: str) -> tuple:
    base_data = await fetch_prices(coin_id, hours=48)
    base_score, base_details = analyze_signals(base_data, coin_id)

    if not base_data or base_score == 0:
        return 0, f"❌ Insufficient base data for {coin_id}"

    volume_task = asyncio.create_task(get_volume_boost(coin_id))
    sentiment_task = asyncio.create_task(get_sentiment_score(coin_id))
    whale_task = asyncio.create_task(get_whale_activity_score(coin_id))

    volume_boost, sentiment_boost, whale_boost = await asyncio.gather(
        volume_task, sentiment_task, whale_task
    )

    # Adaptive vekting basert på effekt
    total_score = (
        base_score * 0.5 +
        volume_boost * 0.2 +
        sentiment_boost * 0.2 +
        whale_boost * 0.1
    )

    # Confluence-bonus hvis alle scorer > 10
    if all(x > 10 for x in [base_score, volume_boost, sentiment_boost, whale_boost]):
        total_score += 5

    # Confidence score basert på datakvalitet (hardkodet her)
    confidence = 0.85 if whale_boost > 2 else 0.75
    total_score *= confidence

    # Kvalitetsmerkelapp
    if total_score > 85:
        quality = "🟢 Ultra-Confluence"
    elif total_score > 70:
        quality = "🟡 Strong Signal"
    else:
        quality = "🔵 Moderate"

    # Repeat-preventer
    global recent_signals
    if coin_id in recent_signals[-3:]:
        logger.info(f"Skipping {coin_id} due to recent signal repetition")
        return 0, f"🔁 Repeat detected, skipped {coin_id}"
    recent_signals.append(coin_id)

    # Logging signalhistorikk
    signal_data = {
        "coin": coin_id,
        "score": round(total_score, 2),
        "time": datetime.utcnow().isoformat(),
        "details": {
            "base": base_score,
            "volume": volume_boost,
            "sentiment": sentiment_boost,
            "whale": whale_boost
        }
    }
    with open(SIGNAL_LOG_PATH, "a") as f:
        f.write(json.dumps(signal_data) + "\n")

    # Telegram-vennlig sammendrag
    breakdown = (
        f"{base_details}\n"
        f"📊 Volum Boost: {volume_boost}\n"
        f"🧠 Sentiment Boost: {sentiment_boost}\n"
        f"🐋 Whale Boost: {whale_boost}\n"
        f"⚖️ Confidence: {confidence}\n"
        f"🏅 Signal Type: {quality}"
    )

    return round(total_score, 2), breakdown
