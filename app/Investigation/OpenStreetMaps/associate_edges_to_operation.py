import pandas as pd

import numpy as np

import time
import osmnx as ox

import mysql.connector
import seaborn as sns
from app import app
import os


class OsmDataAdapter:
    def __init__(self):
        filepath = os.path.join(app.root_path) + "/Investigation/OpenStreetMaps/osm_data/medellin.graphml"
        self.G = ox.load_graphml(filepath)
        self.UG = ox.get_undirected(self.G).edges(keys=True, data=True)

    def get_nearest_edges_of_segments(self, nearest_edges):
        list_attr = []
        for edge in nearest_edges:
            for u, v, k, data in self.UG:
                if [edge[0], edge[1]] == [v, u] or [edge[0], edge[1]] == [u, v]:
                    list_attr.append(data)
                    break
        return list_attr

    def add_osmn_attributes(self, dataframe):
        dates = pd.to_datetime(dataframe["timestamp"], format="%Y-%m-%d %H:%M:%S.%f")

        x = np.array([time.mktime(t.timetuple()) for t in dates])
        dataframe["timestamp2"] = x

        X = dataframe["longitude"].to_numpy()
        Y = dataframe["latitude"].to_numpy()

        nearest_edges = ox.distance.get_nearest_edges(self.G, X=X, Y=Y, method="balltree")
        list_of_attr = self.get_nearest_edges_of_segments(nearest_edges)
        edge_df = pd.DataFrame(list_of_attr)
        df_osm = pd.concat(
            [dataframe.reset_index(drop=True), edge_df.reset_index(drop=True)], axis=1
        )
        df_osm["name"] = df_osm["name"].astype(str)
        df_osm["highway"] = df_osm["highway"].astype(str)
        return df_osm
