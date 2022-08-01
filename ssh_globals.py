import os.path
import logging

VERSION = "0.4.0"

# Setup defaults
LOGGING_LEVEL = logging.INFO
DEFAULT_USER_CONF = os.path.expanduser("~/.ssh/config")
DEFAULT_GROUP_NAME = "default"
DEFAULT_STDOUT = False

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]
