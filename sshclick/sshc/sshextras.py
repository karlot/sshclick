# from rich.table import Table
from prettytable import PrettyTable

#TODO: Try to rework with Rich components !!!
def generate_graph(traced_hosts: list):
    """
    Function that generates nice "graph" view of connected hosts
    """

    # TODO: This is currently static, but we could improve it, as in very long hostname
    #       it will result in broken lines, or alternatively in cut-off names
    max_cell_size = 24   # Keep value as multiple of 2!

    def crop_str(string):
        string = (string[:max_cell_size-2] + '..') if len(string) > max_cell_size else string
        return string

    reversed_hosts = traced_hosts[::-1]
    num_elements = len(traced_hosts) + 1

    # We use prettytable as way to organize graph in columns then print it
    # without usual decorators such as borders and headers, to get graph
    trace = PrettyTable()
    trace.add_column("local", [
        " Connection graph   ",
        "  ────────────────  ",
        "         THIS HOST  ",
        "    SSH Connection ─",
        "                    ",
    ], align="r")

    last_index = len(traced_hosts) - 1
    cp = int((max_cell_size - 6) / 2)  #cell_padding
    for i, host in enumerate(reversed_hosts):
        if i != last_index:
            # Add Jump proxies
            trace.add_column(host.name, [
                crop_str(host.name),                       # SSH Host     (could be long name)
                crop_str(host.params.get("hostname", "")),                   # SSH HostName (usually IP, but can also be long fqdn)
                " " * cp + "│    │" + " " * cp,
                "─" * cp + "╯    ╰" + "─" * cp,
                "",
            ])
        else:
            # Target (last) element
            trace.add_column("target", [
                "         ",
                "         ",
                "  TARGET",
                "─ " + host.name,
                "  " + host.params.get("hostname", ""),
            ], align="l")

    # Print local forward tunnel between current host and target host
    if "localforward" in traced_hosts[0].params:
        # trace.add_row(["" for _ in range(num_elements)])   # Empty row
        trace.add_row(["Local SSH tunnels  "] + ["" for _ in range(num_elements - 1)])
        
        for tun in traced_hosts[0].params["localforward"]:
            tunnel_row = []
            tun_port, tun_end = tun.split()
            for i in range(num_elements):
                if i == 0:                                      # Fill source column (aligned R)
                    tunnel_row.append(f":{tun_port} >")
                elif i != num_elements - 1:                     # Add Jump proxies   (aligned M)
                    tunnel_row.append(">" * max_cell_size)
                else:                                           # Fill last/target   (aligned L)
                    tunnel_row.append("> " + tun_end)
            trace.add_row(tunnel_row)

    # Print remote forward tunnel between current host and target host
    if "remoteforward" in traced_hosts[0].params:
        # trace.add_row(["" for _ in range(num_elements)])   # Empty row
        trace.add_row(["Remote SSH tunnels:  "] + ["" for _ in range(num_elements - 1)])
        
        for tun in traced_hosts[0].params["remoteforward"]:
            tunnel_row = []
            tun_port, tun_end = tun.split()
            for i in range(num_elements):
                if i == 0:                                      # Fill source column (aligned R)
                    tunnel_row.append(f"{tun_end} <")
                elif i != num_elements - 1:                     # Add Jump proxies   (aligned M)
                    tunnel_row.append("<" * max_cell_size)
                else:                                           # Fill last/target   (aligned L)
                    tunnel_row.append("< :" + tun_port)
            trace.add_row(tunnel_row)

    # Remove all decorations from cells
    trace.header = False
    trace.border = False
    trace.padding_width = 0
    return trace.get_string()

