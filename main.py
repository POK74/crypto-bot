import os
import asyncio
import logging
import numpy as np
from telegram_handler import send_telegram_message
from data_collector import fetch_top_coins, fetch_price_data, fetch_news, fetch_whale_transactions
from analysemotor import Analyzer
import pandas as pd

# Konfigurer logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def detect_breakout(df):
    if df is None or len(df) < 20:
        return False
    df["ma20"] = df["close"].rolling(window=20).mean()
    last_price = df["close"].iloc[-1]
    ma20 = df["ma20"].iloc[-1]
    return last_price > ma20 and df["close"].iloc[-2] <= df["ma20"].iloc[-2]

async def main():
    # Initialiser Analyzer
    analyzer = Analyzer()

    # Generer et enkelt treningsdatasett for å trene StandardScaler og XGBoost
    # Dette er et eksempelsett med 100 rader, 2 funksjoner (close, volume)
    np.random.seed(42)
    train_data = np.random.rand(100, 2) * 1000  # Tilfeldige verdier for close og volume
    train_labels = np.random.randint(0, 2, 100)  # Tilfeldige etiketter (0 eller 1)
    analyzer.fit(train_data, train_labels)
    logger.info("Analyzer fitted with training data")

    while True:
        try:
            coins = await fetch_top_coins()
            logger.info(f"Fetched top 100 coins: {coins}")
            for coin in coins[:5]:  # Begrens til topp 5 for testing
                # Hent prisdata og oppdag breakout
                df = await fetch_price_data(coin)
                if df is not None:
                    if await detect_breakout(df):
                        message = f"🚨 Breakout Signal: {coin}/USDT\nPrice: {df['close'].iloc[-1]}"
                        await send_telegram_message(message)
                        logger.info(f"Breakout signal sent for {coin}/USDT")

                # Hent nyheter
                news = await fetch_news(coin)
                for item in news:
                    message = f"📰 News Signal: {coin}\n{item['title']}\n{item['link']}"
                    await send_telegram_message(message)
                    logger.info(f"News signal sent for {coin}: {item['title']}")

                # Hent whale-transaksjoner
                whale_txs = await fetch_whale_transactions(coin)
                if whale_txs:
                    message = f"🐳 Whale Alert: {coin}\nLarge Transactions Detected: {len(whale_txs)} over $500,000"
                    await send_telegram_message(message)
                    logger.info(f"Whale alert sent for {coin}")

                # Analysér data med XGBoost
                if df is not None:
                    # Forbered data for analyse (lukkekurs, volum)
                    data = df[["close", "volume"]].tail(1).values
                    try:
                        prediction = analyzer.analyze_data(data)
                        if prediction and prediction[0] == 1:  # Forutsatt 1 = kjøpssignal
                            message = f"🚀 ML Signal: {coin}/USDT\nPrediction: Buy"
                            await send_telegram_message(message)
                            logger.info(f"ML signal sent for {coin}/USDT")
                    except Exception as e:
                        logger.error(f"Error analyzing data for {coin}: {str(e)}")
                        continue  # Fortsett til neste mynt i stedet for å krasje

        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        await asyncio.sleep(300)  # Vent 5 minutter

if __name__ == "__main__":
    asyncio.run(main())
