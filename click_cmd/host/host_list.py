import click
import re
import copy
from lib.sshutils import *
# from lib.colors import *

from rich.console import Console
from rich.table import Table
from rich import box

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
    config = ctx.obj['CONFIG']

    #TODO: This will not work, since its filtering first, than later outputting to the output.
    #      Currently if filter cuts-out pattern, then inherited params will not be showed in list,
    #      which is not correct. Inherited parameters should be found first, then table output should
    #      be filtered.
    # filtered_config = []
    # for group in config:
    #     # If group filter is defined, check if current group matches the name to progress
    #     if group_filter:
    #         grmatch = re.search(group_filter, group["name"])
    #         if not grmatch:
    #             continue
        
    #     # When group is not skipped, check if name filter is used, and filter out groups
    #     if name_filter:
    #         # Make a new copy of group, so we dont mess original config
    #         # group_copy = copy.deepcopy(group)
    #         group_copy = group

    #         filtered_hosts = []
    #         filtered_patterns = []

    #         for host in group_copy["hosts"]:
    #             match = re.search(name_filter, host["name"])
    #             if match:
    #                 filtered_hosts.append(host)
    #         for pattern in group_copy["patterns"]:
    #             match = re.search(name_filter, pattern["name"])
    #             if match:
    #                 filtered_patterns.append(pattern)

    #         group_copy["hosts"] = filtered_hosts
    #         group_copy["patterns"] = filtered_patterns
    #         filtered_config.append(group_copy)
    #     else:
    #         filtered_config.append(group)

    # if not filtered_config:
    #     print("No host matching any filter!")
    #     exit(1)
    filtered_config = config

    # Generate flat list of all of all hosts
    # TODO: Move to sshutils?
    flat_config = []
    for group in config:
        for h in group["hosts"] + group["patterns"]:
            flat_config.append(h)

    DEFAULT_HEADER = ["name", "group", "type"]
    DEFAULT_PARAMS = ["hostname", "user"]

    # Find all possible params across all defined hosts
    params = [*DEFAULT_PARAMS]
    for host in flat_config:
        for key in host.params:
            if (not key in params):
                params.append(key)



    # pprint(params)
    ctx.exit()

    header = DEFAULT_HEADER + ["info"] + ([f"param:{p}" for p in params])
    x = PrettyTable(field_names=header)
    x.align = "l"
    
    # Generate rows
    for group in filtered_config:
        # Adding line for host
        for host in group["hosts"]:
            inherited = find_inherited_params(host["name"], config)
            host_info = "\n".join(host["info"])
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
                                        [yellow(f"{val}  ({pattern})") for val in key[applied_param]]
                                    ))
                                else:
                                    host_params.append(yellow(f"{key[applied_param]}  ({pattern})"))
                            else:
                                host_params.append("")
                    else:
                        host_params.append("")
            x.add_row([host["name"], group["name"], "normal", host_info] + host_params)
        # Adding line for pattern
        for pattern in group["patterns"]:
            pattern_params = []
            host_info = "\n".join(pattern["info"])
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
            x.add_row([cyan(pattern["name"]), cyan(group["name"]), cyan("pattern"), cyan(host_info)] + pattern_params)

    # Print table in normal or verbose mode
    print(x)
    # if verbose:
    #     print(x)
    # else:
    #     print(x.get_string(fields=DEFAULT_HEADER + [f"param:{i}" for i in DEFAULT_PARAMS]))
