import plotly
import plotly.graph_objs as go
import json
import pandas as pd
import numpy as np
import plotly.express as px

def create_double_plot(data_frame, x_name, y_name):
    x = data_frame[x_name]
    y = data_frame[y_name].to_numpy()
    y1 = np.where(y >= 0, y, 0)
    y2 = np.where(y <= 0, y, 0)

    fig = go.Figure(go.Scatter(x=x, y=y1, mode='lines', name='Consumption',
                               fill='tozeroy', fillcolor='blue'))
    fig.add_trace(go.Scatter(x=x, y=y2, mode='lines', name='Regeneration',
                             fill='tozeroy', fillcolor='orange'))

    scatter_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json


def create_plot(data_frame, x, y):
    data_scatter = [go.Scatter(x=data_frame[x], y=data_frame[y])]
    scatter_json = json.dumps(data_scatter, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json


def create_donnut(df, x, y, y_name):

    labels = [x, y]
    series1 = np.where(df[y_name] < 0, df[y_name], 0)
    series2 = np.where(df[y_name] > 0, df[y_name], 0)
    values = [abs(series1.sum()), abs(series2.sum())]
    data_donnut =[go.Pie(labels=labels, values=values, hole=.3)]
    pie_json = json.dumps(data_donnut, cls=plotly.utils.PlotlyJSONEncoder)
    return pie_json
