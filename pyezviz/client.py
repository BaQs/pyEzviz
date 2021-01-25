import json
import requests
import logging
import hashlib
import time
from fake_useragent import UserAgent
# from uuid import uuid4
from .camera import EzvizCamera
# from pyezviz.camera import EzvizCamera

COOKIE_NAME = "sessionId"
CAMERA_DEVICE_CATEGORY = "IPC"
DOORBELL_DEVICE_CATEGORY = "BDoorBell"


EU_API_DOMAIN = "apiieu"
API_BASE_TLD = "ezvizlife.com"
API_BASE_URI = "https://" + EU_API_DOMAIN + "." + API_BASE_TLD
API_ENDPOINT_LOGIN = "/v3/users/login"
API_ENDPOINT_CLOUDDEVICES = "/api/cloud/v2/cloudDevices/getAll"
API_ENDPOINT_PAGELIST = "/v3/userdevices/v1/devices/pagelist"
API_ENDPOINT_DEVICES = "/v3/devices/"
API_ENDPOINT_SWITCH_STATUS = '/api/device/switchStatus'
API_ENDPOINT_PTZCONTROL = "/ptzControl"
API_ENDPOINT_ALARM_SOUND = "/alarm/sound"
API_ENDPOINT_DATA_REPORT = "/api/other/data/report"
API_ENDPOINT_DETECTION_SENSIBILITY = "/api/device/configAlgorithm"
API_ENDPOINT_DETECTION_SENSIBILITY_GET = "/api/device/queryAlgorithmConfig"

LOGIN_URL = API_BASE_URI + API_ENDPOINT_LOGIN
CLOUDDEVICES_URL = API_BASE_URI + API_ENDPOINT_CLOUDDEVICES
DEVICES_URL = API_BASE_URI + API_ENDPOINT_DEVICES
PAGELIST_URL = API_BASE_URI + API_ENDPOINT_PAGELIST
DATA_REPORT_URL = API_BASE_URI + API_ENDPOINT_DATA_REPORT

SWITCH_STATUS_URL = API_BASE_URI + API_ENDPOINT_SWITCH_STATUS
DETECTION_SENSIBILITY_URL = API_BASE_URI + API_ENDPOINT_DETECTION_SENSIBILITY
DETECTION_SENSIBILITY_GET_URL = API_BASE_URI + API_ENDPOINT_DETECTION_SENSIBILITY_GET



DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3




class PyEzvizError(Exception):
    pass


