import click
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_host_names, complete_styles, generate_graph

from rich.console import Console
console = Console()
styles_str = ",".join(complete_styles(None, None, ""))

#------------------------------------------------------------------------------
# COMMAND: host show
#------------------------------------------------------------------------------
SHORT_HELP = "Show current host configuration"
LONG_HELP  = """
Shows details about host and its configuration

Command can generate nice representation of configuration for given HOST.
If HOST is using "proxyjump" properties, command will try to collect also all info
from intermediate hosts/proxies as well. This relations can then be showed when using
option --follow, to display all interconnected host path. (NOTE: This relations can
only be understand and showed if "proxyjump" hosts are also part of the configuration!!!)

Additionally when using --graph option, command can "draw" visualization of
connection path, and defined end-to-end tunnels

\b
SSHC can ready some of this options via users ENV variables
(trough local shell files such as: .bashrc, .zshrc, etc...)
export SSHC_HOST_STYLE=table1
export SSHC_HOST_FOLLOW=0
export SSHC_HOST_GRAPH=1
"""

# Parameters help:
FOLLOW_HELP =  "Follow and displays all connected hosts via proxyjump (works only for locally defined hosts)"
GRAPH_HELP  =  "Shows connection to target as graph with tunnels visualizations"
STYLE_HELP  = f"Select output rendering style for host details: ({styles_str}), (default: panels)"
#------------------------------------------------------------------------------

@click.command(name="show", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--style", default="panels", envvar='SSHC_HOST_STYLE',  help=STYLE_HELP, shell_complete=complete_styles)
@click.option("--follow", is_flag=True,    envvar='SSHC_HOST_FOLLOW', help=FOLLOW_HELP)
@click.option("--graph",  is_flag=True,    envvar='SSHC_HOST_GRAPH',  help=GRAPH_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, style, follow, graph):
    config: SSH_Config = ctx.obj

    # Keep list of linked hosts via proxyjump option
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
