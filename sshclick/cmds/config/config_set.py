import click
from sshclick.globals import DEFAULT_HOST_STYLE, ENABLED_HOST_STYLES
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_styles

styles_str = ",".join(ENABLED_HOST_STYLES)

#------------------------------------------------------------------------------
# COMMAND: config set
#------------------------------------------------------------------------------
SHORT_HELP = "Set config option"

# Parameters help:
HOST_STYLE_HELP  = f"Set how to display hosts in 'show' command. Available:({styles_str}) (default: {DEFAULT_HOST_STYLE})"
#------------------------------------------------------------------------------
@click.command(name="set", short_help=SHORT_HELP, help=SHORT_HELP)
@click.option("--host-style", help=HOST_STYLE_HELP, shell_complete=complete_styles)
@click.pass_context
def cmd(ctx, host_style):
    config: SSH_Config = ctx.obj

    # Setting host-style trough SSH configuration
    if host_style:
        if not host_style in ENABLED_HOST_STYLES:
            print(f"Cannot set style '{host_style}', as it is not one of available styles!")
            return
        else:
            config.opts["host-style"] = host_style

        # Write out modified config
        config.generate_ssh_config().write_out()
        return
    
    print("No option was provided to set into SSH config options!")

        