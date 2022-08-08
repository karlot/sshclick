import imp
import click
from sshclick.globals import *
from sshclick.sshc import SSH_Config, SSH_Group, complete_ssh_host_names


#TODO: Check click.edit for multiline edit option (info, or even params?)

#------------------------------------------------------------------------------
# COMMAND: host set
#------------------------------------------------------------------------------
@click.command(name="set")
@click.option("-g", "--group", "target_group_name", default=None, help="Changes group for host")
@click.option("-r", "--rename", default=None, help="Rename host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format, to unset/remove parameter from host, set it to empty value (example: param='')")
@click.option("-i", "--info", default=None, multiple=True, help="Set host info, can be set multiple times, or set to empty value to clear it (example: info='')")
@click.option("--force", is_flag=True, default=False, help="Forces moving host to group that does not exist, by creating new group, and moving host to that group.")
@click.argument("names", nargs=-1, shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, names, target_group_name, rename, parameter, info, force):
    """
    Changes/sets host(s) configuration parameters

    Multiple hosts can be specified, and can be set (moved) to different group, set/unset
    parameter or information lines. It is only not possible to "rename" multiple hosts!
    """

    config: SSH_Config = ctx.obj

    # Nothing was provided
    if not target_group_name and not rename and not parameter and not info:
        print("Calling set without setting anything is not valid on host(s). Run with 'sshc host set -h' for help.")
        ctx.exit(1)

    # When multiple hosts are defined, we cannot rename, as it makes no sense 
    if len(names) > 1:
        if rename:
            print(f"Cannot rename multiple hosts ({len(names)}) to same name ({rename}) is not supported")
            ctx.exit(1)

    for name in names:
        found_host, found_group = config.find_host_by_name(name, throw_on_fail=False)
        if not found_host:
            print(f"Cannot set anything on host '{name}' as it is not defined in configuration!")
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

        # Add info
        if info:
            if len(info[0]) > 0:
                found_host.info = info
            else:
                found_host.info = []

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

        if not config.stdout:
            print(f"Modified host: {name}")

    # Write out modified config
    config.generate_ssh_config().write_out()
