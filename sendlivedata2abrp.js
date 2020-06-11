const CAR_MODEL = "nissan:leaf";
const placa = "ASD089";
const URL = "http://104.248.48.68:8080/addjson";
var objTLM;
var objTimer;
var operative_state = 4;
var p = new Date();
var prev = p.getTime();


// http request callback if successful
function OnRequestDone(resp) {
    print("response="+JSON.stringify(resp)+'\n');
}


// http request callback if failed
function OnRequestFail(error) {
    print("error="+JSON.stringify(error)+'\n');
}

function GetUrlABRP() {
    var urljson = URL;
    urljson += "?";
    urljson += "latitude=" + OvmsMetrics.AsFloat(["v.p.latitude"]).toFixed(8) + "&";    //GPS latitude
    urljson += "longitude=" + OvmsMetrics.AsFloat(["v.p.longitude"]).toFixed(8) + "&";    //GPS longitude
    urljson += "elevation=" + OvmsMetrics.AsFloat(["v.p.altitude"]).toFixed() + "&";    //GPS altitude
    urljson += "odometer=" + OvmsMetrics.AsFloat("v.p.odometer") + "&";
    urljson += "vehicle_id=" + "RZ_123" + "&";
    urljson += "user_id=" + "Juan" + "&";
    urljson += "soc=" + OvmsMetrics.AsFloat("v.b.soc") + "&";    //State of charge
    urljson += "soh=" + OvmsMetrics.AsFloat("v.b.soh") + "&";    //State of health
    urljson += "voltage=" + OvmsMetrics.AsFloat("v.b.voltage") + "&";    //Main battery momentary voltage
    urljson += "current=" + OvmsMetrics.AsFloat("v.b.current") + "&";    //Main battery momentary current
    urljson += "capacity=" + OvmsMetrics.AsFloat("v.b.cac") + "&";
    urljson += "batt_temp=" + OvmsMetrics.AsFloat("v.b.temp") + "&";    //Main battery momentary temperature
    urljson += "ext_temp=" + OvmsMetrics.AsFloat("v.e.temp") + "&";    //Ambient temperature
    urljson += "power_kw=" + OvmsMetrics.AsFloat(["v.b.power"]).toFixed(2) + "&";    //Main battery momentary power
    urljson += "operative_state=" + operative_state + "&";    //OS
    urljson += "speed=" + OvmsMetrics.AsFloat("v.p.gpsspeed") + "&";    //State of health
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
    urljson += "tpms=" + OvmsMetrics.AsFloat("v.tp.fl.p");
    urljson += "coulomb_rec=" + OvmsMetrics.AsFloat("v.b.coulomb.recd") + "&";
    urljson += "energy_rec=" + OvmsMetrics.AsFloat("v.b.energy.recd") + "&";
    urljson += "charge_time=" + OvmsMetrics.AsFloat("v.c.time") + "&";
    urljson += "charger_type=" + OvmsMetrics.AsFloat("v.c.type") + "&";

}

// Return config object for HTTP request
function GetURLcfg() {
    var cfg = {
    url: GetUrlABRP(),
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
    var cms = d.getTime();
    print(operative_state);
    switch (operative_state) {

      case 1:
        // Andando sin regenerar
        if ((cms - prev) > 10000) {
            Make_Request();
        }
        if (OvmsMetrics.AsFloat("v.p.gpsspeed") <= 1) {
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
        // Detenido
        if ((cms - prev) > 120000) {
            Make_Request();
        }
        if (OvmsMetrics.AsFloat("v.p.gpsspeed") > 1){
            operative_state = 1;
            Make_Request();
        }
        else if (Boolean(OvmsMetrics.Value("v.c.charging")) == true) {
            operative_state = 3;
            Make_Request();
        }

        break;
    }
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

        //Periodically perform subscribed function
        objTimer = PubSub.subscribe("ticker.1", SendLiveData); // update each second
    }
    else {
        PubSub.unsubscribe(objTimer);
    }
}
