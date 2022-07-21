import click

#------------------------------------------------------------------------------
# GROUP Commands
#------------------------------------------------------------------------------
@click.group(name="group")
def ssh_group():
    """
    Group management commands and options
    """


#// Linking other sub-commands
from commands.group import group_list, group_show, group_create, group_delete, group_set
ssh_group.add_command(group_list.cmd)
ssh_group.add_command(group_show.cmd)
ssh_group.add_command(group_create.cmd)
ssh_group.add_command(group_set.cmd)
ssh_group.add_command(group_delete.cmd)
