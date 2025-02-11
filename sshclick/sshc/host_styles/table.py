from ..ssh_host import SSH_Host, HostType

from rich.table import Table
from rich import box

#------------------------------------------------------------------------------
# Render host data in single flat 3-column table
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type.value if host.type == HostType.NORMAL else f"[cyan]{host.type.value}[/]"
    out_info = "\n".join(host.info) if host.info else ""
    alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""

    table = Table(box=box.SQUARE, style="grey39")
    table.add_column("Parameter")
    table.add_column("Value")
    table.add_column("Inherited-from")
    
    table.add_row("Name",  host.name + alt_names)
    table.add_row("Group", host.group)
    table.add_row("Type",  str(out_type))
    table.add_row("Info",  out_info, style="grey50")
    
    # Add rows for SSH Config parameters
    for param in host.get_all_params():
        value, source = host.get_applied_param(param)
        output_value = value if not isinstance(value, list) else "\n".join(value)
        if source == "local":
            table.add_row(f"Param:{param}", output_value)
        elif source == "global":
            table.add_row(f"Param:{param}", output_value, "global", style="green")
        else:
            table.add_row(f"Param:{param}", output_value, source, style="yellow")

    return table

