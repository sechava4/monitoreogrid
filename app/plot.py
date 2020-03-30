import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json


def create_plot(data_frame,x,y):

    # N = 440
    # x = np.linspace(0, 1, N)
    # y = np.random.randn(N)
    # df = pd.DataFrame({'x': x, 'y': y}) # creating a sample dataframe

    data = [go.Scatter(x=data_frame[x], y=data_frame[y])]

    graphjson = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

    return graphjson
