from collections import defaultdict

from scipy import stats

stats


class MarcovChain:
    def __init__(self, road_cluster_labels):
        self.counters = defaultdict(int)
        prev = road_cluster_labels.iloc[0]
        for x in road_cluster_labels.iloc[1:]:
            self.counters[f"{prev}_{x}"] += 1
            prev = x

        self.prob = {}
        for road_type in road_cluster_labels.unique():
            n = road_cluster_labels[road_cluster_labels == road_type].count()
            state_prob = {
                key: val / n
                for key, val in self.counters.items()
                if key.startswith(str(road_type))
            }
            self.prob[road_type] = state_prob


if __name__ == "__main__":
    import pandas as pd
    import os
    from app import app

    name = "renault"  # input()
    data_path = os.path.join(app.root_path) + "/DataBackup/" + name
    segments = pd.read_hdf(data_path + "_data.h5", key=name + "_segments_degradation")
    chain = MarcovChain(segments.road_clusters)
