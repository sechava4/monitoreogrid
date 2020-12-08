const CAR_MODEL = "nissan:leaf";
//const vehicle_id = "FSV110";
const vehicle_id = "GHW284";
//const vehicle_id = "AVM05C";
//const vehicle_id = "OIO53";
const URL = "http://157.230.209.3/addjson";
var URL_esp32 = "http://192.168.4.2/data";
var espurl = 2;
var objTLM;
var objTimer;
var operative_state = 1;
var p = new Date();
var prev = p.getTime();
var first = true;
var time_to_os4 = new Date();
var time_to_os4_millis = time_to_os4.getTime();
var esp_flag = 0

//Varibales de cálculo
var speed = 0;
var old_speed = 0;
var lat = 0;
var lon = 0;
var sum_acc = 0;
var sum_speed = 0.0;
var sum_current = 0.0;
var i = 1.0;
var arr_from_json

objTimer = PubSub.subscribe("ticker.1", SendLiveData); // update each second

// http request callback if successful
function OnRequestDone(resp) {
    print("response="+JSON.stringify(resp)+'\n');
}

function OnRequestDoneJson(resp) {
    print("response="+JSON.stringify(resp)+'\n');
    var data = resp.body;
    arr_from_json = JSON.parse(data);
    esp_flag=0
    HTTP.Request(GetURLcfg());

}

// http request callback if failed
function OnRequestFail(error) {
    print("error="+JSON.stringify(error)+'\n');
}

function OnRequestFailJson(error) {
    print("error="+JSON.stringify(error)+'\n');
    print(JSON.stringify(error));

    if (JSON.stringify(error) == "timeout") {
        print('trying next url');
        espurl =espurl + 1;
    }

    espurl =espurl + 1;
    if (espurl>7) {
        espurl = 2
    }
    esp_flag = 1
    HTTP.Request(GetURLcfg());
}

//v.tp.fl.p                                231.952kPa
//v.tp.fr.p                                230.58kPa
//v.tp.rl.p                                240.188kPa
//v.tp.rr.p                                223.717kPa

