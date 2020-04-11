import pandas as pd
import geopandas as gpd
# import matplotlib.pyplot as plt
# import folium
from shapely.ops import nearest_points
from shapely.geometry import LineString
from app import open_dataframes


def create_gdf(df, x="latitude", y="longitude"):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y]), crs={"init":"epsg:4326"})


def calculate_nearest(row, destination, val, col="geometry"):
    dest_unary = destination["geometry"].unary_union
    nearest_geom = nearest_points(row[col], dest_unary)
    match_geom = destination.loc[destination.geometry == nearest_geom[1]]
    match_value = match_geom[val].to_numpy()[0]
    return match_value


if __name__ == '__main__':
    # stations = open_dataframes.get_stations()
    # zones = open_dataframes.get_zones()
    # stations_gdf = create_gdf(stations)
    # stations_gdf = stations_gdf[["name", "geometry"]]
    stations_gdf = gpd.read_file("stations_gdf.geojson")
    # zones_gdf = create_gdf(zones)
    #rutas = open_dataframes.alturas_df("elevation", 6)
    #rutas = rutas.iloc[1:2]
    #rutas_gdf = create_gdf(rutas)
    # rutas_gdf["nearest_geom"] = rutas_gdf.apply(calculate_nearest, destination=zones_gdf, val="geometry", axis=1)
    #rutas["Zona_cercana"] = rutas_gdf.apply(calculate_nearest, destination=zones_gdf, val="name", axis=1)

