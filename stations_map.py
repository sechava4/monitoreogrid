import pydeck as pdk


def plot_data(data_frame):
    layer = pdk.Layer(
        "ScatterplotLayer",
        data_frame,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=6,
        radius_min_pixels=5,
        radius_max_pixels=5,
        line_width_min_pixels=1,
        get_position=["longitude","latitude"],
        #get_radius="exits_radius",
        get_fill_color=[255, 140, 0],
        get_line_color=[0, 0, 0],
    )

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=-75.56359,
        latitude=6.25184,
        zoom=10,
        min_zoom=5,
        max_zoom=15,
        pitch=40.5,
        bearing=-27.36
    )

    # Render
    r = pdk.Deck(
        layers=[layer], initial_view_state=view_state, tooltip={"text": "{name}\n{charger_types}"}
    )
    r.to_html("templates/map.html")

