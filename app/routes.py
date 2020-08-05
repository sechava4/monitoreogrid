from app import app, open_dataframes, plot, db
from app.closest_points import Trees
from app.forms import LoginForm, RegistrationForm, TablesForm
from flask import request, session, redirect, url_for, Markup, \
    render_template, flash,send_from_directory
import pandas as pd
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Operation
import os
import geopy.distance
from datetime import datetime
import pytz
import requests
import math


@app.route('/', methods=['GET', 'POST'])
@login_required
def show_entries():
    try:
        session["graph_var_x"]
        session["graph_var_y"]
        session['form_d1']
        session['form_h1']
        session['form_h2']
        session['d1']
        session['h1']
        session['h2']

        session["graph_var_x2"]
        session["graph_var_y2"]
        session['form_d2']
        session['form_h3']
        session['form_h4']
        session['d2']
        session['h3']
        session['h4']
    except KeyError:
        now = datetime.now(pytz.timezone('America/Bogota'))
        session['form_d1'] = now.strftime("%d/%m/%Y")
        session['form_h1'] = '0:01 AM'
        session['form_h2'] = now.strftime("%I:%M %p")  # 12H Format
        session['d1'] = now.strftime("%Y-%m-%d")
        session['h1'] = '00:00:00'
        session['h2'] = now.strftime("%H:%M:%S")
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soh"

        session['form_d2'] = now.strftime("%d/%m/%Y")
        session['form_h3'] = '0:01 AM'
        session['form_h4'] = now.strftime("%I:%M %p")  # 12H Format
        session['d2'] = now.strftime("%Y-%m-%d")
        session['h3'] = '00:00:00'
        session['h4'] = now.strftime("%H:%M:%S")
        session["graph_var_x2"] = "timestamp"
        session["graph_var_y2"] = "soh"

    if request.method == 'POST':

        session["graph_var_x"] = (request.form['variable_x'])
        session["graph_var_y"] = (request.form['variable_y'])
        session['form_d1'] = request.form['d1']
        session['form_h1'] = request.form['h1']
        session['form_h2'] = request.form['h2']

        session["d1"] = (datetime.strptime(request.form['d1'], '%d/%m/%Y')).strftime("%Y-%m-%d")
        session["h1"] = (datetime.strptime(request.form['h1'], '%I:%M %p')).strftime("%H:%M:%S")
        session["h2"] = (datetime.strptime(request.form['h2'], '%I:%M %p')).strftime("%H:%M:%S")
        if session["h2"] < session["h1"]:
            session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

        session["graph_var_x2"] = (request.form['variable_x2'])
        session["graph_var_y2"] = (request.form['variable_y2'])
        session['form_d2'] = request.form['d2']
        session['form_h3'] = request.form['h3']
        session['form_h4'] = request.form['h4']

        session["d2"] = (datetime.strptime(request.form['d2'], '%d/%m/%Y')).strftime("%Y-%m-%d")
        session["h3"] = (datetime.strptime(request.form['h3'], '%I:%M %p')).strftime("%H:%M:%S")
        session["h4"] = (datetime.strptime(request.form['h4'], '%I:%M %p')).strftime("%H:%M:%S")
        if session["h4"] < session["h3"]:
            session["h3"], session["h4"] = session["h4"], session["h3"]  # Swap times

    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d1'] + ' ' + str(session['h1'])[:8] + \
            '" and "' + str(session['d1']) + ' ' + str(session['h2'])[:8] + '"'

    query2 = "SELECT " + session["graph_var_x2"] + " ," + session["graph_var_y2"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d2'] + ' ' + str(session['h3'])[:8] + \
            '" and "' + str(session['d2']) + ' ' + str(session['h4'])[:8] + '"'

    df_o = pd.read_sql_query(query, db.engine)
    df_o2 = pd.read_sql_query(query2, db.engine)

    scatter, donnut = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    scatter2, _ = plot.create_plot(df_o2, session["graph_var_x2"], session["graph_var_y2"])
    box = df_o[session["graph_var_y"]].tolist()
    box2 = df_o2[session["graph_var_y2"]].tolist()
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])

    session["x_pretty_graph2"] = open_dataframes.pretty_var_name(session["graph_var_x2"])
    session["y_pretty_graph2"] = open_dataframes.pretty_var_name(session["graph_var_y2"])
    return render_template('show_entries.html', plot=scatter, pie=donnut, box=box, plot2=scatter2, box2=box2)


@app.route('/updateplot')
def update_plot():
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d1'] + ' ' + str(session['h1'])[:8] + \
            '" and "' + str(session['d1']) + ' ' + str(session['h2'])[:8] + '"'

    query2 = "SELECT " + session["graph_var_x2"] + " ," + session["graph_var_y2"] + \
             ' from operation WHERE timestamp BETWEEN "' + session['d2'] + ' ' + str(session['h3'])[:8] + \
             '" and "' + str(session['d2']) + ' ' + str(session['h4'])[:8] + '"'

    df_o = pd.read_sql_query(query, db.engine)
    df_o2 = pd.read_sql_query(query2, db.engine)
    scatter, donnut = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    scatter2, _ = plot.create_plot(df_o2, session["graph_var_x2"], session["graph_var_y2"])
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])

    session["x_pretty_graph2"] = open_dataframes.pretty_var_name(session["graph_var_x2"])
    session["y_pretty_graph2"] = open_dataframes.pretty_var_name(session["graph_var_y2"])
    return scatter


