import click
from prettytable import PrettyTable


#------------------------------------------------------------------------------
# COMMAND: group list
#------------------------------------------------------------------------------
@click.command(name="list", help="Lists all groups")
@click.pass_context
def cmd(ctx):
    config = ctx.obj['CONFIG']

    x = PrettyTable(field_names=["Name", "Hosts", "Desc"])
    x.align = "l"
    x.align["Hosts"] = "r"

    for group in config:
        x.add_row([group["name"], len(group["hosts"]), group["desc"]])

    print(x)
