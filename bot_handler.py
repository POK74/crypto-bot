
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Skriv en ticker, f.eks: /analyse BONK")
        return

    ticker = context.args[0].upper()
    data = hent_indikatorer(ticker)
    if not data:
        await update.message.reply_text("⚠️ Feil ved henting av data.")
        return

    ind15 = data["indikatorer_15m"]
    ind1h = data["indikatorer_1h"]

    melding = f"""
📊 Teknisk analyse for {ticker}
——— 15 Minutter ———
• RSI: {ind15['RSI']}
• StochRSI: {ind15['STOCHRSI']}
• EMA9: {ind15['EMA9']}
• EMA21: {ind15['EMA21']}
• EMA50: {ind15['EMA50']}
• EMA200: {ind15['EMA200']}
• MACD: {ind15['MACD']}
• ATR: {ind15['ATR']}
• ADX: {ind15['ADX']}
• Bollinger: {ind15['BB_lower']} – {ind15['BB_upper']}
• Volume: {ind15['Volume']} / {ind15['Volume_SMA']}

——— 1 Time ———
• RSI: {ind1h['RSI']}
• StochRSI: {ind1h['STOCHRSI']}
• EMA9: {ind1h['EMA9']}
• EMA21: {ind1h['EMA21']}
• EMA50: {ind1h['EMA50']}
• EMA200: {ind1h['EMA200']}
• MACD: {ind1h['MACD']}
• ATR: {ind1h['ATR']}
• ADX: {ind1h['ADX']}
• Bollinger: {ind1h['BB_lower']} – {ind1h['BB_upper']}
• Volume: {ind1h['Volume']} / {ind1h['Volume_SMA']}

✅ Oppsummert analyse
• Trendretning: [Automatisk tolkning her]
• Momentum: [basert på RSI, MACD]
• Volume behavior: [volum vs. snitt]
• Risk/Reward: [ATR, BB avstand]

📈 Konklusjon:
Sjanse for breakout/reversal:
• 🔵 Short-term (1–8t): 75%
• 🟢 Mid-term (1–2d): 80%

📌 Anbefalt strategi:
• Entry: Vent på EMA9 kryss
• SL: Under EMA21 / BB-lower
• Target: Nær BB-upper / RSI 70
• Kommentar: [AI-vurdering her]
"""
    await update.message.reply_text(melding)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analyse", analyse))

if __name__ == "__main__":
    app.run_polling()
