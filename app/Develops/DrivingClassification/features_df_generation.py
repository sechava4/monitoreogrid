import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import find_peaks
from scipy.stats import iqr
import seaborn as sns

from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


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
        trace, current, 115, 100, 'current')  # mas de nedio acelerador

    std_pot = np.std(trace['power_kw'])
    iqr_pot = iqr(trace['power_kw'])
    prom_abs_pot = np.mean(np.absolute(trace['power_kw'] ))
    consumption = trace['capacity'].iloc[0] - trace['capacity'].iloc[-1]
    kms = trace['cumulative_distance'].iloc[-1]/1000
    consumption_per_km = consumption / kms
    std_current_std_jerk = std_current * std_jerk
    max_speed = trace['speed'].max()
    mean_speed = trace['speed'].mean()
    median_speed = trace['speed'].median()
    std_speed = trace['speed'].std()

    return [num_acc_min, num_acc_fr_min, prom_sobrepaso_acc, prom_sobrepaso_fren, prom_abs_acc, std_acc,
            num_jerk_acc_min, num_jerk_freno_min, prom_sobrepaso_jerk_acc,
            prom_sobrepaso_jerk_freno, prom_abs_jerk, std_jerk, std_pot, prom_abs_pot,  consumption,
            kms, consumption_per_km, num_current_min, num_current_fr_min, prom_sobrepaso_current,
            prom_sobrepaso_current_fr, prom_abs_current, std_current, std_current_std_jerk,
            trace['highway'].iloc[0], np.mean(trace['slope']), max_current, max_jerk, max_acc,
            trace['power_kw'].max(), max_speed, mean_speed, std_speed, iqr_pot]


if __name__ == '__main__':
    complete_df = pd.read_csv('../updated_vehicle_operation.csv', index_col='id')
    classifier_df = complete_df[complete_df['trace_id'] > 0]
    traces = classifier_df.groupby(['trace_id'])
    cols = ['num_acc_min', 'num_acc_fr_min', 'prom_sobrepaso_acc', 'prom_sobrepaso_fren', 'prom_abs_acc',
            'std_acc', 'num_jerk_acc_min', 'num_jerk_freno_min', 'prom_sobrepaso_jerk_acc',
            'prom_sobrepaso_jerk_freno', 'prom_abs_jerk', 'std_jerk', 'std_pot', 'prom_abs_pot',
            'consumption', 'kms', 'consumption_per_km', 'num_current_min', 'num_current_fr_min',
            'prom_sobrepaso_current', 'prom_sobrepaso_current_fr', 'prom_abs_current', 'std_current',
            'std_current_std_jerk', 'highway', 'slope', 'max_current', 'max_jerk', 'max_acc', 'max_pot',
            'max_speed', 'mean_speed', 'std_speed', 'iqr_pot']

    lst = []
    for index, trace in traces:
        if index > 0 and len(trace) > 1:
            lst.append(feature_extraction(trace))

    features = pd.DataFrame(lst, columns=cols)
    features.dropna(subset=['num_acc_min'], inplace=True)
    features.reset_index(inplace=True)
    features = features[features['kms'] <= 1.6]
    features['log_max_pot'] = np.log(features['max_pot'])
    features['log_max_jerk'] = np.log(features['max_jerk'])

    features['log_prom_abs_current'] = np.log(features['prom_abs_current'])
    corr = features.corr()
    features.dropna(inplace=True)
    
    sns.pairplot(features.dropna(), hue='highway', vars=['max_current', 'std_pot', 'slope', 'prom_abs_current',
                                                         'max_pot', 'max_jerk', 'consumption',
                                                         'iqr_pot'], kind='scatter')

    le = LabelEncoder()
    features['highway_enc'] = le.fit_transform(features['highway'])
    X = np.array(features[['max_current', 'std_pot', 'slope', 'prom_abs_current',
                           'max_pot', 'max_jerk', 'consumption_per_km',
                           'max_speed', 'mean_speed', 'highway_enc']])

    '''
    X = np.array(features[['num_acc_min', 'num_acc_fr_min', 'prom_sobrepaso_acc', 'prom_sobrepaso_fren', 'prom_abs_acc',
                          'std_acc', 'num_jerk_acc_min', 'num_jerk_freno_min', 'prom_sobrepaso_jerk_acc',
                          'prom_sobrepaso_jerk_freno', 'prom_abs_jerk', 'std_jerk', 'std_pot', 'prom_abs_pot',
                          'consumption', 'kms', 'consumption_per_km', 'num_current_min', 'num_current_fr_min',
                          'prom_sobrepaso_current', 'prom_sobrepaso_current_fr', 'prom_abs_current', 'std_current',
                          'std_current_std_jerk', 'highway', 'slope', 'max_current', 'max_jerk', 'max_acc', 'max_pot',
                          'max_speed', 'mean_speed', 'std_speed']])

    '''
    pca = PCA()
    pca.fit(X)
    print(pca.explained_variance_ratio_)
    pca_var = pca.explained_variance_ratio_
    print('The explained variances with 2 components is:', pca_var.sum())
    n_components = 2

    if n_components == 2:
        pca = PCA(n_components=2)
        pca.fit(X)
        X_transformed = pca.transform(X)
        fig = plt.figure(figsize=[10, 10])
        plt.scatter(x=X_transformed[:, 0], y=X_transformed[:, 1], s=10)

    elif n_components == 3:
        fig = plt.figure(figsize=[10,10])
        ax = Axes3D(fig)
        ax.scatter(X[:, 0], X[:, 1], X[:, 2], s=10)
