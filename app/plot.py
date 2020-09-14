import plotly
import plotly.graph_objs as go
import json
import pandas as pd
import numpy as np
import plotly.express as px

def create_double_plot(data_frame, x_name, y_name, y2_name):
    x = data_frame[x_name].to_numpy()
    y = data_frame['power_kw'].to_numpy()
    mask = np.where(y > 0)
    notmask = np.where(y < 0)
    print(mask)
    print(notmask)

    fig = go.Figure(go.Scatter(x=x[mask], y=y[mask], mode='lines', name='Consumption',
                               fill='tozeroy', fillcolor='blue'))
    fig.add_trace(go.Scatter(x=x[notmask], y=y[notmask], mode='lines', name='Regeneration',
                             fill='tozeroy', fillcolor='orange'))

    scatter_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json


def create_plot(data_frame, x, y):
    data_scatter = [go.Scatter(x=data_frame[x], y=data_frame[y])]
    scatter_json = json.dumps(data_scatter, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json


def create_donnut(df, x, y):

    labels = [x, y]
    series1 = np.where(df["power_kw"] < 0, df["power_kw"], 0)
    series2 = np.where(df["power_kw"] > 0, df["power_kw"], 0)
    values = [abs(series1.sum()), abs(series2.sum())]
    data_donnut =[go.Pie(labels=labels, values=values, hole=.3)]
    pie_json = json.dumps(data_donnut, cls=plotly.utils.PlotlyJSONEncoder)
    return pie_json
