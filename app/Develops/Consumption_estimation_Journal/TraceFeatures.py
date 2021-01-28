from scipy.signal import find_peaks
from scipy.stats import iqr
import pandas as pd
import numpy as np


def peak_features(trace, var, limit_u, limit_l, name):
    peaks, peak_values = find_peaks(var, height=limit_u) # mas de nedio acelerador
    valleys, valleys_values = find_peaks(-var, height=limit_l)
    num_peaks_minuto = 60 * len(peaks)/ (trace['timestamp2'].iloc[-1] - trace['timestamp2'].iloc[0])
    num_valleys_minuto = 60 * len(valleys)/ (trace['timestamp2'].iloc[-1] - trace['timestamp2'].iloc[0])

    prom_sobrepaso_peak = np.mean(peak_values['peak_heights'])/limit_u
    if np.isnan(prom_sobrepaso_peak):
      prom_sobrepaso_peak = 1

    # Promedio de sobrepaso de la referencia máxima de frenado
    prom_sobrepaso_valley = np.mean(valleys_values['peak_heights'])/limit_l
    if np.isnan(prom_sobrepaso_valley):
      prom_sobrepaso_valley = 1

    # Promedio de valor absoluto de la aceleración
    prom_abs = np.mean(np.absolute(var))
    std = np.std(var)
    max_val = np.max(var)
    return num_peaks_minuto, num_valleys_minuto, prom_sobrepaso_peak, prom_sobrepaso_valley, prom_abs, std, max_val


def feature_extraction(trace):
    trace['cumulative_distance'] = trace['run'].cumsum()

    # Picos aceleraciones y frenadas
    acc = trace['mean_acc'].to_numpy()
    num_acc_min, num_acc_fr_min, prom_sobrepaso_acc, prom_sobrepaso_fren, prom_abs_acc, std_acc, max_acc = peak_features(
        trace, acc, 1, 1, ',mean_acc')  # mas de nedio acelerador

    # Derivative of da/dt to find Jerk  - partir en otra función
    time_indexed_acc = pd.Series(acc, index=trace['timestamp2'])
    jerk = time_indexed_acc.diff().to_numpy()
    num_jerk_acc_min, num_jerk_freno_min, prom_sobrepaso_jerk_acc, prom_sobrepaso_jerk_freno, prom_abs_jerk, std_jerk, max_jerk = peak_features(
        trace, jerk[1:], 1.5, 1.5, 'jerk')  # mas de nedio acelerador

    # Picos corriente
    current = trace['current'].to_numpy()
    num_current_min, num_current_fr_min, prom_sobrepaso_current, prom_sobrepaso_current_fr, prom_abs_current, std_current, max_current = peak_features(
        trace, current, 60, 100, 'current')  # mas de nedio acelerador

    power_nominal_zoe = 65.6216
    power_nominal_leaf = 81.2813
    if trace['vehicle_id'].iloc[0] == 'FRV020':
        power_nominal = power_nominal_leaf
    else:
        power_nominal = power_nominal_zoe

    std_power = np.std(trace['power_kw']) / power_nominal
    iqr_power = iqr(trace['power_kw']) / power_nominal
    prom_abs_power = np.mean(np.absolute(trace['power_kw'])) / power_nominal
    max_power = np.max(trace['power_kw']) / power_nominal
    consumption = trace['capacity'].iloc[0] - trace['capacity'].iloc[-1]
    kms = trace['cumulative_distance'].iloc[-1] / 1000
    consumption_per_km = consumption / kms
    std_current_std_jerk = std_current * std_jerk
    max_speed = np.max(trace['speed'])
    mean_speed = np.mean(trace['speed'])
    median_speed = np.median(trace['speed'])
    std_speed = np.std(trace['speed'])
    time = trace['timestamp2'].iloc[-1] - trace['timestamp2'].iloc[0]

    # This indicator detects traffic (including red lights)
    stopped_time = 0
    old_time = trace['timestamp2'].iloc[0]
    prev = False
    for index, row in trace[['timestamp2', 'mean_speed']].iterrows():
        if row['mean_speed'] < 2:
            if prev:
                stopped_time += row['timestamp2'] - old_time

            old_time = row['timestamp2']
            prev = True
        else:
            prev = False
    idle_time = stopped_time / time
    traffic_factor = mean_speed / std_speed

    mean_temp = trace['ext_temp'].mean()
    nominal_speed = trace['speed_kph'].iloc[0]

    speed_ind = nominal_speed / np.max(trace['speed'])
    try:
        test_id = trace['test_id'].iloc[0]
    except KeyError:
        test_id = 0

    # porcentaje de primary, de secondary

    return [num_acc_min, num_acc_fr_min, prom_sobrepaso_acc, prom_sobrepaso_fren, prom_abs_acc, std_acc,
            num_jerk_acc_min, num_jerk_freno_min, prom_sobrepaso_jerk_acc,
            prom_sobrepaso_jerk_freno, prom_abs_jerk, std_jerk, std_power, prom_abs_power, consumption,
            kms, consumption_per_km, num_current_min, num_current_fr_min, prom_sobrepaso_current,
            prom_sobrepaso_current_fr, prom_abs_current, std_current, std_current_std_jerk,
            trace['highway'].iloc[0], np.mean(trace['slope']), nominal_speed, max_current, max_jerk, max_acc,
            max_power, max_speed, mean_speed, std_speed, iqr_power, trace['soc'].mean(),
            mean_temp, time, idle_time,
            traffic_factor, trace['user_id'].iloc[0], trace['vehicle_id'].iloc[0], speed_ind, test_id,
            trace['timestamp'].iloc[-1]]


def generate_features_df(lst):
    cols = ['num_acc_min', 'num_acc_fr_min', 'prom_sobrepaso_acc', 'prom_sobrepaso_fren', 'prom_abs_acc',
            'std_acc', 'num_jerk_acc_min', 'num_jerk_freno_min', 'prom_sobrepaso_jerk_acc',
            'prom_sobrepaso_jerk_freno', 'prom_abs_jerk', 'std_jerk', 'std_power', 'prom_abs_power',
            'consumption', 'kms', 'consumption_per_km', 'num_current_min', 'num_current_fr_min',
            'prom_sobrepaso_current', 'prom_sobrepaso_current_fr', 'prom_abs_current', 'std_current',
            'std_current_std_jerk', 'highway', 'slope', 'nominal_speed', 'max_current', 'max_jerk', 'max_acc',
            'max_power', 'max_speed', 'mean_speed', 'std_speed', 'iqr_power', 'mean_soc', 'mean_temp', 'travel_time',
            'idle_time', 'traffic_factor', 'user_id', 'vehicle_id', 'speed_ind', 'test_id', 'end_time']

    return pd.DataFrame(lst, columns=cols)

