import time

import telebot

from intelligence.primitives import DataProcessor, CurrStatus
from config.constants import REPORTS_DATA_DIR, BOT_TOKEN, CHAT_ID

MINS = 60
POLL_INTERVAL = 1 * MINS
UPPER_LIMIT = 150
LOWER_LIMIT = 90

bot = telebot.TeleBot(BOT_TOKEN)

def prepare_message(status_obj: CurrStatus, av15):
    time_in_status = status_obj.time_in_status_mins
    curr_val = status_obj.current_value
    text_str = f"{curr_val} -> {av15}, Time in Status : {time_in_status} mins"
    return text_str

def send_message(message_text):
    if message_text:
        bot.send_message(chat_id=CHAT_ID, text=message_text)

def value_out_of_range(value):
    if value <= LOWER_LIMIT or value >= UPPER_LIMIT:
        return True
    return False

def run():
    _status = CurrStatus()
    while True:
        try:
            processor = DataProcessor(reports_data_dir=REPORTS_DATA_DIR)
            curr_t, curr_v = processor.get_present_val()
            _status.update(curr_time=curr_t, curr_val=curr_v)
            projected_v = processor.process_data()

            if value_out_of_range(curr_v) or value_out_of_range(projected_v):
                _status.update(curr_time=curr_t, curr_val=curr_v)
                send_message(message_text=prepare_message(_status, projected_v))
            else:
                _status.reset()
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
    
