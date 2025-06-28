import datetime
import sqlite3
import subprocess
import time

from config.utils import TIMESTAMP_FORMAT
from datastore.primitives import SqliteDatabase, IglooDataElement, IglooUpdatesElement
from intelligence.primitives import DataProcessor
from libre.primitives import LibreManager

MINS = 60
POLL_INTERVAL = 1 * MINS


"""
To deal with timezone issues -
we get localtimestamp (from api) and compare it with systemtimestamp (on server)
if the difference is more than 1 hour, then we use systemtimestamp instead to create 
entries in the database. Of course, if the system is being initialized for the first time,
we might see abulk of new entries, in that case we can skip this check.
This logic will only apply in populator. investigator should ideally use systemtimestamp
to fetch values and populate its own table. It will populate its table by querying latest item
from LiveTable and go forth. 

Needs further thought, in case there are more than one values separated by 1 mins but tz diff
"""


def run():
    libre_manager = LibreManager()
    sqldb = SqliteDatabase()
    while True:
        try:
            libre_manager.update_data_state()
            new_readings = libre_manager.new_readings
            for ts, val in new_readings.items():
                new_elem = IglooDataElement(timestamp=ts, reading_now=val)
                try:
                    sqldb.main_table.insert_element(new_elem)

                    data_processor = DataProcessor(sqldb=sqldb, end_datetime=ts)
                    new_elem.reading_20 = data_processor.projected_reading
                    new_elem.velocity = data_processor.present_velocity

                    sqldb.main_table.update_computed_vals(new_elem)
                    print(f"update done.")
                except sqlite3.IntegrityError:
                    print(f"integrity error. skipping update...")
                finally:
                    print(f"--------")

            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


# def insulin_event(start_time: datetime, ins_units: int):
#     sqldb = SqliteDatabase()
#     for td in range(120):
#         appl_ts = start_time + datetime.timedelta(minutes=td)
#         if not sqldb.main_table.if_exists(appl_ts):
#             new_elem = IglooDataElement(timestamp=appl_ts, insulin_units=ins_units)
#             sqldb.main_table.insert_element(new_elem)
#         else:
#             existing_elem = sqldb.main_table_fetch_w_ts(appl_ts)
#             existing_elem.insulin_units += ins_units
#             sqldb.main_table_insert_element(existing_elem)
#
#
# def food_event(start_time: datetime, food_note: str):
#     sqldb = SqliteDatabase()
#     new_elem = IglooDataElement(timestamp=start_time, food=food_note)
#     sqldb.main_table_insert_element(new_elem)


if __name__ == '__main__':
    # sync_command = "scp dietpi@192.168.1.2:/home/dietpi/projects/igloo/datastore/igloo-database.sqlite /Users/sshn/shreelock/igloo/datastore/igloo-database.sqlite"
    # subprocess.run(sync_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    run()
    pass

