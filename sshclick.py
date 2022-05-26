# Builtin imports
import os
import re
import yaml
import fnmatch
import copy

# External imports
from prettytable import PrettyTable
import click
# import colorama

# -----------------------------------------------------------------------------
VERSION = "0.1.0"
DEBUG = False

DEFAULT_GROUP_NAME = "default"
BACKUP_CONFIG_FILE = True
BACKUP_COPIES = 10

# Setup defaults for local path ssh config
USER_CONF_FILE = "{}/{}".format(os.environ['HOME'], ".ssh/config")
TARGET_CONF_FILE = USER_CONF_FILE
STDOUT_CONF = False

# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]

# -----------------------------------------------------------------------------
class bcolors:
    #---------------------
    RESET   = '\033[0m'
    BRIGHT  = '\033[1m'
    DIM     = '\033[2m'
    NORMAL  = '\033[22m'
    #---------------------
    BLACK   = '\033[30m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'


def red(msg):
    return bcolors.RED + msg + bcolors.RESET
def green(msg):
    return bcolors.GREEN + msg + bcolors.RESET
def yellow(msg):
    return bcolors.YELLOW + msg + bcolors.RESET
def blue(msg):
    return bcolors.BLUE + msg + bcolors.RESET
def magenta(msg):
    return bcolors.MAGENTA + msg + bcolors.RESET
def cyan(msg):
    return bcolors.CYAN + msg + bcolors.RESET

def bred(msg):
    return bcolors.BRIGHT + bcolors.RED + msg + bcolors.RESET
def bgreen(msg):
    return bcolors.BRIGHT + bcolors.GREEN + msg + bcolors.RESET
def byellow(msg):
    return bcolors.BRIGHT + bcolors.YELLOW + msg + bcolors.RESET
def bblue(msg):
    return bcolors.BRIGHT + bcolors.BLUE + msg + bcolors.RESET
def bmagenta(msg):
    return bcolors.BRIGHT + bcolors.MAGENTA + msg + bcolors.RESET
def bcyan(msg):
    return bcolors.BRIGHT + bcolors.CYAN + msg + bcolors.RESET


def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def info(msg):
    print(f"[INFO] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")


# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d, ignored=[]):
    return {k: v for (k, v) in d.items() if k not in ignored}



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


def write_ssh_config(lines):
    """ Write generated SSH config to target file """
    if STDOUT_CONF:
        print("".join(lines))
    else:
        with open(TARGET_CONF_FILE, "w") as out:
            out.writelines(lines)
        

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


#-------------------[ CLI Functions below ]-------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Main CLI group
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--debug/--no-debug", "_debug_", default=DEBUG, help="Enables debug, what did you expect?")
@click.option("--sshconfig", default=USER_CONF_FILE, type=click.Path(exists=True), help="Config file, default is ~/.ssh/config")
@click.option("--outfile",   default=None, help="Location of output SSH Config file, default is same as input SSH file")
@click.option("--stdout",    default=STDOUT_CONF, is_flag=True, help="Original SSH config file will not be changed, instead modified SSH Config will be sent to STDOUT.")
@click.pass_context
def cli(ctx, _debug_, sshconfig, outfile, stdout):
    """
    SSH Config manager

    Basically glorified config file scraper & generator.
    It is for the people that do not want to manually handle veeeery 
    large SSH config files, and editing is just so darn pain in the ass!

    As this is early alpha, please backup your SSH config files before
    this software, as you might accidentally lose some configuration.
    """
    global DEBUG
    global STDOUT_CONF
    global TARGET_CONF_FILE

    DEBUG = _debug_
    STDOUT_CONF = stdout
    TARGET_CONF_FILE = outfile if outfile else sshconfig

    debug(f"! Debug mode is {'on' if _debug_ else 'off'}")

    # Parse ssh config and store it for rest of the commands
    config = parse_ssh_config(sshconfig)
    ctx.ensure_object(dict)
    ctx.obj["CONFIG"] = config
    

#------------------------------------------------------------------------------
# GROUP Commands
#------------------------------------------------------------------------------

# COMMAND: group-list
#-----------------------
@cli.command(help="Lists all groups")
@click.pass_context
def group_list(ctx):
    config = ctx.obj['CONFIG']

    x = PrettyTable(field_names=["Name", "Hosts", "Desc"])
    x.align = "l"
    x.align["Hosts"] = "r"

    for group in config:
        x.add_row([group["name"], len(group["hosts"]), group["desc"]])

    print(x)


