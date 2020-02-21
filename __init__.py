# Santiago Echavarría Correa
# 201220005014

import os
import plot
import map
import pydeck as pdk
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash # g stands for global

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
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row  # para tratar cada entrada de db como un diccionario
    return rv


@app.route('/map_var', methods=['POST'])
def map_var():
    session["graph_var"] = (request.form['variable'])
    session["graph_car"] = (request.form['Vehiculo'])
    return redirect(url_for('show_entries'))
    # return render_template('show_entries.html')


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


@app.route('/')
def show_entries():
    try:
        session["graph_var"]
    except KeyError:
        session["graph_var"] = "seleccione variable"
        session["graph_car"] = "seleccione vehiculo"

    db = get_db()
    r = pdk.Deck(layers=[map.layer], initial_view_state=map.view_state)
    cur = db.execute('select id, latitude,longitude, altitude from entries order by id asc limit 10')
    entries = [] # cur.fetchall()
    bar = plot.create_plot()
    return render_template('show_entries.html',plot = bar,car = session["graph_car"],var_map = session["graph_var"])
    # return render_template('show_entries.html', entries=entries)


@app.route('/addjson', methods=['POST'])
def add_entry():

    db = get_db()
    content = request.get_json()  # Guarde el json que recibe de esp8266
    print(content)
    db.execute('insert into entries (id , medida , color) values (?, ? ,?)', [content["id"], medida, color, ])
    db.commit()
    flash('New data arrived')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('Log in satisfactorio')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


# Run a test server.

app.run(host='0.0.0.0', debug=True, port=8080)
# from extern devices use computer ip adress http://192.168.1.53:8080/
# para que sea visible tiene que estar todos los dispositivos conectados a la misma red
