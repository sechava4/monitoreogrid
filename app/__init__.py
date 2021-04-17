from flask import Flask
from app.config import DevConfig, Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from redis import Redis
import rq

app = Flask(__name__)
app.config.from_object(DevConfig)
# app.config.from_object(Config)

app.redis = Redis.from_url(app.config["REDIS_URL"])
app.task_queue = rq.Queue("app-tasks", connection=app.redis)
db = SQLAlchemy(app)
Bootstrap(app)

migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "login"

from app import routes, models
