import datetime
import time

import telebot

from config.constants import SELECT_BOT_TOKEN, CHAT_ID, REGULAR_BOT_TOKEN
from config.utils import is_in_high_range, is_in_low_range
from datastore.primitives import SqliteDatabase, IglooDataElement
from intelligence.primitives import DataProcessor

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
    sqldb = SqliteDatabase()
    while True:
        try:
            current_time = datetime.datetime.now()
            pr = DataProcessor(sqldb=sqldb, current_time=current_time)

            curr_ts = pr.present_timestamp
            curr_val = pr.present_reading
            proj_val = pr.projected_reading
            curr_velo = pr.present_velocity
            time_oor_mins = pr.get_time_out_of_range()

            text_message = f"{curr_ts.strftime('%H:%M')}, {curr_val} -> {proj_val}, {curr_velo:.2f}/min, {time_oor_mins}mins"
            print(text_message)
            send_message(message_text=text_message, bot_var=regular_bot)

            condition_0 = is_in_high_range(proj_val) and time_oor_mins >= 5
            condition_1 = is_in_low_range(proj_val)
            condition_2 = abs(curr_velo) >= 3.5

            if condition_0 or condition_1 or condition_2:
                send_message(message_text=text_message, bot_var=select_bot)

            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
