import click
from sshclick.sshc import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host rename
#------------------------------------------------------------------------------
SHORT_HELP = "Rename existing host"
LONG_HELP  = "Rename existing host from configuration"

#------------------------------------------------------------------------------

@click.command(name="rename", short_help=SHORT_HELP, help=LONG_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("new_name")
@click.pass_context
def cmd(ctx, name, new_name):
    config: SSH_Config = ctx.obj

    found_host, _ = config.find_host_by_name(name, throw_on_fail=False)
    if not found_host:
        print(f"Cannot rename host '{name}' as it is not defined in configuration!")
        ctx.exit(1)

    found_target_host, _ = config.find_host_by_name(new_name, throw_on_fail=False)
    if found_target_host:
        print(f"Cannot rename host '{name}' to '{new_name}' as new name is already used!")
        ctx.exit(1)

    found_host.name = new_name

    if not config.stdout:
        print(f"Renamed host: {name} -> {new_name}")

    # Write out modified config
    config.generate_ssh_config().write_out()
