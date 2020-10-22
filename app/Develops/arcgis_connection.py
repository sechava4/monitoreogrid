from copy import deepcopy
from datetime import datetime
# from IPython.display import HTML
import json
import arcgis
import pandas as pd
from arcgis.gis import GIS
import arcgis.network as network
import arcgis.geocoding as geocoding
import datetime
import plotly.graph_objects as go
import plotly
import datetime


user_name = 'sechava4'
password = '5Importante.'
my_gis = arcgis.gis.GIS('https://www.arcgis.com', user_name, password)

route_service_url = my_gis.properties.helperServices.route.url
print(route_service_url)

route_service = network.RouteLayer(route_service_url, gis=my_gis)
print(route_service)

# lon, lat: palmeras 3 to eafit to mall del este,
stops = ''' -75.579519,6.199303; -75.541652, 6.153382'''   # palmeras : -75.580855,6.151992

start_time = int(datetime.datetime.utcnow().timestamp() * 1000)

route_layer = network.RouteLayer(route_service_url, gis=my_gis)
result = route_layer.solve(stops=stops,
                           directions_language='es', return_routes=True,
                           return_stops=True, return_directions=True,
                           directions_length_units='esriNAUKilometers', return_z=True,
                           return_barriers=False, return_polygon_barriers=False,
                           return_polyline_barriers=False, start_time=start_time,
                           start_time_is_utc=True, directions_output_type= 'esriDOTFeatureSets',
                           output_geometry_precision=7)

points = result['directionPoints']['features']
paths = result['directionLines']['features']
df = pd.DataFrame(points)
attr = pd.DataFrame(df['attributes'].to_list())
points = pd.DataFrame(df['geometry'].to_list())

# df2 = pd.DataFrame.from_records(result['routes']['features'][0]['geometry']['paths'][0], columns=['lon', 'lat'])


fig = go.Figure(go.Scattermapbox(
    mode = "markers+lines",
    lon = points['x'],
    lat = points['y'],
    marker = {'size': 10}))

fig.update_layout(
    margin ={'l':0,'t':0,'b':0,'r':0},
    mapbox = {
        'center': {'lon': -75.58, 'lat': 6.151},
        'style': "stamen-terrain",
        'center': {'lon': -75.58, 'lat': 6.151},
        'zoom': 10})


plotly.offline.plot(fig, filename='arcgis_short_palmas.html')