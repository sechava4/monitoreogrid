import plotly.graph_objects as go
import plotly
import pandas as pd


def plot_path(df, lon="longitude", lat="latitude"):
    fig = go.Figure(
        go.Scattermapbox(
            mode="markers+lines", lon=df[lon], lat=df[lat], marker={"size": 10}
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            mode="markers+lines", lon=df[lon], lat=df[lat], marker={"size": 10}
        )
    )

    fig.update_layout(
        margin={"l": 0, "t": 0, "b": 0, "r": 0},
        mapbox={
            "center": {"lon": -75.58, "lat": 6.151},
            "style": "stamen-terrain",
            "zoom": 10,
        },
    )

    plotly.offline.plot(fig)
