# bot_bothandler.py

import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from analyse_motor import hent_indikatorer
from analyser import dynamisk_analyse, foreslaa_entry_exit
from formatter import formater_telegram_melding
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Telegram Application
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

# Initialize FastAPI App
app = FastAPI()

# Analyse command
async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a coin symbol, e.g., /analyse BTC",
            parse_mode="HTML"
        )
        return

    ticker = context.args[0].upper()
    data = hent_indikatorer(ticker)

    if not data:
        await update.message.reply_text(
            "🚨 Error: Could not retrieve data for the coin.",
            parse_mode="HTML"
        )
        return

    ind15 = data["indikatorer_15m"]
    ind1h = data["indikatorer_1h"]

    analyse_result = dynamisk_analyse(ind15, ind1h)
    strategi_result = foreslaa_entry_exit(ind15)

    melding = formater_telegram_melding(ticker, analyse_result, strategi_result)
    await update.message.reply_text(melding, parse_mode="HTML")

# Register command handler
telegram_app.add_handler(CommandHandler("analyse", analyse))

# Webhook endpoint
@app.post(f"/{BOT_TOKEN}")
async def webhook_handler(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, telegram_app.bot)
    await telegram_app.update_queue.put(update)
    return {"status": "ok"}
