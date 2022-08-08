import click

#------------------------------------------------------------------------------
# GROUP Commands
#------------------------------------------------------------------------------
@click.group(name="group")
def ssh_group():
    """
    Manage groups
    """

#// Linking other sub-commands
from .group import group_create, group_delete, group_list, group_set, group_show
ssh_group.add_command(group_create.cmd)
ssh_group.add_command(group_delete.cmd)
ssh_group.add_command(group_list.cmd)
ssh_group.add_command(group_set.cmd)
ssh_group.add_command(group_show.cmd)
