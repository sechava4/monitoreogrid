import pandas as pd
import numpy as np
from managev_app import app
import os
import TraceFeatures

# import PlotPath
import plotly.graph_objects as go
import plotly
import time
from pickle import load
from sklearn.metrics import mean_squared_error
import statsmodels.api as sm

path = os.path.join(app.root_path)

# Data cleaning

op = pd.read_csv(path + "/DataBackup/mixed_operation.csv")
op = op.dropna(subset=["power_kw", "odometer"])
# op = op[(op['vehicle_id'] == 'FSV110') | (op['vehicle_id'] == "GHW284")]

# Only valid conditions for testing: Donde manejé aparte de las pruebas en el alquiler de diciembre
op = op[(op["vehicle_id"] == "GHW284")]
op = op[(op["user_id"] == "Santiago_Echavarria")]

op = op[(op["odometer"] > 1)]
op = op[(op["power_kw"] != 0)]
op = op[op["operative_state"] < 3]

op_trace_test_index = TraceFeatures.gen_test_traces(op)

classifier_df = op_trace_test_index[op_trace_test_index["trace_id"] > 0]
segments = classifier_df.groupby(["trace_id"])

# df_to_consolidate = op_trace_test_index[op_trace_test_index['test_id'] > 0]
# df_to_test = op_trace_test_index[op_trace_test_index['test_id'] < 0]


# ------------------------- Measuring and testing groups generation ---------------------------------------#

lst = []
for index, trace in segments:
    if index > 0 and len(trace) > 1:
        lst.append(TraceFeatures.feature_extraction(trace))

features = TraceFeatures.generate_features_df(lst)


features = features[features["kms"] <= 1.3]
features = features[(features["max_current"] < 250)]
features = features[(features["traffic_factor"] < 45)]
features = features[features["max_power"] != 0]
features = features[features["std_acc"] != 0]
features = features[features["travel_time"] < 500]
features = features[~((features["slope"] < 0) & (features["max_power"] > 50))]


# Solo donde manejó Santiago Echavarría
features["cumdist"] = features[
    (features["user_id"] == "Santiago_Echavarria")
].kms.cumsum()
features.loc[features["cumdist"] < 25, "user_id"] = "Santiago_Echavarria_measure1"
features.loc[
    features["cumdist"].between(25, 105), "user_id"
] = "Santiago_Echavarria_test1"

features.loc[
    features["cumdist"].between(105, 130), "user_id"
] = "Santiago_Echavarria_measure2"
features.loc[features["cumdist"] > 130, "user_id"] = "Santiago_Echavarria_test2"

# Assign the slope categorical variable
features["slope_cat"] = pd.cut(features["slope"], np.arange(-10, 10.1, 4)).astype(
    "string"
)

# Load the mean features for all users
mean_features_by_slope = pd.read_csv(
    path + "/Develops/ConsumptionEstimation/mean_features_by_slope.csv"
)

mean_features_by_slope["slope_cat"] = mean_features_by_slope["slope_cat"].astype(
    "string"
)


