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
import os
from app import app


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
    #path = os.path.join(app.root_path)

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

    mean_max_power_by_slope = pd.read_csv(path+'/mean_max_power_by_slope.csv', index_col=0)
    mean_max_power_per_user_and_slope = pd.read_csv(path+'/mean_max_power_per_user_and_slope.csv', index_col=0)

    # Convert to string data type for the inner join
    mean_max_power_per_user_and_slope['slope_cat'] = mean_max_power_per_user_and_slope['slope_cat'].astype('string')
    mean_max_power_by_slope['slope_cat'] = mean_max_power_by_slope['slope_cat'].astype('string')
    segments['slope_cat'] = segments['slope_cat'].astype('string')

    print('no of segments', len(segments))

    segments_consolidated = pd.merge(left=segments, right=mean_max_power_by_slope,
                            left_on=['slope_cat'], right_on=['slope_cat'])

    segments_consolidated = pd.merge(left=segments_consolidated, right=mean_max_power_per_user_and_slope,
                            left_on=['slope_cat', 'user_id'], right_on=['slope_cat', 'user_id'])

    segments_consolidated['mean_max_power_usr'] = segments_consolidated.apply(
        lambda row: row['mean_max_power'] if np.isnan(row['mean_max_power_usr']) else row['mean_max_power_usr'],
        axis=1
    )

    segments_consolidated['mean_soc'] = 70.0

    # Apply scaling
    scaler = load(open(path + '/scaler_lm.pkl', 'rb'))

    columns = ['mean_max_power_usr', 'mean_soc', 'nominal_speed', 'slope']
    segments_scaled = pd.DataFrame(scaler.transform(segments_consolidated[columns]), columns=columns)

    # Load inverse scaler
    scaler_inv = load(open(path + '/scaler.pkl', 'rb'))

    # load random forest regressor
    r_forest_reg = load(open(path + '/randomForest_0_04maxerr_model.pkl', 'rb'))

    # Para cada tramo de la ruta a estimar
    lst_kWh_per_km = []
    lst_kWh = []

    for i in range(len(segments_consolidated)):

        # Se calcula el consumo para el segmento en unidades escaladas
        c_scaled = r_forest_reg.predict(segments_scaled.iloc[i].values.reshape(1, -1))[0]

        # Se transforma el consumo escalado a unidades de kWh/km
        kWh_per_km = scaler_inv.data_min_[4] + (c_scaled / scaler_inv.scale_[4])
        lst_kWh_per_km.append(kWh_per_km)

        # Se calcula el consumo completo del segmento
        kWh = kWh_per_km * segments_consolidated['distanceInMeters'].iloc[i] / 1000
        lst_kWh.append(kWh)

        try:
            # Se estima el estado de carga inicial del próximo segmento
            segments_consolidated.mean_soc.iloc[i + 1] = segments_consolidated.mean_soc.iloc[i] - kWh * 2.5

            # Se escala el soc de la proxima iteración
            segments_scaled.mean_soc[i + 1] = (segments_consolidated.mean_soc.iloc[i + 1] -
                                               scaler.data_min_[1]) * scaler.scale_[1]

        except:
            break

    segments_consolidated['consumptionkWh'] = lst_kWh
    segments_consolidated['consumption_per_km'] = lst_kWh_per_km

    estimated_time = segments_consolidated['durationInSeconds'].sum() / 60
    return segments_consolidated['consumptionkWh'].sum().round(3), estimated_time.round(3)


if __name__ == '__main__':
    path = os.path.join(app.root_path)
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

    mean_max_power_by_slope = pd.read_csv('../Consumption_estimation_Journal/mean_max_power_by_slope.csv', index_col=0)
    mean_max_power_per_user_and_slope = pd.read_csv(
        '../Consumption_estimation_Journal/mean_max_power_per_user_and_slope.csv',
        index_col=0)

    # Convert to string data type for the inner join
    mean_max_power_per_user_and_slope['slope_cat'] = mean_max_power_per_user_and_slope['slope_cat'].astype('string')
    mean_max_power_by_slope['slope_cat'] = mean_max_power_by_slope['slope_cat'].astype('string')
    df['slope_cat'] = df['slope_cat'].astype('string')

    df_consolidated = pd.merge(left=df, right=mean_max_power_by_slope,
                                 left_on=['slope_cat'], right_on=['slope_cat'])

    df_consolidated = pd.merge(left=df_consolidated, right=mean_max_power_per_user_and_slope,
                                 left_on=['slope_cat', 'user_id'], right_on=['slope_cat', 'user_id'])

    df_consolidated['mean_max_power_usr'] = df_consolidated.apply(
        lambda row: row['mean_max_power'] if np.isnan(row['mean_max_power_usr']) else row['mean_max_power_usr'],
        axis=1
    )

    df_consolidated['mean_soc'] = 70.0

    # Apply scaling
    scaler = load(open('../Consumption_estimation_Journal/scaler_lm.pkl', 'rb'))

    # Load inverse scaler
    scaler_inv = load(open('../Consumption_estimation_Journal/scaler.pkl', 'rb'))

    # load random forest regressor
    r_forest_reg = load(open(path + '/Develops/Consumption_estimation_Journal/randomForest_0_04maxerr_model.pkl', 'rb'))

    columns = ['mean_max_power_usr', 'mean_soc', 'nominal_speed', 'slope']
    df_scaled = pd.DataFrame(scaler.transform(df_consolidated[columns]), columns=columns)

    # Para cada tramo de la ruta a estimar
    lst_kWh_per_km = []
    lst_kWh = []
    for i in range(len(df_consolidated)):

        print(df_consolidated.iloc[i])

        # Se calcula el consumo para el segmento en unidades escaladas
        c_scaled = r_forest_reg.predict(df_scaled.iloc[i].values.reshape(1, -1))[0]

        # Se transforma el consumo escalado a unidades de kWh/km
        kWh_per_km = scaler_inv.data_min_[4] + (c_scaled / scaler_inv.scale_[4])
        lst_kWh_per_km.append(kWh_per_km)

        # Se calcula el consumo completo del segmento
        kWh = kWh_per_km * df_consolidated['distanceInMeters'].iloc[i] / 1000
        lst_kWh.append(kWh)

        try:
            # Se estima el estado de carga inicial del próximo segmento
            df_consolidated.mean_soc.iloc[i + 1] = df_consolidated.mean_soc.iloc[i] - kWh * 2.5

            # Se escala el soc de la proxima iteración
            df_scaled.mean_soc[i+1] = (df_consolidated.mean_soc.iloc[i + 1] - scaler.data_min_[1]) * scaler.scale_[1]

        except:
            break

    df_consolidated['consumptionkWh'] = lst_kWh
    df_consolidated['consumption_per_km'] = lst_kWh_per_km
    print('Consumo estimado', df_consolidated['consumptionkWh'].sum(), 'kWh')