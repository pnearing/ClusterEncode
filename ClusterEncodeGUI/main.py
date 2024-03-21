#!/usr/bin/env python3
"""
    File: main.py
"""
import json
import os
from typing import Optional, Final

import common
from SignalHandlers import SignalHandlers

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import Gio
from pymediainfo import MediaInfo

# Consts:
WORKING_DIR_NAME: Final[str] = '.ClusterEncode'
CONFIG_FILE_NAME: Final[str] = 'config.json'
# Global vars:
builder: Gtk.Builder = Gtk.Builder()


def create_working_directory():
    """
    Create the local working directory for the parent application.
    :return: None
    """
    try:
        os.mkdir(common.working_dir)
    except OSError as e:
        print("Failed to create working directory '%s': %s[%d]." % (common.working_dir, e.strerror, e.errno))
        exit(1)
    return


def load_config():
    """
    Load the config file JSON.
    :return:
    """
    try:
        with open(common.config_path, 'r') as file_handle:
            config = json.loads(file_handle.read())
    except OSError as e:
        print("Failed to open config file '%s': %s[%d]." % (common.config_path, e.strerror, e.errno))
        exit(10)
    except json.JSONDecodeError as e:
        print("Failed to load config JSON: %s." % e.msg)
        exit(11)
    return


def create_default_config():
    common.config['shared_dir'] = os.path.join(common.working_dir, 'Working')
    common.config['output_dir'] = os.environ['HOME']
    common.config['hosts'] = {}
    try:
        with open(common.config_path, 'w') as file_handle:
            file_handle.write(json.dumps(common.config))
    except OSError as e:
        print("Failed to write config file: %s[%d]." % (e.strerror, e.errno))
        exit(12)


if __name__ == '__main__':
    # Create GUI:
    builder.add_from_file("ClusterEncode.glade")

    # Locate the local working directory, create it if required, and change to it:
    common.working_dir = os.path.join(os.environ['HOME'], WORKING_DIR_NAME)
    if not os.path.exists(common.working_dir):
        create_working_directory()
    os.chdir(common.working_dir)

    # Locate config, and load it, otherwise create it if it doesn't exist.
    common.config_path = os.path.join(common.working_dir, CONFIG_FILE_NAME)
    if os.path.exists(common.config_path):
        load_config()
    else:
        create_default_config()

    # Connect GUI signals:
    builder.connect_signals(SignalHandlers(builder))

    # Set input directory:
    shared_path = common.config['sharedDir']
    input_file_object = builder.get_object("fbtn_input_file")
    input_file_object.set_directory(shared_path)

    # Get and show the window:
    window = builder.get_object("app_window")
    window.show_all()
    # Main loop:
    Gtk.main()
