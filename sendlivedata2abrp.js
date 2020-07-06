/**
 *       /store/scripts/sendlivedata2abrp.js
 *
 * Module plugin:
 *  Send live data to a better route planner
 *  This version uses the embedded GSM of OVMS, so there's an impact on data consumption
 *  /!\ requires OVMS firmware version 3.2.008-147 minimum (for HTTP call)
 *
 * Version 1.0   2019   dar63 (forum https://www.openvehicles.com)
 *
 * Enable:
 *  - install at above path
 *  - add to /store/scripts/ovmsmain.js:
 *                 abrp = require("sendlivedata2abrp");
 *  - script reload
 *
 * Usage:
 *  - script eval abrp.info()         => to display vehicle data to be sent to abrp
 *  - script eval abrp.onetime()      => to launch one time the request to abrp server
 *  - script eval abrp.send(1)        => toggle send data to abrp
 *  -                      (0)        => stop sending data
 *
 **/

const CAR_MODEL = "nissan:leaf";
const placa = "ASD089";
const URL = "http://104.248.48.68:8080/addjson";
var objTLM;
var objTimer;
var operative_state = 1;
var p = new Date();
var prev = p.getTime();
var first = true;
var time_to_os4 = new Date();
var time_to_os4_millis = time_to_os4.getTime();

//Varibales de cálculo
var speed = 0;
var old_speed = 0;
var altitude = 0;
var old_altitude = 0;
var run = 0;
var rise = 0;
var slope = 0;
var lat = 0;
var lon = 0;
var old_lon = 0;
var old_lat = 0;
var mec_power = 0;
var sum_power = 0;
var sum_slope = 0;
var sum_run = 0;
var max_power = 0;
var sum_acc = 0;
var i = 1;


// http request callback if successful
function OnRequestDone(resp) {
    print("response="+JSON.stringify(resp)+'\n');
}


// http request callback if failed
function OnRequestFail(error) {
    print("error="+JSON.stringify(error)+'\n');
}




function degreesToRadians(degrees) {
  return degrees * Math.PI / 180;
}

function distanceInKmBetweenEarthCoordinates(lat1, lon1, lat2, lon2) {
  var earthRadiusKm = 6371;

  var dLat = degreesToRadians(lat2-lat1);
  var dLon = degreesToRadians(lon2-lon1);

  lat1 = degreesToRadians(lat1);
  lat2 = degreesToRadians(lat2);

  var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
          Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(lat1) * Math.cos(lat2);
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return earthRadiusKm * c * 1000;   //in meters
}




