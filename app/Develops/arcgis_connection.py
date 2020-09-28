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


user_name = 'sechava4'
password = '5Importante.'
my_gis = arcgis.gis.GIS('https://www.arcgis.com', user_name, password)

route_service_url = my_gis.properties.helperServices.route.url
print(route_service_url)

route_service = network.RouteLayer(route_service_url, gis=my_gis)
print(route_service)

# lon, lat: palmeras 3 to eafit to mall del este
stops = '''-75.580855,6.151992; -75.579519,6.199303;  -75.556413, 6.198418'''

start_time = int(datetime.datetime.utcnow().timestamp() * 1000)

route_layer = network.RouteLayer(route_service_url, gis=my_gis)
result = route_layer.solve(stops=stops,
                           directions_language='es', return_routes=True,
                           return_stops=True, return_directions=True,
                           directions_length_units='esriNAUKilometers', return_z=True,
                           return_barriers=False, return_polygon_barriers=False,
                           return_polyline_barriers=False, start_time=start_time,
                           start_time_is_utc=True)

records = []
travel_time, time_counter = 0, 0
distance, distance_counter = 0, 0

for i in result['directions'][0]['features']:
    time_of_day = datetime.datetime.fromtimestamp(i['attributes']['arriveTimeUTC'] / 1000).strftime('%H:%M:%S')
    time_counter = i['attributes']['time']
    distance_counter = i['attributes']['length']
    travel_time += time_counter
    distance += distance_counter
    records.append((time_of_day, i['attributes']['text'],
                    round(travel_time, 2), round(distance, 2)))


# pd.set_option('display.max_colwidth', 100)
df = pd.DataFrame.from_records(records, index=[i for i in range(1, len(records) + 1)],
                               columns=['Time of day', 'Direction text',
                                        'Duration (min)', 'Distance (km)'])


df2 = pd.DataFrame.from_records(result['routes']['features'][0]['geometry']['paths'][0], columns=['lon', 'lat'])




