# Ezviz PyPi

[![Build Status](https://travis-ci.org/BaQs/pyEzviz.svg?branch=master)](https://travis-ci.org/BaQs/pyEzviz)
![Upload Python Package](https://github.com/BaQs/pyEzviz/workflows/Upload%20Python%20Package/badge.svg)

Pilot your Ezviz cameras with this module.

### Installing


```
pip install pyezviz
```

## Playing with it

```
pyezviz -u em@il -p PASS devices status
```

```
                         name  status device_category device_sub_category  sleep  privacy  audio  ir_led  state_led       local_ip local_rtsp_port detection_sensibility battery_level  alarm_schedules_enabled  alarm_notify  Motion_Trigger
D444444   backyard camera 1       1   BatteryCamera                 C3A   True    False   True    True      False  192.168.1.167             554             Hibernate           100                    False          True           False
D444444   Front door camera       1   BatteryCamera                 C3A   True    False   True    True      False  192.168.1.192             554             Hibernate            99                    False          True           False
D444444    courtyard camera       1   BatteryCamera                 C3A   True    False   True    True       True  192.168.1.133             554             Hibernate           100                    False         False           False
D444444  Living room camera       1             IPC                C6CN  False     True   True    True       True   192.168.1.39             554                     3          None                    False          True           False
D444444   Backyard camera 2       1             IPC           Husky Air  False    False   True    True      False  192.168.1.149             554                     1          None                    False          True            True

```

```
pyezviz -u em@il -p PASS camera --serial D44444 status
```

```
{
  "serial": "D44444",
  "name": "backyard camera 1",
  "version": "V5.2.4 build 200812",
  "upgrade_available": false,
  "status": 1,
  "device_category": "BatteryCamera",
  "device_sub_category": "C3A",
  "sleep": true,
  "privacy": false,
  "audio": true,
  "ir_led": true,
  "state_led": false,
  "follow_move": null,
  "alarm_notify": true,
  "alarm_schedules_enabled": false,
  "alarm_sound_mod": "SILENT",
  "encrypted": false,
  "local_ip": "192.168.1.167",
  "wan_ip": "8.8.8.8",
  "local_rtsp_port": "554",
  "supported_channels": 1,
  "detection_sensibility": "Hibernate",
  "battery_level": "100",
  "PIR_Status": 0,
  "Motion_Trigger": false,
  "Seconds_Last_Trigger": 2376.0,
  "last_alarm_time": "2021-11-13 14:11:37",
  "last_alarm_pic": "https://ieu.ezvizlife.com/v3/alarms/pic/get?fileId=dfghjfghjfghujfghjf",
  "wifiInfos": {
    "netName": "w0",
    "netType": "wireless",
    "address": "192.168.1.167",
    "mask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "signal": 100,
    "ssid": "HomeADSL"
  },
  "switches": {
    "1": true,
    "2": false,
    "3": false,
    "7": false,
    "10": true,
    "15": false,
    "21": false,
    "22": true,
    "29": false,
    "32": true,
    "38": false,
    "39": false,
    "202": false,
    "300": false,
    "301": false,
    "302": false
  }
}
```

Switch numbers to name mappings are stored in constants.py file.

## Running the tests
The tox configuration is already included.
Simply launch:
```
$ tox
```

(Do not forget to 'pip install tox' if you do not have it.)
Tests are written in the tests directory.
tests/data folder contains samples of EzvizLife API for tests purposes.


## Side notes

As there is no official documentation on the API, I had to reverse-engineer what is the one used in the Ezviz IOS APP.
Some Regions might operate on an isolated platform and require a url to be entered. US for example:

pyezviz -u username@domain.com -p PASS@123 -r apiius.ezvizlife.com devices status

## Contributing

Any contribution is welcome, considering the number of features the API provides, there is room for improvement!

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/baqs/pyEzviz/tags). 

## Authors

## License

This project is licensed under the ASL 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments


## Changelog


### 0.0.x
Draft versions
