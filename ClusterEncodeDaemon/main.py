#!/usr/bin/env python3
"""
    File: main.py
"""
import argparse
import json
import os
from typing import Final
import common

# Consts:
WORKING_DIR_NAME: Final[str] = ".ClusterEncodeDaemon"
CONFIG_FILENAME: Final[str] = "config.json"

if __name__ == '__main__':
    description = """
    Cluster encode daemon process.
    Exit codes:
        1 = Failed to create working directory in HOME.
        2 = Working directory exists, but is not a directory.
        3 = Supplied config file path doesn't exist.
        4 = Supplied config file isn't a file.
        5 = Failed to create default config file.
    """
    # Command line arguments:
    parser = argparse.ArgumentParser(description=description,
                                     epilog="Written by Peter Nearing.")

    parser.add_argument('--noFork',
                        help="Do not fork the daemon.",
                        action='store_false',
                        dest='doFork',
                        default=True)

    parser.add_argument('--configFile',
                        help="The full path to the config file.",
                        type=str)

    args = parser.parse_args()

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
    if config_file_path == default_config_file_path and not os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'w') as file_handle:
                file_handle.write(json.dumps(common.config))
        except OSError as e:
            print("Failed to create default config file: '%s', %s[%d]." % (config_file_path, e.strerror, e.errno))
            exit(5)


    exit(0)
