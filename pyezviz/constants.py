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
    """Alarm sound level description."""

    silent = 2
    soft = 0
    intense = 1


class DefenseModeType(Enum):
    """Defense mode name and number."""

    HOME_MODE = 1
    AWAY_MODE = 2


class DeviceCatagories(Enum):
    """Supported device categories."""

    COMMON_DEVICE_CATEGORY = "COMMON"
    CAMERA_DEVICE_CATEGORY = "IPC"
    BATTERY_CAMERA_DEVICE_CATEGORY = "BatteryCamera"
    DOORBELL_DEVICE_CATEGORY = "BDoorBell"
    BASE_STATION_DEVICE_CATEGORY = "XVR"


class SensorType(Enum):
    """Sensors and their types to expose in HA."""

    sw_version = "None"
    alarm_sound_mod = "None"
    battery_level = "battery"
    detection_sensibility = "None"
    last_alarm_time = "None"
    Seconds_Last_Trigger = "None"
    last_alarm_pic = "None"
    supported_channels = "None"
    local_ip = "None"
    wan_ip = "None"
    PIR_Status = "motion"


class BinarySensorType(Enum):
    """Binary_sensors and their types to expose in HA."""

    Motion_Trigger = "motion"
    alarm_schedules_enabled = "None"
    encrypted = "None"
    upgrade_available = "None"
