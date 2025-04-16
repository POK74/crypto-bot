import numpy as np
import pandas as pd

def analyze_market_conditions(df):
    if df is None or df.empty:
        return {"confidence": None}

    df["ma"] = df["close"].rolling(window=20).mean()
    df["std"] = df["close"].rolling(window=20).std()
    df["upper_band"] = df["ma"] + 2 * df["std"]
    df["lower_band"] = df["ma"] - 2 * df["std"]

    last_price = df["close"].iloc[-1]
    last_ma = df["ma"].iloc[-1]

    confidence = 0
    if last_price > last_ma:
        confidence += 2
    if last_price > df["upper_band"].iloc[-1]:
        confidence += 2
    if df["volume"].iloc[-1] > df["volume"].mean():
        confidence += 1

    return {
        "confidence": confidence,
        "bias": "Bullish" if last_price > last_ma else "Bearish",
        "volume": df["volume"].iloc[-1]
    }
