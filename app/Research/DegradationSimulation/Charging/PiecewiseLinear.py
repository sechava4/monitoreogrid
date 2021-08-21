class PiecewiseLinear:
    breakPoints = [[]]
    timePoints = [[]]
    power = []

    def __init__(self, breakPoints, timePoints, power):
        self.breakPoints = breakPoints
        self.timePoints = timePoints
        self.power = power

    def getBreakPoints(self):
        return self.breakPoints

    def getTimePoints(self):
        return self.timePoints

    def getPower(self):
        return self.power
