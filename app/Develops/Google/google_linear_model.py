# make sure you can connect to Google's server
import requests
import json
import itertools
import osmnx as ox
import geopy
import pandas as pd
import googlemaps
import datetime
import math
import pytz
import plotly.graph_objects as go
import plotly
import numpy as np
from pickle import load
import statsmodels.api as sm
import os
from app import app
import networkx as nw
import time



gmaps = googlemaps.Client(key='AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI')

locations = '-75.580855,6.151992; -75.579519,6.199303;  6.153764, -75.541675'
'''
url = 'https://maps.googleapis.com/maps/api/directions/json?' \
      'origin="6.151992,-75.580855"&destination="6.199303,-75.579519"&' \
      'key=AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI'

r = requests.get(url).json()
polyline_average = r['routes'][0]['overview_polyline']['points']
'''


def get_segments(json):
    steps = json[0]['legs'][0]['steps']
    # steps=r['routes'][0]['legs'][0]['steps']
    df = pd.DataFrame(steps)

    final_df = pd.DataFrame()
    for index, row in df.iterrows():
        m = row['distance']['value']
        s = row['duration']['value']

        # kmh
        speed = (m / s) * 3.6

        a = gmaps.elevation_along_path(row['polyline']['points'], 5)
        line_df = pd.DataFrame(a)

        # para la coordenada
        aux_loc = line_df['location'][1:].reset_index(drop=True)
        # Repita valor en la última posición
        aux_loc._set_value(len(aux_loc), line_df['location'].iloc[-1])
        line_df['end_location'] = aux_loc

        # para la altitud
        aux_ele = line_df['elevation'][1:].reset_index(drop=True)
        # Repita valor en la última posición
        aux_ele._set_value(len(aux_ele), line_df['elevation'].iloc[-1])
        line_df['end_elevation'] = aux_ele

        end_lat = []
        end_lng = []
        distances = []
        slopes = []
        travel_time = []
        # Para cada polilinea se calculan las distancias entre los 10 puntos
        for line_index, line_row in line_df.iterrows():

            end_lat.append(line_row['end_location']['lat'])
            end_lng.append(line_row['end_location']['lng'])

            coord1 = (line_row['location']['lat'], line_row['location']['lng'])
            coord2 = (line_row['end_location']['lat'], line_row['end_location']['lng'])
            run = geopy.distance.distance(coord1, coord2).km
            travel_time.append(3600 * run / speed)

            rise = line_row['end_elevation'] - line_row['elevation']
            distance = math.sqrt((run*1000) ** 2 + rise ** 2)  # m
            distances.append(distance/1000)  # km

            try:
                slope = math.atan(rise / (run * 1000))  # radians
            except ZeroDivisionError:
                slope = 0
            degree = (slope * 180) / math.pi

            slopes.append(degree)

        line_df['slope'] = slopes
        line_df['kms'] = distances
        line_df['mean_speed'] = speed
        line_df['end_lat'] = end_lat
        line_df['end_lng'] = end_lng
        line_df['travel_time'] = travel_time

        # La ultima queda con distancia 0
        line_df.drop(line_df.tail(1).index, inplace=True)

        final_df = final_df.append(line_df)

    fig = go.Figure(go.Scattermapbox(
        mode="markers+lines",
        lon=final_df['end_lng'],
        lat=final_df['end_lat'],
        marker={'size': 10}))

    fig.update_layout(
        margin ={'l': 0,'t': 0,'b': 0,'r': 0},
        mapbox = {
            'center': {'lon': -75.58, 'lat': 6.151},
            'style': "stamen-terrain",
            'zoom': 10})

    plotly.offline.plot(fig)

    return final_df.reset_index(drop=True)


def calc_shortest_path(G, lat_o, lon_o, lat_d, lon_d):
    point_o = (lat_o, lon_o)
    point_d = (lat_d, lon_d)
    nearest_node_o = ox.distance.get_nearest_node(G, point_o, method='haversine', return_dist=True)
    nearest_node_d = ox.distance.get_nearest_node(G, point_d, method='haversine', return_dist=True)
    try:
        shortest_path = nw.algorithms.shortest_paths.weighted.dijkstra_path(G=G, source=nearest_node_o[0],
                                                                            target=nearest_node_d[0],
                                                                            weight='travel_time')
        traffic_lights = 0
        for node in shortest_path:
            try:
                G.nodes[node]['highway']
                traffic_lights += 1
            except Exception:
                pass

        return shortest_path, traffic_lights
    except Exception:
        return 0, 0


