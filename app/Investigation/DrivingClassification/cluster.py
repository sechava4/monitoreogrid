import os

import category_encoders as ce
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import scipy
import scipy.cluster.hierarchy as sch
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering

from app import app
from app.Investigation.DataInteractor.data_fetcher import DataFetcher

print("Enter file prefix")
name = input()
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


encoder = ce.MEstimateEncoder(cols=["highway"], return_df=True)
encoder.fit(segments[["highway"]], segments["consumption_per_km"])
X_cleaned = encoder.transform(segments[["highway"]])
X_cleaned.rename(columns={"highway": "highway_enc"}, inplace=True)
segments["highway_enc"] = X_cleaned.highway_enc

# se eliminan las variables que no son interesantes para el problema de cluster,
# ya que no hacen parte de los atributos de conducción

X = segments.drop(
    columns=[
        "test_id",
        "user_name",
        "vehicle_id",
        "end_time",
        "slope_cat",
        "mass",
        "speed_cat",
        "highway",
        "end_odometer",
        "consumption",
        "kms",
    ]
).values

# Escalamos antes de aplicar PCA
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Hacemos PCA para reducir la dimensionalidad del problema
pca = PCA()
pca.fit(X_scaled)
print(
    "The explained variances with 2 components is:",
    pca.explained_variance_ratio_[0:1].sum(),
)
n_components = 2

if n_components == 2:
    pca = PCA(n_components=2)
    pca.fit(X_scaled)
    X_transformed = pca.transform(X_scaled)
    fig = plt.figure(figsize=[10, 10])
    plt.scatter(x=X_transformed[:, 0], y=X_transformed[:, 1], s=10)

elif n_components == 3:
    pca = PCA(n_components=3)
    pca.fit(X_scaled)
    X_transformed = pca.transform(X_scaled)
    fig = px.scatter_3d(
        x=X_transformed[:, 0],
        y=X_transformed[:, 1],
        z=X_transformed[:, 2],
        log_x=False,
        size=np.repeat([4], len(X)),
    )
    fig.show()

plt.figure(figsize=[10, 5])
dendrogram = sch.dendrogram(sch.linkage(X_transformed, method="ward"))

plt.title("Dendograma")
plt.xlabel("Segmentos")
plt.ylabel("Distancias Euclidianas")
plt.show()

hc = AgglomerativeClustering(n_clusters=2, affinity="euclidean", linkage="ward")

y_hc = hc.fit_predict(X_transformed)

# Visualising the clusters
plt.figure(figsize=[9, 9])
plt.scatter(
    X_transformed[y_hc == 0, 0],
    X_transformed[y_hc == 0, 1],
    s=20,
    c="red",
    label="Cluster 1",
)
plt.scatter(
    X_transformed[y_hc == 1, 0],
    X_transformed[y_hc == 1, 1],
    s=20,
    c="blue",
    label="Cluster 2",
)
plt.scatter(
    X_transformed[y_hc == 2, 0],
    X_transformed[y_hc == 2, 1],
    s=20,
    c="green",
    label="Cluster 3",
)
plt.scatter(
    X_transformed[y_hc == 3, 0],
    X_transformed[y_hc == 3, 1],
    s=20,
    c="cyan",
    label="Cluster 4",
)
plt.title("Clusters of drivers")
plt.xlabel("Principal component 1")
plt.ylabel("Principal component 2")
plt.legend()
plt.show()

segments["cluster"] = y_hc + 1
sns.pairplot(
    segments.sort_values(["slope"]),
    hue="cluster",
    palette="Paired",
    vars=[
        "max_power",
        "mean_speed",
    ],
    kind="scatter",
)


t, p = scipy.stats.ttest_ind(
    segments["consumption_per_km"][(segments["cluster"] == 1)],
    segments["consumption_per_km"][segments["cluster"] == 2],
)

print("Consumption difference between clusters")
print("t = " + str(t))
print("p-value = " + str(p), "\n")

# Observamos que las medias son significativamente diferentes

