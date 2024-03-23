#!/usr/bin/env python3
"""
    File: common.py
"""
import ipaddress
import sys
import json
from typing import Any, Final
from gi.repository import Gtk
sys.path.append('../')
from ffmpegCli.Ffmpegcli import Ffmpegcli

# Constants:
__version__: Final[str] = '1.0.0'


# Common variables:
working_dir: str = ''
"""The working directory of cluster encode parent"""
config_path: str = ''
"""The path to the config file."""
config: dict[str, Any] = {
    'version': '1.0',
    'sharedDir': '/mnt/convert/',
    'outputDir': '/mnt/convert/Output',
    'hosts': {
        'localhost': {
            'host': '127.0.0.1',
            'port': 65500,
            'isFileHost': False,
        },
    }
}
"""The custer encode GUI config dict."""
builder: Gtk.Builder
"""The common Gtk.Builder object."""
ffpmeg_cli: Ffmpegcli


def save_config() -> None:
    """
    Save the config file. If unable to save, exit's 10 on OSError.
    :return: None
    """
    try:
        with open(config_path, 'w') as file_handle:
            file_handle.write(json.dumps(config, indent=4))
    except OSError as e:
        print("Failed to open config file for writing.")
        exit(10)
    return


def validate_host_name(name: str) -> bool:
    """
    Make sure the given host name is not used.
    :param name: str: The name to check.
    :return: bool: True the name is unique, False it is not.
    """
    return name not in config['hosts'].keys()


def validate_address(address: str) -> bool:
    """
    Validate that the given address is a valid IP address.
    :param address: str: The address to check.
    :return: bool: True the address is good, False the address is bad.
    """
    try:
        _ = ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def validate_port(port: int) -> bool:
    """
    Validate the given port is good.
    :param port: int: The port to check.
    :return: bool: True the port is good; False the port is bad.
    """
    if port < 1024 or port > 65535:  # Allow only userspace ports.
        return False
    return True


def validate_secret(secret: str) -> bool:
    """
    Validate the shared secret is at least 8 chars long.
    :param secret: str: The secret to check.
    :return: bool: True the secret is good; False the secret is bad.
    """
    return len(secret) >= 8

