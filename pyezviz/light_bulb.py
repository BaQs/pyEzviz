"""pyezviz camera api."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .constants import DeviceSwitchType
from .exceptions import PyEzvizError
from .utils import fetch_nested_value

if TYPE_CHECKING:
    from .client import EzvizClient


class EzvizLightBulb:
    """Initialize Ezviz Light Bulb object."""

    def __init__(
            self, client: EzvizClient, serial: str, device_obj: dict | None = None
    ) -> None:
        """Initialize the light bulb object."""
        self._client = client
        self._serial = serial
        self._device = (
            device_obj if device_obj else self._client.get_device_infos(self._serial)
        )
        self._feature_json = self.get_feature_json()
        self._switch: dict[int, bool] = {
            switch["type"]: switch["enable"] for switch in self._device["SWITCH"]
        }
        if DeviceSwitchType.ALARM_LIGHT.value not in self._switch:
            # trying to have same interface as the camera's light
            self._switch[DeviceSwitchType.ALARM_LIGHT.value] = self.get_feature_item("light_switch")["dataValue"]

    def fetch_key(self, keys: list, default_value: Any = None) -> Any:
        """Fetch dictionary key."""
        return fetch_nested_value(self._device, keys, default_value)

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

    def get_feature_json(self) -> Any:
        """Parse the FEATURE json."""
        try:
            json_output = json.loads(self._device["FEATURE"]["featureJson"])

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode FEATURE: "
                + str(err)
            ) from err

        return json_output

    def get_feature_item(self, key: str, default_value: Any = None) -> Any:
        """Get items fron FEATURE."""
        items = self._feature_json["featureItemDtos"]
        for item in items:
            if item["itemKey"] == key:
                return item
        return default_value

    def get_product_id(self) -> Any:
        """Get product id."""
        return self._feature_json["productId"]

    def status(self) -> dict[Any, Any]:
        """Return the status of the light bulb."""
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
            "local_ip": self._local_ip(),
            "wan_ip": self.fetch_key(["CONNECTION", "netIp"]),
            "mac_address": self.fetch_key(["deviceInfos", "mac"]),
            "supported_channels": self.fetch_key(["deviceInfos", "channelNumber"]),
            "wifiInfos": self._device["WIFI"],
            "switches": self._switch,
            "optionals": self.fetch_key(["STATUS", "optionals"]),
            "supportExt": self._device["deviceInfos"]["supportExt"],
            "ezDeviceCapability": self.fetch_key(["deviceInfos", "ezDeviceCapability"]),

            "featureItems": self._feature_json["featureItemDtos"],
            "productId": self._feature_json["productId"],
            "color_temperature": self.get_feature_item("color_temperature")["dataValue"],

            "is_on": self.get_feature_item("light_switch")["dataValue"],
            "brightness": self.get_feature_item("brightness")["dataValue"],
            # same as brightness... added in order to keep "same interface" between camera and light bulb objects
            "alarm_light_luminance": self.get_feature_item("brightness")["dataValue"],
        }

    def toggle_switch(self) -> bool:
        """Toggle on/off light bulb."""
        item = self.get_feature_item("light_switch")
        return self._client.set_device_feature_by_key(
            self._serial,
            self.get_product_id(),
            not bool(item["dataValue"]),
            item["itemKey"]
        )