# COMMAND: group-show
#-----------------------
@cli.command(help="Shows group details")
@click.argument("name")
@click.pass_context
def group_show(ctx, name):
    config = ctx.obj['CONFIG']

    x = PrettyTable(field_names=["Group Parameter", "Value"])
    x.align = "l"

    found = find_group_by_name(config, name)

    x.add_row(["name", found["name"]])
    x.add_row(["description", found["desc"]])
    x.add_row(["info", yaml.dump(found["info"])])

    hostlist = []
    for host in found["hosts"]:
        if "hostname" in host:
            hostlist.append(f"{host['name']} ({host['hostname']})")
        else:
            hostlist.append(f"{host['name']}")

    x.add_row(["hosts", "\n".join(hostlist) + "\n"])

    patternlist = []
    for host in found["patterns"]:
        # hack to search via case insensitive info
        if "hostname" in host:
            patternlist.append(f"{host['name']} ({host['hostname']})")
        else:
            patternlist.append(f"{host['name']}")

    x.add_row(["patterns", "\n".join(patternlist)])

    # Print table
    print(x)


# COMMAND: group-create
#-----------------------
@cli.command(help="Create new group")
@click.option("-d", "--desc", default=None, type=str, help="Short description of group")
@click.option("-i", "--info", default=[], multiple=True, type=str, help="Info line, can be set multiple times")
@click.argument("name")
@click.pass_context
def group_create(ctx, name, desc, info):
    config = ctx.obj['CONFIG']

    # Check if already group exists
    found = find_group_by_name(config, name, exit_on_fail=False)
    if found:
        error(f"Cannot create new group '{name}', as group already exists with this name")
        exit(1)

    new_group = {
        "name": name,
        "desc": desc,
        "info": info,
        "hosts": [],
        "patterns": [],
    }
    debug(f"Created new group: {new_group}")

    # Add new group to config and show newly created group
    config.append(new_group)
    ctx.invoke(group_show, name=name)
    
    lines = generate_ssh_config(config)
    write_ssh_config(lines)
    

# COMMAND: group-delete
#-----------------------
@cli.command(help="Delete group")
@click.argument("name")
@click.pass_context
def group_delete(ctx, name):
    config = ctx.obj['CONFIG']

    # Find group by name
    find_group_by_name(config, name)
    
    new_conf = [gr for gr in config if gr["name"] != name]

    lines = generate_ssh_config(new_conf)
    write_ssh_config(lines)


# COMMAND: group-set
#-----------------------
@cli.command(help="Change group parameters")
@click.option("-r", "--rename", default=None, help="Rename group")
@click.option("-d", "--desc", default=None, help="Set descrioption")
@click.option("-i", "--info", default=None, multiple=True, help="Set info, can be set multiple times")
@click.argument("name")
@click.pass_context
def group_set(ctx, name, rename, desc, info):
    config = ctx.obj['CONFIG']

    # Nothing was provided
    if not rename and not desc and not info:
        error("Calling set without setting anything is not valid. Run with '-h' for help.")
        exit(1)

    # Find group by name
    gr = find_group_by_name(config, name)

    if rename:
        gr["name"] = rename
    
    if desc:
        gr["desc"] = desc

    if info:
        if len(info[0]) > 0:
            gr["info"] = info
        else:
            gr["info"] = []

    lines = generate_ssh_config(config)
    write_ssh_config(lines)



#------------------------------------------------------------------------------
# HOSTS Commands
#------------------------------------------------------------------------------

