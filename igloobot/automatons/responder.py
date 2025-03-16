import telebot

from config.constants import SELECT_BOT_TOKEN, REGULAR_BOT_TOKEN
from intelligence.plotting_utils import plot_data

MINS = 60
POLL_INTERVAL = 1 * MINS
UPPER_LIMIT = 150
LOWER_LIMIT = 90

select_bot = telebot.TeleBot(SELECT_BOT_TOKEN)
regular_bot = telebot.TeleBot(REGULAR_BOT_TOKEN)


def poll():
    @regular_bot.message_handler(content_types=['text'])
    def send_welcome(message):
        im_path = plot_data()
        with open(im_path, 'rb') as photo:
            regular_bot.send_photo(chat_id=message.chat.id, photo=photo)

    regular_bot.infinity_polling()


if __name__ == '__main__':
    poll()
