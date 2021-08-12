from collections import defaultdict

from scipy import stats
import matplotlib.pyplot as plt


class MarcovChain:
    def __init__(self, segments):
        self.counters = defaultdict(int)
        self.attr_names = ["mean_speed", "slope", "kms"]
        road_cluster_labels = segments.road_clusters
        prev = road_cluster_labels.iloc[0]
        for x in road_cluster_labels.iloc[1:]:
            self.counters[f"{prev}_{x}"] += 1
            prev = x

        self.prob = {}
        self.road_attr = {}
        self.generators = {}
        for road_type in road_cluster_labels.unique():
            # if its a driving state
            if road_type.isdigit():
                var = {}
                generator = {}
                for attr in self.attr_names:
                    data = segments[attr][segments.road_clusters == road_type]
                    var[attr] = data
                    if attr == "kms":
                        loc, scale = stats.expon.fit(data)
                        generator[attr] = {
                            "method": stats.expon,
                            "loc": loc,
                            "scale": scale,
                        }
                    elif attr == "mean_speed":
                        shape, floc, scale = stats.lognorm.fit(data)
                        generator[attr] = {
                            "method": stats.lognorm,
                            "shape": shape,
                            "floc": floc,
                            "scale": scale,
                        }
                    else:
                        mu, sigma = stats.norm.fit(data)
                        generator[attr] = {
                            "method": stats.norm,
                            "mu": mu,
                            "sigma": sigma,
                        }
                self.road_attr[road_type] = var
                self.generators[road_type] = generator

            n = road_cluster_labels[road_cluster_labels == road_type].count()
            state_prob = {
                key: val / n
                for key, val in self.counters.items()
                if key.startswith(str(road_type))
            }
            self.prob[road_type] = state_prob

    def plot_road_cluster_attributes(self, road_cluster):
        for attr in self.attr_names:
            plt.figure()
            data = self.road_attr.get(road_cluster, {}).get(attr)
            plt.title(f"fitted dist for {attr}")
            if attr == "slope":

                mu, sigma = stats.norm.fit(data)
                _, bins, _ = plt.hist(data, 20, density=1, alpha=0.5)
                best_fit_line = stats.norm.pdf(bins, mu, sigma)

            elif attr == "kms":

                loc, scale = stats.expon.fit(data)
                _, bins, _ = plt.hist(data, 20, density=1, alpha=0.5)
                best_fit_line = stats.expon.pdf(bins, loc, scale)

            else:
                shape, floc, scale = stats.lognorm.fit(data)
                _, bins, _ = plt.hist(data, 20, density=1, alpha=0.5)
                best_fit_line = stats.lognorm.pdf(bins, shape, floc, scale)

            plt.plot(bins, best_fit_line)
            plt.show()

    def random_walk(self):
        pass

    def generate_values(self, road_type):
        values = {}
        for attr, generator in self.generators.get(road_type).items():
            # We create a copy since we are popping the method
            gen_copy = generator.copy()
            method = gen_copy.pop("method")
            values[attr] = method.rvs(*tuple(gen_copy.values()))
        return values
