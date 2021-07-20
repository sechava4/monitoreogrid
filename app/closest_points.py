from sklearn.neighbors import KDTree

from app import open_dataframes


class Trees:
    station_tree = KDTree(
        open_dataframes.get_stations()[["latitude", "longitude"]].values, leaf_size=2
    )
    zones_tree = KDTree(
        open_dataframes.get_zones()[["latitude", "longitude"]].values, leaf_size=2
    )
    # df_out['distance_nearest'], df_out['id_nearest'] = station_tree.query(df_out[['latitude', 'longitude']].values, k=1)


if __name__ == "__main__":
    stations = open_dataframes.get_stations()
    zones = open_dataframes.get_zones()
    """
    _, a = Trees.station_tree.query(rutas[['latitude', 'longitude']].values, k=2)
    rutas["closest_st_id1"] = a[:, 0]
    rutas["closest_st_id2"] = a[:, 1]
    rutas["closest_station1"] = stations["name"].reindex(index=rutas['closest_st_id1']).tolist()
    rutas["closest_station2"] = stations["name"].reindex(index=rutas['closest_st_id2']).tolist()
    """
    # _, rutas['id_nearest_zone'] = Trees.zones_tree.query(rutas[['latitude', 'longitude']].values, k=1)
    # rutas["closest_zone"] = zones["name"].reindex(index=rutas['id_nearest_zone']).tolist()
    # string = b.item()
