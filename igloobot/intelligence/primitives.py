import warnings
from dataclasses import dataclass, field
from datetime import datetime
from datetime import timedelta
from typing import List, Union, Optional

import numpy as np

from config.utils import is_out_of_range, VAL_CURRENT, TIMESTAMP_FORMAT
from datastore.primitives import SqliteDatabase, IglooDataElement, IglooUpdatesElement, parse_timestamp

warnings.simplefilter(action='ignore', category=FutureWarning)
DEFAULT_MINS_IN_PAST = 15
DEFAULT_MINS_IN_FUTURE = 20
DEFAULT_RECALL_PERIOD_IN_MINS = 60

@dataclass
class CombinedElement:
    timestamp: Union[datetime, str]
    ins_units: int = field(default=0)
    food_note: str = field(default="")
    misc_note: str = field(default="")
    reading_now: int = field(default=0)
    reading_20: int = field(default=0)
    velocity: float = field(default=0.0)
    upd_rowid: int = field(default=0)

    @property
    def timestamp_str(self) -> str:
        return datetime.strftime(self.timestamp, TIMESTAMP_FORMAT)

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse_timestamp(self.timestamp)
        elif isinstance(self.timestamp, datetime):
            self.timestamp = self.timestamp.replace(second=0, microsecond=0)

    def populate(self, data_el: IglooDataElement, update_el: Optional[IglooUpdatesElement]):
        if data_el and update_el:
            assert data_el.timestamp == update_el.timestamp
        if data_el:
            self.timestamp = data_el.timestamp
            self.reading_now = data_el.reading_now
            self.reading_20 = data_el.reading_20
            self.velocity = data_el.velocity
        if update_el:
            self.timestamp = update_el.timestamp
            self.ins_units = update_el.ins_units
            self.food_note = update_el.food_note
            self.misc_note = update_el.misc_note
            self.upd_rowid = update_el.upd_rowid


@dataclass
class DataProcessor:
    sqldb: SqliteDatabase
    end_datetime: datetime
    start_datetime: datetime = None
    # for computing projections
    for_compute_default_mins_in_future: int = DEFAULT_MINS_IN_FUTURE
    for_compute_default_mins_in_past: int = DEFAULT_MINS_IN_PAST

    def __post_init__(self):
        self.start_datetime = self.start_datetime or self.end_datetime - timedelta(minutes=DEFAULT_RECALL_PERIOD_IN_MINS)
        # print(f"Creating DataProcessor from {start_datetime} to {self.data_until}")
        self.data = self.sqldb.main_table.fetch_w_ts_range(ts_start=self.start_datetime, ts_end=self.end_datetime)
        self.updates = self.sqldb.updates_table.fetch_w_ts_range(ts_start=self.start_datetime, ts_end=self.end_datetime)

    @property
    def projected_reading(self):
        return self.get_avg_projected_val_inner(mins_in_future=self.for_compute_default_mins_in_future)

    @property
    def present_reading(self):
        return self.data[0].reading_now

    @property
    def present_timestamp(self):
        return self.data[0].timestamp

    @property
    def present_velocity(self):
        return (self.projected_reading - self.present_reading) / self.for_compute_default_mins_in_future

    def get_combined_data(self, reverse=True) -> List[CombinedElement]:
        data_dict = {element.timestamp: element for element in self.data}
        updates_dict = {element.timestamp: element for element in self.updates}
        combined_elements_list = []
        for ts in set(updates_dict.keys()).union(data_dict.keys()):
            com_el = CombinedElement(timestamp=ts)
            com_el.populate(
                data_el=data_dict.get(ts, None),
                update_el=updates_dict.get(ts, None)
            )
            combined_elements_list.append(com_el)

        sorted_list = sorted(combined_elements_list, key=lambda cel: cel.timestamp, reverse=reverse)
        return sorted_list

    def get_slope_inner(self, mins_in_past):
        window_data = get_last(self.data, minutes=mins_in_past)
        y_curr = window_data[0].reading_now
        y_prev = window_data[-1].reading_now
        return (y_curr - y_prev) / mins_in_past

    def get_projected_val_inner(self, mins_in_future, mins_in_past=for_compute_default_mins_in_past):
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

def get_last(data: List[Union[IglooDataElement, IglooUpdatesElement]], minutes: int) -> List[Union[IglooDataElement, IglooUpdatesElement]]:
    if not data:
        return []
    latest_time = data[0].timestamp
    n_minutes_before_latest = latest_time - timedelta(minutes=minutes)
    last_n_minutes_data = [idel for idel in data if idel.timestamp >= n_minutes_before_latest]
    return last_n_minutes_data
