import pandas as pd
import logging
import sys
import os
import ccxt
import ta
import time
import asyncio
from telegram import Bot

# Sett opp logging først
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Starting bot...")

async def main():
    try:
        # Hent miljøvariabler
        TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
        BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

        # Valider miljøvariabler
        if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BINANCE_API_KEY, BINANCE_SECRET_KEY]):
            missing = [var for var, val in [
                ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
                ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
                ("BINANCE_API_KEY", BINANCE_API_KEY),
                ("BINANCE_SECRET_KEY", BINANCE_SECRET_KEY)
            ] if not val]
            logger.error(f"Missing environment variables: {missing}")
            sys.exit(1)

        logger.info("Environment variables loaded successfully.")

        # Koble til Telegram
        logger.info("Connecting to Telegram...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 Bot started, scanning 12 coins...")
        logger.info("Connected to Telegram.")

        # Koble til Binance testnet
        logger.info("Connecting to Binance...")
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'testnet': True,
            'adjustForTimeDifference': True
        })
        logger.info("Connected to Binance.")

        # Myntliste
        coins = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "SHIB/USDT", "ADA/USDT", 
                 "XRP/USDT", "JASMY/USDT", "BTC/USDT", "ETH/USDT", "FLOKI/USDT", 
                 "PEPE/USDT", "API3/USDT"]

        # Hovedløkke
        while True:
            for coin in coins:
                try:
                    # Hent OHLCV-data for siste 60 minutter
                    ohlcv = exchange.fetch_ohlcv(coin, timeframe='1m', limit=60)  # 60 minutter
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Konverter timestamp til lesbar tid (valgfritt for logging)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    # Finn laveste pris i perioden
                    lowest_price = df['low'].min()
                    lowest_price_idx = df['low'].idxmin()
                    lowest_timestamp = df['timestamp'].iloc[lowest_price_idx]
                    
                    # Nåværende pris
                    current_price = df['close'].iloc[-1]
                    current_timestamp = df['timestamp'].iloc[-1]
                    
                    # Beregn prisendring fra laveste punkt
                    price_change = (current_price / lowest_price - 1) * 100  # % endring
                    
                    # Beregn tidsforskjell (i minutter) fra laveste punkt til nå
                    time_diff_minutes = (current_timestamp - lowest_timestamp).total_seconds() / 60
                    
                    # Beregn RSI
                    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                    rsi = df['rsi'].iloc[-1]
                    
                    # Sjekk for ugyldige RSI-verdier
                    if rsi <= 0 or rsi >= 100:
                        logger.warning(f"{coin}: Invalid RSI value {rsi:.2f}, skipping signal")
                        continue
                    
                    # Logg prisendring og RSI
                    logger.info(f"{coin}: Price change from low {price_change:.2f}% over {time_diff_minutes:.1f} minutes, RSI {rsi:.2f}")
                    
                    # Sjekk betingelser: 3% stigning innen 1 time
                    if price_change >= 3 and time_diff_minutes <= 60 and rsi < 75:
                        entry = current_price
                        target = entry * 1.08  # 8% take profit
                        stop = entry * 0.96    # 4% stop loss
                        message = (f"Buy {coin.split('/')[0]}, 3% breakout at ${entry:.2f} over {time_diff_minutes:.1f} minutes\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Signal sent for {coin}: {message}")
                except Exception as e:
                    logger.error(f"Error scanning {coin}: {str(e)}")
                
                # Legg til en liten forsinkelse for å unngå rate-limiting
                await asyncio.sleep(0.5)  # 0.5 sekunder mellom hver mynt
            
            logger.info("Completed one scan cycle. Waiting 60 seconds...")
            await asyncio.sleep(60)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

# Kjør asynkron hovedfunksjon
if __name__ == "__main__":
    asyncio.run(main())
