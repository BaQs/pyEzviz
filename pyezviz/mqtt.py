"""Ezviz cloud MQTT client for push messages."""
from __future__ import annotations

import base64
import json
import logging
import threading
import time
from typing import Any

import paho.mqtt.client as mqtt
import requests

from .api_endpoints import (
    API_ENDPOINT_REGISTER_MQTT,
    API_ENDPOINT_START_MQTT,
    API_ENDPOINT_STOP_MQTT,
)
from .constants import (
    APP_SECRET,
    DEFAULT_TIMEOUT,
    FEATURE_CODE,
    MQTT_APP_KEY,
    REQUEST_HEADER,
)
from .exceptions import HTTPError, InvalidURL, PyEzvizError

_LOGGER = logging.getLogger(__name__)


class MQTTClient(threading.Thread):
    """Open MQTT connection to ezviz cloud."""

    def __init__(
        self,
        token: dict,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the client object."""
        threading.Thread.__init__(self)
        self._session = requests.session()
        self._session.headers.update(REQUEST_HEADER)
        self._token = token or {
            "session_id": None,
            "rf_session_id": None,
            "username": None,
            "api_url": "apiieu.ezvizlife.com",
        }
        self._timeout = timeout
        self._stop_event = threading.Event()
        self._mqtt_data = {
            "mqtt_clientid": None,
            "ticket": None,
            "push_url": token["service_urls"]["pushAddr"],
        }
        self.mqtt_client = None
        self.rcv_message: dict[Any, Any] = {}

    def on_subscribe(
        self, client: Any, userdata: Any, mid: Any, granted_qos: Any
    ) -> None:
        """On MQTT message subscribe."""
        # pylint: disable=unused-argument
        _LOGGER.info("Subscribed: %s %s", mid, granted_qos)

    def on_connect(
        self, client: Any, userdata: Any, flags: Any, return_code: Any
    ) -> None:
        """On MQTT connect."""
        # pylint: disable=unused-argument
        if return_code == 0:
            _LOGGER.info("Connected OK with return code %s", return_code)
        else:
            _LOGGER.info("Connection Error with Return code %s", return_code)
            client.reconnect()

    def on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        """On MQTT message receive."""
        # pylint: disable=unused-argument
        try:
            mqtt_message = json.loads(msg.payload)

        except ValueError as err:
            self.stop()
            raise PyEzvizError(
                "Impossible to decode mqtt message: " + str(err)
            ) from err

        mqtt_message["ext"] = mqtt_message["ext"].split(",")

        # Format payload message and keep latest device message.
        self.rcv_message[mqtt_message["ext"][2]] = {
            "id": mqtt_message["id"],
            "alert": mqtt_message["alert"],
            "time": mqtt_message["ext"][1],
            "alert type": mqtt_message["ext"][4],
            "image": mqtt_message["ext"][16] if len(mqtt_message["ext"]) > 16 else None,
        }

        _LOGGER.debug(self.rcv_message, exc_info=True)

    def _mqtt(self) -> mqtt.Client:
        """Receive MQTT messages from ezviz server."""

        ezviz_mqtt_client = mqtt.Client(
            client_id=self._mqtt_data["mqtt_clientid"], protocol=4, transport="tcp"
        )
        ezviz_mqtt_client.on_connect = self.on_connect
        ezviz_mqtt_client.on_subscribe = self.on_subscribe
        ezviz_mqtt_client.on_message = self.on_message
        ezviz_mqtt_client.username_pw_set(MQTT_APP_KEY, APP_SECRET)

        ezviz_mqtt_client.connect(self._mqtt_data["push_url"], 1882, 60)
        ezviz_mqtt_client.subscribe(
            f"{MQTT_APP_KEY}/ticket/{self._mqtt_data['ticket']}", qos=2
        )

        ezviz_mqtt_client.loop_start()
        return ezviz_mqtt_client

    def _register_ezviz_push(self) -> None:
        """Register for push messages."""

        auth_seq = (
            "Basic "
            + base64.b64encode(f"{MQTT_APP_KEY}:{APP_SECRET}".encode("ascii")).decode()
        )

        payload = {
            "appKey": MQTT_APP_KEY,
            "clientType": "5",
            "mac": FEATURE_CODE,
            "token": "123456",
            "version": "v1.3.0",
        }

        try:
            req = self._session.post(
                f"https://{self._mqtt_data['push_url']}{API_ENDPOINT_REGISTER_MQTT}",
                allow_redirects=False,
                headers={"Authorization": auth_seq},
                data=payload,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occured") from err

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

        self._mqtt_data["mqtt_clientid"] = json_result["data"]["clientId"]

    def run(self) -> None:
        """Start mqtt thread."""

        if self._token.get("username") is None:
            self._stop_event.set()
            raise PyEzvizError(
                "Ezviz internal username is required. Call EzvizClient login without token."
            )

        self._register_ezviz_push()
        self._start_ezviz_push()
        self.mqtt_client = self._mqtt()

    def start(self) -> None:
        """Start mqtt thread as application. Set logging first to see messages."""
        self.run()

        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop push notifications."""

        payload = {
            "appKey": MQTT_APP_KEY,
            "clientId": self._mqtt_data["mqtt_clientid"],
            "clientType": 5,
            "sessionId": self._token["session_id"],
            "username": self._token["username"],
        }

        try:
            req = self._session.post(
                f"https://{self._mqtt_data['push_url']}{API_ENDPOINT_STOP_MQTT}",
                data=payload,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occured") from err

        except requests.HTTPError as err:
            raise HTTPError from err

        finally:
            self._stop_event.set()
            self.mqtt_client.loop_stop()

    def _start_ezviz_push(self) -> None:
        """Send start for push messages to ezviz api."""

        payload = {
            "appKey": MQTT_APP_KEY,
            "clientId": self._mqtt_data["mqtt_clientid"],
            "clientType": 5,
            "sessionId": self._token["session_id"],
            "username": self._token["username"],
            "token": "123456",
        }

        try:
            req = self._session.post(
                f"https://{self._mqtt_data['push_url']}{API_ENDPOINT_START_MQTT}",
                allow_redirects=False,
                data=payload,
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occured") from err

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

        self._mqtt_data["ticket"] = json_result["ticket"]
