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
import math

@app.route('/')
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


    #print(session['d1'].strftime("%Y-%m-%d"))
    # t1 = datetime.strptime(session['t1'], '%m/%d/%Y %I:%M %p')
    # t2 = datetime.strptime(session['t2'], '%m/%d/%Y %I:%M %p')
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d1'] + ' ' + str(session['h1'])[:8] + \
            '" and "' + str(session['d1']) + ' ' + str(session['h2'])[:8] + '"'

    # conn = db.engine.connect()
    # a = conn.execute(query).fetchall()
    df_o = pd.read_sql_query(query, db.engine)

    scatter, donnut = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])
    return render_template('show_entries.html', plot=scatter, pie=donnut)


@app.route('/updateplot')
def update_plot():
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + \
            ' from operation WHERE timestamp BETWEEN "' + session['d1'] + ' ' + str(session['h1'])[:8] + \
            '" and "' + str(session['d1']) + ' ' + str(session['h2'])[:8] + '"'

    df_o = pd.read_sql_query(query, db.engine)
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
    json_zones = Markup(zones.to_json(orient='records'))

    _, lines_df['id_nearest_zone'] = Trees.zones_tree.query(lines_df[['latitude', 'longitude']].values, k=1)
    lines_df["name"] = zones["name"].reindex(index=lines_df['id_nearest_zone']).tolist()
    json_lines = Markup(lines_df.to_json(orient='records'))

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
        if float(request.args["latitude"]) > 0:

            '''
            last = Operation.query.order_by(Operation.id.desc()).first()
            coords_1 = (last.latitude, last.longitude)
            coords_2 = (float(request.args["latitude"]), float(request.args["longitude"]))
            run = geopy.distance.distance(coords_1, coords_2).m      # meters

            
            rise = float(request.args["elevation"]) - last.elevation
            distance = math.sqrt(run**2 + rise**2)

            try:
                operation.slope = math.atan(rise/run)  # Conversión a radianes
            except ZeroDivisionError:
                operation.slope = 0
            print(operation.slope)

            '''
            operation = Operation(
                **request.args)  # ** pasa un numero variable de argumentos a la funcion/crea instancia
            operation.timestamp = datetime.strptime(
                (datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')),
                '%Y-%m-%d %H:%M:%S')

            '''
            delta_t = (operation.timestamp - last.timestamp).total_seconds()   # SECONDS

            p = 1.2   # Air density kg/m3
            m = float(request.args["mass"])   # kg
            A = 0.790   # Frontal area m2
            cr = 0.01   # Rolling cohef
            cd = 0.2   # Drag cohef
            operation.mean_acc = (float(request.args["speed"]) - last.speed ) / (delta_t * 3.6)   # km/h to ms

            Fd = (cr * m * 9.81 * math.cos(operation.slope)) + (                                       # Rolling Comp
                        0.5 * p * A * cd * ((float(request.args["speed"]) + last.speed) / 7.2) ** 2)   # km/h to ms

            Fw = m * 9.81 * math.sin(operation.slope)
            F = (m * operation.mean_acc) + Fw + Fd

            # print(operation.mean_acc)
            # print(Fd, Fw, F)
            operation.mec_power = F * (float(request.args["speed"]) + last.speed) / (2*3.6*1000)   # Potencia promedio Kw


            E1 = 0.5 * m * (last.speed / 3.6) ** 2  + (m * 9.81 * last.elevation)
            E2 = 0.5 * m * (float(request.args["speed"]) / 3.6) ** 2  + (m * 9.81 * float(request.args["elevation"]))
            Wf = Fd   # Work done by friction
            operation.mec_power_delta_e = ((E2 - E1) / (delta_t * 1000))   # Kw
            print(E1, E2)
            # print(operation.__dict__)
            '''
            db.session.add(operation)
            db.session.commit()
            return ("Data recieved")#redirect(url_for('show_entries'))
        else:
            return ("Null location")

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
    session['form_d1'] = request.form['d1']
    session['form_h1'] = request.form['h1']
    session['form_h2'] = request.form['h2']

    session["d1"] = (datetime.strptime(request.form['d1'], '%d/%m/%Y')).strftime("%Y-%m-%d")
    session["h1"] = (datetime.strptime(request.form['h1'], '%I:%M %p')).strftime("%H:%M:%S")
    session["h2"] = (datetime.strptime(request.form['h2'], '%I:%M %p')).strftime("%H:%M:%S")
    if session["h2"] < session["h1"]:
        session["h1"], session["h2"] = session["h2"], session["h1"] # Swap times

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