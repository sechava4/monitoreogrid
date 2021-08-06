import os

import mysql.connector
import pandas as pd
import numpy as np

from app import app
from app.Investigation.OpenStreetMaps.associate_edges_to_operation import OsmDataAdapter
from app.Investigation.Route_segmentation.segmentation import gen_traces, SegmentTypes


class DataFetcher:
    def __init__(self):
        try:
            self.cnx = mysql.connector.connect(
                user="admin",
                password="actuadores",
                host="104.236.94.94",
                database="monitoreodb",
            )
        except mysql.connector.errors.DatabaseError:
            self.cnx = None

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

    def upload_data_to_h5(
        self, name, query="SELECT * from operation", segment_length=1000
    ):
        data_path = os.path.join(app.root_path) + "/DataBackup/" + name
        try:
            loaded_data = pd.read_hdf(
                data_path + "_data.h5", key=name + "_updated_df_operation"
            )
        except FileNotFoundError:
            all_data_with_osm = self.update_data(query)
            all_data_with_osm = all_data_with_osm[all_data_with_osm.operative_state > 0]
            all_data_with_osm.name.fillna("undefined", inplace=True)
            all_data_with_osm.to_hdf(
                data_path + "_data.h5", key=name + "_updated_df_operation", mode="w"
            )
            loaded_data = pd.read_hdf(
                data_path + "_data.h5", key=name + "_updated_df_operation"
            )
        segments = gen_traces(loaded_data, length=segment_length)

        # Cleaning segments
        segments.replace([np.inf, -np.inf], np.nan, inplace=True)
        for col in ["mean_temp", "idle_time", "speed_ind"]:
            segments[col].fillna(value=np.mean(segments[col]), inplace=True)
        segments.end_odometer.ffill(inplace=True)
        segments.dropna(inplace=True)
        segments = segments[segments["mean_speed"] != 0]
        segments = segments[segments["kms"] < 20]
        segments = segments[segments["consumption"] < 40]

        segments["slope_cat"] = pd.cut(segments["slope"], np.arange(-10, 10.1, 2.5))
        segments["slope_cat"] = segments["slope_cat"].astype(str)

        segments["speed_cat"] = pd.cut(segments["mean_speed"], np.arange(0, 150.1, 50))
        segments["speed_cat"] = segments["speed_cat"].astype(str)
        segments["road_clusters"] = "speed 0 - 50, slope -10 - -7.5"
        speeds = [0, 50, 100]
        slopes = [-10, -5, 0, 5]
        for speed in speeds:
            for slope in slopes:
                segments.loc[
                    (segments["mean_speed"] > speed) & (segments["slope"] > slope),
                    "road_clusters",
                ] = f"speed [{speed}-{speed + 50}], slope [{slope}-{slope + 2.5}]"
        segments.to_hdf(data_path + "_data.h5", key=name + "_segments")


if __name__ == "__main__":
    name = "renault"
    data_path = os.path.join(app.root_path) + "/DataBackup/" + name
    # datafetcher = DataFetcher()
    loaded_data = pd.read_hdf(
        data_path + "_data.h5", key=name + "_updated_df_operation"
    )
    segments = gen_traces(
        loaded_data, length=None, segment_type=SegmentTypes.degradation
    )
    segments = segments[segments.kms < 60]
    segments.to_hdf(data_path + "_data.h5", key=name + "_segments_degradation")
