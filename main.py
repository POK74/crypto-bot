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
        logger.info("Not enough data for breakout detection")
        return False
    df["ma20"] = df["close"].rolling(window=20).mean()
    last_price = df["close"].iloc[-1]
    ma20 = df["ma20"].iloc[-1]
    # Mindre streng logikk: Sjekk om prisen har krysset MA20 de siste 3 candlene
    recent_cross = any(
        df["close"].iloc[-i] > df["ma20"].iloc[-i] and df["close"].iloc[-i-1] <= df["ma20"].iloc[-i-1]
        for i in range(1, 4)
    )
    if recent_cross:
        logger.info(f"Breakout detected: {last_price} crossed above MA20 ({ma20})")
    return recent_cross

async def main():
    # Initialiser Analyzer
    analyzer = Analyzer()

    # Generer et enkelt treningsdatasett for å trene StandardScaler og XGBoost
    np.random.seed(42)
    train_data = np.random.rand(100, 2) * 1000  # Tilfeldige verdier for close og volume
    train_labels = np.random.randint(0, 2, 100)  # Tilfeldige etiketter (0 eller 1)
    analyzer.fit(train_data, train_labels)
    logger.info("Analyzer fitted with training data")

    # Liste over stablecoins å ekskludere
    stablecoins = ["USDT", "USDC", "USDS", "BSC-USD", "USDE", "BUIDL", "FDUSD", "PYUSD"]

    while True:
        try:
            coins = await fetch_top_coins()
            # Filtrer ut stablecoins
            coins = [coin for coin in coins if coin not in stablecoins]
            logger.info(f"Fetched top 100 coins (filtered): {coins}")
            for coin in coins[:5]:  # Begrens til topp 5 for testing
                # Hent prisdata og oppdag breakout
                df = await fetch_price_data(coin)
                if df is not None:
                    breakout_detected = await detect_breakout(df)
                    if breakout_detected:
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
                    message = f"🐳 Whale Alert: {coin}\nLarge Transactions Detected: {len(whale_txs)} over $100,000"
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
