import warnings
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import List

import numpy as np

from config.utils import is_out_of_range, VAL_CURRENT
from datastore.primitives import SqliteDatabase, IglooDataElement

warnings.simplefilter(action='ignore', category=FutureWarning)
DEFAULT_MINS_IN_PAST = 15
DEFAULT_MINS_IN_FUTURE = 20
DEFAULT_HISTORY_MINS = 60


@dataclass
class DataProcessor:
    sqldb: SqliteDatabase
    data_until: datetime
    history_mins: int = DEFAULT_HISTORY_MINS
    default_mins_in_future: int = DEFAULT_MINS_IN_FUTURE
    default_mins_in_past: int = DEFAULT_MINS_IN_PAST

    def __post_init__(self):
        some_time_ago_from_now = self.data_until - timedelta(minutes=self.history_mins)
        print(f"Creating DataProcessor from {some_time_ago_from_now} to {self.data_until}")
        self.data = self.sqldb.fetch_w_ts_range(ts_start=some_time_ago_from_now, ts_end=self.data_until)

    @property
    def projected_reading(self):
        return self.get_avg_projected_val_inner(mins_in_future=self.default_mins_in_future)

    @property
    def present_reading(self):
        return self.data[0].reading_now

    @property
    def present_timestamp(self):
        return self.data[0].timestamp

    @property
    def present_velocity(self):
        return (self.projected_reading - self.present_reading) / self.default_mins_in_future

    def get_slope_inner(self, mins_in_past):
        window_data = get_last(self.data, minutes=mins_in_past)
        y_curr = window_data[0].reading_now
        y_prev = window_data[-1].reading_now
        return (y_curr - y_prev) / mins_in_past

    def get_projected_val_inner(self, mins_in_future, mins_in_past=default_mins_in_past):
        slope = self.get_slope_inner(mins_in_past=mins_in_past)
        y_curr = self.data[0].reading_now
        y_next = y_curr + slope * mins_in_future
        return int(y_next)

    def get_avg_projected_val_inner(self, mins_in_future):
        vals = []
        for mins_in_past in range(5, DEFAULT_MINS_IN_PAST + 1):
            vals.append(
                self.get_projected_val_inner(
                    mins_in_future=mins_in_future,
                    mins_in_past=mins_in_past
                )
            )
        return int(np.mean(vals))

    def log_projections(self):
        v0t, v0v = self.present_timestamp, self.present_reading

        v20 = self.get_projected_val_inner(mins_in_future=20)
        av20 = self.get_avg_projected_val_inner(mins_in_future=20)

        v30 = self.get_projected_val_inner(mins_in_future=30)
        av30 = self.get_avg_projected_val_inner(mins_in_future=30)
        print(f"{v0t} = {v0v}, V20={v20}/{av20}, V30={v30}/{av30}")

    def get_time_out_of_range(self):
        time_oor = 0
        curr_t = self.present_timestamp
        curr_val = self.present_reading
        if is_out_of_range(curr_val, value_type=VAL_CURRENT):
            for idel in self.data:
                if is_out_of_range(idel.reading_now, value_type=VAL_CURRENT):
                    continue
                else:
                    time_oor = (curr_t - idel.timestamp).seconds // 60
                    break
        return time_oor


def get_last(data: List[IglooDataElement], minutes: int) -> List[IglooDataElement]:
    latest_time = data[0].timestamp
    n_minutes_before_latest = latest_time - timedelta(minutes=minutes)
    last_n_minutes_data = [idel for idel in data if idel.timestamp >= n_minutes_before_latest]
    return last_n_minutes_data
