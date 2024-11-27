import os.path
import warnings
from os import listdir
from os.path import isfile, join

import numpy as np
import pandas as pd

warnings.simplefilter(action='ignore', category=FutureWarning)
DEFAULT_MINS_IN_PAST = 15

class CurrStatus:
    def __init__(self):
        self.time_in_status_mins = 0
        self.status_entry_time = 0
        self.last_value = None
        self.current_value = None

    def update(self, curr_val, curr_time):
        if not self.status_entry_time:
            self.status_entry_time = curr_time
        self.time_in_status_mins = (curr_time - self.status_entry_time).seconds // 60

        self.current_value = curr_val
        self.last_value = self.current_value

    def reset(self):
        self.time_in_status_mins = 0
        self.status_entry_time = 0
        self.last_value = None
        self.current_value = None


class DataProcessor:
    def __init__(self, reports_data_dir):
        self.data_dir = reports_data_dir
        df = pd.DataFrame()
        for index in [0, 1]:
            try:
                curr_filename = sorted([f for f in listdir(self.data_dir) if f.endswith("csv") and isfile(join(self.data_dir, f))], reverse=True)[index]
                curr_df = pd.read_csv(os.path.join(self.data_dir, curr_filename), parse_dates=['timestamp'])
                df = pd.concat([df, curr_df], ignore_index=True)
            except IndexError:
                pass

        unique_merged_df = df.drop_duplicates(subset='timestamp').sort_values(by='timestamp', ascending=False)
        unique_merged_df.set_index('timestamp', inplace=True)
        self.dataframe = unique_merged_df


    def get_projected_val(self, mins_in_future, mins_in_past=DEFAULT_MINS_IN_PAST):
        window_dataframe = get_last(self.dataframe, minutes=mins_in_past)
        y_curr = window_dataframe.iloc[0].value
        y_prev = window_dataframe.iloc[-1].value

        y_next = y_curr + (y_curr - y_prev) * mins_in_future / mins_in_past
        return int(y_next)

    def get_avg_projected_val(self, mins_in_future):
        vals = []
        for mins_in_past in range(5, DEFAULT_MINS_IN_PAST + 1):
            vals.append(
                self.get_projected_val(
                    mins_in_future=mins_in_future,
                    mins_in_past=mins_in_past
                )
            )
        return int(np.mean(vals))

    def get_present_val(self):
        t = self.dataframe.iloc[0].name
        v = self.dataframe.iloc[0].value
        return t, v

    def process_data(self):
        av20 = self.get_avg_projected_val(mins_in_future=20)

        # The below are computed only for logging.
        v0t, v0v = self.get_present_val()
        v20 = self.get_projected_val(mins_in_future=20)
        v30 = self.get_projected_val(mins_in_future=30)
        av30 = self.get_avg_projected_val(mins_in_future=30)
        print(f"{v0t} = {v0v}, V20={v20}/{av20}, V30={v30}/{av30}")

        return av20

def get_last(dataframe, minutes):
    latest_time = dataframe.index.max()
    n_minutes_before_latest = latest_time - pd.Timedelta(minutes=minutes)
    last_n_minutes_df = dataframe[dataframe.index >= n_minutes_before_latest]
    return last_n_minutes_df