function GetUrlABRP() {
    var urljson = URL;
    urljson += "?";
    urljson += "latitude=" + OvmsMetrics.AsFloat(["v.p.latitude"]).toFixed(8) + "&";    //GPS latitude
    urljson += "longitude=" + OvmsMetrics.AsFloat(["v.p.longitude"]).toFixed(8) + "&";    //GPS longitude
    urljson += "mean_speed=" + (sum_speed *1.0 /i).toFixed(2) + "&";
    urljson += "speed=" + OvmsMetrics.AsFloat(["v.p.speed"])+ "&";
    urljson += "mean_acc=" + (sum_acc *1.0 /i).toFixed(2) + "&";       //potencia promedio
    urljson += "user_id=" + "Juan" + "&";
    urljson += "mass=" + 170  + "&";
    urljson += "freeram=" + OvmsMetrics.Value("m.freeram") + "&";
    urljson += "odometer=" + OvmsMetrics.AsFloat("v.p.odometer") + "&";
    // urljson += "monotonic=" + OvmsMetrics.Value("m.monotonic") + "&";
    urljson += "net_signal=" + OvmsMetrics.Value("m.net.sq") + "&";
    urljson += "soc=" + OvmsMetrics.AsFloat("v.b.soc") + "&";    //State of charge
    urljson += "soh=" + OvmsMetrics.AsFloat("v.b.soh") + "&";    //State of health
    urljson += "voltage=" + OvmsMetrics.AsFloat("v.b.voltage").toFixed(2) + "&";    //Main battery momentary voltage

    urljson += "current=" + (sum_current *-1.0 /i).toFixed(2) + "&";

    urljson += "capacity=" + OvmsMetrics.AsFloat("xrz.v.avail.energy") + "&";
    urljson += "batt_temp=" + OvmsMetrics.AsFloat("v.b.temp") + "&";    //Main battery momentary temperature
    //urljson += "ext_temp=" + OvmsMetrics.AsFloat("v.e.temp") + "&";    //Ambient temperature

    urljson += "power_kw=" + ( OvmsMetrics.AsFloat("v.b.voltage") * OvmsMetrics.AsFloat("v.b.current") / (-1000.0) ).toFixed(3)  + "&";    //Main battery momentary power

    urljson += "operative_state=" + operative_state + "&";    //OS
    urljson += "vehicle_id=" + vehicle_id + "&";
    urljson += "acceleration=" + OvmsMetrics.AsFloat("v.p.acceleration") + "&";    //Engine momentary acceleration
    urljson += "throttle=" + OvmsMetrics.AsFloat("v.e.throttle") + "&";    //Engine momentary THROTTLE
    urljson += "regen_brake=" + OvmsMetrics.AsFloat("v.e.regenbrake") + "&";    //Engine momentary Regen value
    //urljson += "consumption=" + OvmsMetrics.AsFloat("v.b.consumption") + "&";



    urljson += "range_est=" + OvmsMetrics.AsFloat("v.b.range.est") + "&";
    urljson += "range_ideal=" + OvmsMetrics.AsFloat("v.b.range.ideal") + "&";
    urljson += "range_full=" + OvmsMetrics.AsFloat("v.b.range.full") + "&";
    urljson += "drivetime=" + OvmsMetrics.AsFloat("v.e.drivetime") + "&";
    urljson += "drivemode=" + OvmsMetrics.Value("v.e.drivemode") + "&";
    urljson += "charger_type=" + OvmsMetrics.Value("v.c.type") + "&";
    urljson += "charge_current=" + OvmsMetrics.AsFloat("v.b.12v.current") + "&";
    urljson += "charge_time=" + OvmsMetrics.AsFloat("v.c.time") + "&";
    urljson += "energy_rec=" + OvmsMetrics.AsFloat("v.c.kwh") + "&";

    urljson += "footbrake=" + OvmsMetrics.AsFloat("v.e.footbrake") + "&";
    urljson += "engine_temp=" + OvmsMetrics.AsFloat("v.m.temp") + "&";
    urljson += "coulomb=" + OvmsMetrics.AsFloat("v.b.coulomb.used") + "&";
    urljson += "energy=" + OvmsMetrics.AsFloat("v.b.energy.used") + "&";
    urljson += "rpm=" + OvmsMetrics.AsFloat("v.m.rpm") + "&";

    urljson += "tpms=" + OvmsMetrics.AsFloat("v.tp.fl.p") + "&";
    urljson += "charge_time=" + OvmsMetrics.AsFloat("v.c.time") + "&";
    urljson += "charger_type=" + OvmsMetrics.AsFloat("v.c.type") + "&";

    if (esp_flag==0) {

        urljson += "angle_x=" + arr_from_json["angle_x"] + "&";
        urljson += "angle_y=" + arr_from_json["angle_y"] + "&";
        //urljson += "ext_temp=" + arr_from_json["temp"] + "&";
        urljson += "elevation2=" + arr_from_json["elevation2"] + "&";
        urljson += "AcX=" + arr_from_json["AcX"] + "&";
        urljson += "AcY=" + arr_from_json["AcY"] + "&";
        urljson += "AcZ=" + arr_from_json["AcZ"] + "&";

    }
    print(urljson);
    i = 1.0;
    sum_acc = 0.0;
    sum_speed = 0.0;
    sum_current = 0.0;
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

function GetURL_auxdata() {
    switch (espurl) {
        case 2:
            URL_esp32 = "http://192.168.4.2/data";
        break;
        case 3:
            URL_esp32 = "http://192.168.4.3/data";
        break;
        case 4:
            URL_esp32 = "http://192.168.4.4/data";
        break;
        case 5:
            URL_esp32 = "http://192.168.4.5/data";
        break;
    }
    var cfg = {
    url: URL_esp32,
    timeout: 5000,
    done: function(resp) {OnRequestDoneJson(resp)},
    fail: function(err)  {OnRequestFailJson(err)}
    };
    return cfg;
}

function Make_Request(){
    p = new Date();
    prev = p.getTime();
    HTTP.Request(GetURL_auxdata());
    //HTTP.Request(GetURLcfg());
}

function SendLiveData() {
    var d = new Date();
    var cms = d.getTime();   //current_millis

    speed = OvmsMetrics.AsFloat(["v.p.speed"]);
    //speed = OvmsMetrics.AsFloat(["v.p.gpsspeed"]);
    sum_speed = sum_speed + speed;

    current = OvmsMetrics.AsFloat(["v.b.current"]);
    sum_current = sum_current + current;

    var acc = (speed - old_speed) / 3.6;
    sum_acc = sum_acc + acc;

    print(["current = ",current]);
    print(["state = ",operative_state]);
    print(["i = ",i]);
    print(["speed = ",speed]);


    switch (operative_state) {

      case 1:
        // Andando sin regenerar

        if (i > 8) {
            Make_Request();
        }
        /*
        if ((OvmsMetrics.AsFloat("v.p.speed") <= 1) && (first == true) ) { //&& ((cms - time_to_os4_millis) > 90000) ){  // && (Boolean(OvmsMetrics.Value("v.e.on")) == true) ){
            // Ir al estado "detenido en ruta"
            //operative_state = 4;
            time_to_os4 = new Date();
            time_to_os4_millis = time_to_os4.getTime();
            first = false;
            print("fisrt");
            Make_Request();
        }

        else if (OvmsMetrics.AsFloat("v.p.speed") > 1)  {
            first = true;
            Make_Request();
        }
        */
        // si han pasado mas de 90 segundos de estar quieto
        if ((speed <= 1) && (Boolean(OvmsMetrics.Value("v.e.on")) == false) ) { //&& ((cms - time_to_os4_millis) > 90000) ) {
            operative_state = 4;
            Make_Request();
        }

        else if ( (speed >= 1) && (OvmsMetrics.AsFloat("v.b.current") > 0 ) ){
            operative_state = 2;
            Make_Request();
        }
        break;


      case 2:
        // Andando con freno regenerativo
        if (i > 6) {
            Make_Request();
        }
        if ( (speed >= 1) && (OvmsMetrics.AsFloat("v.b.current") < 0 ) ) {
            first = true;
            operative_state = 1;
            Make_Request();
        }
        else if (speed <= 1) {
            operative_state = 4;
            Make_Request();
        }
        break;


      case 3:
        // Detenido cargando
        if (i > 60) {
            Make_Request();
        }
        if (Boolean(OvmsMetrics.Value("v.c.charging")) == false) {
            operative_state = 4;

            Make_Request();
        }
        break;


      case 4:
        // Detenido no en ruta
        if (i > 60) {
            Make_Request();
        }
        if (speed > 1){
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
    old_speed = speed;
    i = i + 1;
}
