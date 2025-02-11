from ..ssh_host import SSH_Host, HostType

from rich.table import Table
from rich.panel import Panel
from rich import box

#------------------------------------------------------------------------------
# Render host data in panel with single-card look
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type.value if host.type == HostType.NORMAL else f"[cyan]{host.type.value}[/]"
    alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""

    #// Add Host data information
    #// -----------------------------------------------------------------------
    layout_table = Table("", box=box.ROUNDED, style="grey35" ,show_edge=True, show_header=False)
    layout_table.add_row(f"[bright_white]Name [/]:  {host.name}{alt_names}")
    layout_table.add_row(f"[bright_white]Group[/]:  {host.group}")
    layout_table.add_row(f"[bright_white]Type [/]:  {out_type}")

    #// Add Host info panel (if host info exist)
    #// -----------------------------------------------------------------------
    if host.info:
        layout_table.add_row("")
        out_info = "\n".join(host.info)
        layout_table.add_row(f"[gray50]{out_info}[/]")

    layout_table.add_row("")

    #// Prepare table with params and append it to the layout table
    #// -----------------------------------------------------------------------
    param_table = Table(box=box.SIMPLE, style="grey35", show_header=True, show_edge=False, pad_edge=False)
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

    layout_table.add_row(param_table)

    #// Render output
    #// -----------------------------------------------------------------------
    return Panel(layout_table, box=box.SIMPLE, padding=(0,0))
