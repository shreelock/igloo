import os
from datetime import datetime

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from datastore.primitives import SqliteDatabase
from intelligence.primitives import DataProcessor, get_last

matplotlib.use('agg')


def plot_data():
    sqldb = SqliteDatabase()
    processor = DataProcessor(sqldb=sqldb, current_time=datetime.now(), history_mins=480)

    last_data = get_last(processor.data, minutes=60)
    last_df = pd.DataFrame([vars(obj) for obj in last_data])
    last_df.set_index(keys='timestamp')

    event_data = (
        # ('2025-03-09 13:22:00', 4),
        # ('2025-03-09 13:36:00', 4),
    )

    # Convert event timestamps to datetime
    event_data = [(pd.to_datetime(timestamp), label) for timestamp, label in event_data]

    # Convert timestamp to datetime
    last_df['timestamp'] = pd.to_datetime(last_df['timestamp'])

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(last_df['timestamp'], last_df['reading_now'], marker='o', markersize=2, linewidth=0.5)
    # plt.axvline(x=last_df['timestamp'].max(), color='purple', linestyle='--', linewidth=0.35)

    plt.plot(last_df['timestamp'], last_df['velocity']*10, marker='+', markersize=2, linewidth=0.5, color='g')
    plt.axhspan(-10.0, 10.0, color='lightgreen', alpha=0.3)

    future_df = pd.DataFrame()  # last_df.head(1)
    last_n = 5
    # we create a new dataframe with following values
    # curr_ts
    # curr_ts-last_n + 20
    # ...
    # curr_ts-3 + 20
    # curr_ts-2 + 20
    # curr_ts-1 + 20
    # curr_ts + 20
    for idx in range(last_n, -1, -1):
        new_row = pd.DataFrame(
            {
                'timestamp': [last_df.loc[idx, 'timestamp'] + pd.Timedelta(minutes=20)],
                'reading_now': [last_df.loc[idx, 'reading_20']]
            }
        )
        future_df = pd.concat([future_df, new_row], ignore_index=True)

    last_ts = future_df['timestamp'].max()
    last_val = int(future_df.loc[future_df['timestamp'] == last_ts, 'reading_now'])
    plt.text(x=last_ts, y=last_val, s=str(last_val), color='red')
    plt.plot(future_df['timestamp'], future_df['reading_now'], marker='o', markersize=2, linewidth=0.5, color='r')

    # Format x-axis
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Format y-axis
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(20))

    plot_down = 55
    plt.axhline(y=plot_down, color='r', linestyle='--', lw=0.6)
    # Add horizontal dashed lines
    range_low = 75
    # plt.axhline(y=range_low, color='r', linestyle='--', lw=1)
    range_high = 150
    # plt.axhline(y=range_high, color='b', linestyle='--', lw=1)
    plot_up = 225
    plt.axhline(y=plot_up, color='r', linestyle='--', lw=1)

    plt.axhline(y=0, color='r', linestyle='-', lw=0.5)

    # Add light green background between 92 and 108
    plt.axhspan(range_low, range_high, color='lightgreen', alpha=0.3)

    # Add vertical light red shaded area from 23:24 to 23:30
    for event in event_data:
        plt.axvspan(pd.to_datetime(event[0]), pd.to_datetime(event[0]) + pd.Timedelta(hours=2), color='lightcoral',
                    alpha=0.3)

    # Plot vertical lines and annotations
    for timestamp, label in event_data:
        plt.axvline(x=timestamp, color='purple', linestyle='--', linewidth=1)
        plt.text(timestamp, 110, f" *{label}", color='purple', rotation=0, verticalalignment='bottom')

    # number the last event
    last_timestamp = last_df['timestamp'].max()
    last_value = last_df.loc[last_df['timestamp'] == last_timestamp, 'reading_now'].values[0]
    plt.text(last_timestamp, last_value, last_value, color='purple')

    plt.gca().grid(which='major', color='grey', linestyle='--', linewidth=0.5)

    # Rotate date labels for better readability
    plt.xticks(rotation=45)

    # Add labels and title
    plt.xlabel('Timestamp')
    plt.ylabel('Value')
    plt.title('Timestamp vs Value')

    # Show plot
    plt.tight_layout()
    # plt.show()
    plt_filepath = os.path.join(os.getcwd(), "output.jpg")
    plt.savefig(plt_filepath, dpi=500)
    return plt_filepath


if __name__ == '__main__':
    plot_data()