# COMMAND: host-list
#-----------------------
@cli.command(help="List hosts")
@click.option("-g", "--group", "group_filter", default=None, help="Filter for group that host belongs to (regex)")
@click.option("-n", "--name", "name_filter", default=None, help="Filter for host name (regex)")
@click.option("-v", "--verbose", default=False, is_flag=True, help="Show verbose info (all parameters)")
@click.pass_context
def host_list(ctx, group_filter, name_filter, verbose):
    config = ctx.obj['CONFIG']

    filtered_config = []
    for group in config:
        # If group filter is defined, check if group name matches group filter
        if group_filter:
            grmatch = re.search(group_filter, group["name"])
            if not grmatch:
                continue
        
        # If there is no group filter or if group filter matches
        if name_filter:
            # Make a new copy of group, so we dont mess original config
            group_copy = copy.deepcopy(group)

            filtered_hosts = []
            filtered_patterns = []

            for host in group_copy["hosts"]:
                match = re.search(name_filter, host["name"])
                if match:
                    filtered_hosts.append(host)
            for pattern in group_copy["patterns"]:
                match = re.search(name_filter, pattern["name"])
                if match:
                    filtered_patterns.append(pattern)

            group_copy["hosts"] = filtered_hosts
            group_copy["patterns"] = filtered_patterns
            filtered_config.append(group_copy)
        else:
            filtered_config.append(group)

    if not filtered_config:
        print("No host matching any filter!")
        exit(1)

    # Find all possible params to display with inheritence
    params =[]
    for group in filtered_config:
        for host in group["hosts"]:
            for key in host:
                if (key != "name" and not key in params):
                    params.append(key)
        for patern in group["patterns"]:
            for key in patern:
                if (key != "name" and not key in params):
                    params.append(key)

    header = ["name", "group", "type"] + ([f"param:{p}" for p in params] if verbose else [])
    x = PrettyTable(field_names=header)
    x.align = "l"
    
    # Generate rows
    for group in filtered_config:
        # Adding line for host
        for host in group["hosts"]:
            if verbose:
                inherited = find_inherited_params(host["name"], config)
                host_params = []
                # Go trough list of all params we know are available across current host list
                # for current host we need to combine local and inherited params to fill table row
                for applied_param in params:
                    if applied_param in host:
                        # Handle direct params, and handle if its a list or string
                        if isinstance(host[applied_param], list):
                            host_params.append("\n".join(host[applied_param]))
                        else:
                            host_params.append(host[applied_param])
                    else:
                        # Handle inherited params
                        if inherited:
                            for pattern, key in inherited.items():
                                if applied_param in key:
                                    if isinstance(key[applied_param], list):
                                        host_params.append("\n".join(
                                            [yellow(f"{val}  ({pattern})") for val in key[applied_param]]
                                        ))
                                    else:
                                        host_params.append(yellow(f"{key[applied_param]}  ({pattern})"))
                                else:
                                    host_params.append("")
                        else:
                            host_params.append("")
            # Add to table
            x.add_row([host["name"], group["name"], "normal"] + (host_params if verbose else []))
        # Adding line for pattern
        for patt in group["patterns"]:
            if verbose:
                patt_params = []
                for p in params:
                    if p in patt:
                        # Handle direct params
                        if isinstance(patt[p], list):
                            patt_params.append("\n".join(
                                [cyan(val) for val in patt[p]]
                            ))
                        else:
                            patt_params.append(cyan(patt[p]))
                    else:
                        patt_params.append("")
            # Add to table with color to be easily distinguished
            x.add_row([cyan(patt["name"]), cyan(group["name"]), cyan("pattern")] + (patt_params if verbose else []))

    # Print table
    print(x)


# COMMAND: host-show
#-----------------------
@cli.command(help="Display info for host")
@click.option("--follow", is_flag=True, default=False, help="Follow and displays all connected jump-proxy hosts")
@click.option("--graph/--no-graph", default=True, help="Shows connection to target as graph (default:true)")
@click.argument("name")
@click.pass_context
def host_show(ctx, name, follow, graph):
    # global traced_hosts
    config = ctx.obj['CONFIG']

    traced_hosts = []
    traced_host_tables = []

    # Python does not have "do while" loop. (ಠ_ಠ)
    # we are first checking host that is asked, and then check if that host has a "proxy" defined
    # if proxy is defined, we add found host to traced list, and seach atached proxy, it his way we
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
        x.add_row(["type",  host_type,           ""])

        # Add rows for direct parameters
        for key, value in found_host.items():
            if key == "name":
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


