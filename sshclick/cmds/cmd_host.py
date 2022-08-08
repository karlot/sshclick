import click

#------------------------------------------------------------------------------
# HOST Commands
#------------------------------------------------------------------------------
@click.group(name="host")
def ssh_host():
    """
    Manage hosts
    """

#// Linking other sub-commands
from .host import host_create, host_delete, host_list, host_set, host_show, host_test
ssh_host.add_command(host_create.cmd)
ssh_host.add_command(host_delete.cmd)
ssh_host.add_command(host_list.cmd)
ssh_host.add_command(host_set.cmd)
ssh_host.add_command(host_show.cmd)
ssh_host.add_command(host_test.cmd)
