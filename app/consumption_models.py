import math
import numpy as np
import pandas as pd
import time
from scipy import integrate
import requests
import json


def jimenez(mass, frontal_area, cd, slope, speed, acc):
    p = 1.2  # Air density kg/m3
    cr = 0.01 * (1 + speed/(100*3.6))  # Rolling coefficient 1
    bar = 30/14.504
    cr2 = 0.005 + (1 / bar)*(0.01 + 0.0095*(speed / 100)**2)  # Rolling coefficient 2
    n_drive = 0.97  # transmission efficiency
    n_motor = 0.97  # Motor efficiency
    n_batt = 0.95  # Battery efficiency
    k = 0   # speed factor
    p_aux = 1  # kW aux components

    # cr = 0.005 + (1 / p) (0.01 + 0.0095 (v / 100)2)  pressure in Bar V in kmH

    rad = slope * np.pi / 180

    friction_force = (cr * mass * 9.81 * np.cos(rad)) + (0.5 * p * frontal_area * cd * (speed / 3.6) ** 2)

    Fw = mass * 9.81 * np.sin(rad)
    net_force = mass * acc + Fw + friction_force
    # print([(mass * acc), Fw, friction_force])
    mec_power = (net_force * speed / 3.6) / 1000
    speed = speed / 3.6

    k = np.where(speed<5, speed * 0.79 , 0.79 + 0.015 * (speed - 5) )
    jimenez_consumption = np.where(mec_power < 0, k * n_drive * n_motor * n_batt * mec_power , mec_power / (n_drive * n_batt * n_motor) )

    return np.array([(jimenez_consumption + p_aux), mec_power, net_force, friction_force])

def fiori(mass, frontal_area, cd, slope, speed, acc):
    g = 9.8066
    p = 1.2256  # Air density kg/m3
    cr = 1.75  # Rolling coefficient
    n_drive = 0.95  # driveline efficiency
    n_motor = 0.90  # motor efficiency
    n_regen = 0
    c2 = 4.575
    c1 = 0.0328
    k = 0  # speed factor
    speed = speed / 3.6

    rad = (slope * np.pi) / 180
    p_wheels = (mass * acc + mass * g * np.cos(rad) * (cr/1000) * (c1 * speed + c2)
                + 0.5 * p * frontal_area * cd * speed ** 2 + mass *g * np.sin(rad)) * speed/1000

    p_motor = p_wheels / (n_drive * n_motor)

    n_regen = np.where(acc < -0.06, (np.exp(0.11 / acc))**-1 , 0)
    fiori_consumption = np.where(p_motor < 0, p_motor * n_regen, p_motor )

    return np.array([fiori_consumption, p_motor ])


def add_consumption_cols(df, mass, frontal_area, cd):

    # revisar apply completo
    aux_j = jimenez(mass, frontal_area, cd, df['slope'], df['speed'], df['mean_acc'])
    df['jimenez_estimation'] = aux_j[0]
    df['req_power'] = aux_j[1]

    df['fiori_estimation'] = fiori(mass, frontal_area, cd, df['slope'], df['speed'], df['mean_acc'])[0]

    dates = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f")
    x = np.array([time.mktime(t.timetuple()) for t in dates])  # total seconds since epoch
    x1 = x

    '''
    y = df[y_name].to_numpy()
    y1 = np.where(y >= 0, y, 0)
    y2 = np.where(y <= 0, y, 0)
    labels = [out1_name, out2_name]

    try:
    '''
    print(['len(x)', x.shape, 'len(y)', df['jimenez_estimation'].shape, 'len(power)', df['power_kw'].shape])
    df['jimenez_int'] = (integrate.cumtrapz(df['jimenez_estimation'], x, initial=0))/3600
    df['fiori_int'] = (integrate.cumtrapz(df['fiori_estimation'], x, initial=0)) / 3600
    df['power_int'] = (integrate.cumtrapz(df['power_kw'], x.squeeze(), initial=0,))/3600
    # values = [np.around((np.trapz(y1, x) / 3600), 3), abs(np.around((np.trapz(y2, x) / 3600), 3))]  # j to kwh


def smartcharging_consumption_query(df):
    # df = pd.read_csv('Develops/consumption_est1.csv')

    to_ele = df["elevation"].iloc[1:]
    to_ele = to_ele.append(pd.Series(df["elevation"].iloc[-1]), ignore_index=True)
    df["toAltitude"] = to_ele
    df["id"] = df.index
    df = df.rename(columns={"id": "segmentNumber", "distance": "distanceInMeters",
                            "time": "durationInSeconds", "elevation": "fromAltitude"})
    print(df)
    df = df[["segmentNumber", "distanceInMeters", "durationInSeconds", "fromAltitude", "toAltitude"]]
    result = df.to_json(orient="records")
    parsed = json.loads(result)
    r = requests.post('http://192.168.10.138:9090/energy-consumption/get-consumption/1',
                      json=parsed, timeout=10)
    out_data = json.loads(r.content)
    response_df = pd.DataFrame(out_data)
    estimated_consumption = response_df['energyConsumption'].sum() / 1000
    estimated_time = response_df['durationInSeconds'].sum() / 60
    return estimated_consumption.round(3), estimated_time.round(3)


if __name__ == '__main__':

    # df['speed']=df['distance']/df['time']
    pass
