from app import app, open_dataframes, plot, db
from app.closest_points import Trees
from app.forms import LoginForm, RegistrationForm, TablesForm, VehicleMapForm
from flask import request, session, redirect, url_for, Markup, \
    render_template, flash,send_from_directory
import pandas as pd
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Operation
import os
import json
from datetime import datetime

import geopandas as gpd


@app.route('/')
@login_required
def show_entries():
    try:
        session["graph_var_x"]
        session["graph_var_y"]
        session['t1']
        session['t2']
    except KeyError:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soh"
        session['t1'] = datetime(2020, 1, 1)
        session['t2'] = datetime.now()

    # t1 = datetime.strptime(session['t1'], '%m/%d/%Y %I:%M %p')
    # t2 = datetime.strptime(session['t2'], '%m/%d/%Y %I:%M %p')
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + " from operation " +\
            'WHERE timestamp BETWEEN "' + session['t1'].strftime('%Y-%m-%d %I:%M:%S') +\
            '" and "' + session['t2'].strftime('%Y-%m-%d %I:%M:%S') + '"'

    print(query)
    df_o = pd.read_sql_query(query, db.engine)
    #pd.read_sql(session.query(Operation).filter(Operation.id == 2).statement, session.bind)

    bar = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])
    return render_template('show_entries.html', plot=bar)


@app.route('/updateplot')
def update_plot():
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + " from operation " + \
            'WHERE timestamp BETWEEN "' + session['t1'].strftime('%Y-%m-%d %I:%M:%S') + '" and "' + session[
                't2'].strftime('%Y-%m-%d %I:%M:%S') + '"'
    df_o = pd.read_sql_query(query, db.engine)
    #pd.read_sql(session.query(Operation).filter(Operation.id == 2).statement, session.bind)

    bar = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])
    return bar


@app.route('/tables', methods=['GET', 'POST'])
@login_required
def show_tables():
    form = TablesForm()
    if form.is_submitted():
        session["records"] = form.records.data
        session["dataset"] = form.dataset.data

    try:
        session["records"]
    except KeyError:
        session["records"] = 20

    if session["records"] is None:
        session["records"] = 20


    #session["records"] = (request.form['records'])
    doc_dataset = os.path.join(app.root_path, session["dataset"])
    df = pd.read_csv(doc_dataset, index_col="id")
    df = df[1:(int(session["records"])+1)]
    # df = pd.read_sql_query("SELECT * from vehicle", db.engine,index_col="id")
    return render_template('tables.html', tables=[df.to_html(classes='data')], titles=df.columns.values, form=form)


@app.route('/zones_map', methods=['GET', 'POST'])
@login_required
def show_zones_map():

    form = VehicleMapForm()
    if form.is_submitted():
        session["day"] = form.day.data
    try:
        session["day"]
    except KeyError:
        session["day"] = 1


    lines_df = open_dataframes.get_lines()
    zones = open_dataframes.get_zones()
    json_zones = Markup(zones.to_json(orient='records'))

    _, lines_df['id_nearest_zone'] = Trees.zones_tree.query(lines_df[['latitude', 'longitude']].values, k=1)
    lines_df["name"] = zones["name"].reindex(index=lines_df['id_nearest_zone']).tolist()
    json_lines = Markup(lines_df.to_json(orient='records'))

    return render_template('zones_map.html',json_zones=json_zones, json_lines=json_lines,form=form)


@app.route('/vehicle_map', methods=['GET', 'POST'])
@login_required
def show_vehicle_map():
    form = VehicleMapForm()
    if form.is_submitted():
        session["map_var"] = form.variable.data

    try:
        session["map_var"]
    except KeyError:
        session["map_var"] = "elevation"
        session["map_car"] = "seleccione vehiculo"

    stations_df = open_dataframes.get_stations()
    json_stations = Markup(stations_df.to_json(orient='records'))

    lines_df = open_dataframes.get_lines()
    json_lines = Markup(lines_df.to_json(orient='records'))

    alturas_df = open_dataframes.get_heights(session["map_var"])
    # current_pos = alturas.iloc[1:2]

    titles = Operation.__dict__
    form.variable.choices = open_dataframes.form_var(titles)
    session["title_var"] = open_dataframes.pretty_var_name(session["map_var"])

    _, a = Trees.station_tree.query(alturas_df[['latitude', 'longitude']].values, k=2)    #Select neares 2 stations (Knearest)
    alturas_df["closest_st_id1"] = a[:, 0]
    alturas_df["closest_st_id2"] = a[:, 1]
    alturas_df["closest_station1"] = stations_df["name"].reindex(index=alturas_df['closest_st_id1']).tolist()  # map station id with station name (vector)
    alturas_df["closest_station2"] = stations_df["name"].reindex(index=alturas_df['closest_st_id2']).tolist()  # map station2  id with station name (vector)
    # session["closest_station"] = stations_df["name"].iloc[current_pos['id_nearest']].item()              # map station id with station name (current)
    json_operation = Markup(alturas_df.to_json(orient='records'))

    return render_template('vehicle_map.html', form=form, json_lines=json_lines, json_operation=json_operation,
                           json_stations=json_stations)



@app.route('/gauges')
@login_required
def show_indicators():
    df = pd.read_sql_query("SELECT * from operation limit 1", db.engine)
    titles = df.columns.values
    return render_template('indicators.html')


@app.route('/addjson', methods=['POST', 'GET'])
def add_entry():
    if not bool(request.args):
        return ("Null data")
    else:
        operation = Operation(**request.args)   # ** pasa un numero variable argumentos a la funcion
        print(operation.__dict__)
        db.session.add(operation)
        db.session.commit()
        return ("Data recieved")#redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        return redirect(url_for('show_entries'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('show_entries')
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('show_entries'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('show_entries'))


@app.route('/graph_var', methods=['POST'])
def graph_var():
    session["graph_var_x"] = (request.form['variable_x'])
    session["graph_var_y"] = (request.form['variable_y'])
    try:
        session["t1"] = datetime.strptime(request.form['t1'], '%m/%d/%Y %I:%M %p')
    except ValueError:
        session['t1'] = datetime(2020, 1, 1)
    try:
        session["t2"] = datetime.strptime(request.form['t2'], '%m/%d/%Y %I:%M %p')
    except ValueError:
        session['t2'] = datetime.now()

    print(session['t1'], session['t2'])
    return redirect(url_for('show_entries'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'monitor.ico')