#!/usr/bin/env python3
"""
    File: common.py
"""
import logging
import sys
from multiprocessing import AuthenticationError
from multiprocessing.connection import Connection, Listener
from typing import Any, Optional
from ffmpegCli import Ffmpegcli

# common variables:
DEBUG: bool = False
"""Should the daemon produce debug output."""
LOGGER: Optional[logging.Logger] = None
"""The logger to use."""
IS_DAEMON: bool = False
"""True if this process has forked or not."""
config: dict[str, Any] = {
    # Directory settings:
    'sharedWorkingDir': '/mnt/convert/',
    'localWorkingDir': '/home/user/convert/',
    # Connection settings:
    'host': '192.168.1.123',
    'port': 65500,
    'sharedSecret': 'hmkJ}]H%s9)jGQ(tB&AyF^',
    # Daemon configs:
    'numChunks': 2,
    'isFileHost': False,
}
"""The daemon config."""

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


def __accept__(listener: Listener) -> Connection:
    """
    Wait for, and return a valid connection.
    :param listener: Listener: The listener object to connect with.
    :return: Connection: The connected Connection object.
    """
    global connection
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
    :return: None
    """
    global connection
    if connection is not None:
        connection.close()
        connection = None
    return


def __send__(object_to_send: Any) -> None:
    global connection
    if connection is not None:
        try:
            connection.send(object_to_send)
        except ValueError as e:
            out_error("Attempted to send an invalid value.")
            exit(30)
    return


def __recv__() -> Any:
    global connection
    if connection is not None:
        try:
            recv_obj = connection.recv()
            return recv_obj
        except EOFError:
            out_error("EOF while trying to RECV.")
            exit(31)
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


if __name__ == '__main__':
    exit(0)
