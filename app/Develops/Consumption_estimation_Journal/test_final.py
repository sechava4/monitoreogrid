import pandas as pd
import numpy as np
from app import app
import os
import TraceFeatures
# import PlotPath
import plotly.graph_objects as go
import plotly
import time
from pickle import load
import statsmodels.api as sm

path = os.path.join(app.root_path)

# Data cleaning
op = pd.read_csv(path + '/DataBackup/updated_vehicle_operation.csv')
op = op.dropna(subset=['power_kw', 'odometer'])
# op = op[(op['vehicle_id'] == 'FSV110') | (op['vehicle_id'] == "GHW284")]

# Only valid conditions for testing
op = op[(op['vehicle_id'] == 'GHW284')]
op = op[(op['user_id'] == 'Santiago_Echavarria')]

op = op[(op['odometer'] > 1)]
op = op[(op['power_kw'] != 0)]
op = op[op['operative_state'] < 3]


op.drop(columns=['placa'], inplace=True)


def gen_test_traces(df):
    try:
        df.drop(columns='Unnamed: 0', inplace=True)
        df.drop(columns='id', inplace=True)
    except KeyError:
        pass
    trace_id = 1
    aux_trace_id = -1

    consolidar_id = 1
    testear_id = -1
    test_array = np.array([])

    trace_array = np.array([])
    suma = 0
    suma_testing = 0
    old_name = ''
    old_date = df['timestamp2'].iloc[0]

    for index, row in df.iterrows():
        # for index, row in test.iterrows():
        suma = suma + row['run']
        suma_testing = suma_testing + row['run']
        # row['slope']
        trace_array = np.append(trace_array, aux_trace_id)

        nan = (row['name'] != row['name'])

        # feature traces of more than 100m
        if suma > 1200:
            trace_array = np.where(trace_array == aux_trace_id, trace_id, trace_array)

        # Si cambia de vía - empiece un nuevo tramo se escoge 1200 para ver cambios en consumo
        if suma >= 1200 or (old_name != row['name'] and not nan):  # pendiente
            suma = 0
            trace_id += 1
            aux_trace_id -= 1

        old_name = row['name']

    print(trace_array)
    try:
        df.drop(["trace_id"], axis=1, inplace=True)
    except KeyError:
        pass
    df.insert(2, "trace_id", trace_array, True)

    return df



op_trace_test_index = gen_test_traces(op)

classifier_df = op_trace_test_index[op_trace_test_index['trace_id'] > 0]
segments = classifier_df.groupby(['trace_id'])

#df_to_consolidate = op_trace_test_index[op_trace_test_index['test_id'] > 0]
#df_to_test = op_trace_test_index[op_trace_test_index['test_id'] < 0]


def map_plot(df_to_m, df_to_t,i):
    fig = go.Figure(go.Scattermapbox(
        mode="markers+lines",
        lon=df_to_m['longitude'],
        lat=df_to_m['latitude'],
        marker={'size': 10}))

    fig.add_trace(go.Scattermapbox(
        mode="markers+lines",
        lon=df_to_t['longitude'],
        lat=df_to_t['latitude'],
        marker={'size': 10}))

    fig.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        mapbox={
            'center': {'lon': -75.58, 'lat': 6.151},
            'style': "stamen-terrain",
            'zoom': 10}, title='test '+str(i))

    plotly.offline.plot(fig)
    time.sleep(2)


# ------------------------- Measuring and testing groups generation ---------------------------------------#

lst = []
for index, trace in segments:
    if index > 0 and len(trace) > 1:
        lst.append(TraceFeatures.feature_extraction(trace))

features = TraceFeatures.generate_features_df(lst)


features = features[features['kms'] <= 1.6]
features = features[(features['max_current'] < 250)]
features = features[(features['traffic_factor'] < 45)]
features = features[features['max_power'] != 0]
features = features[features['std_acc'] != 0]


features['cumdist'] = features[(features['user_id'] == 'Santiago_Echavarria')].kms.cumsum()
features.loc[features['cumdist'] > 25, 'user_id'] = 'Santiago_Echavarria_test'
features.loc[features['cumdist'] < 25, 'user_id'] = 'Santiago_Echavarria_measure'

# Assign the slope categorical variable
features['slope_cat'] = pd.cut(features["slope"], np.arange(-8.5, 8.6, 3.4)).astype('string')

# Load the mean power feature for all users
mean_max_pot_by_slope = pd.read_csv(path + '/Develops/Consumption_estimation_Journal/mean_max_power_by_slope.csv',
                                    index_col=0)
mean_max_pot_by_slope['slope_cat'] = mean_max_pot_by_slope['slope_cat'].astype('string')


