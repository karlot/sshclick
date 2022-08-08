import click
from sshclick.sshc import SSH_Config, complete_ssh_host_names, generate_graph

from rich.console import Console
console = Console()

# Help autocomplete with host styles
enabled_styles = ["panels", "card", "simple", "table", "table2", "json"]
def complete_styles(ctx, param, incomplete):
    return [k for k in enabled_styles if k.startswith(incomplete)]

#------------------------------------------------------------------------------
# COMMAND: host show
#------------------------------------------------------------------------------
@click.command(name="show", help="Display info for host")
@click.option("--follow", is_flag=True, help="Follow and displays all connected jump-proxy hosts")
@click.option("--graph",  is_flag=True, help="Shows connection to target as graph (default:false)")
@click.option("--style", default="panels", show_default="panels", envvar='SSHC_HOST_STYLE',
    help="Select output rendering style for host details: [panels, card, simple, table, table2, json]",
    shell_complete=complete_styles)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, follow, graph, style):
    config: SSH_Config = ctx.obj

    # Keep list of linked hosts via jumpproxy option
    traced_hosts = []

    # we are first checking host that is asked, and then check if that host has a "proxy" defined
    # if proxy is defined, we add found host to traced list, and search attached proxy, it this way we
    # can trace full connection path for later graph processing
    while True:
        # Search for host in current configuration
        found_host, _ = config.find_host_by_name(name,throw_on_fail=False)
        if not found_host:
            print(f"Cannot show host '{name}' as it is not defined in configuration!")
            ctx.exit(1)

        #TODO: Should this be part of configuration parsing stage?
        inherited_params: list[tuple[str, dict]] = []
        if found_host.type == "normal":
            inherited_params = config.find_inherited_params(name)
            found_host.inherited_params = inherited_params

        # Set SSH host print style from user input
        found_host.print_style = style

        # Add current host, and its table to traced lists
        traced_hosts.append(found_host)

        # Find proxy info if it exists, if not, break the loop
        proxyjump = None
        if "proxyjump" in found_host.params:
            proxyjump = found_host.params["proxyjump"]
        else:
            for _, params in inherited_params:
                for key, value in params.items():
                    if key == "proxyjump":
                        proxyjump = value

        # If there is connected host, we switch "name" and continue the loop
        # Otherwise we exit the loop
        if proxyjump:
            name = proxyjump
        else:
            break
    
    # Print collected host data
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
