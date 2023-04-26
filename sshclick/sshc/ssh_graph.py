from typing import List
from rich.table import Table
from rich.text import Text
from rich.padding import Padding

from sshclick.sshc import SSH_Host

from rich import print
# from rich import inspect

# Fixed width for jump-proxy cell in graph table (Keep value as multiple of 2!)
MAX_CELL_SIZE = 26
PADDING_LR = (0,1)

HOST_NAME_COLOR = "bold white"
LOC_TUNNEL_COLOR = "cyan"
REM_TUNNEL_COLOR = "bold yellow"
ADDRESS_COLOR = {
    "online": "green",
    "offline": "red",
    "unchecked": "white",
}

# This are chars we use to draw...
LINK_UP = "│    │"
LINK_LR = "╯    ╰"
LINK_LR_EXT = "─"


# -----------------------------------------------------------------------------
# Graph generation function...
# -----------------------------------------------------------------------------
def generate_graph(traced_hosts: List[SSH_Host], print_tunnels=True):
    """
    Function that generates nice "graph" view of connected hosts
    """

    # TODO: This is currently static, but we could improve it, as in very long hostname
    #       it will result in broken lines, or alternatively in cut-off names
    reversed_hosts = traced_hosts[::-1]     # list of hosts in order of proxy-jumping

    # Create table with number of columns as we need to fit the data
    tbl = Table.grid()

    tbl.add_column(justify="right")                             # source column  
    for _ in range(len(traced_hosts) - 1):  
        tbl.add_column(justify="center", width=MAX_CELL_SIZE)   # proxy-jump columns
    tbl.add_column(justify="left")                              # target column

    # ----- Main graph row ----------------------------------------------------
    # Add Source info for main graph-row
    graph_row = [Padding(Text("\n".join([
        "Connection graph",
        "────────────────",
        "       THIS HOST",
        "  SSH Connection",
    ])),PADDING_LR)]

    # Add Jump proxies in graph-row
    for host in reversed_hosts[:-1]:
        # Status is filled by testing function before calling graph, so status is
        # already updated in given traced hosts
        host_status = host.params.get("status", "unchecked")
        address = f"[{ADDRESS_COLOR[host_status]}]{host.params.get('hostname', '')}[/]"

        graph_row.append(Padding(Text.from_markup("\n".join([
            f"[{HOST_NAME_COLOR}]{host.name}[/]",
            address,
            LINK_UP,
            LINK_LR.center(MAX_CELL_SIZE, LINK_LR_EXT),
        ]))))

    # Add Target info in graph-row
    target_status = reversed_hosts[-1].params.get("status", "unchecked")
    target_address = f"[{ADDRESS_COLOR[target_status]}]{reversed_hosts[-1].params.get('hostname', '')}[/]"

    graph_row.append(Padding(Text.from_markup("\n".join(["", "",
        "TARGET",
        f"[{HOST_NAME_COLOR}]{reversed_hosts[-1].name}[/]",
        target_address
    ])),PADDING_LR))

    # Add graph-row in the render table
    tbl.add_row(*graph_row)

    if print_tunnels:
        # ----- Local SSH tunnels row ---------------------------------------------
        # Print local forward tunnel between current host and target host
        if "localforward" in traced_hosts[0].params:
            tbl.add_row(*[Padding("Local SSH tunnels", PADDING_LR)])
            
            for tun in traced_hosts[0].params["localforward"]:
                tun_port, tun_end = tun.split()
                tunnel_row = [Padding(":" + tun_port, PADDING_LR)]
                for _ in range(len(traced_hosts) - 1):
                    tunnel_row.append(Padding(f"[{LOC_TUNNEL_COLOR}]{'>' * MAX_CELL_SIZE}[/]"))
                tunnel_row.append(Padding(tun_end, PADDING_LR))

                tbl.add_row(*tunnel_row)


        # ----- Remote SSH tunnels row --------------------------------------------
        # Print remote forward tunnel between current host and target host
        if "remoteforward" in traced_hosts[0].params:
            # trace.add_row(["" for _ in range(num_elements)])   # Empty row
            tbl.add_row(*[Padding("Remote SSH tunnels", PADDING_LR)])
            
            for tun in traced_hosts[0].params["remoteforward"]:
                tun_port, tun_end = tun.split()
                tunnel_row = [Padding(tun_end, PADDING_LR)]
                for _ in range(len(traced_hosts) - 1):
                    tunnel_row.append(Padding("<" * MAX_CELL_SIZE))
                tunnel_row.append(Padding(":" + tun_port, PADDING_LR))
                tbl.add_row(*tunnel_row)

    return tbl

