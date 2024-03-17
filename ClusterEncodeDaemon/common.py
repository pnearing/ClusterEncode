#!/usr/bin/env python3
"""
    File: common.py
"""
from typing import Any

config: dict[str, Any] = {
    # Directory settings:
    'sharedWorkingDir': '/mnt/convert/',
    'localWorkingDir': '/home/user/convert/',
    # Connection settings:
    'host': '192.168.1.123',
    'port': 65500,
    'sharedSecret': 'asdlkalskddjasldk',
    # Daemon configs:
    'numChunks': 2,
    'isFileHost': False,
}
"""The daemon config."""
DEBUG: bool = False
"""Should the daemon produce debug output."""

if __name__ == '__main__':
    exit(0)
