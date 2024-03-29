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
import sys
from datetime import timedelta
from typing import Final, Any
from multiprocessing.connection import Listener
from Config import Config, ConfigError
import common
from common import out_error, out_info, out_debug, out_warning
sys.path.append('../')
from ffmpegCli import Ffmpegcli

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
    'report', 'status', 'split', 'copy_input', 'encode', 'copy_output', 'combine', 'hash', 'shutdown', 'close',
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
            common.send_error(21, "parameter '%s' must be '%s' type." % (key_name, str(value_type)))
            common.__close__()
            return False
    return True


def check_file_or_directory_exists(path: str, is_file: bool = True) -> bool:
    """
    Check if a file or directory exists on the system, and if not, send an error object and close the connection.
    :param path: str: The path to check.
    :param is_file: bool: True check for a file, False, check for a directory.
    :return: bool: The file / directory exists, False the file / directory doesn't exist and the connection has been
    closed.
    """
    if not os.path.exists(path):
        common.send_error(30, "File | directory '%s' doesn't exist." % path)
        common.__close__()
        return False
    if is_file:
        if not os.path.isfile(path):
            common.send_error(31, "'%s' isn't a file." % path)
            common.__close__()
            return False
    else:
        if not os.path.isdir(path):
            common.send_error(32, "'%s' isn't a directory." % path)
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
        'status': common.status,
        'daemonVersion': __version__,
        'ffmpegVersion': common.ffmpeg_cli.get_version(),
        'numChunks': common.config.num_chunks,
        'isFileHost': common.config.is_file_host,
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


def report_split_progress(report_type: str, *args) -> None:
    response_obj = {
        'version': '1.0.0',
    }
    if report_type == 'new_file':
        response_obj['status'] = 'splitting new file'
        response_obj['filePath'] = args[0]  # str
        response_obj['numFiles'] = args[1]  # int
    elif report_type == 'report':
        response_obj['status'] = 'splitting report'
        response_obj['currentTime'] = args[0]  # timedelta
        response_obj['currentSpeed'] = args[1]  # str
        response_obj['segmentComplete'] = args[2]  # float 0.0 -> 100.0
        response_obj['totalComplete'] = args[3]  # Optional[float] 0.0 -> 100.0
    common.__send__(response_obj)
    return


def do_split(input_path: str, output_path: str, chunk_size: int, length: timedelta) -> bool:
    """
    Call ffmpeg split thread
    :param input_path: str: The input file to split.
    :param output_path: str: The output dir for the resulting files.
    :param chunk_size: int: The number of seconds to split by.
    :param length: timedelta: The total length of the input file as a timedelta.
    :return: bool: True the split completed successfully. False it did not.
    """
    # Start the split:
    success: bool = common.ffmpeg_cli.split(
        input_path=input_path,
        output_path=output_path,
        chunk_size=chunk_size,
        callback=report_split_progress,
        report_delay=0.5,
        total_time=length
    )

    if not success:
        common.send_error(40, "Failed to start split thread.")
        common.__close__()
        return False

    success, output_files = common.ffmpeg_cli.split_finish()

    if not success:
        common.send_error(41, "Split reports as failed.")
        common.__close__()
        return False

    # Send split finished.
    finished_obj = {
        'version': '1.0.0',
        'status': 'split finished',
        'success': success,
        'outputFiles': output_files,
    }
    common.__send__(finished_obj)
    return True


