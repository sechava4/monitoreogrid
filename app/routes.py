import ast
import json
import logging
import math
import os
from datetime import datetime, timedelta

import geopy.distance
import googlemaps
import numpy as np
import pandas as pd
import pytz
import requests
from flask import (
    request,
    session,
    redirect,
    url_for,
    Markup,
    render_template,
    flash,
    send_from_directory,
    Response,
)
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, open_dataframes, plot, db, consumption_models, degradation_models
from app.Research.Google import google_linear_model as google_query
from app.closest_points import Trees
from app.config import SessionConfig, OperationQuery, CalendarQuery
from app.forms import (
    LoginForm,
    RegistrationForm,
    VehicleRegistrationForm,
    read_form_dates,
)
from app.models import User, Operation, Vehicle

logger = logging.getLogger(__name__)
google_sdk_key = os.environ.get("GOOGLE_SDK_KEY")


# ---------------------------------Vehicle routes ----------------------------------#
@app.route("/my_vehicles/<username>")
@login_required
def my_vehicles(username):
    user = User.query.filter_by(username=username).first_or_404()

    query = 'SELECT * FROM vehicle where user_id = "' + str(user.id) + '"'

    df_vehicles = pd.read_sql_query(query, db.engine)
    print(df_vehicles.to_json(orient="records", indent=True))
    return render_template(
        "vehicle.html", user=user, vehicles=df_vehicles.to_json(orient="records")
    )


@app.route("/update_vehicle/<placa>")
@login_required
def update_vehicle(placa):
    vehicles = Vehicle.query.filter_by(user_id=current_user.id)
    for vehicle in vehicles:
        if vehicle.placa == placa:
            vehicle.activo = True
            print("Activando vehiculo:", placa)
        else:
            vehicle.activo = False
    db.session.commit()
    return redirect(url_for("show_entries"))


@app.route("/register_vehicle", methods=["GET", "POST"])
@login_required
def register_vehicle():
    form = VehicleRegistrationForm()
    if form.validate_on_submit():
        existing_vehicles = (
            db.session.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()
        )
        for existing in existing_vehicles:
            existing.activo = False
        properties = {}
        if form.marca.data == "RENAULT":
            properties.update(dict(cd=0.31, frontal_area=2.43, weight=1528))
        vehicle = Vehicle(
            placa=form.placa.data,
            marca=form.marca.data,
            year=int(form.year.data),
            user_id=current_user.id,
            cd=properties.get("cd"),
            frontal_area=properties.get("frontal_area"),
            weight=properties.get("weight"),
            odometer=0,
            activo=True,
        )
        db.session.add(vehicle)
        db.session.commit()
        flash("Has registrado un nuevo vehículo!")
        return redirect(url_for("my_vehicles", username=current_user.username))
    return render_template("register_vehicle.html", title="Register", form=form)


# ----------------------------------- Dashboards --------------------------------------------------#


@app.route("/", methods=["GET", "POST"])
@login_required
def show_entries():
    """
    main page
    :return:
    """
    query = 'SELECT * FROM vehicle where user_id = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(user_id=current_user.id, activo=True).first()
    now = datetime.now(pytz.timezone("America/Bogota")) + timedelta(hours=1)

    sess_conf = SessionConfig(now)
    sess_conf.assign_missing_variables(session)

    if request.method == "POST":
        for var in [
            "graph_var_y",
            "graph_var_y2",
            "graph_var_y2",
        ]:
            session[var] = request.form[var]

        for var in ["d1", "h1", "h2", "d2", "h3", "h4"]:
            session["form_" + var] = request.form[var]

        read_form_dates(session, day=1, hour=1)  # hours 1 and 2
        read_form_dates(session, day=2, hour=3)  # hours 3 and 4

    if vehicle:
        operation_query = OperationQuery(session, vehicle)
        calendar_query = CalendarQuery(session, vehicle)

        df_calendar = pd.read_sql_query(calendar_query.query, db.engine)
        df_calendar = df_calendar.dropna()
        if session.get("calendar_var") == "drivetime":
            df_calendar["max_value"] = df_calendar["max_value"] / 3600
        df_o = pd.read_sql_query(operation_query.query_1, db.engine)
        df_o2 = pd.read_sql_query(operation_query.query_2, db.engine)

        scatter = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
        scatter2 = plot.create_plot(
            df_o2, session["graph_var_x2"], session["graph_var_y2"]
        )
        box = df_o[session["graph_var_y"]].tolist()
        box2 = df_o2[session["graph_var_y2"]].tolist()

        for var in [
            "graph_var_y",
            "graph_var_y2",
        ]:
            session[var + "_pretty"] = open_dataframes.pretty_var_name(session[var])

        # map graph
        lines_df = open_dataframes.get_lines(
            vehicle, session["d1"], session["h1"], session["h2"]
        )
        json_lines = Markup(lines_df.to_json(orient="records"))

        alturas_df = open_dataframes.get_heights(
            vehicle,
            session["graph_var_y2"],
            session["d1"],
            session["h1"],
            session["h2"],
        )

        session["map_var_pretty"] = open_dataframes.pretty_var_name(session["map_var"])
        json_operation = Markup(alturas_df.to_json(orient="records"))

    else:
        scatter = 0
        scatter2 = 0
        box = 0
        box2 = 0
        df_calendar = pd.DataFrame()
        json_lines = ({},)
        json_operation = ({},)
    return render_template(
        "show_entries.html",
        plot=scatter,
        box=box,
        plot2=scatter2,
        box2=box2,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
        json_lines=json_lines,
        json_operation=json_operation,
    )


