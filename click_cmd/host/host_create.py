import click
from lib.sshutils import *
# from click_cmd.host import host_show


#------------------------------------------------------------------------------
# COMMAND: host create
#------------------------------------------------------------------------------
@click.command(name="create", help="Create new host configuration")
@click.option("-g", "--group", default=DEFAULT_GROUP_NAME, help="Sets group for the host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format")
@click.argument("name")
@click.pass_context
def cmd(ctx, name, group, parameter):
    config = ctx.obj['CONFIG']

    found_host, _ = find_host_by_name(config, name, exit_on_fail=False)
    if found_host:
        error(f"Cannot create host '{name}' as it already exists!")
        exit(1)
    
    # Find group by name where to store config
    found_group = find_group_by_name(config, group)

    new_host = {
        "name": name
    }

    # Add all passed parameters to config
    # TODO: here we need to implement validation for all "known" parameters that can be used, and possibly
    # some normalization to documented "CamelCase" format
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()
        if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            if not param in new_host:
                new_host[param] = [value]
            else:
                new_host[param].append(value)
        else:
            new_host[param] = value

    group_target = "patterns" if "*" in name else "hosts"
    found_group[group_target].append(new_host)

    # Invoke "host show" command to display new host that is being created
    # ctx.invoke(host_show.cmd, name=name, graph=False)

    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
