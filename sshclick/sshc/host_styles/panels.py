from typing import Union
from textwrap import dedent
from ..ssh_host import SSH_Host, HostType

from rich.table import Table
from rich.panel import Panel
from rich.console import Group
from rich import box

#------------------------------------------------------------------------------
# Render host data in panels with separate sections
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    out_type = host.type.value if host.type == HostType.NORMAL else f"[cyan]{host.type.value}[/]"
    out_info = "\n".join(host.info) if host.info else "- No info defined - "
    alt_names = " (" + ",".join(host.alt_names) + ")" if host.alt_names else ""

    grp_inputs: list[Union[Table,Panel]] = []

    #// Add Host data panel to the group
    #// -----------------------------------------------------------------------
    host_panel_data = f"""\
    [bright_white]Name [/]:  {host.name}{alt_names}
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

    grp_inputs.append(param_table)

    #// Render output
    #// -----------------------------------------------------------------------
    return Panel.fit(Group(*grp_inputs), box=box.SIMPLE, padding=(0,0))
