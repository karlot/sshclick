import click
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_group_names, expand_names

#------------------------------------------------------------------------------
# COMMAND: group delete
#------------------------------------------------------------------------------
SHORT_HELP = "Delete group"
LONG_HELP  = """
Delete group

Command accepts single or multiple groups names to delete.
If autocompletion is enabled, command will also offer current configured groups for TAB completion.
Alternatively when group "NAME" is specified with "r:" prefix, then value is used as regex match
to find all group names that match given pattern, and will expand target group list accordingly.

Regex matches and direct or autocompleted names can be mixed.
Group deletion will be prompted for confirmation.
"""

# Parameters help:
YES_HELP   = "Skip confirmation and assume 'yes'. Be careful!"
#------------------------------------------------------------------------------

@click.command(name="delete", short_help=SHORT_HELP, help=LONG_HELP)
@click.option("--yes", is_flag=True, help=YES_HELP)
@click.argument("names", nargs=-1, required=True, shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, names, yes):
    config: SSH_Config = ctx.obj

    selected_group_list = expand_names(names, config.get_all_group_names())
    selected_group_list.sort()

    # Deleting requires confirmation
    if not yes:
        print(f"Following groups will be deleted: [{','.join(selected_group_list)}]")
        if not click.confirm('Are you sure?'):
            ctx.exit(1)

    # When deleting multiple groups, iterate over all of them
    config_updated = False
    for name in selected_group_list:

        # Find group by name
        if not config.check_group_by_name(name):
            print(f"Cannot delete group '{name}', it is not defined in configuration!")
            continue

        config.groups.remove(config.get_group_by_name(name))
        config_updated = True

        if not config.stdout:
            print(f"Deleted group: {name}")

    # ReWrite config only when config was actually changed
    if config_updated:
        config.generate_ssh_config().write_out()
