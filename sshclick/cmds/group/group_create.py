import click
from sshclick.sshc import SSH_Config, SSH_Group

#------------------------------------------------------------------------------
# COMMAND: group create
#------------------------------------------------------------------------------
SHORT_HELP = "Create new group"
LONG_HELP  = """
Create new group

Group is used as visual and searchable separation between hosts.
It is achieved trough readable comments with special comment keyword
defining start of the group "#@group: <group-name>", every host defined
after this keyword is considered as part of this group.
"""

# Parameters help:
DESC_HELP  = "Short description of group"
INFO_HELP  = "Info line, can be set multiple times"
#------------------------------------------------------------------------------

@click.command(name="create", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-d", "--desc", default="", help=DESC_HELP)
@click.option("-i", "--info", multiple=True, help=INFO_HELP)
@click.argument("name")
@click.pass_context
def cmd(ctx, name, desc, info):
    config: SSH_Config = ctx.obj

    # Check if already group exists
    if not config.check_group_by_name(name):
        print(f"Cannot create new group '{name}', as group already exists with this name")
        ctx.exit(1)

    new_group = SSH_Group(name, desc=desc, info=list(info))

    # Add new group to config and show newly created group
    config.groups.append(new_group)
    config.generate_ssh_config().write_out()

    if not config.stdout:
        print(f"Created group: {name}")
