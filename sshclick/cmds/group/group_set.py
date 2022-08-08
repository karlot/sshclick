import click
from sshclick.sshc import SSH_Config, complete_ssh_group_names

#TODO: Check click.edit for multiline edit option (info, or even params?)

#------------------------------------------------------------------------------
# COMMAND: group-set
#------------------------------------------------------------------------------
@click.command(name="set", help="Change group parameters")
@click.option("-r", "--rename", default=None, help="Rename group")
@click.option("-d", "--desc", default=None, help="Set description")
@click.option("-i", "--info", default=None, multiple=True, help="Set info, can be set multiple times")
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, name, rename, desc, info):
    config: SSH_Config = ctx.obj

    # Nothing was provided
    if not rename and not desc and not info:
        print("Calling set on group without specifying any option is not valid!")
        print("Run 'sshc group set -h' for help.")
        ctx.exit(1)

    # Find group by name
    found_group = config.find_group_by_name(name, throw_on_fail=False)
    if not found_group:
        print(f"Cannot modify group '{name}', it is not defined in configuration!")
        ctx.exit(1)

    if rename:
        found_group.name = rename
    
    if desc:
        found_group.desc = desc

    if info:
        if len(info[0]) > 0:
            found_group.info = info
        else:
            found_group.info = []

    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Modified group: {name}")
