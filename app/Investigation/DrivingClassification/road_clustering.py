import os

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app import app
from app.Investigation.DataInteractor.data_fetcher import DataFetcher

print("Enter file prefix")
name = "renault"  # input()
data_path = os.path.join(app.root_path) + "/DataBackup/" + name

try:
    loaded_data = pd.read_hdf(
        data_path + "_data.h5", key=name + "_updated_df_operation"
    )
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments")
    segments = segments[segments["mean_speed"] > 0]
    segments = segments[segments["consumption_per_km"] < 10]
    segments = segments[segments["consumption_per_km"] > -10]

except FileNotFoundError:
    print("Enter query")
    query = input() or "SELECT * from operation limit 10"
    print(query)
    data_fetcher = DataFetcher()
    data_fetcher.upload_data_to_h5(name, query)
    loaded_data = pd.read_hdf(
        data_path + "_data.h5", key=name + "_updated_df_operation"
    )
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments")

X = segments[
    [
        "slope",
        "mean_speed",
    ]
].values

X = StandardScaler().fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=0).fit(X)
core_samples_mask = np.zeros_like(kmeans.labels_, dtype=bool)
labels = kmeans.labels_

# Number of clusters in labels, ignoring noise if present.
n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
n_noise_ = list(labels).count(-1)

print("Estimated number of clusters: %d" % n_clusters_)
print("Estimated number of noise points: %d" % n_noise_)
print("Silhouette Coefficient: %0.3f" % metrics.silhouette_score(X, labels))

# Plot result

# Black removed and is used for noise instead.
unique_labels = set(labels)
colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
for k, col in zip(unique_labels, colors):
    if k == -1:
        # Black used for noise.
        col = [0, 0, 0, 1]

    class_member_mask = labels == k

    xy = X[class_member_mask & core_samples_mask]
    plt.plot(
        xy[:, 0],
        xy[:, 1],
        "o",
        markerfacecolor=tuple(col),
        markeredgecolor="k",
        markersize=14,
    )

    xy = X[class_member_mask & ~core_samples_mask]
    plt.plot(
        xy[:, 0],
        xy[:, 1],
        "o",
        markerfacecolor=tuple(col),
        markeredgecolor="k",
        markersize=6,
    )

plt.title("Estimated number of clusters: %d" % n_clusters_)
plt.show()
segments["road_clusters"] = labels
sns.pairplot(
    segments.sort_values(["slope"]),
    hue="road_clusters",
    palette="Paired",
    vars=["mean_speed", "slope"],
    kind="scatter",
)

segments.to_hdf(data_path + "_data.h5", key=name + "_segments")
