import pandas as pd
import os
from app import app


def get_stations():
    file = os.path.join(app.root_path, "stations.json")
    df = pd.read_json(file)
    df.columns = ["name","latitude","longitude", "charger_types"]
    return df


def get_zones():
    file = os.path.join(app.root_path,'zones.txt')
    zones = pd.read_csv(file)
    zones = zones[["name", "lon", "lat"]]
    return zones


if __name__ == '__main__':
    df = get_stations()
    print(df.to_json(orient='records'))
    stations_df = df[["longitude", "latitude"]]
    try:
        OD = pd.read_excel("RutasOD.xlsx", sep=";")
        OD = OD[["zone", "name", "lat", "lon"]]
        OD.drop_duplicates(subset="zone", inplace=True)
    except FileNotFoundError:
        OD = get_zones()
    OD
    doc = os.path.join(app.root_path, 'zones.txt')

    #OD = OD[["zone", "name","lat","lon"]]
    #OD['zone'] = OD['zone'].map(lambda x: str(x).replace("Z",""))
    #OD["zone"] = OD["zone"].astype(float)
    #OD = OD.sort_values(by=["zone"])
    #OD.to_csv("zones.txt", index=False)
    #test = pd.read_csv("zones.txt")

    #df2 = pd.read_csv("Z_Z.txt", sep=";", names=["z_o", "lat_o", "lon_o", "z_d", "lat_d", "lon_d", "6", "7"])
    #df2.drop_duplicates(subset="z_o", inplace=True)

    #df2 = df2[["lat_o", "lon_o"]]







