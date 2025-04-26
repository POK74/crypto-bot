# analyser.py

from typing import Dict

def dynamisk_analyse(indikatorer_15m: Dict, indikatorer_1h: Dict) -> Dict:
    """
    Ekte analyse basert på tekniske indikatorer på 15m og 1h timeframe.
    """
    short_score = 50
    mid_score = 50
    trend = "Sideways"
    momentum = "Stable"
    volume_comment = "Average volume"

    # Trend-beregning
    if indikatorer_15m["EMA9"] > indikatorer_15m["EMA21"] > indikatorer_15m["EMA50"]:
        trend = "Bullish"
        short_score += 10
    elif indikatorer_15m["EMA9"] < indikatorer_15m["EMA21"] < indikatorer_15m["EMA50"]:
        trend = "Bearish"
        short_score -= 10

    # Momentum-beregning
    if indikatorer_15m["RSI"] > 60 and indikatorer_15m["MACD"] > 0:
        momentum = "Strong Positive"
        short_score += 5
    elif indikatorer_15m["RSI"] < 40 and indikatorer_15m["MACD"] < 0:
        momentum = "Strong Negative"
        short_score -= 5

    # Volume sjekk
    if indikatorer_15m["Volume"] > 1.2 * indikatorer_15m["Volume_SMA"]:
        volume_comment = "Above Average"
    elif indikatorer_15m["Volume"] < 0.8 * indikatorer_15m["Volume_SMA"]:
        volume_comment = "Below Average"

    # Mid-term analyse basert på 1h timeframe
    if indikatorer_1h["EMA9"] > indikatorer_1h["EMA21"]:
        mid_score += 5
    elif indikatorer_1h["EMA9"] < indikatorer_1h["EMA21"]:
        mid_score -= 5

    # Sikre score mellom 0-100
    short_score = max(0, min(100, short_score))
    mid_score = max(0, min(100, mid_score))

    return {
        "trend": trend,
        "momentum": momentum,
        "volume_comment": volume_comment,
        "short_score": short_score,
        "mid_score": mid_score
    }


def foreslaa_entry_exit(indikatorer_15m: Dict) -> Dict:
    """
    Lager forslag til Entry, Stop Loss og Target basert på indikatorene.
    """
    entry_price = indikatorer_15m["EMA21"]
    stop_loss = indikatorer_15m["BB_lower"]
    target1 = indikatorer_15m["BB_upper"]
    target2 = indikatorer_15m["EMA200"] if not str(indikatorer_15m["EMA200"]).lower() == 'nan' else None

    return {
        "entry": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "target1": round(target1, 2),
        "target2": round(target2, 2) if target2 else None,
        "note": "Wait for breakout confirmation above EMA21 with strong volume."
    }