@app.route("/updateplot")
def update_plot():
    """
    updates graphs of main page
    :return:
    """
    vehicle = Vehicle.query.filter_by(user_id=current_user.id, activo=True).first()
    if "calendar_var" not in session.keys():
        session["calendar_var"] = "drivetime"

    operation_query = OperationQuery(session, vehicle)
    df_o = pd.read_sql_query(operation_query.query_1, db.engine)
    scatter = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])

    return scatter


@app.route("/energy", methods=["GET", "POST"])
@login_required
def energy_monitor():
    """
    page for energy related features such as consumption prediction and energy regeneration
    :return:
    """
    vehicle = Vehicle.query.filter_by(user_id=current_user.id, activo=True).first()
    now = datetime.now(pytz.timezone("America/Bogota"))
    sess_conf = SessionConfig(now)
    sess_conf.assign_missing_variables(session)

    if request.method == "POST":
        session["time_interval"] = request.form["time_interval"]
        try:
            session["P_ini"] = ast.literal_eval(request.form["pos_o"])
            session["P_fin"] = ast.literal_eval(request.form["pos_d"])
            now = datetime.now()
            gmaps = googlemaps.Client(key=google_sdk_key)
            google_client = gmaps.directions(
                origin=session["P_ini"],
                destination=session["P_fin"],
                mode="driving",
                alternatives=False,
                departure_time=now,
                traffic_model="pessimistic",
            )

            segments = google_query.get_segments(google_client)

            estimation_path = os.path.join(
                app.root_path, "Research/ConsumptionEstimation"
            )
            (
                session["est_cons"],
                session["est_time"],
                _,
            ) = google_query.calculate_segments_consumption(segments, estimation_path)
        except SyntaxError:
            session["est_cons"] = 0
            session["est_time"] = 0

    session["energy_t1"] = now

    number = int(session["time_interval"].split()[0])  # example 10 h selects 20
    unit = session["time_interval"].split()[1]  # example 10 h selects h
    if "h" in unit:
        session["energy_t2"] = now - timedelta(hours=number)
    elif "d" in unit:
        session["energy_t2"] = now - timedelta(days=number)

    operation_query = (
        'SELECT timestamp, power_kw from operation WHERE speed > 0 AND timestamp BETWEEN "'
        + str(session["energy_t2"])
        + '" and "'
        + str(session["energy_t1"])
        + '" ORDER BY timestamp'
    )

    df_o = pd.read_sql_query(operation_query, db.engine)
    try:
        scatter_cons = plot.create_double_plot(df_o, "timestamp", "power_kw")
        donut = plot.create_kwh_donut(df_o, "timestamp", "power_kw", "cons", "regen")
    except TypeError:
        scatter_cons = 0
        donut = 0
    session["t_int_pretty"] = open_dataframes.pretty_var_name(session["time_interval"])

    return render_template(
        "energy_monitor.html",
        plot=scatter_cons,
        donut=donut,
        vehicle=vehicle,
        google_sdk_key=google_sdk_key,
    )


