from app import app, open_dataframes, plot, db
from app.forms import LoginForm, RegistrationForm, TablesForm, VehicleMapForm
from flask import Flask, request, session, g, redirect, url_for, Markup, \
    render_template, flash,send_from_directory # g stands for global
import pandas as pd
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Operation
import os



@app.route('/')
@login_required
def show_entries():
    try:
        session["graph_var_x"]
        session["graph_var_y"]
        session["dataset"]
        session["day"]
    except KeyError:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        session["dataset"] = "rutas.csv"
        session["day"] = 1

    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + " from operation"
    # df = pd.read_sql_query(query, db.engine)

    doc_dataset = os.path.join(app.root_path, session["dataset"])
    df = pd.read_csv(doc_dataset, index_col="id")

    try:
        df = df[df["day"] == int(session["day"])]
    except ValueError:
        session["day"] = 1
        df = df[df["day"] == int(session["day"])]

    if session["graph_var_y"] not in df.columns:
        session["graph_var_y"] = "soc"

    if session["graph_var_x"] not in df.columns:
        session["graph_var_x"] = "timestamp"

    bar = plot.create_plot(df, session["graph_var_x"], session["graph_var_y"])
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])
    return render_template('show_entries.html', plot=bar)


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


@app.route('/zones_map')
@login_required
def show_zones_map():
    # Map rendering
    stations_df = open_dataframes.get_zones()
    session["json_zones"] = Markup(stations_df.to_json(orient='records'))
    return render_template('zones_map.html')


@app.route('/vehicle_map', methods=['GET', 'POST'])
@login_required
def show_vehicle_map():
    form = VehicleMapForm()
    if form.is_submitted():
        session["day"] = form.day.data
        session["map_var"] = form.variable.data

    try:
        session["map_var"]
    except KeyError:
        session["map_var"] = "elevation"
        session["map_car"] = "seleccione vehiculo"

    lines_df = open_dataframes.get_lines(session["day"])
    session["json_lines"] = Markup(lines_df.to_json(orient='records'))

    alturas = open_dataframes.alturas_df(session["map_var"], session["day"])
    session["json_operation"] = Markup(alturas.to_json(orient='records'))

    titles = alturas.columns.values
    form.variable.choices = open_dataframes.form_var(titles)

    session["title_var"] = open_dataframes.pretty_var_name(session["map_var"])

    # query = "SELECT longitude, latitude, " + session["map_var"] + " from operation"
    # df = pd.read_sql_query("SELECT * from operation", db.engine)

    return render_template('vehicle_map.html', form=form)



@app.route('/gauges')
@login_required
def show_indicators():
    df = pd.read_sql_query("SELECT * from operation limit 1", db.engine)
    titles = df.columns.values
    return render_template('indicators.html')


@app.route('/addjson', methods=['POST'])
def add_entry():

    df = pd.read_sql_query("SELECT * from operation limit 1", db.engine,index_col="id")
    titles = Operation.query.limit(1)
    titles = df.columns.values
    content = {}
    for col in titles:
        if col == "id":
            continue
        # Create dict
        content[col] = request.args[col]

    operation = User(content)
    db.session.add(operation)
    db.session.commit()
    flash('New data arrived')
    return redirect(url_for('show_entries'))


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
    session["dataset"] = (request.form['dataset'])
    session["day"] = (request.form['day'])
    return redirect(url_for('show_entries'))
    # return render_template('show_entries.html')

# Icon webpage
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'monitor.ico')