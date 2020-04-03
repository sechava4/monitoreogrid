from flask import Flask, session
from app.config import devConfig, ProdConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(devConfig)
#app.config.from_object(ProdConfig)
print(devConfig.SQLALCHEMY_DATABASE_URI)
db = SQLAlchemy(app)
print(db)
Bootstrap(app)

if db.engine.url.drivername == 'sqlite':
    migrate = Migrate(app, db)
else:
    migrate = Migrate(app, db, render_as_batch=True)

login = LoginManager(app)
login.login_view = 'login'

from app import routes,models
