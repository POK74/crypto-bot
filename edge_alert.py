import os
import asyncio
import yfinance as yf
import pandas as pd
import ta
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=BOT_TOKEN)

# Dine valgte coins
TICKERS = [
    "TRUMP-USD",
    "BTC-USD",
    "ETC-USD",
    "BONK-USD",
    "ADA-USD",
    "AST-USD",
    "SHIB-USD",
    "SOL-USD"
]

async def sjekk_edge_signaler():
    meldinger = []

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, interval="15m", period="2d").squeeze()

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            if df.empty:
                continue

            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            # Beregn indikatorer
            rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]
            macd = ta.trend.MACD(close).macd_diff().iloc[-1]
            volume_sma = volume.rolling(window=20).mean().iloc[-1]
            latest_volume = volume.iloc[-1]

            # Betingelser for varsel
            if rsi > 65 and (macd > 0 or latest_volume > volume_sma):
                meldinger.append(f"📣 {ticker} viser styrke! RSI={rsi:.1f}, MACD={macd:.3f}, Volum={latest_volume:.0f} > SMA={volume_sma:.0f}")

        except Exception as e:
            print(f"Feil ved behandling av {ticker}: {e}")

    # Send varsler
    if meldinger:
        for melding in meldinger:
            await bot.send_message(chat_id=CHAT_ID, text=melding)
    else:
        print("Ingen signaler denne runden.")

if __name__ == "__main__":
    asyncio.run(sjekk_edge_signaler())
