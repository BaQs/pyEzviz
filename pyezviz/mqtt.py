"""Ezviz cloud MQTT client for push messages."""

import base64
import json
import logging

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import requests
from pyezviz.client import EzvizClient, HTTPError, InvalidURL, PyEzvizError
from pyezviz.constants import FEATURE_CODE

API_ENDPOINT_SERVER_INFO = "/v3/configurations/system/info"
API_ENDPOINT_REGISTER_MQTT = "/v1/getClientId"
API_ENDPOINT_START_MQTT = "/api/push/start"
API_ENDPOINT_STOP_MQTT = "/api/push/stop"

DEFAULT_TIMEOUT = 25
MAX_RETRIES = 3

MQTT_APP_KEY = "4c6b3cc2-b5eb-4813-a592-612c1374c1fe"
APP_SECRET = "17454517-cc1c-42b3-a845-99b4a15dd3e6"

# hassio or other mqtt broker to receive messages.
STATE_TOPIC = "homeassistant/sensor"


def on_subscribe(client, userdata, mid, granted_qos):
    """On MQTT message subscribe."""
    # pylint: disable=unused-argument
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_connect(client, userdata, flags, return_code):
    """On MQTT connect."""
    # pylint: disable=unused-argument
    if return_code == 0:
        print("connected OK Returned code=", return_code)
    else:
        print("Bad connection Returned code=", return_code)
        client.reconnect()


class MQTTClient:
    """Open MQTT connection to ezviz cloud."""

    def __init__(
        self,
        token,
        broker=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        """Initialize the client object."""
        self._session = None
        self._token = token or {
            "session_id": None,
            "rf_session_id": None,
            "username": None,
        }
        self._timeout = timeout
        self._mqtt_data = {"mqtt_clientid": None, "ticket": None, "push_url": None}
        self._broker = broker or {
            "username": "ezviz",
            "password": "ezviz",
            "broker_ip": "homeassistant",
        }

    def on_message(self, client, userdata, msg):
        """On MQTT message receive."""
        # pylint: disable=unused-argument
        mqtt_message = json.loads(msg.payload)
        mqtt_message["ext"] = mqtt_message["ext"].split(",")

        # Restructure payload message
        new_mqtt_message = {}
        new_mqtt_message["id"] = mqtt_message["id"]
        new_mqtt_message["alert"] = mqtt_message["alert"]
        new_mqtt_message["ezviz_alert_type"] = mqtt_message["ext"][4]
        new_mqtt_message["serial"] = mqtt_message["ext"][2]
        new_mqtt_message["msg_time"] = mqtt_message["ext"][1]
        new_mqtt_message["img_url"] = mqtt_message["ext"][16]
        print(new_mqtt_message)

        if self._broker:
            # Register and update HA sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/state",
                json.dumps(new_mqtt_message),
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

    def _mqtt(self):
        """Receive MQTT messages from ezviz server """

        ezviz_mqtt_client = mqtt.Client(
            client_id=self._mqtt_data["mqtt_clientid"], protocol=4, transport="tcp"
        )
        ezviz_mqtt_client.on_connect = on_connect
        ezviz_mqtt_client.on_subscribe = on_subscribe
        ezviz_mqtt_client.on_message = self.on_message
        ezviz_mqtt_client.username_pw_set(MQTT_APP_KEY, APP_SECRET)

        ezviz_mqtt_client.connect(self._mqtt_data["push_url"], 1882, 60)
        ezviz_mqtt_client.subscribe(
            f"{MQTT_APP_KEY}/ticket/{self._mqtt_data['ticket']}", qos=2
        )

        try:
            ezviz_mqtt_client.loop_forever()
            # ezviz_mqtt_client.loop_start()

        except KeyboardInterrupt as err:
            print(err)

        finally:
            self.stop()

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

        return True

    def start(self):
        """Start."""

        if self._session is None:
            self._session = requests.session()
            self._session.headers.update(
                {"User-Agent": "okhttp/3.12.1"}
            )  # Android generic user agent.

        self._get_service_urls()
        self._register_ezviz_push()
        self._start_ezviz_push()

        return self._mqtt()

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

        return True

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
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                client = EzvizClient(token=self._token)
                self._token = client.login()
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

        return True

    def _get_service_urls(self, max_retries=0):
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.get(
                f"https://{self._token['api_url']}{API_ENDPOINT_SERVER_INFO}",
                headers={
                    "sessionId": self._token["session_id"],
                    "featureCode": FEATURE_CODE,
                },
                timeout=self._timeout,
            )

            req.raise_for_status()

        except requests.ConnectionError as err:
            raise InvalidURL("A Invalid URL or Proxy error occured") from err

        except requests.HTTPError as err:
            if err.response.status_code == 401:
                # session is wrong, need to relogin
                client = EzvizClient(token=self._token)
                self._token = client.login()
                raise HTTPError from err

        if not req.text:
            raise PyEzvizError("No data")

        try:
            json_output = req.json()

        except ValueError as err:
            raise PyEzvizError(
                "Impossible to decode response: "
                + str(err)
                + "\nResponse was: "
                + str(req.text)
            ) from err

        if json_output.get("meta").get("code") != 200:
            logging.info(
                "Json request error, relogging (max retries: %s)", str(max_retries)
            )

        self._mqtt_data["push_url"] = json_output["systemConfigInfo"]["pushAddr"]

        return True
