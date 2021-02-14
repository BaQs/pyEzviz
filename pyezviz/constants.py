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
    """Sensor types. HA sensor type or hide to not add as sensor"""

    name = "hide"
    serial = "hide"
    sw_version = "None"
    upgrade_available = "None"
    device_category = "hide"
    device_sub_category = "None"
    privacy = "hide"
    sleep = "hide"
    audio = "hide"
    ir_led = "hide"
    state_led = "hide"
    follow_move = "hide"
    alarm_sound_mod = "None"
    local_ip = "hide"
    battery_level = "battery"
    detection_sensibility = "None"
    last_alarm_time = "None"
    Seconds_Last_Trigger = "None"
    last_alarm_pic = "None"
    local_rtsp_port = "hide"
    supported_channels = "None"
    wifiInfos = "None"
    wan_ip = "None"


class BinarySensorType(Enum):
    """Binary sensor types. HA sensor type or hide to not add as sensor"""

    Motion_Trigger = "motion"
    PIR_Status = "motion"
    alarm_schedules_enabled = "None"
    encrypted = "None"
    switches = "None"
    alarm_notify = "hide"
