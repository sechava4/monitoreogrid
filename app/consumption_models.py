import math
import numpy as np


def jimenez(weight, frontal_area, cd, slope, speed, acc):
    p = 1.2  # Air density kg/m3
    cr = 0.02  # Rolling coefficient
    nte = 0.85  # transmission efficiency
    ne = 0.85  # Battery efficiency
    k = 0   # speed factor

    # cr = 0.005 + (1 / p) (0.01 + 0.0095 (v / 100)2)  pressure in Bar V in kmH

    friction_force = (cr * weight * 9.81 * math.cos(slope)) + \
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
