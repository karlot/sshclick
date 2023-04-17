import click
import subprocess
from sshclick.sshc import SSH_Config, complete_ssh_host_names, expand_names

#------------------------------------------------------------------------------
# COMMAND: host test
#------------------------------------------------------------------------------
SHORT_HELP = "Install SSH key to hosts (experimental)"
LONG_HELP  = """
Installs SSH key to target hosts

NOTE: This command is experimental and might change or be removed in future
"""

# Parameters help:
TIME_HELP  = "Timeout for SSH connection"
#------------------------------------------------------------------------------

@click.command(name="install", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--timeout", default=3, help=TIME_HELP)
@click.option("--password", required=True, help=TIME_HELP)
@click.argument("name", required=True, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, timeout, password):
    config: SSH_Config = ctx.obj

    # filter config only on host names, not on group level
    filtered_groups = config.filter_config("", name)
    for group in filtered_groups:
        for host in group.hosts:
            hostname = host.name

            #// SSH Command method via subprocess
            #------------------------------------------------
            ssh_command = f"sshpass -p {password} ssh-copy-id -f -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {hostname}"
            response = subprocess.run(ssh_command, shell=True)
            
            print(f"Copy key to: {name} ({hostname}) ", end="")
            if response.returncode == 0:
                print("successful!")
            else:
                print("failed!")
    ctx.exit()
