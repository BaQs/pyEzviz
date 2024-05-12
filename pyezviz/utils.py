"""Decrypt camera images."""
from __future__ import annotations

from hashlib import md5
import json
import logging
from typing import Any

from Crypto.Cipher import AES

from .exceptions import PyEzvizError

_LOGGER = logging.getLogger(__name__)


def convert_to_dict(data: Any) -> Any:
    """Recursively convert a string representation of a dictionary to a dictionary."""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    # Attempt to convert the string back into a dictionary
                    data[key] = json.loads(value)

                except ValueError:
                    continue
            continue

    return data


def string_to_list(data: Any, separator: str = ",") -> Any:
    """Convert a string representation of a list to a list."""
    if isinstance(data, str):
        if separator in data:
            try:
                # Attempt to convert the string into a list
                return data.split(separator)

            except AttributeError:
                return data

    return data


def fetch_nested_value(data: Any, keys: list, default_value: Any = None) -> Any:
    """Fetch the value corresponding to the given nested keys in a dictionary.

    If any of the keys in the path doesn't exist, the default value is returned.

    Args:
        data (dict): The nested dictionary to search for keys.
        keys (list): A list of keys representing the path to the desired value.
        default_value (optional): The value to return if any of the keys doesn't exist.

    Returns:
        The value corresponding to the nested keys or the default value.

    """
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default_value


def decrypt_image(input_data: bytes, password: str) -> bytes:
    """Decrypts image data with provided password.

    Args:
        input_data (bytes): Encrypted image data
        password (string): Verification code

    Raises:
        PyEzvizError

    Returns:
        bytes: Decrypted image data

    """

    if len(input_data) < 48:
        raise PyEzvizError("Invalid image data")

    # check header
    if input_data[:16] != b"hikencodepicture":
        _LOGGER.warning("Image header doesn't contain 'hikencodepicture'")
        return input_data

    file_hash = input_data[16:48]
    passwd_hash = (
        md5(str.encode(md5(str.encode(password)).digest().hex())).digest().hex()
    )
    if file_hash != str.encode(passwd_hash):
        raise PyEzvizError("Invalid password")

    key = str.encode(password.ljust(16, "\u0000")[:16])
    iv_code = bytes([48, 49, 50, 51, 52, 53, 54, 55, 0, 0, 0, 0, 0, 0, 0, 0])
    cipher = AES.new(key, AES.MODE_CBC, iv_code)

    next_chunk = b""
    output_data = b""
    finished = False
    i = 48  # offset hikencodepicture + hash
    chunk_size = 1024 * AES.block_size
    while not finished:
        chunk, next_chunk = next_chunk, cipher.decrypt(input_data[i : i + chunk_size])
        if len(next_chunk) == 0:
            padding_length = chunk[-1]
            chunk = chunk[:-padding_length]
            finished = True
        output_data += chunk
        i += chunk_size
    return output_data

def deep_merge(dict1, dict2):
    """Recursively merges two dictionaries, handling lists as well.

    Args:
    dict1 (dict): The first dictionary.
    dict2 (dict): The second dictionary.

    Returns:
    dict: The merged dictionary.

    """
    # If one of the dictionaries is None, return the other one
    if dict1 is None:
        return dict2
    if dict2 is None:
        return dict1

    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        if isinstance(dict1, list) and isinstance(dict2, list):
            return dict1 + dict2
        return dict2

    # Create a new dictionary to store the merged result
    merged = {}

    # Merge keys from both dictionaries
    for key in set(dict1.keys()) | set(dict2.keys()):
        if key in dict1 and key in dict2:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                merged[key] = deep_merge(dict1[key], dict2[key])
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                merged[key] = dict1[key] + dict2[key]
            else:
                # If both values are not dictionaries or lists, keep the value from dict2
                merged[key] = dict2[key]
        elif key in dict1:
            # If the key is only in dict1, keep its value
            merged[key] = dict1[key]
        else:
            # If the key is only in dict2, keep its value
            merged[key] = dict2[key]

    return merged

