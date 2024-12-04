import os
import time
from datetime import datetime
from typing import Dict

import pandas as pd

from config.constants import LIBRE_EMAIL, LIBRE_PWD
from libre.libre_api import login, get_patient_connections, get_cgm_data, extract_graph_data
from libre.libre_api import extract_latest_reading


class Reading:
    def __init__(self):
        self.rtime = None
        self.rvalue = None

    def update_reading(self, t, v):
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
        self.csvfile = None
        self.dfobject = None
        self.data_dir = data_dir

    def initialize(self, last_reading_timeobj):
        self.csvfile = os.path.join(self.data_dir, f"{last_reading_timeobj.strftime('%Y-%m-%d')}.csv")
        if os.path.exists(self.csvfile):
            self.dfobject = pd.read_csv(self.csvfile, index_col='timestamp', parse_dates=True)

    def write_to_disk(self):
        self.dfobject.to_csv(self.csvfile, index=True)
        pass

    def dfupdate(self, curr_data: Dict[datetime, int], past_data: Dict[datetime, int]):
        if self.dfobject is None or max(past_data.keys()).day != max(curr_data.keys()).day:
            curr_ts = next(iter(curr_data))  # first key
            self.initialize(curr_ts)

        curr_data.update(past_data)
        curr_data_df = pd.DataFrame(list(curr_data.items()), columns=['timestamp', 'value'])
        curr_data_df.set_index('timestamp', inplace=True)

        self.dfobject = pd.concat([self.dfobject, curr_data_df])
        self.dfobject = self.dfobject[~self.dfobject.index.duplicated()]
        self.dfobject = self.dfobject.sort_values(by='timestamp')

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

        self.current_reading.update_reading(t=_curr_time, v=_latest_val)
        self.igloo_dataframe.dfupdate(
            curr_data=latest_reading,
            past_data=extract_graph_data(cgm_response)
        )
