import click

#------------------------------------------------------------------------------
# GROUP Commands
#------------------------------------------------------------------------------
@click.group(name="group", help="Command group for managing groups")
def ssh_group():
    pass

#// Linking other sub-commands
from .group import group_create, group_delete, group_list, group_set, group_show, group_rename
ssh_group.add_command(group_create.cmd)
ssh_group.add_command(group_delete.cmd)
ssh_group.add_command(group_list.cmd)
ssh_group.add_command(group_set.cmd)
ssh_group.add_command(group_show.cmd)
ssh_group.add_command(group_rename.cmd)
