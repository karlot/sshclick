import click

from .config import config_set, config_del, config_show

#------------------------------------------------------------------------------
# CONFIG Commands
#------------------------------------------------------------------------------
@click.group(name="config", help="Modify SSHClick configuration through SSH Config")
def ssh_config():
    pass

#// Linking other sub-commands
ssh_config.add_command(config_set.cmd)
ssh_config.add_command(config_del.cmd)
ssh_config.add_command(config_show.cmd)
