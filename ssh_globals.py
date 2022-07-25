import os

VERSION = "0.3.1"

DEBUG = False

# Setup defaults
DEFAULT_USER_CONF = f"{os.environ['HOME']}/.ssh/config"
DEFAULT_GROUP_NAME = "default"
DEFAULT_STDOUT = False

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]
