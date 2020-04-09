import pydeck as pdk
import os
from app import app
doc_dataset = os.path.join(app.root_path, "test.csv")

import pandas as pd

DATA_URL = {
    "AIRPORTS": "https://raw.githubusercontent.com/uber-common/deck.gl-data/master/examples/line/airports.json",
    "FLIGHT_PATHS": "https://raw.githubusercontent.com/uber-common/deck.gl-data/master/examples/line/heathrow-flights.json",
    # noqa
}

def draw_map():
    INITIAL_VIEW_STATE = pdk.ViewState(latitude=47.65, longitude=7, zoom=4.5, max_zoom=16, pitch=50, bearing=0)

    # RGBA value generated in Javascript by deck.gl's Javascript expression parser
    GET_COLOR_JS = [
        "255 * (1 - (start[2] / 10000) * 2)",
        "128 * (start[2] / 10000)",
        "255 * (start[2] / 10000)",
        "255 * (1 - (start[2] / 10000))",
    ]


    line_layer = pdk.Layer(
        "LineLayer",
        DATA_URL["FLIGHT_PATHS"],
        get_source_position="start",
        get_target_position="end",
        get_color=GET_COLOR_JS,
        get_width=10,
        highlight_color=[255, 255, 0],
        picking_radius=10,
        auto_highlight=True,
        pickable=True,
    )

    r = pdk.Deck(layers=line_layer, initial_view_state=INITIAL_VIEW_STATE, mapbox_key='pk.eyJ1Ijoic2VjaGF2YTQiLCJhIjoiY2s2dTF0eHQ0MDViaTNmbXRhaHVoaG85cSJ9.xMh2vZNuj2PfxsUksteApQ')
    r.to_html("templates/map.html", notebook_display=False)



if __name__ == "__main__":
    df = pd.read_csv("rutas.csv")
    df = df[["latitude", "longitude", "timestamp"]]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['timestamp'] = df['timestamp'].astype('int64')//1e9



