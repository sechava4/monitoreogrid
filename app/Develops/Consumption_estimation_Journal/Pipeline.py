import seaborn as sns
import addcopyfighandler
import pandas as pd
import numpy as np
import osmnx as ox
import networkx as nw

import sklearn
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
import mysql.connector

import matplotlib.pyplot as plt

from scipy import integrate, stats

from app import app

import TraceFeatures

# Regression models
import statsmodels.stats as sms
import statsmodels.api as sm
from statsmodels.formula.api import ols
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
# from app.models import OSM
# Save model
import pickle

import app.Develops.OpenStreetMaps.associate_edges_to_operation as associate


if __name__ == '__main__':

    cnx = mysql.connector.connect(user='admin', password='actuadores',
                                  host='157.230.209.3',
                                  database='monitoreodb')

    print('conexión ok db')
    query = "SELECT * from operation WHERE vehicle_id = 'FVQ731'"
    FVQ731 = pd.read_sql_query(query, cnx, index_col='id')
    FVQ731.dropna(axis=1, how='all', inplace=True)

    UG = ox.get_undirected(OSM.G).edges(keys=True, data=True)
    print('Convierte el grafo')

    FVQ731.dropna(subset=['power_kw', 'odometer'], inplace=True)
    FVQ731 = associate.add_osmn_attributes(FVQ731, UG, OSM.G)

    # Se eliminan saltos muy grandes donde no se enviaron datos
    FVQ731 = FVQ731[FVQ731['run'] < 1000]
    FVQ731['odometer_calc'] = FVQ731['run'].cumsum()

    FVQ731 = TraceFeatures.gen_test_traces(FVQ731)
    classifier_FVQ731 = FVQ731[FVQ731['trace_id'] > 0]
    segments = FVQ731.groupby(['trace_id'])

    lst = []
    for index, trace in segments:
        if index > 0 and len(trace) > 1:
            lst.append(TraceFeatures.feature_extraction(trace))

    features = TraceFeatures.generate_features_df(lst)
    features['cumdist'] = features.kms.cumsum()
    features['slope_cat'] = pd.cut(features["slope"], np.arange(-10, 10.1, 4)).astype('string')
    m = features[features['cumdist'] < 40]

    slope_user_groups = m.groupby(by=['slope_cat', 'user_id'])
    mean_features_by_user_and_slope = slope_user_groups[['max_power']].mean().reset_index()
    mean_features_by_user_and_slope.rename(columns={"max_power": "mean_max_power_usr"}, inplace=True)

    mean_features_by_user_and_slope.to_csv('mean_features_santiago.csv')
    TraceFeatures.map_plot(m, m, 1)