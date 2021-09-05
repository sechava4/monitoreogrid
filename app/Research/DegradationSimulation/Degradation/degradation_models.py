import math
import time
from typing import List
import numpy as np
import pandas as pd
from dataclasses import dataclass
import statistics as stats


def wang(current, delta_t, batt_temp):
    """

    :param current: mean amperes during delta t seconds
    :param delta_t: seconds
    :param batt_temp: celcius degrees
    :return: capacity loss in %
    """
    ah = current * delta_t / 3600
    c_rate = current / 100  # 100 = Amperios hora totales bateria
    if c_rate > 0:
        b = 448.96 * c_rate ** 2 - 6301.1 * c_rate + 33840
        try:
            q_loss = (
                b
                * math.exp((-31700 + (c_rate * 370.3)) / (8.314472 * (batt_temp)))
                * ah ** 0.552
            )
        except OverflowError:
            q_loss = 0
    else:
        q_loss = 0

    return q_loss


def add_wang_column(df):
    dates = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S.%f")
    x = np.array(
        [time.mktime(t.timetuple()) for t in dates]
    )  # total seconds since epoch
    df["x1"] = x
    dates2 = df["x1"].iloc[1:]
    dates2 = dates2.append(pd.Series(df["x1"].iloc[-1]), ignore_index=True)
    df["x2"] = dates2

    df["delta_t"] = df["x2"] - df["x1"]
    df["wang_degradation"] = df.apply(
        lambda row: wang(row["current"], row["delta_t"], row["batt_temp"]), axis=1
    )
    df["cumulative_degradation"] = df["wang_degradation"].cumsum()
    del df["x2"], df["x1"]


class XuDegradationModel:
    # TODO: add helper to append a row
    def __init__(
        self, soc: List, dod: List, c_rates: List, temp: List, n: List, days: int
    ):
        """

        soc: (SoC1, SoC2, . . . , SoCn) float numbers ranging from 0 to 1
        dod: (DoD1, DoD2, . . . , DoDn) float numbers ranging from 0 to 1
        c_rates:  (C1, C2, . . . , Cn)
        temp:  (T1, T2, . . . , Tn) in kelvin degrees
        n:  (n1, n2, . . . , nn) where ni = 1 if full cycle or 0.5 if half cycle
        """

        self.soc = soc
        self.dod = dod
        self.c_rates = c_rates
        self.temp = temp
        self.n = n
        self.length: int = len(soc)

        self.soc_avg = stats.mean(self.soc)
        self.t_avg = stats.mean(self.temp)

        self.days = days

    def compute_degradation(self) -> float:

        self.validate()
        return self.f_cycle() + self.f_calendar()

    def f_cycle(self):
        """
        Calculates degradation due to cycle ageing
        = (fDoD(DoD) · fC(C) + ft(t/N)) · fSoC(SoC) · fT (T) · N
        :return: degradation in x units
        """
        return sum(
            self._f_dod(self.dod[i])
            * self._f_soc(self.soc[i])
            * self._f_c_rate(self.c_rates[i])
            * self._f_temp(self.temp[i])
            * self.n[i]
            for i in range(self.length)
        )

    def f_calendar(self):
        """
        Calculates degradation due to calendar ageing
        :return: degradation in x units
        """
        self.days
        kt = float()
        return kt * self._f_soc(self.soc_avg) * self._f_temp(self.t_avg)

    @staticmethod
    def _f_soc(soc):
        """
        kSoC is the SoC stress coefficient and SoCref is the reference SoC
        level
        :param soc: 0 to 1
        :return:
        """
        k_soc = float()
        soc_ref = 0.5
        return math.exp(k_soc * (soc - soc_ref))

    @staticmethod
    def _f_dod(dod):
        """
        independent from time
        fDoD(DoD) = (kDoD1DoDkDoD2 + kDoD3)**−1
        where kDoD1, kDoD3, and kDoD3 are DoD stress model coefficients
        fitted according to 20% capacity loss

        :param dod:
        """
        k_dod_1 = float()
        k_dod_2 = float()
        k_dod_3 = float()
        return (k_dod_1 * (dod**k_dod_2) + k_dod_3)**-1

    @staticmethod
    def _f_c_rate(c_rate):
        """
        Thus C-rate capacity
        fading tests must be carefully designed to avoid the influence from temperature
        :param c_rate:
        :return:
        """
        c_ref = float()
        return math.exp(c_rate - c_ref)

    @staticmethod
    def _f_temp(t):
        """
        where kT is the temperature stress coefficient,
        Tref is the reference temperature, in Kelvin.
        Here the reference temperature is set to 293K or 25◦C,
        in which most of the calendar ageing experiments are performed
        :rtype: object
        """
        k_t = float()
        t_ref = 293
        return math.exp(k_t * (t - t_ref) * (t_ref / t))

    def validate(self):
        if any(
            len(i) != len(self.soc)
            for i in [self.soc, self.dod, self.c_rates, self.temp, self.n]
        ):
            raise ValueError("Input vector lengths not equal")