def main() -> None:
    """
    Main loop.
    :return: None
    """
    running: bool = True
    while running:
        # Accept a connection:
        out_info("Waiting for connection...")
        common.__accept__()
        out_info("Accepted connection.")
        while True:  # Command response loop.
            # Receive the command:
            out_info("Waiting for command...")
            command_obj: dict[str, Any] = common.__recv__()
            out_info("Command received, verifying...")
            # Validate command
            if not validate_command_obj(command_obj):  # Sends an error and closes the connection.
                out_warning("Invalid command: %s" % str(command_obj))
                break  # The connection was closed.
            out_info("Command is valid.")
            # Act on command:
            if command_obj['command'] == 'shutdown':  # Shutdown command:
                out_info("Received shutdown command, shutting down.")
                common.__close__()
                running = False
                break
            elif command_obj['command'] == 'report':  # Report settings command:
                out_info("Received report command.")
                common.status = 'reporting'
                response_obj = build_report_dict()
                common.__send__(response_obj)
                common.status = 'idle'
                out_info("Report sent.")
            elif command_obj['command'] == 'status':  # Current status command:
                out_info("Received status command.")
                response_obj = build_status_dict()
                common.__send__(response_obj)
                out_info("Status sent.")
            elif command_obj['command'] == 'split':  # Split the video command:
                out_info("Received split command, verifying params.")
                # Make sure params exist, and are the right type:
                params = (('inputFile', str), ('outputDir', str), ('chunkSize', int), ('length', timedelta))
                if not validate_command_params(command_obj, params):  # Sends an error and closes the connection.
                    out_warning("Invalid params for split command.")
                    break  # The connection was closed.
                out_info("Params validated, verifying values...")
                # Parse the input file and output directory for shared / local directory:
                input_file_path = common.parse_path(command_obj['inputFile'])
                output_dir_path = common.parse_path(command_obj['outputDir'])
                # Verify the input file exists:
                if not check_file_or_directory_exists(input_file_path, True):  # Sends error and closes connection
                    out_warning("Input path doesn't exist.")
                    out_debug("Input path = %s" % input_file_path)
                    break  # Connection has been closed.
                # Verify the output directory exists:
                if not check_file_or_directory_exists(output_dir_path, False):  # Sens error and closes connection
                    out_warning("Output directory doesn't exist.")
                    out_debug("Output dir = %s" % output_dir_path)
                    break  # Connection has been closed.
                # Do the split:
                out_info("Values validated, doing split.")
                common.status = "splitting"
                do_split(input_file_path, output_dir_path, command_obj['chunkSize'], command_obj['length'])
                common.status = "idle"
                out_info("Split finished.")
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
            elif command_obj['command'] == 'close':  # Close the connection.
                common.__close__()
                break

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
        6 = Failed to load the config file.
        7 = Shared working directory must be a string or doesn't exist. (Invalid config.)
        8 = Local working directory must be a string or doesn't exist. (Invalid config.)
        9 = IP address must be a string, or isn't a valid ip address. (Invalid config.)
        10 = Port to listen on must be an integer, or is out of range. (Invalid config.)
        11 = Shared secret must be a string, and at least 8 char long. (Invalid config.)
        12 = Is file host must be a boolean. (Invalid config.)        
        13 = Number of chunks must be an integer and either min 0 if file host, or min 1 if not. (Invalid config type.)
        14 = Failed to save config file.
        15 = Unable to find ffmpeg.
        16 = Failed to create local input working directory.
        17 = Failed to create local output working directory.
        18 = Failed to create shared input working directory.
        19 = Failed to create shared output working directory.
        20 = Failed to bind to address.


        23 = Error while trying to fork process.
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
    _args = parser.parse_args()

    # Set debug:
    common.DEBUG = _args.debug

    # Create and change to working directory:
    out_info("Changing to '.ClusterEncodeDaemon' directory.")
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
    if _args.configFile is not None:
        out_info("User provided config file.")
        if not os.path.exists(_args.configFile):
            out_error("Config file: '%s' doesn't exist." % _args.configFile)
            exit(3)
        if not os.path.isfile(_args.configFile):
            out_error("Config file: '%s' doesn't report as a file." % _args.configFile)
            exit(4)
        config_file_path = _args.configFile
    else:
        out_info("Using default config file.")
        config_file_path = default_config_file_path

    # Create the default config if it doesn't already exist:
    if config_file_path == default_config_file_path and not os.path.exists(config_file_path):
        out_debug("Default config doesn't exist, creating.")
        # Create the config object and set some default options:
        common.config = Config(config_file_path, do_load=False)
        common.config.local_working_dir = os.environ['HOME']
        common.config.shared_working_dir = os.environ['HOME']
        common.config.host = '192.168.1.123'
        common.config.port = 65500
        common.config.is_file_host = False
        common.config.num_chunks = 1
        try:
            common.config.save()
        except ConfigError as e:
            out_error("Failed to save default config: %s" % e.message)
            exit(5)

    # Load the config:
    out_info("Loading config.")
    try:
        common.config = Config(config_file_path)
    except ConfigError as e:
        out_error("Failed to load config: %s" % e.message)
        exit(6)

    # Override configs with command line options:
    if _args.sharedWorkingDir is not None:  # Shared working Directory:
        try:
            common.config.shared_working_dir = _args.sharedWorkingDir
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(7)

    if _args.localWorkingDir is not None:  # Local working directory:
        try:
            common.config.local_working_dir = _args.localWorkingDir
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(8)

    if _args.hostIP is not None:  # Listen IP:
        try:
            common.config.host = _args.hostIP
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(9)

    if _args.port is not None:  # Listen port:
        try:
            common.config.port = _args.port
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(10)

    if _args.sharedSecret is not None:  # Connection shared secret.
        try:
            common.config.shared_secret = _args.sharedSecret
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(11)

    if _args.isFileHost is not None:  # Is file host, NOTE: This must be set before num chunks.:
        try:
            common.config.is_file_host = _args.isFileHost
        except(TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(12)

    if _args.numChunks is not None:  # Number of chunks to process:
        try:
            common.config.num_chunks = _args.numChunks
        except (TypeError, ValueError) as e:
            out_error(e.args[0])
            exit(13)

    # If --saveConfig is selected, save config and exit:
    if _args.saveConfig is True:
        out_info("Saving config, and exiting.")
        try:
            common.config.save()
            exit(0)
        except ConfigError as e:
            out_error("Failed to write config: %s" % e.message)
            exit(14)
        # exit(0)

    # Find ffmpeg, and setup cli object:
    out_info("Locating ffmpeg.")
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        out_error("Unable to find ffmpeg.")
        exit(15)
    common.ffmpeg_cli = Ffmpegcli(ffmpeg_path)

    # Setup local working directory:
    out_info("Checking local working directory...")
    local_input_path: str = os.path.join(common.config.local_working_dir, 'Input')
    local_output_path: str = os.path.join(common.config.local_working_dir, 'Output')

    # Check for and create local working INPUT path:
    if not os.path.exists(local_input_path):
        out_warning("Local working input directory doesn't exist. Creating.")
        try:
            os.mkdir(local_input_path)
            out_info("Local input directory created.")
        except OSError as e:
            out_error("Failed to create local working input directory: %s[%d]" % (e.strerror, e.errno))
            exit(16)

    # Check for and create local OUTPUT directory:
    if not os.path.exists(local_output_path):
        out_warning("Local working output directory doesn't exist. Creating.")
        try:
            os.mkdir(local_output_path)
            out_info("Local output directory created.")
        except OSError as e:
            out_error("Failed to create local working output directory: %s[%d]." % (e.strerror, e.errno))
            exit(17)

    # If file host, setup shared directory:
    if common.config.is_file_host:
        out_info("Checking shared directory.")
        shared_input_path: str = os.path.join(common.config.shared_working_dir, 'Input')
        shared_output_path: str = os.path.join(common.config.shared_working_dir, 'Output')
        # Locate or create shared input dir:
        if not os.path.exists(shared_input_path):
            try:
                os.mkdir(shared_input_path)
                out_info("Shared input directory created.")
            except OSError as e:
                out_error("Failed to create shared input directory:  %s[%d]." % (e.strerror, e.errno))
                exit(18)
        if not os.path.exists(shared_output_path):
            try:
                os.mkdir(shared_output_path)
                out_info("Shared output directory created.")
            except OSError as e:
                out_error("Failed to create shared output directory: %s[%d]" % (e.strerror, e.errno))
                exit(19)

    # Create listener
    out_info("Connecting to socket.")
    passwd: bytes = common.config.shared_secret.encode()
    try:
        common.listener = Listener((common.config.host, common.config.port), authkey=passwd)
    except OSError as e:
        out_error("Failed to bind to socket: %s[%d]." % (e.strerror, e.errno))
        exit(20)
    out_info("Connected.")

    # Fork if requested:
    if _args.doFork is True:
        out_info("Detaching from terminal")
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
