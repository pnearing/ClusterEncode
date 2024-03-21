#!/usr/bin/env python3
"""
    File: main.py
"""
import argparse
import ipaddress
import json
import logging
import os
import shutil
from typing import Final, Any, Optional
from multiprocessing.connection import Listener

import common
from common import out_error, out_info, out_warning, out_debug
from ffmpegCli import ffmpegCli

# Consts:
__version__: Final[str] = '1.0.0'
"""The version of the daemon."""
WORKING_DIR_NAME: Final[str] = ".ClusterEncodeDaemon"
"""The working directory where config is kept, and session status is kept."""
CONFIG_FILENAME: Final[str] = "config.json"
"""The configuration filename."""
LOG_FILENAME: Final[str] = 'CEDaemon.log'
"""The log file file name."""
VALID_COMMANDS: Final[tuple[str, ...]] = (
    'report', 'status', 'split', 'copy_input', 'encode', 'copy_output', 'combine', 'hash', 'shutdown'
)
"""A list of valid daemon commands."""


def validate_command_obj(command_obj: dict[str, Any]) -> bool:
    """
    Validate the basic command structure.
    :param command_obj: dict[str, Any] the command object.
    :return: bool: True the command passes the check, false it does not.
    """
    # Make sure command object is a dict:
    if not isinstance(command_obj, dict):
        common.send_error(1, "Invalid command object type. Not a dict.")
        common.__close__()
        return False
    # Make sure there is a version key:
    if 'version' not in command_obj.keys():
        common.send_error(2, "No version key in command object.")
        common.__close__()
        return False
    # Type check the version key:
    if not isinstance(command_obj['version'], str):
        common.send_error(3, "Version key is of wrong type, not a string.")
        common.__close__()
        return False
    # Make sure the version is 1.0.0:
    if command_obj['version'] != '1.0.0':
        common.send_error(4, "Un supported version.")
        common.__close__()
        return False
    # Make sure there is a command in the command object, if not close the connection and wait for another:
    if 'command' not in command_obj.keys():
        common.send_error(5, "No command key found in command object.")
        common.__close__()
        return False
    # Make sure the command value is of the right type:
    if not isinstance(command_obj['command'], str):
        common.send_error(6, "Invalid command type, not a string.")
        common.__close__()
        return False
    # Make sure the command is a valid command:
    if command_obj['command'] not in VALID_COMMANDS:
        common.send_error(7, "Command is invalid.")
        common.__close__()
        return False
    return True


def validate_command_params(command_obj: dict[str, Any], params: tuple[tuple[str, type], ...]) -> bool:
    for param in params:
        key_name, value_type = param
        if key_name not in command_obj.keys():
            common.send_error(20, "parameter '%s' doesn't exist." % key_name)
            common.__close__()
            return False
        if not isinstance(command_obj[key_name], value_type):
            common.send_error(21, "parameter '%s' must be '%s' type." % (key_name, value_type))
            common.__close__()
            return False
    return True


def build_report_dict() -> dict[str, Any]:
    """
    Create the dict to send as a report.
    :return: dict[str, Any]
    """
    response_obj: dict[str, Any] = {
        'version': '1.0.0',
        'daemonVersion': __version__,
        'ffmpegVersion': common.ffmpeg_cli.get_version(),
        'numChunks': common.config['numChunks'],
        'isFileHost': common.config['isFileHost'],
    }
    return response_obj


def build_status_dict() -> dict[str, Any]:
    """
    Build the response dict to status.
    :return: dict[str, Any]
    """
    response_obj = {
        'version': '1.0.0',
        'status': common.status,
    }
    # TODO: Add encoding / splitting data.
    return response_obj


def main() -> None:
    """
    Main loop.
    :return: None
    """
    # Create listener
    passwd = common.config['sharedSecret'].encode()
    listener = Listener((common.config['host'], common.config['port']), authkey=passwd)
    running = True
    while running:
        # Accept a connection:
        common.__accept__(listener)

        while True:  # Command response loop.
            # Receive the command and check that it's a dict, if not, close the connection and wait for another:
            command_obj: dict[str, Any] = common.__recv__()

            # Validate command
            if not validate_command_obj(command_obj):
                break  # The connection was closed.

            # Act on command:
            if command_obj['command'] == 'shutdown':  # Shutdown command:
                common.__close__()
                running = False
                break
            elif command_obj['command'] == 'report':  # Report settings command:
                response_obj = build_report_dict()
                common.__send__(response_obj)
            elif command_obj['command'] == 'status':  # Current status command:
                response_obj = build_status_dict()
                common.__send__(response_obj)
            elif command_obj['command'] == 'split':  # Split the video command:
                def send_progress(file_path, file_count):
                    progress_obj = {
                        'version': '1.0.0',
                        'status': 'splitting',
                        'filePath': file_path,
                        'fileCount': file_count,
                    }
                    common.__send__(progress_obj)
                    return
                params = (('inputFile', str), ('outputDir', str), ('chunkSize', int))
                if not validate_command_params(command_obj, params):
                    break  # The connection was closed.
                suppress_error: bool = not common.DEBUG
                common.ffmpeg_cli.split(
                    command_obj['inputFile'],
                    command_obj['outputDir'],
                    command_obj['chunkSize'],
                    send_progress)
                success, output_files = common.ffmpeg_cli.split_finish()
                finished_obj = {
                    'version': '1.0.0',
                    'status': 'split finished',
                    'success': success,
                    'outputFiles': output_files,
                }

            elif command_obj['command'] == 'copy_input':  # Copy input chunk to local working directory command:
                pass
            elif command_obj['command'] == 'encode':  # Encode chunk command:
                pass
            elif command_obj['command'] == 'copy_output':  # Copy output chunk.
                pass
            elif command_obj['command'] == 'combine':  # Combine the video chunks command:
                pass
            elif command_obj['command'] == 'hash':  # Preform a hash on a video chunk:
                pass

    return


