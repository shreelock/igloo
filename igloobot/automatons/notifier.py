import time

import telebot

from config.constants import SELECT_BOT_TOKEN, CHAT_ID, REGULAR_BOT_TOKEN
from config.utils import REPORTS_DATA_DIR, is_out_of_range, VAL_PROJECTED
from intelligence.primitives import DataProcessor, DEFAULT_MINS_IN_FUTURE

MINS = 60
POLL_INTERVAL = 1 * MINS
UPPER_LIMIT = 150
LOWER_LIMIT = 90

select_bot = telebot.TeleBot(SELECT_BOT_TOKEN)
regular_bot = telebot.TeleBot(REGULAR_BOT_TOKEN)


def send_message(message_text, bot_var):
    if message_text:
        bot_var.send_message(chat_id=CHAT_ID, text=message_text)


def run():
    while True:
        try:
            processor = DataProcessor(reports_data_dir=REPORTS_DATA_DIR)
            current_t_str = processor.get_present_timestamp().strftime("%H:%M")

            current_v = processor.get_present_val()
            projected_v = processor.get_projected_val()

            current_roc = (projected_v - current_v) / DEFAULT_MINS_IN_FUTURE
            time_oor_mins = processor.get_time_out_of_range()

            text_message = f"{current_t_str}, {current_v} -> {projected_v}, {current_roc:.2f}/min, {time_oor_mins}mins"
            print(text_message)
            send_message(message_text=text_message, bot_var=regular_bot)

            condition_1 = is_out_of_range(projected_v, value_type=VAL_PROJECTED) and time_oor_mins >= 5
            condition_2 = abs(current_roc) >= 3.5

            if condition_1 or condition_2:
                send_message(message_text=text_message, bot_var=select_bot)

            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
