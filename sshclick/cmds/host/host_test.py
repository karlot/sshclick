import click
import subprocess
from sshclick.sshc import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host test
#------------------------------------------------------------------------------
SHORT_HELP = "Test SSH host connection  (experimental)"
LONG_HELP  = """
Test SSH host connectivity end-to-end

NOTE: This command is experimental and might change or be removed in future
"""

# Parameters help:
TIME_HELP  = "Timeout for SSH connection"
#------------------------------------------------------------------------------

@click.command(name="test", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--timeout", default=3, help=TIME_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx: click.core.Context, name: str, timeout: int):
    config: SSH_Config = ctx.obj

    found_host, _ = config.get_host_by_name(name)
    if not found_host:
        print(f"Cannot test host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    hostname = found_host.params["hostname"]

    #// SSH Command method via subprocess
    #------------------------------------------------
    ssh_command = f"ssh -q -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {name} 'exit 0'"
    response = subprocess.run(ssh_command, shell=True)
    
    print(f"Connection to: {name} ({hostname}) ", end="")
    if response.returncode == 0:
        print("successful!")
        ctx.exit()
    else:
        print("failed!")
        ctx.exit(1)
