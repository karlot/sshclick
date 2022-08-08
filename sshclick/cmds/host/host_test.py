import click
import subprocess
from sshclick.sshc import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host connect
#------------------------------------------------------------------------------
@click.command(name="test", help="Test SSH host connection")
@click.option("--timeout", default=3, help="Timeout for SSH connection")
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, timeout):
    config: SSH_Config = ctx.obj

    found_host, _ = config.find_host_by_name(name, throw_on_fail=False)
    if not found_host:
        print(f"Cannot test host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    hostname = found_host.params["hostname"]

    #// SSH Command method via subprocess
    #------------------------------------------------
    ssh_command = f"ssh -q -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {name} 'exit 0'"
    response = subprocess.run(ssh_command, shell=True)
    
    print(f"Connection with SSH Host name: {name} ({hostname}) ", end="")
    if response.returncode == 0:
        print("successful!")
        ctx.exit()
    else:
        print("failed!")
        ctx.exit(1)
