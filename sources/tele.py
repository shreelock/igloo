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
HIGHER_LIMIT = 150

MINS = 60
POLL_INTERVAL = 5*MINS

# @bot.message_handler(func=lambda msg: True)
# def echo_all(message):
#     bot.reply_to(message, message.text)

class LibreToken:
    def __init__(self):
        self.token = login(LIBRE_EMAIL, LIBRE_PWD)
        self.patient_id = get_patient_connections(self.token)['data'][0]["patientId"]
        self.expires = None

    def refresh(self):
        print("Refreshing")
        if self.expires and time.time() >= self.expires:
            self.token = login(LIBRE_EMAIL, LIBRE_PWD)


def fetch_latest_reading(libre_token: LibreToken):
    cgm_data = get_cgm_data(token=libre_token.token, patient_id=libre_token.patient_id)
    libre_token.expires = cgm_data['ticket']['expires']
    glucose_value = cgm_data['data']['connection']['glucoseItem']['ValueInMgPerDl']
    return glucose_value

def send_message(message_text):
    bot.send_message(chat_id=CHAT_ID, text=message_text)


if __name__ == '__main__':
    _token = LibreToken()
    while True:
        _token.refresh()
        try:
            latest_val = fetch_latest_reading(_token)
            if latest_val >= HIGHER_LIMIT:
                send_message(message_text=latest_val)
                POLL_INTERVAL = 2*MINS
            else:
                POLL_INTERVAL = 5*MINS

            print(f"{datetime.datetime.now()}, Current Reading is {latest_val}")
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            send_message(f"Processing failed. Exception = {exd}")
            break
