import numpy as np
from scipy import integrate
from scipy.stats import skew
import pandas as pd


def gen_traces(df):
    try:
        df.drop(columns="Unnamed: 0", inplace=True)
        df.drop(columns="id", inplace=True)
    except KeyError:
        pass
    trace_id = 1
    aux_trace_id = -1
    trace_array = np.array([])
    suma = 0
    old_name = ""

    for _, row in df.iterrows():
        suma = suma + row["run"]
        trace_array = np.append(trace_array, aux_trace_id)
        nan = row["name"] != row["name"]

        # Si recorre mas de 300 metros - cambiele el id del segmento actual de aux a definitivo para que se tenga en cuenta
        if suma >= 1200:  # 800
            trace_array = np.where(trace_array == aux_trace_id, trace_id, trace_array)

        # Si cambia de vía - empiece un nuevo tramo se escoge 1200 para ver cambios en consumo
        if (
            suma >= 1200
            or (old_name != row["name"] and not nan)
            or row["operative_state"] == 3
        ):
            # if suma >=1100: # or (old_name != row['name'] and not nan):  # pendiente
            suma = 0
            trace_id += 1
            aux_trace_id -= 1

        old_name = row["name"]

    try:
        df.drop(["trace_id"], axis=1, inplace=True)
    except KeyError:
        pass

    df.insert(2, "trace_id", trace_array, True)
    positive_traces = df[df["trace_id"] > 0]
    traces = positive_traces.groupby(["trace_id"])
    lst = []
    for index, trace in traces:
        if index > 0 and len(trace) > 1:
            lst.append(feature_extraction(trace))

    features = generate_features_df(lst)
    return features


def peak_features(var):
    # Promedio de valor absoluto de la aceleración
    mean_val = np.mean(var)
    prom_abs = np.mean(np.absolute(var))
    std = np.std(var)
    max_val = np.max(var)
    min_val = np.min(var)
    return mean_val, prom_abs, std, max_val, min_val, skew(var)


def feature_extraction(trace):
    """

    :param trace: slice of operation_df for an specific trace number
    :return: list of attributes for that trace
    """
    trace["cumulative_distance"] = trace["run"].cumsum()

    # Picos aceleraciones y frenadas
    acc = trace["mean_acc"].to_numpy()
    mean_acc, prom_abs_acc, std_acc, max_acc, min_acc, skew_acc = peak_features(acc)

    # Derivative of da/dt to find Jerk  - partir en otra función
    time_indexed_acc = pd.Series(acc, index=trace["timestamp2"])
    jerk = time_indexed_acc.diff().to_numpy()

    # Picos corriente
    current = trace["current"].to_numpy()
    (
        mean_current,
        prom_abs_current,
        std_current,
        max_current,
        min_current,
        skew_current,
    ) = peak_features(current)
    slope = np.mean(trace["slope"])

    # Medidas de potencia específica
    power = trace["power_kw"].to_numpy()
    (
        mean_power,
        prom_abs_power,
        std_power,
        max_power,
        min_power,
        skew_power,
    ) = peak_features(power)

    # With battery capacity
    consumption2 = trace["capacity"].iloc[0] - trace["capacity"].iloc[-1]

    # With power integration
    consumption3 = integrate.cumtrapz(trace["power_kw"], trace["timestamp2"])
    consumption3 = (consumption3[-1] - consumption3[0]) / 3600

    consumption = (consumption2 + consumption3) / 2
    kms = trace["cumulative_distance"].iloc[-1] / 1000
    consumption_per_km = consumption / kms

    speed = trace["speed"].to_numpy()
    (
        mean_speed,
        prom_abs_speed,
        std_speed,
        max_speed,
        min_speed,
        skew_speed,
    ) = peak_features(speed)

    time = trace["timestamp2"].iloc[-1] - trace["timestamp2"].iloc[0]

    stopped_time = 0
    old_time = trace["timestamp2"].iloc[0]
    prev = False

    for index, row in trace[["timestamp2", "mean_speed"]].iterrows():
        if row["mean_speed"] < 2:
            if prev:
                stopped_time += row["timestamp2"] - old_time

            old_time = row["timestamp2"]
            prev = True
        else:
            prev = False
    idle_time = stopped_time / time
    traffic_factor = mean_speed / std_speed if std_speed != 0 else 0
    mean_temp = trace["ext_temp"].mean()
    nominal_speed = trace["speed_kph"].iloc[0]
    speed_ind = nominal_speed / np.max(trace["speed"])

    try:
        test_id = trace["test_id"].iloc[0]
    except KeyError:
        test_id = 0

    return [
        mean_acc,
        prom_abs_acc,
        std_acc,
        max_acc,
        min_acc,
        skew_acc,
        mean_current,
        prom_abs_current,
        std_current,
        max_current,
        min_current,
        skew_current,
        mean_power,
        prom_abs_power,
        std_power,
        max_power,
        min_power,
        skew_power,
        mean_speed,
        prom_abs_speed,
        std_speed,
        max_speed,
        min_speed,
        skew_speed,
        kms,
        consumption_per_km,
        consumption,
        trace["highway"].iloc[0],
        slope,
        nominal_speed,
        trace["soc"].mean(),
        mean_temp,
        time,
        idle_time,
        traffic_factor,
        trace["user_name"].iloc[0],
        trace["vehicle_id"].iloc[0],
        speed_ind,
        test_id,
        trace["timestamp"].iloc[-1],
        trace["mass"].iloc[-1],
        trace["odometer"].iloc[-1],
    ]


def generate_features_df(lst):
    cols = [
        "mean_acc",
        "prom_abs_acc",
        "std_acc",
        "max_acc",
        "min_acc",
        "skew_acc",
        "mean_current",
        "prom_abs_current",
        "std_current",
        "max_current",
        "min_current",
        "skew_current",
        "mean_power",
        "prom_abs_power",
        "std_power",
        "max_power",
        "min_power",
        "skew_power",
        "mean_speed",
        "prom_abs_speed",
        "std_speed",
        "max_speed",
        "min_speed",
        "skew_speed",
        "kms",
        "consumption_per_km",
        "consumption",
        "highway",
        "slope",
        "nominal_speed",
        "mean_soc",
        "mean_temp",
        "time",
        "idle_time",
        "traffic_factor",
        "user_name",
        "vehicle_id",
        "speed_ind",
        "test_id",
        "end_time",
        "mass",
        "end_odometer",
    ]

    return pd.DataFrame(lst, columns=cols)
