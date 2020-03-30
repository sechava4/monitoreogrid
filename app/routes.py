from app import app, openmaps, map, plot, db
from app.forms import LoginForm, RegistrationForm
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
    except KeyError:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
    query = "SELECT " + session["graph_var_x"] + " ," + session["graph_var_y"] + " from operation"
    df = pd.read_sql_query(query, db.engine)
    # stations_map.plot_data(stations_df)
    bar = plot.create_plot(df, session["graph_var_x"],session["graph_var_y"])

    return render_template('show_entries.html', plot=bar)



@app.route('/tables')
@login_required
def show_tables():
    df = pd.read_sql_query("SELECT * from vehicle", db.engine,index_col="id")
    # df.drop(["password_hash"], axis=1, inplace=True)
    return render_template('tables.html', tables=[df.to_html(classes='data')], titles=df.columns.values)


@app.route('/stations_map')
@login_required
def show_stations_map():
    # Map rendering
    stations_df = openmaps.get_stations()
    session["json_stations"] = Markup(stations_df.to_json(orient='records'))
    return render_template('stations_map.html')


@app.route('/zones_map')
@login_required
def show_zones_map():
    # Map rendering
    stations_df = openmaps.get_zones()
    session["json_zones"] = Markup(stations_df.to_json(orient='records'))
    # print(session["json_zones"])
    return render_template('zones_map.html')


@app.route('/vehicle_map')
@login_required
def show_vehicle_map():
    try:
        session["map_var"]
    except KeyError:
        session["map_var"] = "soc"
        session["map_car"] = "seleccione vehiculo"


    session["title_var"] = str(session["map_var"]).replace('_', ' ').lower()
    print(session["title_var"])
    df = pd.read_sql_query("SELECT * from operation", db.engine)
    session["json_operation"] = Markup(df.to_json(orient='records'))

    return render_template('vehicle_map.html')



@app.route('/gauges')
@login_required
def show_indicators():
    df = pd.read_sql_query("SELECT * from entries limit 1", db.engine)
    titles = df.columns.values
    return render_template('indicators.html')


@app.route('/addjson', methods=['POST'])
def add_entry():

    df = pd.read_sql_query("SELECT * from entries", db.engine,index_col="id")
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
        return redirect(url_for('show_zones_map'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('show_zones_map')
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

# Icon webpage
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'monitor.ico')