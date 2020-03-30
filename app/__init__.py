from flask import Flask, request, session, g, redirect, url_for, Markup, \
    render_template, flash,send_from_directory # g stands for global
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

if db.engine.url.drivername == 'sqlite':
    migrate = Migrate(app, db)
else:
    migrate = Migrate(app, db, render_as_batch=True)

login = LoginManager(app)
login.login_view = 'login'

from app import routes,models
