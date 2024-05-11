"""Ezviz API."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
import logging
from typing import Any
import urllib.parse
from uuid import uuid4

import requests

from .api_endpoints import (
    API_ENDPOINT_ALARM_SOUND,
    API_ENDPOINT_ALARMINFO_GET,
    API_ENDPOINT_CAM_ENCRYPTKEY,
    API_ENDPOINT_CANCEL_ALARM,
    API_ENDPOINT_CHANGE_DEFENCE_STATUS,
    API_ENDPOINT_CREATE_PANORAMIC,
    API_ENDPOINT_DETECTION_SENSIBILITY,
    API_ENDPOINT_DETECTION_SENSIBILITY_GET,
    API_ENDPOINT_DEVCONFIG_BY_KEY,
    API_ENDPOINT_DEVICE_STORAGE_STATUS,
    API_ENDPOINT_DEVICE_SYS_OPERATION,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_DO_NOT_DISTURB,
    API_ENDPOINT_GROUP_DEFENCE_MODE,
    API_ENDPOINT_IOT_FEATURE,
    API_ENDPOINT_LOGIN,
    API_ENDPOINT_LOGOUT,
    API_ENDPOINT_PAGELIST,
    API_ENDPOINT_PANORAMIC_DEVICES_OPERATION,
    API_ENDPOINT_PTZCONTROL,
    API_ENDPOINT_REFRESH_SESSION_ID,
    API_ENDPOINT_RETURN_PANORAMIC,
    API_ENDPOINT_SEND_CODE,
    API_ENDPOINT_SERVER_INFO,
    API_ENDPOINT_SET_DEFENCE_SCHEDULE,
    API_ENDPOINT_SET_LUMINANCE,
    API_ENDPOINT_SWITCH_DEFENCE_MODE,
    API_ENDPOINT_SWITCH_OTHER,
    API_ENDPOINT_SWITCH_SOUND_ALARM,
    API_ENDPOINT_SWITCH_STATUS,
    API_ENDPOINT_UNIFIEDMSG_LIST_GET,
    API_ENDPOINT_UPGRADE_DEVICE,
    API_ENDPOINT_USER_ID,
    API_ENDPOINT_V3_ALARMS,
    API_ENDPOINT_VIDEO_ENCRYPT,
)
from .camera import EzvizCamera
from .cas import EzvizCAS
from .constants import (
    DEFAULT_TIMEOUT,
    FEATURE_CODE,
    MAX_RETRIES,
    REQUEST_HEADER,
    DefenseModeType,
    DeviceCatagories,
    DeviceSwitchType,
    MessageFilterType,
)
from .exceptions import (
    EzvizAuthTokenExpired,
    EzvizAuthVerificationCode,
    HTTPError,
    InvalidURL,
    PyEzvizError,
)
from .light_bulb import EzvizLightBulb
from .utils import convert_to_dict, deep_merge

_LOGGER = logging.getLogger(__name__)


class EzvizClient:
    """Initialize api client object."""

    def __init__(
        self,
        account: str | None = None,
        password: str | None = None,
        url: str = "apiieu.ezvizlife.com",
        timeout: int = DEFAULT_TIMEOUT,
        token: dict | None = None,
    ) -> None:
        """Initialize the client object."""
        self.account = account
        self.password = (
            hashlib.md5(password.encode("utf-8")).hexdigest() if password else None
        )  # Ezviz API sends md5 of password
        self._session = requests.session()
        self._session.headers.update(REQUEST_HEADER)
        self._session.headers["sessionId"] = token["session_id"] if token else None
        self._token = token or {
            "session_id": None,
            "rf_session_id": None,
            "username": None,
            "api_url": url,
        }
        self._timeout = timeout
        self._cameras: dict[str, Any] = {}
        self._light_bulbs: dict[str, Any] = {}

    def _login(self, smscode: int | None = None) -> dict[Any, Any]:
        """Login to Ezviz API."""

        # Region code to url.
        if len(self._token["api_url"].split(".")) == 1:
            self._token["api_url"] = "apii" + self._token["api_url"] + ".ezvizlife.com"

        payload = {
            "account": self.account,
            "password": self.password,
            "featureCode": FEATURE_CODE,
            "msgType": "3" if smscode else "0",
            "bizType": "TERMINAL_BIND" if smscode else "",
            "cuName": "SGFzc2lv",  # hassio base64 encoded
            "smsCode": smscode,
        }

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_LOGIN,
                allow_redirects=False,
                data=payload,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occurred") from err

        except requests.HTTPError as err:
            raise HTTPError from err

        try:
            json_result = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_result["meta"]["code"] == 200:
            self._session.headers["sessionId"] = json_result["loginSession"][
                "sessionId"
            ]
            self._token = {
                "session_id": str(json_result["loginSession"]["sessionId"]),
                "rf_session_id": str(json_result["loginSession"]["rfSessionId"]),
                "username": str(json_result["loginUser"]["username"]),
                "api_url": str(json_result["loginArea"]["apiDomain"]),
            }

            self._token["service_urls"] = self.get_service_urls()

            return self._token

        if json_result["meta"]["code"] == 1100:
            self._token["api_url"] = json_result["loginArea"]["apiDomain"]
            _LOGGER.warning("Region incorrect!")
            _LOGGER.warning("Your region url: %s", self._token["api_url"])
            return self.login()

        if json_result["meta"]["code"] == 1012:
            raise PyEzvizError("The MFA code is invalid, please try again.")

        if json_result["meta"]["code"] == 1013:
            raise PyEzvizError("Incorrect Username.")

        if json_result["meta"]["code"] == 1014:
            raise PyEzvizError("Incorrect Password.")

        if json_result["meta"]["code"] == 1015:
            raise PyEzvizError("The user is locked.")

        if json_result["meta"]["code"] == 6002:
            self.send_mfa_code()
            raise EzvizAuthVerificationCode(
                "MFA enabled on account. Please retry with code."
            )

        raise PyEzvizError(f"Login error: {json_result['meta']}")

    def send_mfa_code(self) -> bool:
        """Send verification code."""
        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_SEND_CODE,
                data={
                    "from": self.account,
                    "bizType": "TERMINAL_BIND",
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not request MFA code: Got {json_output})")

        return True

    def get_service_urls(self) -> Any:
        """Get Ezviz service urls."""

        if not self._token["session_id"]:
            raise PyEzvizError("No Login token present!")

        try:
            req = self._session.get(
                f"https://{self._token['api_url']}{API_ENDPOINT_SERVER_INFO}",
                timeout=self._timeout,
            )
            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occurred") from err

        except requests.HTTPError as err:
            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Error getting Service URLs: {json_output}")

        service_urls = json_output["systemConfigInfo"]
        service_urls["sysConf"] = service_urls["sysConf"].split("|")

        return service_urls

    def _api_get_pagelist(
        self,
        page_filter: str,
        json_key: str | None = None,
        group_id: int = -1,
        limit: int = 30,
        offset: int = 0,
        max_retries: int = 0,
    ) -> Any:
        """Get data from pagelist API."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if page_filter is None:
            raise PyEzvizError("Trying to call get_pagelist without filter")

        params: dict[str, int | str] = {
            "groupId": group_id,
            "limit": limit,
            "offset": offset,
            "filter": page_filter,
        }

        try:
            req = self._session.get(
                "https://" + self._token["api_url"] + API_ENDPOINT_PAGELIST,
                params=params,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self._api_get_pagelist(
                    page_filter, json_key, group_id, limit, offset, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            # session is wrong, need to relogin
            self.login()
            _LOGGER.warning(
                "Could not get pagelist, relogging (max retries: %s), got: %s",
                str(max_retries),
                json_output,
            )
            return self._api_get_pagelist(
                page_filter, json_key, group_id, limit, offset, max_retries + 1
            )

        next_page = json_output["page"].get("hasNext", False)

        data = json_output[json_key] if json_key else json_output

        if next_page:
            next_offset = offset + limit
            # Recursive call to fetch next page
            next_data = self._api_get_pagelist(
                page_filter, json_key, group_id, limit, next_offset, max_retries
            )
            # Merge data from next page into current data
            data = deep_merge(data, next_data)

        return data


    def get_alarminfo(self, serial: str, limit: int = 1, max_retries: int = 0) -> dict:
        """Get data from alarm info API for camera serial."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        params: dict[str, int | str] = {
            "deviceSerials": serial,
            "queryType": -1,
            "limit": limit,
            "stype": -1,
        }

        try:
            req = self._session.get(
                "https://" + self._token["api_url"] + API_ENDPOINT_ALARMINFO_GET,
                params=params,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_alarminfo(serial, limit, max_retries + 1)

            raise HTTPError from err

        try:
            json_output: dict = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            if json_output["meta"]["code"] == 500:
                _LOGGER.debug(
                    "Retry getting alarm info, server returned busy: %s",
                    json_output,
                )
                return self.get_alarminfo(serial, limit, max_retries + 1)

            raise PyEzvizError(f"Could not get data from alarm api: Got {json_output})")

        return json_output

    def get_device_messages_list(
        self,
        serials: str | None = None,
        s_type: int = MessageFilterType.FILTER_TYPE_ALL_ALARM.value,
        limit: int | None = 20,  # 50 is the max even if you set it higher
        date: str = datetime.today().strftime("%Y%m%d"),
        end_time: str | None = None,
        tags: str = "ALL",
        max_retries: int = 0,
    ) -> dict:
        """Get data from Unified message list API."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        params: dict[str, int | str | None] = {
            "serials:": serials,
            "stype": s_type,
            "limit": limit,
            "date": date,
            "endTime": end_time,
            "tags": tags,
        }

        try:
            req = self._session.get(
                "https://" + self._token["api_url"] + API_ENDPOINT_UNIFIEDMSG_LIST_GET,
                params=params,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_device_messages_list(
                    serials, s_type, limit, date, end_time, tags, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output: dict = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(
                f"Could not get unified message list: Got {json_output})"
            )

        return json_output

    def switch_status(
        self,
        serial: str,
        status_type: int,
        enable: int,
        channel_no: int = 0,
        max_retries: int = 0,
    ) -> bool:
        """Camera features are represented as switches. Switch them on or off."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                url=f"https://{self._token['api_url']}{API_ENDPOINT_DEVICES}{serial}/{channel_no}/{enable}/{status_type}{API_ENDPOINT_SWITCH_STATUS}",
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.switch_status(serial, status_type, enable, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set the switch: Got {json_output})")

        if self._cameras.get(serial):
            self._cameras[serial]["switches"][status_type] = bool(enable)

        return True

    def switch_status_other(
        self,
        serial: str,
        status_type: int,
        enable: int,
        channel_number: int = 1,
        max_retries: int = 0,
    ) -> bool:
        """Features are represented as switches. This api is for alternative switch types to turn them on or off.

        All day recording is a good example.
        """
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                url=f"https://{self._token['api_url']}{API_ENDPOINT_DEVICES}{serial}{API_ENDPOINT_SWITCH_OTHER}",
                timeout=self._timeout,
                params={
                    "channelNo": channel_number,
                    "enable": enable,
                    "switchType": status_type,
                },
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.switch_status_other(
                    serial, status_type, enable, channel_number, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set the switch: Got {json_output})")

        return True

    def set_camera_defence(
        self,
        serial: str,
        enable: int,
        channel_no: int = 1,
        arm_type: str = "Global",
        actor: str = "V",
        max_retries: int = 0,
    ) -> bool:
        """Enable/Disable motion detection on camera."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                url=f"https://{self._token['api_url']}{API_ENDPOINT_DEVICES}{serial}/{channel_no}/{API_ENDPOINT_CHANGE_DEFENCE_STATUS}",
                timeout=self._timeout,
                data={
                    "type": arm_type,
                    "status": enable,
                    "actor": actor,
                },
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.set_camera_defence(serial, enable, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            if json_output["meta"]["code"] == 504:
                _LOGGER.warning(
                    "Arm or disarm for camera %s timed out. Retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.set_camera_defence(serial, enable, max_retries + 1)

            raise PyEzvizError(
                f"Could not arm or disarm Camera {serial}: Got {json_output})"
            )

        return True

    def set_battery_camera_work_mode(self, serial: str, value: int) -> bool:
        """Set battery camera work mode."""
        return self.set_device_config_by_key(serial, value, key="batteryCameraWorkMode")

    def set_detection_mode(self, serial: str, value: int) -> bool:
        """Set detection mode."""
        return self.set_device_config_by_key(
            serial, value=f'{{"type":{value}}}', key="Alarm_DetectHumanCar"
        )

    def set_night_vision_mode(
        self, serial: str, mode: int, luminance: int = 100
    ) -> bool:
        """Set night vision mode."""
        return self.set_device_config_by_key(
            serial,
            value=f'{{"graphicType":{mode},"luminance":{luminance}}}',
            key="NightVision_Model",
        )

    def set_display_mode(self, serial: str, mode: int) -> bool:
        """Change video color and saturation mode."""
        return self.set_device_config_by_key(
            serial, value=f'{{"mode":{mode}}}', key="display_mode"
        )

    def set_device_config_by_key(
        self,
        serial: str,
        value: Any,
        key: str,
        max_retries: int = 0,
    ) -> bool:
        """Change value on device by setting key."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        params = {"key": key, "value": value}
        params_str = urllib.parse.urlencode(
            params, safe="}{:"
        )  # not encode curly braces and colon

        full_url = f'https://{self._token["api_url"]}{API_ENDPOINT_DEVCONFIG_BY_KEY}{serial}/1/op'

        # EZVIZ api request needs {}: in the url, but requests lib doesn't allow it
        # so we need to manually prepare it
        req_prep = requests.Request(
            method="PUT", url=full_url, headers=self._session.headers
        ).prepare()
        req_prep.url = full_url + "?" + params_str

        try:
            req = self._session.send(
                request=req_prep,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.set_device_config_by_key(
                    serial, value, key, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set config key '${key}': Got {json_output})")

        return True

    def set_device_feature_by_key(
        self,
        serial: str,
        product_id: str,
        value: Any,
        key: str,
        max_retries: int = 0,
    ) -> bool:
        """Change value on device by setting the iot-feature's key.

        The FEATURE key that is part of 'device info' holds
        information about the device's functions (for example light_switch, brightness etc.).
        """
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        payload = json.dumps({"itemKey": key, "productId": product_id, "value": value})

        full_url = f'https://{self._token["api_url"]}{API_ENDPOINT_IOT_FEATURE}{serial.upper()}/0'

        headers = self._session.headers
        headers.update({"Content-Type": "application/json"})

        req_prep = requests.Request(
            method="PUT", url=full_url, headers=headers, data=payload
        ).prepare()

        try:
            req = self._session.send(
                request=req_prep,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.set_device_feature_by_key(
                    serial, product_id, value, key, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(
                f"Could not set iot-feature key '${key}': Got {json_output})"
            )

        return True

    def upgrade_device(self, serial: str, max_retries: int = 0) -> bool:
        """Upgrade device firmware."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_UPGRADE_DEVICE
                + serial
                + "/0/upgrade",
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.upgrade_device(serial, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(
                f"Could not initiate firmware upgrade: Got {json_output})"
            )

        return True

    def get_storage_status(self, serial: str, max_retries: int = 0) -> Any:
        """Get device storage status."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                url=f"https://{self._token['api_url']}{API_ENDPOINT_DEVICE_STORAGE_STATUS}",
                data={"subSerial": serial},
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_storage_status(serial, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Can't get storage status from device %s, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.get_storage_status(serial, max_retries + 1)
            raise PyEzvizError(
                f"Could not get device storage status: Got {json_output})"
            )

        return json_output["storageStatus"]

    def sound_alarm(self, serial: str, enable: int = 1, max_retries: int = 0) -> bool:
        """Sound alarm on a device."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DEVICES
                + serial
                + "/0"
                + API_ENDPOINT_SWITCH_SOUND_ALARM,
                data={
                    "enable": enable,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.sound_alarm(serial, enable, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set the alarm sound: Got {json_output})")

        return True

    def get_user_id(self, max_retries: int = 0) -> Any:
        """Get Ezviz userid, used by restricted api endpoints."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.get(
                f"https://{self._token['api_url']}{API_ENDPOINT_USER_ID}",
                timeout=self._timeout,
            )
            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_user_id(max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could get user id, Got: {json_output})")

        return json_output["deviceTokenInfo"]

    def set_video_enc(
        self,
        serial: str,
        enable: int = 1,
        camera_verification_code: str | None = None,
        new_password: str | None = None,
        old_password: str | None = None,
        max_retries: int = 0,
    ) -> bool:
        """Enable or Disable video encryption."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        device_token_info = self.get_user_id()
        cookies = {
            "clientType": "3",
            "clientVersion": "5.12.1.0517",
            "userId": device_token_info["userId"],
            "ASG_DisplayName": "home",
            "C_SS": self._session.headers["sessionId"],
            "lang": "en_US",
        }

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DEVICES
                + API_ENDPOINT_VIDEO_ENCRYPT,
                data={
                    "deviceSerial": serial,
                    "isEncrypt": enable,
                    "oldPassword": old_password,
                    "password": new_password,
                    "featureCode": FEATURE_CODE,
                    "validateCode": camera_verification_code,
                    "msgType": -1,
                },
                cookies=cookies,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.set_video_enc(
                    serial,
                    enable,
                    camera_verification_code,
                    new_password,
                    old_password,
                    max_retries + 1,
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set video encryption: Got {json_output})")

        return True

    def reboot_camera(
        self,
        serial: str,
        delay: int = 1,
        operation: int = 1,
        max_retries: int = 0,
    ) -> bool:
        """Reboot camera."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                url=f'https://{self._token["api_url"]}{API_ENDPOINT_DEVICE_SYS_OPERATION}{serial}',
                data={
                    "oper": operation,
                    "deviceSerial": serial,
                    "delay": delay,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.reboot_camera(
                    serial,
                    delay,
                    operation,
                    max_retries + 1,
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Unable to reboot camera, camera %s is unreachable, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.reboot_camera(serial, delay, operation, max_retries + 1)
            raise PyEzvizError(f"Could not reboot device {json_output})")

        return True

    def get_group_defence_mode(self, max_retries: int = 0) -> Any:
        """Get group arm status. The alarm arm/disarm concept on 1st page of app."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.get(
                "https://" + self._token["api_url"] + API_ENDPOINT_GROUP_DEFENCE_MODE,
                params={
                    "groupId": -1,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_group_defence_mode(max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(
                f"Could not get group defence status: Got {json_output})"
            )

        return json_output["mode"]

    # Not tested
    def cancel_alarm_device(self, serial: str, max_retries: int = 0) -> bool:
        """Cacnel alarm on an Alarm device."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_CANCEL_ALARM,
                data={"subSerial": serial},
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.sound_alarm(serial, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not cancel alarm siren: Got {json_output})")

        return True

    def load_devices(self) -> dict[Any, Any]:
        """Load and return all cameras and light bulb objects."""

        devices = self.get_device_infos()
        supported_categories = [
            DeviceCatagories.COMMON_DEVICE_CATEGORY.value,
            DeviceCatagories.CAMERA_DEVICE_CATEGORY.value,
            DeviceCatagories.BATTERY_CAMERA_DEVICE_CATEGORY.value,
            DeviceCatagories.DOORBELL_DEVICE_CATEGORY.value,
            DeviceCatagories.BASE_STATION_DEVICE_CATEGORY.value,
            DeviceCatagories.CAT_EYE_CATEGORY.value,
            DeviceCatagories.LIGHTING.value,
        ]

        for device, data in devices.items():
            if data["deviceInfos"]["deviceCategory"] in supported_categories:
                # Add support for connected HikVision cameras
                if (
                    data["deviceInfos"]["deviceCategory"]
                    == DeviceCatagories.COMMON_DEVICE_CATEGORY.value
                    and not data["deviceInfos"]["hik"]
                ):
                    continue

                if (
                    data["deviceInfos"]["deviceCategory"]
                    == DeviceCatagories.LIGHTING.value
                ):
                    # Create a light bulb object
                    self._light_bulbs[device] = EzvizLightBulb(
                        self, device, data
                    ).status()
                else:
                    # Create camera object
                    self._cameras[device] = EzvizCamera(self, device, data).status()

        return {**self._cameras, **self._light_bulbs}

    def load_cameras(self) -> dict[Any, Any]:
        """Load and return all cameras objects."""

        self.load_devices()
        return self._cameras

    def load_light_bulbs(self) -> dict[Any, Any]:
        """Load light bulbs."""

        self.load_devices()
        return self._light_bulbs

    def get_device_infos(self, serial: str | None = None) -> dict[Any, Any]:
        """Load all devices and build dict per device serial."""

        devices = self._get_page_list()
        result: dict[str, Any] = {}
        _res_id = "NONE"

        for device in devices["deviceInfos"]:
            _serial = device["deviceSerial"]
            _res_id_list = {
                item
                for item in devices.get("CLOUD", {})
                if devices["CLOUD"][item].get("deviceSerial") == _serial
            }
            _res_id = _res_id_list.pop() if len(_res_id_list) else "NONE"

            result[_serial] = {
                "CLOUD": {_res_id: devices.get("CLOUD", {}).get(_res_id, {})},
                "VTM": {_res_id: devices.get("VTM", {}).get(_res_id, {})},
                "P2P": devices.get("P2P", {}).get(_serial, {}),
                "CONNECTION": devices.get("CONNECTION", {}).get(_serial, {}),
                "KMS": devices.get("KMS", {}).get(_serial, {}),
                "STATUS": devices.get("STATUS", {}).get(_serial, {}),
                "TIME_PLAN": devices.get("TIME_PLAN", {}).get(_serial, {}),
                "CHANNEL": {_res_id: devices.get("CHANNEL", {}).get(_res_id, {})},
                "QOS": devices.get("QOS", {}).get(_serial, {}),
                "NODISTURB": devices.get("NODISTURB", {}).get(_serial, {}),
                "FEATURE": devices.get("FEATURE", {}).get(_serial, {}),
                "UPGRADE": devices.get("UPGRADE", {}).get(_serial, {}),
                "FEATURE_INFO": devices.get("FEATURE_INFO", {}).get(_serial, {}),
                "SWITCH": devices.get("SWITCH", {}).get(_serial, {}),
                "CUSTOM_TAG": devices.get("CUSTOM_TAG", {}).get(_serial, {}),
                "VIDEO_QUALITY": {
                    _res_id: devices.get("VIDEO_QUALITY", {}).get(_res_id, {})
                },
                "resourceInfos": [
                    item
                    for item in devices.get("resourceInfos")
                    if item.get("deviceSerial") == _serial
                ],  # Could be more than one
                "WIFI": devices.get("WIFI", {}).get(_serial, {}),
                "deviceInfos": device,
            }
            # Nested keys are still encoded as JSON strings
            result[_serial]["deviceInfos"]["supportExt"] = json.loads(
                result[_serial]["deviceInfos"]["supportExt"]
            )
            convert_to_dict(result[_serial]["STATUS"].get("optionals"))

        if not serial:
            return result

        return result.get(serial, {})

    def ptz_control(
        self, command: str, serial: str, action: str, speed: int = 5
    ) -> Any:
        """PTZ Control by API."""
        if command is None:
            raise PyEzvizError("Trying to call ptzControl without command")
        if action is None:
            raise PyEzvizError("Trying to call ptzControl without action")

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DEVICES
                + serial
                + API_ENDPOINT_PTZCONTROL,
                data={
                    "command": command,
                    "action": action,
                    "channelNo": "1",
                    "speed": speed,
                    "uuid": str(uuid4()),
                    "serial": serial,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        _LOGGER.debug("PTZ Control: %s", json_output)

        return True

    def get_cam_key(
        self, serial: str, smscode: int | None = None, max_retries: int = 0
    ) -> Any:
        """Get Camera encryption key. The key that is set after the camera is added to the account."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_CAM_ENCRYPTKEY,
                data={
                    "checkcode": smscode,
                    "serial": serial,
                    "clientNo": "web_site",
                    "clientType": 3,
                    "netType": "WIFI",
                    "featureCode": FEATURE_CODE,
                    "sessionId": self._token["session_id"],
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.get_cam_key(serial, smscode, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] == "20002":
            raise EzvizAuthVerificationCode(f"MFA code required: Got {json_output})")

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Camera %s encryption key not found, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.get_cam_key(serial, smscode, max_retries + 1)
            raise PyEzvizError(
                f"Could not get camera encryption key: Got {json_output})"
            )

        return json_output["encryptkey"]

    def create_panoramic(self, serial: str, max_retries: int = 0) -> Any:
        """Create panoramic image."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_CREATE_PANORAMIC,
                data={"deviceSerial": serial},
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.create_panoramic(serial, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Create panoramic failed on device %s retrying %s",
                    serial,
                    max_retries,
                )
                return self.create_panoramic(serial, max_retries + 1)
            raise PyEzvizError(
                f"Could not send command to create panoramic photo: Got {json_output})"
            )

        return json_output

    def return_panoramic(self, serial: str, max_retries: int = 0) -> Any:
        """Return panoramic image url list."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_RETURN_PANORAMIC,
                data={"deviceSerial": serial},
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.return_panoramic(serial, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Camera %s busy or unreachable, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.return_panoramic(serial, max_retries + 1)
            raise PyEzvizError(f"Could retrieve panoramic photo: Got {json_output})")

        return json_output

    def ptz_control_coordinates(
        self, serial: str, x_axis: float, y_axis: float
    ) -> bool:
        """PTZ Coordinate Move."""
        if 0 < x_axis > 1:
            raise PyEzvizError(
                f"Invalid X coordinate: {x_axis}: Should be between 0 and 1 inclusive"
            )

        if 0 < y_axis > 1:
            raise PyEzvizError(
                f"Invalid Y coordinate: {y_axis}: Should be between 0 and 1 inclusive"
            )

        try:
            req = self._session.post(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_PANORAMIC_DEVICES_OPERATION,
                data={
                    "x": f"{x_axis:.6f}",
                    "y": f"{y_axis:.6f}",
                    "deviceSerial": serial,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            raise HTTPError from err

        try:
            json_result = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        _LOGGER.debug("PTZ control coordinates: %s", json_result)

        return True

    def login(self, sms_code: int | None = None) -> dict[Any, Any]:
        """Get or refresh ezviz login token."""
        if self._token["session_id"] and self._token["rf_session_id"]:
            try:
                req = self._session.put(
                    "https://"
                    + self._token["api_url"]
                    + API_ENDPOINT_REFRESH_SESSION_ID,
                    data={
                        "refreshSessionId": self._token["rf_session_id"],
                        "featureCode": FEATURE_CODE,
                    },
                    timeout=self._timeout,
                )
                req.raise_for_status()

            except requests.HTTPError as err:
                raise HTTPError from err

            try:
                json_result = req.json()

            except ValueError as err:
                raise PyEzvizError(
                    "Impossible to decode response: "
                    + str(err)
                    + "\nResponse was: "
                    + str(req.text)
                ) from err

            if json_result["meta"]["code"] == 200:
                self._session.headers["sessionId"] = json_result["sessionInfo"][
                    "sessionId"
                ]
                self._token["session_id"] = str(json_result["sessionInfo"]["sessionId"])
                self._token["rf_session_id"] = str(
                    json_result["sessionInfo"]["refreshSessionId"]
                )

                if not self._token.get("service_urls"):
                    self._token["service_urls"] = self.get_service_urls()

                return self._token

            if json_result["meta"]["code"] == 403:
                if self.account and self.password:
                    self._token = {
                        "session_id": None,
                        "rf_session_id": None,
                        "username": None,
                        "api_url": self._token["api_url"],
                    }
                    return self.login()

                raise EzvizAuthTokenExpired(
                    f"Token expired, Login with username and password required: {req.text}"
                )

            raise PyEzvizError(f"Error renewing login token: {json_result['meta']}")

        if self.account and self.password:
            return self._login(sms_code)

        raise PyEzvizError("Login with account and password required")

    def logout(self) -> bool:
        """Close Ezviz session and remove login session from ezviz servers."""
        try:
            req = self._session.delete(
                "https://" + self._token["api_url"] + API_ENDPOINT_LOGOUT,
                timeout=self._timeout,
            )
            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                _LOGGER.warning("Token is no longer valid. Already logged out?")
                return True
            raise HTTPError from err

        try:
            json_result = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        self.close_session()

        return bool(json_result["meta"]["code"] == 200)

    def set_camera_defence_old(self, serial: str, enable: int) -> bool:
        """Enable/Disable motion detection on camera."""
        cas_client = EzvizCAS(self._token)
        cas_client.set_camera_defence_state(serial, enable)

        return True

    def api_set_defence_schedule(
        self, serial: str, schedule: str, enable: int, max_retries: int = 0
    ) -> bool:
        """Set defence schedules."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        schedulestring = (
            '{"CN":0,"EL":'
            + str(enable)
            + ',"SS":"'
            + serial
            + '","WP":['
            + schedule
            + "]}]}"
        )
        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_SET_DEFENCE_SCHEDULE,
                data={
                    "devTimingPlan": schedulestring,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.api_set_defence_schedule(
                    serial, schedule, enable, max_retries + 1
                )

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["resultCode"] != "0":
            if json_output["resultCode"] == "-1":
                _LOGGER.warning(
                    "Camara %s offline or unreachable, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.api_set_defence_schedule(
                    serial, schedule, enable, max_retries + 1
                )
            raise PyEzvizError(f"Could not set the schedule: Got {json_output})")

        return True

    def api_set_defence_mode(self, mode: DefenseModeType, max_retries: int = 0) -> bool:
        """Set defence mode for all devices. The alarm panel from main page is used."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://" + self._token["api_url"] + API_ENDPOINT_SWITCH_DEFENCE_MODE,
                data={
                    "groupId": -1,
                    "mode": mode,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                self.login()
                return self.api_set_defence_mode(mode, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set defence mode: Got {json_output})")

        return True

    def do_not_disturb(
        self,
        serial: str,
        enable: int = 1,
        channelno: int = 1,
        max_retries: int = 0,
    ) -> bool:
        """Set do not disturb on camera with specified serial."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_V3_ALARMS
                + serial
                + "/"
                + channelno
                + API_ENDPOINT_DO_NOT_DISTURB,
                data={"enable": enable, "channelNo": channelno, "deviceSerial": serial},
                timeout=self._timeout,
            )
            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to re-log-in
                self.login()
                return self.do_not_disturb(serial, enable, channelno, max_retries + 1)

            raise HTTPError from err

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError("Could not decode response:" + str(err)) from err

        if json_output["meta"]["code"] != 200:
            raise PyEzvizError(f"Could not set do not disturb: Got {json_output})")

        return True

    def set_floodlight_brightness(
        self,
        serial: str,
        luminance: int = 50,
        channelno: str = "1",
        max_retries: int = 0,
    ) -> bool | str:
        """Set brightness on camera with adjustable light."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if luminance not in range(1, 100):
            raise PyEzvizError(
                "Range of luminance is 1-100, got " + str(luminance) + "."
            )

        try:
            req = self._session.post(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_SET_LUMINANCE
                + "/"
                + serial
                + "/"
                + channelno,
                data={
                    "luminance": luminance,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to re-log-in
                self.login()
                return self.set_floodlight_brightness(
                    serial, luminance, channelno, max_retries + 1
                )

            raise HTTPError from err

        try:
            response_json = req.json()

        except ValueError as err:
            raise PyEzvizError("Could not decode response:" + str(err)) from err

        if response_json["meta"]["code"] != 200:
            raise PyEzvizError(f"Unable to set brightness, got: {response_json}")

        return True

    def set_brightness(
        self,
        serial: str,
        luminance: int = 50,
        channelno: str = "1",
        max_retries: int = 0,
    ) -> bool | str:
        """Facade that changes the brightness to light bulbs or cameras' light."""

        device = self._light_bulbs.get(serial)
        if device:
            # the device is a light bulb
            return self.set_device_feature_by_key(
                serial, device["productId"], luminance, "brightness", max_retries
            )

        # assume the device is a camera
        return self.set_floodlight_brightness(serial, luminance, channelno, max_retries)

    def switch_light_status(
        self,
        serial: str,
        enable: int,
        channel_no: int = 0,
        max_retries: int = 0,
    ) -> bool:
        """Facade that turns on/off light bulbs or cameras' light."""

        device = self._light_bulbs.get(serial)
        if device:
            # the device is a light bulb
            return self.set_device_feature_by_key(
                serial, device["productId"], bool(enable), "light_switch", max_retries
            )

        # assume the device is a camera
        return self.switch_status(
            serial, DeviceSwitchType.ALARM_LIGHT.value, enable, channel_no, max_retries
        )

    def detection_sensibility(
        self,
        serial: str,
        sensibility: int = 3,
        type_value: int = 3,
        max_retries: int = 0,
    ) -> bool | str:
        """Set detection sensibility."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if sensibility not in [0, 1, 2, 3, 4, 5, 6] and type_value == 0:
            raise PyEzvizError(
                "Unproper sensibility for type 0 (should be within 1 to 6)."
            )

        try:
            req = self._session.post(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DETECTION_SENSIBILITY,
                data={
                    "subSerial": serial,
                    "type": type_value,
                    "channelNo": "1",
                    "value": sensibility,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to re-log-in
                self.login()
                return self.detection_sensibility(
                    serial, sensibility, type_value, max_retries + 1
                )

            raise HTTPError from err

        try:
            response_json = req.json()

        except ValueError as err:
            raise PyEzvizError("Could not decode response:" + str(err)) from err

        if response_json["resultCode"] != "0":
            if response_json["resultCode"] == "-1":
                _LOGGER.warning(
                    "Camera %s is offline or unreachable, can't set sensitivity, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.detection_sensibility(
                    serial, sensibility, type_value, max_retries + 1
                )
            raise PyEzvizError(
                f"Unable to set detection sensibility. Got: {response_json}"
            )

        return True

    def get_detection_sensibility(
        self, serial: str, type_value: str = "0", max_retries: int = 0
    ) -> Any:
        """Get detection sensibility notifications."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DETECTION_SENSIBILITY_GET,
                data={
                    "subSerial": serial,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to re-log-in.
                self.login()
                return self.get_detection_sensibility(
                    serial, type_value, max_retries + 1
                )

            raise HTTPError from err

        try:
            response_json = req.json()

        except ValueError as err:
            raise PyEzvizError("Could not decode response:" + str(err)) from err

        if response_json["resultCode"] != "0":
            if response_json["resultCode"] == "-1":
                _LOGGER.warning(
                    "Camera %s is offline or unreachable, retrying %s of %s",
                    serial,
                    max_retries,
                    MAX_RETRIES,
                )
                return self.get_detection_sensibility(
                    serial, type_value, max_retries + 1
                )
            raise PyEzvizError(
                f"Unable to get detection sensibility. Got: {response_json}"
            )

        if response_json["algorithmConfig"]["algorithmList"]:
            for idx in response_json["algorithmConfig"]["algorithmList"]:
                if idx["type"] == type_value:
                    return idx["value"]

        return None

    # soundtype: 0 = normal, 1 = intensive, 2 = disabled ... don't ask me why...
    def alarm_sound(
        self, serial: str, sound_type: int, enable: int = 1, max_retries: int = 0
    ) -> bool:
        """Enable alarm sound by API."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if sound_type not in [0, 1, 2]:
            raise PyEzvizError(
                "Invalid sound_type, should be 0,1,2: " + str(sound_type)
            )

        try:
            req = self._session.put(
                "https://"
                + self._token["api_url"]
                + API_ENDPOINT_DEVICES
                + serial
                + API_ENDPOINT_ALARM_SOUND,
                data={
                    "enable": enable,
                    "soundType": sound_type,
                    "voiceId": "0",
                    "deviceSerial": serial,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to re-log-in
                self.login()
                return self.alarm_sound(serial, sound_type, enable, max_retries + 1)

            raise HTTPError from err

        try:
            response_json = req.json()

        except ValueError as err:
            raise PyEzvizError("Could not decode response:" + str(err)) from err

        _LOGGER.debug("Response: %s", response_json)

        return True

    def _get_page_list(self) -> Any:
        """Get ezviz device info broken down in sections."""
        return self._api_get_pagelist(
            page_filter="CLOUD, TIME_PLAN, CONNECTION, SWITCH,"
            "STATUS, WIFI, NODISTURB, KMS,"
            "P2P, TIME_PLAN, CHANNEL, VTM, DETECTOR,"
            "FEATURE, CUSTOM_TAG, UPGRADE, VIDEO_QUALITY,"
            "QOS, PRODUCTS_INFO, SIM_CARD, MULTI_UPGRADE_EXT,"
            "FEATURE_INFO",
            json_key=None,
        )

    def get_device(self) -> Any:
        """Get ezviz devices filter."""
        return self._api_get_pagelist(page_filter="CLOUD", json_key="deviceInfos")

    def get_connection(self) -> Any:
        """Get ezviz connection infos filter."""
        return self._api_get_pagelist(
            page_filter="CONNECTION", json_key="CONNECTION"
        )

    def _get_status(self) -> Any:
        """Get ezviz status infos filter."""
        return self._api_get_pagelist(page_filter="STATUS", json_key="STATUS")

    def get_switch(self) -> Any:
        """Get ezviz switch infos filter."""
        return self._api_get_pagelist(
            page_filter="SWITCH", json_key="SWITCH"
        )

    def _get_wifi(self) -> Any:
        """Get ezviz wifi infos filter."""
        return self._api_get_pagelist(page_filter="WIFI", json_key="WIFI")

    def _get_nodisturb(self) -> Any:
        """Get ezviz nodisturb infos filter."""
        return self._api_get_pagelist(
            page_filter="NODISTURB", json_key="NODISTURB"
        )

    def _get_p2p(self) -> Any:
        """Get ezviz P2P infos filter."""
        return self._api_get_pagelist(page_filter="P2P", json_key="P2P")

    def _get_kms(self) -> Any:
        """Get ezviz KMS infos filter."""
        return self._api_get_pagelist(page_filter="KMS", json_key="KMS")

    def _get_time_plan(self) -> Any:
        """Get ezviz TIME_PLAN infos filter."""
        return self._api_get_pagelist(page_filter="TIME_PLAN", json_key="TIME_PLAN")

    def close_session(self) -> None:
        """Clear current session."""
        if self._session:
            self._session.close()

        self._session = requests.session()
        self._session.headers.update(REQUEST_HEADER)  # Reset session.
