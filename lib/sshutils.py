import re
import fnmatch
from prettytable import PrettyTable

from ssh_globals import *
from lib.mylog import *


def parse_ssh_config(file):
    """ Main SSH config parsing function

    Function scrapes given ssh config file and generate structured data
    representation of given configuration file.
    """
    # Our parsed config map (array of "groups")
    config = [{
        "name": DEFAULT_GROUP_NAME,
        "desc": "",
        "info": [],
        "hosts": [],
        "patterns": [],
    }]

    # Read ssh config location 
    with open(file) as ssh_conf_file:
        conf_lines = ssh_conf_file.readlines()

        # Keep track of where we are...
        curr_group_index = 0
        host = None

        # Parse each line of the configuration, line by line
        for config_line_index, line in enumerate(conf_lines):
            line = line.strip()     # remove start and end whitespace

            # Ignore empty lines 
            if not line:
                continue
            
            # Process special metadata for grouping: "#@group", "#@desc", "#@info"
            if line.startswith("#@"):
                match = re.search("^#@(\w+):\s*(.+)$", line)

                # In case special comment is unreadable
                if not match:
                    warn(f"Unmatched metadata line {line} on SSH-config line number {config_line_index}")
                    continue
                
                metadata, value = match.groups()
                if metadata == "group":
                    # New group found... flush any previous data and create new baseline
                    if host:
                        debug(f"Found new 'group' metadata, appending to group ({config[curr_group_index]['name']}) collected host info: {host}")
                        # Check if host is actually pattern or regular host
                        if "*" in host['name']:
                            debug(f"{host['name']} is pattern!")
                            config[curr_group_index]["patterns"].append(host)
                        else:
                            debug(f"{host['name']} is normal host!")
                            config[curr_group_index]["hosts"].append(host)
                        host = None

                    debug(f"Starting new group: {value}")
                    config.append({
                        "name": value,
                        "desc": None,
                        "info": [],
                        "hosts": [],
                        "patterns": [],
                    })
                    curr_group_index = len(config) - 1
                    debug(f"Group index set to: {curr_group_index}")
                    continue
                elif metadata == "desc":
                    debug(f"Setting 'desc' param to '{value}' for group '{config[curr_group_index]['name']}'")
                    config[curr_group_index]["desc"] = value
                    continue
                elif metadata == "info":
                    debug(f"Setting 'info' param to '{value}' for group '{config[curr_group_index]['name']}'")
                    config[curr_group_index]["info"].append(value)
                    continue
                else:
                    warn(f"Unhandled metadata metadata '{metadata}' on SSH-config line number {config_line_index}")
                    continue

            # Ignore rest of commented lines
            if line.startswith("#"):
                debug(f"Discarding: {line}")
                continue

            # Here we expect only normal ssh config lines "Host" is usually the keyword that begins definition
            # if we find any other keyword before first host keyword is defined, configuration is wrong probably
            match = re.search("^(\w+)\s+(.+)$", line)
            if not match:
                warn(f"Incorrect configuration line '{line}' on SSH-config line number {config_line_index}")
                continue

            keyword, value = match.groups()
            keyword = keyword.lower()         # keywords are case insensitive, so we lowercase them

            if keyword == "host":
                # A definition of "host" is starting, if host is previously defined, we need to store its data and
                # reset any specific host metadata
                if host:
                    # Save current last pending host info
                    debug(f"Found new 'host' keyword, appending to group ({config[curr_group_index]['name']}) collected host info: {host}")

                    # Check if host is actually pattern or regular host
                    if "*" in host["name"]:
                        debug(f"{host['name']} is pattern!")
                        config[curr_group_index]["patterns"].append(host)
                    else:
                        debug(f"{host['name']} is normal host!")
                        config[curr_group_index]["hosts"].append(host)
                    # host = None

                debug(f"generating new host info for: {value}")
                host = {
                    "name": value,
                }
                # Reset host specific values when we find new host definition
                continue
            else:
                # any other normal line we just use as it is, wrong or not... :)
                # Currently there is no support for keyword validation
                if not host:
                    warn(f"Config info without Host definition on SSH-config line number {config_line_index}")
                    exit(1)
                else:
                    debug(f"Config keyword for host '{host['name']}': {keyword} -> {value}")
                    # Save any specific info...
                    if keyword in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                        if not keyword in host:
                            host[keyword] = [value]
                        else:
                            host[keyword].append(value)
                    else:
                        host[keyword] = value
                        continue
        
        # Last entries must be flushed manually as there are no new "hosts" to trigger storing parsed data into config struct
        if host:
            debug(f"Found leftover un-flushed host info, appending to group ({config[curr_group_index]['name']}) collected host info: {host}")
            # Check if host is actually pattern or regular host
            # print(host["name"])
            if "*" in host["name"]:
                debug(f"{host['name']} is pattern!")
                config[curr_group_index]["patterns"].append(host)
            else:
                debug(f"{host['name']} is normal host!")
                config[curr_group_index]["hosts"].append(host)
            host = None
        
    return config


