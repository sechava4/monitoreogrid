import pandas as pd

import numpy as np

import time
import osmnx as ox

import mysql.connector
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style="ticks", color_codes=True)


def get_nearest_edges_of_segments(UG, nearest_edges):
    list_attr = []
    for edge in nearest_edges:
        for u, v, k, data in UG:
            if [edge[0], edge[1]] == [v, u] or [edge[0], edge[1]] == [u, v]:
                list_attr.append(data)
                break
    return list_attr


def add_osmn_attributes(df, UG, G):
    dates = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S.%f")

    x = np.array([time.mktime(t.timetuple()) for t in dates])
    df["timestamp2"] = x

    X = df["longitude"].to_numpy()
    Y = df["latitude"].to_numpy()

    print("empieza nearest_edges")
    nearest_edges = ox.distance.get_nearest_edges(G, X=X, Y=Y, method="balltree")
    list_of_attr = get_nearest_edges_of_segments(UG, nearest_edges)
    edge_df = pd.DataFrame(list_of_attr)
    df_osm = pd.concat(
        [df.reset_index(drop=True), edge_df.reset_index(drop=True)], axis=1
    )
    df_osm["name"] = df_osm["name"].astype(str)
    df_osm["highway"] = df_osm["highway"].astype(str)
    return df_osm


if __name__ == "__main__":
    # df = pd.read_csv('../DataBackup/old_vehicle_operation.csv')
    # df = pd.read_csv('../DataBackup/old_vehicle_operation.csv')

    print("empieza")
    cnx = mysql.connector.connect(
        user="admin",
        password="actuadores",
        host="157.230.209.3",
        database="monitoreodb",
    )
    print("conexión ok db")
    query = "SELECT * from operation WHERE vehicle_id = 'FVQ731'"
    FVQ731 = pd.read_sql_query(query, cnx, index_col="id")
    FVQ731.dropna(axis=1, how="all", inplace=True)

    filepath = "MedellinGraphData/medellin.graphml"
    G = ox.load_graphml(filepath)
    UG = ox.get_undirected(G).edges(keys=True, data=True)
    print("carga el grafo")

    FVQ731.dropna(subset=["power_kw", "odometer"], inplace=True)
    df = add_osmn_attributes(FVQ731, UG, G)

    # FVQ731_osm.to_csv('updated_old_vehicle_operation.csv', index=False)
    # plot
    # sns.catplot(x="power_kw", y="highway_str", kind="boxen", osm_data=real_route_with_attr)
    # real_route_with_attr['length'][real_route_with_attr['length'] < 3000].hist(bins=30)
