import json
import requests
import logging
import hashlib
from fake_useragent import UserAgent


COOKIE_NAME = "sessionId"
API_BASE_URI = "https://apiieu.ezvizlife.com"
API_ENDPOINT_LOGIN = "/v3/users/login"
API_ENDPOINT_DEVICES = "/api/cloud/v2/cloudDevices/getAll"
API_ENDPOINT_PAGELIST = "/v3/userdevices/v1/devices/pagelist"
API_ENDPOINT_SWITCH_STATUS = '/api/device/switchStatus'

LOGIN_URL = API_BASE_URI + API_ENDPOINT_LOGIN
DEVICES_URL = API_BASE_URI + API_ENDPOINT_DEVICES
PAGELIST_URL = API_BASE_URI + API_ENDPOINT_PAGELIST
SWITCH_STATUS_URL = API_BASE_URI + API_ENDPOINT_SWITCH_STATUS

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3

# seems to be some internal reference. 21 = sleep mode
PRIVACY_MODE_TYPE = 21
PRIVACY_MODE_CHANNEL = 0

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

    def login(self):
        """Set http session."""
        if self._sessionId is None:
            self._session = requests.session()
            # adding fake user-agent header
            self._session.headers.update({'User-agent': str(UserAgent().random)})

        return self._login()

    def _login(self):
        """Login to Ezviz' API."""

        # Ezviz API sends md5 of password
        m = hashlib.md5()
        m.update(self.password.encode('utf-8'))
        md5pass = m.hexdigest()
        payload = {"account": self.account, "password": md5pass, "featureCode": "92c579faa0902cbfcfcc4fc004ef67e7"}

        try:
            req = self._session.post(LOGIN_URL,
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
            sessionId = str(response_json["loginSession"]["sessionId"])
            if not sessionId:
                raise PyEzvizError("Login error: Please check your username/password: %s ", str(req.text))
            self._sessionId = sessionId

        except (OSError, json.decoder.JSONDecodeError) as e:
            raise PyEzvizError("Impossible to decode response: \nResponse was: [%s] %s", str(e), str(req.status_code), str(req.text))

        # print(f"session: {sessionId}")

        return True

    # def _get_devices(self, max_retries=0):
    #     """Get devices infos."""

    #     if max_retries > MAX_RETRIES:
    #         raise PyEzvizError("Can't gather proper data. Max retries exceeded.")

    #     try:
    #         req = self._session.post(DEVICES_URL,
    #                                 data={ 'sessionId': self._sessionId, 'enable': '1'},
    #                                 timeout=self._timeout)

    #     except OSError as e:
    #         raise PyEzvizError("Could not access Ezviz' API: " + str(e))
            
    #     if req.status_code == 401:
    #     # session is wrong, need to relogin
    #         self.login()
    #         logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
    #         return self._get_devices(max_retries+1)

    #     if req.text is "":
    #         raise PyEzvizError("No data")

    #     try:
    #         json_output = req.json()
    #     except (OSError, json.decoder.JSONDecodeError) as e:
    #         raise PyEzvizError("Impossible to decode response: " + str(e) + "\nResponse was: " + str(req.text))

    #     cloudDevices = json_output["cloudDevices"]
    #     if not cloudDevices:
    #         raise PyEzvizError("Impossible to load the devices, here is the returned response: %s ", str(req.text))

    #     return cloudDevices


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
            return self._get_devices(max_retries+1)

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

    def _switch_device(self, serial, enable=0, max_retries=0):
        """Switch privacy status on a device"""

        try:
            req = self._session.post(SWITCH_STATUS_URL,
                                    data={  'sessionId': self._sessionId, 
                                            'enable': enable,
                                            'serial': serial,
                                            'type': PRIVACY_MODE_TYPE,
                                            'channel': PRIVACY_MODE_CHANNEL},
                                    timeout=self._timeout)

        except OSError as e:
            raise PyEzvizError("Could not access Ezviz' API: " + str(e))

        if req.status_code == 401:
        # session is wrong, need to relogin
            self.login()
            logging.info("Got 401, relogging (max retries: %s)",str(max_retries))
            return self._switch_device(serial, max_retries+1)

        return True

    def _switch_devices(self, enable=0):
        """Switch privacy status on all devices"""

        #  enable=1 means privacy is ON

        # get all devices
        devices = self._get_devices()

        # foreach, launch a switchstatus for the proper serial
        for idx, device in enumerate(devices):
            serial = devices[idx]['serial']
            self._switch_device(serial, enable)

        return True



    def get_devices(self):
        """Get current data."""
        return self._get_devices()

    def switch_devices(self,enable=0):
        """Switch status on all devices."""
        return self._switch_devices(enable)

    def get_DEVICE(self, max_retries=0):
        return self._get_pagelist(filter='CLOUD',json_key='deviceInfos')

    def get_CONNECTION(self, max_retries=0):
        return self._get_pagelist(filter='CONNECTION',json_key='connectionInfos')

    def get_STATUS(self, max_retries=0):
        return self._get_pagelist(filter='STATUS',json_key='statusInfos')


    def close_session(self):
        """Close current session."""
        self._session.close()
        self._session = None

