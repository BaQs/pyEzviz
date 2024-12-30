# Ezviz PyPi

![Upload Python Package](https://github.com/BaQs/pyEzviz/workflows/Upload%20Python%20Package/badge.svg)

> [!WARNING]
> This repository is depreciated, continuing the work on https://github.com/RenierM26/pyEzvizApi **
> The new repository and package is called PyEzvizApi and starts with V1.0.0.0





Pilot your Ezviz cameras (and light bulbs) with this module.

### Installing


```
pip install pyezvizapi
```

## Playing with it

```
pyezvizapi -u em@il -p PASS devices status
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
pyezvizapi -u em@il -p PASS camera --serial D44444 status
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

### Light bulbs

```
pyezvizapi -u em@il -p PASS devices_light status
```

```
                  name  status device_category device_sub_category      local_ip               productId  is_on  brightness  color_temperature
D55555     Office lamp       1        lighting                 LB1  192.168.1.168 9C22222222A22A2AAEEEE2   True          55               5540
D55555    Kitchen lamp       1        lighting                 LB1  192.168.1.169 9C33333333A22A2AAEEEE2   True         100               6000

```

```
# toggles on/off the light bulb with serial D55555

pyezvizapi -u em@il -p PASS light --serial D55555 toggle
```

```
# retrieves details of a specific light bulb

pyezvizapi -u em@il -p PASS light --serial D55555 status
```

<details>
    <summary>Expand to see the response with the light bulb's details</summary>

```
{
  "serial": "D55555",
  "name": "Office lamp",
  "version": "V1.1.0 build 200814",
  "upgrade_available": false,
  "status": 1,
  "device_category": "lighting",
  "device_sub_category": "LB1",
  "upgrade_percent": 0,
  "upgrade_in_progress": false,
  "latest_firmware_info": null,
  "local_ip": "192.168.1.168",
  "wan_ip": null,
  "mac_address": "",
  "supported_channels": 0,
  "wifiInfos": {
    "netName": null,
    "netType": "wireless",
    "address": "192.168.1.168",
    "mask": "255.255.255.0",
    "gateway": "192.168.1.1",
    "signal": -56,
    "ssid": "HomeADSL"
  },
  "featureItems": [
    {
      "dataDesc": "[\"white\", \"color\", \"scene\",\"music\"]",
      "dataType": "enum",
      "dataValue": "white",
      "itemKey": "light_mode",
      "itemName": "亮灯模式",
      "transportType": "rw",
      "visible": 1
    },
    {
      "dataDesc": "{\"range_from\": 2700, \"range_to\": 6500, \"interval\": 10, \"multiple\": 0, \"unit\": \"k\"}",
      "dataType": "num",
      "dataValue": 5540,
      "itemKey": "color_temperature",
      "itemName": "色温",
      "transportType": "rw",
      "visible": 1
    },
    {
      "dataDesc": "{\"max_length\": 255}",
      "dataType": "char",
      "dataValue": "#52FF79",
      "itemKey": "color_rgb",
      "itemName": "彩光",
      "transportType": "rw",
      "visible": 1
    },
    {
      "dataDesc": "[{\"k\":\"sleep\",\"t\":\"color\",\"stat\":[{\"id\":1,\"b\":100,\"c\":\"#FFFFFF\",\"t\":4000}],\"trans\":{\"low\":1,\"dura\":1000},\"speed\":1000}]",
      "dataType": "json",
      "dataValue": [],
      "itemKey": "scene_conf",
      "itemName": "场景配置",
      "transportType": "rw",
      "visible": 1
    },
    {
      "dataDesc": "",
      "dataType": "bool",
      "dataValue": true,
      "itemKey": "light_switch",
      "itemName": "开关",
      "transportType": "rw",
      "visible": 1
    },
    {
      "dataDesc": "[\"e1\", \"e2\", \"e3\"]",
      "dataType": "fault",
      "itemKey": "common_fault",
      "itemName": "默认错误类型",
      "transportType": "rw",
      "visible": 0
    },
    {
      "dataDesc": "{\"range_from\": 1, \"range_to\": 100, \"interval\": 1, \"multiple\": 0, \"unit\": \"\"}",
      "dataType": "num",
      "dataValue": 55,
      "itemKey": "brightness",
      "itemName": "亮度",
      "transportType": "rw",
      "visible": 1
    },
    ...
  ],
  "productId": "9C22222222A22A2AAEEEE2",
  "switches": {},
  "optionals": {
    "latestUnbandTime": 1674813112997,
    "wanIp": "78.87.201.33",
    "updateCode": 0,
    "OnlineStatus": 1,
    "superState": 0,
    "latestUnbindTime": 1674813112997,
    "lastUpgradeTime": 1674815832305,
    "updateProcessExtend": ""
  },
  "supportExt": {
    "232": "0",
    "233": "0",
    "234": 0,
    "236": "1",
    "237": "1",
    "30": "0",
    "31": "0",
    "10": "1"
  },
  "ezDeviceCapability": "{\"232\":\"0\",\"233\":\"0\",\"234\":1,\"30\":\"0\",\"31\":\"0\",\"262\":\"0\",\"175\":\"1\",\"263\":\"0\"}",
  "is_on": true,
  "brightness": 55,
  "color_temperature": 5540
}

```
</details>

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

pyezvizapi -u username@domain.com -p PASS@123 -r apiius.ezvizlife.com devices status

## Contributing

Any contribution is welcome, considering the number of features the API provides, there is room for improvement!

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/baqs/pyEzviz/tags).

## Authors

## License

This project is licensed under the ASL 2.0 License - see the [LICENSE.md](LICENSE.md) file for details

## For those wou would like to contribute to this library, this should help fast track you:

All credit towards @ollu69 and @zimmra for the instructions below. While it's catered for LG, the EZVIZ app works the same way (so just use EZVIZ when any references to LG/Thinq android app pops up.)

Obtaining API Information
For troubleshooting issues, or investigating potential new devices, information can be intercepted from the API via a man-in-the-middle (MITM) http proxy interception method. Charles, mitmproxy, and Fiddler are examples of software that can be used to perform this mitm 'attack'/observation.

This can be done using a physical or virtual device that can run the EZVIZ API app. While it is possible with iOS, this instructions are for running Android on a modern Windows 11 PC.

Windows 11 enables the ability to run Android apps on most modern machines, making this process more accessible by eliminating the need for a physical device or separate emulation/virtualization software.

For information on how to do this with Windows Subsystem for Android (WSA) on Windows 11 using mitmproxy, please see the repo zimmra/frida-rootbypass-and-sslunpinning-lg-thinq.

### 0.0.x
Draft versions
