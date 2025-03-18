import os
from datetime import datetime
from datetime import timedelta

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from datastore.primitives import SqliteDatabase
from intelligence.primitives import DataProcessor, get_last

matplotlib.use('agg')


def create_figure():
    figure = plt.figure(figsize=(10, 6))
    ax = figure.add_subplot(111)
    return figure, ax

def remove_empty_from_df(input_df):
    zero_indices = input_df[input_df['reading_now'] == 0].index
    ret_df = input_df.drop(zero_indices)
    ret_df = ret_df.reset_index(drop=True)
    return ret_df

def create_future_df(df_to_plot, last_n=5):
    sanitized_df = remove_empty_from_df(df_to_plot)
    new_df = sanitized_df[:last_n]
    new_df.loc[:, 'timestamp'] = new_df['timestamp'] + pd.Timedelta(minutes=20)
    new_df.loc[:, 'reading_now'] = new_df['reading_20']
    return new_df


def add_timestamp_xtick(axes, event_ts):
    axes.text(x=event_ts, y=30, s=datetime.strftime(event_ts, '%H:%M'),
              color='purple', va="bottom", ha="right", fontsize=5, rotation=90)

def sanitize(ds, ts):
    zero_indices = ds[ds == 0].index
    ds = ds.drop(zero_indices)
    ts = ts.drop(zero_indices)
    return ds, ts

def plot_text_events(axes, ts_series, data_series):
    for idx, val in enumerate(data_series):
        ts = ts_series[idx]
        if val:
            add_vline(axes, xpt=ts)
            axes.text(x=ts, y=60, s=val, color='purple', fontsize=6, va="bottom", ha="right", rotation=90)
            add_timestamp_xtick(axes, ts)


def plot_series(axes, ts_series, data_series, marker='o', markersize=2, linewidth=0.5, color='g', zeros_ok=False, show_last_text=True):
    if not zeros_ok:
        data_series, ts_series = sanitize(data_series, ts_series)
    axes.plot(ts_series, data_series, marker=marker, markersize=markersize, linewidth=linewidth, color=color)

    last_ts = ts_series.max()
    last_value = data_series.loc[ts_series == last_ts].values[0]

    if show_last_text:
        axes.text(last_ts, last_value, int(last_value), color='purple')


def plot_fill_series(axes, ts_series, data_series, scale, color='#ffeff8', alpha=0.99):
    axes.fill_between(ts_series, data_series * scale, color=color, alpha=alpha)
    prev_val = 0

    data_series = data_series[::-1].reset_index(drop=True)
    ts_series = ts_series[::-1].reset_index(drop=True)
    for idx, _ in enumerate(data_series):
        event_idx = idx
        event_ts = ts_series[event_idx]
        event_val = data_series[event_idx]
        if event_val > 0 and event_val != prev_val:
            axes.text(x=event_ts, y=event_val * scale, s=f"{int(event_val)} units",
                      color='purple', va="top", ha="right",  fontsize=5, rotation=90)
            if idx:  # to avoid adding line at first element
                add_vline(axes, xpt=event_ts)
                add_timestamp_xtick(axes, event_ts)
        elif (event_val == 0 and event_val != prev_val) or idx == len(data_series)-1:
            # insulin ended
            add_vline(axes, xpt=event_ts)
            add_timestamp_xtick(axes, event_ts)
        prev_val = event_val


def decorate_axes(axes):
    axes.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
    axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    # Format y-axis
    axes.yaxis.set_major_locator(plt.MultipleLocator(20))

    axes.grid(which='major', color='grey', linestyle=':', linewidth=0.05)

    # Rotate date labels for better readability
    axes.tick_params(axis='x', rotation=45)

    # Add labels and title
    axes.set_xlabel('time')
    axes.set_ylabel('readings')
    # axes.set_title('')


def add_vline(axes, xpt, ypt=None, text="", color='g', linestyle='--', lw=0.6):
    axes.axvline(xpt, color=color, linestyle=linestyle, lw=lw)


def add_hline(axes, ypt, color='r', linestyle='--', lw=0.6):
    axes.axhline(ypt, color=color, linestyle=linestyle, lw=lw)


def annotate_plot(axes):
    plot_down = 55
    plot_up = 225
    add_hline(axes, plot_up)
    add_hline(axes, plot_down)
    add_hline(axes, 0, linestyle='-', lw=0.5)

    range_low = 75
    range_high = 145
    axes.axhspan(range_low, range_high, color='lightgreen', alpha=0.3, zorder=99)

    axes.axhspan(-10.0, 10.0, color='lightgreen', alpha=0.3, zorder=99)

def create_plot(data_to_plot):
    df_dtp = pd.DataFrame([vars(obj) for obj in data_to_plot])
    df_dtp['timestamp'] = pd.to_datetime(df_dtp['timestamp'])

    # Plot
    figure, ax = create_figure()
    decorate_axes(ax)
    annotate_plot(ax)
    plot_series(ax, df_dtp['timestamp'], df_dtp['reading_now'])
    plot_series(ax, df_dtp['timestamp'], df_dtp['velocity'] * 10, show_last_text=False)

    # plot_series(ax, df_dtp['timestamp'], df_dtp['insulin_units']*50, marker='')
    ax.fill_between(df_dtp['timestamp'], df_dtp['insulin_units'] * 50)

    future_df = create_future_df(df_dtp)
    max_ts_w_value = remove_empty_from_df(df_dtp)['timestamp'].max()
    ax.axvspan(max_ts_w_value, future_df['timestamp'].max(),
               facecolor='none', edgecolor='k', hatch='\\\\', alpha=0.05, zorder=99.1)

    plot_series(ax, future_df['timestamp'], future_df['reading_now'], color='r')
    plot_fill_series(ax, df_dtp['timestamp'], df_dtp['insulin_units'], scale=50)

    plot_text_events(ax, df_dtp['timestamp'], df_dtp['food'])

    # Show plot
    figure.tight_layout()
    # plt.show()
    plt_filepath = os.path.join(os.getcwd(), "output.jpg")
    figure.savefig(plt_filepath, dpi=500)
    return plt_filepath

def plot_data():
    sqldb = SqliteDatabase()
    ahead_mins = 60
    behind_mins = 60
    processor = DataProcessor(sqldb=sqldb, data_until=datetime.now() + timedelta(minutes=ahead_mins), history_mins=360)

    data_to_plot = get_last(processor.data, minutes=ahead_mins + behind_mins)
    return create_plot(data_to_plot)


def food_plot():
    sqldb = SqliteDatabase()
    request_time = datetime.now()
    can_lookup_until_these_mins_ago = 360
    processor = DataProcessor(sqldb=sqldb, data_until=datetime.now(), history_mins=can_lookup_until_these_mins_ago)
    for idel in processor.data:
        if idel.food:
            request_time = idel.timestamp
            break

    pre_food_history = 60
    food_footprint_mins = 300
    processor = DataProcessor(sqldb, data_until=request_time + timedelta(minutes=food_footprint_mins), history_mins=food_footprint_mins + pre_food_history)
    return create_plot(data_to_plot=processor.data)


if __name__ == '__main__':
    # plot_data()
    # food_plot()
    pass
