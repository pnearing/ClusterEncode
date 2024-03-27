#!/usr/bin/env python3
"""
    File: common.py
"""
import ipaddress
import sys
import json
from typing import Any, Final, Optional
from gi.repository import Gtk
from multiprocessing.connection import Client, Connection
from multiprocessing import AuthenticationError


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
builder: Optional[Gtk.Builder] = None
"""The common Gtk.Builder object."""
ffpmeg_cli: Optional[Ffmpegcli] = None
"""The ffmpeg cli object."""
open_connections: list[tuple[str, Connection]] = []
"""A list of open connections and their names."""


####################################
# Config functions:
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


#####################################
# Validation functions:
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


def validate_host_values(name: str, address: str, port: int, secret: str) -> bool:
    """
    Validate the host values and show a pop up saying what went wrong.
    :param name: str: The name of the host
    :param address: str: The ip address of the host.
    :param port: int: The port of the host.
    :param secret: str: The shared secret.
    :return: bool: True, no error, False, an error occurred.
    """
    error_dialog: Gtk.Dialog = builder.get_object('error_dialog')  # The error dialog for errors.
    error_label: Gtk.Label = builder.get_object('lbl_error_text')  # The error label for the message.

    if not validate_host_name(name):
        error_label.set_label('Invalid name for the host, already in use.')
        error_dialog.run()
        error_dialog.hide()
        return False
    elif not validate_address(address):
        error_label.set_label('Address is not a valid IPv4 or IPv6 address.')
        error_dialog.run()
        error_dialog.hide()
        return False
    elif not validate_port(port):
        error_label.set_label('Port is an invalid port.')
        error_dialog.run()
        error_dialog.hide()
        return False
    elif not validate_secret(secret):
        error_label.set_label('Secret is too short.')
        error_dialog.run()
        error_dialog.hide()
        return False
    return True


###################################
# Open connections functions:
def get_connection_by_name(search_name: str) -> Optional[Connection]:
    """
    Get an open connection by the hosts name.
    :param search_name: str: The host's name to search for.
    :return: Optional[Connection]: The open connection, or None if name not found.
    """
    global open_connections
    for host_name, connection in open_connections:
        if search_name == host_name:
            return connection
    return None


def get_name_by_connection(search_connection: Connection) -> Optional[str]:
    """
    Get the name of a given connection if it's in the list.
    :param search_connection: Connection: The connection object to search for.
    :return: Optional[str]: If the connection was found in the list, returns the name, otherwise returns None.
    """
    global open_connections
    for host_name, connection in open_connections:
        if connection == search_connection:
            return host_name
    return None


def append_connection(host_name: str, connection: Connection) -> bool:
    """
    Append a connection to the open connections list.
    :param host_name: str: The host's name to append.
    :param connection: The Connection object to append.
    :return: bool: True if the connection was added to the list, False if not.
    """
    global open_connections
    if get_connection_by_name(host_name) is None and get_name_by_connection(connection) is None:
        open_connections.append((host_name, connection))
        return True
    return False


def remove_connection_by_name(search_name: str) -> bool:
    """
    Remove a connection from the list given its name.
    :param search_name: str: The name of the host to remove.
    :return: bool: True if the host was removed, False if not.
    """
    global open_connections
    new_open_connections: list[tuple[str, Connection]] = []
    connection_found: bool = False
    for host_name, connection in open_connections:
        if host_name == search_name:
            connection_found = True
        else:
            new_open_connections.append((host_name, connection))
    open_connections = new_open_connections
    return connection_found


def remove_connection_by_connection(search_connection: Connection) -> bool:
    """
    Remove a connection from the open connections:
    :param search_connection: Connection: The connection to remove.
    :return: bool: True the connection was removed, False it was not.
    """
    global open_connections
    new_open_connections: list[tuple[str, Connection]] = []
    connection_found: bool = False
    for host_name, connection in open_connections:
        if connection == search_connection:
            connection_found = True
        else:
            new_open_connections.append((host_name, connection))
    open_connections = new_open_connections
    return connection_found


#################################
# Communications functions:
def connect_to_host(address: str, port: int, secret: str) -> tuple[bool, Connection | str]:
    """
    Connect to a host and return the connection.
    :param address: str: The address of the host.
    :param port: int: The port of the host.
    :param secret: str: The shared secret for this host.
    :return: tuple[str, Connection | str]: The first element of the returned tuple is True the connection was a success,
    and False if the connection failed.  The second element is the tuple is either the Connection object, or a str
    with an error message.
    """
    try:
        connection = Client((address, port), authkey=secret.encode())
        return True, connection
    except ConnectionRefusedError:
        return False, "Connection refused."
    except AuthenticationError:
        return False, "Authentication error."
    except OSError as e:
        if e.errno == -2:
            return False, "Invalid address."
        return False, "Error connecting: %s[%d]" % (e.strerror, e.errno)


def get_host_status(host_name: str) -> Optional[dict[str, Any]]:
    connection = get_connection_by_name(host_name)
    if connection is None or connection.closed:
        return None
    # Create and send the status command object:
    command_obj: dict[str, Any] = {
        'version': '1.0.0',
        'command': 'status',
    }
    connection.send(command_obj)

    # Receive the response:
    response_obj: dict[str, Any] = connection.recv()

























