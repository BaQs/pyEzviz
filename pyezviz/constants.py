"""Device switch types relationship."""
from enum import Enum, unique

FEATURE_CODE = "1fc28fa018178a1cd1c091b13b2f9f02"
XOR_KEY = b"\x0c\x0eJ^X\x15@Rr"
DEFAULT_TIMEOUT = 25
MAX_RETRIES = 3
REQUEST_HEADER = {
    "featureCode": FEATURE_CODE,
    "clientType": "3",
    "osVersion": "",
    "clientVersion": "",
    "netType": "WIFI",
    "customno": "1000001",
    "ssid": "",
    "clientNo": "web_site",
    "appId": "ys7",
    "language": "en_GB",
    "lang": "en",
    "sessionId": "",
    "User-Agent": "okhttp/3.12.1",
}  # Standard android header.


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
    INTELLIGENT_PQ_SWITCH = 40
    DOORBELL_TALK = 101
    HUMAN_INTELLIGENT_DETECTION = 200
    LIGHT_FLICKER = 301
    ALARM_LIGHT = 303
    ALARM_LIGHT_RELEVANCE = 305
    DEVICE_HUMAN_RELATE_LIGHT = 41
    TAMPER_ALARM = 306
    DETECTION_TYPE = 451
    OUTLET_RECOVER = 600
    CHIME_INDICATOR_LIGHT = 611
    TRACKING = 650
    CRUISE_TRACKING = 651
    PARTIAL_IMAGE_OPTIMIZE = 700
    FEATURE_TRACKING = 701


class SoundMode(Enum):
    """Alarm sound level description."""

    SILENT = 2
    SOFT = 0
    INTENSE = 1
    CUSTOM = 3
    PLAN = 4


class DefenseModeType(Enum):
    """Defense mode name and number."""

    HOME_MODE = 1
    AWAY_MODE = 2
    SLEEP_MODE = 3
    UNSET_MODE = 0


class DeviceCatagories(Enum):
    """Supported device categories."""

    COMMON_DEVICE_CATEGORY = "COMMON"
    CAMERA_DEVICE_CATEGORY = "IPC"
    BATTERY_CAMERA_DEVICE_CATEGORY = "BatteryCamera"
    DOORBELL_DEVICE_CATEGORY = "BDoorBell"
    BASE_STATION_DEVICE_CATEGORY = "XVR"
    CAT_EYE_CATEGORY = "CatEye"
