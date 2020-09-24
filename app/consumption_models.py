import math
import numpy as np
import pandas as pd


def jimenez(weight, frontal_area, cd, slope, speed, acc):
    p = 1.2  # Air density kg/m3
    cr = 0.02  # Rolling coefficient
    nte = 0.85  # transmission efficiency
    ne = 0.85  # Battery efficiency
    k = 0   # speed factor

    # cr = 0.005 + (1 / p) (0.01 + 0.0095 (v / 100)2)  pressure in Bar V in kmH

    rad = (slope * math.pi) / 180

    friction_force = (cr * weight * 9.81 * math.cos(rad)) + \
                     (0.5 * p * frontal_area * cd
                      * (speed / 3.6) ** 2)

    Fw = weight * 9.81 * math.sin(slope)
    net_force = weight * acc + Fw + friction_force
    mec_power = (net_force * speed / 3.6) / 1000
    if acc < 0:
        if speed < 5:
            k = 0.5 * speed
    else:
        k = 0.5 + 0.015 * (speed - 5)

    if mec_power < 0:
        jimenez_consumption = k * nte * ne * mec_power
    else:
        jimenez_consumption = mec_power / (nte * ne)
    print("Jimenez consumption")
    print(jimenez_consumption)
    return np.array([jimenez_consumption, mec_power, net_force, friction_force])


def add_jimenez_row(df, weight, frontal_area, cd):
    print(df)
    df['added_jimenez'] = df.apply(lambda row: jimenez(weight, frontal_area, cd,
                                                       row['slope'], row['mean_speed'], row['mean_acc'])[0], axis=1)
    df['req_power'] = df.apply(lambda row: jimenez(weight, frontal_area, cd,
                                                   row['slope'], row['mean_speed'], row['mean_acc'])[1], axis=1)
    df['friction_force_calc'] = df.apply(lambda row: jimenez(weight, frontal_area, cd,
                                                   row['slope'], row['mean_speed'], row['mean_acc'])[3], axis=1)
    print(df)


if __name__ == '__main__':
    pass
