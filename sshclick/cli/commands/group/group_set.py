import click
from sshclick.ops import SSHClickOpsError, update_group
from sshclick.core import SSH_Config
from sshclick.core import complete_ssh_group_names

#TODO: Check click.edit for multiline edit option (info, or even params?)

#------------------------------------------------------------------------------
# COMMAND: group set
#------------------------------------------------------------------------------
SHORT_HELP = "Change group parameters"
LONG_HELP  = r"""
Change/modify group parameters

Command allows to modify current information on the group, like info lines
and description. To rename group, use command "sshc group rename" command.
To move hosts between group, use "sshc host set" command.

When modifying group, work can be done on single group only. I didn't find
any use-case where I would set same description or info lines on multiple
groups at the same time... ¯\_(ツ)_/¯
"""

# Parameters help:
DESC_HELP  = "Short description of group"
INFO_HELP  = "Info line, can be set multiple times"
#------------------------------------------------------------------------------

@click.command(name="set", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-d", "--desc", help=DESC_HELP)
@click.option("-i", "--info", multiple=True, help=INFO_HELP)
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, name, desc, info):
    config: SSH_Config = ctx.obj

    try:
        update_group(config, name, desc=desc if desc is not None else None, info=info if info else None)
    except SSHClickOpsError as exc:
        print(str(exc))
        ctx.exit(1)

    if config.generate_ssh_config():
        print(f"Modified group: {name}")
