from ..ssh_host import SSH_Host

from rich.table import Table
from rich import box

#------------------------------------------------------------------------------
# Render host data in single flat 3-column table
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type if host.type == "normal" else f"[cyan]{host.type}[/]"
    out_info = "\n".join(host.info) if host.info else "- No info defined - "

    table = Table(box=box.SQUARE, style="grey39")
    table.add_column("Parameter")
    table.add_column("Value")
    table.add_column("Inherited-from")
    
    table.add_row("Name",  host.name)
    table.add_row("Group", host.group)
    table.add_row("Type",  out_type)
    table.add_row("Info",  out_info, style="grey50")
    
    # Add rows for SSH Config parameters
    for key, value in host.params.items():
        output_value = value if not isinstance(value, list) else "\n".join(value)
        table.add_row(f"Param:{key}", output_value)

    # Add rows for inherited SSH Config parameters
    for pattern, pattern_params in host.inherited_params:
        for param, value in pattern_params.items():
            if not param in host.params:
                output_value = value if not isinstance(value, list) else "\n".join(value)
                table.add_row(f"param:{param}", output_value, pattern, style="yellow")
    
    return table

