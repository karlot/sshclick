import click
from sshclick.sshc import SSH_Config

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

#------------------------------------------------------------------------------
# COMMAND: config show
#------------------------------------------------------------------------------
SHORT_HELP = "Show all config options"

#------------------------------------------------------------------------------
@click.command(name="show", short_help=SHORT_HELP, help=SHORT_HELP)
@click.pass_context
def cmd(ctx):
    config: SSH_Config = ctx.obj

    #// Prepare table with params
    #// -----------------------------------------------------------------------
    param_table = Table(box=box.SIMPLE, style="grey35", show_header=True, show_edge=False, pad_edge=True)
    param_table.add_column("Config Parameter")
    param_table.add_column("Value")

    # Add rows for SSH Config parameters
    for key, value in config.opts.items():
        param_table.add_row(key, value)

    console.print("List of all saved SSHClick config parameters:\n", param_table, "\n")
