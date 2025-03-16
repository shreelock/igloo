import time
from dataclasses import dataclass, field
from datetime import datetime
from functools import cached_property
from typing import Dict

from config.constants import LIBRE_EMAIL, LIBRE_PWD
from libre.libre_api import extract_latest_reading
from libre.libre_api import login, get_patient_connections, get_cgm_data, extract_previous_readings


class LibreToken:
    def __init__(self):
        self.token, self.expires = login(LIBRE_EMAIL, LIBRE_PWD)
        self.patient_id = get_patient_connections(self.token)['data'][0]["patientId"]

    def refresh(self):
        if self.expires and time.time() >= self.expires:
            print("Token expired, refreshing.")
            self.token, self.expires = login(LIBRE_EMAIL, LIBRE_PWD)


@dataclass
class LibreManager:
    curr_response: Dict[datetime, int] = field(default_factory=dict)
    prev_response: Dict[datetime, int] = field(default_factory=dict)

    @cached_property
    def libre_token(self) -> LibreToken:
        return LibreToken()

    @property
    def new_readings(self) -> Dict[datetime, int]:
        return {k: v for k, v in self.curr_response.items() if k not in self.prev_response}

    def get_full_cgm_response(self):
        self.libre_token.refresh()
        cgm_data = get_cgm_data(token=self.libre_token.token, patient_id=self.libre_token.patient_id)
        self.libre_token.expires = cgm_data['ticket']['expires']
        return cgm_data

    def update_data_state(self):
        cgm_response = self.get_full_cgm_response()
        latest_reading = extract_latest_reading(cgm_response)
        previous_readings = extract_previous_readings(cgm_response)

        self.prev_response = self.curr_response.copy()

        self.curr_response.clear()
        self.curr_response.update(latest_reading)
        self.curr_response.update(previous_readings)

        _curr_time = next(iter(latest_reading))
        _latest_val = latest_reading[_curr_time]
        print(f"{_curr_time}, Current Reading is {_latest_val}")
