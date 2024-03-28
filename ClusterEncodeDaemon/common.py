#!/usr/bin/env python3
"""
    File: common.py
"""
import logging
import os
import sys
from multiprocessing import AuthenticationError
from multiprocessing.connection import Connection, Listener
from typing import Any, Optional
from Config import Config, ConfigError
sys.path.append('../')
from ffmpegCli import Ffmpegcli
# common variables:
DEBUG: bool = False
"""Should the daemon produce debug output."""
LOGGER: Optional[logging.Logger] = None
"""The logger to use."""
IS_DAEMON: bool = False
"""True if this process has forked or not."""
config: Optional[Config] = None
"""The daemon config."""
listener: Optional[Listener] = None
"""The listener for the daemon."""
connection: Optional[Connection] = None
"""The current connection."""
ffmpeg_cli: Optional[Ffmpegcli] = None
"""The ffmpeg cli helper."""
status: str = "Idle"
"""The current status of the daemon."""


##########################################################################
# Output methods:
def out_info(message: str) -> None:
    """
    Output an info message.
    :param message: str: The message to output.
    :return: None
    """
    global LOGGER, IS_DAEMON
    if LOGGER is not None:
        LOGGER.info(message)
    if not IS_DAEMON:
        print("INFO:", message, file=sys.stdout)
    return


def out_warning(message: str) -> None:
    """
    Output a warning message.
    :param message: str: The message to output.
    :return: None
    """
    global LOGGER, IS_DAEMON
    if LOGGER is not None:
        LOGGER.warning(message)
    if not IS_DAEMON:
        print("WARNING:", message, file=sys.stderr)
    return


def out_error(message: str) -> None:
    """
    Output an error message.
    :param message: str: The message to output.
    :return: None
    """
    global LOGGER, IS_DAEMON
    if LOGGER is not None:
        LOGGER.error(message)
    if not IS_DAEMON:
        print("ERROR:", message, file=sys.stderr)
    return


def out_debug(message: str) -> None:
    """
    Output a debug message.
    :param message: str: The message to output
    :return: None
    """
    global LOGGER, DEBUG
    if LOGGER is not None:
        LOGGER.debug(message)
    if DEBUG:
        print("DEBUG:", message, file=sys.stdout)
    return


#######################################
# Connection functions:
def __accept__() -> Connection:
    """
    Wait for, and set a valid connection.
    :return: Connection: The connected Connection object.
    """
    global connection, listener
    while True:
        try:
            connection = listener.accept()
            return connection
        except AuthenticationError:
            continue
        except ConnectionResetError:
            continue


def __close__() -> None:
    """
    Close the connection if it's open.
    :return: bool: True the connection was closed, False it was not.
    """
    global connection
    if connection is not None:
        connection.close()
        connection = None
        return True
    return False


def __send__(object_to_send: Any) -> bool:
    """
    Send data over the comms channel.
    :param object_to_send: Any: The data to send.
    :return: bool: True the data was sent, False is was not.
    """
    global connection
    if connection is not None:
        connection.send(object_to_send)
        return True
    return False


def __recv__() -> Any:
    global connection
    if connection is not None:
        recv_obj = connection.recv()
        return recv_obj
    return None


def send_error(error_no: int, error_msg: str) -> None:
    """
    Send an error response from the daemon to the GUI.
    :param error_no: int: The error number.
    :param error_msg: The error message.
    :return: None
    """
    error_obj = {
        'status': 'error',
        'error': {
            'number': error_no,
            'message': error_msg,
        },
    }
    __send__(error_obj)
    return


#############################################
# Protocol functions:
def parse_path(path: str) -> str:
    """
    Replace %shared% and %local% with their respective directories.
    :param path: The path to parse.
    :return: str: The path with the values replaced.
    """
    return_path: str = path
    if path.startswith('%shared%/'):
        temp_path: str = path[9:]
        return_path = os.path.join(config.shared_working_dir, temp_path)
    elif path.startswith('%local%/'):
        temp_path: str = path[8:]
        return_path = os.path.join(config.local_working_dir, temp_path)
    return return_path




if __name__ == '__main__':
    exit(0)
