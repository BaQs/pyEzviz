"""pyezviz camera api."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from .constants import DeviceCatagories, DeviceSwitchType, SoundMode
from .exceptions import PyEzvizError

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
            switch["type"]: switch["enable"]
            for switch in self._device.get("SWITCH", {})
        }

    def _detection_sensibility(self) -> Any:
        """Load detection sensitivity."""
        result = "Unknown"

        if self._switch.get(DeviceSwitchType.AUTO_SLEEP.value) is not True:
            if (
                self._device["deviceInfos"]["deviceCategory"]
                == DeviceCatagories.BATTERY_CAMERA_DEVICE_CATEGORY.value
            ):
                result = self._client.get_detection_sensibility(
                    self._serial,
                    "3",
                )
            else:
                result = self._client.get_detection_sensibility(self._serial)

        if self._switch.get(DeviceSwitchType.AUTO_SLEEP.value) is True:
            result = "Hibernate"

        return result

    def _alarm_list(self) -> None:
        """Get last alarm info for this camera's self._serial."""
        _alarmlist = self._client.get_alarminfo(self._serial)

        if _alarmlist["page"].get("totalResults") > 0:
            self._last_alarm = _alarmlist["alarms"][0]
            return self._motion_trigger()

    def _local_ip(self) -> Any:
        """Fix empty ip value for certain cameras."""
        if (
            self._device["WIFI"].get("address")
            and self._device["WIFI"]["address"] != "0.0.0.0"
        ):
            return self._device["WIFI"]["address"]

        # Seems to return none or 0.0.0.0 on some.
        if (
            self._device["CONNECTION"].get("localIp")
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
            item for item in self._device.get("TIME_PLAN", {}) if item.get("type") == 2
        ]

        if _alarm_schedules:
            return bool(_alarm_schedules[0].get("enable"))

        return False

    def status(self) -> dict[Any, Any]:
        """Return the status of the camera."""
        self._alarm_list()

        return {
            "serial": self._serial,
            "name": self._device["deviceInfos"].get("name"),
            "version": self._device["deviceInfos"].get("version"),
            "upgrade_available": bool(
                self._device["UPGRADE"].get("isNeedUpgrade") == 3
            ),
            "status": self._device["deviceInfos"].get("status"),
            "device_category": self._device["deviceInfos"].get("deviceCategory"),
            "device_sub_category": self._device["deviceInfos"].get("deviceSubCategory"),
            "sleep": self._switch.get(DeviceSwitchType.SLEEP.value)
            or self._switch.get(DeviceSwitchType.AUTO_SLEEP.value),
            "privacy": self._switch.get(DeviceSwitchType.PRIVACY.value),
            "audio": self._switch.get(DeviceSwitchType.SOUND.value),
            "ir_led": self._switch.get(DeviceSwitchType.INFRARED_LIGHT.value),
            "state_led": self._switch.get(DeviceSwitchType.LIGHT.value),
            "upgrade_percent": self._device["STATUS"].get("upgradeProcess"),
            "upgrade_in_progress": bool(
                self._device["STATUS"].get("upgradeStatus") == 0
            ),
            "follow_move": self._switch.get(DeviceSwitchType.MOBILE_TRACKING.value),
            "alarm_notify": bool(self._device["STATUS"].get("globalStatus")),
            "alarm_schedules_enabled": self._is_alarm_schedules_enabled(),
            "alarm_sound_mod": SoundMode(
                self._device["STATUS"].get("alarmSoundMode")
            ).name,
            "encrypted": bool(self._device["STATUS"].get("isEncrypt")),
            "local_ip": self._local_ip(),
            "wan_ip": self._device["CONNECTION"].get("netIp"),
            "mac_address": self._device["deviceInfos"].get("mac"),
            "local_rtsp_port": self._device["CONNECTION"].get("localRtspPort", "554")
            if self._device["CONNECTION"].get("localRtspPort", "554") != 0
            else "554",
            "supported_channels": self._device["deviceInfos"].get("channelNumber"),
            "detection_sensibility": self._detection_sensibility(),
            "battery_level": self._device["STATUS"]
            .get("optionals", {})
            .get("powerRemaining"),
            "PIR_Status": self._device["STATUS"].get("pirStatus"),
            "Motion_Trigger": self._alarmmotiontrigger.get("alarm_trigger_active"),
            "Seconds_Last_Trigger": self._alarmmotiontrigger.get("timepassed"),
            "last_alarm_time": self._last_alarm.get("alarmStartTimeStr"),
            "last_alarm_pic": self._last_alarm.get(
                "picUrl",
                "https://eustatics.ezvizlife.com/ovs_mall/web/img/index/EZVIZ_logo.png?ver=3007907502",
            ),
            "last_alarm_type_code": self._last_alarm.get("alarmType", "0000"),
            "last_alarm_type_name": self._last_alarm.get("sampleName", "NoAlarm"),
            "wifiInfos": self._device.get("WIFI"),
            "switches": self._switch,
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
