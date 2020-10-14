import math
import numpy as np
import pandas as pd
import time
from scipy import integrate

def fiori(mass, frontal_area, cd, slope, speed, acc):
    g = 9.8066
    p = 1.2256  # Air density kg/m3
    cr = 1.75  # Rolling coefficient
    n_drive = 0.95  # driveline efficiency
    n_motor = 0.96  # motor efficiency
    n_regen = 0
    c2 = 4.575
    c1 = 0.0328
    k = 0  # speed factor
    speed = speed / 3.6

    rad = (slope * math.pi) / 180
    p_wheels = (mass * acc + mass * g * math.cos(rad) * (cr/1000) * (c1 * speed + c2)
                + 0.5 * p * frontal_area * cd * speed ** 2 + mass *g * math.sin(rad)) * speed/1000

    p_motor = p_wheels / (n_drive * n_motor)

    if acc < -0.06:
        n_regen = (math.exp(0.11 / acc))**-1

    if p_motor < 0:
        fiori_consumption = p_motor * n_regen
    else:
        fiori_consumption = p_motor

    return np.array([fiori_consumption, p_wheels, p_motor])


def jimenez(mass, frontal_area, cd, slope, speed, acc):   # tpms

    p = 1.2  # Air density kg/m3
    cr = 0.001 * (1 + speed/(100*3.6))  # Rolling coefficient 1
    bar = 30/14.504
    cr2 = 0.005 + (1 / bar)*(0.01 + 0.0095*(speed / 100)**2)  # Rolling coefficient 2
    n_drive = 0.97  # transmission efficiency
    n_motor = 0.97  # Motor efficiency
    n_batt = 0.95  # Battery efficiency
    k = 0   # speed factor
    p_aux = 0.2  # kW aux components

    # cr = 0.005 + (1 / p) (0.01 + 0.0095 (v / 100)2)  pressure in Bar V in kmH

    rad = (slope * math.pi) / 180

    friction_force = (cr * mass * 9.81 * math.cos(rad)) + (0.5 * p * frontal_area * cd * (speed / 3.6) ** 2)

    Fw = mass * 9.81 * math.sin(rad)
    net_force = mass * acc + Fw + friction_force
    # print([(mass * acc), Fw, friction_force])
    mec_power = (net_force * speed / 3.6) / 1000
    speed = speed / 3.6

    if speed < 5:
            k = 0.78 * speed
    else:
        k = 0.78+ 0.015 * (speed - 5)

    if mec_power < 0:
        jimenez_consumption = k * n_drive * n_motor * n_batt * mec_power
    else:
        jimenez_consumption = mec_power / (n_drive * n_batt * n_motor)

    return np.array([jimenez_consumption, mec_power, net_force, friction_force])


def add_consumption_cols(df, mass, frontal_area, cd):

    df['jimenez_estimation'] = df.apply(lambda row: jimenez(mass, frontal_area, cd, row['slope'], row['speed'], row['mean_acc'])[0], axis=1)

    df['fiori_estimation'] = df.apply(lambda row: fiori(mass, frontal_area, cd, row['slope'], row['speed'], row['mean_acc'])[0], axis=1)
    '''
    df['friction_force_calc'] = df.apply(lambda row: jimenez(mass, frontal_area, cd,
                                                             row['slope'], row['mean_speed'], row['mean_acc'])[3], axis=1)
    df['net_force_calc'] = df.apply(lambda row: jimenez(mass, frontal_area, cd,
                                                        row['slope'], row['mean_speed'], row['mean_acc'])[2], axis=1)
    '''
    df['req_power'] = df.apply(lambda row: jimenez(mass, frontal_area, cd,
                                                   row['slope'], row['speed'], row['mean_acc'])[1], axis=1)

    dates = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f")
    x = np.array([time.mktime(t.timetuple()) for t in dates])  # total seconds since epoch
    x1=x

    '''
    y = df[y_name].to_numpy()
    y1 = np.where(y >= 0, y, 0)
    y2 = np.where(y <= 0, y, 0)
    labels = [out1_name, out2_name]

    try:
    '''
    print(['len(x)', x.shape,'len(y)',df['jimenez_estimation'].shape, 'len(power)', df['power_kw'].shape])
    df['jimenez_int'] = (integrate.cumtrapz(df['jimenez_estimation'], x, initial=0))/3600
    df['fiori_int'] = (integrate.cumtrapz(df['fiori_estimation'], x, initial=0)) / 3600
    df['power_int'] = (integrate.cumtrapz(df['power_kw'], x.squeeze(), initial=0,))/3600
    # values = [np.around((np.trapz(y1, x) / 3600), 3), abs(np.around((np.trapz(y2, x) / 3600), 3))]  # j to kwh


if __name__ == '__main__':
    pass
