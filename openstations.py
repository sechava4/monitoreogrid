import pandas as pd

def get_stations():
    df = pd.read_json("stations.json")
    df.columns = ["name","latitude","longitude", "charger_types"]
    return df


if __name__ == '__main__':
    df = get_stations()
    print(df.to_json(orient='records'))
    stations_df = df[["longitude","latitude"]]
    csv = stations_df.to_csv(index = False)







