import os

import pandas as pd

from app import app
from app.Investigation.DataInteractor.data_fetcher import DataFetcher
from app.Investigation.DrivingClassification.road_clustering import RoadClassifier


def common_states(segments_df):
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
from app.Investigation.DrivingClassification.cluster import DrivingClassifier
from app.Investigation.MarcovChain.MarcovChain import MarcovChain

data_path = os.path.join(app.root_path) + "/DataBackup/" + name

try:
    loaded_data = pd.read_hdf(
        data_path + "_data.h5", key=name + "_updated_df_operation"
    )
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments")

except (FileNotFoundError, KeyError):
    print("Enter query")
    query = (
        input()
        or "select * from operation where vehicle_id in ('GHW284', 'GVQ446', 'EGZ112');"
    )
    print(query)
    data_fetcher = DataFetcher()
    data_fetcher.upload_data_to_h5(name, query)
    loaded_data = pd.read_hdf(
        data_path + "_data.h5", key=name + "_updated_df_operation"
    )
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments_degradation")

# common states are idle and charging

common_states = common_states(segments)
driving_segments = segments.loc[segments.index.difference(common_states.index)]
driving_classifier = DrivingClassifier(segments=driving_segments)
driving_segments["driving_cluster"] = driving_classifier.cluster_labels

chains = {}
for driving_style in driving_classifier.cluster_labels.unique():
    drivers = driving_segments[driving_segments["driving_cluster"] == driving_style]
    drivers = drivers.append(common_states)
    road_classifier = RoadClassifier(drivers)
    chain = MarcovChain(road_classifier.road_segments)
    chains[driving_style] = chain
