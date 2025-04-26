# bot_bothandler.py

import os
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from analyser import dynamisk_analyse, foreslaa_entry_exit
from formatter import formater_telegram_melding
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 🔍 Analyse command
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a coin symbol, e.g., /analyse BTC",
            parse_mode=ParseMode.HTML
        )
        return

    ticker = context.args[0].upper()
    data = hent_indikatorer(ticker)

    if not data:
        await update.message.reply_text(
            "🚨 Error: Could not retrieve data for the coin.",
            parse_mode=ParseMode.HTML
        )
        return

    ind15 = data["indikatorer_15m"]
    ind1h = data["indikatorer_1h"]

    # 🧠 Perform real analysis
    analyse_result = dynamisk_analyse(ind15, ind1h)
    strategi_result = foreslaa_entry_exit(ind15)

    # 🧾 Format and send the result
    melding = formater_telegram_melding(ticker, analyse_result, strategi_result)
    await update.message.reply_text(melding, parse_mode=ParseMode.HTML)

# 🚀 Start the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("analyse", analyse))

if __name__ == "__main__":
    print("Bot handler is ready and waiting for commands...")
    app.run()  # IKKE polling! Bare server run
