import plotly
import plotly.graph_objs as go
import json
import pandas as pd
import plotly.express as px


def create_plot(data_frame, x, y):
    data_scatter = [go.Scatter(x=data_frame[x], y=data_frame[y])]

    labels = ['Oxygen', 'Hydrogen', 'Carbon_Dioxide', 'Nitrogen']
    values = [4500, 2500, 1053, 500]

    # Use `hole` to create a donut-like pie chart
    data_donnut =[go.Pie(labels=labels, values=values, hole=.3)]

    scatter_json = json.dumps(data_scatter, cls=plotly.utils.PlotlyJSONEncoder)
    pie_json = json.dumps(data_donnut, cls=plotly.utils.PlotlyJSONEncoder)
    return scatter_json, pie_json
