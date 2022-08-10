import click
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_host_names, expand_host_names

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

Whenever target host list is larger than single host, confirmation dialog will appear to confirm if
deletion is ok to continue.
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

    selected_hosts_list = list(expand_host_names(names, config))
    selected_hosts_list.sort()
    
    # When more than single
    if not yes:
        if len(selected_hosts_list) > 1:
            print("Multiple hosts are selected for action:")
            for name in selected_hosts_list:
                print(f" - {name}")
            if not click.confirm('Are you sure?'):
                ctx.exit(1)

    # When deleting multiple hosts, iterate over all of them
    for name in selected_hosts_list:
        found_host, found_group = config.find_host_by_name(name, throw_on_fail=False)
        if not found_host:
            print(f"Cannot delete host '{name}' as it is not defined in configuration!")
            continue
        
        if found_host.type == "normal":
            found_group.hosts.remove(found_host)
        else:
            found_group.patterns.remove(found_host)

        config.generate_ssh_config().write_out()
        if not config.stdout:
            print(f"Deleted host: {name}")
