import click
from sshclick.sshc import SSH_Config, HostType

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

    # Filter out hosts if filters are defined via CLI
    filtered_hosts = config.filter_hosts(group_filter, name_filter)

    if not filtered_hosts:
        print("No host is matching any given filter!")
        ctx.exit(1)
    
    # This lists define host properties and which parameters will be displayed by default
    host_props   = ["group", "type"]
    table_params = ["hostname", "user"]

    # If output is verbose, we need to find all used parameters, and add them to params list
    if verbose:
        for host in filtered_hosts:
            for param in host.get_all_params():
                if param not in table_params: table_params.append(param)
    
    header = ["name"] + host_props + [f"param:{p}" for p in table_params]
    table = Table(*header, box=box.SQUARE, style="gray35")

    # Start adding rows    
    for host in filtered_hosts:
        # Iterate trough hosts and patters
        host_params = []

        # Go trough list of all params we need to fill in table, and get value for each host
        for tp in table_params:
            value, source = host.get_applied_param(tp)
            host_params.append(merge_with_color(value, source))
                
        alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""
        row = [host.name + alt_names] + [getattr(host, prop, "") for prop in host_props] + host_params
        table.add_row(*row) if host.type == HostType.NORMAL else table.add_row(*row, style="cyan")

    console.print(table)


# Helper function for list particular style
# - adds color based on "source" of parameter (local, global, or from pattern)
# - if value is based on non-local source, it adds reference to the source
# - if value is list, it merges line into multiline output, keeping color and source references
def merge_with_color(v, s="local"):
    if v == "": return ""
    if s == "local":
        if isinstance(v, list): return "\n".join(v)
        return v

    c = "green" if s == "global" else "yellow"
    if isinstance(v, list): return "\n".join([f"[{c}]{val}  ({s})[/]" for val in v])
    return f"[{c}]{v}  ({s})[/]"    

