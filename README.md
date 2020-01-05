# Ezviz PyPi

[![Build Status](https://travis-ci.org/BaQs/pyEzviz.svg?branch=master)](https://travis-ci.org/BaQs/pyEzviz)

Pilot your Ezviz cameras with this module.

### Installing


```
pip install pyezviz
```

## Playing with it

```
pyezviz -u em@il -p PASS device -h
...
pyezviz -u em@il -p PASS --debug devices status
      serial            name  status  privacy  audio  ir_led  state_led  follow_move  alarm_notify alarm_sound_mod  encrypted       local_ip detection_sensibility
0  D733333333 C6N(D73333333)       1    False   True    True       True         True         False        Software       True  192.168.2.10                     3
1  D733333333 C6N(D73333333)       1    False   True    True       True         True         False        Software       True  192.168.2.13                     4
2  D833333333 C6N(D83333333)       1    False   True    True       True         True         False        Disabled       True  192.168.2.12                     3
3  D833333333 C6N(D83333333)       1    False   True    True       True        False         False        Software       True  192.168.2.11                     3
4  D933333333 C6N(D93333333)       1    False   True    True       True        False         False        Software       True  192.168.2.14                     3


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

As there is no official documentation on the API, I had to reverse-engineer what is the one used in the Ezviz IOS APP.


## Contributing

Any contribution is welcome, considering the number of features the API provides, there is room for improvement!

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/baqs/pyEzviz/tags). 

## Authors

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments


## Changelog


### 0.0.x
Draft versions
