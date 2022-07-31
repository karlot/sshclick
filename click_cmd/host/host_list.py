import click
import re
import copy
from lib.sshutils import *

from rich.console import Console
from rich.table import Table
from rich import box
from rich.pretty import pprint

console = Console()

#TODO: Rework this list logic...
#------------------------------------------------------------------------------
# COMMAND: host-list
#------------------------------------------------------------------------------
@click.command(name="list", help="List hosts")
@click.option("-g", "--group",  "group_filter", default=None,  help="Filter for group that host belongs to (regex)")
@click.option("-n", "--name",   "name_filter",  default=None,  help="Filter for host name (regex)")
@click.option("-v", "--verbose", is_flag=True,  default=False, help="Show verbose info (all parameters)")
@click.pass_context
def cmd(ctx, group_filter, name_filter, verbose):
    config: SSH_Config = ctx.obj['CONFIG']

    #TODO: RE-Check if this still works
    filtered_groups = []
    for group in config.groups:
        # If group filter is defined, check if current group matches the name to progress
        if group_filter:
            group_match = re.search(group_filter, group.name)
            if not group_match:
                continue
        
        # When group is not skipped, check if name filter is used, and filter out groups
        if name_filter:
            # Make a new copy of group, so we dont mess original config
            group_copy = copy.deepcopy(group)

            filtered_hosts = []
            filtered_patterns = []

            for host in group_copy.hosts:
                match = re.search(name_filter, host.name)
                if match:
                    filtered_hosts.append(host)
            for pattern in group_copy.patterns:
                match = re.search(name_filter, pattern.name)
                if match:
                    filtered_patterns.append(pattern)

            group_copy.hosts = filtered_hosts
            group_copy.patterns = filtered_patterns
            filtered_groups.append(group_copy)
        else:
            filtered_groups.append(group)

    if not filtered_groups:
        print("No host is matching any given filter!")
        ctx.exit(1)

    # Generate flat list of all of all hosts
    # TODO: Move to sshutils? Or as method on config itself?
    flat_config = []
    for group in config.groups:
        for h in group.hosts + group.patterns:
            flat_config.append(h)

    DEFAULT_HEADER = ["name", "group", "type"]
    DEFAULT_PARAMS = ["hostname", "user"]

    # Find all possible params across all showed hosts
    params = [*DEFAULT_PARAMS]
    for host in flat_config:
        for key in host.params:
            if (not key in params):
                params.append(key)
    
    header = DEFAULT_HEADER + ([f"param:{p}" for p in params])
    table = Table(*header, box=box.SQUARE)
    
    # Generate rows
    for group in filtered_groups:
        # Adding line for host
        for host in group.hosts:
            inherited = config.find_inherited_params(host.name)
            host_params = []
            # Go trough list of all params we know are available across current host list
            # for current host we need to combine local and inherited params to fill table row
            for applied_param in params:
                if applied_param in host:
                    # Handle direct params, and handle if its a list or string
                    if isinstance(host[applied_param], list):
                        host_params.append("\n".join(host[applied_param]))
                    else:
                        host_params.append(host[applied_param])
                else:
                    # Handle inherited params
                    if inherited:
                        for pattern, key in inherited.items():
                            if applied_param in key:
                                if isinstance(key[applied_param], list):
                                    host_params.append("\n".join(
                                        [f"{val}  ({pattern})" for val in key[applied_param]]
                                    ))
                                else:
                                    host_params.append(yellow(f"{key[applied_param]}  ({pattern})"))
                            else:
                                host_params.append("")
                    else:
                        host_params.append("")
            x.add_row([host["name"], group["name"], "normal"] + host_params)
        # Adding line for pattern
        for pattern in group["patterns"]:
            pattern_params = []
            for p in params:
                if p in pattern:
                    # Handle direct params
                    if isinstance(pattern[p], list):
                        pattern_params.append("\n".join(
                            [cyan(val) for val in pattern[p]]
                        ))
                    else:
                        pattern_params.append(cyan(pattern[p]))
                else:
                    pattern_params.append("")
            # Add to table with color to be easily distinguished
            x.add_row([cyan(pattern["name"]), cyan(group["name"]), cyan("pattern")] + pattern_params)

    console.print(table)

    # Print table in normal or verbose mode
    # if verbose:
    #     print(x)
    # else:
    #     print(x.get_string(fields=DEFAULT_HEADER + [f"param:{i}" for i in DEFAULT_PARAMS]))