function GetUrlABRP() {
    var urljson = URL;


    urljson += "?";
    urljson += "latitude=" + lat + "&";    //GPS latitude
    urljson += "longitude=" + lon + "&";    //GPS longitude
    urljson += "elevation=" + altitude + "&";    //GPS altitude
    urljson += "speed=" + speed + "&";
    urljson += "mec_power=" + (sum_power/i) + "&";       //potencia promedio
    urljson += "mec_power_delta_e=" + max_power + "&";   //potenica máxima
    urljson += "mean_acc=" + (sum_acc/i) + "&";       //potencia promedio
    urljson += "slope=" + (sum_slope/i) + "&";       //pendiente promedio
    urljson += "run=" + sum_run + "&";       //pendiente promedio

    urljson += "odometer=" + OvmsMetrics.AsFloat("v.p.odometer") + "&";
    urljson += "vehicle_id=" + "RZ_123" + "&";
    urljson += "user_id=" + "Juan" + "&";
    urljson += "mass=" + 210 + "&";
    urljson += "soc=" + OvmsMetrics.AsFloat("v.b.soc") + "&";    //State of charge
    urljson += "soh=" + OvmsMetrics.AsFloat("v.b.soh") + "&";    //State of health
    urljson += "voltage=" + OvmsMetrics.AsFloat("v.b.voltage") + "&";    //Main battery momentary voltage
    urljson += "current=" + OvmsMetrics.AsFloat("v.b.current") + "&";    //Main battery momentary current
    urljson += "capacity=" + OvmsMetrics.AsFloat("v.b.cac") + "&";
    urljson += "batt_temp=" + OvmsMetrics.AsFloat("v.b.temp") + "&";    //Main battery momentary temperature
    urljson += "ext_temp=" + OvmsMetrics.AsFloat("v.e.temp") + "&";    //Ambient temperature
    urljson += "power_kw=" + OvmsMetrics.AsFloat(["v.b.power"]).toFixed(2) + "&";    //Main battery momentary power
    urljson += "operative_state=" + operative_state + "&";    //OS
    urljson += "acceleration=" + OvmsMetrics.AsFloat("v.p.acceleration") + "&";    //Engine momentary acceleration
    urljson += "throttle=" + OvmsMetrics.AsFloat("v.e.throttle") + "&";    //Engine momentary THROTTLE
    urljson += "regen_brake=" + OvmsMetrics.AsFloat("v.e.regenbrake") + "&";    //Engine momentary Regen value
    urljson += "consumption=" + OvmsMetrics.AsFloat("v.b.consumption") + "&";
    urljson += "range_est=" + OvmsMetrics.AsFloat("v.b.range.est") + "&";
    urljson += "range_ideal=" + OvmsMetrics.AsFloat("v.b.range.ideal") + "&";
    urljson += "range_full=" + OvmsMetrics.AsFloat("v.b.range.full") + "&";
    urljson += "drivetime=" + OvmsMetrics.AsFloat("v.e.drivetime") + "&";
    urljson += "drivemode=" + OvmsMetrics.Value("v.e.drivemode") + "&";
    urljson += "footbrake=" + OvmsMetrics.AsFloat("v.e.footbrake") + "&";
    urljson += "engine_temp=" + OvmsMetrics.AsFloat("v.m.temp") + "&";
    urljson += "coulomb=" + OvmsMetrics.AsFloat("v.b.coulomb.used") + "&";
    urljson += "energy=" + OvmsMetrics.AsFloat("v.b.energy.used") + "&";
    urljson += "rpm=" + OvmsMetrics.AsFloat("v.m.rpm") + "&";

    // Analizar drivetime para el cambio de estados

    urljson += "coulomb_rec=" + OvmsMetrics.AsFloat("v.b.coulomb.recd") + "&";
    urljson += "energy_rec=" + OvmsMetrics.AsFloat("v.b.energy.recd") + "&";
    urljson += "tpms=" + OvmsMetrics.AsFloat("v.tp.fl.p") + "&";
    urljson += "charge_time=" + OvmsMetrics.AsFloat("v.c.time") + "&";
    urljson += "charger_type=" + OvmsMetrics.AsFloat("v.c.type") + "&";
    print(urljson);
    i = 1;
    sum_power = 0;
    max_power = 0;
    sum_acc = 0;
    sum_slope = 0;
    sum_run = 0;
    return urljson;

}

// Return config object for HTTP request
function GetURLcfg() {
    var cfg = {
    url: GetUrlABRP(),
    timeout: 20000,
    done: function(resp) {OnRequestDone(resp)},
    fail: function(err)  {OnRequestFail(err)}
    };
    return cfg;
}

function Make_Request(){
    p = new Date();
    prev = p.getTime();
    HTTP.Request(GetURLcfg());

}

