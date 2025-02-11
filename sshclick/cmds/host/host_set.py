import click
from sshclick.sshc import SSH_Config, SSH_Group
from sshclick.sshc import complete_ssh_host_names, complete_ssh_group_names, complete_params, expand_names
from sshclick.sshc import PARAMS_WITH_ALLOWED_MULTIPLE_VALUES

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

    # Nothing was provided
    if not target_group_name and not parameter and not info:
        print("Calling set without setting anything is not valid on host(s). Run with 'sshc host set -h' for help.")
        ctx.exit(1)

    # For setting stuff, we confirm only if it applies on more hosts
    if not yes:
        if len(selected_hosts_list) > 1:
            print(f"Following hosts will be changed: [{','.join(selected_hosts_list)}]")
            if not click.confirm('Are you sure?'):
                ctx.exit(1)

    # When setting stuff on multiple hosts, iterate over them
    for host_name in selected_hosts_list:
        if not config.check_host_by_name(host_name):
            print(f"Unknown host '{host_name}'!")
            ctx.exit(1)

        current_host = config.get_host_by_name(host_name)
        current_group = config.get_group_by_name(current_host.group)
        
        # Defined "target" group provided, we have to check if we can move host to different group
        if target_group_name:
            # Check if current and target group names are the same
            if target_group_name == current_host.group:
                print(f"Host '{host_name}' already in group '{target_group_name}', group unchanged!")

            else:
                # Find target group
                if config.check_group_by_name(target_group_name):
                    # Move host to target group
                    target_group = config.get_group_by_name(target_group_name)
                    config.move_host_to_group(current_host, current_group, target_group)
                else:
                    if force:
                        target_group = SSH_Group(name=target_group_name)
                        config.groups.append(target_group)
                        # Move host to target group
                        config.move_host_to_group(current_host, current_group, target_group)
                    else:
                        print(f"Cannot move host '{host_name}' to group '{target_group_name}' which does not exist!")
                        print("Consider using --force to automatically create target group, or create it manually first.")
                        ctx.exit(1)
                        exit(1) # unreachable, but avoids issues with static checks
            
        # Update info (appending if value is passed, clearing the list if value is empty)
        if info:
            if len(info[0]) > 0:
                current_host.info = current_host.info + list(info)
            else:
                current_host.info = []

        # Sets parameters for host
        for param, value in parameter:
            param = param.lower()            # lowercase keyword/param as they are case insensitive
            if value:
                if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                    if not param in current_host.params:
                        current_host.params[param] = [value]
                    else:
                        if value in current_host.params[param]:
                            print(f"Cannot add existing value '{value}' to host parameter '{param}' multiple times!")
                        else:
                            current_host.params[param].append(value)
                else:
                    current_host.params[param] = value
            else:
                if param in current_host.params:
                    current_host.params.pop(param)
                else:
                    print(f"Cannot unset parameter that is not defined!")

        if not config.stdout and not config.diff:
            print(f"Modified host: {host_name}")

    # Write out modified config
    if config.generate_ssh_config(): config.write_out()
