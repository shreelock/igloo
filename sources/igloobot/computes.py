

def get_projected_val(dataframe, mins_in_future, mins_in_past=15):
    window_dataframe = dataframe.last(str(mins_in_past) + 'min')
    y_prev = window_dataframe.iloc[0].value
    y_curr = window_dataframe.iloc[-1].value

    y_next = y_curr + (y_curr - y_prev) * mins_in_future / mins_in_past
    return y_next


def process_data(dataframe):
    v0t = dataframe.iloc[-1].name
    v0v = dataframe.iloc[-1].value
    v15 = get_projected_val(dataframe, mins_in_future=15)
    v30 = get_projected_val(dataframe, mins_in_future=30)

    print(f"{v0t} = {v0v}, P15={v15}, P30={v30}")