def test(p, m):

    # Generate user attribute from measured segments
    slope_user_groups = m.groupby(by=['slope_cat', 'user_id'])
    mean_max_p_per_user_and_slope = slope_user_groups[['max_power']].mean().reset_index()
    mean_max_p_per_user_and_slope.rename(columns={"max_power": "mean_max_power_usr", 'slope': 'slope_cat'}, inplace=True)
    mean_max_p_per_user_and_slope['user_id'] = 'Santiago_Echavarria_test'
    p = pd.merge(how='left', left=p, right=mean_max_p_per_user_and_slope,
                 left_on=['user_id', 'slope_cat'], right_on=['user_id', 'slope_cat'])

    # -------------------------- Add atributes to prediction dataset--------------------------------------------
    p = pd.merge(how='left', left=p, right=mean_max_pot_by_slope,
                 left_on=['slope_cat'], right_on=['slope_cat'])

    p['mean_max_power_usr'] = p.apply(
        lambda row: row['mean_max_power'] if np.isnan(row['mean_max_power_usr']) else row['mean_max_power_usr'],
        axis=1)

    # p['mean_soc'] = p['mean_soc'].iloc[0]
    # row['mean_soc'] = row['mean_soc'] + (pred * 2.5)

    # Apply scaling
    scaler = load(open(path + '/Develops/Consumption_estimation_Journal/scaler_lm.pkl', 'rb'))
    columns = ['mean_max_power_usr', 'mean_soc', 'nominal_speed', 'slope']
    p_scaled = pd.DataFrame(scaler.transform(p[columns]), columns=columns)

    # Load linear model
    #lm_cons = sm.load(path + '/Develops/Consumption_estimation_Journal/lm_consumo.pickle')

    # load random forest regressor
    r_forest_reg = load(open(path + '/Develops/Consumption_estimation_Journal/randomForest_0_04maxerr_model.pkl', 'rb'))

    # load ANN regressor
    #ann_reg = load(open(path + '/Develops/Consumption_estimation_Journal/ann_regr.pkl', 'rb'))

    # Apply linear model
    # p_scaled['consumption_per_km'] = lm_cons.predict(p_scaled)
    # p_scaled['consumption_per_km'] = 0.873 * p_scaled['slope'] + 0.1295 * p_scaled['mean_max_power_usr'] - 0.0721 * \
    #                                  p_scaled['mean_speed']

    p_scaled['consumption_per_km'] = r_forest_reg.predict(p_scaled[['mean_max_power_usr', 'mean_soc',
                                                               'nominal_speed', 'slope']].values)

    # Load inverse scaler
    scaler_inv = load(open(path + '/Develops/Consumption_estimation_Journal/scaler.pkl', 'rb'))

    # Apply inverse scaling
    p_pred = pd.DataFrame(scaler_inv.inverse_transform(p_scaled), columns=p_scaled.columns)

    # Multiply by segment length
    p['consumption_pred'] = p_pred['consumption_per_km'] * p['kms']

    # plot
    p['end_time'] = pd.to_datetime(p.end_time)
    p = p.sort_values(by=['end_time'])

    # Plots of estimated segment - by - segment (not accumulating)
    fig = go.Figure([go.Scatter(x=p['kms'].cumsum(), y=p['consumption_pred'], name='Predicted')])
    fig.add_trace(go.Scatter(x=p['kms'].cumsum(), y=p['consumption'], name='Measured'))
    fig.update_layout(
            title="Model evaluation for test route (segment by segment)",
            xaxis_title="km",
            yaxis_title="kWh/km")
    plotly.offline.plot(fig)

    time.sleep(2)

    fig2 = go.Figure([go.Scatter(x=p['kms'].cumsum(), y=p['consumption_pred'].cumsum(), name='Predicted')])
    fig2.add_trace(go.Scatter(x=p['kms'].cumsum(), y=p['consumption'].cumsum(), name='Measured'))
    fig2.update_layout(
        title="Model evaluation for test route (cumulative consumption)",
        xaxis_title="km",
        yaxis_title="kWh/km")
    plotly.offline.plot(fig2)

    time.sleep(2)
    error = 100 * (p['consumption'].cumsum().iloc[-1] - p['consumption_pred'].cumsum().iloc[-1]) / \
            p['consumption'].cumsum().iloc[-1]

    print('error =', abs(error), '%')

    return abs(error)


test_test = features[features['user_id'] == 'Santiago_Echavarria_test']
test_measure = features[features['user_id'] == 'Santiago_Echavarria_measure']

# map_plot(plot_consolidate, plot_test, 1)
e = test(test_test, test_measure)

