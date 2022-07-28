import os
import logging

VERSION = "0.3.1"

# DEBUG = False
LOGGING_LEVEL = logging.INFO
# LOGGING_LEVEL = logging.DEBUG

# Setup defaults
DEFAULT_USER_CONF = f"{os.environ['HOME']}/.ssh/config"
DEFAULT_GROUP_NAME = "default"
DEFAULT_STDOUT = True

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
    "test",
]
