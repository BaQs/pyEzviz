"""API endpoints."""

# API Endpoints
API_ENDPOINT_CLOUDDEVICES = "/api/cloud/v2/cloudDevices/getAll"

API_ENDPOINT_LOGIN = "/v3/users/login/v5"
API_ENDPOINT_LOGOUT = "/v3/users/logout/v2"
API_ENDPOINT_REFRESH_SESSION_ID = "/v3/apigateway/login"
API_ENDPOINT_SERVER_INFO = "/v3/configurations/system/info"
API_ENDPOINT_USER_ID = "/v3/userdevices/v1/token"
API_ENDPOINT_GROUP_DEFENCE_MODE = "/v3/userdevices/v1/group/defenceMode"

API_ENDPOINT_PANORAMIC_DEVICES_OPERATION = "/v3/panoramicDevices/operation"
API_ENDPOINT_UPGRADE_DEVICE = "/v3/upgrades/v1/devices/"
API_ENDPOINT_SEND_CODE = "/v3/sms/nologin/checkcode"

API_ENDPOINT_ALARMINFO_GET = "/v3/alarms/v2/advanced"
API_ENDPOINT_UNIFIEDMSG_LIST_GET = "/v3/unifiedmsg/list"
API_ENDPOINT_V3_ALARMS = "/v3/alarms/"
API_ENDPOINT_SET_LUMINANCE = "/v3/alarms/device/alarmLight"

API_ENDPOINT_PAGELIST = "/v3/userdevices/v1/resources/pagelist"
API_ENDPOINT_SWITCH_DEFENCE_MODE = "/v3/userdevices/v1/group/switchDefenceMode"

API_ENDPOINT_DETECTION_SENSIBILITY = "/api/device/configAlgorithm"
API_ENDPOINT_DETECTION_SENSIBILITY_GET = "/api/device/queryAlgorithmConfig"
API_ENDPOINT_SET_DEFENCE_SCHEDULE = "/api/device/defence/plan2"
API_ENDPOINT_CAM_ENCRYPTKEY = "/api/device/query/encryptkey"
API_ENDPOINT_CANCEL_ALARM = "/api/device/cancelAlarm"
API_ENDPOINT_DEVICE_SYS_OPERATION = "/api/device/v2/sysOper/"
API_ENDPOINT_DEVICE_STORAGE_STATUS = "/api/device/queryStorageStatus"
API_ENDPOINT_DEVCONFIG_BY_KEY = "/v3/devconfig/v1/keyValue/"

# Videogo DeviceApi
API_ENDPOINT_DEVICES = "/v3/devices/"
API_ENDPOINT_SWITCH_STATUS = "/switchStatus"
API_ENDPOINT_SWITCH_OTHER = "/switch"
API_ENDPOINT_PTZCONTROL = "/ptzControl"
API_ENDPOINT_ALARM_SOUND = "/alarm/sound"
API_ENDPOINT_SWITCH_SOUND_ALARM = "/sendAlarm"
API_ENDPOINT_DO_NOT_DISTURB = "/nodisturb"
API_ENDPOINT_VIDEO_ENCRYPT = "encryptedInfo/risk"
API_ENDPOINT_CHANGE_DEFENCE_STATUS = "changeDefenceStatusReq"

API_ENDPOINT_CREATE_PANORAMIC = "/api/panoramic/devices/pics/collect"
API_ENDPOINT_RETURN_PANORAMIC = "/api/panoramic/devices/pics"

# MQTT
API_ENDPOINT_REGISTER_MQTT = "/v1/getClientId"
API_ENDPOINT_START_MQTT = "/api/push/start"
API_ENDPOINT_STOP_MQTT = "/api/push/stop"
