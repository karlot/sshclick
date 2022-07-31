import click

from lib.sshutils import SSH_Config
from lib.sshextras import generate_graph

from rich.console import Console
console = Console()

#------------------------------------------------------------------------------
# COMMAND: host show
#------------------------------------------------------------------------------
@click.command(name="show", help="Display info for host")
@click.option("--follow", is_flag=True, help="Follow and displays all connected jump-proxy hosts")
@click.option("--graph",  is_flag=True, help="Shows connection to target as graph (default:false)")
@click.option("--style", default="panels")
# @click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("name")
@click.pass_context
def cmd(ctx, name, follow, graph, style):
    config: SSH_Config = ctx.obj['CONFIG']

    # Keep list of linked hosts via jumpproxy option
    traced_hosts = []

    # Python does not have "do while" loop. (ಠ_ಠ)
    # we are first checking host that is asked, and then check if that host has a "proxy" defined
    # if proxy is defined, we add found host to traced list, and search attached proxy, it his way we
    # can trace full connection path for later graph processing
    while True:
        # At start assume host is "normal" and contains no inherited parameters
        inherited_params: list[tuple[str, dict]] = []

        # Search for host in current configuration
        found_host, _ = config.find_host_by_name(name,throw_on_fail=False)
        if not found_host:
            print(f"Cannot show host '{name}' as it is not defined in configuration!")
            ctx.exit(1)

        # If this host is "normal" try to find inherited parameters
        if found_host.type == "normal":
            inherited_params = config.find_inherited_params(name)

        # We have everything to print out host information
        found_host.print_style = style
        
        #TODO: Should this be part of configuration parsing stage?
        found_host.inherited_params = inherited_params

        # Add current host, and its table to traced lists
        traced_hosts.append(found_host)

        # Find proxy info if it exists, if not, break the loop
        proxyjump = None
        if "proxyjump" in found_host.params:
            proxyjump = found_host.params["proxyjump"]
        else:
            for pattern, params in inherited_params:
                for key, val in params.items():
                    if key == "proxyjump":
                        proxyjump = val

        if proxyjump:
            name = proxyjump
        else:
            break
    
    # Print collected host table(s)
    if not follow:
        console.print(traced_hosts[0])
    else:
        for i, output in enumerate(traced_hosts):
            console.print(output)
            if i < len(traced_hosts) - 1:
                console.print("  [bright_green]▼ via proxy[/]")
    
    #TODO: Make better graph output
    if graph:
        console.print("\n", generate_graph(traced_hosts), "\n")
