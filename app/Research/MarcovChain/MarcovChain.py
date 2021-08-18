from collections import defaultdict
from numpy.random import default_rng
from scipy import stats
import matplotlib.pyplot as plt


rng = default_rng()


class MarcovChain:
    def __init__(self, segments, scaler=None, scaler_inv=None, model=None):
        self.scaler = scaler
        self.scaler_inv = scaler_inv
        self.model = model
        self.counters = defaultdict(int)
        self.attr_names = ["max_power", "min_acc", "mean_speed", "slope", "kms"]
        road_cluster_labels = segments.road_clusters
        prev = road_cluster_labels.iloc[0]
        for x in road_cluster_labels.iloc[1:]:
            self.counters[f"{prev}_{x}"] += 1
            prev = x

        self.transition_probs = {}
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
                    if attr == "mean_speed":
                        shape, floc, scale = stats.lognorm.fit(data)
                        generator[attr] = {
                            "method": stats.lognorm,
                            "shape": shape,
                            "floc": floc,
                            "scale": scale,
                        }
                    elif attr == "kms":
                        shape, floc, scale = stats.pareto.fit(data)
                        generator[attr] = {
                            "method": stats.pareto,
                            "shape": shape,
                            "floc": floc,
                            "scale": scale,
                        }
                    elif attr == "slope":
                        mu, sigma = stats.norm.fit(data)
                        generator[attr] = {
                            "method": stats.norm,
                            "mu": mu,
                            "sigma": sigma,
                        }
                    # max_power and min_acc
                    else:
                        generator[attr] = data.mean()
                self.road_attr[road_type] = var
                self.generators[road_type] = generator

            n = road_cluster_labels[road_cluster_labels == road_type].count()
            state_prob = {
                key: val / n
                for key, val in self.counters.items()
                if key.startswith(str(road_type))
            }
            self.transition_probs[road_type] = state_prob

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
                shape, floc, scale = stats.pareto.fit(data)
                _, bins, _ = plt.hist(data, 20, density=1, alpha=0.5)
                best_fit_line = stats.pareto.pdf(bins, shape, floc, scale)
            else:
                shape, floc, scale = stats.lognorm.fit(data)
                _, bins, _ = plt.hist(data, 20, density=1, alpha=0.5)
                best_fit_line = stats.lognorm.pdf(bins, shape, floc, scale)

            plt.plot(bins, best_fit_line)
            plt.show()

    def generate_values(self, road_type):
        values = {}
        for attr, generator in self.generators.get(road_type).items():
            if attr in {"min_acc", "max_power"}:
                values[attr] = generator
                continue
            # We create a copy since we are popping the method
            gen_copy = generator.copy()
            method = gen_copy.pop("method")
            # if attr == "kms"
            #     limitar segun rango del vehiculo
            values[attr] = method.rvs(*tuple(gen_copy.values()))
        return values

    def compute_consumption(self, road_type):
        values = self.generate_values(road_type).copy()
        print(values)
        kms = values.pop("kms")
        scaled_values = self.scaler.transform([list(values.values())])
        consumption = self.model.predict(scaled_values)
        kWh_per_km = self.scaler_inv.data_min_[4] + (
            consumption / self.scaler_inv.scale_[4]
        )
        kWh = kWh_per_km * kms
        return kWh[0]

    def decide_transition(self, current_state):
        transition_states = [
            transition.split("_")[1]
            for transition in self.transition_probs.get(current_state).keys()
        ]

        transition_probabilities = list(self.transition_probs.get(current_state).values())
        # normalize
        transition_probabilities /= sum(transition_probabilities)

        next_state = rng.choice(a=transition_states, p=transition_probabilities)
        return next_state

    def random_walk(self, state="idle", energy=40, iterations=10):
        for i in range(iterations):
            if state.isdigit():
                energy -= self.compute_consumption(state)
                # degration += self.compute_degradation(state)
            state = self.decide_transition(state)

        return energy