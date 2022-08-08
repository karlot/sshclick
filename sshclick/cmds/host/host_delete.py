import click
from sshclick.sshc import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host delete
#------------------------------------------------------------------------------
@click.command(name="delete", help="Delete host from configuration")
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name):
    config: SSH_Config = ctx.obj

    found_host, found_group = config.find_host_by_name(name, throw_on_fail=False)
    if not found_host:
        print(f"Cannot delete host '{name}' as it is not defined in configuration!")
        ctx.exit(1)
    
    if found_host.type == "normal":
        found_group.hosts.remove(found_host)
    else:
        found_group.patterns.remove(found_host)

    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Deleted host: {name}")
