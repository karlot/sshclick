import click

#------------------------------------------------------------------------------
# CONFIG Commands
#------------------------------------------------------------------------------
@click.group(name="config", help="Modify SSHClick configuration trough SSH Config")
def ssh_config():
    pass

#// Linking other sub-commands
from .config import config_set, config_del, config_show
ssh_config.add_command(config_set.cmd)
ssh_config.add_command(config_del.cmd)
ssh_config.add_command(config_show.cmd)