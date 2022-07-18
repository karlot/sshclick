import click

#------------------------------------------------------------------------------
# HOST Commands
#------------------------------------------------------------------------------
@click.group(name="host")
def ssh_host():
    """
    Hosts management commands and options
    """


#// Linking other sub-commands
from commands.host import host_list, host_show, host_create, host_set, host_delete
ssh_host.add_command(host_list.cmd)
ssh_host.add_command(host_show.cmd)
ssh_host.add_command(host_create.cmd)
ssh_host.add_command(host_set.cmd)
ssh_host.add_command(host_delete.cmd)












