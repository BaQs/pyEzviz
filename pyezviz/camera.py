"""pyezviz camera api."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from .constants import DeviceSwitchType, SoundMode
from .exceptions import PyEzvizError
from .utils import fetch_nested_value, string_to_list

if TYPE_CHECKING:
    from .client import EzvizClient


class EzvizCamera:
    """Initialize Ezviz camera object."""

    def __init__(
        self, client: EzvizClient, serial: str, device_obj: dict | None = None
    ) -> None:
        """Initialize the camera object."""
        self._client = client
        self._serial = serial
        self._alarmmotiontrigger: dict[str, Any] = {
            "alarm_trigger_active": False,
            "timepassed": None,
        }
        self._device = (
            device_obj if device_obj else self._client.get_device_infos(self._serial)
        )
        self._last_alarm: dict[str, Any] = {}
        self._switch: dict[int, bool] = {
            switch["type"]: switch["enable"] for switch in self._device["SWITCH"]
        }

    def fetch_key(self, keys: list, default_value: Any = None) -> Any:
        """Fetch dictionary key."""
        return fetch_nested_value(self._device, keys, default_value)

    def _alarm_list(self) -> None:
        """Get last alarm info for this camera's self._serial."""
        _alarmlist = self._client.get_alarminfo(self._serial)

        if fetch_nested_value(_alarmlist, ["page", "totalResults"], 0) > 0:
            self._last_alarm = _alarmlist["alarms"][0]
            return self._motion_trigger()

    def _local_ip(self) -> Any:
        """Fix empty ip value for certain cameras."""
        if (
            self.fetch_key(["WIFI", "address"])
            and self._device["WIFI"]["address"] != "0.0.0.0"
        ):
            return self._device["WIFI"]["address"]

        # Seems to return none or 0.0.0.0 on some.
        if (
            self.fetch_key(["CONNECTION", "localIp"])
            and self._device["CONNECTION"]["localIp"] != "0.0.0.0"
        ):
            return self._device["CONNECTION"]["localIp"]

        return "0.0.0.0"

    def _motion_trigger(self) -> None:
        """Create motion sensor based on last alarm time."""
        if not self._last_alarm.get("alarmStartTimeStr"):
            return

        _today_date = datetime.date.today()
        _now = datetime.datetime.now().replace(microsecond=0)

        _last_alarm_time = datetime.datetime.strptime(
            self._last_alarm["alarmStartTimeStr"].replace("Today", str(_today_date)),
            "%Y-%m-%d %H:%M:%S",
        )

        # returns a timedelta object
        timepassed = _now - _last_alarm_time

        self._alarmmotiontrigger = {
            "alarm_trigger_active": bool(timepassed < datetime.timedelta(seconds=60)),
            "timepassed": timepassed.total_seconds(),
        }

    def _is_alarm_schedules_enabled(self) -> bool:
        """Check if alarm schedules enabled."""
        _alarm_schedules = [
            item for item in self._device["TIME_PLAN"] if item.get("type") == 2
        ]

        if _alarm_schedules:
            return bool(_alarm_schedules[0].get("enable"))

        return False

    def status(self) -> dict[Any, Any]:
        """Return the status of the camera."""
        self._alarm_list()

        return {
            "serial": self._serial,
            "name": self.fetch_key(["deviceInfos", "name"]),
            "version": self.fetch_key(["deviceInfos", "version"]),
            "upgrade_available": bool(
                self.fetch_key(["UPGRADE", "isNeedUpgrade"]) == 3
            ),
            "status": self.fetch_key(["deviceInfos", "status"]),
            "device_category": self.fetch_key(["deviceInfos", "deviceCategory"]),
            "device_sub_category": self.fetch_key(["deviceInfos", "deviceSubCategory"]),
            "upgrade_percent": self.fetch_key(["STATUS", "upgradeProcess"]),
            "upgrade_in_progress": bool(
                self.fetch_key(["STATUS", "upgradeStatus"]) == 0
            ),
            "latest_firmware_info": self.fetch_key(["UPGRADE", "upgradePackageInfo"]),
            "alarm_notify": bool(self.fetch_key(["STATUS", "globalStatus"])),
            "alarm_schedules_enabled": self._is_alarm_schedules_enabled(),
            "alarm_sound_mod": SoundMode(
                self.fetch_key(["STATUS", "alarmSoundMode"], -1)
            ).name,
            "encrypted": bool(self.fetch_key(["STATUS", "isEncrypt"])),
            "encrypted_pwd_hash": self.fetch_key(["STATUS", "encryptPwd"]),
            "local_ip": self._local_ip(),
            "wan_ip": self.fetch_key(["CONNECTION", "netIp"]),
            "mac_address": self.fetch_key(["deviceInfos", "mac"]),
            "local_rtsp_port": self.fetch_key(["CONNECTION", "localRtspPort"], "554")
            if self.fetch_key(["CONNECTION", "localRtspPort"], "554") != 0
            else "554",
            "supported_channels": self.fetch_key(["deviceInfos", "channelNumber"]),
            "battery_level": self.fetch_key(["STATUS", "optionals", "powerRemaining"]),
            "PIR_Status": self.fetch_key(["STATUS", "pirStatus"]),
            "Motion_Trigger": self._alarmmotiontrigger["alarm_trigger_active"],
            "Seconds_Last_Trigger": self._alarmmotiontrigger["timepassed"],
            "last_alarm_time": self._last_alarm.get(
                "alarmStartTimeStr", "2000-01-01 00:00:00"
            ),
            "last_alarm_pic": self._last_alarm.get(
                "picUrl",
                "https://eustatics.ezvizlife.com/ovs_mall/web/img/index/EZVIZ_logo.png?ver=3007907502",
            ),
            "last_alarm_type_code": self._last_alarm.get("alarmType", "0000"),
            "last_alarm_type_name": self._last_alarm.get("sampleName", "NoAlarm"),
            "cam_timezone": self.fetch_key(["STATUS", "optionals", "timeZone"]),
            "push_notify_alarm": not bool(self.fetch_key(["NODISTURB", "alarmEnable"])),
            "push_notify_call": not bool(
                self.fetch_key(["NODISTURB", "callingEnable"])
            ),
            "alarm_light_luminance": self.fetch_key(
                ["STATUS", "optionals", "Alarm_Light", "luminance"]
            ),
            "Alarm_DetectHumanCar": self.fetch_key(
                ["STATUS", "optionals", "Alarm_DetectHumanCar", "type"]
            ),
            "diskCapacity": string_to_list(
                self.fetch_key(["STATUS", "optionals", "diskCapacity"])
            ),
            "NightVision_Model": self.fetch_key(
                ["STATUS", "optionals", "NightVision_Model"]
            ),
            "batteryCameraWorkMode": self.fetch_key(
                ["STATUS", "optionals", "workMode"]
            ),
            "wifiInfos": self._device["WIFI"],
            "switches": self._switch,
            "optionals": self.fetch_key(["STATUS", "optionals"]),
            "supportExt": self._device["deviceInfos"]["supportExt"],
            "ezDeviceCapability": self.fetch_key(["deviceInfos", "ezDeviceCapability"]),
        }

    def move(self, direction: str, speed: int = 5) -> bool:
        """Move camera."""
        if direction not in ["right", "left", "down", "up"]:
            raise PyEzvizError(f"Invalid direction: {direction} ")

        # launch the start command
        self._client.ptz_control(str(direction).upper(), self._serial, "START", speed)
        # launch the stop command
        self._client.ptz_control(str(direction).upper(), self._serial, "STOP", speed)

        return True

    def move_coordinates(self, x_axis: float, y_axis: float) -> bool:
        """Move camera to specified coordinates."""
        return self._client.ptz_control_coordinates(self._serial, x_axis, y_axis)

    def alarm_notify(self, enable: int) -> bool:
        """Enable/Disable camera notification when movement is detected."""
        return self._client.set_camera_defence(self._serial, enable)

    def alarm_sound(self, sound_type: int) -> bool:
        """Enable/Disable camera sound when movement is detected."""
        # we force enable = 1 , to make sound...
        return self._client.alarm_sound(self._serial, sound_type, 1)

    def do_not_disturb(self, enable: int) -> bool:
        """Enable/Disable do not disturb.

        if motion triggers are normally sent to your device as a
        notification, then enabling this feature stops these notification being sent.
        The alarm event is still recorded in the EzViz app as normal.
        """
        return self._client.do_not_disturb(self._serial, enable)

    def alarm_detection_sensibility(
        self, sensibility: int, type_value: int = 0
    ) -> bool | str:
        """Enable/Disable camera sound when movement is detected."""
        # we force enable = 1 , to make sound...
        return self._client.detection_sensibility(self._serial, sensibility, type_value)

    def switch_device_audio(self, enable: int = 0) -> bool:
        """Switch audio status on a device."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.SOUND.value, enable
        )

    def switch_device_state_led(self, enable: int = 0) -> bool:
        """Switch led status on a device."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.LIGHT.value, enable
        )

    def switch_device_ir_led(self, enable: int = 0) -> bool:
        """Switch ir status on a device."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.INFRARED_LIGHT.value, enable
        )

    def switch_privacy_mode(self, enable: int = 0) -> bool:
        """Switch privacy mode on a device."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.PRIVACY.value, enable
        )

    def switch_sleep_mode(self, enable: int = 0) -> bool:
        """Switch sleep mode on a device."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.SLEEP.value, enable
        )

    def switch_follow_move(self, enable: int = 0) -> bool:
        """Switch follow move."""
        return self._client.switch_status(
            self._serial, DeviceSwitchType.MOBILE_TRACKING.value, enable
        )

    def switch_sound_alarm(self, enable: int = 0) -> bool:
        """Sound alarm on a device."""
        return self._client.sound_alarm(self._serial, enable)

    def change_defence_schedule(self, schedule: str, enable: int = 0) -> bool:
        """Change defence schedule. Requires json formatted schedules."""
        return self._client.api_set_defence_schedule(self._serial, schedule, enable)
