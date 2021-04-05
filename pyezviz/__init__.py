"""init pyezviz."""
from pyezviz.camera import EzvizCamera
from pyezviz.client import EzvizClient, PyEzvizError
from pyezviz.constants import (DefenseModeType, DeviceCatagories,
                               DeviceSwitchType, SoundMode)
from pyezviz.test_cam_rtsp import AuthTestResultFailed, TestRTSPAuth

__all__ = [
    "EzvizCamera",
    "EzvizClient",
    "PyEzvizError",
    "DefenseModeType",
    "DeviceCatagories",
    "DeviceSwitchType",
    "SoundMode",
    "TestRTSPAuth",
    "AuthTestResultFailed",
]
