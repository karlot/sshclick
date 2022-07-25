import click
from lib.sshutils import *


#------------------------------------------------------------------------------
# COMMAND: host set
#------------------------------------------------------------------------------
@click.command(name="set", help="Changes/sets host configuration parameters")
@click.option("-g", "--group", "target_group_name", default=None, help="Changes group for host")
@click.option("-r", "--rename", default=None, help="Rename host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format, to unset/remove parameter from host, set it to empty value (example: 'param=')")
@click.option("--force", is_flag=True, default=False, help="Forces moving host to group that does not exist, by creating new group, and moving host to that group.")
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, target_group_name, rename, parameter, force):
    config = ctx.obj['CONFIG']

    # Nothing was provided
    if not target_group_name and not rename and not parameter:
        error("Calling set without setting anything is not valid. Run with '-h' for help.")
        exit(1)

    found_host, found_group = find_host_by_name(config, name)
    
    # Move host to different group
    if target_group_name:
        # Find target group
        target_group = find_group_by_name(config, target_group_name, exit_on_fail=False)
        if not target_group:
            if not force:
                error(f"Cannot move host '{name}' to group '{target_group_name}' which does not exist! Consider using --force to automatically create target group.")
                exit(1)
            else:
                # Create new group
                new_group = {
                    "name": target_group_name,
                    "desc": None,
                    "info": [],
                    "hosts": [],
                    "patterns": [],
                }
                # Add new group to config and set it as target group
                config.append(new_group)
                target_group = new_group

        # Add host to target group
        if "*" in name:
            target_group["patterns"].append(found_host)
        else:
            target_group["hosts"].append(found_host)

        # Remove from source group
        if found_host in found_group["hosts"]:
            found_group["hosts"].remove(found_host)
        if found_host in found_group["patterns"]:
            found_group["patterns"].remove(found_host)
        
    # Rename a host
    if rename:
        found_host["name"] = rename
    
    # Sets parameters for host (or erase them if value is provided as unset)
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()            # lowercase keyword/param as they are case insensitive
        if value:
            if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                if not param in found_host:
                    found_host[param] = [value]
                else:
                    if value in found_host[param]:
                        error(f"Cannot add existing value '{value}' to host parameter '{param}' multiple times!")
                    else:
                        found_host[param].append(value)
            else:
                found_host[param] = value
        else:
            if param in found_host:
                found_host.pop(param)
            else:
                error(f"Cannot unset parameter that is not defined!")

    print(f"Modified host: {name}")

    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
