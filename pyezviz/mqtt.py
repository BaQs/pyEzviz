"""Ezviz cloud MQTT client for push messages."""

import base64
import json
import threading
import time

import paho.mqtt.client as mqtt
import requests

from .constants import DEFAULT_TIMEOUT, FEATURE_CODE
from .exceptions import HTTPError, InvalidURL, PyEzvizError

API_ENDPOINT_SERVER_INFO = "/v3/configurations/system/info"
API_ENDPOINT_REGISTER_MQTT = "/v1/getClientId"
API_ENDPOINT_START_MQTT = "/api/push/start"
API_ENDPOINT_STOP_MQTT = "/api/push/stop"


MQTT_APP_KEY = "4c6b3cc2-b5eb-4813-a592-612c1374c1fe"
APP_SECRET = "17454517-cc1c-42b3-a845-99b4a15dd3e6"


class MQTTClient(threading.Thread):
    """Open MQTT connection to ezviz cloud."""

    def __init__(
        self,
        token,
        timeout=DEFAULT_TIMEOUT,
    ):
        """Initialize the client object."""
        threading.Thread.__init__(self)
        self._session = None
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

    def on_subscribe(self, client, userdata, mid, granted_qos):
        """On MQTT message subscribe."""
        # pylint: disable=unused-argument
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def on_connect(self, client, userdata, flags, return_code):
        """On MQTT connect."""
        # pylint: disable=unused-argument
        if return_code == 0:
            print("connected OK Returned code=", return_code)
        else:
            print("Bad connection Returned code=", return_code)
            client.reconnect()

    def on_message(self, client, userdata, msg):
        """On MQTT message receive."""
        # pylint: disable=unused-argument
        mqtt_message = json.loads(msg.payload)
        mqtt_message["ext"] = mqtt_message["ext"].split(",")

        # Print payload message
        decoded_message = {
            mqtt_message["ext"][2]: {
                "id": mqtt_message["id"],
                "alert": mqtt_message["alert"],
                "time": mqtt_message["ext"][1],
                "alert type": mqtt_message["ext"][4],
                "image": mqtt_message["ext"][16]
                if len(mqtt_message["ext"]) > 16
                else None,
            }
        }
        print(decoded_message)

    def _mqtt(self):
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

    def _register_ezviz_push(self):
        """Register for push messages."""

        auth_seq = base64.b64encode(f"{MQTT_APP_KEY}:{APP_SECRET}".encode("ascii"))
        auth_seq = "Basic " + auth_seq.decode()

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

    def run(self):
        """Represent the thread's activity, should not be used directly."""

        if self._session is None:
            self._session = requests.session()
            self._session.headers.update(
                {"User-Agent": "okhttp/3.12.1"}
            )  # Android generic user agent.

        self._register_ezviz_push()
        self._start_ezviz_push()
        self._mqtt()

        try:
            while not self._stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def start(self):
        """Start mqtt thread."""
        super().start()

    def stop(self):
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

        self._stop_event.set()

    def _start_ezviz_push(self):
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
