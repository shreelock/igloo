import time

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

                    data_processor = DataProcessor(sqldb=sqldb, current_time=ts)
                    new_elem.reading_20 = data_processor.projected_reading
                    new_elem.velocity = data_processor.present_velocity

                    sqldb.insert_element(new_elem)
                else:
                    print(f"skipping {ts} to maintain data integrity")
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
