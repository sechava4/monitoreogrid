
create table entries (
id integer primary key autoincrement,
tiempo text,
latitude float(10),
longitude float(10),
altitude float(10),
soc float,
soh SMALLINT,
speed smallint,
car_model text,
batt_temp float,
ext_temp float,
voltage float,
batt_current float,
powerKw float,
engine_acceleration float,
throttle SMALLINT,
regenbrake SMALLINT,
consumption float,
range_est SMALLINT,
range_ideal SMALLINT,
drivetime int,
footbrake smallint,
engine_temp smallint,
is_charging bool);


