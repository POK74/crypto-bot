import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from analyse_motor import analyser_coin
from notifier import send_result

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('✅ Bot er aktiv. Send /analyse COIN for å få teknisk analyse.')

def analyse(update: Update, context: CallbackContext) -> None:
    try:
        coin = context.args[0].upper()
        update.message.reply_text(f"🔍 Kjører analyse på {coin} ...")
        resultat = analyser_coin(coin)
        send_result(resultat, CHAT_ID)
    except IndexError:
        update.message.reply_text("⚠️ Du må skrive /analyse etterfulgt av et coin-symbol, f.eks. /analyse BONK")
    except Exception as e:
        update.message.reply_text(f"🚨 Feil under analyse: {str(e)}")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("analyse", analyse))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
