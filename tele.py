import os
import time
from datetime import datetime

import pandas as pd
import telebot

from libre.libre_api import login, get_patient_connections, get_cgm_data
from panda_utils import compute_slope

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

DATA_DIR = "data"

MINS = 60
POLL_INTERVAL = 5 * MINS


class LibreToken:
    def __init__(self):
        self.token = login(LIBRE_EMAIL, LIBRE_PWD)
        self.patient_id = get_patient_connections(self.token)['data'][0]["patientId"]
        self.expires = None

    def refresh(self):
        if self.expires and time.time() >= self.expires:
            self.token = login(LIBRE_EMAIL, LIBRE_PWD)

class IglooDataFrame:
    def __init__(self):
        self.file = None
        self.object = None

    def initialize(self, timeobj):
        self.file = os.path.join(DATA_DIR, f"{timeobj.strftime('%Y-%m-%d')}.csv")
        if os.path.exists(self.file):
            self.object = pd.read_csv(self.file, index_col='timestamp', parse_dates=True)

    def write_to_disk(self):
        self.object.to_csv(self.file, index=True)
        pass

    def update(self, curr_data, past_data):
        if self.object is None:
            curr_ts = next(iter(curr_data))  # first key
            self.initialize(curr_ts)

        curr_data.update(past_data)
        curr_data_df = pd.DataFrame(list(curr_data.items()), columns=['timestamp', 'value'])
        curr_data_df.set_index('timestamp', inplace=True)

        self.object = pd.concat([self.object, curr_data_df])
        self.object = self.object[~self.object.index.duplicated()]
        self.object = self.object.sort_values(by='timestamp')

        # finally
        print("written to disk")
        self.write_to_disk()

class CurrStatus:
    def __init__(self):
        self.time_in_status_mins = 0
        self.status_entry_time = 0
        self.last_value = None
        self.current_value = None
        self.igloo_dataframe = IglooDataFrame()

    def update(self, _curr_data=None, _past_data=None):
        curr_time = next(iter(_curr_data))
        if not self.status_entry_time:
            self.status_entry_time = curr_time
        self.time_in_status_mins = (curr_time - self.status_entry_time).seconds // 60

        self.last_value = self.current_value
        self.current_value = _curr_data[curr_time]

        self.igloo_dataframe.update(_curr_data, _past_data)

    def reset(self):
        self.time_in_status_mins = 0
        self.status_entry_time = 0
        self.last_value = None
        self.current_value = None

def fetch_latest_reading(libre_token: LibreToken):
    cgm_data = get_cgm_data(token=libre_token.token, patient_id=libre_token.patient_id)
    libre_token.expires = cgm_data['ticket']['expires']
    glucose_value = cgm_data['data']['connection']['glucoseItem']['ValueInMgPerDl']
    return glucose_value

def get_full_cgm_data(libre_token: LibreToken):
    cgm_data = get_cgm_data(token=libre_token.token, patient_id=libre_token.patient_id)
    libre_token.expires = cgm_data['ticket']['expires']
    return cgm_data

def extract_graph_data(_response):
    all_data = _response['data']['graphData']
    _graphdata_map = {}
    for item in all_data:
        ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
        val = item['ValueInMgPerDl']
        _graphdata_map[ts] = val
    return _graphdata_map

def extract_latest_reading(_response):
    item = _response['data']['connection']['glucoseItem']
    ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
    val = item['ValueInMgPerDl']
    return {ts: val}

def send_message(message_text):
    if message_text:
        bot.send_message(chat_id=CHAT_ID, text=message_text)

def value_out_of_range(value):
    if value <= LOWER_LIMIT or value >= UPPER_LIMIT:
        return True
    return False

def prepare_message(status_obj: CurrStatus):
    time_in_status = status_obj.time_in_status_mins
    curr_val = status_obj.current_value
    text_str = f"{curr_val}, Time in Status : {time_in_status} mins"
    compute_slope(status_obj)
    return text_str


def get_poll_interval(value):
    return 2 * MINS


if __name__ == '__main__':
    _token = LibreToken()
    _status = CurrStatus()
    while True:
        _token.refresh()
        try:
            cgm_response = get_full_cgm_data(_token)
            _last_reading = extract_latest_reading(cgm_response)
            _graph_data = extract_graph_data(cgm_response)

            _curr_time = next(iter(_last_reading))
            _latest_val = _last_reading[_curr_time]
            print(f"{_curr_time}, Current Reading is {_latest_val}")

            # if value_out_of_range(_latest_val):
            _status.update(_last_reading, _graph_data)
            send_message(message_text=prepare_message(_status))
            # else:
            #     _status.reset()

            POLL_INTERVAL = get_poll_interval(_latest_val)
            time.sleep(POLL_INTERVAL)


        except Exception as exd:
            send_message(f"Processing failed. Exception = {exd}")
            raise
