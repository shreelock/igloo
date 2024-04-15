import os
import time
import datetime

import telebot

from libre.libre_fetch import login, get_patient_connections, get_cgm_data

"""
Following the guide from here : https://www.freecodecamp.org/news/how-to-create-a-telegram-bot-using-python/
"""
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
bot = telebot.TeleBot(BOT_TOKEN)

LIBRE_TOKEN = None
LIBRE_EMAIL = os.environ.get('LIBRE_EMAIL')
LIBRE_PWD = os.environ.get('LIBRE_PWD')
UPPER_LIMIT = 150
LOWER_LIMIT = 80

MINS = 60
POLL_INTERVAL = 5 * MINS


# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

class LibreToken:
    def __init__(self):
        self.token = login(LIBRE_EMAIL, LIBRE_PWD)
        self.patient_id = get_patient_connections(self.token)['data'][0]["patientId"]
        self.expires = None

    def refresh(self):
        if self.expires and time.time() >= self.expires:
            self.token = login(LIBRE_EMAIL, LIBRE_PWD)


class CurrStatus:
    def __init__(self):
        self.time_in_status_mins = 0
        self.status_entry_time = 0
        self.last_value = None
        self.current_value = None

    def update(self, val, input_time):
        if not self.status_entry_time:
            self.status_entry_time = input_time
        self.time_in_status_mins = (input_time - self.status_entry_time).seconds // 60
        self.last_value = self.current_value
        self.current_value = val

    def reset(self):
        self.__init__()

def fetch_latest_reading(libre_token: LibreToken):
    cgm_data = get_cgm_data(token=libre_token.token, patient_id=libre_token.patient_id)
    libre_token.expires = cgm_data['ticket']['expires']
    glucose_value = cgm_data['data']['connection']['glucoseItem']['ValueInMgPerDl']
    return glucose_value


def send_message(message_text):
    bot.send_message(chat_id=CHAT_ID, text=message_text)

def value_out_of_range(value):
    if value <= LOWER_LIMIT or value >= UPPER_LIMIT:
        return True
    return False

def prepare_message(value, status_obj: CurrStatus):
    time_in_status = status_obj.time_in_status_mins
    text_str = f"{value}, Time in Status : {time_in_status} mins"
    return text_str


def get_poll_interval(value):
    if value <= LOWER_LIMIT:
        return 1 * MINS
    elif value >= UPPER_LIMIT:
        return 2 * MINS
    else:
        return 5 * MINS


if __name__ == '__main__':
    _token = LibreToken()
    _status = CurrStatus()
    while True:
        _curr_time = datetime.datetime.now()
        _token.refresh()
        try:
            _latest_val = fetch_latest_reading(_token)
            if value_out_of_range(_latest_val):
                _status.update(_latest_val, _curr_time)
                send_message(message_text=prepare_message(_latest_val, _status))
            else:
                _status.reset()

            POLL_INTERVAL = get_poll_interval(_latest_val)
            print(f"{_curr_time}, Current Reading is {_latest_val}")
            time.sleep(POLL_INTERVAL)


        except Exception as exd:
            send_message(f"Processing failed. Exception = {exd}")
            break
