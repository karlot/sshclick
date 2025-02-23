import click
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host, HostType
from sshclick.sshc import complete_ssh_group_names, complete_params
from sshclick.sshc import PARAMS_WITH_ALLOWED_MULTIPLE_VALUES
from sshclick.globals import DEFAULT_GROUP_NAME

#------------------------------------------------------------------------------
# COMMAND: host create
#------------------------------------------------------------------------------
SHORT_HELP = "Create new host"
LONG_HELP  = """
Create new host and save it to config file

Command can be used to create a single HOST definition, and also set definitions within single command.
Later definitions can be changes with "sshc host set" commands.

If autocomplete is enabled, command will try to give suggestions for your inputs on definition of GROUP and well known PARAM names.
"""

# Parameters help:
INFO_HELP  = "Set host info, can be set multiple times, or set to empty value to clear it (example: -i '')"
PARAM_HELP = "Sets parameter for the host, takes 2 values (<sshparam> <value>). To unset/remove parameter from host, set its value to empty string like this (example: -p user '')"
GROUP_HELP = "Defined in which group host will be created, if not specified, 'default' group will be used"
FORCE_HELP = "Allows during host creation, to create group for host if target group is missing/not yet defined."
#------------------------------------------------------------------------------

@click.command(name="create", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-i", "--info", multiple=True, help=INFO_HELP)
@click.option("-p", "--parameter", nargs=2, multiple=True, help=PARAM_HELP, shell_complete=complete_params)
@click.option("-g", "--group", "target_group_name", help=GROUP_HELP, shell_complete=complete_ssh_group_names)
@click.option("--force", is_flag=True, help=FORCE_HELP)
@click.argument("name")
@click.pass_context
def cmd(ctx, name, info, parameter, target_group_name, force):
    config: SSH_Config = ctx.obj

    if not target_group_name:
        target_group_name = DEFAULT_GROUP_NAME

    if config.check_host_by_name(name):
        print(f"Cannot create host '{name}' as it already exists in configuration!")
        ctx.exit(1)
        
    # Find group by name where to store config
    if config.check_group_by_name(target_group_name):
        target_group = config.get_group_by_name(target_group_name)
    else:
        if force:
            target_group = SSH_Group(name=target_group_name)
            config.groups.append(target_group)
        else:
            print(f"Cannot create host '{name}' in group '{target_group_name}' since the group does not exist")
            print("Create group first, or use '--force' option to create it automatically!")
            ctx.exit(1)
            exit(1) # unreachable, but avoids issues with static checks

    # This is patter host
    target_type = HostType.PATTERN if "*" in name else HostType.NORMAL
    new_host = SSH_Host(name=name, group=target_group_name, type=target_type, info=list(info))

    # Add all passed parameters to config
    for param, value in parameter:
        # parameter keyword will be lowercased as they are case insensitive
        param = param.lower()
        if not value or value.isspace():
            print(f"Cannot define empty value for parameter during host creation!")
            ctx.exit(1)
        if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            # We need to handle host parameter as "list"
            if not param in new_host.params:
                new_host.params[param] = [ value ]
            else:
                new_host.params[param].append(value)
        else:
            # Simple single keyword
            new_host.params[param] = value

    # Append new host to the group
    if target_type == HostType.NORMAL:
        target_group.hosts.append(new_host)
    else:
        target_group.patterns.append(new_host)

    if not config.stdout and not config.diff:
        print(f"Created host: {name}")

    # Generate new config
    if config.generate_ssh_config(): config.write_out()
