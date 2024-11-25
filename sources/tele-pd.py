# This script now includes sorting the DataFrame by timestamp after each data insertion and dropping duplicates before
# writing the data to the CSV file. This ensures that the data is sorted and deduplicated at each iteration. Adjust the
# data generation interval and directory path as needed.
from datetime import datetime

import pandas as pd
import time

from libre.libre_fetch import login, get_patient_connections, get_cgm_data
from tele import LibreToken, CurrStatus, get_full_cgm_data

# Directory to save the CSV files
csv_dir = 'data/'

def generate_data():
    # Generate timestamp
    timestamp = pd.Timestamp.now()
    # Generate random value (replace this with your actual data generation logic)
    value = 10  # Example random value
    return timestamp, value

def process_data(df):
    # Get values from the last five minutes
    last_five_minutes = df.last('5min')

    # Calculate the average of values from the last n minutes
    n_minutes = 3
    last_n_minutes = df.last(str(n_minutes)+'min')
    average_value = last_n_minutes['value'].mean()

    print("Values from the last five minutes:")
    print(last_five_minutes)
    print("\nAverage of values from the last", n_minutes, "minutes:", average_value)

def extract_graph_data(_response):
    all_data = _response['data']['graphData']
    _graphdata_map = {}
    for item in all_data:
        ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
        val = item['ValueInMgPerDl']
        _graphdata_map[ts] = val
    return _graphdata_map

def extract_latest_reading(_response):
    item = _response['data']['connection']['glucoseItem']
    ts = datetime.strptime(item['Timestamp'], '%m/%d/%Y %I:%M:%S %p')
    val = item['ValueInMgPerDl']
    return { ts: val }

def fello():
    while True:
        # Generate data
        timestamp, value = generate_data()

        # Create DataFrame with the new data
        new_data = pd.DataFrame([(timestamp, value)], columns=['timestamp', 'value'])

        # Generate filename based on date
        csv_file = csv_dir + timestamp.strftime('%Y-%m-%d') + '.csv'

        # Check if CSV file exists
        try:
            # Read existing data from CSV file
            existing_data = pd.read_csv(csv_file, parse_dates=['timestamp'])
            # Concatenate existing data with new data
            updated_data = pd.concat([existing_data, new_data], ignore_index=True)
        except FileNotFoundError:
            # If file does not exist, just use the new data
            updated_data = new_data

        # Drop duplicates
        updated_data = updated_data.drop_duplicates()

        # Sort DataFrame by timestamp
        updated_data = updated_data.sort_values(by='timestamp')

        # Write updated data to CSV file
        updated_data.to_csv(csv_file, index=False)

        # Process the data
        process_data(updated_data)

        # Sleep for 2 minutes (adjust this based on your actual data generation interval)
        time.sleep(120)  # 120 seconds = 2 minutes


def update_on_disk(_graph_data=None, _curr_val=None):
    pass


if __name__ == '__main__':
    _token = LibreToken()
    _status = CurrStatus()
    while True:
        _curr_time = datetime.now()
        _token.refresh()
        try:
            _latest_response = get_full_cgm_data(libre_token=_token)
            print(_latest_response)
        finally:
            pass

