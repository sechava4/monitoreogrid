import os

import mysql.connector
import pandas as pd
import numpy as np

from app import app
from app.Investigation.OpenStreetMaps.associate_edges_to_operation import OsmDataAdapter
from app.Investigation.Route_segmentation.segmentation import gen_traces


class DataFetcher:
    def __init__(self):
        self.cnx = mysql.connector.connect(
            user="admin",
            password="actuadores",
            host="104.236.94.94",
            database="monitoreodb",
        )

    def update_data(self, query):
        all_data = pd.read_sql_query(query, self.cnx, index_col="id")
        all_data.dropna(axis=1, how="all", inplace=True)

        osm_adapter = OsmDataAdapter()
        all_data_with_osm = osm_adapter.add_osmn_attributes(all_data)

        convert_dict = {
            "vehicle_id": str,
            "charger_type": str,
            "drivemode": str,
            "user_name": str,
            "osmid": str,
            "lanes": str,
            "name": str,
            "highway": str,
            "geometry": str,
            "maxspeed": str,
            "bridge": str,
            "junction": str,
            "ref": str,
            "width": str,
            "tunnel": str,
            "access": str,
        }
        try:
            all_data_with_osm = all_data_with_osm.astype(convert_dict)
            return all_data_with_osm
        except KeyError:
            return all_data_with_osm

    def upload_data_to_h5(self, name, query="SELECT * from operation"):
        all_data_with_osm = self.update_data(query)
        data_path = os.path.join(app.root_path) + "/DataBackup/" + name
        all_data_with_osm.to_hdf(
            data_path + "_data.h5", key=name + "_updated_df_operation", mode="w"
        )
        loaded_data = pd.read_hdf(
            data_path + "_data.h5", key=name + "_updated_df_operation"
        )
        segments = gen_traces(loaded_data)
        
        # Cleaning segments
        segments.replace([np.inf, -np.inf], np.nan, inplace=True)
        for col in ["mean_temp", "idle_time", "speed_ind"]:
            segments[col].fillna(value=np.mean(segments[col]), inplace=True)
        segments.end_odometer.ffill(inplace=True)
        segments.dropna(inplace=True)
        segments = segments[segments['kms'] < 20]
        segments = segments[segments['consumption'] < 40]

        segments['slope_cat'] = pd.cut(segments["slope"], np.arange(-10, 10.1, 2.5))
        segments['slope_cat'] = segments['slope_cat'].astype(str)
        segments.to_hdf(data_path + "_data.h5", key=name + "_segments")
