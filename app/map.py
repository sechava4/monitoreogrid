import pydeck as pdk
import os
from app import app,open_dataframes
df = open_dataframes.alturas_df("elevation", 1)
import pydeck
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/ajduberstein/geo_datasets/master/housing.csv"
#df = pd.read_csv(DATA_URL)

view = pydeck.data_utils.compute_view(df[["longitude", "latitude"]])
view.pitch = 75
view.bearing = 60

column_layer = pydeck.Layer(
    "ColumnLayer",
    data=df,
    get_position=["longitude", "latitude"],
    get_elevation="elevation",
    elevation_scale=100,
    radius=50,
    get_fill_color=["elevation * 10", 100, 120, 140],
    pickable=True,
    auto_highlight=True,
)

tooltip = {
    "html": "<b>{mrt_distance}</b> meters away from an MRT station, costs <b>{price_per_unit_area}</b> NTD/sqm",
    "style": {"background": "grey", "color": "white", "font-family": '"Helvetica Neue", Arial', "z-index": "10000"},
}

r = pydeck.Deck(
    column_layer, initial_view_state=view, tooltip=tooltip, map_style="mapbox://styles/mapbox/satellite-v9",
)

r.to_html("column_layer.html", notebook_display=False)

"""
if __name__ == "__main__":
    df = pd.read_csv("rutas.csv")
    df = df[["latitude", "longitude", "timestamp"]]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp'] = df['timestamp'].astype('int64')//1e9

"""

