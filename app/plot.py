import plotly
import plotly.graph_objs as go
import json
import pandas as pd
import plotly.express as px


def create_plot(data_frame, x, y):
    data_scatter = [go.Scatter(x=data_frame[x], y=data_frame[y])]

    scatter_json = json.dumps(data_scatter, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json


def create_donnut(series1, series2, x, y):

    labels = [x, y]
    values = [series1.sum(), series2.sum()]

    data_donnut =[go.Pie(labels=labels, values=values, hole=.3)]

    pie_json = json.dumps(data_donnut, cls=plotly.utils.PlotlyJSONEncoder)
    return pie_json
