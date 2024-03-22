#!/usr/bin/env python3
"""
    File: main.py
"""
import argparse
import json
import os
import shutil
from typing import Final

import gi

import common
from SignalHandlers import SignalHandlers

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio, GLib, GObject

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
        print("Failed to create working directory: %s[%d]." % (e.strerror, e.errno))
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
            file_handle.write(json.dumps(common.config, indent=4))
    except OSError as e:
        print("Failed to write config file: %s[%d]." % (e.strerror, e.errno))
        exit(12)


if __name__ == '__main__':
    description = """
    ClusterEncoderGui:
    The gui to manage an encode process.
    
    Exit Codes: 1 -> failed to create local working directory.
                10 -> Failed to open config file.
                11 -> Failed to load config JSON.
                12 -> Failed to write config file.
    """
    parser = argparse.ArgumentParser(description=description,
                                     epilog="Written by Peter Nearing.")

    parser.add_argument('--configFile',
                        help="The full path to the config file to use. Default=$HOME/.ClusterEncode/config.json",
                        type=str)

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

    ffmpeg_path: str = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        print("ffmpeg not installed. Please install with 'sudo apt install ffmpeg'.")
        exit()

    # Create GUI:
    builder.add_from_file("ClusterEncode.glade")


    # Connect GUI signals:
    builder.connect_signals(SignalHandlers(builder))

    # Set input/ output / shared directory for the file chooser buttons:
    shared_path = common.config['sharedDir']
    output_path = common.config['outputDir']
    input_file_object: Gtk.FileChooserWidget = builder.get_object("fbtn_input_file")
    shared_dir_object: Gtk.FileChooserWidget = builder.get_object("fbtn_shared_directory")
    output_dir_object: Gtk.FileChooserWidget = builder.get_object("fbtn_output_directory")
    input_file_object.set_current_folder(shared_path)
    shared_dir_object.set_current_folder(shared_path)
    output_dir_object.set_current_folder(output_path)

    # Create a list store for the audio encoders.
    lst_store_audio_encoders: Gtk.ListStore = Gtk.ListStore.new(types=(str, str))
    lst_store_audio_encoders.append(('mp3', 'mp3 audio'))
    combo_audio_encoders: Gtk.ComboBox = builder.get_object('cmb_output_audio_encoder')
    combo_audio_encoders.set_model(lst_store_audio_encoders)


    # Get and show the window:
    window: Gtk.ApplicationWindow = builder.get_object("app_window")
    window.show_all()
    # Main loop:
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

    exit(0)
