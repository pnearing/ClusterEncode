#!/usr/bin/env python3
"""
    File: common.py
"""
import sys
import json
from typing import Any, Final
from gi.repository import Gtk
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
builder: Gtk.Builder
"""The common Gtk.Builder object."""
ffpmeg_cli: Ffmpegcli

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
