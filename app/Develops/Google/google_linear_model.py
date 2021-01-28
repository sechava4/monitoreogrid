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
import numpy as np
from pickle import load
import statsmodels.api as sm


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
    df = pd.DataFrame(steps)
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

    plotly.offline.plot(fig)

    return newdf, fig, path2_df


def calculate_consumption(segments, path):
    to_ele = segments["elevation"].iloc[1:]
    segments["toAltitude"] = to_ele.append(pd.Series(segments["elevation"].iloc[-1]), ignore_index=True)
    segments["id"] = segments.index
    segments = segments.rename(columns={"id": "segmentNumber", "distance": "distanceInMeters",
                               "time": "durationInSeconds", "elevation": "fromAltitude"})

    segments['slope'] = np.arctan((segments['toAltitude'] - segments['fromAltitude']) / segments['distanceInMeters'])
    segments['nominal_speed'] = 3.6 * segments['distanceInMeters'] / segments['durationInSeconds']
    # segments['user_id'] = 'Santiago_Echavarria'
    #df['user_id'] = 'Santiago_Echavarria'
    segments['user_id'] = 'Jose_Alejandro_Montoya'
    segments['slope_cat'] = pd.cut(segments["slope"], np.arange(-8.5, 8.6, 3.4))

    mean_max_pot_by_slope = pd.read_csv(path+'/mean_max_pot_by_slope.csv', index_col=0)
    mean_max_pot_per_user_and_slope = pd.read_csv(path+'/mean_max_pot_per_user_and_slope.csv', index_col=0)

    # Convert to string data type for the inner join
    mean_max_pot_per_user_and_slope['slope_cat'] = mean_max_pot_per_user_and_slope['slope_cat'].astype('string')
    mean_max_pot_by_slope['slope_cat'] = mean_max_pot_by_slope['slope_cat'].astype('string')
    segments['slope_cat'] = segments['slope_cat'].astype('string')

    print('no of segments', len(segments))

    segments_consolidated = pd.merge(left=segments, right=mean_max_pot_by_slope,
                               left_on=['slope_cat'], right_on=['slope_cat'])

    segments_consolidated = pd.merge(left=segments_consolidated, right=mean_max_pot_per_user_and_slope,
                               left_on=['slope_cat', 'user_id'], right_on=['slope_cat', 'user_id'])

    segments_consolidated['mean_max_pot_usr'] = segments_consolidated.apply(
        lambda row: row['mean_max_pot'] if np.isnan(row['mean_max_pot_usr']) else row['mean_max_pot_usr'],
        axis=1
    )

    print('no of segments', len(segments_consolidated))

    # Apply scaling
    scaler = load(open(path+'/scaler_lm.pkl', 'rb'))
    columns = ['nominal_speed', 'mean_max_pot_usr', 'slope']
    segments_scaled = pd.DataFrame(scaler.transform(segments_consolidated[columns]), columns=columns)

    # Load linear model
    lm_consumo = sm.load(path+'/lm_consumo.pickle')

    # Apply linear model
    segments_scaled['consumption_per_km'] = lm_consumo.predict(segments_scaled)

    # Load inverse scaler
    scaler_inv = load(open(path+'/scaler.pkl', 'rb'))

    # Apply inverse scaling
    pred = pd.DataFrame(scaler_inv.inverse_transform(segments_scaled), columns=segments_scaled.columns)

    # Estimate consumption on every segment based length
    segments_consolidated['consumptionkWh'] = pred['consumption_per_km'] \
                                              * segments_consolidated['distanceInMeters'] / 1000

    print('Consumo estimado', segments_consolidated['consumptionkWh'].sum(), 'kWh')
    estimated_time = segments_consolidated['durationInSeconds'].sum() / 60
    return segments_consolidated['consumptionkWh'].sum().round(3), estimated_time.round(3)


