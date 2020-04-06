import pandas as pd
import os
from app import app


def get_stations():
    file = os.path.join(app.root_path, "stations.json")
    df = pd.read_json(file)
    df.columns = ["name","latitude","longitude", "charger_types"]
    return df


def get_zones():
    file = os.path.join(app.root_path, 'zones.csv')
    zones = pd.read_csv(file)
    zones = zones[["name", "lon", "lat"]]
    return zones


def concat(df1,df2):
    result = pd.concat([df1, df2], axis=1, join='inner')
    return result


def filter_by_column_value(df, colname, value):
    s= df[df[colname] == value]
    return s


if __name__ == '__main__':


    #OD.drop_duplicates(subset="zone", inplace=True)
    doc = os.path.join(app.root_path, 'variables.csv')
    #doc2 = os.path.join(app.root_path, '21_rutas_accel.csv')
    #rutas = pd.read_csv(doc, names=["longitude", "latitude", "elevation", "x", "timestamp","y","soc"])
    df = pd.read_csv(doc, index_col="id")
    s = df.var_pretty[df['var']=="speed"].values[0]
    print(s.values[0])



    #rutas2 = pd.read_csv(doc2, index_col="id")
    #rutas2 = rutas2[["accelerationX","accelerationY","accelerationZ", "Time_2", "dia"]]
    #df.to_csv("variables.csv")

    #s.to_csv("elevation.csv")
    #df = rutas[rutas.elevation.notnull()]

    #OD = OD[["zone", "name","lat","lon"]]
    #OD['zone'] = OD['zone'].map(lambda x: str(x).replace("Z",""))
    #OD["zone"] = OD["zone"].astype(float)
    #OD = OD.sort_values(by=["zone"])
    #OD.to_csv("zones.csv", index=False)
    #test = pd.read_csv("zones.csv")

    #df2 = pd.read_csv("Z_Z.txt", sep=";", names=["z_o", "lat_o", "lon_o", "z_d", "lat_d", "lon_d", "6", "7"])
    #df2.drop_duplicates(subset="z_o", inplace=True)

    #df2 = df2[["lat_o", "lon_o"]]