##############################################
# Initialize:
if __name__ == '__main__':
    description = """
    Cluster encode daemon process.
    Exit codes:
        1 = Failed to create working directory in HOME.
        2 = Working directory exists, but is not a directory.
        3 = Supplied config file path doesn't exist.
        4 = Supplied config file isn't a file.
        5 = Failed to create default config file.
        6 = Failed to read the config file.
        7 = Failed to decode JSON from config file. (Invalid config JSON.)
        8 = Shared working directory must be a string. (Invalid config type.)
        9 = Shared working directory doesn't exist. (Invalid config option.)
        10 = Local working directory must be a string. (Invalid config type.)
        11 = Local working directory doesn't exist. (Invalid cconfig option.)
        12 = IP address must be a string. (Invalid config type.)
        13 = IP address to listen on isn't a valid IP address. (Invalid config option.)
        14 = Port to listen on must be an integer. (Invalid config type.)
        15 = Port to listen on is out of range. (Invalid config option.)
        16 = Shared secret must be a string. (Invalid config type.)
        17 = Shared secret is too short. (Invalid config option.)
        18 = Number of chunks must be an integer. (Invalid config type.)
        19 = Number of chunks is less than 0. (Invalid config option.)
        20 = Is file host must be a boolean. (Invalid config type.)
        21 = Failed to save config file.
        22 = Unable to find ffmpeg
        23 = Error while trying to fork process.
        30 = Error while sending data.
        31 = Error while receiving data.
    """
    # Command line arguments:
    parser = argparse.ArgumentParser(description=description,
                                     epilog="Written by Peter Nearing.")
    parser.add_argument('--debug',
                        help='Produce debug output.',
                        action='store_true',
                        default=False)
    parser.add_argument('--noFork',
                        help="Do not fork the daemon.",
                        action='store_false',
                        dest='doFork',
                        default=True)
    parser.add_argument('--configFile',
                        help="The full path to the config file.",
                        type=str)
    parser.add_argument('--sharedWorkingDir',
                        help="The full path to the shared working directory.",
                        type=str)
    parser.add_argument('--localWorkingDir',
                        help="The full path to the local working directory.",
                        type=str)
    parser.add_argument('--hostIP',
                        help="The IP to listen on.",
                        type=str)
    parser.add_argument('--port',
                        help='The port to listen on.',
                        type=int)
    parser.add_argument('--sharedSecret',
                        help='The shared secret for the daemon / client connection.',
                        type=str)
    parser.add_argument('--numChunks',
                        help="The number of simultaneous jobs to execute.",
                        type=int)
    parser.add_argument('--isFileHost',
                        help='This daemon instance hosts the files. IE: Is the NFS server.',
                        action='store_true',
                        default=None)
    parser.add_argument('--saveConfig',
                        help="Save the options to the config file and exit.",
                        action='store_true',
                        default=False)
    args = parser.parse_args()

    # Set debug:
    common.DEBUG = args.debug

    # Create and change to working directory:
    out_info("Changing to working directory.")
    working_dir_path = os.path.join(os.environ['HOME'], WORKING_DIR_NAME)
    if not os.path.exists(working_dir_path):
        out_debug("Working directory doesn't exist, creating.")
        try:
            os.mkdir(working_dir_path)
            out_debug("Working directory created.")
        except OSError as e:
            out_error("Failed to create default data directory '%s': %s[%d]" % (working_dir_path, e.strerror, e.errno))
            exit(1)
    if not os.path.isdir(working_dir_path):
        out_error("Error: Working directory is a regular file: %s" % working_dir_path)
        exit(2)
    os.chdir(working_dir_path)

    # Setup logging
    out_debug("Setup logging.")
    log_level = logging.INFO
    if common.DEBUG:
        log_level = logging.DEBUG
    log_path = os.path.join(working_dir_path, LOG_FILENAME)
    logging.basicConfig(filename=log_path, level=log_level)
    common.LOGGER = logging.getLogger(__name__)
    out_debug("Logging started.")

    # Set the default config file path, and select the config file path to use:
    out_info("Selecting config file.")
    default_config_file_path = os.path.join(working_dir_path, CONFIG_FILENAME)
    if args.configFile is not None:
        out_info("User provided config file.")
        if not os.path.exists(args.configFile):
            out_error("Config file: '%s' doesn't exist." % args.configFile)
            exit(3)
        if not os.path.isfile(args.configFile):
            out_error("Config file: '%s' doesn't report as a file." % args.configFile)
            exit(4)
        config_file_path = args.configFile
    else:
        out_info("Using default config file.")
        config_file_path = default_config_file_path

    # Create the default config if it doesn't already exist:
    if config_file_path == default_config_file_path and not os.path.exists(config_file_path):
        out_debug("Default config doesn't exist, creating.")
        try:
            with open(config_file_path, 'w') as file_handle:
                file_handle.write(json.dumps(common.config, indent=4))
        except OSError as e:
            out_error("Failed to create default config file: '%s', %s[%d]." % (config_file_path, e.strerror, e.errno))
            exit(5)

    # Load the config:
    out_info("Loading config.")
    try:
        with open(config_file_path, 'r') as file_handle:
            common.config = json.loads(file_handle.read())
    except OSError as e:
        out_error("Failed to load config file '%s': %s[%d]" % (config_file_path, e.strerror, e.errno))
        exit(6)
    except json.JSONDecodeError as e:
        out_error("Failed to decode JSON from config file '%s': %s." % (config_file_path, e.msg))
        exit(7)

    # Override configs with command line options:
    if args.sharedWorkingDir is not None:  # Shared working Directory:
        common.config['sharedWorkingDir'] = args.sharedWorkingDirectory
    if not isinstance(common.config['sharedWorkingDir'], str):
        out_error("Shared working directory must be a string.")
        exit(8)
    if not os.path.exists(common.config['sharedWorkingDir']):
        out_error("Provided shared working directory doesn't exist.")
        exit(9)

    if args.localWorkingDir is not None:  # Local working directory:
        common.config['localWorkingDir'] = args.localWorkingDir
    if not isinstance(common.config['localWorkingDir'], str):
        out_error("Provided local working directory must be a string.")
        exit(10)
    if not os.path.exists(common.config['localWorkingDir']):
        out_error("Provided local working directory doesn't exist.")
        exit(11)

    if args.hostIP is not None:  # Listen IP:
        common.config['host'] = args.hostIP
    if not isinstance(common.config['host'], str):
        out_error("Provided host IP must be a string.")
        exit(12)
    try:
        _ = ipaddress.ip_address(common.config['host'])
    except ValueError as e:
        out_error("Provided host IP isn't an IP address.")
        exit(13)

    if args.port is not None:  # Listen port:
        common.config['port'] = args.port
    if not isinstance(common.config['port'], int):
        out_error("Provided port must be an integer.")
        exit(14)
    if common.config['port'] <= 0 or common.config['port'] > 65535:
        out_error("Invalid port provided.")
        exit(15)

    if args.sharedSecret is not None:  # Connection shared secret.
        common.config['sharedSecret'] = args.sharedSecret
    if not isinstance(common.config['sharedSecret'], str):
        out_error("Provided shared secret is not a string.")
        exit(16)
    if len(common.config['sharedSecret']) < 8:
        out_error("Shared secret too short. (< 8 char.)")
        exit(17)

    if args.numChunks is not None:  # Number of chunks to process:
        common.config['numChunks'] = args.numChunks
    if not isinstance(common.config['numChunks'], int):
        out_error("Provided numChunks must be an integer.")
        exit(18)
    if common.config['numChunks'] < 0:
        out_error("Number of chunks must be greater than or equal to 0.")
        exit(19)

    if args.isFileHost is not None:  # Is file host:
        common.config['isFileHost'] = args.isFileHost
    if not isinstance(common.config['isFileHost'], bool):
        out_error("Config 'isFileHost' must be a boolean.")
        exit(20)

    # If --saveConfig is selected, save config and exit:
    if args.saveConfig is True:
        out_info("Saving config, and exiting.")
        try:
            with open(config_file_path, 'w') as file_handle:
                file_handle.write(json.dumps(common.config, indent=4))
            exit(0)
        except OSError as e:
            out_error("Failed to write config: %s[%d]." % (e.strerror, e.errno))
            exit(21)

    # Find ffmpeg, and setup cli object:
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        out_error("Unable to find ffmpeg.")
        exit(22)
    common.ffmpeg_cli = ffmpegCli(ffmpeg_path)

    # Fork if requested:
    if args.doFork is True:
        try:
            pid = os.fork()
            if pid == 0:  # Child process:
                os.setsid()  # Set new session
                os.chdir(working_dir_path)  # Make sure the working dir is set.
            else:  # Parent process:
                os._exit(0)  # Exit parent.
        except OSError as e:
            out_error("Got error while trying to fork: %s[%d]" % (e.strerror, e.errno))
            exit(23)

    # Run main:
    try:
        main()
    except (KeyboardInterrupt, InterruptedError):
        pass

    # Exit gracefully:
    exit(0)
