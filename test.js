const CAR_MODEL = "@@:@@:@@:@@:@@";
  const OVMS_API_KEY = "32b2162f-9599-4647-8139-66e9f9528370";
  const MY_TOKEN = "@@@@@@@@-@@@@-@@@@-@@@@-@@@@@@@@@@@@";
  const TIMER_INTERVAL = "ticker.60";                         // every minute
  const EVENT_MOTORS_ON = "vehicle.on";
  const URL = "http://www.google.com";
  const CR = '\n';

  var objTLM;
  var objTimer, objEvent;
  var sHasChanged = "";
  var bMotorsOn = false;

  var abrp_cfg = {
    "url": URL,                     // abrp api url (by default, URL)

  };

  // check if json object is empty
  function isJsonEmpty(obj) {
    for(var key in obj) {
      if(obj.hasOwnProperty(key))
        return false;
      }
    return true;
  }

  // Read & process config:
  function readConfig() {
    // check if config exist
    var read_cfg = OvmsConfig.GetValues("usr", "abrp.");
    print(JSON.stringify(read_cfg) + CR);
    if (isJsonEmpty(read_cfg) == true) {
      // no config yet, set the default values
      OvmsConfig.SetValues("usr","abrp.",abrp_cfg);
    } else {
      // config existing
      abrp_cfg.url = read_cfg.url;

    }
  }

  // Make json telemetry object
  function InitTelemetryObj() {
    var myJSON = {
      "utc": 0,
      "soc": 0,
      "soh": 0,
      "speed": 0,
      "lat": 0,
      "lon": 0,
      "alt": 0,
      "ext_temp": 0,
      "is_charging": 0,
      "batt_temp": 0,
      "voltage": 0,
      "current": 0,
      "power": 0
    };
    return myJSON;
  }

  // Fill json telemetry object
  function UpdateTelemetryObj(myJSON) {
    var read_num = 0;
    var read_str = "";
    var read_bool = false;

    sHasChanged = "";

    if (bMotorsOn) {
      sHasChanged = "_MOTORS-ON";
      bMotorsOn = false;
    }

    read_num = Number(OvmsMetrics.Value("v.b.soc"));
    if (myJSON.soc != read_num) {
      myJSON.soc = read_num;
      sHasChanged += "_SOC:" + myJSON.soc + "%";
    }

    read_num = Number(OvmsMetrics.Value("v.b.soh"));
    if (myJSON.soh != read_num) {
      myJSON.soh = read_num;
      sHasChanged += "_SOH:" + myJSON.soh + "%";
    }


    //myJSON.lat = OvmsMetrics.AsFloat("v.p.latitude").toFixed(3);
    //above code line works, except when value is undefined, after reboot

    read_num = OvmsMetrics.AsFloat("v.p.latitude");
    read_num = read_num.toFixed(3);
    if (myJSON.lat != read_num) {
      myJSON.lat = read_num;
      sHasChanged += "_LAT:" + myJSON.lat + "°";
    }

    read_num = Number(OvmsMetrics.Value("v.p.longitude"));
    read_num = read_num.toFixed(3);
    if (myJSON.lon != read_num) {
      myJSON.lon = read_num;
      sHasChanged += "_LON:" + myJSON.lon + "°";
    }

    read_num = Number(OvmsMetrics.Value("v.p.altitude"));
    read_num = read_num.toFixed();
    if ( (myJSON.alt > (read_num-2)) && (myJSON.alt < (read_num+2)) ) {
      myJSON.alt = read_num;
      sHasChanged += "_ALT:" + myJSON.alt + "m";
    }

    read_num = Number(OvmsMetrics.Value("v.b.power"));
    myJSON.power = read_num.toFixed(1);

    myJSON.speed=Number(OvmsMetrics.Value("v.p.speed"));
    myJSON.batt_temp=Number(OvmsMetrics.Value("v.b.temp"));
    myJSON.ext_temp=Number(OvmsMetrics.Value("v.e.temp"));
    myJSON.voltage=Number(OvmsMetrics.Value("v.b.voltage"));
    myJSON.current=Number(OvmsMetrics.Value("v.b.current"));

    myJSON.utc = Math.trunc(Date.now()/1000);
    //myJSON.utc = OvmsMetrics.Value("m.time.utc");

    // read_bool = Boolean(OvmsMetrics.Value("v.c.charging"));
    // v.c.charging is also on when regen => not wanted here
    read_str = OvmsMetrics.Value("v.c.state");
    if ( (read_str == "charging") || (read_str == "topoff") ) {
      myJSON.is_charging = 1;
      read_str = OvmsMetrics.Value("v.c.mode");
      if (sHasChanged != "") {
        sHasChanged += "_CHRG:" + read_str + "(" + OvmsMetrics.Value("v.c.charging") + ")";
        print("Charging in mode " + read_str + CR);
      }
    } else {
      myJSON.is_charging = 0;
    }

    myJSON.car_model = abrp_cfg.car_model;

    return (sHasChanged != "");
  }

  // Show available vehicle data
  function DisplayLiveData(myJSON) {
    var newcontent = "";
    newcontent += "altitude = " + myJSON.alt       + "m"  + CR;    //GPS altitude
    newcontent += "latitude = " + myJSON.lat       + "°"  + CR;    //GPS latitude
    newcontent += "longitude= " + myJSON.lon       + "°"  + CR;    //GPS longitude
    newcontent += "ext temp = " + myJSON.ext_temp  + "°C" + CR;    //Ambient temperature
    newcontent += "charge   = " + myJSON.soc       + "%"  + CR;    //State of charge
    newcontent += "health   = " + myJSON.soh       + "%"  + CR;    //State of health
    newcontent += "bat temp = " + myJSON.batt_temp + "°C" + CR;    //Main battery momentary temperature
    newcontent += "voltage  = " + myJSON.voltage   + "V"  + CR;    //Main battery momentary voltage
    newcontent += "current  = " + myJSON.current   + "A"  + CR;    //Main battery momentary current
    newcontent += "power    = " + myJSON.power     + "kW" + CR;    //Main battery momentary power
    newcontent += "charging = " + myJSON.is_charging + CR;         //yes = currently charging
    print(newcontent);
  }

  function InitTelemetry() {
    objTLM = InitTelemetryObj();
    sHasChanged = "";
  }

  function UpdateTelemetry() {
    var bChanged = UpdateTelemetryObj(objTLM);
    if (bChanged) { DisplayLiveData(objTLM); }
    return bChanged;
  }

  function CloseTelemetry() {
    objTLM = null;
    sHasChanged = "";
  }

  // http request callback if successful
  function OnRequestDone(resp) {
    print("response="+JSON.stringify(resp)+CR);
    //OvmsNotify.Raise("info", "usr.abrp.status", "ABRP::" + sHasChanged);
  }

  // http request callback if failed
  function OnRequestFail(error) {
    print("error="+JSON.stringify(error)+CR);
    OvmsNotify.Raise("info", "usr.abrp.status", "ABRP::" + JSON.stringify(error));
  }

  // Return full url with JSON telemetry object
  function GetUrlABRP() {
    var urljson = abrp_cfg.url;
    urljson += "?";
    //urljson += "api_key=" + OVMS_API_KEY;
    //urljson += "&";
    //urljson += "token=" + abrp_cfg.user_token;
    //urljson += "&";
    urljson += "tlm=" + encodeURIComponent(JSON.stringify(objTLM));
    print(urljson + CR);
    return urljson;
  }

  // Return config object for HTTP request
  function GetURLcfg() {
    var cfg = {
      //url: GetUrlABRP(),
      url: "http://104.248.48.68:8080",
      done: function(resp) {OnRequestDone(resp)},
      fail: function(err)  {OnRequestFail(err)}
    };
    return cfg;
  }

  function SendLiveData() {
    if (UpdateTelemetry()) {
      HTTP.Request( GetURLcfg() );
    }
  }

  function Reactivate_MotorsOn() {
    bMotorsOn = true;
    SendLiveData();
  }

  function InitTimer() {
    objTimer = PubSub.subscribe(TIMER_INTERVAL, SendLiveData);
    objEvent = PubSub.subscribe(EVENT_MOTORS_ON, SendLiveData);
  }

  function CloseTimer() {
    PubSub.unsubscribe(objEvent);
    PubSub.unsubscribe(objTimer);
    objEvent = null;
    objTimer = null;
  }

  // API method abrp.onetime():
  //   Read and send data, but only once, no timer launched
  exports.onetime = function() {
    readConfig();
    InitTelemetry();
    SendLiveData();
    CloseTelemetry();
  }

  // API method abrp.info():
  //   Do not send any data, just read vehicle data and writes in the console
  exports.info = function() {
    readConfig();
    InitTelemetry();
    UpdateTelemetry();
    CloseTelemetry();
  }

  // API method abrp.send():
  //   Checks every minut if important data has changed, and send it
  exports.send = function(onoff) {
    if (onoff) {
      readConfig();
      if (objTimer != null) {
        print("Already running !" + CR);
        return;
      }
      print("Start sending data..." + CR);
      InitTelemetry();
      SendLiveData();
      InitTimer();
      OvmsNotify.Raise("info", "usr.abrp.status", "ABRP::started");
    } else {
      if (objTimer == null) {
        print("Already stopped !" + CR);
        return;
      }
      print("Stop sending data" + CR);
      CloseTimer();
      CloseTelemetry();
      OvmsNotify.Raise("info", "usr.abrp.status", "ABRP::stopped");
    }
  }