import click
from sshclick.sshc import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host rename
#------------------------------------------------------------------------------
SHORT_HELP = "Rename existing host"
LONG_HELP  = "Rename existing host in configuration"

#------------------------------------------------------------------------------

@click.command(name="rename", short_help=SHORT_HELP, help=LONG_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("new_name")
@click.pass_context
def cmd(ctx, name, new_name):
    config: SSH_Config = ctx.obj

    if (not config.check_host_by_name(name)):
        print(f"Cannot rename host '{name}' as it is not defined in configuration!")
        ctx.exit(1)
    if (config.check_host_by_name(new_name)):
        print(f"Cannot rename host '{name}' to '{new_name}' as new name is already used!")
        ctx.exit(1)

    config.get_host_by_name(name)[0].name = new_name
    config.generate_ssh_config().write_out()

    if not config.stdout:
        print(f"Renamed host: {name} -> {new_name}")
