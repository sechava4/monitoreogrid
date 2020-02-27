import pydeck as pdk

UK_ACCIDENTS_DATA = ('https://raw.githubusercontent.com/uber-common/'
                     'deck.gl-data/master/examples/3d-heatmap/heatmap-data.csv')


def plot_data(data_frame, elevation):

    # Define a layer to display on a map
    layer = pdk.Layer(
        'HexagonLayer',
        data_frame,
        get_position=['longitude', 'latitude'],
        get_elevation=elevation,
        auto_highlight=True,
        elevation_scale=50,
        pickable=True,
        elevation_range=[0, 3000],
        extruded=True,
        coverage=1)

    # Set the viewport location
    view_state = pdk.ViewState(
        longitude=-75.56359,
        latitude=6.25184,
        zoom=6,
        min_zoom=5,
        max_zoom=15,
        pitch=40.5,
        bearing=-27.36)

    r = pdk.Deck(layers=[layer], initial_view_state=view_state)
