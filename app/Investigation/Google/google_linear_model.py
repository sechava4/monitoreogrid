import datetime
import math
import os
from pickle import load

import geopy
import googlemaps
import networkx as nw
import numpy as np
import osmnx as ox
import pandas as pd
import plotly.graph_objects as go
import pytz

from app import app

gmaps = googlemaps.Client(key="AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI")


def moving_average(x, w):
    return np.convolve(x, np.ones(w), "valid") / w


def get_segments(g_json, n_segments=5):
    # The large segments taken from google
    steps = g_json[0]["legs"][0]["steps"]
    # steps=r['routes'][0]['legs'][0]['steps']
    g_df = pd.DataFrame(steps)

    final_df = pd.DataFrame()
    for index, row in g_df.iterrows():
        m = row["distance"]["value"]
        t = row["duration"]["value"]

        # kmh
        speed = (m / t) * 3.6
        n_segments = round(np.cbrt(m))
        line_path = gmaps.elevation_along_path(row["polyline"]["points"], n_segments)
        line_df = pd.DataFrame(line_path)
        line_df["m"] = m
        line_df["mean_speed"] = speed

        final_df = final_df.append(line_df)

    final_df.reset_index(drop=True, inplace=True)

    aux_loc = final_df["location"][1:].reset_index(drop=True)
    # Repita valor en la última posición
    aux_loc._set_value(len(aux_loc), g_df.iloc[-1]["end_location"])
    final_df["end_location"] = aux_loc

    # para la altitud
    aux_ele = final_df["elevation"][1:].reset_index(drop=True)
    # Repita valor en la última posición
    aux_ele._set_value(len(aux_ele), final_df["elevation"].iloc[-1])
    final_df["end_elevation"] = aux_ele

    end_lat = []
    end_lng = []
    distances = []
    slopes = []
    travel_time = []
    # Para cada polilinea se calculan las distancias entre los 10 puntos
    for line_index, line_row in final_df.iterrows():

        end_lat.append(line_row["end_location"]["lat"])
        end_lng.append(line_row["end_location"]["lng"])

        coord1 = (line_row["location"]["lat"], line_row["location"]["lng"])
        coord2 = (line_row["end_location"]["lat"], line_row["end_location"]["lng"])
        run = geopy.distance.great_circle(coord1, coord2).km
        travel_time.append(3600 * run / line_row["mean_speed"])

        rise = line_row["end_elevation"] - line_row["elevation"]
        distance = math.sqrt((run * 1000) ** 2 + rise ** 2)  # m
        distances.append(distance / 1000)  # km

        try:
            slope = math.atan(rise / (run * 1000))  # radians
        except ZeroDivisionError:
            slope = 0
        degree = (slope * 180) / math.pi

        slopes.append(degree)

    final_df["slope"] = slopes
    final_df["kms"] = distances
    final_df["end_lat"] = end_lat
    final_df["end_lng"] = end_lng
    final_df["travel_time"] = travel_time
    final_df["slope_cat"] = pd.cut(final_df["slope"], np.arange(-10, 10.1, 2.5))
    final_df["slope_cat"] = final_df["slope_cat"].astype("string")

    # final_df['slope_average'] = moving_average(final_df['slope'].to_numpy(), 3)

    fig = go.Figure(
        go.Scattermapbox(
            mode="markers+lines",
            lon=final_df["end_lng"],
            lat=final_df["end_lat"],
            marker={"size": 10},
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

    fig.show()
    # plotly.offline.plot(fig)
    final_df = final_df.reset_index(drop=True)
    return final_df


def calc_shortest_path(G, lat_o, lon_o, lat_d, lon_d):
    point_o = (lat_o, lon_o)
    point_d = (lat_d, lon_d)
    nearest_node_o = ox.distance.get_nearest_node(
        G, point_o, method="haversine", return_dist=True
    )
    nearest_node_d = ox.distance.get_nearest_node(
        G, point_d, method="haversine", return_dist=True
    )
    try:
        shortest_path = nw.algorithms.shortest_paths.weighted.dijkstra_path(
            G=G,
            source=nearest_node_o[0],
            target=nearest_node_d[0],
            weight="travel_time",
        )
        traffic_lights = 0
        for node in shortest_path:
            try:
                G.nodes[node]["highway"]
                traffic_lights += 1
            except Exception:
                pass

        return shortest_path, traffic_lights
    except Exception:
        return 0, 0


def calculate_consumption(
    segments,
    path=os.path.join(app.root_path) + "/Investigation/ConsumptionEstimationJournal",
    model="linear",
    soc=70,
    user="Santiago_Echavarria_01",
):
    segments["id"] = segments.index
    segments = segments.sort_values(by=["id"])
    segments["mass"] = 1604
    segments["user_id"] = user
    # segments['user_id'] = 'Jose_Alejandro_Montoya'

    mean_features_by_slope = pd.read_csv(
        path + "/UserDrivingData/mean_features_by_slope.csv"
    )
    mean_features_by_user_and_slope = pd.read_csv(
        path + "/UserDrivingData/mean_features_by_user_and_slope.csv"
    )

    # Convert to string osm_data type for the inner join
    mean_features_by_user_and_slope["slope_cat"] = mean_features_by_user_and_slope[
        "slope_cat"
    ].astype("string")
    mean_features_by_slope["slope_cat"] = mean_features_by_slope["slope_cat"].astype(
        "string"
    )

    print("no of segments", len(segments))

    segments_consolidated = pd.merge(
        left=segments,
        right=mean_features_by_slope,
        left_on=["slope_cat"],
        right_on=["slope_cat"],
    )

    segments_consolidated = pd.merge(
        left=segments_consolidated,
        right=mean_features_by_user_and_slope,
        left_on=["slope_cat", "user_id"],
        right_on=["slope_cat", "user_id"],
    )

    segments_consolidated["mean_max_power_usr"] = segments_consolidated.apply(
        lambda row: row["mean_max_power"]
        if np.isnan(row["mean_max_power_usr"])
        else row["mean_max_power_usr"],
        axis=1,
    )

    segments_consolidated["mean_min_power_usr"] = segments_consolidated.apply(
        lambda row: row["mean_min_power"]
        if np.isnan(row["mean_min_power_usr"])
        else row["mean_min_power_usr"],
        axis=1,
    )

    segments_consolidated["mean_consumption_per_km_usr"] = segments_consolidated.apply(
        lambda row: row["mean_consumption_per_km"]
        if np.isnan(row["mean_consumption_per_km_usr"])
        else row["mean_consumption_per_km_usr"],
        axis=1,
    )

    segments_consolidated["mean_soc"] = soc

    # Apply scaling
    scaler = load(open(path + "/MachineLearningModels/scaler_lm.pkl", "rb"))

    columns = [
        "mean_max_power_usr",
        "mean_soc",
        "mean_speed",
        "slope",
        "mean_min_power_usr",
        "mean_consumption_per_km_usr",
    ]

    segments_scaled = pd.DataFrame(
        scaler.transform(segments_consolidated[columns]), columns=columns
    )

    # Load inverse scaler
    scaler_inv = load(open(path + "/MachineLearningModels//scaler.pkl", "rb"))

    # load random forest regressor
    r_forest_reg = load(
        open(
            path
            + "/MachineLearningModels/randomForest_0_3_mean_consumption_maxerr_model.pkl",
            "rb",
        )
    )

    # Load XGBoost model
    xgb_reg = load(open(path + "/MachineLearningModels/xg_reg_model.pickle.dat", "rb"))

    # Load linear model
    lm_cons = load(open(path + "/MachineLearningModels/linear_model.pkl", "rb"))

    # Load linear model
    linear_regr_sklearn = load(
        open(path + "/MachineLearningModels/linear_regr_sklearn.pkl", "rb")
    )

    # load ANN regressor
    ann_reg = load(open(path + "/MachineLearningModels/ann_regr.pkl", "rb"))

    models = {
        "linear": linear_regr_sklearn,
        "RF": r_forest_reg,
        "XGB": xgb_reg,
        "ANN": ann_reg,
    }

    # # Para cada tramo de la ruta a estimar consumo y restarselo al soc siguiente
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

    # segments_consolidated['consumptionkWh'] = lst_kWh
    # segments_consolidated['consumption_per_km'] = lst_kWh_per_km

    for mod in models:
        # if mod == 'linear':
        #     segments_consolidated['consumption_per_km_lm'] = 0.0598 * segments_consolidated['slope'] + \
        #                                                      0.0023 * segments_consolidated['mean_max_power_usr'] + \
        #                                                      0.0004 + segments_consolidated['mean_soc'] + \
        #                                                      0.0005 * segments_consolidated['mean_speed']
        #
        #     segments_consolidated['consumptionWh_lm'] = segments_consolidated['consumption_per_km_lm'] * \
        #                                                 segments_consolidated['kms']
        #
        # else:
        segments_scaled["consumption_per_km"] = models[mod].predict(
            segments_scaled[columns].values
        )

        # Apply inverse scaling
        p_pred = pd.DataFrame(
            scaler_inv.inverse_transform(segments_scaled),
            columns=segments_scaled.columns,
        )
        segments_consolidated["consumption_per_km_" + mod] = (
            p_pred["consumption_per_km"] * 1000
        )

        segments_consolidated["consumptionWh_" + mod] = (
            segments_consolidated["consumption_per_km_" + mod]
            * segments_consolidated["kms"]
        )

    estimated_time = segments_consolidated["travel_time"].sum() / 60
    return (
        (segments_consolidated["consumptionWh_linear"].sum() / 1000).round(3),
        estimated_time.round(3),
        segments_consolidated,
    )


if __name__ == "__main__":
    path = os.path.join(app.root_path) + "/Investigation/ConsumptionEstimationJournal"
    now = datetime.datetime.now(pytz.timezone("America/Bogota"))
    test_date = datetime.datetime.strptime("2020-08-12 10:26:45", "%Y-%m-%d %H:%M:%S")
    a = gmaps.directions(
        origin=(6.201123674133, -75.5757960580202),
        destination=(6.1976485409797535, -75.55707688749959),
        mode="driving",
        alternatives=False,
        departure_time=now,
        traffic_model="optimistic",
    )

    df = get_segments(a)

    consumption, time, df = calculate_consumption(
        segments=df, path=path, model="RF", soc=100, user="Santiago_Echavarria_01"
    )

    print("Consumo estimado", consumption, "kWh")
