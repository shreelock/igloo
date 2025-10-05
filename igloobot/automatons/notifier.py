import datetime
import time
from dataclasses import dataclass, field

import telebot

from config.constants import SELECT_BOT_TOKEN, CHAT_ID, REGULAR_BOT_TOKEN
from config.utils import is_high, is_very_high, is_very_low
from datastore.primitives import SqliteDatabase
from intelligence.primitives import DataProcessor

SECONDS = 1
MINS = 60 * SECONDS
POLL_INTERVAL = 1 * MINS

select_bot = telebot.TeleBot(SELECT_BOT_TOKEN)
regular_bot = telebot.TeleBot(REGULAR_BOT_TOKEN)
clickables = "/menu"


def send_message(message_text, bot_var):
    if message_text:
        bot_var.send_message(chat_id=CHAT_ID, text=message_text)

def high_condition(curr_state):
    return is_high(curr_state.curr_val) and is_very_high(curr_state.proj_val) and curr_state.curr_velo >= 0.8 and curr_state.delta > 0

def low_condition(curr_state):
    return is_very_low(curr_state.proj_val) and curr_state.curr_velo <= 0.8 and curr_state.delta <= 0

def velo_condition(curr_state):
    return abs(curr_state.curr_velo) >= 3.5

@dataclass
class NotifState:
    curr_val: float = field(default=0)
    last_val: float = field(default=0)
    proj_val: float = field(default=0)
    curr_velo: float = field(default=0)

    def __post_init__(self):
        self.delta = self.curr_val - self.last_val

    def str(self):
        return f"{self.curr_val} to {self.proj_val}, Δ{self.delta} : {self.curr_velo:.2f}/min"

    def __str__(self):
        return self.str()

    def cstr(self):
        return f"{self.curr_val} to {self.proj_val}, {self.curr_velo:.2f}/min"

def run():
    prev_state = NotifState()
    sqldb = SqliteDatabase()
    while True:
        try:
            current_time = datetime.datetime.now()
            pr = DataProcessor(sqldb=sqldb, end_datetime=current_time)

            curr_state = NotifState(
                pr.present_reading,
                pr.last_reading,
                pr.projected_reading,
                pr.present_velocity,
            )

            print(curr_state.str())
            if prev_state != curr_state:
                send_message(message_text=f"{curr_state.str()} {clickables}", bot_var=regular_bot)
                if high_condition(curr_state) or low_condition(curr_state) or velo_condition(curr_state):
                    send_message(message_text=curr_state.cstr(), bot_var=select_bot)

            prev_state = curr_state
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
