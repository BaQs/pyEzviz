"""Test camera RTSP authentication."""
import base64
import hashlib
import socket

from pyezviz.exceptions import AuthTestResultFailed, InvalidHost


def genmsg_describe(url, seq, user_agent, auth_seq):
    """Generate RTSP describe message."""
    msg_ret = "DESCRIBE " + url + " RTSP/1.0\r\n"
    msg_ret += "CSeq: " + str(seq) + "\r\n"
    msg_ret += "Authorization: " + auth_seq + "\r\n"
    msg_ret += "User-Agent: " + user_agent + "\r\n"
    msg_ret += "Accept: application/sdp\r\n"
    msg_ret += "\r\n"
    return msg_ret


class TestRTSPAuth:
    """Test RTSP credentials."""

    def __init__(
        self,
        ip_addr,
        username=None,
        password=None,
        test_uri="",
    ):
        """Initialize RTSP credential test."""
        self._rtsp_details = {
            "bufLen": 1024,
            "defaultServerIp": ip_addr,
            "defaultServerPort": 554,
            "defaultTestUri": test_uri,
            "defaultUserAgent": "RTSP Client",
            "defaultUsername": username,
            "defaultPassword": password,
        }

    def generate_auth_string(self, realm, method, uri, nonce):
        """Generate digest auth string."""
        map_return_info = {}
        m_1 = hashlib.md5(
            f"{self._rtsp_details['defaultUsername']}:"
            f"{realm.decode()}:"
            f"{self._rtsp_details['defaultPassword']}".encode()
        ).hexdigest()
        m_2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()
        response = hashlib.md5(f"{m_1}:{nonce}:{m_2}".encode()).hexdigest()

        map_return_info = (
            f"Digest "
            f"username=\"{self._rtsp_details['defaultUsername']}\", "
            f'realm="{realm.decode()}", '
            f'algorithm="MD5", '
            f'nonce="{nonce.decode()}", '
            f'uri="{uri}", '
            f'response="{response}"'
        )
        return map_return_info

    def main(self):
        """Start main method."""
        session = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            session.connect(
                (
                    self._rtsp_details["defaultServerIp"],
                    self._rtsp_details["defaultServerPort"],
                )
            )

        except TimeoutError as err:
            raise AuthTestResultFailed("Invalid ip or camera hibernating") from err

        except (socket.gaierror, ConnectionRefusedError) as err:
            raise InvalidHost("Invalid IP or Hostname") from err

        seq = 1

        url = (
            "rtsp://"
            + self._rtsp_details["defaultServerIp"]
            + self._rtsp_details["defaultTestUri"]
        )

        auth_seq = base64.b64encode(
            f"{self._rtsp_details['defaultUsername']}:"
            f"{self._rtsp_details['defaultPassword']}".encode("ascii")
        )
        auth_seq = "Basic " + auth_seq.decode()

        print(
            genmsg_describe(url, seq, self._rtsp_details["defaultUserAgent"], auth_seq)
        )
        session.send(
            genmsg_describe(
                url, seq, self._rtsp_details["defaultUserAgent"], auth_seq
            ).encode()
        )
        msg1 = session.recv(self._rtsp_details["bufLen"])
        seq = seq + 1

        if msg1.decode().find("200 OK") > 1:
            print(f"Basic auth result: {msg1.decode()}")
            return print("Basic Auth test passed. Credentials Valid!")

        if msg1.decode().find("Unauthorized") > 1:
            # Basic failed, doing new DESCRIBE with digest authentication.
            start = msg1.decode().find("realm")
            begin = msg1.decode().find('"', start)
            end = msg1.decode().find('"', begin + 1)
            realm = msg1[begin + 1 : end]

            start = msg1.decode().find("nonce")
            begin = msg1.decode().find('"', start)
            end = msg1.decode().find('"', begin + 1)
            nonce = msg1[begin + 1 : end]

            auth_seq = self.generate_auth_string(
                realm,
                "DESCRIBE",
                self._rtsp_details["defaultTestUri"],
                nonce,
            )

            print(
                genmsg_describe(
                    url, seq, self._rtsp_details["defaultUserAgent"], auth_seq
                )
            )

            session.send(
                genmsg_describe(
                    url, seq, self._rtsp_details["defaultUserAgent"], auth_seq
                ).encode()
            )
            msg1 = session.recv(self._rtsp_details["bufLen"])
            print(f"Digest auth result: {msg1.decode()}")

            if msg1.decode().find("200 OK") > 1:
                return print("Digest Auth test Passed. Credentials Valid!")

            if msg1.decode().find("401 Unauthorized") > 1:
                raise AuthTestResultFailed("Credentials not valid!!")

        return print("Basic Auth test passed. Credentials Valid!")
