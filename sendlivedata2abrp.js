 
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



/*
 * Declarations:
 *   CAR_MODEL: find your car model here: https://api.iternio.com/1/tlm/get_carmodels_list?api_key=32b2162f-9599-4647-8139-66e9f9528370
 *   OVMS_API_KEY : API_KEY to access to ABRP API, given by the developer
 *   MY_TOKEN : Your token (corresponding to your abrp profile)
 *   URL : url to send telemetry to abrp following: https://iternio.com/index.php/iternio-telemetry-api/
 */
 
  const CAR_MODEL = "nissan:leaf";
  const placa = "ASD089";
  const URL = "http://10.161.62.129:8080/addjson";
  const CR = '\n';
  var objTLM;
  var objTimer;


  // Make json telemetry object
  function GetTelemetryObj() {
    var myJSON = { 
      "tiempo": 0,
      "latitude": 0,
      "longitude": 0,
      "altitude": 0,
      "soc": 0,
      "soh": 0,
      "speed": 0,
      "odometer": 0,
      "car_model": CAR_MODEL,
      "batt_temp": 0,
      "ext_temp": 0, 
      "voltage": 0,
      "batt_current": 0,
      "powerKw": 0,
      "engine_acceleration": 0,
      "throttle": 0,
      "regenbrake": 0,
      "consumption" :0,
      "range_est": 0,
      "range_ideal": 0,
      "drivetime": 0,
      "footbrake": 0,
      "Qn_Ah": 0,
      "engine_temp": 0,
      "is_charging": 0
    };
    return myJSON;


  }

  // Fill json telemetry object
  function UpdateTelemetryObj(myJSON) {
    var read_bool = false;

    myJSON.latitude = OvmsMetrics.AsFloat(["v.p.latitude"]).toFixed(8);
    myJSON.longitude = OvmsMetrics.AsFloat(["v.p.longitude"]).toFixed(8);
    myJSON.altitude = OvmsMetrics.AsFloat(["v.p.altitude"]).toFixed();
    myJSON.soc = OvmsMetrics.AsFloat("v.b.soc");
    myJSON.soh = OvmsMetrics.AsFloat("v.b.soh");
    myJSON.speed = OvmsMetrics.AsFloat("v.p.speed");
    myJSON.odometer = OvmsMetrics.AsFloat("v.p.odometer");
    myJSON.batt_temp = OvmsMetrics.AsFloat("v.b.temp");
    myJSON.ext_temp = OvmsMetrics.AsFloat("v.e.temp");
    myJSON.voltage = OvmsMetrics.AsFloat("v.b.voltage");
    myJSON.batt_current = OvmsMetrics.AsFloat("v.b.current");
    myJSON.powerKw = OvmsMetrics.AsFloat(["v.b.power"]).toFixed(1);
    myJSON.engine_acceleration = OvmsMetrics.AsFloat("v.p.acceleration");
    myJSON.throttle = OvmsMetrics.AsFloat("v.e.throttle");
    myJSON.regenbrake = OvmsMetrics.AsFloat("v.e.regenbrake");
    myJSON.consumption = OvmsMetrics.AsFloat("v.b.consumption");
    myJSON.range_est = OvmsMetrics.AsFloat("v.b.range.est");
    myJSON.range_ideal = OvmsMetrics.AsFloat("v.b.range.ideal");
    myJSON.drivetime = OvmsMetrics.AsFloat("v.e.drivetime");
    myJSON.footbrake = OvmsMetrics.AsFloat("v.e.footbrake");
    myJSON.Qn_Ah = OvmsMetrics.AsFloat("v.b.cac");
    myJSON.engine_temp = OvmsMetrics.AsFloat("v.m.temp");


    var d = new Date();
    myJSON.tiempo = Math.trunc(d.getTime()/1000);
    //myJSON.utc = OvmsMetrics.Value("m.time.utc");

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
  function DisplayLiveData(myJSON) {
    var newcontent = "";
    newcontent += "tiempo=" + myJSON.tiempo + CR;    //Sample time
    newcontent += "latitude=" + myJSON.latitude + CR;    //GPS latitude
    newcontent += "longitude=" + myJSON.longitude + CR;    //GPS longitude
    newcontent += "altitude =" + myJSON.altitude + CR;    //GPS altitude
    newcontent += "soc=" + myJSON.soc + CR;    //State of charge
    newcontent += "soh=" + myJSON.soh + CR;    //State of health
    newcontent += "speed=" + myJSON.speed + CR;    //State of health
    newcontent += "odometer=" + myJSON.odometer + CR;    //State of health
    newcontent += "bat_temp=" + myJSON.batt_temp + CR;    //Main battery momentary temperature
    newcontent += "ext temp=" + myJSON.ext_temp + CR;    //Ambient temperature
    newcontent += "voltage=" + myJSON.voltage + CR;    //Main battery momentary voltage
    newcontent += "batt_current=" + myJSON.batt_current + CR;    //Main battery momentary current
    newcontent += "engine_acceleration=" + myJSON.engine_acceleration + CR;    //Engine momentary acceleration
    newcontent += "throttle=" + myJSON.throttle + CR;    //Engine momentary THROTTLE
    newcontent += "regenbrake=" + myJSON.regenbrake + CR;    //Engine momentary Regen value
    newcontent += "consumption=" + myJSON.consumption + CR;    //Engine momentary acceleration
    newcontent += "range_est=" + myJSON.range_est + CR;
    newcontent += "range_ideal=" + myJSON.range_ideal + CR;
    newcontent += "drivetime=" + myJSON.drivetime + CR;
    newcontent += "footbrake=" + myJSON.footbrake + CR;
    newcontent += "Qn_Ah=" + myJSON.Qn_Ah + CR;
    newcontent += "engine_temp=" + myJSON.engine_temp + CR;
    newcontent += "powerKw=" + myJSON.powerKw + CR;    //Main battery momentary power
    newcontent += "is_charging=" + myJSON.is_charging + CR;         //yes = currently charging
    print(newcontent);
  }



  function InitObjTelemetry() {
    objTLM = GetTelemetryObj();
  }
  
  function UpdateObjTelemetry() {
    UpdateTelemetryObj(objTLM);
    DisplayLiveData(objTLM);
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
  function GetUrlABRP() {
    var urljson = URL;
    urljson += "?";
    //urljson += "api_key=" + OVMS_API_KEY;
    //urljson += "&";
    //urljson += "token=" + MY_TOKEN;
    //urljson += "&";
    urljson += encodeURIComponent(JSON.stringify(objTLM));
    print(urljson + CR);
    return urljson;
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

  function SendLiveData() {
    UpdateObjTelemetry();
    HTTP.Request( GetURLcfg() );
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
      objTimer = PubSub.subscribe("ticker.60", SendLiveData); // update each 60s
    } else {
      PubSub.unsubscribe(objTimer);
    }
  }
