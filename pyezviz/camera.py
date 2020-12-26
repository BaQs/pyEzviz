import time
import pyezviz.DeviceSwitchType
from pyezviz.DeviceSwitchType import DeviceSwitchType

class PyEzvizError(Exception):
    pass

class EzvizCamera(object):
    def __init__(self, client, serial):
        """Initialize the camera object."""
        self._client = client
        self._serial = serial

    def load(self):

        # Update device info for camera serial  
        self._device = self._client._get_deviceinfo(self._serial)

        # get last alarm info for this camera's self._serial
        self._alarmlist = self._client._get_alarminfo(self._serial)
        if self._alarmlist['totalCount'] == 0:
          self._alarmlist_time = None
          self._alarmlist_pic = None
        else:
          self._alarmlist_time = self._alarmlist['alarmLogs'][0]['alarmOccurTime']
          self._alarmlist_pic = self._alarmlist['alarmLogs'][0]['alarmPicUrl']

        # load detection sensibility
        if self._device['deviceCategory']['link'] != "COMMON" and not "BatteryCamera":
            self._detection_sensibility = self._client.get_detection_sensibility(self._serial)
        else:
            self._detection_sensibility = None

        return True

    # load battery camera battery level
    def get_camera_battery (self):
        if self._device['deviceCategory']['link'] == "BatteryCamera":
            return self._device['deviceExtStatus']['powerRemaining']

    # load device switches
    def get_switch(self, switch_type):
        for SwitchName in self._device['deviceSwitchStatuses']:
            if switch_type.value == SwitchName['type']:
                return SwitchName['enable']

    def status(self):
        """Return the status of the camera."""
        self.load()

        return {
            'serial': self._serial,
            'name': self._device['name'],
            'status': self._device['status'],
            'device_sub_category': self._device['deviceCategory']['category'],

            'sleep': self.get_switch(DeviceSwitchType.SLEEP),
            'privacy': self.get_switch(DeviceSwitchType.PRIVACY),
            'audio': self.get_switch(DeviceSwitchType.SOUND),
            'ir_led': self.get_switch(DeviceSwitchType.INFRARED_LIGHT),
            'state_led': self.get_switch(DeviceSwitchType.LIGHT),
            'follow_move': self.get_switch(DeviceSwitchType.MOBILE_TRACKING),

            'alarm_notify': bool(self._device['defence']),
            'alarm_schedules_enabled': bool(self._device['defencePlanEnable']),
            'alarm_sound_mod': self._device['alarmSoundMode'],

            'encrypted': bool(self._device['isEncrypted']),

            'local_ip': self._device['localIp'],
            'local_rtsp_port': self._device['localRtspPort'],

            'detection_sensibility': self._detection_sensibility,
            'battery_level': self.get_camera_battery(),
            'PIR_Status': self._device['pirStatus'],
            'last_alarm_time': self._alarmlist_time,
            'last_alarm_pic': self._alarmlist_pic,
        }


    def move(self, direction, speed=5):
        """Moves the camera."""
        if direction not in ['right','left','down','up']:
            raise PyEzvizError("Invalid direction: %s ", direction)

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
        return self._client.switch_status(self._serial, DeviceSwitchType.SOUND.value, enable)

    def switch_device_state_led(self, enable=0):
        """Switch led status on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.LIGHT.value, enable)

    def switch_device_ir_led(self, enable=0):
        """Switch ir status on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.INFRARED_LIGHT.value, enable)

    def switch_privacy_mode(self, enable=0):
        """Switch privacy mode on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.PRIVACY.value, enable)

    def switch_sleep_mode(self, enable=0):
        """Switch sleep mode on a device."""
        return self._client.switch_status(self._serial, DeviceSwitchType.SLEEP.value, enable)

    def switch_follow_move(self, enable=0):
        """Switch follow move."""
        return self._client.switch_status(self._serial, DeviceSwitchType.MOBILE_TRACKING.value, enable)

    def change_defence_schedule(self, schedule, enable=0):
        """Change defence schedule. Requires json formatted schedules"""
        return self._client.api_set_defence_schdule(self._serial, schedule, enable)

        return None