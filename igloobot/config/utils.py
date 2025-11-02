import os

import numpy as np
import datetime
from config.constants import CURR_TIMEZONE


DS_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../datastore")
os.makedirs(DS_DATA_DIR, exist_ok=True)
DS_FILE_NAME = "igloo-database.sqlite"
IDATA_TABLE_NAME = "igloo_data"
UPDATES_DATA_TABLE = "igloo_updates_data"

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"

VAL_PROJECTED = "Projected"
VAL_CURRENT = "Current"

VL_RANGE = np.arange(-120, 70)
L_RANGE = np.arange(70, 90)
IN_RANGE = np.arange(90, 150)
H_RANGE = np.arange(150, 200)
VH_RANGE = np.arange(200, 500)

GLU_RANGES = {
    1: VL_RANGE,
    2: L_RANGE,
    3: IN_RANGE,
    4: H_RANGE,
    5: VH_RANGE
}

TIMEZONE_DIFF_MAP = {
    "INDIA": datetime.timezone(datetime.timedelta(hours=5, minutes=30)),
    "SEATTLE_PDT": datetime.timezone(datetime.timedelta(hours=-7, minutes=00)),
    "SEATTLE_PST": datetime.timezone(datetime.timedelta(hours=-8, minutes=00)),
}

def get_current_time():
    tz_diff = TIMEZONE_DIFF_MAP.get(CURR_TIMEZONE, "SEATTLE_PDT")
    current_time = datetime.datetime.now(tz_diff)
    return current_time

def get_glu_range_id(value: int):
    for k, v in GLU_RANGES.items():
        if value in v:
            return k


def is_out_of_range(value: int, value_type: str):
    if value_type == VAL_PROJECTED:
        return value not in np.hstack((L_RANGE, IN_RANGE, H_RANGE))
    else:
        return value not in IN_RANGE


def is_high(value: int):
    return value in H_RANGE or value in VH_RANGE

def is_very_high(value: int):
    return value in VH_RANGE


def is_low(value: int):
    return value in L_RANGE

def is_very_low(value: int):
    return value in VL_RANGE