function SendLiveData() {
    var d = new Date();
    var cms = d.getTime();   //current_millis

    lat = OvmsMetrics.AsFloat(["v.p.latitude"]).toFixed(8);
    lon = OvmsMetrics.AsFloat(["v.p.longitude"]).toFixed(8);
    altitude = OvmsMetrics.AsFloat(["v.p.altitude"]).toFixed();
    speed = OvmsMetrics.AsFloat(["v.p.gpsspeed"]).toFixed();

    acc = (speed - old_speed) / 3.6;    // divided by 1 second
    sum_acc = sum_acc + acc;

    if (lat > 0 && lon > 0 && old_lat > 0 && old_lon > 0) {
        run = distanceInKmBetweenEarthCoordinates(lat, lon, old_lat, old_lon);
    }
    else {
        run = 0;
    }
    print("run");
    print(run);

    var run2 = (speed + old_speed) / 7.2;   // meters
    sum_run = sum_run + run2

    rise = altitude - old_altitude;

    if (run > 0){
        slope = Math.atan(rise / run2);
    }
    else {
        slope = 0;
    }
    sum_slope = sum_slope + slope;

    var p = 1.2;    // Air density kg/m3
    var m = 170;    // kg
    var A = 0.790;  // Frontal area m2
    var cr = 0.01;  // Rolling cohef
    var cd = 0.2;   // Drag cohef

    var Fd = (cr * m * 9.81 * Math.cos(slope)) + ( 0.5 * p * A * cd * Math.pow( (speed / 3.6), 2) );
    var Fw = m * 9.81 * Math.sin(slope);
    var F = (m * acc) + Fw + Fd;
    /*
    print("speed= ");
    print(speed);
    print("slope = ");
    print(slope);
    print("Fd= ");
    print(Fd);
    print("acc= ");
    print(acc);
    print("Fw = ");
    print(Fw);
    print("fuerza = ");
    print(F);
    */
    mec_power = F * (speed + old_speed) / (7200);   //kw

    print("potencia = ");
    print(mec_power );
    sum_power = sum_power + mec_power;

    if (mec_power > max_power) {
        max_power = mec_power;
    }



    //print(operative_state);
    switch (operative_state) {

      case 1:
        // Andando sin regenerar
        if ((cms - prev) > 8000) {
            Make_Request();
        }
        /*
        if ((OvmsMetrics.AsFloat("v.p.gpsspeed") <= 1) && (first == true) ) { //&& ((cms - time_to_os4_millis) > 90000) ){  // && (Boolean(OvmsMetrics.Value("v.e.on")) == true) ){
            // Ir al estado "detenido en ruta"
            //operative_state = 4;
            time_to_os4 = new Date();
            time_to_os4_millis = time_to_os4.getTime();
            first = false;
            print("fisrt");
            Make_Request();
        }

        else if (OvmsMetrics.AsFloat("v.p.gpsspeed") > 1)  {
            first = true;
            Make_Request();
        }
        */
        // si han pasado mas de 90 segundos de estar quieto
        if ((OvmsMetrics.AsFloat("v.p.gpsspeed") <= 1) && (Boolean(OvmsMetrics.Value("v.e.on")) == false) ) { //&& ((cms - time_to_os4_millis) > 90000) ) {
            operative_state = 4;
            Make_Request();
        }

        else if (Boolean(OvmsMetrics.Value("v.e.regenbrake")) == true){
            operative_state = 2;
            Make_Request();
        }
        break;


      case 2:
        // Andando con freno regenerativo
        if ((cms - prev) > 2000) {
            Make_Request();
        }
        if ((OvmsMetrics.AsFloat("v.p.gpsspeed") > 0) && (Boolean(OvmsMetrics.Value("v.e.regenbrake")) == true) ) {
            first = true;
            operative_state = 1;
            Make_Request();
        }
        else if (OvmsMetrics.AsFloat("v.p.gpsspeed") <= 1) {
            operative_state = 4;
            Make_Request();
        }
        break;


      case 3:
        // Detenido cargando
        if ((cms - prev) > 10000) {
            Make_Request();
        }
        if (Boolean(OvmsMetrics.Value("v.c.charging")) == false) {
            operative_state = 4;

            Make_Request();
        }
        break;


      case 4:
        // Detenido no en ruta
        if ((cms - prev) > 120000) {
            Make_Request();
        }
        if (OvmsMetrics.AsFloat("v.p.gpsspeed") > 1){
            first = true;
            operative_state = 1;
            Make_Request();
        }
        else if (Boolean(OvmsMetrics.Value("v.c.charging")) == true) {
            operative_state = 3;
            Make_Request();
        }

        break;

    }
    old_lat = lat;
    old_lon = lon;
    old_speed = speed;
    old_altitude = altitude;
    i = i + 1;
}



//test purpose : one time execution
function onetime() {
    Make_Request();
}

// API method abrp.onetime():
exports.onetime = function() {
    onetime();
}


// API method abrp.send():
exports.send = function(onoff) {
    if (onoff) {
        onetime();
        p = new Date();
        prev = p.getTime();
        time_to_os4 = new Date();
        time_to_os4_millis = time_to_os4.getTime();
        first = true;

        //Periodically perform subscribed function
        objTimer = PubSub.subscribe("ticker.1", SendLiveData); // update each second
    }
    else {
        PubSub.unsubscribe(objTimer);
    }
}