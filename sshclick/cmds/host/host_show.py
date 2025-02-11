from sshclick.globals import DEFAULT_HOST_STYLE, ENABLED_HOST_STYLES
import click
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_host_names, complete_styles, generate_graph

from rich.console import Console
console = Console()
styles_str = ",".join(ENABLED_HOST_STYLES)

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
STYLE_HELP  = f"Select output rendering style for host details: ({styles_str}), (default: {DEFAULT_HOST_STYLE})"
#------------------------------------------------------------------------------

@click.command(name="show", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--style", default="", envvar='SSHC_HOST_STYLE', help=STYLE_HELP, shell_complete=complete_styles)
@click.option("--graph", is_flag=True, envvar='SSHC_HOST_GRAPH', help=GRAPH_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx: click.core.Context, name: str, style:str, graph: bool):
    config: SSH_Config = ctx.obj

    # Define host print style from CLI or config or default
    if style == "":
        style = config.opts["host-style"] if "host-style" in config.opts else DEFAULT_HOST_STYLE

    if not config.check_host_by_name(name):
        print(f"Unknown host '{name}'!")
        ctx.exit(1)

    # Normal show, no linked graphs needed
    host = config.get_host_by_name(name)
    host.print_style = style
    console.print(host)

    #TODO: Make better graph output
    if graph:
        # Get info about linked hosts (required for graph and follow)
        traced_hosts = config.trace_proxyjump(name)
        if not traced_hosts:
            # Tracing config was broken somewhere in proxy chain
            ctx.exit(1)

        console.print(generate_graph(traced_hosts), "")
