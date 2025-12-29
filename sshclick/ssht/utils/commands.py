import subprocess, signal, os

from textual.app import App

# SSHClick stuff
from sshclick.globals import SSH_CONNECT_TIMEOUT
from sshclick.sshc import SSH_Host, HostType

# Forced defaults for sane openssh connection
DEFAULT_CONNECT_OPTS = {
    "ConnectTimeout": SSH_CONNECT_TIMEOUT,  # Add explicit timeout option
}


# ---------------------------------
# Connect options
# ---------------------------------
def run_connect(tui: App, prog, target, opts=DEFAULT_CONNECT_OPTS):
    # "Connect" only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    # Build command arguments and join into full CLI command
    cmd_args = " ".join([f"-o {k}={v}" for k, v in opts.items()])
    full_cmd = f"{prog} {cmd_args} {target.name}"
    with tui.suspend():
        # Temporary suspend default sig-int handling if user presses Ctrl-C
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, lambda sig, frame: None)

        result = subprocess.run(full_cmd, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode == 255:
            # SSH connection originated error
            tui.notify(
                str(result.stderr),
                title=f"{target.name}: code {result.returncode}",
                severity="error")
        elif result.returncode > 0:
            tui.notify(
                str(result.stderr),
                title=f"{target.name}: code {result.returncode}",
                severity="warning")
        # else:
        #     tui.notify(
        #         f"Connection to '{target.name}' interrupted!",
        #         severity="error")
        
        # Restore default sig-int handling
        signal.signal(signal.SIGINT, original_handler)


# ---------------------------------
# Reset fingerprints for hosts
# TODO: Handle timeout...
# ---------------------------------
def reset_fingerprint(tui: App, target):
    # Command only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    # Build command arguments and join into full CLI command
    full_cmd = f"ssh-keygen -R {target.params.get('hostname', target.name)}"
    with tui.suspend():
        # Temporary suspend default sig-int handling if user presses Ctrl-C
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, lambda sig, frame: None)

        result = subprocess.run(full_cmd, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode > 0:
            tui.notify(
                str(result.stderr),
                title=f"{target.name}: code {result.returncode}",
                severity="warning")
        
        # Restore default sig-int handling
        signal.signal(signal.SIGINT, original_handler)

# ---------------------------------
# Copy SSH Keys
# TODO: Check if duplicate keys or not, should we force or not, handle timeout...
# ---------------------------------
def copy_ssh_keys(tui: App, target):
    # Command only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    # Build command arguments and join into full CLI command
    full_cmd = f"ssh-copy-id {target.params.get('user', os.environ.get('USER'))}@{target.params.get('hostname', target.name)}"
    with tui.suspend():
        # Temporary suspend default sig-int handling if user presses Ctrl-C
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, lambda sig, frame: None)

        result = subprocess.run(full_cmd, stderr=subprocess.PIPE, text=True, shell=True)
        if result.returncode > 0:
            tui.notify(
                str(result.stderr),
                title=f"{target.name}: code {result.returncode}",
                severity="warning")
        
        # Restore default sig-int handling
        signal.signal(signal.SIGINT, original_handler)
