import click
from ssh_globals import *
from lib.sshutils import SSH_Config, SSH_Group
from rich.pretty import pprint

#------------------------------------------------------------------------------
# COMMAND: host set
#------------------------------------------------------------------------------
@click.command(name="set", help="Changes/sets host configuration parameters")
@click.option("-g", "--group", "target_group_name", default=None, help="Changes group for host")
@click.option("-r", "--rename", default=None, help="Rename host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format, to unset/remove parameter from host, set it to empty value (example: 'param=')")
@click.option("--force", is_flag=True, default=False, help="Forces moving host to group that does not exist, by creating new group, and moving host to that group.")
# @click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("name")
@click.pass_context
def cmd(ctx, name, target_group_name, rename, parameter, force):
    config: SSH_Config = ctx.obj['CONFIG']

    # Nothing was provided
    if not target_group_name and not rename and not parameter:
        print("Calling set without setting anything is not valid. Run with '-h' for help.")
        ctx.exit(1)

    found_host, found_group = config.find_host_by_name(name, throw_on_fail=False)
    if not found_host:
        print(f"Cannot set anything on host '{name}' as host does not exist!")
        ctx.exit(1)
    
    # Move host to different group
    if target_group_name:
        # Find target group
        target_group = config.find_group_by_name(target_group_name, throw_on_fail=False)
        if not target_group:
            if not force:
                print(f"Cannot move host '{name}' to group '{target_group_name}' which does not exist!")
                print("Consider using --force to automatically create target group.")
                exit(1)
            else:
                # Create new group
                new_group = SSH_Group(name=target_group_name)
                # Add new group to config and set it as target group
                config.groups.append(new_group)
                target_group = new_group

        # Add host to target group
        if found_host.type == "normal":
            target_group.hosts.append(found_host)
            found_group.hosts.remove(found_host)
        else:
            target_group.patterns.append(found_host)
            found_group.patterns.remove(found_host)
        
    # Rename a host
    if rename:
        found_host.name = rename
    
    # Sets parameters for host (or erase them if value is provided as unset)
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()            # lowercase keyword/param as they are case insensitive
        if value:
            if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                if not param in found_host.params:
                    found_host.params[param] = [value]
                else:
                    if value in found_host.params[param]:
                        print(f"Cannot add existing value '{value}' to host parameter '{param}' multiple times!")
                    else:
                        found_host.params[param].append(value)
            else:
                found_host.params[param] = value
        else:
            if param in found_host.params:
                found_host.params.pop(param)
            else:
                print(f"Cannot unset parameter that is not defined!")

    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Modified host: {name}")
