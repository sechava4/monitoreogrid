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


if __name__ == "__main__":
    complete_df = pd.read_csv(
        "../../DataBackup/updated_vehicle_operation.csv", index_col="id"
    )
    classifier_df = complete_df[complete_df["trace_id"] > 0]

    sns.catplot(
        x="highway",
        y="power_kw",
        kind="boxen",
        data=classifier_df.sort_values("power_kw"),
    )

    traces = classifier_df.groupby(["trace_id"])

    features = pd.read_csv("../../DataBackup/trace_features.csv", index_col="id")

    features.dropna(subset=["num_acc_min"], inplace=True)
    features.reset_index(inplace=True)
    features = features[features["kms"] <= 1.6]

    corr = features.corr()
    features.dropna(inplace=True)

    sns.pairplot(
        features.dropna(),
        hue="highway",
        vars=[
            "max_current",
            "std_pot",
            "slope",
            "prom_abs_current",
            "max_pot",
            "max_jerk",
            "consumption",
            "iqr_pot",
        ],
        kind="scatter",
    )

    le = LabelEncoder()
    features["highway_enc"] = le.fit_transform(features["highway"])
    X = features[
        [
            "max_current",
            "std_pot",
            "slope",
            "prom_abs_current",
            "max_pot",
            "max_jerk",
            "consumption_per_km",
            "max_speed",
            "mean_speed",
            "highway_enc",
        ]
    ].values

    """
    X = np.array(features[['num_acc_min', 'num_acc_fr_min', 'prom_sobrepaso_acc', 'prom_sobrepaso_fren', 'prom_abs_acc',
                          'std_acc', 'num_jerk_acc_min', 'num_jerk_freno_min', 'prom_sobrepaso_jerk_acc',
                          'prom_sobrepaso_jerk_freno', 'prom_abs_jerk', 'std_jerk', 'std_pot', 'prom_abs_pot',
                          'consumption', 'kms', 'consumption_per_km', 'num_current_min', 'num_current_fr_min',
                          'prom_sobrepaso_current', 'prom_sobrepaso_current_fr', 'prom_abs_current', 'std_current',
                          'std_current_std_jerk', 'highway', 'slope', 'max_current', 'max_jerk', 'max_acc', 'max_pot',
                          'max_speed', 'mean_speed', 'std_speed']])

    """
    pca = PCA()
    pca.fit(X)
    print(pca.explained_variance_ratio_)
    pca_var = pca.explained_variance_ratio_
    print("The explained variances with 2 components is:", pca_var.sum())
    n_components = 3

    if n_components == 2:
        pca = PCA(n_components=2)
        pca.fit(X)
        X_transformed = pca.transform(X)
        fig = plt.figure(figsize=[10, 10])
        plt.scatter(x=X_transformed[:, 0], y=X_transformed[:, 1], s=10)

    elif n_components == 3:
        fig = plt.figure(figsize=[10, 10])
        ax = Axes3D(fig)
        ax.scatter(X[:, 0], X[:, 1], X[:, 2], s=10)