@app.route("/tables", methods=["GET", "POST"])
@login_required
def show_tables():
    """
    page for displaying osm_data in tabular form
    :return:
    """
    query = 'SELECT * FROM vehicle where user_id = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(user_id=current_user.id, activo=True).first()
    now = datetime.now(pytz.timezone("America/Bogota"))
    sess_conf = SessionConfig(now)
    sess_conf.assign_missing_variables(session)

    if request.method == "POST":
        for i in range(1, 6):
            session["var%d" % i] = request.form["var%d" % i]

        session["records"] = request.form["records"]
        for var in ["d1", "h1", "h2"]:
            session["form_" + var] = request.form[var]

        if session["records"] is None:
            session["records"] = 20

        read_form_dates(session, day=1, hour=1)

    if vehicle:
        query = (
            "SELECT timestamp, "
            + session["var1"]
            + " ,"
            + session["var2"]
            + " ,"
            + session["var3"]
            + " ,"
            + session["var4"]
            + " ,"
            + session["var5"]
            + ' from operation WHERE vehicle_id = "'
            + str(vehicle.placa)
            + '" AND timestamp BETWEEN "'
            + session["d1"]
            + " "
            + str(session["h1"])[:8]
            + '" and "'
            + str(session["d1"])
            + " "
            + str(session["h2"])[:8]
            + '" limit '
            + str(session["records"])
        )

        session["query"] = query
        calendar_query = CalendarQuery(session, vehicle)
        df_calendar = pd.read_sql_query(calendar_query.query, db.engine)
        df_calendar = df_calendar.dropna()
        operation_df = pd.read_sql_query(query, db.engine)
        scatter = 0
        integral_jimenez = 0
        integral_power = 0
        integral_fiori = 0
        if (
            all(
                col in operation_df.columns
                for col in ["slope", "speed", "mean_acc", "power_kw"]
            )
            and len(operation_df.columns) == 6
            and len(operation_df) > 1
        ):

            try:
                consumption_models.add_consumption_cols(
                    operation_df,
                    float(vehicle.weight),
                    float(vehicle.frontal_area),
                    float(vehicle.cd),
                )

                scatter = plot.create_plot(
                    operation_df, "jimenez_estimation", "power_kw"
                )
                integral_jimenez = plot.create_plot(
                    operation_df, "timestamp", "jimenez_int"
                )
                integral_fiori = plot.create_plot(
                    operation_df, "timestamp", "fiori_int"
                )
                integral_power = plot.create_plot(
                    operation_df, "timestamp", "power_int"
                )
            except Exception as e:
                print(e)

        else:
            integral_jimenez = 0
            integral_fiori = 0
            integral_power = 0

        if all(col in operation_df.columns for col in ["current", "batt_temp"]):
            degradation_models.add_wang_column(operation_df)
    else:
        integral_jimenez = 0
        integral_fiori = 0
        integral_power = 0
        operation_df = pd.DataFrame([])
        session["query"] = None
        df_calendar = pd.DataFrame([])
        scatter = 0

    session["var1_pretty"] = open_dataframes.pretty_var_name(session["var1"])
    session["var2_pretty"] = open_dataframes.pretty_var_name(session["var2"])
    session["var3_pretty"] = open_dataframes.pretty_var_name(session["var3"])
    session["var4_pretty"] = open_dataframes.pretty_var_name(session["var4"])
    session["var5_pretty"] = open_dataframes.pretty_var_name(session["var5"])
    session["calendar_pretty"] = open_dataframes.pretty_var_name(
        session["calendar_var"]
    )

    return render_template(
        "tables.html",
        tables=[operation_df.to_html(classes="osm_data")],
        titles=operation_df.columns.values,
        plot=scatter,
        plotint1=integral_jimenez,
        plotint2=integral_power,
        plotint3=integral_fiori,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
    )


@app.route("/<username>/download-csv")
def download_csv(username):
    query = session["query"] or "select 1"
    operation = pd.read_sql_query(query, db.engine)
    return Response(
        operation.to_csv(sep=";"),
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=operation-{}.csv".format(
                username
            )
        },
    )


@app.route("/vehicle_map", methods=["GET", "POST"])
@login_required
def show_vehicle_map():
    """
    page for showing osm_data in map
    :return:
    """
    stations_df = open_dataframes.get_stations()
    json_stations = Markup(stations_df.to_json(orient="records"))

    query = 'SELECT * FROM vehicle where user_id = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle_list = []
    for vehicle in (
        db.session.query(Vehicle.placa)
        .filter_by(user_id=current_user.id)
        .distinct()
        .all()
    ):
        last = (
            db.session.query(Operation)
            .filter(Operation.vehicle_id == vehicle.placa)
            .order_by(Operation.id.desc())
            .first()
        )
        keys = ["latitude", "longitude", "elevation", "vehicle_id", "timestamp"]

        if last:
            last = {key: value for key, value in last.__dict__.items() if key in keys}
            last["name"] = last.get("vehicle_id")
            # Closest station
            _, st_id = Trees.station_tree.query(
                np.array([last["latitude"], last["longitude"]]).reshape(1, -1), k=1
            )
            last["closest_station"] = (
                stations_df["name"].reindex(index=st_id[0]).tolist()
            )
            vehicle_list.append(last)

    return render_template(
        "vehicle_map.html",
        json_stations=json_stations,
        json_operation=json.dumps(vehicle_list, default=str),
        vehicles=df_vehicles.to_json(orient="records"),
    )


