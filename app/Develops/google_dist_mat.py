# make sure you can connect to Google's server
import requests
import json
import itertools
import json
import pandas as pd
import googlemaps
import datetime
import pytz
import plotly.graph_objects as go
import plotly


gmaps = googlemaps.Client(key='AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI')

locations = '-75.580855,6.151992; -75.579519,6.199303;  6.153764, -75.541675'
'''
url = 'https://maps.googleapis.com/maps/api/directions/json?' \
      'origin="6.151992,-75.580855"&destination="6.199303,-75.579519"&' \
      'key=AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI'

r = requests.get(url).json()
polyline_average = r['routes'][0]['overview_polyline']['points']
'''


def calc(json):
    steps= json[0]['legs'][0]['steps']
    # steps=r['routes'][0]['legs'][0]['steps']
    df=pd.DataFrame(steps)
    distances = pd.DataFrame(df['distance'].to_list())
    duration = pd.DataFrame(df['duration'].to_list())
    end_location = pd.DataFrame(df['end_location'].to_list())

    frame = {'distance': distances['value'], 'time': duration['value'],
              'end_lat': end_location['lat'], 'end_lng': end_location['lng']}

    newdf = pd.DataFrame(frame)
    # ele = gmaps.elevation_along_path(json[0]['overview_polyline']['points'], len(df))  # Equally distanced (m) samples
    subset = newdf[['end_lat', 'end_lng']]
    tuples = [tuple(x) for x in subset.to_numpy()]
    ele = gmaps.elevation(tuples)
    
    df_ele = pd.DataFrame(ele)
    path2 = df_ele['location'].to_list()
    path2_df = pd.DataFrame(path2)

    newdf['elevation'] = df_ele['elevation']

    fig = go.Figure(go.Scattermapbox(
        mode = "markers+lines",
        lon = newdf['end_lng'],
        lat = newdf['end_lat'],
        marker = {'size': 10}))

    fig.add_trace(go.Scattermapbox(
        mode="markers+lines",
        lon=path2_df['lng'],
        lat=path2_df['lat'],
        marker={'size': 10}))

    fig.update_layout(
        margin ={'l':0,'t':0,'b':0,'r':0},
        mapbox = {
            'center': {'lon': -75.58, 'lat': 6.151},
            'style': "stamen-terrain",
            'zoom': 10})

    # plotly.offline.plot(fig, filename='google_path_eafit_palmas.html')
    return newdf, fig, path2_df


if __name__ == '__main__':

    now = datetime.datetime.now(pytz.timezone('America/Bogota'))
    a = gmaps.directions(origin=(6.199303, -75.579519), destination=(6.153676, -75.541933),
                         mode='driving', alternatives=False, departure_time=now, traffic_model='pessimistic')

    # b = gmaps.directions(origin=(6.199303, -75.579519), destination=(6.153382, -75.541652),
    #                      mode='driving', alternatives=False, departure_time=now, traffic_model='optimistic')

    new_df, fig1, ele_df = calc(a)
    new_df.to_csv('consumption_est1.csv', index_label='id')