@app.route('/tables', methods=['GET', 'POST'])
@login_required
def show_tables():
    try:
        session["var1"]
        session["var2"]
        session["var3"]
        session["records"]
    except KeyError:

        session["var1"] = "timestamp"
        session["var2"] = "speed"
        session["var3"] = "mean_acc"
        session["records"] = 20

    if request.method == 'POST':
        session["var1"] = (request.form['var1'])
        session["var2"] = (request.form['var2'])
        session["var3"] = (request.form['var3'])
        session["records"] = (request.form['records'])
        session['form_d1'] = request.form['d1']
        session['form_h1'] = request.form['h1']
        session['form_h2'] = request.form['h2']
        if session["records"] is None:
            session["records"] = 20

        session["d1"] = (datetime.strptime(request.form['d1'], '%d/%m/%Y')).strftime("%Y-%m-%d")
        session["h1"] = (datetime.strptime(request.form['h1'], '%I:%M %p')).strftime("%H:%M:%S")
        session["h2"] = (datetime.strptime(request.form['h2'], '%I:%M %p')).strftime("%H:%M:%S")
        if session["h2"] < session["h1"]:
            session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

    query = "SELECT " + session["var1"] + " ," + session["var2"] + " ," + session["var3"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d1'] + ' ' + str(session['h1'])[:8] + \
            '" and "' + str(session['d1']) + ' ' + str(session['h2'])[:8] + '" limit ' + str(session["records"])

    df = pd.read_sql_query(query, db.engine)
    session["var1_pretty"] = open_dataframes.pretty_var_name(session["var1"])
    session["var2_pretty"] = open_dataframes.pretty_var_name(session["var2"])
    session["var3_pretty"] = open_dataframes.pretty_var_name(session["var3"])
    return render_template('tables.html', tables=[df.to_html(classes='data')], titles=df.columns.values)


@app.route('/zones_map', methods=['GET', 'POST'])
@login_required
def show_zones_map():
    try:
        session['form_d1']
        session['form_h1']
        session['form_h2']
        session['d1']
        session['h1']
        session['h2']

    except KeyError:
        now = datetime.now(pytz.timezone('America/Bogota'))
        session['form_d1'] = now.strftime("%d/%m/%Y")
        session['form_h1'] = '0:01 AM'
        session['form_h2'] = now.strftime("%I:%M %p")  # 12H Format
        session['d1'] = now.strftime("%Y-%m-%d")
        session['h1'] = '00:00:00'
        session['h2'] = now.strftime("%H:%M:%S")

    lines_df = open_dataframes.get_lines(session['d1'], session['h1'], session['h2'])
    zones = open_dataframes.get_zones()
    if len(lines_df) > 0:
        _, lines_df['id_nearest_zone'] = Trees.zones_tree.query(lines_df[['latitude', 'longitude']].values, k=1)
        lines_df["name"] = zones["name"].reindex(index=lines_df['id_nearest_zone']).tolist()

    json_lines = Markup(lines_df.to_json(orient='records'))
    json_zones = Markup(zones.to_json(orient='records'))

    return render_template('zones_map.html',json_zones=json_zones, json_lines=json_lines)


@app.route('/vehicle_map', methods=['GET', 'POST'])
@login_required
def show_vehicle_map():

    try:
        session["map_var"]
        session['form_d1']
        session['form_h1']
        session['form_h2']
        session['d1']
        session['h1']
        session['h2']
    except KeyError:
        session["map_var"] = "elevation"
        session["map_car"] = "seleccione vehiculo"
        now = datetime.now(pytz.timezone('America/Bogota'))
        session['form_d1'] = now.strftime("%d/%m/%Y")
        session['form_h1'] = '0:01 AM'
        session['form_h2'] = now.strftime("%I:%M %p")  # 12H Format
        session['d1'] = now.strftime("%Y-%m-%d")
        session['h1'] = '00:00:00'
        session['h2'] = now.strftime("%H:%M:%S ")

    stations_df = open_dataframes.get_stations()
    json_stations = Markup(stations_df.to_json(orient='records'))

    lines_df = open_dataframes.get_lines(session['d1'], session['h1'], session['h2'])
    json_lines = Markup(lines_df.to_json(orient='records'))

    alturas_df = open_dataframes.get_heights(session["map_var"], session['d1'], session['h1'], session['h2'])
    # current_pos = alturas_df.iloc[1:2]

    session["map_var_pretty"] = open_dataframes.pretty_var_name(session["map_var"])

    if len(lines_df) > 0:
        _, a = Trees.station_tree.query(alturas_df[['latitude', 'longitude']].values, k=2)    # Select neares 2 stations (Knearest)
        alturas_df["closest_st_id1"] = a[:, 0]
        alturas_df["closest_st_id2"] = a[:, 1]
        alturas_df["closest_station1"] = stations_df["name"].reindex(index=alturas_df['closest_st_id1']).tolist()  # map station id with station name (vector)
        alturas_df["closest_station2"] = stations_df["name"].reindex(index=alturas_df['closest_st_id2']).tolist()  # map station2  id with station name (vector)
        # session["closest_station"] = stations_df["name"].iloc[current_pos['id_nearest']].item()    # map station id with station name (current)
    json_operation = Markup(alturas_df.to_json(orient='records'))

    return render_template('vehicle_map.html', json_lines=json_lines, json_operation=json_operation,
                           json_stations=json_stations)

    # return Json para hacer el render en el cliente
    #

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
        if float(request.args["latitude"]) > 0 and ((float(request.args["elevation"]) >  0) and (float(request.args["elevation"]) < 3000)):
            operation = Operation(
                **request.args)  # ** pasa un numero variable de argumentos a la funcion/crea instancia

            operation.timestamp = datetime.strptime(
                (datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')),
                '%Y-%m-%d %H:%M:%S')

            last = Operation.query.order_by(Operation.id.desc()).first()
            delta_t = (operation.timestamp - last.timestamp).total_seconds()
            coords_1 = (last.latitude, last.longitude)
            coords_2 = (float(request.args["latitude"]), float(request.args["longitude"]))
            run = geopy.distance.distance(coords_1, coords_2).m  # meters

            google_url = 'https://maps.googleapis.com/maps/api/elevation/json?locations=' + \
                         request.args["latitude"] + ',' + request.args["longitude"] + \
                         '&key=AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI'

            r = requests.get(google_url).json()
            elevation = r['results'][0]['elevation']
            rise = elevation - last.elevation2
            print('rise = ',rise)
            print('elevation = ', elevation)
            distance = math.sqrt(run ** 2 + rise ** 2)
            operation.elevation2 = elevation
            operation.run = distance

            try:
                slope = math.atan(rise/run)  # radianes
            except ZeroDivisionError:
                slope = 0
            degree = (slope * 180) / math.pi
            operation.slope = degree
            print('slope = ', operation.slope)

            p = 1.2  # Air density kg/m3
            m = float(request.args["mass"])  # kg
            A = 0.303  # 0.79 car 0.303 motorcycle # Frontal area m2
            cr = 0.02  # Rolling coefficient
            cd = 1.8  # 0.29 car 1.8 motorcycle # Drag coefficient
            operation.mean_acc_server = (float(request.args["speed"]) - last.speed) / (delta_t * 3.6)  # km/h to ms

            operation.friction_force = (cr * m * 9.81 * math.cos(operation.slope)) + \
                                       (0.5 * p * A * cd * (float(request.args["speed"]) / 3.6) ** 2)   # km/h to m/s
            Fw = m * 9.81 * math.sin(operation.slope)
            operation.net_force = (m * operation.mean_acc_server) + Fw + operation.friction_force

            print('acceleration = ', operation.mean_acc_server)
            operation.mec_power = (operation.net_force * (float(request.args["speed"]) + last.speed) / 2) * 1.341 / 1000  # Hp
            #operation.mec_power_delta_e = (operation.friction_force + Fw + (m * operation.mean_acc)) * ((float(request.args["speed"]) + last.speed) / 2) * 1.341 / 1000  # Hp
            print('mec_power = ', operation.mec_power)
            operation.en_pot = rise * 9.81 * float(request.args["mass"])   # mgh
            db.session.add(operation)
            db.session.commit()
            return "Data received"
        else:
            return "Null location"


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


@app.route('/map_var', methods=['POST'])
def map_var():
    session["map_var"] = (request.form['map_var'])
    session['form_d1'] = request.form['d1']
    session['form_h1'] = request.form['h1']
    session['form_h2'] = request.form['h2']

    session["d1"] = (datetime.strptime(request.form['d1'], '%d/%m/%Y')).strftime("%Y-%m-%d")
    session["h1"] = (datetime.strptime(request.form['h1'], '%I:%M %p')).strftime("%H:%M:%S")
    session["h2"] = (datetime.strptime(request.form['h2'], '%I:%M %p')).strftime("%H:%M:%S")
    if session["h2"] < session["h1"]:
        session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

    return redirect(url_for('show_vehicle_map'))

@app.route('/zones_interval', methods=['POST'])
def zones_interval():
    session['form_d1'] = request.form['d1']
    session['form_h1'] = request.form['h1']
    session['form_h2'] = request.form['h2']

    session["d1"] = (datetime.strptime(request.form['d1'], '%d/%m/%Y')).strftime("%Y-%m-%d")
    session["h1"] = (datetime.strptime(request.form['h1'], '%I:%M %p')).strftime("%H:%M:%S")
    session["h2"] = (datetime.strptime(request.form['h2'], '%I:%M %p')).strftime("%H:%M:%S")
    if session["h2"] < session["h1"]:
        session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times
    return redirect(url_for('show_zones_map'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'monitor.ico')