def test(p, m):

    # Generate differentiated user attributes from measured segments
    slope_user_groups = m.groupby(by=["slope_cat", "user_id"])
    mean_features_by_user_and_slope = (
        slope_user_groups[["max_power", "min_power", "consumption_per_km"]]
        .mean()
        .reset_index()
    )
    mean_features_by_user_and_slope.rename(
        columns={
            "max_power": "mean_max_power_usr",
            "min_power": "mean_min_power_usr",
            "consumption_per_km": "mean_consumption_per_km_usr",
        },
        inplace=True,
    )

    mean_features_by_user_and_slope["user_id"] = p.user_id.unique()[0]
    p = pd.merge(
        how="left",
        left=p,
        right=mean_features_by_user_and_slope,
        left_on=["user_id", "slope_cat"],
        right_on=["user_id", "slope_cat"],
    )

    # -------------------------- Add mean for all users atributes to prediction dataset--------------------------------------------
    p = pd.merge(
        how="left",
        left=p,
        right=mean_features_by_slope,
        left_on=["slope_cat"],
        right_on=["slope_cat"],
    )

    p["mean_max_power_usr"] = p.apply(
        lambda row: row["mean_max_power"]
        if np.isnan(row["mean_max_power_usr"])
        else row["mean_max_power_usr"],
        axis=1,
    )

    # p['mean_soc'] = p['mean_soc'].iloc[0]
    # row['mean_soc'] = row['mean_soc'] + (pred * 2.5)

    # Apply scaling

    scaler = load(open(path + "/Develops/ConsumptionEstimation/scaler_lm.pkl", "rb"))
    columns = ["mean_max_power_usr", "mean_soc", "mean_speed", "slope"]
    p_scaled = pd.DataFrame(scaler.transform(p[columns]), columns=columns)
    p_scaled = p_scaled.dropna()

    # Load linear model
    lm_cons = sm.load(path + "/Develops/ConsumptionEstimation/lm_consumo.pickle")
    lm_cons = load(
        open(path + "/Develops/ConsumptionEstimation/linear_model.pkl", "rb")
    )

    # load random forest regressor
    r_forest_reg = load(
        open(
            path
            + "/Develops/ConsumptionEstimation/randomForest_0_16_mean_consumption_maxerr_model.pkl",
            "rb",
        )
    )

    # Load XGBoost model
    xgb_reg = load(
        open(
            path + "/Develops/ConsumptionEstimation/xg_reg_model.pickle.dat",
            "rb",
        )
    )

    # load ANN regressor
    ann_reg = load(open(path + "/Develops/ConsumptionEstimation/ann_regr.pkl", "rb"))

    # Apply linear model
    # p_scaled['consumption_per_km'] = lm_cons.predict(p_scaled)
    # p_scaled['consumption_per_km'] = 0.873 * p_scaled['slope'] + 0.1295 * p_scaled['mean_max_power_usr'] - 0.0721 * \
    #                                  p_scaled['mean_speed']

    p_scaled["consumption_per_km"] = r_forest_reg.predict(
        p_scaled[["mean_max_power_usr", "mean_soc", "mean_speed", "slope"]].values
    )

    # For linear model
    # p_scaled['consumption_per_km'] = lm_cons.predict(
    #     p_scaled[['mean_max_power_usr', 'mean_soc', 'mean_speed', 'slope']])

    # Load inverse scaler
    scaler_inv = load(open(path + "/Develops/ConsumptionEstimation/scaler.pkl", "rb"))

    # Apply inverse scaling
    p_pred = pd.DataFrame(
        scaler_inv.inverse_transform(p_scaled), columns=p_scaled.columns
    )

    p["consumption_per_km_pred"] = p_pred["consumption_per_km"]

    # Multiply by segment length
    p["consumption_pred"] = p["consumption_per_km_pred"] * p["kms"]

    # plot
    p["end_time"] = pd.to_datetime(p.end_time)
    p = p.sort_values(by=["end_time"])
    p = p[p["consumption_pred"] > -0.08]

    # Plots of estimated segment - by - segment (not accumulating)
    fig = go.Figure(
        [go.Scatter(x=p["kms"].cumsum(), y=p["consumption_pred"], name="Predicted")]
    )
    fig.add_trace(go.Scatter(x=p["kms"].cumsum(), y=p["consumption"], name="Measured"))
    fig.update_layout(
        title="Model evaluation for test route (segment by segment)",
        xaxis_title="km",
        yaxis_title="kWh/km",
    )
    plotly.offline.plot(fig)

    fig2 = go.Figure(
        [
            go.Scatter(
                x=p["kms"].cumsum(), y=p["consumption_pred"].cumsum(), name="Predicted"
            )
        ]
    )
    fig2.add_trace(
        go.Scatter(x=p["kms"].cumsum(), y=p["consumption"].cumsum(), name="Measured")
    )
    fig2.update_layout(
        title="Model evaluation for test route (cumulative consumption)",
        xaxis_title="km",
        yaxis_title="kWh",
    )
    plotly.offline.plot(fig2)

    error = (
        100
        * (p["consumption"].cumsum().iloc[-1] - p["consumption_pred"].cumsum().iloc[-1])
        / p["consumption"].cumsum().iloc[-1]
    )

    # error = mean_squared_error(p['consumption'].cumsum(), p['consumption_pred'].cumsum())

    return p


