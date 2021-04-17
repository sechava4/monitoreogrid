import os
import math

from flask import (
    request,
    session,
    redirect,
    url_for,
    Markup,
    render_template,
    flash,
    send_from_directory,
    Response
)
import pandas as pd
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
import geopy.distance
from datetime import datetime, timedelta
import pytz
import ast
import googlemaps
import requests
from scipy import stats
from app import app, open_dataframes, plot, db, consumption_models, degradation_models
from app.Investigation.Google import google_linear_model as google_query
from app.closest_points import Trees
from app.forms import LoginForm, RegistrationForm, VehicleRegistrationForm
from app.models import User, Operation, Vehicle


# ---------------------------------Vehicle routes ----------------------------------#
@app.route("/my_vehicles/<username>")
@login_required
def my_vehicles(username):
    user = User.query.filter_by(username=username).first_or_404()

    query = 'SELECT * FROM vehicle where belongs_to = "' + str(user.id) + '"'

    df_vehicles = pd.read_sql_query(query, db.engine)
    print(df_vehicles.to_json(orient="records", indent=True))
    return render_template(
        "vehicle.html", user=user, vehicles=df_vehicles.to_json(orient="records")
    )


@app.route("/update_vehicle/<placa>")
@login_required
def update_vehicle(placa):
    vehicles = Vehicle.query.filter_by(belongs_to=current_user.id)
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
        print(current_user.id)
        vehicle = Vehicle(
            placa=form.placa.data,
            marca=form.marca.data,
            year=int(form.year.data),
            belongs_to=current_user.id,
            odometer=0,
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
    query = 'SELECT * FROM vehicle where belongs_to = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    now = datetime.now(pytz.timezone("America/Bogota")) + timedelta(hours=1)
    try:
        session["graph_var_x"]
        session["graph_var_y"]
        session["form_d1"]
        session["form_h1"]
        session["form_h2"]
        session["d1"]
        session["h1"]
        session["h2"]
        session["calendar_var"]

    except KeyError:

        session["form_d1"] = now.strftime("%d/%m/%Y")
        session["form_h1"] = "0:01 AM"
        session["form_h2"] = now.strftime("%I:%M %p")  # 12H Format
        session["d1"] = now.strftime("%Y-%m-%d")
        session["h1"] = "00:00:00"
        session["h2"] = now.strftime("%H:%M:%S")
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "power_kw"
        session["calendar_var"] = "power_kw"
    try:
        session["graph_var_x2"]
        session["graph_var_y2"]
        session["form_d2"]
        session["form_h3"]
        session["form_h4"]
        session["d2"]
        session["h3"]
        session["h4"]

    except KeyError:
        session["form_d2"] = now.strftime("%d/%m/%Y")
        session["form_h3"] = "0:01 AM"
        session["form_h4"] = now.strftime("%I:%M %p")  # 12H Format
        session["d2"] = now.strftime("%Y-%m-%d")
        session["h3"] = "00:00:00"
        session["h4"] = now.strftime("%H:%M:%S")
        session["graph_var_x2"] = "timestamp"
        session["graph_var_y2"] = "power_kw"

    if request.method == "POST":

        session["graph_var_x"] = request.form["variable_x"]
        session["graph_var_y"] = request.form["variable_y"]
        session["calendar_var"] = request.form["calendar_var"]

        session["form_d1"] = request.form["d1"]
        session["form_h1"] = request.form["h1"]
        session["form_h2"] = request.form["h2"]

        session["d1"] = (datetime.strptime(request.form["d1"], "%d/%m/%Y")).strftime(
            "%Y-%m-%d"
        )
        session["h1"] = (datetime.strptime(request.form["h1"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        session["h2"] = (datetime.strptime(request.form["h2"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        if session["h2"] < session["h1"]:
            session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

        session["graph_var_x2"] = request.form["variable_x2"]
        session["graph_var_y2"] = request.form["variable_y2"]
        session["form_d2"] = request.form["d2"]
        session["form_h3"] = request.form["h3"]
        session["form_h4"] = request.form["h4"]

        session["d2"] = (datetime.strptime(request.form["d2"], "%d/%m/%Y")).strftime(
            "%Y-%m-%d"
        )
        session["h3"] = (datetime.strptime(request.form["h3"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        session["h4"] = (datetime.strptime(request.form["h4"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        if session["h4"] < session["h3"]:
            session["h3"], session["h4"] = session["h4"], session["h3"]  # Swap times

    if vehicle is not None:

        query0 = (
            "SELECT date(timestamp), MAX("
            + session["calendar_var"]
            + ") as 'max_value' FROM operation WHERE vehicle_id = '"
            + str(vehicle.placa)
            + "' GROUP BY date(timestamp)"
        )

        query1 = (
            "SELECT "
            + session["graph_var_x"]
            + " ,"
            + session["graph_var_y"]
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
            + '"'
        )

        query2 = (
            "SELECT "
            + session["graph_var_x2"]
            + " ,"
            + session["graph_var_y2"]
            + ' from operation WHERE vehicle_id = "'
            + str(vehicle.placa)
            + '" AND timestamp BETWEEN "'
            + session["d2"]
            + " "
            + str(session["h3"])[:8]
            + '" and "'
            + str(session["d2"])
            + " "
            + str(session["h4"])[:8]
            + '"'
        )

        # df_exp = pd.read_csv('app/old_vehicle_operation.csv', sep=',', index_col=0, decimal=".")
        # df['timestamp'] = pd.to_datetime(df['timestamp'])"
        # df_exp.to_sql('DB',db.engine )

        df_calendar = pd.read_sql_query(query0, db.engine)
        df_calendar = df_calendar.dropna()
        df_o = pd.read_sql_query(query1, db.engine)
        df_o2 = pd.read_sql_query(query2, db.engine)

        try:
            pearson_coef = stats.pearsonr(
                df_o[session["graph_var_x"]].to_numpy(),
                df_o[session["graph_var_y"]].to_numpy(),
            )
        except (ValueError, TypeError):
            pearson_coef = 0
            pass

        scatter = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
        scatter2 = plot.create_plot(
            df_o2, session["graph_var_x2"], session["graph_var_y2"]
        )
        box = df_o[session["graph_var_y"]].tolist()
        box2 = df_o2[session["graph_var_y2"]].tolist()
        session["calendar_pretty"] = open_dataframes.pretty_var_name(
            session["calendar_var"]
        )
        session["x_pretty_graph"] = open_dataframes.pretty_var_name(
            session["graph_var_x"]
        )
        session["y_pretty_graph"] = open_dataframes.pretty_var_name(
            session["graph_var_y"]
        )

        session["x_pretty_graph2"] = open_dataframes.pretty_var_name(
            session["graph_var_x2"]
        )
        session["y_pretty_graph2"] = open_dataframes.pretty_var_name(
            session["graph_var_y2"]
        )
    else:
        scatter = 0
        scatter2 = 0
        box = 0
        box2 = 0
        df_calendar = pd.DataFrame()
    return render_template(
        "show_entries.html",
        plot=scatter,
        box=box,
        plot2=scatter2,
        box2=box2,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
    )


@app.route("/updateplot")
def update_plot():
    """
    updates graphs of main page
    :return:
    """
    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    try:

        session["calendar_var"]
    except KeyError:
        session["calendar_var"] = "power_kw"

    "SELECT date(timestamp), MAX(" + session[
        "calendar_var"
    ] + ") as 'max_value' FROM operation WHERE vehicle_id = '" + str(
        vehicle.placa
    ) + "' GROUP BY date(timestamp)"

    query = (
        "SELECT "
        + session["graph_var_x"]
        + " ,"
        + session["graph_var_y"]
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
        + '"'
    )

    query2 = (
        "SELECT "
        + session["graph_var_x2"]
        + " ,"
        + session["graph_var_y2"]
        + ' from operation WHERE vehicle_id = "'
        + str(vehicle.placa)
        + '" AND timestamp BETWEEN "'
        + session["d2"]
        + " "
        + str(session["h3"])[:8]
        + '" and "'
        + str(session["d2"])
        + " "
        + str(session["h4"])[:8]
        + '"'
    )

    df_o = pd.read_sql_query(query, db.engine)
    df_o2 = pd.read_sql_query(query2, db.engine)
    scatter = plot.create_plot(df_o, session["graph_var_x"], session["graph_var_y"])
    scatter2 = plot.create_plot(df_o2, session["graph_var_x2"], session["graph_var_y2"])
    session["calendar_pretty"] = open_dataframes.pretty_var_name(
        session["calendar_var"]
    )
    session["x_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_x"])
    session["y_pretty_graph"] = open_dataframes.pretty_var_name(session["graph_var_y"])

    session["x_pretty_graph2"] = open_dataframes.pretty_var_name(
        session["graph_var_x2"]
    )
    session["y_pretty_graph2"] = open_dataframes.pretty_var_name(
        session["graph_var_y2"]
    )
    return scatter


@app.route("/energy", methods=["GET", "POST"])
@login_required
def energy_monitor():
    """
    page for energy related features such as consumption prediction and energy regeneration
    :return:
    """
    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    try:
        session["time_interval"]
        session["est_cons"]
        session["est_time"]
        session["lights"]
    except KeyError:
        session["time_interval"] = "2 d"
        session["est_time"] = 0
        session["est_cons"] = 0
        session["lights"] = 0

    if request.method == "POST":
        session["time_interval"] = request.form["time_interval"]
        try:
            session["P_ini"] = ast.literal_eval(request.form["pos_o"])
            session["P_fin"] = ast.literal_eval(request.form["pos_d"])
            now = datetime.now(pytz.timezone("America/Bogota"))
            print(session["P_fin"])
            gmaps = googlemaps.Client(key="AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI")
            a = gmaps.directions(
                origin=session["P_ini"],
                destination=session["P_fin"],
                mode="driving",
                alternatives=False,
                departure_time=now,
                traffic_model="pessimistic",
            )  # departure_time=now

            segments = google_query.get_segments(a)

            estimation_path = os.path.join(
                app.root_path, "Develops/ConsumptionEstimationJournal"
            )
            # session['est_cons'], session['est_time'] = consumption_models.smartcharging_consumption_query(new_df)
            (
                session["est_cons"],
                session["est_time"],
                _,
            ) = google_query.calculate_consumption(segments, estimation_path)
        except SyntaxError:
            session["est_cons"] = 0
            session["est_time"] = 0

    # print(session["time_interval"])
    now = datetime.now(pytz.timezone("America/Bogota"))
    session["energy_t1"] = now

    number = int(session["time_interval"].split()[0])  # example 10 h selects 20
    unit = session["time_interval"].split()[1]  # example 10 h selects h
    if "h" in unit:
        session["energy_t2"] = now - timedelta(hours=number)
    elif "d" in unit:
        session["energy_t2"] = now - timedelta(days=number)

    query1 = (
        'SELECT timestamp, power_kw from operation WHERE speed > 0 AND timestamp BETWEEN "'
        + str(session["energy_t2"])
        + '" and "'
        + str(session["energy_t1"])
        + '" ORDER BY timestamp'
    )

    df_o = pd.read_sql_query(query1, db.engine)
    try:
        scatter_cons = plot.create_double_plot(df_o, "timestamp", "power_kw")
        donut = plot.create_kwh_donut(df_o, "timestamp", "power_kw", "cons", "regen")
    except TypeError:
        scatter_cons = 0
        donut = 0
    session["t_int_pretty"] = open_dataframes.pretty_var_name(session["time_interval"])

    return render_template(
        "energy_monitor.html", plot=scatter_cons, donut=donut, vehicle=vehicle
    )


@app.route("/tables", methods=["GET", "POST"])
@login_required
def show_tables():
    """
    page for displaying osm_data in tabular form
    :return:
    """
    query = 'SELECT * FROM vehicle where belongs_to = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    try:
        session["var1"]
        session["var2"]
        session["var3"]
        session["var4"]
        session["var5"]
        session["records"]
    except KeyError:

        session["var1"] = "odometer"
        session["var2"] = "speed"
        session["var3"] = "mean_acc"
        session["var4"] = "power_kw"
        session["var5"] = "slope"
        session["records"] = 200

    if request.method == "POST":
        session["var1"] = request.form["var1"]
        session["var2"] = request.form["var2"]
        session["var3"] = request.form["var3"]
        session["var4"] = request.form["var4"]
        session["var5"] = request.form["var5"]
        session["records"] = request.form["records"]
        session["form_d1"] = request.form["d1"]
        session["form_h1"] = request.form["h1"]
        session["form_h2"] = request.form["h2"]
        if session["records"] is None:
            session["records"] = 20

        session["d1"] = (datetime.strptime(request.form["d1"], "%d/%m/%Y")).strftime(
            "%Y-%m-%d"
        )
        session["h1"] = (datetime.strptime(request.form["h1"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        session["h2"] = (datetime.strptime(request.form["h2"], "%I:%M %p")).strftime(
            "%H:%M:%S"
        )
        if session["h2"] < session["h1"]:
            session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

    if vehicle is not None:

        query0 = (
            "SELECT date(timestamp), MAX("
            + session["calendar_var"]
            + ") as 'max_value' FROM operation WHERE vehicle_id = '"
            + str(vehicle.placa)
            + "' GROUP BY date(timestamp)"
        )

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

        df_calendar = pd.read_sql_query(query0, db.engine)
        df_calendar = df_calendar.dropna()
        df = pd.read_sql_query(query, db.engine)
        scatter = 0
        integral_jimenez = 0
        integral_power = 0
        integral_fiori = 0
        if (
            all(elem in list(df) for elem in ["slope", "speed", "mean_acc", "power_kw"])
            and len(set(list(df))) == 6
            and len(df) > 1
        ):

            try:
                consumption_models.add_consumption_cols(
                    df,
                    float(vehicle.weight),
                    float(vehicle.frontal_area),
                    float(vehicle.cd),
                )

                scatter = plot.create_plot(df, "jimenez_estimation", "power_kw")
                integral_jimenez = plot.create_plot(df, "timestamp", "jimenez_int")
                integral_fiori = plot.create_plot(df, "timestamp", "fiori_int")
                integral_power = plot.create_plot(df, "timestamp", "power_int")
            except Exception as e:
                print(e)

        else:
            integral_jimenez = 0
            integral_fiori = 0
            integral_power = 0

        if all(elem in list(df) for elem in ["current", "batt_temp"]):
            degradation_models.add_wang_column(df)
    else:
        integral_jimenez = 0
        integral_fiori = 0
        integral_power = 0
        df = pd.DataFrame([])
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
        tables=[df.to_html(classes="osm_data")],
        titles=df.columns.values,
        plot=scatter,
        plotint1=integral_jimenez,
        plotint2=integral_power,
        plotint3=integral_fiori,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
    )


@app.route("/<username>/download-csv")
def download_csv(username):
    query = session["query"] or 'select * from operation limit 1000'
    operation = pd.read_sql_query(query, db.engine)
    return Response(
        operation.to_csv(sep=";"),
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=operation.csv"})


@app.route("/zones_map", methods=["GET", "POST"])
@login_required
def show_zones_map():
    """
    page for showing sit zones
    :return:
    """
    query = 'SELECT * FROM vehicle where belongs_to = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    try:
        session["form_d1"]
        session["form_h1"]
        session["form_h2"]
        session["d1"]
        session["h1"]
        session["h2"]
        session["calendar_var"]

    except KeyError:
        now = datetime.now(pytz.timezone("America/Bogota"))
        session["form_d1"] = now.strftime("%d/%m/%Y")
        session["form_h1"] = "0:01 AM"
        session["form_h2"] = now.strftime("%I:%M %p")  # 12H Format
        session["d1"] = now.strftime("%Y-%m-%d")
        session["h1"] = "00:00:00"
        session["h2"] = now.strftime("%H:%M:%S")
        session["calendar_var"] = "power_kw"

    # if vehicle is not None:

    query0 = (
        "SELECT date(timestamp), MAX("
        + session["calendar_var"]
        + ") as 'max_value' FROM operation WHERE vehicle_id = '"
        + str(vehicle.placa)
        + "' GROUP BY date(timestamp)"
    )

    df_calendar = pd.read_sql_query(query0, db.engine)
    session["calendar_pretty"] = open_dataframes.pretty_var_name(
        session["calendar_var"]
    )
    zones = open_dataframes.get_zones()
    json_zones = Markup(zones.to_json(orient="records"))

    if vehicle is not None:

        lines_df = open_dataframes.get_lines(
            vehicle, session["d1"], session["h1"], session["h2"]
        )
        if len(lines_df) > 0:
            _, lines_df["id_nearest_zone"] = Trees.zones_tree.query(
                lines_df[["latitude", "longitude"]].values, k=1
            )
            lines_df["name"] = (
                zones["name"].reindex(index=lines_df["id_nearest_zone"]).tolist()
            )

        json_lines = Markup(lines_df.to_json(orient="records"))
    else:
        json_lines = 0

    return render_template(
        "zones_map.html",
        json_zones=json_zones,
        json_lines=json_lines,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
    )


@app.route("/vehicle_map", methods=["GET", "POST"])
@login_required
def show_vehicle_map():
    """
    page for showing osm_data in map
    :return:
    """
    query = 'SELECT * FROM vehicle where belongs_to = "' + str(current_user.id) + '"'
    df_vehicles = pd.read_sql_query(query, db.engine)

    vehicle = Vehicle.query.filter_by(belongs_to=current_user.id, activo=True).first()
    try:
        session["map_var"]
        session["form_d1"]
        session["form_h1"]
        session["form_h2"]
        session["d1"]
        session["h1"]
        session["h2"]
        session["calendar_var"]
    except KeyError:
        session["map_var"] = "elevation"
        session["map_car"] = "seleccione vehiculo"
        now = datetime.now(pytz.timezone("America/Bogota"))
        session["form_d1"] = now.strftime("%d/%m/%Y")
        session["form_h1"] = "0:01 AM"
        session["form_h2"] = now.strftime("%I:%M %p")  # 12H Format
        session["d1"] = now.strftime("%Y-%m-%d")
        session["h1"] = "00:00:00"
        session["h2"] = now.strftime("%H:%M:%S ")
        session["calendar_var"] = "power_kw"

    query0 = (
        "SELECT date(timestamp), MAX("
        + session["calendar_var"]
        + ") as 'max_value' FROM operation WHERE vehicle_id = '"
        + str(vehicle.placa)
        + "' GROUP BY date(timestamp)"
    )

    df_calendar = pd.read_sql_query(query0, db.engine)
    session["calendar_pretty"] = open_dataframes.pretty_var_name(
        session["calendar_var"]
    )

    stations_df = open_dataframes.get_stations()
    json_stations = Markup(stations_df.to_json(orient="records"))

    if vehicle is not None:

        lines_df = open_dataframes.get_lines(
            vehicle, session["d1"], session["h1"], session["h2"]
        )
        json_lines = Markup(lines_df.to_json(orient="records"))

        alturas_df = open_dataframes.get_heights(
            vehicle, session["map_var"], session["d1"], session["h1"], session["h2"]
        )
        # current_pos = alturas_df.iloc[1:2]

        session["map_var_pretty"] = open_dataframes.pretty_var_name(session["map_var"])

        if len(lines_df) > 0:
            # Select nearest 2 stations (K-nearest)
            _, a = Trees.station_tree.query(
                alturas_df[["latitude", "longitude"]].values, k=2
            )
            alturas_df["closest_st_id1"] = a[:, 0]
            alturas_df["closest_st_id2"] = a[:, 1]
            alturas_df["closest_station1"] = (
                stations_df["name"].reindex(index=alturas_df["closest_st_id1"]).tolist()
            )  # map station id with station name
            alturas_df["closest_station2"] = (
                stations_df["name"].reindex(index=alturas_df["closest_st_id2"]).tolist()
            )  # map station2  id with station name
        json_operation = Markup(alturas_df.to_json(orient="records"))
    else:
        json_lines = 0
        json_operation = 0

    return render_template(
        "vehicle_map.html",
        json_lines=json_lines,
        json_operation=json_operation,
        json_stations=json_stations,
        calendar=df_calendar.to_json(orient="records"),
        vehicles=df_vehicles.to_json(orient="records"),
    )

    # return Json para hacer el render en el cliente


# --------------------------------- IoT routes ---------------------------------------------------#


@app.route("/addjson", methods=["POST", "GET"])
def add_entry():
    """
    communication route for handling incoming vehicle osm_data
    """
    # If its coming in json format:
    if request.method == "POST":
        args = request.get_json()

    # If its coming by url
    else:
        args = request.args

    if not bool(args):
        return "Null osm_data"
    else:
        if float(args["latitude"]) > 0:
            operation = Operation(
                **args
            )  # ** pasa un numero variable de argumentos a la funcion/crea instancia

            operation.timestamp = datetime.strptime(
                (
                    datetime.now(pytz.timezone("America/Bogota")).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                ),
                "%Y-%m-%d %H:%M:%S",
            )

            # insert into vehicle(placa, marca, modelo, year, odometer) values('BOTE01', 'ENERGETICA', 'ECO100', 2011, 10)
            # operation.angle_y = -float(request.args["angle_y"]) - 9.27

            # Si es el primer dato de ese vehículo
            last = args
            query = (
                'SELECT * FROM operation where vehicle_id = "'
                + args["vehicle_id"]
                + '" ORDER  BY id DESC LIMIT 1'
            )

            # Select the last from the same vehicle that is incoming
            with db.engine.connect() as con:
                rs = con.execute(query)
                for row in rs:
                    last = row

            coords_2 = (float(args["latitude"]), float(args["longitude"]))
            google_url = (
                "https://maps.googleapis.com/maps/api/elevation/json?locations="
                + str(args["latitude"])
                + ","
                + str(args["longitude"])
                + "&key=AIzaSyChV7Sy3km3Fi8hGKQ8K9t7n7J9f6yq9cI"
            )

            r = requests.get(google_url).json()
            elevation = r["results"][0]["elevation"]

            # Si es el primer dato de la base de datos
            try:
                delta_t = (operation.timestamp - last["timestamp"]).total_seconds()
                coords_1 = (last["latitude"], last["longitude"])
                rise = elevation - last["elevation"]

            except Exception as e:
                print(e)
                coords_1 = coords_2
                delta_t = 7
                rise = 0

            run = geopy.distance.distance(coords_1, coords_2).m  # meters

            distance = math.sqrt(run ** 2 + rise ** 2)
            operation.elevation = elevation
            operation.run = distance
            print(operation.vehicle_id)
            vehicle = Vehicle.query.filter_by(placa=operation.vehicle_id).first()
            print(vehicle.marca)
            try:
                vehicle.odometer = float(args["odometer"])
            except KeyError:
                try:
                    vehicle.odometer += run
                except TypeError:
                    vehicle.odometer = run

            try:
                slope = math.atan(rise / run)  # radians
            except ZeroDivisionError:
                slope = 0
            degree = (slope * 180) / math.pi
            operation.slope = degree

            # JIMENEZ MODEL IMPLEMANTATION
            vehicle.weight = float(args["mass"])
            if "BOTE" in operation.vehicle_id:
                operation.mec_power, operation.net_force = consumption_models.zavitsky(
                    (float(operation.mean_speed) / 3.6),
                    float(operation.mean_acc),
                    float(vehicle.weight),
                )
            else:
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

                operation.en_pot = rise * 9.81 * vehicle.weight

                # WANG MODEL IMPLEMANTATION

                current = float(args["current"])
                ah = current * delta_t / 3600
                c_rate = current / 100  # 100 = Amperios hora totales bateria
                if c_rate > 0:
                    b = 448.96 * c_rate ** 2 - 6301.1 * c_rate + 33840
                    operation.q_loss = (
                        b
                        * math.exp(
                            (-31700 + (c_rate * 370.3))
                            / (8.314472 * (float(args["batt_temp"])))
                        )
                        * ah ** 0.552
                    )
                else:
                    operation.q_loss = 0

            db.session.add(operation)
            db.session.commit()
            return "Data received"
        else:
            return "Null location"


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    login page
    :return:
    """
    if current_user.is_authenticated:
        session["graph_var_x"] = "timestamp"
        session["graph_var_y"] = "soc"
        return redirect(url_for("show_entries"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("show_entries")
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
        return redirect(url_for("show_entries"))
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
    session["form_d1"] = request.form["d1"]
    session["form_h1"] = request.form["h1"]
    session["form_h2"] = request.form["h2"]

    session["d1"] = (datetime.strptime(request.form["d1"], "%d/%m/%Y")).strftime(
        "%Y-%m-%d"
    )
    session["h1"] = (datetime.strptime(request.form["h1"], "%I:%M %p")).strftime(
        "%H:%M:%S"
    )
    session["h2"] = (datetime.strptime(request.form["h2"], "%I:%M %p")).strftime(
        "%H:%M:%S"
    )
    if session["h2"] < session["h1"]:
        session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times

    return redirect(url_for("show_vehicle_map"))


@app.route("/zones_interval", methods=["POST"])
def zones_interval():
    """
    redirects when zones map form is submitted
    :return:
    """
    session["form_d1"] = request.form["d1"]
    session["form_h1"] = request.form["h1"]
    session["form_h2"] = request.form["h2"]

    session["d1"] = (datetime.strptime(request.form["d1"], "%d/%m/%Y")).strftime(
        "%Y-%m-%d"
    )
    session["h1"] = (datetime.strptime(request.form["h1"], "%I:%M %p")).strftime(
        "%H:%M:%S"
    )
    session["h2"] = (datetime.strptime(request.form["h2"], "%I:%M %p")).strftime(
        "%H:%M:%S"
    )
    if session["h2"] < session["h1"]:
        session["h1"], session["h2"] = session["h2"], session["h1"]  # Swap times
    return redirect(url_for("show_zones_map"))


@app.route("/favicon.ico")
def favicon():
    """
    favicon
    """
    return send_from_directory(os.path.join(app.root_path, "static"), "monitor.ico")
