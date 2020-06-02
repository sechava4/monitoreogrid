import plotly
import plotly.graph_objs as go
import json


def create_plot(data_frame, x, y):
    data = [go.Scatter(x=data_frame[x], y=data_frame[y])]
    graphjson = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)
    return graphjson