# plt.figure(figsize=[9,9])
# fig = plt.figure(figsize=[10, 10])
# ax = Axes3D(fig)
# fig = px.scatter_3d(segments['mean_speed'][y_hc == 0], segments['max_current'][y_hc == 0], segments['traffic_factor'][y_hc == 0]) #, color = 'red')  #, label = 'Cluster 1')
fig = px.scatter_3d(
    segments,
    x="mean_speed",
    y="max_current",
    z="traffic_factor",
    color="cluster",
    width=800,
    height=800,
)
# px.scatter_3d(segments['mean_speed'][y_hc == 2], segments['max_current'][y_hc == 2], segments['traffic_factor'][y_hc == 2]) #, c = 'green', label = 'Cluster 3')
# px.scatter_3d(segments['mean_speed'][y_hc == 3], segments['max_current'][y_hc == 3], segments['traffic_factor'][y_hc == 3]) #, c = 'cyan', label = 'Cluster 4')
# plt.title('Clusters of drivers')
# plt.xlabel('mean_speed kmh')
# plt.ylabel('max_current A')
# plt.legend()
fig.show()

# fig = px.scatter_3d(x=X_transformed[:, 0], y=X_transformed[:, 1], z=X_transformed[:, 2], log_x=False, size=np.repeat([4], len(X)))
#     fig.show()

# Evaluamos el performance del modelo medieante el coheficiente de silueta

from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.cm as cm

range_n_clusters = [2]

for n_clusters in range_n_clusters:
    # Create a subplot with 1 row and 2 columns
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(18, 7)

    # The 1st subplot is the silhouette plot
    # The silhouette coefficient can range from -1, 1 but in this example all
    # lie within [-0.1, 1]
    ax1.set_xlim([-0.1, 1])
    # The (n_clusters+1)*10 is for inserting blank space between silhouette
    # plots of individual clusters, to demarcate them clearly.
    ax1.set_ylim([0, len(X_transformed) + (n_clusters + 1) * 10])

    # Initialize the clusterer with n_clusters value and a random generator
    # seed of 10 for reproducibility.
    clusterer = AgglomerativeClustering(
        n_clusters=n_clusters, affinity="euclidean", linkage="ward"
    )
    cluster_labels = clusterer.fit_predict(X_transformed)

    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed
    # clusters
    silhouette_avg = silhouette_score(X_transformed, cluster_labels)
    print(
        "For n_clusters =",
        n_clusters,
        "The average silhouette_score is :",
        silhouette_avg,
    )

    # Compute the silhouette scores for each sample
    sample_silhouette_values = silhouette_samples(X_transformed, cluster_labels)

    y_lower = 10
    for i in range(n_clusters):
        # Aggregate the silhouette scores for samples belonging to
        # cluster i, and sort them
        ith_cluster_silhouette_values = sample_silhouette_values[cluster_labels == i]

        ith_cluster_silhouette_values.sort()

        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i

        color = cm.nipy_spectral(float(i) / n_clusters)
        ax1.fill_betweenx(
            np.arange(y_lower, y_upper),
            0,
            ith_cluster_silhouette_values,
            facecolor=color,
            edgecolor=color,
            alpha=0.7,
        )

        # Label the silhouette plots with their cluster numbers at the middle
        ax1.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))

        # Compute the new y_lower for next plot
        y_lower = y_upper + 10  # 10 for the 0 samples

    ax1.set_title("The silhouette plot for the various clusters.")
    ax1.set_xlabel("The silhouette coefficient values")
    ax1.set_ylabel("Cluster label")

    # The vertical line for average silhouette score of all the values
    ax1.axvline(x=silhouette_avg, color="red", linestyle="--")

    ax1.set_yticks([])  # Clear the yaxis labels / ticks
    ax1.set_xticks([-0.1, 0, 0.2, 0.4, 0.6, 0.8, 1])

    # 2nd Plot showing the actual clusters formed
    colors = cm.nipy_spectral(cluster_labels.astype(float) / n_clusters)
    ax2.scatter(
        X_transformed[:, 0],
        X_transformed[:, 1],
        marker=".",
        s=30,
        lw=0,
        alpha=0.7,
        c=colors,
        edgecolor="k",
    )

    ax2.set_title("The visualization of the clustered data.")
    ax2.set_xlabel("Feature space for the 1st feature")
    ax2.set_ylabel("Feature space for the 2nd feature")

    plt.suptitle(
        (
            "Silhouette analysis for KMeans clustering on sample data "
            "with n_clusters = %d" % n_clusters
        ),
        fontsize=14,
        fontweight="bold",
    )

plt.show()

segments["driving_cluster"] = cluster_labels
segments.to_hdf(data_path + "_data.h5", key=name + "_segments")
