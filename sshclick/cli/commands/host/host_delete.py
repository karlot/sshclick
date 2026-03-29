import click
from sshclick.ops import SSHClickOpsError, delete_host
from sshclick.core import SSH_Config
from sshclick.core import complete_ssh_host_names, expand_names

#------------------------------------------------------------------------------
# COMMAND: host delete
#------------------------------------------------------------------------------
SHORT_HELP = "Delete host(s)"
LONG_HELP  = """
Delete host(s) from configuration

Command accepts single or multiple host names to delete.
If autocompletion is enabled, command will also offer current configured hosts for TAB completion.
Alternatively when "NAME" is specified with "r:" prefix, then part after ":" is used as regex match
to find all hosts that match that pattern, and will expand target host list accordingly.
If multiple regex matches are defined, results from all individual matches will be combined to target host list (exclusive OR)

\b
Regex NAMES example command: (sshc host delete r:^test_ r:_test$)
-> will delete all hosts which names start with "test_" or end with "_test"

Confirmation dialog will appear to confirm if deletion is ok to continue.
"""

# Parameters help:
YES_HELP   = "Skip confirmation and assume 'yes'. Be careful!"
#------------------------------------------------------------------------------

@click.command(name="delete", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--yes", is_flag=True, help=YES_HELP)
@click.argument("names", nargs=-1, required=True, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, names, yes):
    config: SSH_Config = ctx.obj

    selected_hosts_list = expand_names(names, config.get_all_host_names())
    selected_hosts_list.sort()
    
    # Deleting requires confirmation
    if not yes:
        print(f"Following hosts will be deleted: [{','.join(selected_hosts_list)}]")
        if not click.confirm('Are you sure?'):
            ctx.exit(1)

    # When deleting multiple hosts, iterate over all of them
    for name in selected_hosts_list:
        try:
            delete_host(config, name)
        except SSHClickOpsError as exc:
            print(str(exc))
            ctx.exit(1)

    if config.generate_ssh_config():
        print(f"Deleted hosts: {', '.join(selected_hosts_list)}")
