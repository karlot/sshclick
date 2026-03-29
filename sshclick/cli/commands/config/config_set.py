import click
from sshclick.globals import DEFAULT_HOST_STYLE, ENABLED_HOST_STYLES
from sshclick.ops import SSHClickOpsError, set_host_style
from sshclick.core import SSH_Config
from sshclick.core import complete_styles

styles_str = ",".join(ENABLED_HOST_STYLES)

#------------------------------------------------------------------------------
# COMMAND: config set
#------------------------------------------------------------------------------
SHORT_HELP = "Set config option"

# Parameters help:
HOST_STYLE_HELP  = f"Set how to display hosts in 'show' command. Available:({styles_str}) (default: {DEFAULT_HOST_STYLE})"
# DISABLE_WARN_HELP  = f"Disables common warnings. (default: False)"

#------------------------------------------------------------------------------
@click.command(name="set", short_help=SHORT_HELP, help=SHORT_HELP)
@click.option("--host-style", help=HOST_STYLE_HELP, shell_complete=complete_styles)
# @click.option("--disable-warnings", is_flag=True, default=False, help=DISABLE_WARN_HELP)
@click.pass_context
def cmd(ctx, host_style):
    config: SSH_Config = ctx.obj

    try:
        set_host_style(config, host_style)
    except SSHClickOpsError as exc:
        print(str(exc))
        return

    config.generate_ssh_config()

        
