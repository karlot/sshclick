import click
from sshclick.ops import SSHClickOpsError, create_group
from sshclick.core import SSH_Config

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

    try:
        create_group(config, name, desc=desc, info=info)
    except SSHClickOpsError as exc:
        print(str(exc))
        ctx.exit(1)

    if config.generate_ssh_config():
        print(f"Created group: {name}")
