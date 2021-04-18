from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import DevConfig, Config

app = Flask(__name__)
app.config.from_object(DevConfig)
# app.config.from_object(Config)

db = SQLAlchemy(app)
Bootstrap(app)

migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "login"

from app import routes, models
