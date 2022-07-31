from dataclasses import dataclass, field
from ssh_globals import *
from lib.ssh_host import SSH_Host
from lib.ssh_group import SSH_Group
from lib.ssh_config import SSH_Config


# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d: dict, ignored: list = []) -> dict:
    return {k: v for (k, v) in d.items() if k not in ignored}

