def send_telegram_melding(bot, chat_id, melding):
    bot.send_message(chat_id=chat_id, text=melding)
