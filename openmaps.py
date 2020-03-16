import pandas as pd


def get_stations():
    df = pd.read_json("stations.json")
    df.columns = ["name","latitude","longitude", "charger_types"]
    return df


def get_zones():
    df2 = pd.read_csv("Z_Z.txt", sep=";", names=["z_o", "lat", "lon", "z_d", "lat_d", "lon_d", "6", "7"])
    df2.drop_duplicates(subset="z_o", inplace=True)
    df2 = df2[["lon", "lat"]]
    return df2


if __name__ == '__main__':
    df = get_stations()
    print(df.to_json(orient='records'))
    stations_df = df[["longitude", "latitude"]]

    df2 = pd.read_csv("Z_Z.txt", sep=";", names=["z_o", "lat_o", "lon_o", "z_d", "lat_d", "lon_d", "6", "7"])
    df2.drop_duplicates(subset="z_o", inplace=True)

    df2 = df2[["lat_o", "lon_o"]]







