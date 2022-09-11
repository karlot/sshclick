from ..ssh_host import SSH_Host

from rich.table import Table
from rich.panel import Panel
from rich.console import Group
from rich import box

#------------------------------------------------------------------------------
# Render host data in panel without borders and minimal decorations
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type if host.type == "normal" else f"[cyan]{host.type}[/]"

    #// Add Host data information
    #// -----------------------------------------------------------------------
    panel_data = [
        f"[bright_white]Name [/]:  {host.name}",
        f"[bright_white]Group[/]:  {host.group}",
        f"[bright_white]Type [/]:  {out_type}",
    ]
    
    #// Add Host info data (if host info exist)
    #// -----------------------------------------------------------------------
    if host.info:
        out_info = "\n".join(host.info)
        panel_data = panel_data + [
            f"",
            f"[gray50]{out_info}[/]",
        ]
    host_panel = Panel("\n".join(panel_data), box=box.SIMPLE, border_style="grey35", padding=(0,0))

    #// Prepare table with params
    #// -----------------------------------------------------------------------
    param_table = Table(box=box.SIMPLE, style="grey35", show_header=True, show_edge=False, pad_edge=True)
    param_table.add_column("Param")
    param_table.add_column("Value")
    param_table.add_column("Inherited-from")

    # Add rows for SSH Config parameters
    for key, value in host.params.items():
        output_value = value if not isinstance(value, list) else "\n".join(value)
        param_table.add_row(key, output_value)

    # Add rows for inherited SSH Config parameters
    for pattern, pattern_params in host.inherited_params:
        for param, value in pattern_params.items():
            if not param in host.params:
                output_value = value if not isinstance(value, list) else "\n".join(value)
                param_table.add_row(param, output_value, pattern, style="yellow")

    param_table.add_row("")
    
    #// Render output
    #// -----------------------------------------------------------------------
    return Group(host_panel, param_table)