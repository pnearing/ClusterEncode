#!/usr/bin/env python3
"""
    File: main.py
"""
import argparse
import json
import os
import shutil
import sys
from typing import Final, Optional

# Import GUI stuff:
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# Include my libs:
sys.path.append('../')
from ffmpegCli.Ffmpegcli import Ffmpegcli
import common
from SignalHandlers import SignalHandlers


# Consts:
WORKING_DIR_NAME: Final[str] = '.ClusterEncode'
CONFIG_FILE_NAME: Final[str] = 'config.json'
# Global vars:
common.builder = Gtk.Builder()


if __name__ == '__main__':
    description = """
    ClusterEncoderGUI:
    The gui to manage an encode process.
    
    Exit Codes: 1 -> Failed to create local working directory.
                2 -> Provided config file doesn't exist.
                3 -> Failed to write default config.
                4 -> Failed to open config file for reading.
                5 -> Failed to load JSON from config file.
                6 -> Provided shared directory doesn't exist.
                7 -> Provided shared directory isn't a directory.
                8 -> Provided output directory doesn't exist.
                9 -> Provided output directory isn't a directory.
                10 -> Failed to open config file for writing.
                11 -> Failed to locate ffmpeg.
                12 -> Failed to get audio encoder list from ffmpeg.
                13 -> Failed to get video encoder list from ffmpeg.
    """
    parser = argparse.ArgumentParser(description=description,
                                     epilog="Written by Peter Nearing.")

    parser.add_argument('--configFile',
                        help="The full path to the config file to use. Default=$HOME/.ClusterEncode/config.json",
                        type=str)
    parser.add_argument('--sharedDir',
                        help="The full path to the shared directory. IE: /mnt/convert/",
                        type=str)
    parser.add_argument('--outputDir',
                        help="The full path to the final output directory. IE: /mnt/convert/Output/",
                        type=str)
    parser.add_argument('--saveConfig',
                        help="Save the config file.",
                        action='store_true',
                        default=False)

    args = parser.parse_args()

    # Create GUI, do this before we change directories :
    common.builder.add_from_file("ClusterEncode.glade")

    # Locate the local working directory, create it if required, and change to it:
    common.working_dir = os.path.join(os.environ['HOME'], WORKING_DIR_NAME)
    if not os.path.exists(common.working_dir):
        try:
            os.mkdir(common.working_dir)
        except OSError as e:
            print("Failed to create working directory: %s[%d]." % (e.strerror, e.errno))
            exit(1)
    os.chdir(common.working_dir)

    # Determine what config file we're going to use:
    default_config_path: str = os.path.join(common.working_dir, CONFIG_FILE_NAME)
    common.config_path = default_config_path
    if args.configFile is not None:
        common.config_path = args.configFile

    # Locate the config file, if it's the default and it doesn't exist, create it.
    if not os.path.exists(common.config_path):
        if common.config_path != default_config_path:
            print("Failed to locate config file: %s." % common.config_path)
            exit(2)
        else:
            # Set default GUI config:
            common.config['sharedDir'] = os.environ['HOME']
            common.config['outputDir'] = os.environ['HOME']
            common.config['hosts'] = {}
            # Write the config to the default config pathfile:
            try:
                with open(common.config_path, 'w') as file_handle:
                    file_handle.write(json.dumps(common.config, indent=4))
            except OSError as e:
                print("Failed to open default config for writing: %s[%d]." % (e.strerror, e.errno))
                exit(3)

    # Load the config:
    try:
        with open(common.config_path, 'r') as file_handle:
            common.config = json.loads(file_handle.read())
    except OSError as e:
        print("Failed to open config file for reading: %s[%d]" % (e.strerror, e.errno))
        exit(4)
    except json.JSONDecodeError as e:
        print("Failed to load JSON from config file: %s" % e.msg)
        exit(5)

    # Process argument overrides:
    if args.sharedDir is not None:  # Shared directory config:
        if not os.path.exists(args.sharedDir):
            print("Shared directory '%s' doesn't exist." % args.sharedDir)
            exit(6)
        elif not os.path.isdir(args.sharedDir):
            print("Shared directory '%s' isn't a directory." % args.sharedDir)
            exit(7)
        common.config['sharedDir'] = args.sharedDir

    if args.outputDir is not None:
        if not os.path.exists(args.outputDir):
            print("Output directory '%s' doesn't exist." % args.outputDir)
            exit(8)
        elif not os.path.isdir(args.outputDir):
            print("Output directory '%s' isn't a directory." % args.outputDir)
            exit(9)
        common.config['outputDir'] = args.outputDir

    # Save config if requested:
    if args.saveConfig is True:
        common.save_config()  # Exit's 10 on failure.

    # Find ffmpeg path, and set common ffmpeg instance:
    ffmpeg_path: str = shutil.which('ffmpeg')
    if ffmpeg_path is None:
        print("ffmpeg not installed. Please install with 'sudo apt install ffmpeg'.")
        exit(11)
    common.ffpmeg_cli = Ffmpegcli(ffmpeg_path)

    # Connect GUI signals:
    common.builder.connect_signals(SignalHandlers())

    # Set input/ output / shared directory for the file chooser buttons:
    input_file_object: Gtk.FileChooserWidget = common.builder.get_object("fbtn_input_file")
    shared_dir_object: Gtk.FileChooserWidget = common.builder.get_object("fbtn_shared_directory")
    output_dir_object: Gtk.FileChooserWidget = common.builder.get_object("fbtn_output_directory")
    input_file_object.set_current_folder(common.config['sharedDir'])
    shared_dir_object.set_current_folder(common.config['sharedDir'])
    output_dir_object.set_current_folder(common.config['outputDir'])

    # Create a list store for the audio encoders.
    lst_store_audio_encoders: Gtk.ListStore = Gtk.ListStore.new(types=(str, str))
    audio_encoders: Optional[list[tuple[str, str]]] = common.ffpmeg_cli.get_audio_encoders()
    if audio_encoders is None:
        print("Failed to get list of audio encoders from ffmpeg.")
        exit(12)
    mp3_idx: Optional[int] = None
    for i, data in enumerate(audio_encoders):
        encoder, description = data
        if encoder == 'libmp3lame':
            mp3_idx = i
        lst_store_audio_encoders.append((encoder, description))

    # Set the audio encoders combo box model:
    combo_audio_encoders: Gtk.ComboBox = common.builder.get_object('cmb_output_audio_encoder')
    combo_audio_encoders.set_model(lst_store_audio_encoders)
    if mp3_idx is not None:
        combo_audio_encoders.set_active(mp3_idx)
    else:
        combo_audio_encoders.set_active(0)

    # Create a list store for the video encoders:
    lst_store_video_encoders: Gtk.ListStore = Gtk.ListStore.new(types=(str, str))
    video_encoders: Optional[list[tuple[str, str]]] = common.ffpmeg_cli.get_video_encoders()
    if video_encoders is None:
        print("Failed to get a list of video encoders from ffmpeg.")
        exit(13)
    x265_idx: Optional[int] = None
    for i, data in enumerate(video_encoders):
        encoder, description = data
        if encoder == 'libx265':
            x265_idx = i
        lst_store_video_encoders.append(row=(encoder, description))

    # Set the video encoders combo box model:
    combo_video_encoders: Gtk.ComboBox = common.builder.get_object('cmb_output_video_encoder')
    combo_video_encoders.set_model(lst_store_video_encoders)
    if x265_idx is not None:
        combo_video_encoders.set_active(x265_idx)
    else:
        combo_video_encoders.set_active(0)

    # Set the scale width / height to reasonable values:
    spin_video_width: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_width')
    spin_video_height: Gtk.SpinButton = common.builder.get_object('sbtn_output_video_height')
    spin_video_width.set_value(1920)
    spin_video_height.set_value(1080)

    # Get and show the window:
    window: Gtk.ApplicationWindow = common.builder.get_object("app_window")
    window.show_all()
    # Main loop:
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass

    exit(0)
