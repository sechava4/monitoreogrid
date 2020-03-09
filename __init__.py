# Santiago Echavarría Correa
# 201220005014


import openstations
import os
import time
import math
import plot
import stations_map
import sqlite3
import pandas as pd
import numpy as np
from flask import Flask, request, session, g, redirect, url_for, Markup, \
    render_template, flash,send_from_directory # g stands for global

app = Flask(
    __name__)  # create the application instance :  (__name__) se usa para que busque templates y static
app.config.from_object(__name__)  # load config from this file , __init__.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'database.db'),
    SECRET_KEY='dljsaklqk24e21cjn!Ew@fhfghfghggg4565t@dsa5',
    USERNAME='grid',
    PASSWORD='admin'
))
#os.environ['MAPBOX_API_KEY'] ='pk.eyJ1Ijoic2VjaGF2YTQiLCJhIjoiY2s2dTF0eHQ0MDViaTNmbXRhaHVoaG85cSJ9.xMh2vZNuj2PfxsUksteApQ'
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
# Default









@app.route('/map_var', methods=['POST'])
def map_var():
    session["map_var"] = (request.form['variable'])
    session["map_car"] = (request.form['Vehiculo'])
    return redirect(url_for('show_vehicle_map'))
    # return render_template('show_entries.html')


@app.route('/graph_var', methods=['POST'])
def graph_var():
    session["graph_var_x"] = (request.form['variable_x'])
    session["graph_var_y"] = (request.form['variable_y'])
    return redirect(url_for('show_entries'))
    # return render_template('show_entries.html')




@app.route('/')
def show_entries():

    db = get_db()
    df = pd.read_sql_query("SELECT * from entries", db)

    session["battery_temp"] = 40

    # map_df = df[['longitude', 'latitude',session["map_var"]]]
    # stations_map.plot_data(stations_df)

    # Plotting variables
    plot_df = df[[session["graph_var_x"], session["graph_var_y"]]]
    bar = plot.create_plot(plot_df, session["graph_var_x"],session["graph_var_y"])
    return render_template('show_entries.html', plot=bar)



@app.route('/stations_map')
def show_stations_map():
    # Map rendering
    stations_df = openstations.get_stations()
    session["json_stations"] = Markup(stations_df.to_json(orient='records'))
    return render_template('stations_map.html')


@app.route('/vehicle_map')
def show_vehicle_map():
    try:
        session["map_var"]
    except KeyError:
        session["map_var"] = "soc"
        session["map_car"] = "seleccione vehiculo"

    try:
        session["graph_var_x"]
        session["graph_var_y"]
    except KeyError:
        session["graph_var_x"] = "tiempo"
        session["graph_var_y"] = "soc"
    db = get_db()
    df = pd.read_sql_query("SELECT * from entries", db)
    session["json_operation"] = Markup(df.to_json(orient='records'))

    return render_template('vehicle_map.html')



@app.route('/gauges')
def show_indicators():
    return render_template('indicators.html')




@app.route('/addjson', methods=['POST'])
def add_entry():

    db = get_db()
    df = pd.read_sql_query("SELECT * from entries", db,index_col="id")
    print(df)
    content = {}
    for col in df.head():
        if col == "id":
            continue
        # Create dict
        content[col]=request.args[col]


    df = df.append(content, ignore_index=True)
    df.to_sql('entries', db, schema="schema.sql", if_exists="append", index=False)
    flash('New data arrived')
    return redirect(url_for('show_entries'))








@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    session["map_var"] = "soc"
    session["graph_var_x"] = "tiempo"
    session["graph_var_y"] = "soc"
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True         # Las variables session[] se pueden acceder desde js en templates
            flash('Log in satisfactorio')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


# Icon webpage
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'monitor.ico')


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    # rv.row_factory = sqlite3.Row  # para tratar cada entrada de db como un diccionario
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):  # Chequear si el atributo ha sido nombrado 'sqlite_db'(si ya fue instanciado)
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# Run a test server.


app.run(host='0.0.0.0', debug=True, port=8077)
app.add_url_rule('/favicon.ico',redirect_to=url_for('static', filename='monitor.ico'))

