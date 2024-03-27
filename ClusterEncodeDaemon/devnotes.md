Daemon exit codes:
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
        22 = Error while trying to fork process.
        30 = Error while sending data.
        31 = Error while receiving data.

Protocol Version 1.0.0 error numbers and their messages:

            1, "Invalid command object type. NOT A DICT."
            2, "No 'version' key in command object."
            3, "Version key is of wrong type, not a string."
            4, "Un-supported version."
            5, "No 'command' key found in command object."
            6, "Invalid command type, not a string."
            7, "Command is invalid, not in valid_commands."
            20, "Required parameter doesn't exist. More info in error message."
            21, "Required parameter is wrong type. More info in error message."
            30, "File or directory doesn't exist. More infor in error message."
            31, "path isn't a file. More info in error message."
            32, "path isn't a directory. More info in error message."
