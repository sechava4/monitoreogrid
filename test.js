const CAR_MODEL = "nissan:leaf";
const placa = "ASD089";
const URL = "http://104.248.48.68:8080/addjson";
var objTLM;
var objTimer;



// Make json telemetry object
function GetTelemetryObj() {
    var myJSON = {
    "latitude": 0,
    "longitude": 0,
    "elevation": 0,
    "soc": 0,
    "soh": 0,
    "speed": 0,
    "odometer": 0,
    "car_model": CAR_MODEL,
    "batt_temp": 0,
    "ext_temp": 0,
    "voltage": 0,
    "current": 0,
    "power_kw": 0,
    "acceleration": 0,
    "throttle": 0,
    "regen_brake": 0,
    "consumption" :0,
    "range_est": 0,
    "range_ideal": 0,
    "drivetime": 0,
    "footbrake": 0,
    "capacity": 0,
    "engine_temp": 0,
    "is_charging": 0,
    "range_full":0,
    "coulomb":0,
    "rpm":0,
    "energy":0

    };
    return myJSON;


}

// Fill json telemetry object
function UpdateTelemetryObj(myJSON) {
    var read_bool = false;


    myJSON.latitude = OvmsMetrics.AsFloat(["v.p.latitude"]).toFixed(8);
    myJSON.longitude = OvmsMetrics.AsFloat(["v.p.longitude"]).toFixed(8);
    myJSON.elevation= OvmsMetrics.AsFloat(["v.p.altitude"]).toFixed();
    myJSON.soc = OvmsMetrics.AsFloat("v.b.soc");
    myJSON.soh = OvmsMetrics.AsFloat("v.b.soh");
    myJSON.speed = OvmsMetrics.AsFloat("v.p.gpsspeed");
    myJSON.odometer = OvmsMetrics.AsFloat("v.p.odometer");
    myJSON.batt_temp = OvmsMetrics.AsFloat("v.b.temp");
    myJSON.ext_temp = OvmsMetrics.AsFloat("v.e.temp");
    myJSON.voltage = OvmsMetrics.AsFloat("v.b.voltage");
    myJSON.current = OvmsMetrics.AsFloat("v.b.current");
    myJSON.power_kw = OvmsMetrics.AsFloat(["v.b.power"]).toFixed(1);
    myJSON.acceleration = OvmsMetrics.AsFloat("v.p.acceleration");
    myJSON.throttle = OvmsMetrics.AsFloat("v.e.throttle");
    myJSON.regen_brake = OvmsMetrics.AsFloat("v.e.regenbrake");
    myJSON.consumption = OvmsMetrics.AsFloat("v.b.consumption");
    myJSON.range_est = OvmsMetrics.AsFloat("v.b.range.est");
    myJSON.range_ideal = OvmsMetrics.AsFloat("v.b.range.ideal");
    myJSON.drivetime = OvmsMetrics.AsFloat("v.e.drivetime");
    myJSON.footbrake = OvmsMetrics.AsFloat("v.e.footbrake");
    myJSON.capacity = OvmsMetrics.AsFloat("v.b.cac");
    myJSON.engine_temp = OvmsMetrics.AsFloat("v.m.temp");
    myJSON.rpm= OvmsMetrics.AsFloat("v.m.rpm");
    myJSON.enery= OvmsMetrics.AsFloat("v.b.energy.used");
    myJSON.coulomb= OvmsMetrics.AsFloat("v.b.coulomb.used");
    myJSON.range_full = OvmsMetrics.AsFloat("v.b.range.full");



    read_bool = Boolean(OvmsMetrics.Value("v.c.charging"));
    if (read_bool == true) {
    myJSON.is_charging = 1;
    }
    else {
    myJSON.is_charging = 0;
    }

    return true;
}

// Show available vehicle data
function DisplayLiveData(myJSON,CR) {
    var newcontent = "";
    newcontent += "latitude=" + myJSON.latitude + CR;    //GPS latitude
    newcontent += "longitude=" + myJSON.longitude + CR;    //GPS longitude
    newcontent += "elevation=" + myJSON.elevation+ CR;    //GPS altitude
    newcontent += "soc=" + myJSON.soc + CR;    //State of charge
    newcontent += "soh=" + myJSON.soh + CR;    //State of health
    newcontent += "speed=" + myJSON.speed + CR;    //State of health
    newcontent += "odometer=" + myJSON.odometer + CR;    //State of health
    newcontent += "batt_temp=" + myJSON.batt_temp + CR;    //Main battery momentary temperature
    newcontent += "ext_temp=" + myJSON.ext_temp + CR;    //Ambient temperature
    newcontent += "voltage=" + myJSON.voltage + CR;    //Main battery momentary voltage
    newcontent += "current=" + myJSON.current + CR;    //Main battery momentary current
    newcontent += "acceleration=" + myJSON.acceleration + CR;    //Engine momentary acceleration
    newcontent += "throttle=" + myJSON.throttle + CR;    //Engine momentary THROTTLE
    newcontent += "regen_brake=" + myJSON.regen_brake + CR;    //Engine momentary Regen value
    newcontent += "consumption=" + myJSON.consumption + CR;
    newcontent += "range_est=" + myJSON.range_est + CR;
    newcontent += "range_ideal=" + myJSON.range_ideal + CR;
    newcontent += "range_full=" + myJSON.range_ideal + CR;
    newcontent += "drivetime=" + myJSON.drivetime + CR;
    newcontent += "footbrake=" + myJSON.footbrake + CR;
    newcontent += "capacity=" + myJSON.capacity + CR;
    newcontent += "engine_temp=" + myJSON.engine_temp + CR;
    newcontent += "power_kw=" + myJSON.power_kw + CR;    //Main battery momentary power
    newcontent += "is_charging=" + myJSON.is_charging + CR;         //yes = currently charging
    newcontent += "coulomb=" + myJSON.coulomb + CR;
    newcontent += "energy=" + myJSON.energy + CR;
    newcontent += "rpm=" + myJSON.rpm;         //yes = currently charging

    print(newcontent);
}



