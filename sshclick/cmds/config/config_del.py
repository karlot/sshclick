import click
from sshclick.sshc import SSH_Config

#------------------------------------------------------------------------------
# COMMAND: config del
#------------------------------------------------------------------------------
SHORT_HELP = "Delete config option"

# Parameters help:
HOST_STYLE_HELP  = "Remove host-style from configuration"
#------------------------------------------------------------------------------
@click.command(name="del", short_help=SHORT_HELP, help=SHORT_HELP)
@click.option("--host-style", is_flag=True, help=HOST_STYLE_HELP)
@click.pass_context
def cmd(ctx, host_style):
    config: SSH_Config = ctx.obj

    # Deleting host-style trough SSH configuration
    if host_style:
        if "host-style" not in config.opts:
            print("Cannot remove host-style from configuration, as it is not defined!")
            return
        else:
            del config.opts["host-style"]

        # Write out modified config
        config.generate_ssh_config()
        return

    print("No option was provided to delete from SSH config options!")
