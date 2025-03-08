import pandas as pd

from config.utils import REPORTS_DATA_DIR
from intelligence.primitives import DataProcessor, get_last
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


if __name__ == '__main__':
    processor = DataProcessor(reports_data_dir=REPORTS_DATA_DIR)
    last_df = get_last(processor.dataframe, minutes=60)
    last_df = last_df.reset_index()
    event_data = (
        # ('2025-03-07 23:24:30', 4),
        # ('2025-03-07 23:28:00', 4),
    )

    # Convert event timestamps to datetime
    event_data = [(pd.to_datetime(timestamp), label) for timestamp, label in event_data]

    # Convert timestamp to datetime
    last_df['timestamp'] = pd.to_datetime(last_df['timestamp'])

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(last_df['timestamp'], last_df['value'], marker='o', markersize=2, linewidth=0.5)
    # plt.xlim(last_df['timestamp'].min(), last_df['timestamp'].max())

    # Format x-axis
    plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Format y-axis
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(20))

    plot_down = 55
    plt.axhline(y=plot_down, color='r', linestyle='--', lw=1)
    # Add horizontal dashed lines
    range_low = 75
    plt.axhline(y=range_low, color='r', linestyle='--', lw=1)
    range_high = 150
    plt.axhline(y=range_high, color='b', linestyle='--', lw=1)
    plot_up = 250
    plt.axhline(y=plot_up, color='r', linestyle='--', lw=1)

    # Add light green background between 92 and 108
    plt.axhspan(range_low, range_high, color='lightgreen', alpha=0.3)

    # Add vertical light red shaded area from 23:24 to 23:30
    for event in event_data:
        plt.axvspan(pd.to_datetime(event[0]), pd.to_datetime(event[0]) + pd.Timedelta(minutes=2), color='lightcoral',
                    alpha=0.3)

    # Plot vertical lines and annotations
    for timestamp, label in event_data:
        plt.axvline(x=timestamp, color='purple', linestyle='--', linewidth=1)
        plt.text(timestamp, 110, f" *{label}", color='purple', rotation=0, verticalalignment='bottom')

    last_timestamp = last_df['timestamp'].max()
    last_value = last_df.loc[last_df['timestamp'] == last_timestamp, 'value'].values[0]
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
    plt.savefig("output.jpg", dpi=350)
