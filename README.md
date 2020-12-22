# Ezviz PyPi

Pilot your Ezviz cameras with this module.

### Installing

1) Clone git repository.
2) pip install pyezviz
```

## Playing with it

Required Arguments : -u "username -p "password" devices/camera "action"

"devices", "Action" argument available: status, connection, switch-all, switch
"camera", "Action" arguments available: move, status, switch, alarm

pyezviz -u em@il -p PASS device -h
...
pyezviz -u em@il -p PASS --debug devices status

pyezviz u em@il -p PASS camera --serial D9999999 status
{
  "serial": "D9999999",
  "name": "courtyard camera",
  "status": 1,
  "device_sub_category": "C3A",
  "sleep": false,
  "privacy": false,
  "audio": true,
  "ir_led": true,
  "state_led": true,
  "follow_move": null,
  "alarm_notify": true,
  "alarm_sound_mod": "MUTE_MODE",
  "encrypted": false,
  "local_ip": "192.168.1.187",
  "local_rtsp_port": 0,
  "detection_sensibility": "4",
  "battery_level": "100",
  "PIR_Status": 0,
  "last_alarm_time": today 12:00
  "last_alarm_pic": eu.myalarmpicur.com/sadfadsfa
}

```


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

This module is based on BaQs/pyEzviz. Doesn't seem to be maintained any longer so I'm updating and improving on pyEzviz.


## Contributing

Any contribution is welcome, considering the number of features the API provides, there is room for improvement!

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository]. 

## Authors

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments


## Changelog


### 0.0.x
Draft versions
