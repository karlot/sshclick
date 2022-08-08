import click
from sshclick.globals import *
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# COMMAND: host create
#------------------------------------------------------------------------------
@click.command(name="create", help="Create new host configuration")
@click.option("-g", "--group", "target_group_name", default=DEFAULT_GROUP_NAME, help="Sets group for the host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format")
@click.option("--force", is_flag=True, default=False, help="Forces automatically create group for host if group is missing")
@click.argument("name")
@click.pass_context
def cmd(ctx, name, target_group_name, parameter, force):
    config: SSH_Config = ctx.obj

    found_host, _ = config.find_host_by_name(name, throw_on_fail=False)
    if found_host:
        print(f"Cannot create host '{name}' as it already exists in configuration!")
        ctx.exit(1)
    
    # Find group by name where to store config
    found_group = config.find_group_by_name(target_group_name, throw_on_fail=False)
    if not found_group:
        if not force:
            print(f"Cannot create host '{name}' in group '{target_group_name}' since the group does not exist")
            print("Create group first, or use '--force' option to create it automatically!")
            ctx.exit(1)
        else:
            # Create new group
            new_group = SSH_Group(name=target_group_name)
            # Add new group to config and set it as target group
            config.groups.append(new_group)
            found_group = new_group

    # This is patter host
    target_type = "pattern" if "*" in name else "normal"
    new_host = SSH_Host(name=name, group=target_group_name, type=target_type)

    # Add all passed parameters to config
    # TODO: here we need to implement validation for all "known" parameters that can be used, and possibly
    # some normalization to documented "CamelCase" format
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()           # parametar keyword will be lowercased as they are case insensitive
        if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            # We need to handle host parameter as "list"
            if not param in new_host.params:
                new_host.params[param] = [ value ]
            else:
                new_host.params[param].append(value)
        else:
            # Simple single keyword
            new_host.params[param] = value

    if new_host.type == "normal":
        found_group.hosts.append(new_host)
    else:
        found_group.patterns.append(new_host)

    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Created host: {name}")
