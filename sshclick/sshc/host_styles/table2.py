from ..ssh_host import SSH_Host, HostType

from rich.table import Table
from rich.panel import Panel
from rich import box

#------------------------------------------------------------------------------
# Render host data in nested table with separate SSH parameters
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type.value if host.type == HostType.NORMAL else f"[cyan]{host.type.value}[/]"
    out_info = "\n".join(host.info) if host.info else "- No info defined - "
    alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""

    outer_table = Table(box=box.SQUARE, style="grey35", show_header=False)
    outer_table.add_column("Parameter")
    outer_table.add_column("Value")

    outer_table.add_row("Name",  host.name + alt_names)
    outer_table.add_row("Group", host.group)
    outer_table.add_row("Type",  str(out_type))
    outer_table.add_row("Info",  Panel(out_info, border_style="grey35", style="grey50"))

    param_table = Table(box=box.SQUARE, style="grey35", show_header=True, show_edge=True, expand=True)
    param_table.add_column("Param")
    param_table.add_column("Value")
    param_table.add_column("Inherited-from")

    # Add rows for SSH Config parameters
    for param in host.get_all_params():
        value, source = host.get_applied_param(param)
        output_value = value if not isinstance(value, list) else "\n".join(value)
        if source == "local":
            param_table.add_row(param, output_value)
        elif source == "global":
            param_table.add_row(param, output_value, "global", style="green")
        else:
            param_table.add_row(param, output_value, source, style="yellow")

    outer_table.add_row("SSH Params", param_table)
    return outer_table
