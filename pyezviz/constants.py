"""Device switch types relationship."""
from enum import Enum, unique


@unique
class DeviceSwitchType(Enum):
    """Device switch name and number."""

    ALARM_TONE = 1
    STREAM_ADAPTIVE = 2
    LIGHT = 3
    INTELLIGENT_ANALYSIS = 4
    LOG_UPLOAD = 5
    DEFENCE_PLAN = 6
    PRIVACY = 7
    SOUND_LOCALIZATION = 8
    CRUISE = 9
    INFRARED_LIGHT = 10
    WIFI = 11
    WIFI_MARKETING = 12
    WIFI_LIGHT = 13
    PLUG = 14
    SLEEP = 21
    SOUND = 22
    BABY_CARE = 23
    LOGO = 24
    MOBILE_TRACKING = 25
    CHANNELOFFLINE = 26
    ALL_DAY_VIDEO = 29
    AUTO_SLEEP = 32
    ROAMING_STATUS = 34
    DEVICE_4G = 35
    ALARM_REMIND_MODE = 37
    OUTDOOR_RINGING_SOUND = 39
    HUMAN_INTELLIGENT_DETECTION = 200
    LIGHT_FLICKER = 301
    ALARM_LIGHT = 303
    ALARM_LIGHT_RELEVANCE = 305
    OUTLET_RECOVER = 600
    TRACKING = 650


class SoundMode(Enum):
    """Alarm sound level descryption """

    silent = 2
    soft = 0
    intense = 1


class DefenseModeType(Enum):
    """Defense mode name and number."""

    HOME_MODE = 1
    AWAY_MODE = 2


class DeviceCatagories(Enum):
    """Supported device catagories"""

    COMMON_DEVICE_CATEGORY = "COMMON"
    CAMERA_DEVICE_CATEGORY = "IPC"
    BATTERY_CAMERA_DEVICE_CATEGORY = "BatteryCamera"
    DOORBELL_DEVICE_CATEGORY = "BDoorBell"
    BASE_STATION_DEVICE_CATEGORY = "XVR"


class SensorType(Enum):
    """Sensor types"""

    BATTERY = "battery"
    WIFI = "wifi"


class BinarySensorType(Enum):
    """Binary sensor types"""

    MOTION = "motion"
    GENERIC = "None"
