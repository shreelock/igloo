import time

from config.utils import REPORTS_DATA_DIR
from libre.primitives import LibreManager

MINS = 60
POLL_INTERVAL = 1 * MINS


def run():
    libre_manager = LibreManager(reports_data_dir=REPORTS_DATA_DIR)
    while True:
        try:
            libre_manager.update_data()
            time.sleep(POLL_INTERVAL)
        except Exception as exd:
            print(f"Processing failed. Exception = {exd}")
            raise


if __name__ == '__main__':
    run()
