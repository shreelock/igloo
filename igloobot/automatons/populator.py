import datetime
import subprocess
import time

from config.utils import TIMESTAMP_FORMAT
from datastore.primitives import SqliteDatabase, IglooDataElement
from intelligence.primitives import DataProcessor
from libre.primitives import LibreManager

MINS = 60
POLL_INTERVAL = 1 * MINS


def run():
    libre_manager = LibreManager()
    sqldb = SqliteDatabase()
    while True:
        try:
            libre_manager.update_data_state()
            new_readings = libre_manager.new_readings
            for ts, val in new_readings.items():
                if not sqldb.if_exists(timestamp=ts):
                    new_elem = IglooDataElement(timestamp=ts, reading_now=val)
                    sqldb.insert_element(new_elem)

                    data_processor = DataProcessor(sqldb=sqldb, data_until=ts)
                    new_elem.reading_20 = data_processor.projected_reading
                    new_elem.velocity = data_processor.present_velocity

                    sqldb.insert_element(new_elem)
                else:
                    print(f"skipping {ts} to maintain data integrity")
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


def insulin_event(start_time: datetime, ins_units: int):
    sqldb = SqliteDatabase()
    for td in range(120):
        appl_ts = start_time + datetime.timedelta(minutes=td)
        if not sqldb.if_exists(appl_ts):
            new_elem = IglooDataElement(timestamp=appl_ts, insulin_units=ins_units)
            sqldb.insert_element(new_elem)
        else:
            existing_elem = sqldb.fetch_w_ts(appl_ts)
            existing_elem.insulin_units += ins_units
            sqldb.insert_element(existing_elem)


def food_event(start_time: datetime, food_note: str):
    sqldb = SqliteDatabase()
    new_elem = IglooDataElement(timestamp=start_time, food=food_note)
    sqldb.insert_element(new_elem)


if __name__ == '__main__':
    sync_command = "scp dietpi@192.168.1.2:/home/dietpi/projects/igloo/datastore/igloo-database.sqlite /Users/sshn/shreelock/igloo/datastore/igloo-database.sqlite"
    subprocess.run(sync_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    insulin_event(datetime.datetime.strptime("2025-03-17 15:55", TIMESTAMP_FORMAT), 6)
    food_event(datetime.datetime.strptime("2025-03-17 15:55", TIMESTAMP_FORMAT), "2-paratha")
    insulin_event(datetime.datetime.strptime("2025-03-17 18:13", TIMESTAMP_FORMAT), 3)
    food_event(datetime.datetime.strptime("2025-03-17 21:02", TIMESTAMP_FORMAT), "sugar15g")
    pass

