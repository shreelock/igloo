import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Sample data
data = {
    'timestamp': [
        '2025-03-07 23:32:00', '2025-03-07 23:31:00', '2025-03-07 23:30:00',
        '2025-03-07 23:29:00', '2025-03-07 23:28:00', '2025-03-07 23:27:00',
        '2025-03-07 23:26:00', '2025-03-07 23:25:00', '2025-03-07 23:24:00',
        '2025-03-07 23:23:00', '2025-03-07 23:22:00', '2025-03-07 23:21:00'
    ],
    'value': [100, 101, 101, 100, 100, 99, 99, 100, 101, 101, 101, 101]
}


event_data = (
    ('2025-03-07 23:24:30', 4),
    ('2025-03-07 23:28:00', 4),
)


# Convert event timestamps to datetime
event_data = [(pd.to_datetime(timestamp), label) for timestamp, label in event_data]

# Create DataFrame
df = pd.DataFrame(data)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Plot
plt.figure(figsize=(10, 6))
plt.plot(df['timestamp'], df['value'], marker='o')

# Format x-axis
plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Format y-axis
plt.gca().yaxis.set_major_locator(plt.MultipleLocator(5))

# Add horizontal dashed lines
plt.axhline(y=80, color='r', linestyle='--', lw=1)
plt.axhline(y=90, color='g', linestyle='--', lw=1)
plt.axhline(y=120, color='b', linestyle='--', lw=1)

# Add light green background between 92 and 108
plt.axhspan(92, 108, color='lightgreen', alpha=0.3)

# Add vertical light red shaded area from 23:24 to 23:30
for event in event_data:
    plt.axvspan(pd.to_datetime(event[0]), pd.to_datetime(event[0]) + pd.Timedelta(minutes=2), color='lightcoral', alpha=0.3)


# Plot vertical lines and annotations
for timestamp, label in event_data:
    plt.axvline(x=timestamp, color='purple', linestyle='--', linewidth=1)
    plt.text(timestamp, 110, f" *{label}", color='purple', rotation=0, verticalalignment='bottom')


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
plt.savefig("output.jpg")
