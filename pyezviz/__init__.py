"""init pyezviz."""
from pyezviz.camera import EzvizCamera
from pyezviz.cas import EzvizCAS
from pyezviz.client import EzvizClient
from pyezviz.constants import (DefenseModeType, DeviceCatagories,
                               DeviceSwitchType, SoundMode)
from pyezviz.exceptions import (AuthTestResultFailed, HTTPError, InvalidHost,
                                InvalidURL, PyEzvizError)
from pyezviz.mqtt import MQTTClient
from pyezviz.test_cam_rtsp import TestRTSPAuth

__all__ = [
    "EzvizCamera",
    "EzvizClient",
    "PyEzvizError",
    "InvalidURL",
    "HTTPError",
    "InvalidHost",
    "AuthTestResultFailed",
    "EzvizCAS",
    "MQTTClient",
    "DefenseModeType",
    "DeviceCatagories",
    "DeviceSwitchType",
    "SoundMode",
    "TestRTSPAuth",
]
