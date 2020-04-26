import pandas as pd
import os
from app import app
import geopandas as gpd
import matplotlib as plt
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from rq import get_current_job
from app import db
from app.models import Task



def get_stations():
    file = os.path.join(app.root_path, "stations.json")
    df = pd.read_json(file)
    df.columns = ["name","latitude","longitude", "charger_types"]
    df = df[["name","latitude","longitude"]]
    return df


def get_lines(day):
    file = os.path.join(app.root_path, "rutas.csv")
    df = pd.read_csv(file, index_col="id")
    df = df[["longitude", "latitude", "day"]]

    df = df[df["day"] == int(day)]
    df = df.reset_index(drop=True)

    lat2 = df["latitude"].iloc[1:]
    lat2 = lat2.append(pd.Series(df["latitude"].iloc[-1]), ignore_index=True)
    df["latitude2"] = lat2

    lon2 = df["longitude"].iloc[1:]
    lon2 = lon2.append(pd.Series(df["longitude"].iloc[-1]), ignore_index=True)
    df["longitude2"] = lon2
    df = df.drop(df.tail(1).index)
    df = df.drop(df.head(1).index)
    return df


def get_zones():
    file = os.path.join(app.root_path, 'zones.csv')
    zones = pd.read_csv(file)
    zones = zones[["name", "longitude", "latitude"]]
    return zones


def concat(df1, df2):
    result = pd.concat([df1, df2], axis=1, join='inner')
    return result


def filter_by_column_value(df, colname, value):
    s= df[df[colname] == value]
    return s


def pretty_var_name(var_name):
    doc_var = os.path.join(app.root_path, "variables.csv")
    variables = pd.read_csv(doc_var, index_col="id")
    return variables.var_pretty[variables['var'] == var_name].values[0]


def form_var(titles):
    doc_var = os.path.join(app.root_path, "variables.csv")
    variables = pd.read_csv(doc_var, index_col="id")
    groups_list = []
    for i in range(len(variables)):
        if (variables["var"][i]) in titles:
            if (variables["var"][i]) == "longitude":
                continue
            if (variables["var"][i]) == "latitude":
                continue
            groups_list.insert(i, [(variables["var"][i]), (variables["var_pretty"][i])])
    return groups_list


def alturas_df(var, day):
    doc = os.path.join(app.root_path, 'rutas.csv')
    df = pd.read_csv(doc, index_col="id")
    df = df[df["day"] == int(day)]
    if var not in df.columns:
        var = "elevation"
    df = df[["latitude", "longitude", var]]
    if var == "elevation":
        df["name"] = df[var]
        df[var] = df[var].map(lambda x: x-1520)
    return df


def point_in_zone(day):
    _set_task_progress(0)
    doc_var = os.path.join(app.root_path, "ZONAS SIT_2017/ZONAS SIT_2017.shp")
    gdf = gpd.read_file(doc_var)

    alturas = alturas_df("elevation", day)
    alturas = alturas[["latitude", "longitude"]]
    points_df = alturas.iloc[-2:-1]
    points_gdf = gpd.GeoDataFrame(
        points_df, geometry=gpd.points_from_xy(points_df.longitude, points_df.latitude))

    a = gdf["geometry"].contains(points_gdf["geometry"].values[0])
    _set_task_progress(0)
    return gdf.Nueva_Zona[a == True], gdf.Municipio[a == True]


def _set_task_progress(progress):
    job = get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        task = Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()


if __name__ == '__main__':
    id, municipio = point_in_zone(1)
    id = id.item()
    municipio = municipio.item()


    # gdf.to_file("zones.geojson", driver="GeoJSON")
    #fig, ax = plt.subplots(1, 1)
    #df.plot(column="Nueva_Zona", ax=ax, legend=True)
    # rutas2 = pd.read_csv(doc2, index_col="id")
    # rutas2 = rutas2[["accelerationX","accelerationY","accelerationZ", "Time_2", "dia"]]
    # df.to_csv("variables.csv")

    # s.to_csv("rutas.csv")
    # df = rutas[rutas.elevation.notnull()]

    # OD = OD[["zone", "name","lat","lon"]]
    # OD['zone'] = OD['zone'].map(lambda x: str(x).replace("Z",""))
    # OD["zone"] = OD["zone"].astype(float)
    # OD = OD.sort_values(by=["zone"])

    # OD.drop_duplicates(subset="zone", inplace=True)
    # s = df.var_pretty[df['var']=="speed"].values[0]
    # df = df[0:20]







