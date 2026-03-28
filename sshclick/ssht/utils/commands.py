import os

from textual.app import App

from sshclick.process_utils import run_captured_command, run_interactive_command
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

    argv = [prog]
    for key, value in opts.items():
        argv.extend(["-o", f"{key}={value}"])
    argv.append(target.name)

    try:
        rc = run_interactive_command(argv, tui=tui)
    except FileNotFoundError:
        tui.notify(f"'{prog}' command not found", title=target.name, severity="error")
        return
    except OSError as exc:
        tui.notify(str(exc), title=target.name, severity="error")
        return

    if rc == 255:
        tui.notify(f"{prog} exited with code {rc}", title=target.name, severity="error")
    elif rc > 0:
        tui.notify(f"{prog} exited with code {rc}", title=target.name, severity="warning")


# ---------------------------------
# Reset fingerprints for hosts
# TODO: Handle timeout...
# ---------------------------------
def reset_fingerprint(tui: App, target):
    # Command only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    argv = ["ssh-keygen", "-R", target.params.get("hostname", target.name)]
    try:
        result = run_captured_command(argv)
    except FileNotFoundError:
        tui.notify("'ssh-keygen' command not found", title=target.name, severity="error")
        return
    except OSError as exc:
        tui.notify(str(exc), title=target.name, severity="error")
        return

    if result.returncode > 0:
        tui.notify(str(result.stderr), title=f"{target.name}: code {result.returncode}", severity="warning")

# ---------------------------------
# Copy SSH Keys
# TODO: Check if duplicate keys or not, should we force or not, handle timeout...
# ---------------------------------
def copy_ssh_keys(tui: App, target):
    # Command only works on normal nodes (not groups or patterns)
    if not isinstance(target, SSH_Host) or target.type != HostType.NORMAL:
        return

    target_spec = f"{target.params.get('user', os.environ.get('USER'))}@{target.params.get('hostname', target.name)}"
    argv = ["ssh-copy-id", target_spec]

    try:
        rc = run_interactive_command(argv, tui=tui)
    except FileNotFoundError:
        tui.notify("'ssh-copy-id' command not found", title=target.name, severity="error")
        return
    except OSError as exc:
        tui.notify(str(exc), title=target.name, severity="error")
        return

    if rc > 0:
        tui.notify(f"ssh-copy-id exited with code {rc}", title=target.name, severity="warning")
