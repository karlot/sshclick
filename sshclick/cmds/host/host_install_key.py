import os
import click
from shutil import which

from sshclick.sshc import SSH_Config, complete_ssh_host_names
from sshclick.globals import SSH_CONNECT_TIMEOUT


#------------------------------------------------------------------------------
# COMMAND: host test
#------------------------------------------------------------------------------
SHORT_HELP = "Install SSH key to hosts (experimental)"
LONG_HELP  = """
Installs SSH key to target hosts

!!! NOTE: This command is experimental and might change or be removed in future !!!
"""

# Parameters help:
TIME_HELP  = "Timeout for SSH connection"
#------------------------------------------------------------------------------

@click.command(name="install", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--timeout", default=SSH_CONNECT_TIMEOUT, help=TIME_HELP)
@click.option("--password", help=TIME_HELP)
@click.argument("name", required=True, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, timeout, password):
    config: SSH_Config = ctx.obj

    # filter config only on host names, not on group level
    if not config.check_host_by_name(name):
        print(f"Cannot manage host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    # Get host from config
    host = config.get_host_by_name(name)

    # Build default command args for ssh commands
    ssh_command_args = f"-f -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {name}"

    if password:
        if which("sshpass"):
            ssh_command = f"sshpass -p {password} ssh-copy-id {ssh_command_args}"
            rc = os.system(ssh_command)
        else:
            print("Cannot install key automatically with directly provided password, as 'sshpass' is not installed.")
            print("Try to repeat command, but remove --password option, and enter pass directly if prompted.")
            ctx.exit(1)
    else:
        ssh_command = f"ssh-copy-id {ssh_command_args}"
        rc = os.system(ssh_command)
        
    print(f"Copy key to: {name} ({host.params['hostname']}) ", end="")
    if rc == 0:
        print("successful!")
    else:
        print("failed!")
