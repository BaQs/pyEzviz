"""pyezviz command line."""
import argparse
import http.client
import json
import logging
import sys

import pandas
from pyezviz import EzvizCamera, EzvizClient
from pyezviz.constants import DefenseModeType


def main():
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

    parser_home_defence_mode = subparsers.add_parser(
        "home_defence_mode", help="Set home defence mode"
    )
    parser_home_defence_mode.add_argument(
        "--mode", required=False, help="Choose mode", choices=["HOME_MODE", "AWAY_MODE"]
    )

    parser_camera = subparsers.add_parser("camera", help="Camera actions")
    parser_camera.add_argument("--serial", required=True, help="camera SERIAL")

    subparsers_camera = parser_camera.add_subparsers(dest="camera_action")

    parser_camera_status = subparsers_camera.add_parser(
        "status", help="Get the status of the camera"
    )
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

    parser_camera_switch = subparsers_camera.add_parser(
        "switch", help="Change the status of a switch"
    )
    parser_camera_switch.add_argument(
        "--switch",
        required=True,
        help="Switch to switch",
        choices=["audio", "ir", "state", "privacy", "sleep", "follow_move"],
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
        help="Sound level (2 is disabled, 1 intensive, 0 software)",
        type=int,
        choices=[0, 1, 2],
    )
    parser_camera_alarm.add_argument(
        "--sensibility",
        required=False,
        help="Sensibility level (Non-Cameras = from 1 to 6) or (Cameras = 1 to 100)",
        type=int,
        choices=range(0, 100),
    )
    parser_camera_alarm.add_argument(
        "--schedule", required=False, help="Schedule in json format *test*", type=str
    )

    args = parser.parse_args()

    # print("--------------args")
    # print("--------------args: %s",args)
    # print("--------------args")

    client = EzvizClient(args.username, args.password, args.region)

    if args.debug:

        http.client.HTTPConnection.debuglevel = 5
        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    if args.action == "devices":

        if args.device_action == "device":
            try:
                client.login()
                print(json.dumps(client.get_device(), indent=2))
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "status":
            try:
                client.login()
                # print(json.dumps(client.load_cameras(), indent=2))
                print(
                    pandas.DataFrame(client.load_cameras()).to_string(
                        columns=[
                            "serial",
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
                        ]
                    )
                )
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "switch":
            try:
                client.login()
                print(json.dumps(client.get_switch(), indent=2))
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

        elif args.device_action == "connection":
            try:
                client.login()
                print(json.dumps(client.get_connection(), indent=2))
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

        else:
            print("Action not implemented: %s", args.device_action)

    elif args.action == "home_defence_mode":

        if args.mode:
            try:
                client.login()
                print(
                    json.dumps(
                        client.api_set_defence_mode(
                            getattr(DefenseModeType, args.mode).value
                        ),
                        indent=2,
                    )
                )
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

    elif args.action == "camera":

        # load camera object
        try:
            client.login()
            camera = EzvizCamera(client, args.serial)
            logging.debug("Camera loaded")
        except BaseException as exp:
            print(exp)
        finally:
            client.close_session()

        if args.camera_action == "move":
            try:
                camera.move(args.direction, args.speed)
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()

        elif args.camera_action == "status":
            try:
                print(json.dumps(camera.status(), indent=2))

            except BaseException as exp:
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
            except BaseException as exp:
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
                if args.schedule is not None:
                    camera.change_defence_schedule(args.schedule)
            except BaseException as exp:
                print(exp)
            finally:
                client.close_session()
    else:
        print("Action not implemented: %s", args.action)


if __name__ == "__main__":
    sys.exit(main())