if __name__ == '__main__':

    now = datetime.datetime.now(pytz.timezone('America/Bogota'))
    test_date = datetime.datetime.strptime('2020-08-12 10:26:45', '%Y-%m-%d %H:%M:%S')
    # Eafit to palmas
    a = gmaps.directions(origin=(6.202736, -75.577407), destination=(6.152245, -75.624450),
                         mode='driving', alternatives=False, departure_time=now, traffic_model='pessimistic')

    # b = gmaps.directions(origin=(6.199303, -75.579519), destination=(6.153382, -75.541652),
    #                      mode='driving', alternatives=False, departure_time=now, traffic_model='optimistic')

    df, fig1, ele_df = calc(a)

    to_ele = df["elevation"].iloc[1:]
    to_ele = to_ele.append(pd.Series(df["elevation"].iloc[-1]), ignore_index=True)
    df["toAltitude"] = to_ele
    df["id"] = df.index
    df = df.rename(columns={"id": "segmentNumber", "distance": "distanceInMeters",
                            "time": "durationInSeconds", "elevation": "fromAltitude"})

    df['slope'] = np.arctan((df['toAltitude'] - df['fromAltitude']) / df['distanceInMeters'])
    df['nominal_speed'] = 3.6 * df['distanceInMeters'] / df['durationInSeconds']
    df['user_id'] = 'Santiago_Echavarria'
    #df['user_id'] = 'Jose_Alejandro_Montoya'
    #df['user_id'] = 'Ana_Cristina_G'
    #df['user_id'] = 'Juan_David_Mira'

    df['slope_cat'] = pd.cut(df["slope"], np.arange(-8.5, 8.6, 3.4))

    mean_max_pot_by_slope = pd.read_csv('../Consumption_estimation_Journal/mean_max_pot_by_slope.csv', index_col=0)
    mean_max_pot_per_user_and_slope = pd.read_csv('../Consumption_estimation_Journal/mean_max_pot_per_user_and_slope.csv',
                                        index_col=0)

    # Convert to string data type for the inner join
    mean_max_pot_per_user_and_slope['slope_cat'] = mean_max_pot_per_user_and_slope['slope_cat'].astype('string')
    mean_max_pot_by_slope['slope_cat'] = mean_max_pot_by_slope['slope_cat'].astype('string')
    df['slope_cat'] = df['slope_cat'].astype('string')

    print('no of segments', len(df))

    df_consolidated = pd.merge(left=df, right=mean_max_pot_by_slope,
                                 left_on=['slope_cat'], right_on=['slope_cat'])

    df_consolidated = pd.merge(left=df_consolidated, right=mean_max_pot_per_user_and_slope,
                                 left_on=['slope_cat', 'user_id'], right_on=['slope_cat', 'user_id'])

    df_consolidated['mean_max_pot_usr'] = df_consolidated.apply(
        lambda row: row['mean_max_pot'] if np.isnan(row['mean_max_pot_usr']) else row['mean_max_pot_usr'],
        axis=1
    )

    print('no of segments', len(df_consolidated))

    # Apply scaling
    scaler = load(open('../Consumption_estimation_Journal/scaler_lm.pkl', 'rb'))
    columns = ['nominal_speed', 'mean_max_pot_usr', 'slope']
    df_scaled = pd.DataFrame(scaler.transform(df_consolidated[columns]), columns=columns)

    # Load linear model
    lm_consumo = sm.load('../Consumption_estimation_Journal/lm_consumo.pickle')

    # Apply linear model
    df_scaled['consumption_per_km'] = lm_consumo.predict(df_scaled)

    # Load inverse scaler
    scaler_inv = load(open('../Consumption_estimation_Journal/scaler.pkl', 'rb'))

    # Apply inverse scaling
    df_pred = pd.DataFrame(scaler_inv.inverse_transform(df_scaled), columns=df_scaled.columns)
    # new_df.to_csv('google_path.csv', index_label='id')

    # Estimate consumption on every segment based length
    df_consolidated['consumptionkWh'] = df_pred['consumption_per_km'] * df_consolidated['distanceInMeters'] / 1000
    print('Consumo estimado', df_consolidated['consumptionkWh'].sum(), 'kWh')