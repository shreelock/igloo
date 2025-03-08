import telebot

from config.constants import SELECT_BOT_TOKEN, REGULAR_BOT_TOKEN

MINS = 60
POLL_INTERVAL = 1 * MINS
UPPER_LIMIT = 150
LOWER_LIMIT = 90

select_bot = telebot.TeleBot(SELECT_BOT_TOKEN)
regular_bot = telebot.TeleBot(REGULAR_BOT_TOKEN)


@select_bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    select_bot.reply_to(message, f"Howdy : pardner")


select_bot.infinity_polling()