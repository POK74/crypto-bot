import pandas as pd
import logging
import sys
import os
import ccxt
import ta
import time
import asyncio
from telegram import Bot
from datetime import datetime, timedelta

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

        # Valider miljøvariabler
        if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
            missing = [var for var, val in [
                ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
                ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)
            ] if not val]
            logger.error(f"Missing environment variables: {missing}")
            sys.exit(1)

        logger.info("Environment variables loaded successfully.")

        # Koble til Telegram
        logger.info("Connecting to Telegram...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 Bot started, scanning 12 coins...")
        logger.info("Connected to Telegram.")

        # Koble til live Binance API (uten API-nøkler, siden vi kun henter offentlige data)
        logger.info("Connecting to Binance...")
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'adjustForTimeDifference': True
        })
        logger.info("Connected to Binance.")

        # Myntliste
        coins = ["SOL/USDT", "AVAX/USDT", "DOGE/USDT", "SHIB/USDT", "ADA/USDT", 
                 "XRP/USDT", "JASMY/USDT", "BTC/USDT", "ETH/USDT", "FLOKI/USDT", 
                 "PEPE/USDT", "API3/USDT"]

        # Dictionary for å holde styr på cooldown for hver mynt
        signal_cooldown = {coin: None for coin in coins}
        COOLDOWN_MINUTES = 60  # 1 time cooldown

        # Hovedløkke
        while True:
            for coin in coins:
                try:
                    # Sjekk om mynten er i cooldown
                    if signal_cooldown[coin]:
                        time_since_signal = (datetime.utcnow() - signal_cooldown[coin]).total_seconds() / 60
                        if time_since_signal < COOLDOWN_MINUTES:
                            logger.info(f"{coin}: In cooldown, {COOLDOWN_MINUTES - time_since_signal:.1f} minutes remaining")
                            continue
                        else:
                            signal_cooldown[coin] = None  # Reset cooldown

                    # Hent OHLCV-data for siste 60 minutter
                    ohlcv = exchange.fetch_ohlcv(coin, timeframe='1m', limit=60)  # 60 minutter
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # Konverter timestamp til lesbar tid
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    
                    # Pris ved starten av perioden (første lys)
                    start_price = df['close'].iloc[0]
                    start_timestamp = df['timestamp'].iloc[0]
                    
                    # Nåværende pris og tid
                    current_price = df['close'].iloc[-1]
                    current_timestamp = df['timestamp'].iloc[-1]
                    
                    # Beregn prisendring fra startprisen
                    price_change = (current_price / start_price - 1) * 100  # % endring
                    
                    # Beregn tidsforskjell (i minutter) fra start til nå
                    time_diff_minutes = (current_timestamp - start_timestamp).total_seconds() / 60
                    
                    # Beregn RSI
                    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
                    rsi = df['rsi'].iloc[-1]
                    
                    # Sjekk for ugyldige RSI-verdier
                    if rsi <= 0 or rsi >= 100:
                        logger.warning(f"{coin}: Invalid RSI value {rsi:.2f}, skipping signal")
                        continue
                    
                    # Logg prisendring og RSI
                    logger.info(f"{coin}: Price change from start {price_change:.2f}% over {time_diff_minutes:.1f} minutes, RSI {rsi:.2f}")
                    
                    # Sjekk betingelser: 2% stigning fra start innen 1 time
                    if price_change >= 2 and time_diff_minutes <= 60 and rsi < 80:
                        entry = current_price
                        target = entry * 1.08  # 8% take profit
                        stop = entry * 0.96    # 4% stop loss
                        message = (f"Buy {coin.split('/')[0]}, 2% breakout at ${entry:.2f} over {time_diff_minutes:.1f} minutes\n"
                                   f"Trade opened: Entry ${entry:.2f}, Target ${target:.2f}, Stop ${stop:.2f}")
                        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                        logger.info(f"Signal sent for {coin}: {message}")
                        signal_cooldown[coin] = datetime.utcnow()  # Sett cooldown
                except Exception as e:
                    logger.error(f"Error scanning {coin}: {str(e)}")
                
                # Legg til en liten forsinkelse for å unngå rate-limiting
                await asyncio.sleep(0.5)  # 0.5 sekunder mellom hver mynt
            
            logger.info("Completed one scan cycle. Waiting 30 seconds...")
            await asyncio.sleep(30)  # Redusert fra 60 til 30 sekunder

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

# Kjør asynkron hovedfunksjon
if __name__ == "__main__":
    asyncio.run(main())
