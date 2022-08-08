import os.path

VERSION = "0.4.4"

# Setup defaults
DEFAULT_USER_CONF = os.path.expanduser("~/.ssh/config")
DEFAULT_GROUP_NAME = "default"
DEFAULT_STDOUT = False

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]