def generate_ssh_config(config):
    """ SSH config generation function

    Function takes config data structure, and target file information.
    Then generated SSH config compatible file with all data, compatible with
    internal object model.
    """

    # First we prepare all lines before we flush them into file
    lines = ["#<<<<< SSH Config file managed by sshclick >>>>>\n"]

    for group in config:
        # Ship default group as it does not have to be specified
        render_header = False if group['name'] == "default" else True
        
        if render_header:
            # Start header line for the group with known metadata
            lines.append(f"#{'-'*79}\n")        # add horizontal decoration line
            lines.append(f"#@group: {group['name']}\n")
            if group['desc']:
                lines.append(f"#@desc: {group['desc']}\n")
            for info in group['info']:
                lines.append(f"#@info: {info}\n")
            lines.append(f"#{'-'*79}\n")        # add horizontal decoration line
        # Append hosts from each group
        for host in group["hosts"]:
            lines.append(f"Host {host['name']}\n")
            for token, value in host.items():
                if token == "name":
                    continue
                if type(value) is list:
                    for v in value:
                        lines.append(f"    {token} {v}\n")
                else:
                    lines.append(f"    {token} {value}\n")
            lines.append( "\n")
        # Append pattern last (as this is usual and probably most correct way)
        for pattern in group["patterns"]:
            lines.append(f"Host {pattern['name']}\n")
            for token, value in pattern.items():
                if token == "name":
                    continue
                if type(value) is list:
                    for v in value:
                        lines.append(f"    {token} {v}\n")
                else:
                    lines.append(f"    {token} {value}\n")
            lines.append( "\n")
        # Add extra line separation between groups
        lines.append( "\n")
    return lines


def write_ssh_config(ctx, lines):
    """ Write generated SSH config to target file """
    if ctx.obj["STDOUT"]:
        print("".join(lines))
    else:
        with open(ctx.obj["USER_CONF_FILE"], "w") as out:
            out.writelines(lines)
        

# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d, ignored=[]):
    return {k: v for (k, v) in d.items() if k not in ignored}


def get_all_host_names(config):
    all_hosts = []
    for g in config:
        for h in g["hosts"]:
            all_hosts.append(h["name"])
    return all_hosts


def get_all_group_names(config):
    all_groups = []
    for g in config:
        all_groups.append(g["name"])
    return all_groups


def find_group_by_name(config, name, exit_on_fail=True):
    for group in config:
        if group["name"] == name:
            return group
    if not exit_on_fail:
        return False
    error(f"Requested group '{name}' not found in the SSH configuration")
    exit(1)


def find_host_by_name(config, name, exit_on_fail=True):
    found_host = None
    found_group = None
    
    for group in config:
        all_hosts = group["hosts"] + group["patterns"]
        for host in all_hosts:
            if host["name"] == name:
                found_host = host
                found_group = group
    
    if not found_host and exit_on_fail:
        error(f"Requested host '{name}' not found in the SSH configuration")
        exit(1)

    return found_host, found_group


def find_inherited_params(host_name, config):
    inherited = {}
    for group in config:
        for pattern in group["patterns"]:
            # Check if one of group pattern matches host
            if fnmatch.fnmatch(host_name, pattern["name"]):
                inherited[pattern["name"]] = filter_dict(pattern, ignored=["name"])

    # Currently not supporting multiple parameter inheritance, so warn and exit if it's found
    if len(inherited) > 1:
        error(f"Unsupported multiple parameter inheritance detected for host {host_name}!")
        exit(1)

    return inherited


def generate_graph(traced_hosts):
    """ Function that generates nice "graph" view of connected hosts"""

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
        "  Connection graph  ",
        "  ----------------  ",
        "         THIS HOST  ",
        "    SSH Connection -",
        "                    ",
    ], align="r")

    last_index = len(traced_hosts) - 1
    cp = int((max_cell_size - 6) / 2)  #cell_padding
    for i, elem in enumerate(reversed_hosts):
        if i != last_index:
            # Add Jump proxies
            trace.add_column(elem["name"], [
                crop_str(elem["name"]),                       # SSH Host     (could be long name)
                crop_str(elem.get("hostname", "")),                   # SSH HostName (usually IP, but can also be long fqdn)
                " " * cp + "|    |" + " " * cp,
                "-" * cp + "+    +" + "-" * cp,
                "",
            ])
        else:
            # Target (last) element
            trace.add_column("target", [
                "         ",
                "         ",
                "  TARGET",
                "> " + elem["name"],
                "  " + elem.get("hostname", ""),
            ], align="l")

    # Print local forward tunnel between current host and target host
    if "localforward" in traced_hosts[0]:
        # trace.add_row(["" for _ in range(num_elements)])   # Empty row
        trace.add_row(["Local SSH tunnels  "] + ["" for _ in range(num_elements - 1)])
        
        for tun in traced_hosts[0]["localforward"]:
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
    if "remoteforward" in traced_hosts[0]:
        # trace.add_row(["" for _ in range(num_elements)])   # Empty row
        trace.add_row(["Remote SSH tunnels:  "] + ["" for _ in range(num_elements - 1)])
        
        for tun in traced_hosts[0]["remoteforward"]:
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


def complete_ssh_host_names(ctx, param, incomplete):
    #// For some reason I cant get context object initialized by main app when running autocomplete
    #// so we get used sshconfig file, and parse it directly
    #// TODO: Try to see if we can force main to parse config, so we dont have to do this
    config = parse_ssh_config(ctx.parent.parent.params["sshconfig"])
    all_hosts = get_all_host_names(config)
    return [k for k in all_hosts if k.startswith(incomplete)]

def complete_ssh_group_names(ctx, param, incomplete):
    #// For some reason I cant get context object initialized by main app when running autocomplete
    #// so we get used sshconfig file, and parse it directly
    #// TODO: Try to see if we can force main to parse config, so we dont have to do this
    config = parse_ssh_config(ctx.parent.parent.params["sshconfig"])
    all_groups = get_all_group_names(config)
    return [k for k in all_groups if k.startswith(incomplete)]

