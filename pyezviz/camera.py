import datetime
import json
from pyezviz.DeviceSwitchType import DeviceSwitchType

class PyEzvizError(Exception):
    pass

class EzvizCamera(object):
    def __init__(self, client, serial):
        """Initialize the camera object."""
        self._client = client
        self._serial = serial
        self._switch = {}
        self._alarmmotiontrigger = {}

    def load(self):
        """Update device info for camera serial"""
        self._device = self._client._get_deviceinfo(self._serial)

        """get last alarm info for this camera's self._serial"""
        self._alarmlist = self._client._get_alarminfo(self._serial)
        if self._alarmlist['totalCount'] == 0:
          self._alarmlist_time = None
          self._alarmlist_pic = None
        else:
          self._alarmlist_time = self._alarmlist['alarmLogs'][0]['alarmOccurTime']
          self._alarmlist_pic = self._alarmlist['alarmLogs'][0]['alarmPicUrl']

        """load device switches"""
        for switch in self._device['deviceSwitchStatuses']:
            self._switch.update({switch['type'] : switch['enable']})

        """load detection sensibility if supported"""
        if self._device['supportExt']['support_sensibility_adjust']:
            if self._switch.get(DeviceSwitchType.AUTO_SLEEP.value) != True:
                self._detection_sensibility = self._client.get_detection_sensibility(self._serial, self._device['supportExt']['support_sensibility_adjust'])
            if self._switch.get(DeviceSwitchType.AUTO_SLEEP.value) == True:
                self._detection_sensibility = "Hibernate"
           
        else:
            self._detection_sensibility = None

        return True

    def motionalarm(self):
        """Create motion sensor based on last alarm time"""
        now = datetime.datetime.now().replace(microsecond = 0)
        AlarmTriggerActive = 0
        today_date = datetime.date.today()

        """Need to handle error if time format different"""
        try:
            fix = datetime.datetime.strptime(self._alarmlist_time.replace("Today", str(today_date)), '%Y-%m-%d %H:%M:%S')
        except:
            fix = datetime.datetime.now().replace(microsecond = 0)

        fix = fix.replace(tzinfo=datetime.timezone.utc).timestamp()
        now = now.replace(tzinfo=datetime.timezone.utc).timestamp()

        # returns a timedelta object 
        timepassed = now-fix
        #timepassed = timepassed.seconds
        
        if timepassed < 60:
            AlarmTriggerActive = 1

        self._alarmmotiontrigger = {'AlarmTriggerActive': AlarmTriggerActive, 'timepassed' : timepassed}

    def status(self):
        """Return the status of the camera."""
        self.load()

        if self._alarmlist_time:
            self.motionalarm()

        return {
            'serial': self._serial,
            'name': self._device['name'],
            'version': self._device['version'],
            'upgrade_available': self._device['upgradeAvailable'],
            'status': self._device['deviceExtStatus']['OnlineStatus'],
            'device_category': self._device['deviceCategory']['link'],
            'device_sub_category': self._device['deviceCategory']['category'],

            'sleep': self._switch.get(DeviceSwitchType.SLEEP.value) or self._switch.get(DeviceSwitchType.AUTO_SLEEP.value),
            'privacy': self._switch.get(DeviceSwitchType.PRIVACY.value),
            'audio': self._switch.get(DeviceSwitchType.SOUND.value),
            'ir_led': self._switch.get(DeviceSwitchType.INFRARED_LIGHT.value),
            'state_led': self._switch.get(DeviceSwitchType.LIGHT.value),
            'follow_move': self._switch.get(DeviceSwitchType.MOBILE_TRACKING.value),

            'alarm_notify': bool(self._device.get('defence')),
            'alarm_schedules_enabled': bool(self._device.get('defencePlanEnable')),
            'alarm_sound_mod': self._device.get('alarmSoundMode'),

            'encrypted': bool(self._device.get('isEncrypted')),

            'local_ip': self._device.get('deviceNetStatus', {}).get('addr',"0.0.0.0"),
            'wan_ip': self._device.get('deviceExtStatus', {}).get('wanIp',"0.0.0.0"),
            'mac': self._device.get('mac'),
            'net_type': self._device.get('deviceNetStatus', {}).get('netType'),
            'wireless_signal': self._device.get('deviceNetStatus', {}).get('signal'),
            'local_rtsp_port': self._device.get('localRtspPort'),
            'supported_channels': self._device.get('supportChannelNums'),

            'detection_sensibility': self._detection_sensibility,
            'battery_level': self._device.get('deviceExtStatus', {}).get('powerRemaining'),
            'PIR_Status': self._device.get('pirStatus'),
            'Motion_Trigger': self._alarmmotiontrigger.get('AlarmTriggerActive'),
            'Seconds_Last_Trigger': self._alarmmotiontrigger.get('timepassed'),
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

    def alarm_detection_sensibility(self, sensibility, type_value=0):
        """Enable/Disable camera sound when movement is detected."""
        # we force enable = 1 , to make sound...
        return self._client.detection_sensibility(self._serial, sensibility, type_value)

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