class EzvizClient(object):
    def __init__(self, account, password, session=None, sessionId=None, timeout=None, cloud=None, connection=None):
        """Initialize the client object."""
        self.account = account
        self.password = password
        # self._user_id = None
        # self._user_reference = None
        self._session = session
        self._sessionId = sessionId
        self._data = {}
        self._timeout = timeout
        self._CLOUD = cloud
        self._CONNECTION = connection

    def _login(self, apiDomain=EU_API_DOMAIN):
        """Login to Ezviz' API."""

        # Ezviz API sends md5 of password
        m = hashlib.md5()
        m.update(self.password.encode('utf-8'))
        md5pass = m.hexdigest()
        payload = {"account": self.account, "password": md5pass, "featureCode": "93c579faa0902cbfcfcc4fc004ef67e7"}

        try:
            req = self._session.post("https://" + apiDomain + "." + API_BASE_TLD + API_ENDPOINT_LOGIN,
                                data=payload,
                                headers={"Content-Type": "application/x-www-form-urlencoded",
                                        "clientType": "1",
                                        "customNo": "1000001"},
                                timeout=self._timeout)
        except OSError:
            raise PyEzvizError("Can not login to API")

        if req.status_code == 400:
            raise PyEzvizError("Login error: Please check your username/password: %s ", str(req.text))


        # let's parse the answer, session is in {.."loginSession":{"sessionId":"xxx...}
        try:
            response_json = req.json()

            # if the apidomain is not proper
            if response_json["meta"]["code"] == 1100: 
                return self._login(response_json["loginArea"]["apiDomain"])

            sessionId = str(response_json["loginSession"]["sessionId"])
            if not sessionId:
                raise PyEzvizError("Login error: Please check your username/password: %s ", str(req.text))

            self._sessionId = sessionId

        except (OSError, json.decoder.JSONDecodeError) as e:
            raise PyEzvizError("Impossible to decode response: \nResponse was: [%s] %s", str(e), str(req.status_code), str(req.text))


        return True

    def _get_pagelist(self, filter=None, json_key=None, max_retries=0):
        """Get data from pagelist API."""

        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if filter == None:
            raise PyEzvizError("Trying to call get_pagelist without filter")

        try:
            req = self._session.get(PAGELIST_URL,
                                    params={'filter': filter},
                                    headers={ 'sessionId': self._sessionId},
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to relogin
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self._get_pagelist(max_retries+1)

        if req.text is "":
            raise PyEzvizError("No data")

        try:
            json_output = req.json()
        except (OSError, json.decoder.JSONDecodeError) as e:
            raise PyEzvizError("Impossible to decode response: " + str(e) + "\nResponse was: " + str(req.text))

        if json_key == None:
            json_result = json_output
        else:
            json_result = json_output[json_key]

        if not json_result:
            raise PyEzvizError("Impossible to load the devices, here is the returned response: %s ", str(req.text))

        return json_result

    def _switch_status(self, serial, status_type, enable, max_retries=0):
        """Switch status on a device"""

        try:
            req = self._session.post(SWITCH_STATUS_URL,
                                    data={  'sessionId': self._sessionId, 
                                            'enable': enable,
                                            'serial': serial,
                                            'channel': '0',
                                            'netType' : 'WIFI',
                                            'clientType': '1',
                                            'type': status_type},
                                    timeout=self._timeout)


            if req.status_code == 401:
            # session is wrong, need to relogin
                self.login()
                logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
                return self._switch_status(serial, type, enable, max_retries+1)

            response_json = req.json()
            if response_json['resultCode'] and response_json['resultCode'] != '0':
                raise PyEzvizError("Could not set the switch, maybe a permission issue ?: Got %s : %s)",str(req.status_code), str(req.text))
                return False
        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))

        return True

    def _switch_devices_privacy(self, enable=0):
        """Switch privacy status on ALL devices (batch)"""

        #  enable=1 means privacy is ON

        # get all devices
        devices = self._get_devices()

        # foreach, launch a switchstatus for the proper serial
        for idx, device in enumerate(devices):
            serial = devices[idx]['serial']
            self._switch_status(serial, TYPE_PRIVACY_MODE, enable)

        return True

    def load_cameras(self):
        """Load and return all cameras objects"""

        # get all devices
        devices = self.get_DEVICE()
        cameras = []

        # foreach, launch a switchstatus for the proper serial
        for idx, device in enumerate(devices):
            if devices[idx]['deviceCategory'] == CAMERA_DEVICE_CATEGORY:
                camera = EzvizCamera(self, device['deviceSerial'])
                camera.load()
                cameras.append(camera.status())
            if devices[idx]['deviceCategory'] == DOORBELL_DEVICE_CATEGORY:
                camera = EzvizCamera(self, device['deviceSerial'])
                camera.load()
                cameras.append(camera.status())

        return cameras

    def ptzControl(self, command, serial, action, speed=5, max_retries=0):
        """PTZ Control by API."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if command == None:
            raise PyEzvizError("Trying to call ptzControl without command")
        if action == None:
            raise PyEzvizError("Trying to call ptzControl without action")


        try:
            req = self._session.put(DEVICES_URL + serial + API_ENDPOINT_PTZCONTROL,
                                    data={'command': command,
                                        'action': action,
                                        'channelNo': "1",
                                        'speed': speed,
                                        # 'uuid': str(uuid4()),
                                        'serial': serial},
                                    headers={ 'sessionId': self._sessionId,
                                    'clientType': "1"},
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to re-log-in
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self.ptzControl(max_retries+1)

    def login(self):
        """Set http session."""
        if self._sessionId is None:
            self._session = requests.session()
            # adding fake user-agent header
            self._session.headers.update({'User-agent': str(UserAgent().random)})

        return self._login()

    def data_report(self, serial, enable=1, max_retries=0):
        """Enable alarm notifications."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        # operationType = 2 if disable, and 1 if enable
        operationType = 2 - int(enable)
        print(f"enable: {enable}, operationType: {operationType}")

        try:
            req = self._session.post(DATA_REPORT_URL,
                                    data={  'clientType': '1',
                                            'infoDetail': json.dumps({
                                                "operationType" : int(operationType),
                                                "detail" : '0',
                                                "deviceSerial" : serial + ",2"
                                                }, separators=(',',':')),
                                            'infoType': '3',
                                            'netType': 'WIFI',
                                            'reportData': None,
                                            'requestType': '0',
                                            'sessionId': self._sessionId
                                    },
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to re-log-in
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self.data_report(serial, enable, max_retries+1)
        
        return True
    # soundtype: 0 = normal, 1 = intensive, 2 = disabled ... don't ask me why...

    def detection_sensibility(self, serial, sensibility=3, max_retries=0):
        """Enable alarm notifications."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if sensibility not in [0,1,2,3,4,5,6]:
            raise PyEzvizError("Unproper sensibility (should be within 1 to 6).")

        try:
            req = self._session.post(DETECTION_SENSIBILITY_URL,
                                    data={  'subSerial' : serial,
                                            'type': '0',
                                            'sessionId': self._sessionId,
                                            'value': sensibility,
                                    },
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to re-log-in
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self.detection_sensibility(serial, enable, max_retries+1)
        
        return True

    def get_detection_sensibility(self, serial, max_retries=0):
        """Enable alarm notifications."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        try:
            req = self._session.post(DETECTION_SENSIBILITY_GET_URL,
                                    data={  'subSerial' : serial,
                                            'sessionId': self._sessionId,
                                            'clientType': 1
                                    },
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to re-log-in
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self.get_detection_sensibility(serial, enable, max_retries+1)
        # elif req.status_code != 200:
        #     raise PyEzvizError("Could not get detection sensibility: Got %s : %s)",str(req.status_code), str(req.text))

        response_json = req.json()
        if response_json['resultCode'] and response_json['resultCode'] != '0':
            # raise PyEzvizError("Could not get detection sensibility: Got %s : %s)",str(req.status_code), str(req.text))
            return 'Unknown'
        else:
            return response_json['algorithmConfig']['algorithmList'][0]['value']

    def alarm_sound(self, serial, soundType, enable=1, max_retries=0):
        """Enable alarm sound by API."""
        if max_retries > MAX_RETRIES:
            raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

        if soundType not in [0,1,2]:
            raise PyEzvizError("Invalid soundType, should be 0,1,2: " + str(soundType))

        try:
            req = self._session.put(DEVICES_URL + serial + API_ENDPOINT_ALARM_SOUND,
                                    data={  'enable': enable,
                                            'soundType': soundType,
                                            'voiceId': '0',
                                            'deviceSerial': serial
                                    },
                                    headers={ 'sessionId': self._sessionId},
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
        if req.status_code == 401:
        # session is wrong, need to re-log-in
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self.alarm_sound(serial, enable, soundType, max_retries+1)
        elif req.status_code != 200:
            logging.error("Got %s : %s)",str(req.status_code), str(req.text))

        return True

    def switch_devices_privacy(self,enable=0):
        """Switch status on all devices."""
        return self._switch_devices_privacy(enable)

    def switch_status(self, serial, status_type, enable=0):
        """Switch status of a device."""
        return self._switch_status(serial, status_type, enable)

    def get_PAGE_LIST(self, max_retries=0):
        return self._get_pagelist(filter='CLOUD,TIME_PLAN,CONNECTION,SWITCH,STATUS,WIFI,STATUS_EXT,NODISTURB,P2P,TTS,KMS,HIDDNS', json_key=None)

    def get_DEVICE(self, max_retries=0):
        return self._get_pagelist(filter='CLOUD',json_key='deviceInfos')

    def get_CONNECTION(self, max_retries=0):
        return self._get_pagelist(filter='CONNECTION',json_key='connectionInfos')

    def get_STATUS(self, max_retries=0):
        return self._get_pagelist(filter='STATUS',json_key='statusInfos')

    def get_SWITCH(self, max_retries=0):
        return self._get_pagelist(filter='SWITCH',json_key='switchStatusInfos')

    def get_WIFI(self, max_retries=0):
        return self._get_pagelist(filter='WIFI',json_key='wifiInfos')

    def get_NODISTURB(self, max_retries=0):
        return self._get_pagelist(filter='NODISTURB',json_key='alarmNodisturbInfos')

    def get_P2P(self, max_retries=0):
        return self._get_pagelist(filter='P2P',json_key='p2pInfos')

    def get_KMS(self, max_retries=0):
        return self._get_pagelist(filter='KMS',json_key='kmsInfos')

    def get_TIME_PLAN(self, max_retries=0):
        return self._get_pagelist(filter='TIME_PLAN',json_key='timePlanInfos')

    def close_session(self):
        """Close current session."""
        self._session.close()
        self._session = None