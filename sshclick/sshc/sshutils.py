import os.path
import re
from typing import List

from ..globals import ENABLED_HOST_STYLES
from .ssh_parameters import ALL_PARAM_LC_NAMES
from .ssh_config import SSH_Config, SSH_Host

from rich.console import Console
err = Console(stderr=True)


# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d: dict, ignored: list = []) -> dict:
    return {k: v for (k, v) in d.items() if k not in ignored}


# Custom parsing trough parent object types until required parameters are found
# Then build config object and bound it to ctx.obj
def build_context_config(ctx) -> None:
    if ctx.obj is None:
        current_obj = ctx.parent
        try:
            while True:
                if "sshconfig" in current_obj.params:
                    full_path = os.path.expanduser(current_obj.params["sshconfig"])
                    ctx.obj = SSH_Config(
                        file=full_path,
                        stdout=current_obj.params["stdout"]
                    ).read().parse()
                    break
                else:
                    current_obj = current_obj.parent
        except:
            err.print("INTERNAL ERROR: Could not reconstruct context for SSH configuration!")
            ctx.exit(1)


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_host_names(ctx, param, incomplete) -> List[str]:
    build_context_config(ctx)
    all_hosts = ctx.obj.get_all_host_names()
    return [k for k in all_hosts if k.startswith(incomplete)]


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_group_names(ctx, param, incomplete) -> List[str]:
    build_context_config(ctx)
    all_groups = ctx.obj.get_all_group_names()
    return [k for k in all_groups if k.startswith(incomplete)]


def complete_params(ctx, param, incomplete) -> List[str]:
    return [k for k in ALL_PARAM_LC_NAMES if k.startswith(incomplete)]


def complete_styles(ctx, param, incomplete) -> List[str]:
    return [k for k in ENABLED_HOST_STYLES if k.startswith(incomplete)]


# We use this functions to give a tuple of group/host names as input, where some names
# can be regexps (with "r:"" prefix), and we evaluate regex based on "all_names" list
# which we use to create a set of expanded host names; direct ones, and expanded ones from
# regex processing. Then return final list...
def expand_names(names: tuple, all_names: list) -> List[str]:
    selected = set()

    for name in names:
        if name.startswith("r:"):
            name_re = name.split(":")[1]
            # print(f"Got regex type name def - '{name_re}'")
            for i_name in all_names:
                match = re.search(name_re, i_name)
                if match:
                    selected.add(i_name)
        else:
            selected.add(name)
    return list(selected)


# Function to trace connected hosts via "proxyjump" SSH parameter
# For target host, return a list of hosts in order of connections to reach the target host
# In case host is directly reachable (no "proxyjump" param), it will return list of single (target) host
def trace_jumphosts(name: str, config: SSH_Config, ctx, style: str) -> List[SSH_Host]:

    # Keep list of linked hosts via proxyjump option
    traced_hosts: List[SSH_Host] = []

    # we are first checking host that is asked, and then check if that host has a "proxy" defined
    # if proxy is defined, we add found host to traced list, and search attached proxy, it this way we
    # can trace full connection path for later graph processing
    while True:
        # Search for host in current configuration
        if (not config.check_host_by_name(name)):
            print(f"Cannot get info for used host '{name}' as it is not defined in configuration!")
            ctx.exit(1)

        found_host = config.get_host_by_name(name)[0]

        # Set SSH host print style from user input
        found_host.print_style = style

        # Add current host, and its table to traced lists
        traced_hosts.append(found_host)

        # Find proxy info if it exists, if not, break the loop
        proxyjump = None
        if "proxyjump" in found_host.params:
            proxyjump = found_host.params["proxyjump"]
        else:
            for _, params in found_host.inherited_params:
                for key, value in params.items():
                    if key == "proxyjump":
                        proxyjump = value

        # If there is connected host, we switch "name" and continue the loop
        # Otherwise we exit the loop
        if proxyjump:
            name = proxyjump
        else:
            break
    
    return traced_hosts
