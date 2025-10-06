import os
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import List

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from datastore.primitives import SqliteDatabase
from intelligence.primitives import DataProcessor

matplotlib.use('agg')

HOUR = 60
DEFAULT_FOOD_SEARCH_WINDOW_HRS = 4
@dataclass
class YLim:
    min: int = -30
    max: int = 400

@dataclass
class UpdatesRowIdentifier:
    timestamp: datetime
    row_id: int


@dataclass
class PlotConfig:
    bef_duration_min: int = 120
    aft_duration_min: int = 20


FOOD_PLOT_CONFIG = PlotConfig(bef_duration_min=int(0.5 * HOUR), aft_duration_min=4 * HOUR)


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
    axes.text(x=event_ts, y=YLim.min, s=datetime.strftime(event_ts, '%H:%M'),
              color='purple', va="bottom", ha="right", fontsize=5, rotation=90)


def sanitize(ds, ts):
    zero_indices = ds[ds == 0].index
    ds = ds.drop(zero_indices)
    ts = ts.drop(zero_indices)
    return ds, ts


def plot_text_events(axes, ts_series, data_series, y_height=60):
    for idx, val in enumerate(data_series):
        ts = ts_series[idx]
        if val:
            add_vline(axes, xpt=ts)
            axes.text(x=ts, y=y_height, s=val, color='purple', fontsize=6, va="bottom", ha="right", rotation=90)
            add_timestamp_xtick(axes, ts)


def plot_series(axes, ts_series, data_series, marker='o', markersize=0.35, linewidth=0.25, color='g', zeros_ok=False,
                show_last_text=True):
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
            axes.text(x=event_ts, y=event_val * scale, s=f"{int(event_val)}u",
                      color='purple', va="top", ha="right", fontsize=5, rotation=45)
            if idx:  # to avoid adding line at first element
                add_vline(axes, xpt=event_ts)
                add_timestamp_xtick(axes, event_ts)
        elif (event_val == 0 and event_val != prev_val) or idx == len(data_series) - 1:
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
    axes.set_ylim(YLim.min, YLim.max)
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
    df_dtp_raw = pd.DataFrame([vars(obj) for obj in data_to_plot])
    df_dtp_raw['timestamp'] = pd.to_datetime(df_dtp_raw['timestamp'])
    df_dtp_raw = df_dtp_raw.sort_values(by='timestamp', ascending=False)

    df_dtp = df_dtp_raw  # remove_empty_from_df(df_dtp_raw)

    # Plot
    figure, ax = create_figure()
    decorate_axes(ax)
    annotate_plot(ax)

    # plot current reading and velocity
    plot_series(ax, df_dtp['timestamp'], df_dtp['reading_now'])
    plot_series(ax, df_dtp['timestamp'], df_dtp['velocity'] * 10, show_last_text=False)

    # create a future df with values from 20 minutes
    future_df = create_future_df(df_dtp)

    # to display timestamp of last value of future_df
    max_ts_w_value = remove_empty_from_df(df_dtp)['timestamp'].max()
    ax.axvspan(max_ts_w_value, future_df['timestamp'].max(),
               facecolor='none', edgecolor='k', hatch='\\\\', alpha=0.05, zorder=99.1)

    # plot future_df
    plot_series(ax, future_df['timestamp'], future_df['reading_now'], color='r')

    INS_CARB_SCALE = 14
    # IRL is (50), However, having it plot like that does not add value. Let's change to 14;
    # Assuming maximum ins input at a time of 25 we get scale of 350, which also corresponds to ins range.
    plot_fill_series(ax, df_dtp['timestamp'], df_dtp['ins_units'], scale=INS_CARB_SCALE, color='r', alpha=0.25)

    plot_text_events(ax, df_dtp['timestamp'], df_dtp['food_note'], y_height=120)

    plot_text_events(ax, df_dtp['timestamp'], df_dtp['misc_note'])

    figure.tight_layout()
    plt_filepath = os.path.join(os.getcwd(), "output.jpg")
    figure.savefig(plt_filepath, dpi=500)
    return plt_filepath


def _plot(request_time: datetime, plot_config: PlotConfig = PlotConfig()) -> str:
    # mins_in_future is needed for events in ahead_mins
    # mins_in_past is needed to set lookback duration

    sqldb = SqliteDatabase()
    _processor = DataProcessor(
        sqldb=sqldb,
        end_datetime=request_time + timedelta(minutes=plot_config.aft_duration_min),
        start_datetime=request_time - timedelta(minutes=plot_config.bef_duration_min)
    )
    if not _processor.data:
        print("no data in requested time range")
        return None

    data_to_plot = _processor.get_combined_data()
    return create_plot(data_to_plot=data_to_plot)


def search_food_str(
        request_time: datetime = datetime.now(),
        food_item_to_search: str = None,
        food_search_window_hrs: int = None
) -> List[UpdatesRowIdentifier]:
    sqldb = SqliteDatabase()
    food_search_window_hrs = food_search_window_hrs or DEFAULT_FOOD_SEARCH_WINDOW_HRS
    start_time = request_time - timedelta(hours=food_search_window_hrs)
    _processor = DataProcessor(sqldb=sqldb, end_datetime=request_time, start_datetime=start_time)
    combined_data = _processor.get_combined_data()

    _results: List[UpdatesRowIdentifier] = []
    for comb_el in combined_data:
        if comb_el.food_note and (not food_item_to_search or food_item_to_search in comb_el.food_note):
            print(f"Found food {comb_el.food_note} at {comb_el.timestamp}")
            row_iden = UpdatesRowIdentifier(
                timestamp=comb_el.timestamp,
                row_id=comb_el.upd_rowid
            )
            _results.append(row_iden)
    print(_results or f"Did not find food {food_item_to_search or ''}")
    return _results

def plot_default():
    return _plot(request_time=datetime.now())


def plot_specific(request_id: int = None, event_time: datetime = None, plot_config: PlotConfig = PlotConfig()):
    assert (request_id is None) != (event_time is None)

    sqldb = SqliteDatabase()
    if request_id is not None:
        updates_row = sqldb.updates_table.fetch_w_rowid(rowid=request_id)
    else:
        updates_row = sqldb.updates_table.fetch_w_ts(timestamp=event_time)
    return _plot(
        request_time=updates_row.timestamp,
        plot_config=plot_config
    )


if __name__ == '__main__':
    # food_events = search_food_str(food_item_to_search="bread", food_search_window_hrs=8)
    # if food_events and len(food_events) == 1:
    #     plot_specific(event_time=food_events[0].timestamp, plot_config=FOOD_PLOT_CONFIG)

    plot_default()