def calculate_consumption(segments, path):

    segments["id"] = segments.index

    segments['mass'] = 1604
    # segments['user_id'] = 'Esterban_Betancur'
    segments['user_id'] = 'Santiago_Echavarria_01'
    segments['slope_cat'] = pd.cut(segments["slope"], np.arange(-10, 10.1, 5))

    mean_features_by_slope = pd.read_csv(path+'/mean_features_by_slope.csv')
    mean_features_by_user_and_slope = pd.read_csv(path+'/mean_features_by_user_and_slope.csv')

    # Convert to string data type for the inner join
    mean_features_by_user_and_slope['slope_cat'] = mean_features_by_user_and_slope['slope_cat'].astype('string')
    mean_features_by_slope['slope_cat'] = mean_features_by_slope['slope_cat'].astype('string')
    segments['slope_cat'] = segments['slope_cat'].astype('string')

    print('no of segments', len(segments))

    segments_consolidated = pd.merge(left=segments, right=mean_features_by_slope,
                                     left_on=['slope_cat'], right_on=['slope_cat'])

    segments_consolidated = pd.merge(left=segments_consolidated, right=mean_features_by_user_and_slope,
                                     left_on=['slope_cat', 'user_id'], right_on=['slope_cat', 'user_id'])

    segments_consolidated['mean_max_power_usr'] = segments_consolidated.apply(
        lambda row: row['mean_max_power'] if np.isnan(row['mean_max_power_usr']) else row['mean_max_power_usr'],
        axis=1
    )

    segments_consolidated['mean_soc'] = 50

    # Apply scaling
    scaler = load(open(path + '/scaler_lm.pkl', 'rb'))

    columns = ['mean_max_power_usr', 'mean_soc', 'mean_speed', 'slope']
    segments_scaled = pd.DataFrame(scaler.transform(segments_consolidated[columns]), columns=columns)

    # Load inverse scaler
    scaler_inv = load(open(path + '/scaler.pkl', 'rb'))

    # load random forest regressor
    r_forest_reg = load(open(path + '/randomForest_0_13_mean_consumption_maxerr_model.pkl', 'rb'))

    # Load XGBoost model
    xgb_reg = load(open(path + '/xg_reg_model.pickle.dat', "rb"))

    # Load linear model
    lm_cons = load(open(path + '/linear_model.pkl', 'rb'))

    # load ANN regressor
    ann_reg = load(open(path + '/ann_regr.pkl', 'rb'))
    #
    # # Para cada tramo de la ruta a estimar
    # lst_kWh_per_km = []
    # lst_kWh = []
    #
    # for i in range(len(segments_consolidated)):
    #
    #     # Se calcula el consumo para el segmento en unidades escaladas sklearn
    #     c_scaled = ann_reg.predict(segments_scaled.iloc[i].values.reshape(1, -1))[0]
    #
    #     # Se calcula el consumo para el segmento en unidades escaladas lineal
    #     # c_scaled = lm_cons.predict(segments_scaled.iloc[i])
    #
    #     # Se transforma el consumo escalado a unidades de kWh/km
    #     kWh_per_km = scaler_inv.data_min_[4] + (c_scaled / scaler_inv.scale_[4])
    #     lst_kWh_per_km.append(kWh_per_km)
    #
    #     # Se calcula el consumo completo del segmento
    #     kWh = kWh_per_km * segments_consolidated['distanceInMeters'].iloc[i] / 1000
    #     lst_kWh.append(kWh)
    #
    #     try:
    #         # Se estima el estado de carga inicial del próximo segmento
    #         segments_consolidated.mean_soc.iloc[i + 1] = segments_consolidated.mean_soc.iloc[i] - kWh * 2.5
    #
    #         # Se escala el soc de la proxima iteración
    #         segments_scaled.mean_soc[i + 1] = (segments_consolidated.mean_soc.iloc[i + 1] -
    #                                            scaler.data_min_[1]) * scaler.scale_[1]
    #
    #     except:
    #         break

    segments_consolidated['consumption_per_km'] = 66.478 * segments_consolidated['slope'] + \
                                                  2.274 * segments_consolidated['mean_max_power_usr'] + \
                                                  0.186 + segments_consolidated['mean_soc'] + \
                                                  1.102 * segments_consolidated['mean_speed']

    # segments_scaled['consumption_per_km'] = xgb_reg.predict(segments_scaled[columns].values)
    #
    # # Apply inverse scaling
    # p_pred = pd.DataFrame(scaler_inv.inverse_transform(segments_scaled), columns=segments_scaled.columns)
    # segments_consolidated['consumption_per_km'] = p_pred['consumption_per_km']

    segments_consolidated['consumptionWh'] = segments_consolidated['consumption_per_km'] * \
                                             segments_consolidated['kms']

    # segments_consolidated['consumptionkWh'] = lst_kWh
    # segments_consolidated['consumption_per_km'] = lst_kWh_per_km


    estimated_time = segments_consolidated['travel_time'].sum() / 60
    return (segments_consolidated['consumptionWh'].sum()/1000).round(3), estimated_time.round(3), segments_consolidated


if __name__ == '__main__':
    path = os.path.join(app.root_path) + '/Develops/Consumption_estimation_Journal'
    now = datetime.datetime.now(pytz.timezone('America/Bogota'))
    test_date = datetime.datetime.strptime('2020-08-12 10:26:45', '%Y-%m-%d %H:%M:%S')
    # Eafit to palmas
    a = gmaps.directions(origin=(6.1997762127391995, -75.5793285369873),
                         destination=(6.197557661928623, -75.55890083312988),
                         mode='driving', alternatives=False, departure_time=now, traffic_model='pessimistic')

    # b = gmaps.directions(origin=(6.199303, -75.579519), destination=(6.153382, -75.541652),
    #                      mode='driving', alternatives=False, departure_time=now, traffic_model='optimistic')

    df = get_segments(a)

    # Load OSM info ----------------------------------------

    # filepath = '../data/medellin.graphml'
    # G = ox.load_graphml(filepath)
    #
    # # Calculate number of traffic lights per segment
    # lights = []
    # for index, row in df.iterrows():
    #     a, b = calc_shortest_path(G, row['start_lat'], row['start_lng'], row['end_lat'], row['end_lng'])
    #     lights.append(b)
    # df['lights'] = pd.Series(lights)

    consumption, time, df = calculate_consumption(df, path)

    print('Consumo estimado', consumption, 'kWh')
