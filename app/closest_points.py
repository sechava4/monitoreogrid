import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points
from shapely.geometry import LineString
from app import open_dataframes
from sklearn.neighbors import BallTree, KDTree

def create_gdf(df, x="latitude", y="longitude"):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y]), crs={"init":"epsg:4326"})


def calculate_nearest(row, destination, val, col="geometry"):
    a = destination["geometry"]
    dest_unary = a.unary_union
    nearest_geom = nearest_points(row[col], dest_unary)
    match_geom = destination.loc[destination.geometry == nearest_geom[1]]
    match_value = match_geom[val].to_numpy()[0]
    return match_value


class Trees:
    station_tree = KDTree(open_dataframes.get_stations()[['latitude', 'longitude']].values, leaf_size=2)
    zones_tree = BallTree(open_dataframes.get_zones()[['latitude', 'longitude']].values, leaf_size=2)
    # df_out['distance_nearest'], df_out['id_nearest'] = station_tree.query(df_out[['latitude', 'longitude']].values, k=1)


if __name__ == '__main__':
    stations = open_dataframes.get_stations()
    # zones = open_dataframes.get_zones()
    # stations_gdf = create_gdf(stations)
    stations = stations[["name", "latitude", "longitude"]]
    rutas = open_dataframes.alturas_df("elevation", 1)
    #rutas = rutas.iloc[1:2]
    _, rutas['id_nearest'] = Trees.station_tree.query(rutas[['latitude', 'longitude']].values, k=1)
    rutas["near_station"] = stations["name"].iloc[rutas['id_nearest']]
    #rutas["near_station"] = b.values
    #string = b.item()

    # zones_gdf = gpd.read_file("zones.geojson")
    # zones_gdf = create_gdf(zones)
    # zones_gdf = zones_gdf[["name", "geometry"]]
    # zones_gdf.to_file("zones.geojson", driver='GeoJSON')
    # rutas_gdf = create_gdf(rutas)
    # rutas_gdf["nearest_zone"] = rutas_gdf.apply(calculate_nearest, destination=zones_gdf, val="geometry", axis=1)
    #rutas["Zona_cercana"] = rutas_gdf.apply(calculate_nearest, destination=zones_gdf, val="name", axis=1)

