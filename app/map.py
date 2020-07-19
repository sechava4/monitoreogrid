import pydeck
'''
DATA_URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/geojson/vancouver-blocks.json"
LAND_COVER = [[[-123.0, 49.196], [-123.0, 49.324], [-123.306, 49.324], [-123.306, 49.196]]]

INITIAL_VIEW_STATE = pydeck.ViewState(
  latitude=49.254,
  longitude=-123.13,
  zoom=11,
  max_zoom=16,
  pitch=45,
  bearing=0
)

polygon = pydeck.Layer(
    'PolygonLayer',
    LAND_COVER,
    stroked=False,
    # processes the data as a flat longitude-latitude pair
    get_polygon='-',
    get_fill_color=[0, 0, 0, 20]
)

geojson = pydeck.Layer(
    'GeoJsonLayer',
    DATA_URL,
    opacity=0.8,
    stroked=False,
    filled=True,
    extruded=True,
    wireframe=True,
    get_elevation='properties.valuePerSqm / 20',
    get_fill_color='[255, 255, properties.growth * 255]',
    get_line_color=[255, 255, 255],
    pickable=True
)

r = pydeck.Deck(
    layers=[polygon, geojson],
    initial_view_state=INITIAL_VIEW_STATE)

r.to_html()
'''

import pydeck
import os

# Import Mapbox API Key from environment
MAPBOX_API_KEY = 'pk.eyJ1Ijoic2FudGlhZ28xNzFjYyIsImEiOiJja2NjZTkzOTkwM3ZxMndxa296YTVseGNkIn0.EFcvvL83cLQZYsqSgLVa6A'

# AWS Open Data Terrain Tiles
TERRAIN_IMAGE = '"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"'

# Define how to parse elevation tiles
ELEVATION_DECODER = {"rScaler": 256, "gScaler": 1, "bScaler": 1 / 256, "offset": -32768}

SURFACE_IMAGE = '"https://api.mapbox.com/v4/mapbox.satellite/{{z}}/{{x}}/{{y}}@2x.png?access_token={}"'.format(
    MAPBOX_API_KEY
)

terrain_layer = pydeck.Layer(
    "TerrainLayer", data=None, elevation_decoder=ELEVATION_DECODER, texture=SURFACE_IMAGE, elevation_data=TERRAIN_IMAGE
)

view_state = pydeck.ViewState(latitude=46.24, longitude=-122.18, zoom=11.5, bearing=140, pitch=60)

r = pydeck.Deck(terrain_layer, initial_view_state=view_state)

r.to_html("terrain_layer.html", notebook_display=False)

