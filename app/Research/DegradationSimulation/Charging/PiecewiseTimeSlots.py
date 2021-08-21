import numpy as np

from PiecewiseLinear import PiecewiseLinear


class Piecewise:
    def __init__(self, G, B, E):
        # Parametros
        """if G == None:
            self.G = [('prot1',3),('prot2',11),('prot3',22),('prot4',44)]#pair of charging powers and charging protocols
        else:"""
        self.G = G

        """if B == None:
            self.B = [0,1,2,3]
        else:"""
        self.B = B

        """if E == None:
            self.E = [16000,24000,30000]
        else:"""
        self.E = [e * 1000 for e in E]

        self.breakPoints1 = [0, 0.85, 0.95, 1]
        self.timePoints1 = [0, 0.61, 0.76, 1]

        # miu(ghl) g in G, h in B, l in E
        # miu es el nivel de la bateria asociado a cada breakpoint

        self.miu = {
            (g, e): [self.breakPoints1[i] * e for i in self.B]
            for g in self.G
            for e in self.E
        }

        # psi(ghl) g in G, h in B, l in E
        # psi es el tiempo de carga asociado a cada breakpoint

        self.powerStation1 = []
        self.psi = {}

        for g in self.G:
            self.powerStation1.append(g)
            if g == 2.3:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 9.76 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 3:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 7.48 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 3.6:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 6.23 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 7.2:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 3.12 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 7.4:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 3.03 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 11:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 2.04 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 22:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 1.01 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 43:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 0.51 / 16000 for i in self.B
                            ]
                        }
                    )
            elif g == 50:
                for e in self.E:
                    self.psi.update(
                        {
                            (g, e): [
                                self.timePoints1[i] * e * 0.45 / 16000 for i in self.B
                            ]
                        }
                    )

        self.PW = PiecewiseLinear(self.miu, self.psi, self.powerStation1)

        # Parametros de entrada: estado de carga inicial, estado de carga final, potencia de carga, capacidad de la bateria
        # Para un vehiculo esto seria o,o+q,y,delta
        # startLevel y exitLevel [0,1], inputPower y batterySize en kW

    # Funcion para calcular la duracion de la carga
    def chargingTimeFunction(self, startLevel, exitLevel, inputPower, batterySize):
        batterySize *= 1000
        outputTime = 0.0
        j = (inputPower, batterySize)

        startLevel *= batterySize
        exitLevel *= batterySize

        times = []  # Inicio, Fin y BkPoints de tiempo de los tramos usados la PW
        eLevels = []  # Inicio, Fin y BkPoints de batLevel de los tramos usados la PW

        for i in range(1, len(self.PW.getBreakPoints()[j])):
            # lowerBound y upperBound son los valores de los breakpoints de bateria para el tramo correspondiente donde inicia la carga
            lowerBound = self.PW.getBreakPoints()[j][i - 1]
            upperBound = self.PW.getBreakPoints()[j][i]

            # identifica en que tramo de la funcion inicia el vehiculo la carga
            if lowerBound <= startLevel and upperBound >= startLevel:
                # alpha es el porcentaje que falta para finalizar el tramo
                alpha = (startLevel - upperBound) / (lowerBound - upperBound)
                lowerTime = self.PW.getTimePoints()[j][
                    i - 1
                    ]  # breakpoint del tiempo en que inicia el tramo
                UpperTime = self.PW.getTimePoints()[j][
                    i
                ]  # breakpoint del tiempo en que termina el tramo
                inputTime = lowerTime * alpha + UpperTime * (
                        1 - alpha
                )  # valor del tiempo en la piecewise en el que inicia el vehiculo la carga

                times.append(inputTime)
                eLevels.append(startLevel)

                for n in range(i, len(self.PW.getBreakPoints()[j])):
                    # Este ciclo lo recorre cada vez que se usa un tramo de la PW
                    # son los valores de los breakpoints de bateria para el tramo correspondiente
                    lowerBoundOutput = self.PW.getBreakPoints()[j][n - 1]
                    upperBoundOutput = self.PW.getBreakPoints()[j][n]

                    if lowerBoundOutput <= exitLevel and upperBoundOutput >= exitLevel:
                        # Beta es el porcentaje que falta para finalizar el tramo
                        beta = (exitLevel - upperBoundOutput) / (
                                lowerBoundOutput - upperBoundOutput
                        )
                        lowerTimeOutput = self.PW.getTimePoints()[j][
                            n - 1
                            ]  # breakpoint del tiempo en que inicia el tramo
                        upperTimeOutput = self.PW.getTimePoints()[j][
                            n
                        ]  # breakpoint del tiempo en que termina el tramo
                        outputTime = lowerTimeOutput * beta + upperTimeOutput * (
                                1 - beta
                        )  # valor del tiempo en la piecewise en el que termina el vehiculo la carga

                        times.append(outputTime)
                        eLevels.append(exitLevel)
                        break

                    else:
                        times.append(self.PW.getTimePoints()[j][n])
                        eLevels.append(upperBoundOutput)

                break

        # Energia cargada en cada tramo de la PW (de los tramos usados)
        eCharged = [(eLevels[i + 1] - eLevels[i]) for i in range(len(eLevels) - 1)]

        # Tiempo cargado en cada tramo de la PW (de los tramos usados)
        tCharged = [(times[i + 1] - times[i]) for i in range(len(times) - 1)]

        serviceTime = outputTime - inputTime

        return serviceTime, times, eLevels, eCharged, tCharged

    # Funcion para calcular cuanto tiempo y cuanta energia se carga en cada intervalo de tiempo
    def energyTimeSlot(
            self, inputPower, batterySize, startPW, endPW, startHour, timeSlots
    ):
        batterySize *= 1000
        j = (inputPower, batterySize)

        # Identifico cuales y cuantos intervalos de tiempo se usan
        low_t = int(startHour)
        upper_t = int(startHour + (endPW - startPW))
        # Buscando en el array de timeSlots la horas de inicio y fin
        idx_tSlots = np.where((timeSlots >= low_t) & (timeSlots <= upper_t))[0]
        # idx_tSlots guarda las posiciones de timeSlots de los intervalos usados

        # Guardo la cantidad de intervalos usados
        cntSlots = len(idx_tSlots)
        result = np.zeros([2, cntSlots])

        # Loop para calcular en cada intervalo, cuanto energia se carga y cuanto tiempo
        for h in range(cntSlots):
            # Calcular para cada intervalo los tiempos correspondientes en la PW (no esta sujeto a la hora)
            if cntSlots == 1:
                # si solo se usa un intervalo, van a ser el tiempo de inicio y fin de la PW
                startTime = startPW
                exitTime = endPW
            else:
                if h == 0:
                    # si es el primer intervalo
                    startTime = startPW  # Se inicia en el tiempo de inicio de la PW hasta que se termina el intervalo
                    exitTime = timeSlots[idx_tSlots[h] + 1] - startHour + startTime
                elif h == cntSlots - 1:
                    # si es el ultimo intervalo
                    startTime = exitTime  # Se inicia cuando se termina el anterior y va hasta el tiempo de fin de la PW
                    exitTime = endPW
                else:
                    # si es un intervalo intermedio
                    startTime = exitTime  # Se inicia cuando se termina el anterior y va hasta que se termina el intervalo
                    exitTime = (
                            timeSlots[idx_tSlots[h] + 1]
                            - timeSlots[idx_tSlots[h]]
                            + startTime
                    )

            # Loop para cada tramo de la PW
            for i in range(1, len(self.PW.getTimePoints()[j])):
                # lowerTime y upperTime son los valores de los breakpoints de tiempo para el tramo correspondiente donde inicia el vehiculo en el intervalo
                lowerTime = self.PW.getTimePoints()[j][i - 1]
                upperTime = self.PW.getTimePoints()[j][i]

                # Identifica en que tramo de la funcion PW inicia el vehiculo para el tiempo de inicio correspondiente (startTime)
                if lowerTime <= startTime and upperTime >= startTime:

                    # alpha es el porcentaje que falta para finalizar el tramo en el que inicia
                    alpha = (startTime - upperTime) / (lowerTime - upperTime)
                    lowerEnergy = self.PW.getBreakPoints()[j][
                        i - 1
                        ]  # breakpoint de la bat en que inicia el tramo
                    upperEnergy = self.PW.getBreakPoints()[j][
                        i
                    ]  # breakpoint de la bat en que termina el tramo
                    inputEnergy = lowerEnergy * alpha + upperEnergy * (
                            1 - alpha
                    )  # valor de la bateria en el que inicia el vehiculo la carga en el intervalo actual

                    # Loop para cada tramo de la PW para calcular lo cargado en cada uno
                    for n in range(i, len(self.PW.getTimePoints()[j])):
                        # Este ciclo lo recorre cada vez que se usa un tramo de la PW
                        # lowerTime y upperTime son los valores de los breakpoints de tiempo para el tramo correspondiente donde termina el vehiculo en el itnervalo
                        lowerTimeOutput = self.PW.getTimePoints()[j][n - 1]
                        upperTimeOutput = self.PW.getTimePoints()[j][n]

                        # Identifica en que tramo de la funcion PW termina el vehiculo para el tiempo de fin correspondiente (exitTime)
                        if lowerTimeOutput <= exitTime and upperTimeOutput >= exitTime:
                            # Beta es el porcentaje que falta para finalizar el tramo en el que termina
                            beta = (exitTime - upperTimeOutput) / (
                                    lowerTimeOutput - upperTimeOutput
                            )
                            lowerEnergyOutput = self.PW.getBreakPoints()[j][
                                n - 1
                                ]  # breakpoint de la bat en que inicia el tramo
                            upperEnergyOutput = self.PW.getBreakPoints()[j][
                                n
                            ]  # breakpoint de la bat en que termina el tramo
                            outputEnergy = lowerEnergyOutput * beta + upperEnergyOutput * (
                                    1 - beta
                            )  # valor de la bateria en el que termina el vehiculo en el intervalo actual
                            break
                    break

            energyCharged = (
                    outputEnergy - inputEnergy
            )  # Energia cargada en el intervalo
            timeCharged = exitTime - startTime  # Tiempo cargado en el intervalo
            result[0, h] = timeCharged
            result[1, h] = energyCharged

        return result

    # Funcion para calcular la duracion de la carga, y cada breakpoint
    def chargingProcess(self, startLevel, exitLevel, inputPower, batterySize):
        batterySize *= 1000
        j = (inputPower, batterySize)

        times = []
        eLevels = []

        startLevel *= batterySize
        exitLevel *= batterySize

        for i in range(1, len(self.PW.getBreakPoints()[j])):
            # lowerBound y upperBound son los valores de los breakpoints de bateria para el tramo correspondiente donde inicia la carga
            lowerBound = self.PW.getBreakPoints()[j][i - 1]
            upperBound = self.PW.getBreakPoints()[j][i]

            # identifica en que tramo de la funcion inicia el vehiculo la carga
            if lowerBound <= startLevel and upperBound >= startLevel:
                # alpha es el porcentaje que falta para finalizar el tramo
                alpha = (startLevel - upperBound) / (lowerBound - upperBound)
                lowerTime = self.PW.getTimePoints()[j][
                    i - 1
                    ]  # breakpoint del tiempo en que inicia el tramo
                UpperTime = self.PW.getTimePoints()[j][
                    i
                ]  # breakpoint del tiempo en que termina el tramo
                inputTime = lowerTime * alpha + UpperTime * (
                        1 - alpha
                )  # valor del tiempo en la piecewise en el que inicia el vehiculo la carga

                times.append(inputTime)
                eLevels.append(startLevel)

                for n in range(i, len(self.PW.getBreakPoints()[j])):
                    # Este ciclo lo recorre cada vez que se usa un tramo de la PW
                    # son los valores de los breakpoints de bateria para el tramo correspondiente
                    lowerBoundOutput = self.PW.getBreakPoints()[j][n - 1]
                    upperBoundOutput = self.PW.getBreakPoints()[j][n]

                    if lowerBoundOutput <= exitLevel and upperBoundOutput >= exitLevel:
                        # Beta es el porcentaje que falta para finalizar el tramo
                        beta = (exitLevel - upperBoundOutput) / (
                                lowerBoundOutput - upperBoundOutput
                        )
                        lowerTimeOutput = self.PW.getTimePoints()[j][
                            n - 1
                            ]  # breakpoint del tiempo en que inicia el tramo
                        upperTimeOutput = self.PW.getTimePoints()[j][
                            n
                        ]  # breakpoint del tiempo en que termina el tramo
                        outputTime = lowerTimeOutput * beta + upperTimeOutput * (
                                1 - beta
                        )  # valor del tiempo en la piecewise en el que termina el vehiculo la carga

                        times.append(outputTime)
                        eLevels.append(exitLevel)
                        break

                    else:
                        times.append(self.PW.getTimePoints()[j][n])
                        eLevels.append(upperBoundOutput)
                break
        sizeOut = len(times)
        outputs = np.zeros([2, sizeOut])

        outputs[0, :] = times
        outputs[1, :] = eLevels

        return outputs
