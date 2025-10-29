import time
from dataclasses import dataclass, field

import telebot
import threading

from config.constants import SELECT_BOT_TOKEN, CHAT_ID, REGULAR_BOT_TOKEN
from config.utils import is_high, is_very_high, is_very_low, get_current_time
from datastore.primitives import SqliteDatabase
from intelligence.plotting_utils import plot_default
from intelligence.primitives import DataProcessor

SECONDS = 1
MINS = 60 * SECONDS
POLL_INTERVAL = 1 * MINS

select_bot = telebot.TeleBot(SELECT_BOT_TOKEN)
regular_bot = telebot.TeleBot(REGULAR_BOT_TOKEN)
clickables = "/menu"


def send_message(message_text, bot_var=regular_bot):
    if message_text:
        bot_var.send_message(chat_id=CHAT_ID, text=message_text)

def send_photo(im_path, bot_var=regular_bot):
    try:
        with open(im_path, 'rb') as photo:
            bot_var.send_photo(chat_id=CHAT_ID, photo=photo)
    except Exception as exc:
        bot_var.send_message(chat_id=CHAT_ID, text=f"Plot cannot be created : {exc}")

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
        del_sign = ""
        if self.delta < 0:
            del_sign = "∇"
        elif self.delta > 0:
            del_sign = "Δ"
        return f"{self.curr_val} to {self.proj_val}, {del_sign}{abs(self.delta)} : {self.curr_velo:.2f}/min"

    def __str__(self):
        return self.str()

    def cstr(self):
        return f"{self.curr_val} to {self.proj_val}, {self.curr_velo:.2f}/min"

def automatic_plot_delivery():
    send_message("Plot Delivery Requested")
    im_path = plot_default()
    send_photo(im_path)

def run():
    prev_state = NotifState()
    sqldb = SqliteDatabase()
    while True:
        try:
            current_time = get_current_time()
            if current_time.minute in [5, 35]:
                threading.Thread(target=automatic_plot_delivery).start()
            pr = DataProcessor(sqldb=sqldb, end_datetime=current_time)

            curr_state = NotifState(
                pr.present_reading,
                pr.last_reading,
                pr.projected_reading,
                pr.present_velocity,
            )

            print(curr_state.str())
            if prev_state != curr_state:
                send_message(message_text=f"{curr_state.str()} {clickables}")
                if high_condition(curr_state) or low_condition(curr_state) or velo_condition(curr_state):
                    send_message(message_text=curr_state.str(), bot_var=select_bot)

            prev_state = curr_state
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
