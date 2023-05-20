import subprocess
import click
from sshclick.sshc import SSH_Config, complete_ssh_host_names
from rich.pretty import pprint

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

    if not config.check_host_by_name(name):
        print(f"Cannot test host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    # Get host from config, and all linked properties (configured and inherited)
    found_host, _ = config.get_host_by_name(name)
    # host_all_params = found_host.get_all_params()
    # inspect(found_host)

    # Test can conclude few things
    # - [x] if target is not IP address, can we resolve it?
    # - [x] Can we establish SSH connection?
    #   - [x] Directly connected and via jump host?
    #   - [ ] Can we test both key based auth and un/pw based auth?
    #   - [ ] Is test OK if only connection is OK, but not authentication?

    # ------------------------------------------------------------
    # Manually test if target is resolvable
    # ------------------------------------------------------------
    # Based internally on get_target(), also tries to resolve to IP
    target = found_host.get_target()
    target_ip, err = found_host.resolve_target()
    if err:
        print(f"Test host failed: {name} ({target}) is not resolvable!")
        ctx.exit(1)

    # SSH Command method via subprocess
    #------------------------------------------------
    # ssh_command = f"ssh -q -o PasswordAuthentication=no StrictHostKeyChecking=no -o ConnectTimeout={timeout} {name} 'exit'"
    ssh_command = f"ssh -q -o StrictHostKeyChecking=no -o ConnectTimeout={timeout} {name} 'exit'"
    response = subprocess.run(ssh_command, shell=True, capture_output=True)
    pprint(response)
    
    print(f"Connection to: {name} ({target}) ", end="")
    if response.returncode == 0:
        print("OK!")
    else:
        print(f"Failed! - {response.returncode}")
        ctx.exit(response.returncode)
