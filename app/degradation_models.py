import math
import time

import numpy as np
import pandas as pd


def wang(current, delta_t, batt_temp):
    ah = current * delta_t / 3600
    c_rate = current / 100  # 100 = Amperios hora totales bateria
    if c_rate > 0:
        b = 448.96 * c_rate ** 2 - 6301.1 * c_rate + 33840
        q_loss = (
            b
            * math.exp((-31700 + (c_rate * 370.3)) / (8.314472 * (batt_temp)))
            * ah ** 0.552
        )
    else:
        q_loss = 0

    print("Wang degradation")
    print(q_loss)
    return q_loss


def add_wang_column(df):
    dates = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S.%f")
    x = np.array(
        [time.mktime(t.timetuple()) for t in dates]
    )  # total seconds since epoch
    df["x1"] = x
    dates2 = df["x1"].iloc[1:]
    dates2 = dates2.append(pd.Series(df["x1"].iloc[-1]), ignore_index=True)
    df["x2"] = dates2

    df["delta_t"] = df["x2"] - df["x1"]
    df["wang_degradation"] = df.apply(
        lambda row: wang(row["current"], row["delta_t"], row["batt_temp"]), axis=1
    )
    df["cumulative_degradation"] = df["wang_degradation"].cumsum()
    del df["x2"], df["x1"]
