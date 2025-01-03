import click
from typing import List
from sshclick.sshc import SSH_Config, SSH_Host, HostType

from rich.console import Console
from rich.table import Table
from rich import box
console = Console()

#------------------------------------------------------------------------------
# COMMAND: host-list
#------------------------------------------------------------------------------
SHORT_HELP = "List configured hosts"
LONG_HELP  = """
List hosts from current configuration

Command allows displaying hosts with various properties, and filtering output list for easier searching.
SSHC will display also usually not visible "INHERITANCE" of parameters trough "PATTERNS", and from
which pattern parameter for given host would be applied (inherited).

Normal output will try to show only most important information about listed hosts, while if requested,
VERBOSE option will try to show ALL defined/inherited parameters for all listed hosts.
Alternatively for details on only single host, use "sshc host show" command.

Host list can be limited with filters, to only show specific hosts that match NAME regex or GROUP regex.
When both NAME and GROUP regex are defined, output must satisfy both filters.
"""

# Parameters help:
GROUP_HELP   = "Filter for host groups (regex)"
NAME_HELP    = "Filter for host names (regex)"
VERBOSE_HELP = "Show verbose info (all parameters)"
#------------------------------------------------------------------------------

@click.command(name="list", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-g", "--group",  "group_filter", help=GROUP_HELP)
@click.option("-n", "--name",   "name_filter",  help=NAME_HELP)
@click.option("-v", "--verbose", is_flag=True,  help=VERBOSE_HELP)
@click.pass_context
def cmd(ctx, group_filter, name_filter, verbose):
    config: SSH_Config = ctx.obj

    # Filter out groups and hosts if filters are defined via CLI
    filtered_groups = config.filter_config(group_filter, name_filter)

    if not filtered_groups:
        print("No host is matching any given filter!")
        ctx.exit(1)
    
    # This lists define host properties and which parameters will be displayed
    host_props = ["group", "type"]
    params     = ["hostname", "user"]

    # If output is verbose, we need to find all parameters, and add them to params list
    if verbose:
        params += [k for k in config.global_params if k not in params]  # Add support for global parameters
        flat_config: List[SSH_Host] = []
        for group in filtered_groups:
            for h in group.hosts + group.patterns:
                flat_config.append(h)
        for host in flat_config:
            for i_params in host.params:
                if (not i_params in params):
                    params.append(i_params)
    
    header = ["name"] + host_props + [f"param:{p}" for p in params]
    table = Table(*header, box=box.SQUARE, style="gray35")

    # Start adding rows    
    for group in filtered_groups:
        # Iterate trough hosts and patters
        for host in group.hosts + group.patterns:
            host_params = []
            # Go trough list of all params we know are available across current host list
            for table_param in params:

                # Handle direct params, and handle if its a list or string
                if table_param in host.params:
                    if isinstance(host.params[table_param], list):
                        host_params.append("\n".join(host.params[table_param]))
                    else:
                        host_params.append(host.params[table_param])

                # Inherited params... (TODO: parse config in different way so this is accessible directly from host)
                # elif table_param in [ k for t in host.inherited_params for k, _ in t[1].items()]:
                elif table_param in host.pattern_params:
                    for pattern, i_params in host.inherited_params:
                        if table_param in i_params:
                            if isinstance(i_params[table_param], list):
                                table_param = "\n".join([f"{val}  ({pattern})" for val in i_params[table_param]])
                                host_params.append(table_param)
                            else:
                                host_params.append(f"[yellow]{i_params[table_param]}  ({pattern})[/]")
                        else:
                            host_params.append("")

                # If parameter is not filled yet, then it might come from global params
                elif table_param in host.global_params:
                    host_params.append(f"[cyan]{config.global_params[table_param]}  (glob)[/]")

                # Else this host does not have this parameter (or its outside configuration)
                else:
                    host_params.append("")
                    
            alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""
            row = [host.name + alt_names] + [host.__dict__[prop] for prop in host_props] + host_params
            table.add_row(*row) if host.type == HostType.NORMAL else table.add_row(*row, style="cyan")

    console.print(table)
