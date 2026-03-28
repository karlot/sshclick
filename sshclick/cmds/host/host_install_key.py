import click

from sshclick.process_utils import run_interactive_command
from sshclick.sshc import SSH_Config, complete_ssh_host_names
from sshclick.globals import SSH_CONNECT_TIMEOUT


#------------------------------------------------------------------------------
# COMMAND: host install
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
@click.argument("name", required=True, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, timeout):
    config: SSH_Config = ctx.obj

    # filter config only on host names, not on group level
    if not config.check_host_by_name(name):
        print(f"Cannot manage host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    # Get host from config
    host = config.get_host_by_name(name)

    ssh_command = ["ssh-copy-id", "-f", "-o", f"ConnectTimeout={timeout}", name]
    try:
        rc = run_interactive_command(ssh_command)
    except FileNotFoundError:
        print("Cannot install SSH key automatically, as 'ssh-copy-id' is not installed.")
        ctx.exit(1)
    except KeyboardInterrupt:
        ctx.exit(130)
    except OSError as exc:
        print(f"Failed running ssh-copy-id: {exc}")
        ctx.exit(1)

    print(f"Copy key to: {name} ({host.params['hostname']}) ", end="")
    if rc == 0:
        print("successful!")
    else:
        print("failed!")
