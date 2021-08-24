from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from app.config import DevConfig, Config


db = SQLAlchemy()
bootstrap = Bootstrap()
migrate = Migrate()
login = LoginManager()
login.login_view = "login"


def create_app(config_class):
    application = Flask(__name__)
    application.config.from_object(config_class)
    db.init_app(application)
    login.init_app(application)
    migrate.init_app(application, db)
    bootstrap.init_app(application)

    from app.api import bp as api_bp
    application.register_blueprint(api_bp)

    return application


app = create_app(Config)
from app import routes, models