# COMMAND: host-create
#-----------------------
@cli.command(help="Create new host configuration")
@click.option("-g", "--group", default=DEFAULT_GROUP_NAME, help="Sets group for the host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format")
@click.argument("name")
@click.pass_context
def host_create(ctx, name, group, parameter):
    # global traced_hosts
    config = ctx.obj['CONFIG']

    found_host, _ = find_host_by_name(config, name, exit_on_fail=False)
    if found_host:
        error(f"Cannot create host '{name}' as it already exists!")
        exit(1)
    
    # Find group by name where to store config
    found_group = find_group_by_name(config, group)

    new_host = {
        "name": name
    }

    # Add all passed parameters to config
    # TODO: here we need to implement validation for all "known" parameters that can be used, and possibly
    # some normalization to documented "CammelCase" format
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()
        if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            if not param in new_host:
                new_host[param] = [value]
            else:
                new_host[param].append(value)
        else:
            new_host[param] = value

    group_target = "patterns" if "*" in name else "hosts"
    found_group[group_target].append(new_host)

    ctx.invoke(host_show, name=name, graph=False)

    lines = generate_ssh_config(config)
    write_ssh_config(lines)


# COMMAND: host-delete
#-----------------------
@cli.command(help="Delete host from configuration")
@click.argument("name")
@click.pass_context
def host_delete(ctx, name):
    # global traced_hosts
    config = ctx.obj['CONFIG']

    found_host, found_group = find_host_by_name(config, name)
    print("Deleted host:")
    ctx.invoke(host_show, name=name, graph=False)
    
    if found_host in found_group["hosts"]:
        found_group["hosts"].remove(found_host)
    if found_host in found_group["patterns"]:
        found_group["patterns"].remove(found_host)

    lines = generate_ssh_config(config)
    write_ssh_config(lines)


# COMMAND: host-set
#-----------------------
@cli.command(help="Changes/sets configuration parameters")
@click.option("-g", "--group", "target_group_name", default=None, help="Changes group for host")
@click.option("-r", "--rename", default=None, help="Re-name host")
@click.option("-p", "--parameter", default=[], multiple=True, help="Sets parameter for the host, must be in 'param=value' format")
@click.option("--force", is_flag=True, default=False, help="Forces moving host to group that does not exist, by creating new group, and moving host to that group.")
@click.argument("name")
@click.pass_context
def host_set(ctx, name, target_group_name, rename, parameter, force):
    # global traced_hosts
    config = ctx.obj['CONFIG']

    # Nothing was provided
    if not target_group_name and not rename and not parameter:
        error("Calling set without setting anything is not valid. Run with '-h' for help.")
        exit(1)

    found_host, found_group = find_host_by_name(config, name)
    
    # Move host to different group
    if target_group_name:
        # Find target group
        target_group = find_group_by_name(config, target_group_name, exit_on_fail=False)
        if not target_group:
            if not force:
                error(f"Cannot move host '{name}' to group '{target_group_name}' which does not exist! Consider using --force to automatically create target group.")
                exit(1)
            else:
                # Create new group
                new_group = {
                    "name": target_group_name,
                    "desc": None,
                    "info": [],
                    "hosts": [],
                    "patterns": [],
                }
                # Add new group to config and set it as target group
                config.append(new_group)
                target_group = new_group

        # Add host to target group
        if "*" in name:
            target_group["patterns"].append(found_host)
        else:
            target_group["hosts"].append(found_host)

        # Remove from source group
        if found_host in found_group["hosts"]:
            found_group["hosts"].remove(found_host)
        if found_host in found_group["patterns"]:
            found_group["patterns"].remove(found_host)
        
    # Rename a host
    if rename:
        found_host["name"] = rename
    
    # Sets parameters for host (or erase them if value is provided as unset)
    for item in parameter:
        param, value = item.split("=")
        param = param.lower()            # lowercase keyword/param as they are case insensitive
        if value:
            if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                if not param in found_host:
                    found_host[param] = [value]
                else:
                    if value in found_host[param]:
                        error(f"Cannot add existing value '{value}' to host parameter '{param}' multiple times!")
                    else:
                        found_host[param].append(value)
            else:
                found_host[param] = value
        else:
            if param in found_host:
                found_host.pop(param)
            else:
                error(f"Cannot unset parameter that is not defined!")

    lines = generate_ssh_config(config)
    write_ssh_config(lines)


# COMMAND: host-add-tunnel
#-------------------------
# TODO


# COMMAND: host-del-tunnel
#-------------------------
# TODO


# COMMAND: history
#-------------------------
# TODO


# COMMAND: revert
#-------------------------
# TODO