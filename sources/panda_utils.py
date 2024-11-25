import pandas as pd

def get_rate_of_change(df: pd.DataFrame, mins: int):
    min_str = f"{str(mins)}min"
    _df = df.last(min_str)
    total_change = _df['value'].iloc[-1] - _df['value'].iloc[0]
    return float(total_change / mins)


def compute_slope(status_obj):
    df = status_obj.igloo_dataframe.object
    print(get_rate_of_change(df, 15))
    print(get_rate_of_change(df, 30))
    print(get_rate_of_change(df, 60))
    pass
