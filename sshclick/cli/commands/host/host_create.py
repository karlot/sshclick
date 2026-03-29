import click
from sshclick.ops import SSHClickOpsError, create_host
from sshclick.core import SSH_Config
from sshclick.core import complete_ssh_group_names, complete_params

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
ADDR_HELP  = "Set host ip/hostname parameter directly (shortcut for 'hostname' parameter)"
USER_HELP  = "Set host user parameter directly (shortcut for 'user' parameter)"
PARAM_HELP = "Sets parameter for the host, takes 2 values (<sshparam> <value>). To unset/remove parameter from host, set its value to empty string like this (example: -p user '')"
GROUP_HELP = "Defined in which group host will be created, if not specified, 'default' group will be used"
FORCE_HELP = "Allows during host creation, to create group for host if target group is missing/not yet defined."
#------------------------------------------------------------------------------

@click.command(name="create", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("-a", "--address", help=ADDR_HELP)
@click.option("-u", "--user", help=USER_HELP)
@click.option("-i", "--info", multiple=True, help=INFO_HELP)
@click.option("-p", "--parameter", nargs=2, multiple=True, help=PARAM_HELP, shell_complete=complete_params)
@click.option("-g", "--group", "target_group_name", help=GROUP_HELP, shell_complete=complete_ssh_group_names)
@click.option("--force", is_flag=True, help=FORCE_HELP)
@click.argument("name")
@click.pass_context
def cmd(ctx, name, address, user, info, parameter, target_group_name, force):
    config: SSH_Config = ctx.obj

    try:
        create_host(
            config,
            name,
            address=address,
            user=user,
            info=info,
            parameters=parameter,
            target_group_name=target_group_name,
            force_group=force,
        )
    except SSHClickOpsError as exc:
        print(str(exc))
        ctx.exit(1)

    # Generate new config
    if config.generate_ssh_config():
        print(f"Created host: {name}")