test_test1 = features[features["user_id"] == "Santiago_Echavarria_test1"]
test_test1 = test_test1[
    (test_test1.consumption < 0.6) & (test_test1.consumption > -0.3)
]
test_measure1 = features[features["user_id"] == "Santiago_Echavarria_measure1"]

e1 = test(test_test1, test_measure1)
e1.dropna(subset=["consumption_pred"], inplace=True)
TraceFeatures.map_plot(test_measure1, test_test1, 1)
rmse_kWh = np.sqrt(
    mean_squared_error(e1["consumption"].cumsum(), e1["consumption_pred"].cumsum())
)
rmse_kWh_km = np.sqrt(
    mean_squared_error(e1["consumption_per_km"], e1["consumption_per_km_pred"])
)

print("rmse_kWh", rmse_kWh)
print("rmse_kWh_km", rmse_kWh_km)

# A more aggresive segment

test_test2 = features[features["user_id"] == "Santiago_Echavarria_test2"]
test_test2 = test_test2[
    (test_test2.consumption < 0.6) & (test_test2.consumption > -0.3)
]
test_measure2 = features[features["user_id"] == "Santiago_Echavarria_measure2"]

e2 = test(test_test2, test_measure2)
e2.dropna(subset=["consumption_pred"], inplace=True)
e2["cumdist_km"] = e2.kms.cumsum()
TraceFeatures.map_plot(test_measure1, test_test2, 2)

rmse_kWh = np.sqrt(
    mean_squared_error(e2["consumption"].cumsum(), e2["consumption_pred"].cumsum())
)
rmse_kWh_km = np.sqrt(
    mean_squared_error(e2["consumption_per_km"], e2["consumption_per_km_pred"])
)

print("rmse_kWh", rmse_kWh)
print("rmse_kWh_km", rmse_kWh_km)


# # Some useful figures
# # To compare the mean_max_power with max power
# # To compare the mean_min_power with min power
#
# slope_user_groups = test_measure1.groupby(by=['slope_cat', 'user_id'])
# mean_features_by_user_and_slope = slope_user_groups[['max_power', 'min_power', 'consumption_per_km']].mean().reset_index()
# mean_features_by_user_and_slope.rename(columns={"max_power": "mean_max_power_usr", "min_power": "mean_min_power_usr",
#                                                 'consumption_per_km': 'mean_consumption_per_km_usr'}, inplace=True)
#
# test_measure = pd.merge(how='left', left=test_measure1, right=mean_features_by_user_and_slope,
#              left_on=['user_id', 'slope_cat'], right_on=['user_id', 'slope_cat'])
#
# fig3 = go.Figure([go.Scatter(x=test_measure['kms'].cumsum(), y=test_measure['max_power'], name='Measured max')])
# fig3.add_trace(go.Scatter(x=test_measure['kms'].cumsum(), y=test_measure['min_power'], name='Measured min'))
# fig3.add_trace(go.Scatter(x=test_measure['kms'].cumsum(), y=test_measure['mean_max_power_usr'], name='Mean_max'))
#
# fig3.add_trace(go.Scatter(x=test_measure['kms'].cumsum(), y=test_measure['mean_min_power_usr'], name='Mean_min'))
# fig3.update_layout(
#     title="max_power",
#     xaxis_title="km",
#     yaxis_title="kW")
# plotly.offline.plot(fig3)
