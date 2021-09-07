import os

import pandas as pd

from managev_app import app
from managev_app import db
from managev_app.models import Operation


def get_stations():
    file = os.path.join(app.root_path, "stations.json")
    df = pd.read_json(file)
    df.columns = ["name", "latitude", "longitude", "charger_types"]
    return df


def get_zones():
    file = os.path.join(app.root_path, "zones.csv")
    zones = pd.read_csv(file)
    zones = zones[["name", "longitude", "latitude"]]
    return zones


def concat(df1, df2):
    result = pd.concat([df1, df2], axis=1, join="inner")
    return result


def filter_by_column_value(df, colname, value):
    s = df[df[colname] == value]
    return s


def pretty_var_name(var_name):
    doc_var = os.path.join(app.root_path, "variables.csv")
    variables = pd.read_csv(doc_var, index_col="id")
    return variables.var_pretty[variables["var"] == var_name].values[0]


def form_var(titles):
    doc_var = os.path.join(app.root_path, "variables.csv")
    variables = pd.read_csv(doc_var, index_col="id")
    groups_list = []
    for i in range(len(variables)):
        if variables["var"][i] in titles:
            if variables["var"][i] in ["longitude", "latitude"]:
                continue
            groups_list.insert(i, [(variables["var"][i]), (variables["var_pretty"][i])])
    return groups_list


def get_lines(vehicle, d1, h1, h2):
    query = (
        "SELECT latitude, longitude from operation WHERE "
        ' latitude != 0 AND longitude != 0 AND vehicle_id = "'
        + str(vehicle.placa)
        + '" AND timestamp BETWEEN "'
        + str(d1)
        + " "
        + str(h1)[:8]
        + '" and "'
        + str(d1)
        + " "
        + str(h2)[:8]
        + '"'
    )

    df = pd.read_sql_query(query, db.engine)
    lat2 = df["latitude"].iloc[1:]
    if len(lat2) == 0:
        return df
    else:
        aux1 = lat2.append(pd.Series(df["latitude"].iloc[-1]), ignore_index=True)
        df["latitude2"] = aux1

        lon2 = df["longitude"].iloc[1:]
        aux2 = lon2.append(pd.Series(df["longitude"].iloc[-1]), ignore_index=True)
        df["longitude2"] = aux2
        df = df.drop(df.tail(1).index)
        df = df.drop(df.head(1).index)
        return df


def get_heights(vehicle, var, d1, h1, h2):

    query = (
        "SELECT timestamp, "
        + var
        + ', latitude, longitude from operation WHERE latitude != 0 AND longitude != 0 AND vehicle_id = "'
        + str(vehicle.placa)
        + '" AND timestamp BETWEEN "'
        + str(d1)
        + " "
        + str(h1)[:8]
        + '" and "'
        + str(d1)
        + " "
        + str(h2)[:8]
        + '"'
    )

    df = pd.read_sql_query(query, db.engine)
    if var not in df.columns:
        var = "elevation"

    if all(
        elem in df.columns for elem in ["latitude", "longitude", "timestamp", var]
    ) and len(df[var]):
        df = df[["latitude", "longitude", "timestamp", var]]
        df["name"] = df[var]
        if df[var].iloc[0]:
            if var in ("elevation", "elevation2"):
                df["var"] = df[var].map(lambda x: (x - 1400) * 0.5)
            elif var in ("mec_power_delta_e", "mec_power"):
                df["var"] = df[var].map(lambda x: x * 35)
            elif var in "mean_acc":
                df["var"] = df[var].map(lambda x: x * 45)
            elif var in "angle_x":
                df["var"] = df[var].abs()
            else:
                df["var"] = df[var].map(lambda x: x * 4)
            df = df[["latitude", "longitude", "name", "var", "timestamp"]]
    return df


if __name__ == "__main__":
    a = get_heights("elevation")
    titles = Operation.__dict__
    print(titles)
    b = form_var(titles)
