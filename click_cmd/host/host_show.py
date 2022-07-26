import click
from lib.sshutils import *
from lib.colors import *


#------------------------------------------------------------------------------
# COMMAND: host show
#------------------------------------------------------------------------------
@click.command(name="show", help="Display info for host")
@click.option("--follow", is_flag=True, help="Follow and displays all connected jump-proxy hosts")
@click.option("--graph/--no-graph", default=True, help="Shows connection to target as graph (default:true)")
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.pass_context
def cmd(ctx, name, follow, graph):
    config = ctx.obj['CONFIG']

    traced_hosts = []
    traced_host_tables = []

    # Python does not have "do while" loop. (ಠ_ಠ)
    # we are first checking host that is asked, and then check if that host has a "proxy" defined
    # if proxy is defined, we add found host to traced list, and search attached proxy, it his way we
    # can trace full connection path for later graph processing
    while True:
        # At start assume host is "normal" and contains no inherited parameters
        inherited_params = {}

        # Search for host in current configuration
        found_host, found_group = find_host_by_name(config, name)

        # If this host is "pattern" type
        if "*" in name:
            host_type = cyan("pattern")
        else:
            host_type = "normal"
            inherited_params = find_inherited_params(name, config)

        # Prepare table for host output
        x = PrettyTable(field_names=["Parameter", "Value", "Inherited-from"])
        x.align = "l"
        x.add_row(["name",  found_host["name"],  ""])
        x.add_row(["group", found_group["name"], ""])
        x.add_row(["info",  found_host["hostinfo"], ""])
        x.add_row(["type",  host_type,           ""])

        # Add rows for direct parameters
        for key, value in found_host.items():
            if key in ["name", "hostinfo"]:
                continue
            x.add_row([f"param:{key}", value if not isinstance(value, list) else "\n".join(value), ""])

        # Add rows for inherited parameters
        for pattern, data in inherited_params.items():
            for param, value in data.items():
                if not param in found_host:
                    if isinstance(value, list):
                        x.add_row([f"param:{param}", "\n".join([yellow(v) for v in value]), yellow(pattern)])
                    else:
                        x.add_row([f"param:{param}", yellow(value), yellow(pattern)])
                    found_host[param] = value

        # Add current host, and its table to traced lists
        traced_hosts.append(found_host)
        traced_host_tables.append(x)

        # Depending on proxy info in parameters, we continue or exit the loop
        if "proxyjump" in found_host:
            name = found_host["proxyjump"]
        else:
            break

    # Print collected host table(s)
    # In follow mode we print all connected host tables, otherwise we print only target host table
    if not follow:
        print(traced_host_tables[0])
    else:
        for i, table in enumerate(traced_host_tables):
            print(table)
            if i < len(traced_host_tables) - 1:
                print(green("  | via jump proxy"))
        
    if graph:
        print("\n" + generate_graph(traced_hosts) + "\n")