# --------------------------------- IoT routes ---------------------------------------------------#


@app.route("/addjson", methods=["POST", "GET"])
def add_entry():
    """
    communication route for handling incoming vehicle data
    """
    # If its coming in json format:
    if request.method == "POST":
        args = request.get_json()

    # If its coming by url
    else:
        args = request.args

    if not args:
        return "Null osm_data"
    else:
        operation = Operation(**args)
        operation.timestamp = datetime.strptime(
            (
                datetime.now(pytz.timezone("America/Bogota")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ),
            "%Y-%m-%d %H:%M:%S",
        )

        last = (
            db.session.query(Operation)
            .filter(Operation.vehicle_id == args.get("vehicle_id"))
            .order_by(Operation.id.desc())
            .first()
        )

        coords_2 = (float(args.get("latitude")), float(args.get("longitude")))

        if last:
            delta_t = (operation.timestamp - last.timestamp).total_seconds()
            coords_1 = (last.latitude, last.longitude)

        else:
            coords_1 = coords_2
            delta_t = 7

        run = geopy.distance.distance(coords_1, coords_2).m  # meters
        operation.run = run
        print(operation.vehicle_id)
        vehicle = Vehicle.query.filter_by(placa=operation.vehicle_id).first()
        if not vehicle:
            return "Please create the vehicle first"
        try:
            vehicle.odometer = float(args.get("odometer", vehicle.odometer + run))
        except TypeError:
            vehicle.odometer = run

        vehicle.weight = float(args.get("mass"))
        if "bote" in operation.vehicle_id.lower():
            operation.mec_power, operation.net_force = consumption_models.zavitsky(
                (float(operation.mean_speed) / 3.6),
                float(operation.mean_acc),
                float(vehicle.weight),
            )
        elif "RENAULT" in vehicle.marca:
            # JIMENEZ MODEL IMPLEMENTATION
            consumption_values = consumption_models.jimenez(
                vehicle.weight,
                float(vehicle.frontal_area),
                float(vehicle.cd),
                operation.slope,
                float(operation.mean_speed),
                float(operation.mean_acc),
            )

            operation.consumption = float(consumption_values[0])
            operation.mec_power = float(consumption_values[1])
            operation.net_force = float(consumption_values[2])
            operation.friction_force = float(consumption_values[3])

            # WANG MODEL IMPLEMENTATION
            current = float(args.get("current", 0))
            if current:
                ah = current * delta_t / 3600
                c_rate = current / 100  # 100 = Amperios hora totales bateria
                if c_rate > 0:
                    b = 448.96 * c_rate ** 2 - 6301.1 * c_rate + 33840
                    operation.q_loss = (
                        b
                        * math.exp(
                            (-31700 + (c_rate * 370.3))
                            / (8.314472 * (float(args.get("batt_temp", 22))))
                        )
                        * ah ** 0.552
                    )
                else:
                    operation.q_loss = 0

        db.session.add(operation)
        db.session.commit()
        return "Data received"


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    login page
    :return:
    """
    if current_user.is_authenticated:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        return redirect(url_for("show_vehicle_map"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("show_vehicle_map")
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    register page
    :return:
    """
    if current_user.is_authenticated:
        return redirect(url_for("show_vehicle_map"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/logout")
def logout():
    """
    logout page
    :return:
    """
    logout_user()
    return redirect(url_for("show_entries"))


@app.route("/map_var", methods=["POST"])
def map_var():
    """
    redirects when map form is submitted
    :return:
    """
    session["map_var"] = request.form["map_var"]
    for var in ["d1", "h1", "h2"]:
        session["form_" + var] = request.form[var]

    read_form_dates(session, day=1, hour=1)

    return redirect(url_for("show_vehicle_map"))


@app.route("/favicon.ico")
def favicon():
    """
    favicon
    """
    return send_from_directory(os.path.join(app.root_path, "static"), "monitor.ico")
