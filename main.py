import ccxt
import pandas as pd
import ta
from telegram import Bot
import asyncio
import os

# Telegram config
BOT_TOKEN = "8012533338:AAGnD3KP5-YWvi-4xhQb849dDGMk_4pHbJQ"
CHAT_ID = 5613251713
bot = Bot(token=BOT_TOKEN)

# Binance testnet
exchange = ccxt.binance({
    "enableRateLimit": True,
    "apiKey": os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET_KEY")
})
exchange.set_sandbox_mode(True)

# Coins and settings
COINS = [
    "SOL/USDT", "AVAX/USDT", "DOGE/USDT", "SHIB/USDT", "ADA/USDT",
    "XRP/USDT", "JASMY/USDT", "BTC/USDT", "ETH/USDT", "FLOKI/USDT",
    "PEPE/USDT", "API3/USDT", "XCN/USDT"
]
ENTRY_SIZE = 150
BREAKOUT = 0.03
TAKE_PROFIT = 0.08
TRAIL_STOP = 0.04

def send_signal(message):
    bot.send_message(chat_id=CHAT_ID, text=message)  # Removed 'await'

def get_breakout_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="5m", limit=20)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
        last_close = df["close"].iloc[-1]
        prev_close = df["close"].iloc[-2]
        if (last_close / prev_close - 1) >= BREAKOUT:
            return {"symbol": symbol, "price": last_close, "rsi": df["rsi"].iloc[-1]}
        return None
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None

async def main():
    send_signal("🤖 Bot started, scanning 13 coins...")  # Removed 'await'
    while True:
        for symbol in COINS:
            signal = get_breakout_signal(symbol)
            if signal and signal["rsi"] < 75:
                msg = f"Buy {symbol.split('/')[0]}, 3% breakout at ${signal['price']:.6f}"
                send_signal(msg)  # Removed 'await'
                entry_price = signal["price"]
                target_price = entry_price * (1 + TAKE_PROFIT)
                stop_price = entry_price * (1 - TRAIL_STOP)
                send_signal(f"Trade opened: Entry ${entry_price:.6f}, Target ${target_price:.6f}, Stop ${stop_price:.6f}")
        await asyncio.sleep(60)  # Keep 'await' for asyncio.sleep

if __name__ == "__main__":
    asyncio.run(main())
