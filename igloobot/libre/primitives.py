import os
import time

import pandas as pd

from config.constants import LIBRE_EMAIL, LIBRE_PWD
from libre.libre_api import login, get_patient_connections, get_cgm_data, extract_graph_data
from libre.libre_api import extract_latest_reading

class Reading:
    def __init__(self):
        self.rtime = None
        self.rvalue = None

    def update(self, t, v):
        self.rtime = t
        self.rvalue = v

class LibreToken:
    def __init__(self):
        self.token = login(LIBRE_EMAIL, LIBRE_PWD)
        self.patient_id = get_patient_connections(self.token)['data'][0]["patientId"]
        self.expires = None

    def refresh(self):
        if self.expires and time.time() >= self.expires:
            self.token = login(LIBRE_EMAIL, LIBRE_PWD)

class IglooDataFrame:
    def __init__(self, data_dir):
        self.file = None
        self.object = None
        self.data_dir = data_dir

    def initialize(self, timeobj):
        self.file = os.path.join(self.data_dir, f"{timeobj.strftime('%Y-%m-%d')}.csv")
        if os.path.exists(self.file):
            self.object = pd.read_csv(self.file, index_col='timestamp', parse_dates=True)

    def write_to_disk(self):
        self.object.to_csv(self.file, index=True)
        pass

    def update(self, curr_data, past_data):
        if self.object is None or max(past_data.keys()).day != max(curr_data.keys()).day:
            curr_ts = next(iter(curr_data))  # first key
            self.initialize(curr_ts)

        curr_data.update(past_data)
        curr_data_df = pd.DataFrame(list(curr_data.items()), columns=['timestamp', 'value'])
        curr_data_df.set_index('timestamp', inplace=True)

        self.object = pd.concat([self.object, curr_data_df])
        self.object = self.object[~self.object.index.duplicated()]
        self.object = self.object.sort_values(by='timestamp')

        self.write_to_disk()

class LibreManager:
    def __init__(self, reports_data_dir):
        self.igloo_dataframe: IglooDataFrame = IglooDataFrame(data_dir=reports_data_dir)
        self.libre_token: LibreToken = LibreToken()
        self.current_reading: Reading = Reading()

    def get_full_cgm_response(self):
        self.libre_token.refresh()
        cgm_data = get_cgm_data(token=self.libre_token.token, patient_id=self.libre_token.patient_id)
        self.libre_token.expires = cgm_data['ticket']['expires']
        return cgm_data

    def update_data(self):
        cgm_response = self.get_full_cgm_response()
        latest_reading = extract_latest_reading(cgm_response)

        _curr_time = next(iter(latest_reading))
        _latest_val = latest_reading[_curr_time]
        print(f"{_curr_time}, Current Reading is {_latest_val}")

        self.current_reading.update(
            t=_curr_time,
            v=_latest_val
        )
        self.igloo_dataframe.update(
            curr_data=latest_reading,
            past_data=extract_graph_data(cgm_response)
        )
