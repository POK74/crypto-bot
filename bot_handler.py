
import os
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from formatter import tolk_trend, vurder_momentum, vurder_volume, vurder_risk_reward, konklusjon_short_mid, anbefalt_strategi
from img_generator import lag_analysebilde
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Skriv et coin, f.eks. /analyse BONK")
        return

    ticker = context.args[0].upper()
    data = hent_indikatorer(ticker)
    if not data:
        await update.message.reply_text("🚨 Feil: Kunne ikke hente data for coin.")
        return

    ind15 = data["indikatorer_15m"]
    ind1h = data["indikatorer_1h"]

    trend = tolk_trend(ind1h["EMA9"], ind1h["EMA21"], ind1h["EMA50"], ind1h["EMA200"])
    moment = vurder_momentum(ind15["RSI"], ind15["MACD"])
    volume = vurder_volume(ind15["Volume"], ind15["Volume_SMA"])
    risk = vurder_risk_reward(ind15["ATR"], ind15["BB_upper"], ind15["BB_lower"])
    short, mid = konklusjon_short_mid(ind15["RSI"], ind15["STOCHRSI"], ind15["ADX"])
    strategi = anbefalt_strategi(short)

    melding = f"""
📊 Teknisk analyse for {ticker}

✅ Oppsummert analyse
• Trendretning: {trend}
• Momentum: {moment}
• Volume behavior: {volume}
• Risk/Reward: {risk}

📈 Konklusjon:
Sjanse for breakout/reversal:
• 🔵 Short-term (1–8t): {short}%
• 🟢 Mid-term (1–2d): {mid}%

📌 Anbefalt strategi:
• {strategi}
• Kommentar: Automatisk vurdert basert på indikatorer
"""

    bilde_path = lag_analysebilde(ticker, ind15, ind1h)

    await update.message.reply_text(melding)
    with open(bilde_path, "rb") as img:
        await update.message.reply_photo(InputFile(img))

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analyse", analyse))

if __name__ == "__main__":
    app.run_polling()
