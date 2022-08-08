import click
import re
import copy
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

#------------------------------------------------------------------------------
# COMMAND: host-list
#------------------------------------------------------------------------------
@click.command(name="list", help="List hosts")
@click.option("-g", "--group",  "group_filter", default=None,  help="Filter for group that host belongs to (regex)")
@click.option("-n", "--name",   "name_filter",  default=None,  help="Filter for host name (regex)")
@click.option("-v", "--verbose", is_flag=True,  default=False, help="Show verbose info (all parameters)")
@click.pass_context
def cmd(ctx, group_filter, name_filter, verbose):
    config: SSH_Config = ctx.obj

    # Filter out groups and hosts if filters are defined via CLI
    filtered_groups: list[SSH_Group] = []
    for group in config.groups:
        # If group filter is defined, check if current group matches the name to progress
        if group_filter:
            group_match = re.search(group_filter, group.name)
            if not group_match:
                continue
        
        # When group is not skipped, check if name filter is used, and filter out groups
        if name_filter:
            # Make a new copy of group, so we dont mess original config
            group_copy = copy.copy(group)
            group_copy.hosts = []
            group_copy.patterns = []
            include_group = False

            for host in group.hosts + group.patterns:
                match = re.search(name_filter, host.name)
                if match:
                    include_group = True
                    if host.type == "normal":
                        group_copy.hosts.append(host)
                    else:
                        group_copy.patterns.append(host)
            if include_group:
                filtered_groups.append(group_copy)
        else:
            filtered_groups.append(group)

    if not filtered_groups:
        print("No host is matching any given filter!")
        ctx.exit(1)
    
    # This lists define host properties and which parameters will be displayed
    host_props = ["name", "group", "type"]
    params     = ["hostname", "user"]

    # If output is verbose, we need to find all parameters, and add them to params list
    if verbose:
        flat_config: list[SSH_Host] = []
        for group in filtered_groups:
            for h in group.hosts + group.patterns:
                flat_config.append(h)
        for host in flat_config:
            for i_params in host.params:
                if (not i_params in params):
                    params.append(i_params)
    
    header = host_props + ([f"param:{p}" for p in params])
    table = Table(*header, box=box.SQUARE, style="gray35")

    # Start adding rows    
    for group in filtered_groups:
        # Iterate trough hosts and patters
        for host in group.hosts + group.patterns:
            inherited: list[tuple[str, dict]] = []
            if host.type == "normal":
                inherited = config.find_inherited_params(host.name)
            host_params = []
            # Go trough list of all params we know are available across current host list
            for table_param in params:
                if table_param in host.params:
                    # Handle direct params, and handle if its a list or string
                    if isinstance(host.params[table_param], list):
                        host_params.append("\n".join(host.params[table_param]))
                    else:
                        host_params.append(host.params[table_param])
                else:
                    # Handle inherited params (only valid for "normal" hosts)
                    if inherited:
                        for pattern, i_params in inherited:
                            if table_param in i_params:
                                if isinstance(i_params[table_param], list):
                                    table_param = "\n".join([f"{val}  ({pattern})" for val in i_params[table_param]])
                                    host_params.append(table_param)
                                else:
                                    host_params.append(f"[yellow]{i_params[table_param]}  ({pattern})[/]")
                            else:
                                host_params.append("")
                    else:
                        host_params.append("")
            row = [host.__dict__[prop] for prop in host_props] + host_params
            table.add_row(*row) if host.type == "normal" else table.add_row(*row, style="cyan")

    console.print(table)
