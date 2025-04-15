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
    if df is None or len(df) < 10:  # Redusert krav til antall candlesticks
        logger.info("Not enough data for breakout detection")
        return False
    df["ma10"] = df["close"].rolling(window=10).mean()
    df["avg_volume"] = df["volume"].rolling(window=10).mean()
    last_price = df["close"].iloc[-1]
    ma10 = df["ma10"].iloc[-1]
    last_volume = df["volume"].iloc[-1]
    avg_volume = df["avg_volume"].iloc[-1]
    # Sjekk om prisen har krysset MA10 de siste 2 candlene og om volumet er over gjennomsnittet
    recent_cross = any(
        df["close"].iloc[-i] > df["ma10"].iloc[-i] and df["close"].iloc[-i-1] <= df["ma10"].iloc[-i-1]
        for i in range(1, 3)
    )
    volume_increase = last_volume > avg_volume * 1.5  # Volum må være 50 % over gjennomsnittet
    if recent_cross and volume_increase:
        logger.info(f"Breakout detected: {last_price} crossed above MA10 ({ma10}) with volume {last_volume} (avg: {avg_volume})")
        return True
    return False

async def main():
    # Send oppstartsmelding til Telegram
    await send_telegram_message("🤖 Bot started successfully!")
    
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
            
            # Send melding om hvilke mynter som skannes
            scan_count = min(len(coins), 5)  # Vi skanner topp 5
            await send_telegram_message(f"🔍 Scanning top {scan_count} coins: {', '.join(coins[:scan_count])}\nMonitoring news and whale activity...")

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
                    current_price = df["close"].iloc[-1]
                    try:
                        prediction = analyzer.analyze_data(data, current_price)
                        if prediction:
                            message = prediction  # Meldingen genereres i analysemotor.py
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
