#!/usr/bin/env python3
"""
    Name:Config.py
    Description: Store the config, and its save / load functions:
"""
import ipaddress
import json
import os.path
from typing import Optional, Any, TextIO, Final

_CONFIG_KEYS: Final[tuple[tuple[str, type], ...]] = (
    ('sharedWorkingDir', str), ('localWorkingDir', str), ('host', str), ('port', int), ('sharedSecret', str),
    ('numChunks', int), ('isFileHost', bool)
)
"""Configuration keys and their types."""


###################################################################
# Config Exception
class ConfigError(Exception):
    """
    Exception to throw on error with the config.
    """
    def __init__(self,
                 message: str,
                 error_num: int,
                 exception: Optional[Exception] = None
                 ) -> None:
        self._message: str = message
        self._error_num: int = error_num
        self._exception: Optional[Exception] = exception
        return

    @property
    def message(self) -> str:
        return self._message

    @property
    def error_num(self) -> int:
        return self._error_num

    @property
    def exception(self) -> Optional[Exception]:
        return self._exception


#######################################################################
# Config class:
class Config(object):
    """
    Class to store config file stuff.
    """
    def __init__(self, file_path: str, do_load: bool = True) -> None:
        if not os.path.exists(file_path) and do_load:
            raise ConfigError("Config file not found.", 1)
        elif not os.path.isfile(file_path) and do_load:
            raise ConfigError("Config file is not a file.", error_num=2)
        self._file_path: str = file_path
        self._config: dict[str, Any] = {}
        if do_load:
            self.load()
            self.verify()
        return

    def load(self) -> None:
        """
        Loads the config file.
        :return: None
        :raises ConfigFileError: On error [opening |reading | loading JSON from] the file.
        """
        # Open the file, and read its contents:
        try:
            with open(self._file_path, 'r') as file_handle:
                file_contents: list[str] = file_handle.readlines()
        except OSError as e:
            raise ConfigError("Failed to open config file for reading.", 3, e)

        # Remove any lines that start with '#':
        temp_config: list[str] = []
        for line in file_contents:
            if not line.startswith('#'):
                temp_config.append(line)
        json_config: str = ''.join(temp_config)

        # Load the config:
        try:
            self._config = json.loads(json_config)
        except json.JSONDecodeError as e:
            raise ConfigError("Failed to load config file JSON.", 4, e)
        return

    def verify(self) -> None:
        """
        Verify the config.
        :return: None
        :raises ConfigError: On invalid key | key type.
        """
        for key_data in _CONFIG_KEYS:
            key, key_type = key_data
            if key not in self._config.keys():
                raise ConfigError("Key '%s' not found." % key, 7)
            if not isinstance(self._config[key], key_type):
                raise ConfigError("Key '%s' not proper type '%s'." % (key, str(key_type)), 8)
        return

    def save(self) -> None:
        """
        Save the current config to the file.
        :return: None
        :raises ConfigFileError: On error [opening | encoding to JSON | writing to] the file.
        """
        # Open the file:
        try:
            file_handle: TextIO = open(self._file_path, 'w')
        except OSError as e:
            raise ConfigError("Failed to open file for writing.", 5, e)
        # Convert the config to JSON and write it to the file:
        try:
            file_handle.write(json.dumps(self._config, indent=4))
        except ValueError as e:
            raise ConfigError("Failed to encode config into JSON.", 6, e)
        file_handle.close()
        return

    ###################################################
    # Config properties:
    @property
    def shared_working_dir(self) -> str:
        return self._config['sharedWorkingDir']

    @shared_working_dir.setter
    def shared_working_dir(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("shared working directory expected str type.")
        if not os.path.exists(value):
            raise ValueError("shared working directory doesn't exist.")
        if not os.path.isdir(value):
            raise ValueError("shared working directory doesn't report as a directory.")
        self._config['sharedWorkingDir'] = value
        return

    @property
    def local_working_dir(self) -> str:
        return self._config['localWorkingDir']

    @local_working_dir.setter
    def local_working_dir(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("local working directory expected type str.")
        if not os.path.exists(value):
            raise ValueError("local working directory doesn't exist.")
        if not os.path.isdir(value):
            raise ValueError("local working directory doesn't report as a directory.")
        self._config['localWorkingDir'] = value
        return

    @property
    def host(self) -> str:
        return self._config['host']

    @host.setter
    def host(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("host expected type str.")
        try:
            _ = ipaddress.ip_address(value)  # Raises ValueError.
        except ValueError:
            raise ValueError("host must be a valid ip address.")
        self._config['host'] = value
        return

    @property
    def port(self) -> int:
        return self._config['port']

    @port.setter
    def port(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("port expected type int.")
        if value < 1025 or value > 65535:
            raise ValueError("port value out of range. 1025->65535, inclusive.")
        self._config['port'] = value
        return

    @property
    def shared_secret(self) -> str:
        return self._config['sharedSecret']

    @shared_secret.setter
    def shared_secret(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("shared secret expected type str.")
        if len(value) < 8:
            raise ValueError("shared secret must be at least 8 chars.")
        self._config['sharedSecret'] = value
        return

    @property
    def is_file_host(self) -> bool:
        return self._config['isFileHost']

    @is_file_host.setter
    def is_file_host(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError("is file host expected type bool.")
        self._config['isFileHost'] = value
        return

    @property
    def min_num_chunks(self) -> int:
        if self.is_file_host:
            return 0
        return 1

    @property
    def num_chunks(self) -> int:
        return self._config['numChunks']

    @num_chunks.setter
    def num_chunks(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("num chunks expected type int.")
        if value < self.min_num_chunks:
            raise ValueError("num chunks must be min 1 if not the file host, if this is the file host, min value is 0.")
        self._config['numChunks'] = value
        return


##########################################################################
# Config Test:
if __name__ == '__main__':
    exit(0)