function InitObjTelemetry() {
    objTLM = GetTelemetryObj();
}

function UpdateObjTelemetry() {
    UpdateTelemetryObj(objTLM);
    DisplayLiveData(objTLM, "\n");
}

// http request callback if successful
function OnRequestDone(resp) {
    print("response="+JSON.stringify(resp)+'\n');
}

// http request callback if failed
function OnRequestFail(error) {
    print("error="+JSON.stringify(error)+'\n');
}

// Return full url with JSON telemetry object
function GetUrlABRP(myJSON,CR) {
    var urljson = URL;
    urljson += "?";
    urljson += "latitude=" + myJSON.latitude + CR;    //GPS latitude
    urljson += "longitude=" + myJSON.longitude + CR;    //GPS longitude
    urljson += "elevation=" + myJSON.elevation+ CR;    //GPS altitude

    urljson += "soc=" + myJSON.soc + CR;    //State of charge
    urljson += "soh=" + myJSON.soh + CR;    //State of health
    urljson += "speed=" + myJSON.speed + CR;    //State of health
    urljson += "odometer=" + myJSON.odometer + CR;    //State of health
    urljson += "batt_temp=" + myJSON.batt_temp + CR;    //Main battery momentary temperature
    urljson += "ext_temp=" + myJSON.ext_temp + CR;    //Ambient temperature
    urljson += "voltage=" + myJSON.voltage + CR;    //Main battery momentary voltage
    urljson += "current=" + myJSON.current + CR;    //Main battery momentary current
    urljson += "acceleration=" + myJSON.acceleration + CR;    //Engine momentary acceleration
    urljson += "throttle=" + myJSON.throttle + CR;    //Engine momentary THROTTLE
    urljson += "regen_brake=" + myJSON.regen_brake + CR;    //Engine momentary Regen value
    urljson += "consumption=" + myJSON.consumption + CR;
    urljson += "range_est=" + myJSON.range_est + CR;
    urljson += "vehicle_id=" + "RZ_123" + CR;
    urljson += "user_id=" + "Juan" + CR;
    urljson += "range_ideal=" + myJSON.range_ideal + CR;
    urljson += "range_full=" + myJSON.range_ideal + CR;
    urljson += "drivetime=" + myJSON.drivetime + CR;
    urljson += "footbrake=" + myJSON.footbrake + CR;
    urljson += "capacity=" + myJSON.capacity + CR;
    urljson += "engine_temp=" + myJSON.engine_temp + CR;
    urljson += "power_kw=" + myJSON.power_kw + CR;    //Main battery momentary power
    urljson += "is_charging=" + myJSON.is_charging + CR;         //yes = currently charging
    urljson += "coulomb=" + myJSON.coulomb + CR;
    urljson += "energy=" + myJSON.energy + CR;
    urljson += "rpm=" + myJSON.rpm;
    print(urljson);
    return urljson;
}

// Return config object for HTTP request
function GetURLcfg() {
    var cfg = {
    url: GetUrlABRP(objTLM, "&"),
    done: function(resp) {OnRequestDone(resp)},
    fail: function(err)  {OnRequestFail(err)}
    };
    return cfg;
}

function SendLiveData() {
    UpdateObjTelemetry();
    HTTP.Request(GetURLcfg());
}

//test purpose : one time execution
function onetime() {
    InitObjTelemetry();
    SendLiveData();
}

// API method abrp.onetime():
exports.onetime = function() {
    onetime();
}

// API method abrp.info():
exports.info = function() {
    InitObjTelemetry();
    UpdateObjTelemetry();
}

// API method abrp.send():
exports.send = function(onoff) {
    if (onoff) {
        onetime();
        //Periodically perform subscribed function
        objTimer = PubSub.subscribe("ticker.10", SendLiveData); // update each 60s
    }
    else {
        PubSub.unsubscribe(objTimer);
    }
}