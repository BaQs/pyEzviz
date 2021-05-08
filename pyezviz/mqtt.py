"""Ezviz cloud MQTT client for push messages."""

import base64
import json

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import requests
from pyezviz.constants import DEFAULT_TIMEOUT, FEATURE_CODE
from pyezviz.exceptions import HTTPError, InvalidURL, PyEzvizError

API_ENDPOINT_SERVER_INFO = "/v3/configurations/system/info"
API_ENDPOINT_REGISTER_MQTT = "/v1/getClientId"
API_ENDPOINT_START_MQTT = "/api/push/start"
API_ENDPOINT_STOP_MQTT = "/api/push/stop"


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
            "api_url": "apiieu.ezvizlife.com",
        }
        self._timeout = timeout
        self._mqtt_data = {
            "mqtt_clientid": None,
            "ticket": None,
            "push_url": token["service_urls"]["pushAddr"],
        }
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
        new_mqtt_message["name"] = mqtt_message["ext"][17]
        print(new_mqtt_message)

        if self._broker:
            # Register HA alert sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/alert/config",
                json.dumps(
                    {
                        "name": "alert",
                        "device": {
                            "name": f"{new_mqtt_message['name']}",
                            "mf": "Ezviz",
                            "ids": f"(ezviz, {new_mqtt_message['serial']})",
                        },
                        "state_topic": f"{STATE_TOPIC}/{new_mqtt_message['serial']}/alert/state",
                        "platform": "mqtt",
                    }
                ),
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Register HA alert_type sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/ezviz_alert_type/config",
                json.dumps(
                    {
                        "name": "ezviz_alert_type",
                        "device": {
                            "name": f"{new_mqtt_message['name']}",
                            "mf": "Ezviz",
                            "ids": f"(ezviz, {new_mqtt_message['serial']})",
                        },
                        "state_topic": f"{STATE_TOPIC}/{new_mqtt_message['serial']}/ezviz_alert_type/state",
                        "platform": "mqtt",
                    }
                ),
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Register HA msg_time sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/msg_time/config",
                json.dumps(
                    {
                        "name": "msg_time",
                        "device": {
                            "name": f"{new_mqtt_message['name']}",
                            "mf": "Ezviz",
                            "ids": "(ezviz, {new_mqtt_message['serial']})",
                        },
                        "state_topic": f"{STATE_TOPIC}/{new_mqtt_message['serial']}/msg_time/state",
                        "platform": "mqtt",
                    }
                ),
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Register HA img_url sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/img_url/config",
                json.dumps(
                    {
                        "name": "img_url",
                        "device": {
                            "name": f"{new_mqtt_message['name']}",
                            "mf": "Ezviz",
                            "ids": f"(ezviz, {new_mqtt_message['serial']})",
                        },
                        "state_topic": f"{STATE_TOPIC}/{new_mqtt_message['serial']}/img_url/state",
                        "platform": "mqtt",
                    }
                ),
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Update HA Alert sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/alert/state",
                f"{new_mqtt_message['alert']}",
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Update HA ezviz_alert_type sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/ezviz_alert_type/state",
                f"{new_mqtt_message['ezviz_alert_type']}",
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Update HA msg_time sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/msg_time/state",
                f"{new_mqtt_message['msg_time']}",
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

            # Update HA img_url sensor
            publish.single(
                f"{STATE_TOPIC}/{new_mqtt_message['serial']}/img_url/state",
                f"{new_mqtt_message['img_url']}",
                hostname=self._broker["broker_ip"],
                auth={
                    "username": self._broker["username"],
                    "password": self._broker["password"],
                },
            )

    def _mqtt(self):
        """Receive MQTT messages from ezviz server"""

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
