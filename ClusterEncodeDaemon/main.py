#!/usr/bin/env python3
"""
    File: main.py
"""
import argparse
import ipaddress
import json
import os
from typing import Final, Any
from multiprocessing.connection import Listener, Connection
from multiprocessing import AuthenticationError
import common

# Consts:
WORKING_DIR_NAME: Final[str] = ".ClusterEncodeDaemon"
CONFIG_FILENAME: Final[str] = "config.json"


def main() -> None:
    # Create listener
    passwd = common.config['sharedSecret'].encode()
    listener = Listener((common.config['host'], common.config['port']), authkey=passwd)
    running = True
    while running:
        # Accept a connection:
        try:
            connection: Connection = listener.accept()
        except AuthenticationError:
            continue
        except ConnectionResetError:
            continue

        # Receive the command and check that it's a dict, if not, close the connection and wait for another:
        command_obj: dict[str, Any] = connection.recv()
        if not isinstance(command_obj, dict):
            connection.close()
            continue
        # Make sure there is a command in the command object, if not close the connection and wait for another:
        if 'command' not in command_obj.keys():
            connection.close()
            continue


    return


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
        21 = Error while trying to fork process.
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
    working_dir_path = os.path.join(os.environ['HOME'], WORKING_DIR_NAME)
    if not os.path.exists(working_dir_path):
        try:
            os.mkdir(working_dir_path)
        except OSError as e:
            print("Failed to create default data directory '%s': %s[%d]" % (working_dir_path, e.strerror, e.errno))
            exit(1)
    if not os.path.isdir(working_dir_path):
        print("Error: Working directory is a regular file: %s" % working_dir_path)
        exit(2)
    os.chdir(working_dir_path)

    # Set the default config file path, and select the config file path to use:
    default_config_file_path = os.path.join(working_dir_path, CONFIG_FILENAME)
    if args.configFile is not None:
        if not os.path.exists(args.configFile):
            print("Config file: '%s' doesn't exist." % args.configFile)
            exit(3)
        if not os.path.isfile(args.configFile):
            print("Config file: '%s' doesn't report as a file." % args.configFile)
            exit(4)
        config_file_path = args.configFile
    else:
        config_file_path = default_config_file_path

    # Create the default config if it doesn't already exist:
    if config_file_path == default_config_file_path and not os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'w') as file_handle:
                file_handle.write(json.dumps(common.config, indent=4))
        except OSError as e:
            print("Failed to create default config file: '%s', %s[%d]." % (config_file_path, e.strerror, e.errno))
            exit(5)

    # Load the config:
    try:
        with open(config_file_path, 'r') as file_handle:
            common.config = json.loads(file_handle.read())
    except OSError as e:
        print("Failed to load config file '%s': %s[%d]" % (config_file_path, e.strerror, e.errno))
        exit(6)
    except json.JSONDecodeError as e:
        print("Failed to decode JSON from config file '%s': %s." % (config_file_path, e.msg))
        exit(7)

    # Override configs with command line options:
    if args.sharedWorkingDir is not None:  # Shared working Directory:
        common.config['sharedWorkingDir'] = args.sharedWorkingDirectory
    if not isinstance(common.config['sharedWorkingDir'], str):
        print("Shared working directory must be a string.")
        exit(8)
    if not os.path.exists(common.config['sharedWorkingDir']):
        print("Provided shared working directory doesn't exist.")
        exit(9)

    if args.localWorkingDir is not None:  # Local working directory:
        common.config['localWorkingDir'] = args.localWorkingDir
    if not isinstance(common.config['localWorkingDir'], str):
        print("Provided local working directory must be a string.")
        exit(10)
    if not os.path.exists(common.config['localWorkingDir']):
        print("Provided local working directory doesn't exist.")
        exit(11)

    if args.hostIP is not None:  # Listen IP:
        common.config['host'] = args.hostIP
    if not isinstance(common.config['host'], str):
        print("Provided host IP must be a string.")
        exit(12)
    try:
        _ = ipaddress.ip_address(common.config['host'])
    except ValueError as e:
        print("Provided host IP isn't an IP address.")
        exit(13)

    if args.port is not None:  # Listen port:
        common.config['port'] = args.port
    if not isinstance(common.config['port'], int):
        print("Provided port must be an integer.")
        exit(14)
    if common.config['port'] <= 0 or common.config['port'] > 65535:
        print("Invalid port provided.")
        exit(15)

    if args.sharedSecret is not None:  # Connection shared secret.
        common.config['sharedSecret'] = args.sharedSecret
    if not isinstance(common.config['sharedSecret'], str):
        print("Provided shared secret is not a string.")
        exit(16)
    if len(common.config['sharedSecret']) < 8:
        print("Shared secret too short. (< 8 char.)")
        exit(17)

    if args.numChunks is not None:  # Number of chunks to process:
        common.config['numChunks'] = args.numChunks
    if not isinstance(common.config['numChunks'], int):
        print("Provided numChunks must be an integer.")
        exit(18)
    if common.config['numChunks'] < 0:
        print("Number of chunks must be greater than or equal to 0.")
        exit(19)

    if args.isFileHost is not None:  # Is file host:
        common.config['isFileHost'] = args.isFileHost
    if not isinstance(common.config['isFileHost'], bool):
        print("Config 'isFileHost' must be a boolean.")
        exit(20)

    # If --saveConfig is selected, save config and exit:
    if args.saveConfig is True:
        try:
            with open(config_file_path, 'w') as file_handle:
                file_handle.write(json.dumps(common.config, indent=4))
        except OSError as e:
            print("Failed to write config: %s[%d]." % (e.strerror, e.errno))
            exit(21)

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
            print("Got error while trying to fork: %s[%d]" % (e.strerror, e.errno))
            exit(22)

    # Run main:
    main()

    # Exit gracefully:
    exit(0)
