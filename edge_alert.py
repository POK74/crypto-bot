import asyncio
import os
import time
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

COINS = ["TRUMP-USD", "BTC-USD", "ETC-USD", "BONK-USD", "ADA-USD", "AST-USD", "SHIB-USD", "SOL-USD"]

def analyse_coin(coin):
    df = yf.download(coin, interval="15m", period="1d")
    if df.empty or len(df) < 50:
        return None

    df["EMA21"] = df["Close"].ewm(span=21).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()
    df["RSI"] = compute_rsi(df["Close"], 14)
    df["MACD"] = df["Close"].ewm(span=12).mean() - df["Close"].ewm(span=26).mean()
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    df["Volume_SMA"] = df["Volume"].rolling(window=20).mean()

    last = df.iloc[-1]

    trend = "Bullish" if last["EMA21"] > last["EMA50"] else "Sideways"
    macd_cross = last["MACD"] > last["Signal"]
    rsi_strong = last["RSI"] > 70
    volume_valid = last["Volume"] > last["Volume_SMA"]

    if trend == "Bullish" and macd_cross and rsi_strong and volume_valid:
        entry = round(last["Close"], 8)
        sl = round(last["EMA21"] * 0.98, 8)
        target = round(last["EMA200"], 8) if not pd.isna(last["EMA200"]) else round(entry * 1.1, 8)

        risk_reward_ratio = (target - entry) / (entry - sl) if (entry - sl) != 0 else 0
        if risk_reward_ratio < 2:
            return None

        melding = f"""
📊 [EDGE SIGNAL] {coin.replace("-USD", "-USDT")}

📈 Trend: {trend} (EMA21 > EMA50)
📊 RSI: {round(last['RSI'], 1)} (overkjøpt)
💥 MACD: Bullish crossover
🔊 Volum: {int(last['Volume'])} > SMA={int(last['Volume_SMA'])} (validert)

🎯 Entry: {entry}
🛡️ SL: {sl}
🏁 Target: {target}

🧠 Kommentar: Kjøpssignal trigget med høy RSI + MACD + volumbekreftelse. Vurder inngang kun med støtte i trend.
"""
        return melding.strip()

    return None

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

async def sjekk_edge_signaler():
    total_start = time.time()
    antall_signal = 0
    for coin in COINS:
        start = time.time()
        melding = analyse_coin(coin)
        elapsed = time.time() - start
        print(f"⏱️ Ferdig analyse for {coin} på {elapsed:.2f} sekunder.")
        if melding:
            await bot.send_message(chat_id=CHAT_ID, text=melding)
            antall_signal += 1
    total_elapsed = time.time() - total_start
    oppsummering = f"\n\n🚀 Ferdig!\nAnalysert {len(COINS)} coins på {total_elapsed:.2f} sekunder.\nFant {antall_signal} signaler."
    await bot.send_message(chat_id=CHAT_ID, text=oppsummering)

if __name__ == "__main__":
    asyncio.run(sjekk_edge_signaler())
