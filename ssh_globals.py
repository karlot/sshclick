import os

VERSION = "0.2.0"
DEBUG = False

DEFAULT_GROUP_NAME = "default"
# BACKUP_CONFIG_FILE = True
# BACKUP_COPIES = 10

# Setup defaults for local path ssh config
USER_CONF_FILE = f"{os.environ['HOME']}/.ssh/config"
STDOUT_CONF = True

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]
