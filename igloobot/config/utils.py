import os

import numpy as np

REPORTS_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../reports")
os.makedirs(REPORTS_DATA_DIR, exist_ok=True)

VAL_PROJECTED = "Projected"
VAL_CURRENT = "Current"

VL_RANGE = np.arange(-120, 70, 0.5)
L_RANGE = np.arange(70, 90, 0.5)
IN_RANGE = np.arange(90, 150, 0.5)
H_RANGE = np.arange(150, 200, 0.5)
VH_RANGE = np.arange(200, 500, 0.5)

GLU_RANGES = {
    1: VL_RANGE,
    2: L_RANGE,
    3: IN_RANGE,
    4: H_RANGE,
    5: VH_RANGE
}


def get_glu_range_id(value: int):
    for k, v in GLU_RANGES.items():
        if value in v:
            return k

def is_out_of_range(value: int, value_type: str):
    if value_type == VAL_PROJECTED:
        return value not in np.hstack((L_RANGE, IN_RANGE, H_RANGE))
    else:
        return value not in IN_RANGE
