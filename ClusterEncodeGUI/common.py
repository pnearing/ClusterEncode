#!/usr/bin/env python3
"""
    File: common.py
"""
from typing import Any

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
"""The custer encode config dict."""

if __name__ == '__main__':
    exit(0)
