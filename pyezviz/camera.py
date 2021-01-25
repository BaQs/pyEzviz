import time
import pyezviz.DeviceSwitchType
from pyezviz.DeviceSwitchType import DeviceSwitchType

KEY_ALARM_NOTIFICATION = 'globalStatus'

ALARM_SOUND_MODE= { 0 : 'Software',
                    1 : 'Intensive',
                    2 : 'Disabled',
}

class PyEzvizError(Exception):
    pass

class EzvizCamera(object):
    def __init__(self, client, serial):
        """Initialize the camera object."""
        self._serial = serial
        self._client = client
        
    def load(self):
        """Load object properties"""
        page_list = self._client.get_PAGE_LIST()

        # we need to know the index of this camera's self._serial  
        for device in page_list['deviceInfos']:
            if device['deviceSerial'] == self._serial :
                self._device = device
                break

        for camera in page_list['cameraInfos']:
            if camera['deviceSerial'] == self._serial :
                self._camera_infos = camera
                break

        # global status
        self._status = page_list['statusInfos'][self._serial]

        # load connection infos
        self._connection = page_list['connectionInfos'][self._serial]

        # # load switches
        switches = {}
        for switch in  page_list['switchStatusInfos'][self._serial]:
            switches[switch['type']] = switch

        self._switch = switches

        # load detection sensibility
        self._detection_sensibility = self._client.get_detection_sensibility(self._serial)

        return True


    def status(self):
        """Return the status of the camera."""
        self.load()

        return {
            'serial': self._serial,
            'name': self._device['name'],
            'status': self._device['status'],
            'device_sub_category': self._device['deviceSubCategory'],

            'privacy': self._switch.get(DeviceSwitchType.SLEEP, {'enable': False})['enable'],
            'audio': self._switch.get(DeviceSwitchType.SOUND, {'enable': False})['enable'],
            'ir_led': self._switch.get(DeviceSwitchType.INFRARED_LIGHT, {'enable': False})['enable'],
            'state_led': self._switch.get(DeviceSwitchType.LIGHT, {'enable': False})['enable'],
            'follow_move': self._switch.get(DeviceSwitchType.MOBILE_TRACKING, {'enable': False})['enable'],
            

            'alarm_notify': bool(self._status[KEY_ALARM_NOTIFICATION]),
            'alarm_sound_mod': ALARM_SOUND_MODE[int(self._status['alarmSoundMode'])],

            'encrypted': bool(self._status['isEncrypt']),

            'local_ip': self._connection['localIp'],
            'local_rtsp_port': self._connection['localRtspPort'],

            'detection_sensibility': self._detection_sensibility,
        }


    def move(self, direction, speed=5):
        """Moves the camera."""
        if direction not in ['right','left','down','up']:
            raise PyEzvizError("Invalid direction: %s ", command)

        # launch the start command
        self._client.ptzControl(str(direction).upper(), self._serial, 'START', speed)
        # launch the stop command
        self._client.ptzControl(str(direction).upper(), self._serial, 'STOP', speed)

        return True

    def alarm_notify(self, enable):
        """Enable/Disable camera notification when movement is detected."""
        return self._client.data_report(self._serial, enable)

    def alarm_sound(self, sound_type):
        """Enable/Disable camera sound when movement is detected."""
        # we force enable = 1 , to make sound...
        return self._client.alarm_sound(self._serial, sound_type, 1)

    def alarm_detection_sensibility(self, sensibility):
        """Enable/Disable camera sound when movement is detected."""
        # we force enable = 1 , to make sound...
        return self._client.detection_sensibility(self._serial, sensibility)

    def switch_device_audio(self, enable=0):
        """Switch audio status on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.SOUND, enable)

    def switch_device_state_led(self, enable=0):
        """Switch audio status on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.LIGHT, enable)

    def switch_device_ir_led(self, enable=0):
        """Switch audio status on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.INFRARED_LIGHT, enable)

    def switch_privacy_mode(self, enable=0):
        """Switch privacy mode on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.SLEEP, enable)

    def switch_follow_move(self, enable=0):
        """Switch follow move."""
        return self._client.switch_status(self._serial, DeviceSwitchType.MOBILE_TRACKING, enable)
        