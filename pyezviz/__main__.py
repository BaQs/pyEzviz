"""pyezviz command line."""
import argparse
import json
import logging
import sys
from typing import Any

import pandas as pd

from .camera import EzvizCamera
from .client import EzvizClient, EzvizSessionManager
from .constants import BatteryCameraWorkMode, DefenseModeType
from .exceptions import EzvizAuthVerificationCode
from .light_bulb import EzvizLightBulb
from .mqtt import MQTTClient


def main() -> Any:
    """Initiate arg parser."""
    parser = argparse.ArgumentParser(prog="pyezviz")
    parser.add_argument("-u", "--username", required=True, help="Ezviz username")
    parser.add_argument("-p", "--password", required=True, help="Ezviz Password")
    parser.add_argument(
        "-r",
        "--region",
        required=False,
        default="apiieu.ezvizlife.com",
        help="Ezviz API region",
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Print debug messages to stderr"
    )
    parser.add_argument(
        "--force-login",
        action="store_true",
        help="Force new login ignoring stored session"
    )
    parser.add_argument(
        "--config-dir",
        required=False,
        help="Custom directory for storing the configuration file",
    )

    subparsers = parser.add_subparsers(dest="action")

    parser_device = subparsers.add_parser(
        "devices", help="Play with all devices at once"
    )
    parser_device.add_argument(
        "device_action",
        type=str,
        default="status",
        help="Device action to perform",
        choices=["device", "status", "switch", "connection"],
    )

    parser_device_lights = subparsers.add_parser(
        "devices_light", help="Get all the light bulbs"
    )
    parser_device_lights.add_argument(
        "devices_light_action",
        type=str,
        default="status",
        help="Light bulbs action to perform",
        choices=["status"]
    )

    parser_light = subparsers.add_parser("light", help="Light actions")
    parser_light.add_argument("--serial", required=True, help="light bulb SERIAL")

    subparsers_light = parser_light.add_subparsers(dest="light_action")
    subparsers_light.add_parser("toggle", help="Toggle the light bulb")
    subparsers_light.add_parser("status", help="Get information about the light bulb")

    parser_home_defence_mode = subparsers.add_parser(
        "home_defence_mode", help="Set home defence mode"
    )

    subparsers.add_parser("mqtt", help="Connect to mqtt push notifications")

    parser_home_defence_mode.add_argument(
        "--mode", required=False, help="Choose mode", choices=["HOME_MODE", "AWAY_MODE"]
    )

    parser_camera = subparsers.add_parser("camera", help="Camera actions")
    parser_camera.add_argument("--serial", required=True, help="camera SERIAL")

    subparsers_camera = parser_camera.add_subparsers(dest="camera_action")

    subparsers_camera.add_parser("status", help="Get the status of the camera")
    parser_camera_move = subparsers_camera.add_parser("move", help="Move the camera")
    parser_camera_move.add_argument(
        "--direction",
        required=True,
        help="Direction to move the camera to",
        choices=["up", "down", "right", "left"],
    )
    parser_camera_move.add_argument(
        "--speed",
        required=False,
        help="Speed of the movement",
        default=5,
        type=int,
        choices=range(1, 10),
    )

    parser_camera_move_coords = subparsers_camera.add_parser(
        "move_coords", help="Move the camera to the X,Y coordinates"
    )
    parser_camera_move_coords.add_argument(
        "--x",
        required=True,
        help="The X coordinate to move the camera to",
        type=float,
    )
    parser_camera_move_coords.add_argument(
        "--y",
        required=True,
        help="The Y coordinate to move the camera to",
        type=float,
    )

    parser_camera_switch = subparsers_camera.add_parser(
        "switch", help="Change the status of a switch"
    )
    parser_camera_switch.add_argument(
        "--switch",
        required=True,
        help="Switch to switch",
        choices=[
            "audio",
            "ir",
            "state",
            "privacy",
            "sleep",
            "follow_move",
            "sound_alarm",
        ],
    )
    parser_camera_switch.add_argument(
        "--enable",
        required=False,
        help="Enable (or not)",
        default=1,
        type=int,
        choices=[0, 1],
    )

    parser_camera_alarm = subparsers_camera.add_parser(
        "alarm", help="Configure the camera alarm"
    )
    parser_camera_alarm.add_argument(
        "--notify", required=False, help="Enable (or not)", type=int, choices=[0, 1]
    )
    parser_camera_alarm.add_argument(
        "--sound",
        required=False,
        help="Sound level (2 is silent, 1 intensive, 0 soft)",
        type=int,
        choices=[0, 1, 2],
    )
    parser_camera_alarm.add_argument(
        "--sensibility",
        required=False,
        help="Sensibility level (Non-Cameras = from 1 to 6) or (Cameras = 1 to 100)",
        type=int,
        choices=range(100),
    )
    parser_camera_alarm.add_argument(
        "--do_not_disturb",
        required=False,
        help="\
If alarm notifications are enabled in the EZViz app then movement normally causes a notification to be sent. \
Enabling this feature stops these notifications, i.e. you are not to be disturbed even if movement occurs. \
Care must be taken because do-not-disturb can not be reset using the mobile app. \
No new notifications will be sent until do-not-disturb is disabled. \
Movement is still recorded even if do-not-disturb is enabled.",
        default=None,
        type=int,
        choices=[0, 1],
    )
    parser_camera_alarm.add_argument(
        "--schedule", required=False, help="Schedule in json format *test*", type=str
    )

    parser_camera_select = subparsers_camera.add_parser(
        "select", help="Change the value of a multi-value option (for on/off value, see 'switch' command)"
    )

    parser_camera_select.add_argument(
        "--battery_work_mode",
        required=False,
        help="Change the work mode for battery powered camera",
        choices=[mode.name for mode in BatteryCameraWorkMode if mode is not BatteryCameraWorkMode.UNKNOWN],
    )

    args = parser.parse_args()
    session_manager = EzvizSessionManager(config_dir=args.config_dir)

    if args.force_login:
        session_manager.save_session({})

    # print("--------------args")
    # print("--------------args: %s",args)
    # print("--------------args")

    client = EzvizClient(
        account=args.username,
        password=args.password,
        api_url=args.region,
        session_manager=session_manager
    )
    try:
        client.start()
    except EzvizAuthVerificationCode:
        mfa_code = input("MFA code required, please input MFA code.\n")
        client._login(smscode=mfa_code)
    except Exception as exp:  # pylint: disable=broad-except
        print(f"Error: {exp}")
        session_manager.save_session({})
        return 1

    if args.debug:
        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if args.action == "devices":

        if args.device_action == "device":
            try:
                print(json.dumps(client.get_device(), indent=2))
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "status":
            try:
                print(
                    pd.DataFrame.from_dict(
                        data=client.load_cameras(),
                        orient="index",
                        columns=[
                            "name",
                            # version,
                            # upgrade_available,
                            "status",
                            "device_category",
                            "device_sub_category",
                            "sleep",
                            "privacy",
                            "audio",
                            "ir_led",
                            "state_led",
                            # follow_move,
                            # alarm_notify,
                            # alarm_schedules_enabled,
                            # alarm_sound_mod,
                            # encrypted,
                            "local_ip",
                            "local_rtsp_port",
                            "detection_sensibility",
                            "battery_level",
                            "alarm_schedules_enabled",
                            "alarm_notify",
                            "Motion_Trigger",
                            # last_alarm_time,
                            # last_alarm_pic
                        ],
                    )
                )
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "switch":
            try:
                print(json.dumps(client.get_switch(), indent=2))
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "connection":
            try:
                print(json.dumps(client.get_connection(), indent=2))
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        else:
            print("Action not implemented: %s", args.device_action)

    elif args.action == "devices_light":
        if args.devices_light_action == "status":
            try:
                print(
                    pd.DataFrame.from_dict(
                        data=client.load_light_bulbs(),
                        orient="index",
                        columns=[
                            "name",
                            # "version",
                            # "upgrade_available",
                            "status",
                            "device_category",
                            "device_sub_category",
                            "local_ip",
                            "productId",
                            "is_on",
                            "brightness",
                            "color_temperature",
                        ],
                    )
                )
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

    elif args.action == "light":
        # load light bulb object
        try:
            light_bulb = EzvizLightBulb(client, args.serial)
            logging.debug("Light bulb loaded")
        except Exception as exp:  # pylint: disable=broad-except
            print(exp)
            client.close_session()

        if args.light_action == "toggle":
            try:
                light_bulb.toggle_switch()
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.light_action == "status":
            try:
                print(json.dumps(light_bulb.status(), indent=2))

            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

    elif args.action == "home_defence_mode":

        if args.mode:
            try:
                print(
                    json.dumps(
                        client.api_set_defence_mode(
                            getattr(DefenseModeType, args.mode).value
                        ),
                        indent=2,
                    )
                )
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

    elif args.action == "mqtt":

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

        try:
            token = client.login()
            mqtt = MQTTClient(token)
            mqtt.start()

        except Exception as exp:  # pylint: disable=broad-except
            print(exp)
        finally:
            client.close_session()

    elif args.action == "camera":

        # load camera object
        try:
            camera = EzvizCamera(client, args.serial)
            logging.debug("Camera loaded")
        except Exception as exp:  # pylint: disable=broad-except
            print(exp)
            client.close_session()

        if args.camera_action == "move":
            try:
                camera.move(args.direction, args.speed)
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "move_coords":
            try:
                camera.move_coordinates(args.x, args.y)
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "status":
            try:
                print(json.dumps(camera.status(), indent=2))

            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "switch":
            try:
                if args.switch == "ir":
                    camera.switch_device_ir_led(args.enable)
                elif args.switch == "state":
                    print(args.enable)
                    camera.switch_device_state_led(args.enable)
                elif args.switch == "audio":
                    camera.switch_device_audio(args.enable)
                elif args.switch == "privacy":
                    camera.switch_privacy_mode(args.enable)
                elif args.switch == "sleep":
                    camera.switch_sleep_mode(args.enable)
                elif args.switch == "follow_move":
                    camera.switch_follow_move(args.enable)
                elif args.switch == "sound_alarm":
                    # Map 0|1 enable flog to operation type: 1 for off and 2 for on.
                    camera.switch_sound_alarm(args.enable + 1)
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "alarm":
            try:
                if args.sound is not None:
                    camera.alarm_sound(args.sound)
                if args.notify is not None:
                    camera.alarm_notify(args.notify)
                if args.sensibility is not None:
                    camera.alarm_detection_sensibility(args.sensibility)
                if args.do_not_disturb is not None:
                    camera.do_not_disturb(args.do_not_disturb)
                if args.schedule is not None:
                    camera.change_defence_schedule(args.schedule)
            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "select":
            try:
                if args.battery_work_mode is not None:
                    camera.set_battery_camera_work_mode(getattr(BatteryCameraWorkMode, args.battery_work_mode))

            except Exception as exp:  # pylint: disable=broad-except
                print(exp)
            finally:
                client.close_session()

        else:
            print("Action not implemented, try running with -h switch for help")

    else:
        print("Action not implemented: %s", args.action)


if __name__ == "__main__":
    sys.exit(main())
