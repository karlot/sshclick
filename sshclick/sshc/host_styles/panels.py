from typing import Union, List
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

    grp_inputs: List[Union[Table,Panel]] = []

    #// Add Host data panel to the group
    #// -----------------------------------------------------------------------
    host_panel_data = f"""\
    [bright_white]Name [/]:  {host.name}
    [bright_white]Group[/]:  {host.group}
    [bright_white]Type [/]:  {out_type}\
    """
    grp_inputs.append(Panel(dedent(host_panel_data), border_style="grey35", title="Host", title_align="left"))

    #// Add Host info panel to the group (if host info exist)
    #// -----------------------------------------------------------------------
    if host.info:
        grp_inputs.append(Panel(out_info, border_style="grey35", style="gray50", title="Info", title_align="left"))

    #// Prepare table with params and append it to the group
    #// -----------------------------------------------------------------------
    param_table = Table(box=box.ROUNDED, style="grey35", show_header=True, show_edge=True, expand=True)
    param_table.add_column("Param")
    param_table.add_column("Value")
    param_table.add_column("Inherited-from")

    # Add rows for SSH Config parameter table
    for key, value in host.params.items():
        output_value = value if not isinstance(value, list) else "\n".join(value)
        param_table.add_row(key, output_value)

    # Add rows for inherited SSH Config parameters
    for pattern, pattern_params in host.inherited_params:
        for param, value in pattern_params.items():
            if not param in host.params:
                output_value = value if not isinstance(value, list) else "\n".join(value)
                param_table.add_row(param, output_value, pattern, style="yellow")

    grp_inputs.append(param_table)

    #// Render output
    #// -----------------------------------------------------------------------
    return Panel.fit(Group(*grp_inputs), box=box.SIMPLE, padding=(0,0))
