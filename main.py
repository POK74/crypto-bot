import os
import logging
import asyncio
from datetime import datetime
import pandas as pd
import numpy as np
from data_collector import fetch_top_coins, fetch_price_data, fetch_news, fetch_whale_transactions, fetch_historical_data_for_training, get_current_price
from analysemotor import Analyzer
from telegram_handler import send_telegram_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    analyzer = Analyzer()
    training_data = {}
    coins_to_train = ["BTC", "ETH", "BNB", "SOL", "ADA"]

    for coin in coins_to_train:
        logger.info(f"Fetching historical training data for {coin}")
        df = await fetch_historical_data_for_training(coin)
        if df is not None and not df.empty:
            training_data[coin] = df
        else:
            logger.warning(f"Could not fetch training data for {coin}")

    if training_data:
        logger.info("Training ML model with historical data")
        for coin, df in training_data.items():
            analyzer.fit(df)
            logger.info(f"Analyzer fitted with {len(df)} data points for {coin}")
    else:
        logger.error("No training data available, using fallback random data")
        random_data = pd.DataFrame({
            "timestamp": pd.date_range(start=datetime.now(), periods=1000, freq="h"),
            "close": np.random.normal(100, 10, 1000),
            "volume": np.random.normal(1000, 100, 1000)
        })
        random_data["next_close"] = random_data["close"].shift(-1)
        random_data["label"] = np.where(random_data["next_close"] > random_data["close"], 1, 0)
        random_data = random_data.dropna()
        analyzer.fit(random_data)
        logger.info(f"Analyzer fitted with fallback random data")

    coins = await fetch_top_coins()
    logger.info(f"Fetched top 100 coins (filtered): {coins}")
    top_coins = coins[:5]
    await send_telegram_message(f"🔍 Scanning top 5 coins: {', '.join(top_coins)}")

    while True:
        try:
            for coin in top_coins:
                news = await fetch_news(coin)
                for article in news:
                    message = f"📰 News Signal: {coin}\nTitle: {article['title']}\nLink: {article['link']}"
                    await send_telegram_message(message)
                    logger.info(f"News signal sent for {coin}: {article['title']}")
                    await asyncio.sleep(1)

                whale_transactions = await fetch_whale_transactions(coin)
                for tx in whale_transactions:
                    price = await get_current_price(coin)
                    if coin == "BTC":
                        total_value = sum(int(out.get("value", 0)) for out in tx.get("out", [])) / 1e8
                    elif coin in ["ETH", "BNB"]:
                        total_value = float(tx.get("value", 0)) / 1e18
                    else:
                        total_value = float(tx.get("amount", 0))
                    usd_value = total_value * price
                    message = f"🐳 Whale Alert: {coin}\nTransaction Value: {total_value:.2f} {coin} (${usd_value:,.2f})\nTx Hash: {tx.get('hash', 'N/A')}"
                    await send_telegram_message(message)
                    logger.info(f"Whale alert sent for {coin}")
                    await asyncio.sleep(1)

                df = await fetch_price_data(coin)
                if df is not None and not df.empty:
                    window = 20
                    df['ma'] = df['close'].rolling(window=window).mean()
                    df['std'] = df['close'].rolling(window=window).std()
                    df['upper_band'] = df['ma'] + (df['std'] * 0.5)  # Senket til 0.5
                    df['lower_band'] = df['ma'] - (df['std'] * 0.5)
                    latest = df.iloc[-1]
                    logger.info(f"{coin}/USDT - Price: {latest['close']:.2f}, MA: {latest['ma']:.2f}, Std: {latest['std']:.2f}, Upper Band: {latest['upper_band']:.2f}, Lower Band: {latest['lower_band']:.2f}")
                    if latest['close'] > latest['upper_band']:
                        message = f"🚨 Breakout Signal: {coin}/USDT\nPrice: ${latest['close']:.2f}\nAbove Upper Bollinger Band: ${latest['upper_band']:.2f}"
                        await send_telegram_message(message)
                        logger.info(f"Breakout signal sent for {coin}/USDT")
                    elif latest['close'] < latest['lower_band']:
                        message = f"🚨 Breakout Signal: {coin}/USDT\nPrice: ${latest['close']:.2f}\nBelow Lower Bollinger Band: ${latest['lower_band']:.2f}"
                        await send_telegram_message(message)
                        logger.info(f"Breakout signal sent for {coin}/USDT")

                    features = pd.DataFrame({
                        "close": [latest['close']],
                        "volume": [latest['volume']]
                    })
                    prediction = analyzer.predict(features)[0]
                    current_price = latest['close']
                    target_price = current_price * 1.05
                    stop_loss = current_price * 0.98
                    prediction_text = "Buy" if prediction == 1 else "Sell"
                    message = (f"🚀 ML Signal: {coin}/USDT\n"
                               f"Prediction: {prediction_text}\n"
                               f"Current Price: ${current_price:.2f}\n"
                               f"Target Price: ${target_price:.2f} (+5%)\n"
                               f"Stop-Loss: ${stop_loss:.2f} (-2%)\n"
                               f"Horizon: Within 1 hour")
                    await send_telegram_message(message)
                    logger.info(f"ML signal sent for {coin}/USDT")

            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    logger.info("Bot started successfully")
    asyncio.run(main())
