import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from formatter import (
    tolk_trend,
    vurder_momentum,
    vurder_volume,
    vurder_risk_reward,
    konklusjon_short_mid,
    anbefalt_strategi,
    utvidet_formatter_output
)
from dotenv import load_dotenv

# Last inn .env-variabler (BOT_TOKEN osv.)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 🔍 Analysekommando
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Skriv et coin, f.eks. /analyse BTC", parse_mode=ParseMode.HTML)
        return

    ticker = context.args[0].upper()
    data = hent_indikatorer(ticker)

    if not data:
        await update.message.reply_text("🚨 Feil: Kunne ikke hente data for coin.", parse_mode=ParseMode.HTML)
        return

    ind15 = data["indikatorer_15m"]
    ind1h = data["indikatorer_1h"]
    df15 = data["df15"]

    # 💡 Tolk indikatorene
    trend = tolk_trend(ind1h["EMA9"], ind1h["EMA21"], ind1h["EMA50"], ind1h["EMA200"])
    moment = vurder_momentum(ind15["RSI"], ind15["MACD"])
    volume = vurder_volume(ind15["Volume"], ind15["Volume_SMA"])
    risk = vurder_risk_reward(ind15["ATR"], ind15["BB_upper"], ind15["BB_lower"])
    short, mid = konklusjon_short_mid(ind15["RSI"], ind15["STOCHRSI"], ind15["ADX"])
    strategi = anbefalt_strategi(short)

    # 🧾 Formater og send svar
    melding = utvidet_formatter_output(ticker, ind15, ind1h, df15, trend, moment, volume, risk, short, mid, strategi)
    await update.message.reply_text(melding, parse_mode=ParseMode.HTML)

# 🚀 Start boten
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analyse", analyse))

if __name__ == "__main__":
    app.run_polling()
