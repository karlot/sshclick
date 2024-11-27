import os, subprocess

# SSHClick stuff
from sshclick.globals import USER_SSH_CONFIG, SSH_CONNECT_TIMEOUT
from sshclick.sshc import SSH_Config, SSH_Host, HostType

# Forced defaults for sane openssh connection
DEFAULT_CONNECT_OPTS = {
    "ConnectTimeout": SSH_CONNECT_TIMEOUT,  # Add explicit timout option
}

# ---------------------------------
# Connect options
# ---------------------------------
def run_connect(tui, prog, target, opts=DEFAULT_CONNECT_OPTS):
    # "Connect" only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    # Build command arguments and join into full CLI command
    cmd_args = " ".join([f"-o {k}={v}" for k, v in opts.items()])
    fullcmd = f"{prog} {cmd_args} {target.name}"

    with tui.suspend():
        cmd_result = subprocess.run(fullcmd, stderr=subprocess.PIPE, text=True, shell=True)
        if cmd_result.returncode != 0:
            tui.notify(
                f"ReturnCode: {cmd_result.returncode}\n"
                f"Error: {cmd_result.stderr}",
                title=f"Connect failed to '{target.name}'!", severity="warning")
