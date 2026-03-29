import click
from sshclick.ops import SSHClickOpsError, update_host
from sshclick.core import SSH_Config
from sshclick.core import complete_ssh_host_names, complete_ssh_group_names, complete_params, expand_names

#------------------------------------------------------------------------------
# COMMAND: host set
#------------------------------------------------------------------------------
SHORT_HELP = "Set/Change host configuration"
LONG_HELP  = """
Set/Change various host definitions and parameters

Command accepts single or multiple host names for modification.
If autocompletion is enabled, command will also offer current configured hosts for TAB completion.
Alternatively when "NAME" is specified with "r:" prefix, then part after ":" is used as regex match
to find all hosts that match that pattern, and will expand target host list accordingly.
If multiple regex matches are defined, results from all individual matches will be combined to target host list (exclusive OR)

\b
Regex NAMES example command: (sshc host set -f -g new r:^test_ r:_test$)
-> will MOVE hosts which names start with "test_" or end with "_test" to
    "new" group

\b
Set tunnel: (sshc host set test1 -p localforward "8080 localhost:80")
-> Access on your local port 8080 services from remote local port 80:


Whenever target host list is larger than single host, confirmation dialog will appear to confirm if
deletion is ok to continue.
"""

# Parameters help:
INFO_HELP  = "Set host info, can be set multiple times, or set to empty value to clear it (example: -i '')"
PARAM_HELP = "Sets parameter for the host, takes 2 values (<sshparam> <value>). To unset/remove parameter from host, set its value to empty string like this (example: -p user '')"
GROUP_HELP = "Group change for host. Moves one or many hosts from their groups (they can be in different ones) to specified group."
FORCE_HELP = "Allows during group host group change, to move host(s) to group that does not exist, by creating it automatically, and moving specified hosts to new group."
YES_HELP   = "Skip confirmation and assume 'yes'. Be careful!"
#------------------------------------------------------------------------------

# TODO: parameter autocomplete does not work great with "option" as it cant complete correctly both param and value with
#       "nargs=2", autocomplete function does not get info which of the two args are "completed" so it will try to autocomplete
#       second arg with same rules...
#       ... some enhancement on Click library can be tested, or introduction of some custom Click.Option class ???

# TODO: Check click.edit for multiline edit option (info, or even params?)
# TODO: Add option to set user and address directly like in "create" command

@click.command(name="set", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-i", "--info", multiple=True, help=INFO_HELP)
@click.option("-p", "--parameter", nargs=2, multiple=True, help=PARAM_HELP, shell_complete=complete_params)
@click.option("-g", "--group", "target_group_name", help=GROUP_HELP, shell_complete=complete_ssh_group_names)
@click.option("-f", "--force", is_flag=True, help=FORCE_HELP)
@click.option("--yes", is_flag=True, help=YES_HELP)
@click.argument("names", nargs=-1, required=True, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, names, info, parameter, target_group_name, force, yes):
    config: SSH_Config = ctx.obj

    selected_hosts_list = expand_names(names, config.get_all_host_names())
    selected_hosts_list.sort()

    # For setting stuff, we confirm only if it applies on more hosts
    if not yes:
        if len(selected_hosts_list) > 1:
            print(f"Following hosts will be changed: [{','.join(selected_hosts_list)}]")
            if not click.confirm('Are you sure?'):
                ctx.exit(1)

    # When setting stuff on multiple hosts, iterate over them
    for host_name in selected_hosts_list:
        try:
            previous_group = config.get_host_by_name(host_name).group if config.check_host_by_name(host_name) else None
            update_host(
                config,
                host_name,
                info=info if info else None,
                parameters=parameter,
                target_group_name=target_group_name,
                force_group=force,
            )
        except SSHClickOpsError as exc:
            print(str(exc))
            ctx.exit(1)
        if target_group_name and previous_group == target_group_name:
            print(f"Host '{host_name}' already in group '{target_group_name}', group unchanged!")

    # Write out modified config
    if config.generate_ssh_config():
        print(f"Modified host: {','.join(selected_hosts_list)}")
