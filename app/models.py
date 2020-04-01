from app import db, login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    genre = (db.String(64))
    driven_kms = db.Column(db.Integer)
    co2_saved = db.Column(db.Integer)
    roi = db.Column(db.Integer)    # Return on investment
    age = db.Column(db.Integer)
    driving_cluster = db.Column(db.Integer)
    charging_cluster = db.Column(db.Integer)
    geo_cluster = db.Column(db.Integer)

    # For debuging purposes, we type the instance name and it prints self,username
    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(64), index=True, unique=True)
    marca = db.Column(db.String(64))
    modelo = db.Column(db.String(64))
    year = db.Column(db.Integer)
    capacity_nominal = db.Column(db.Float)
    soh = db.Column(db.Float)
    rul = db.Column(db.Integer)

    # For debuging purposes, we type the instance name and it prints self,username
    def __repr__(self):
        return '<Placa {}>'.format(self.placa)


class Station(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elevation = db.Column(db.Float)
    charger_types = db.Column(db.String(64))
    number_of_chargers = db.Column(db.Integer)

    # For debuging purposes, we type the instance name and it prints self,username
    def __repr__(self):
        return '<Placa {}>'.format(self.placa)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Operation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    elevation = db.Column(db.Float)
    slope = db.Column(db.String)
    speed = db.Column(db.Integer)
    odometer = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    batt_temp = db.Column(db.Float)
    ext_temp = db.Column(db.Float)
    power_kw = db.Column(db.Float)
    acceleration = db.Column(db.Float)
    capacity = db.Column(db.Float)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    soc = db.Column(db.Float)
    soh = db.Column(db.Float)
    voltage = db.Column(db.Float)
    current = db.Column(db.Float)
    throttle = db.Column(db.Integer)
    regen_brake = db.Column(db.Float)
    consumption = db.Column(db.Float)
    range_est = db.Column(db.Integer)
    range_ideal = db.Column(db.Integer)
    drivetime = db.Column(db.Integer)
    charge_time = db.Column(db.Integer)
    footbrake = db.Column(db.Integer)
    engine_temp = db.Column(db.Float)
    is_charging = db.Column(db.Integer)
    tpms = db.Column(db.Float)
    ocv = db.Column(db.Float)
    occupants = db.Column(db.Integer)
    station_id = db.Column(db.Integer, db.ForeignKey('station.id'))
    sensor_data = db.Column(db.String)

    def __repr__(self):
        return '<User = {} Placa = {} Timestamp = {}>'.format(self.placa, self.username, self.timestamp)