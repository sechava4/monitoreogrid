import os

import pandas as pd
from pickle import load

from managev_app import app
from managev_app.Research.DataInteractor.data_fetcher import DataFetcher
from managev_app.Research.DegradationSimulation.Charging.PiecewiseTimeSlots import (
    Piecewise,
)
from managev_app.Research.DrivingClassification.cluster import DrivingClassifier
from managev_app.Research.DrivingClassification.road_clustering import RoadClassifier
from managev_app.Research.DegradationSimulation.MarcovChain.MarcovChain import (
    MarcovChain,
    VehicleSimulator,
)


def common_states(segments_df):
    """
    This function aims to create a dataframe of common
    states between the 2 clusters (aggressive vs non aggressive).

    common states are idle, charging, and driving out out those states
    """
    result = []
    indexes = []
    common = ["idle", "charging"]
    first = True
    for index, row in segments_df.iterrows():
        if first:
            first = False
            prev_row = row
            continue
        prev_state = prev_row["vehicle_state"]
        state = row["vehicle_state"]
        if state in common or (state == "driving" and prev_state in common):
            result.append(row)
            indexes.append(index)

        prev_row = row
    return pd.DataFrame(result, index=indexes)


print("Enter file prefix")
# name = input()
name = "renault"

data_path = os.path.join(app.root_path, "DataBackup", name)
models_path = os.path.join(
    os.path.dirname(__file__),
    "../ConsumptionEstimation",
    "MachineLearningModels",
)

try:
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments")
    # loaded_data = pd.read_hdf(data_path + "_data.h5", key=name + "_updated_df_operation")
    # segments = gen_traces(loaded_data)

except (FileNotFoundError, KeyError):
    print("Enter query")
    query = (
        input()
        or "select * from operation where "
        "vehicle_id in ('GHW284', 'GVQ446', 'EGZ112') and "
        "elevation is not null order by vehicle_id desc;"
    )
    print(query)
    data_fetcher = DataFetcher()
    data_fetcher.upload_data_to_h5(name=name, query=query)
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments")


# common states are idle and charging
common_states = common_states(segments)
driving_segments = segments.loc[segments.index.difference(common_states.index)]
driving_classifier = DrivingClassifier(segments=driving_segments)
driving_segments["driving_cluster"] = driving_classifier.cluster_labels

scaler = load(open(os.path.join(models_path, "scaler_lm.pkl"), "rb"))
scaler_inv = load(open(os.path.join(models_path, "scaler.pkl"), "rb"))
consumption_model = load(
    open(os.path.join(models_path, "linear_regr_sklearn.pkl"), "rb")
)

chains = {}
for driving_style in driving_classifier.cluster_labels.unique():
    drivers = driving_segments[driving_segments["driving_cluster"] == driving_style]
    drivers = drivers.append(common_states)
    road_classifier = RoadClassifier(drivers)
    charge_simulator = Piecewise()
    vehicle = VehicleSimulator(charge_simulator=charge_simulator)
    vehicle.set_charge_levels(road_classifier.road_segments)
    chain = MarcovChain(
        vehicle=vehicle,
        segments=road_classifier.road_segments,
        scaler=scaler,
        scaler_inv=scaler_inv,
        model=consumption_model,
    )
    chains[driving_style] = chain
