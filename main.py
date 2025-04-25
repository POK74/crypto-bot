
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from notifier import send_telegram_melding

TOKEN = "DIN_BOT_TOKEN_HER"

async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Skriv en ticker, f.eks: /analyse BONK-USD")
        return

    ticker = context.args[0]
    data = hent_indikatorer(ticker)
    if not data:
        await update.message.reply_text("Feil ved henting av data.")
        return

    melding = f"Analyse for {ticker}\nRSI: {data['RSI']}\nEMA9: {data['EMA9']}\nMACD: {data['MACD']}\nATR: {data['ATR']}"
    await update.message.reply_text(melding)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("analyse", analyse))

if __name__ == "__main__":
    app.run_polling()
