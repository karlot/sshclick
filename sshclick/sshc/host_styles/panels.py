from textwrap import dedent
from ..ssh_host import SSH_Host

from rich.table import Table
from rich.panel import Panel
from rich.console import Group
from rich import box

#------------------------------------------------------------------------------
# Render host data in panels with separate sections
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type if host.type == "normal" else f"[cyan]{host.type}[/]"
    out_info = "\n".join(host.info) if host.info else "- No info defined - "

    panel_data = f"""\
    [bright_white]Name [/]:  {host.name}
    [bright_white]Group[/]:  {host.group}
    [bright_white]Type [/]:  {out_type}\
    """
    host_panel = Panel(dedent(panel_data), border_style="grey35", title="Host", title_align="left")
    info_panel = Panel(out_info,           border_style="grey35", style="gray50", title="Info", title_align="left")

    param_table = Table(box=box.ROUNDED, style="grey35", show_header=True, show_edge=True, expand=True)
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

    panel_group = Group(host_panel, info_panel, param_table) if host.info else Group(host_panel, param_table)

    return Panel.fit(panel_group, box=box.SIMPLE, padding=(0,0))
