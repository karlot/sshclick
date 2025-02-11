import os, re, fnmatch, time
from typing import Optional
from enum import Enum

from .ssh_host import SSH_Host, HostType
from .ssh_group import SSH_Group
from .ssh_parameters import PARAMS_WITH_ALLOWED_MULTIPLE_VALUES
from .ssh_diff import generate_diff

from sshclick.globals import *
# from rich import print


# I dont really need full logging import, just output some info if currently debugging
DEBUG = True if 'SSHC_DEBUG' in os.environ and os.environ['SSHC_DEBUG'] == "1" else False
def debug(msg):
    if DEBUG: print("D:", msg)


HOST_KEYWORD = "host"

class MetaTAG(str, Enum):
    CONFIG = "config"
    GNAME = "group"
    GDESC = "desc"
    GINFO = "info"
    HINFO = "host"
    HPASS = "pass"


class SSH_Config:
    """
    SSH Configuration class

    Main class for handling SSH configuration, reading from file, parsing and
    generating and writing contents back to SSH configuration file
    """
    def __init__(self, file: str, config_lines: list[str] = [], stdout: bool = False, diff: bool = False):
        self.ssh_config_file: str = file
        self.ssh_config_lines: list[str] = config_lines

        # configuration representation (array of SSH groups?)
        self.groups: list[SSH_Group] = [SSH_Group(name=DEFAULT_GROUP_NAME, desc=DEFAULT_GROUP_DESC)]
        self.all_hosts: list[SSH_Host] = []

        # options
        self.stdout: bool = stdout      # Redirect configuration change/write to stdout instead of input file
        self.diff: bool = diff          # Option to only show differences that would be applied to configuration
        self.opts: dict = {}

        # parsing "cache" info
        self.current_grindex: int = 0
        self.current_group: str = DEFAULT_GROUP_NAME
        self.current_host: Optional[SSH_Host] = None
        self.current_host_info: list = []
        self.current_host_pass: str = ""

        # Support for global keywords
        self.global_params: dict = {}


    def read(self):
        """
        Read content of SSH config file
        """
        config_path = self.ssh_config_file
        try:
            with open(config_path, "r") as fh:
                content = fh.read()
                self.ssh_config_lines = content.split("\n")
        except FileNotFoundError:
            print(f"SSH config file not found ({config_path})!")
            answer = input("Would you like to create it (y/n)? :")
            if answer.lower() in ["y", "yes"]:
                try:
                    # Make sure full path is available
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    # Write initial config file
                    with open(config_path, "w") as file:
                        file.write(SSHCONFIG_SIGNATURE_LINE)
                    # SSH config must be user read only
                    os.chmod(config_path, 0o600)
                    
                    # Assume we start with empty lines
                    self.ssh_config_lines = []
                except:
                    print(f"Failed to create ssh config file in ({config_path})!")
                    exit(1)
            else:
                print("Cannot proceed without config file!")
                exit(1)
        return self


    def _config_flush_host(self) -> None:
        """
        Internal function used to flush host configuration while parsing config file
        """
        if self.current_host:
            if self.current_host.type == HostType.NORMAL:
                self.groups[self.current_grindex].hosts.append(self.current_host)
            else:
                self.groups[self.current_grindex].patterns.append(self.current_host)

            self.all_hosts.append(self.current_host)
            # Reset "cache" since we flushed host info
            self.current_host = None


    def parse(self):
        """
        Parse config lines one by one and generate configuration structure
        """
        # Parse each line of the configuration, line by line
        for config_line_index, line in enumerate(self.ssh_config_lines):
            line = line.strip()     # remove start and end whitespace

            # Skip empty lines, go to next...
            if not line:
                continue
            
            # Reworked parsing method... special "meta" keys not needed, regex now parses words
            # so its much more "freely" in reading from config file writing is still in legacy style
            # in future, output config write styles could be changed... 
            if line.startswith("#"):
                match = re.search(r"^#[ @]{1}(\w+):\s+(.+)$", line)

                # If we didn't find metadata, 
                if not match: continue
                
                # extract two items expected in matching group
                metadata, value = match.groups()

                if metadata == MetaTAG.CONFIG:
                    # Config options are configured as key=value within config line...
                    debug(f"META config: '{value}'")
                    conf_key, conf_val = value.split("=")
                    self.opts[conf_key] = conf_val
                    continue

                elif metadata == MetaTAG.GNAME:
                    # New group found... flush any previous data and create new baseline
                    self._config_flush_host()

                    debug(f"META group: {value}")
                    self.groups.append(SSH_Group(name=value))

                    self.current_grindex = len(self.groups) - 1
                    self.current_group = value
                    debug(f"META Group index: {self.current_grindex}")
                    continue

                elif metadata == MetaTAG.GDESC:
                    debug(f"META Group description: {value}")
                    self.groups[self.current_grindex].desc = value
                    continue

                elif metadata == MetaTAG.GINFO:
                    debug(f"META Group info: {value}")
                    self.groups[self.current_grindex].info.append(value)
                    continue

                elif metadata == MetaTAG.HINFO:
                    debug(f"META Host info cached: {value}")
                    self.current_host_info.append(value)
                    continue

                else:
                    print(f"Unhandled metadata: '{metadata}' on SSH-config line number: {config_line_index + 1}")
                    continue

            # This NEW regex should fix this spec from ssh_config definition:
            # "Configuration options may be separated by whitespace or optional whitespace and exactly one ‘=’ ""
            # although I have tested clients like ssh or sftp, they dont complain, and allow multiple "=" symbols. :D
            match = re.search(r"^(\w+)\s*(?:=\s*|\s+)([^=]+)$", line)
            if not match:
                print(f"KEYWORD: Ignoring incorrect configuration line '{line}' on SSH-config line number {config_line_index + 1}")
                continue

            keyword, value = match.groups()
            keyword = keyword.lower()         # keywords are case insensitive, so we lowercase them

            # --- Found "host" keyword, that defines new block, usually followed with name
            if keyword == HOST_KEYWORD:
                self._config_flush_host()

                host_type = HostType.PATTERN if "*" in value else HostType.NORMAL
                
                # We need to check if multiple host keyword patterns are present, and store them separately from "main" name
                if " " in value or "\t" in value:
                    name, *names = value.split()
                else:
                    name = value
                    names=[]

                new_host = SSH_Host(
                    name=name,
                    alt_names=names,
                    password=self.current_host_pass,
                    group=self.current_group,
                    type=host_type,
                    info=self.current_host_info,
                )

                debug(f"SSH Host definition created: {new_host}")
                self.current_host = new_host

                # Reset global host info cache when we find new host (from this line, any host comments will apply to next host)
                self.current_host_info = []
                self.current_host_pass = ""
            else:
                # any other normal line we just use as it is, wrong or not... :)
                # Currently there is no support for keyword validation
                if not self.current_host:
                    # Added support for top/global level keywords, this will be filled only from start of the file
                    debug(f"SSH Config global keyword defined: {keyword} -> {value}")
                    if keyword in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                        if not keyword in self.global_params:
                            self.global_params[keyword] = [value]
                        else:
                            self.global_params[keyword].append(value)
                    else:
                        self.global_params[keyword] = value
                else:
                    debug(f"SSH Config keyword for host '{self.current_host.name}': {keyword} -> {value}")
                    if keyword in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                        if not keyword in self.current_host.params:
                            self.current_host.params[keyword] = [value]
                        else:
                            self.current_host.params[keyword].append(value)
                    else:
                        self.current_host.params[keyword] = value
        
        # Last entries must be flushed manually as there are no new "hosts" to trigger storing parsed data into config struct
        self._config_flush_host()

        # Second stage, check any inheritances and fill it in
        self._check_inheritance()

        return self


    def _check_inheritance(self):
        """
        Function that checks inheritance for each host in configuration
        """
        if DEBUG:
            start = time.time()

        for host in self.all_hosts:
            # We only check what "normal" hosts inherits
            if host.type == HostType.PATTERN: continue

            # Add global parameters to host, if they are not already defined
            # They normally override any other parameters, but only if they are not defined already as used
            for param, value in self.global_params.items():
                if param not in host.matched_params:
                    host.matched_params[param] = (value, "global")

            # NOTE: This has added almost O^2 complexity with the number of hosts
            #       We need to find a way to optimize this, if it becomes a problem
            before = True
            for other_host in self.all_hosts:
                # Skip current host, and mark that we have passed it
                if other_host == host:
                    before = False
                    continue
                
                # We test only pattern hosts, and if they match the name of current host
                if other_host.type == HostType.PATTERN and fnmatch.fnmatch(host.name, other_host.name):
                    for param, value in other_host.params.items():
                        if before:
                            # If parameter is seen before in used params, first instance is then already
                            # seen, and we dont care about this value anymore
                            if param not in host.matched_params:
                                host.matched_params[param] = (value, other_host.name)
                        else:
                            # If matching host is after current host, store parameter only if it is not
                            # already defined in current host parameters or used parameters that are inherited
                            if param in host.params: continue
                            if param in host.matched_params: continue
                            # if param not in host.params or param not in host.matched_params:
                            host.matched_params[param] = (value, other_host.name)
        if DEBUG:
            end = time.time() - start
            print(f"Inheritance check elapsed: {end:0.6f}s")
            # inspect(self, all=True)


    def generate_ssh_config(self):
        """
        SSH config generation function

        Function takes config data structure, and target file information.
        Then generates SSH config compatible file with all data, compatible with
        internal object model.
        """

        # Prepare all lines for configuration
        lines: list[str] = [SSHCONFIG_SIGNATURE_LINE]

        # Dump any saved configuration
        for option in self.opts:
            lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.CONFIG.value}{SSHCONFIG_META_SEPARATOR} {option}={self.opts[option]}")

        # Add separation from header/config and rest of ssh-config
        lines.append("")

        if self.global_params:
            lines.append(SSHCONFIG_GLOBAL_KEYWORDS_LINE)
            for token, value in self.global_params.items():
                lines.append(f"{token} {value}")
                lines.append("")

        # Render all groups
        for group in self.groups:
            # Ship default group as it does not have to be specified
            render_header = False if group.name == DEFAULT_GROUP_NAME else True
            
            if render_header:
                # Add extra blank line when outputting new group header
                lines.append("")
                comment_hline = f"#{'-' * 79}"

                # Start header line for the group with known metadata
                lines.append(comment_hline)
                lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GNAME.value}{SSHCONFIG_META_SEPARATOR} {group.name}")

                if group.desc:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GDESC.value}{SSHCONFIG_META_SEPARATOR} {group.desc}")

                for info in group.info:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GINFO.value}{SSHCONFIG_META_SEPARATOR} {info}")

                lines.append(comment_hline)

            # Append hosts and patterns items from group
            for host in group.hosts + group.patterns:
                # If there is host-info assigned to host, add it before adding "host" definition
                for host_info in host.info:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.HINFO.value}{SSHCONFIG_META_SEPARATOR} {host_info}")

                # Add "host" line definition
                alt_names = " " + " ".join(host.alt_names) if host.alt_names else ""
                lines.append(f"{HOST_KEYWORD.capitalize()} {host.name}{alt_names}")

                # Add all assigned host params
                for token, value in host.params.items():
                    SSHCONFIG_INDENT_STR = ' ' * SSHCONFIG_INDENT
                    if type(value) is str:
                        lines.append(f"{SSHCONFIG_INDENT_STR}{token} {value}")
                    elif type(value) is list:
                        for v in value:
                            lines.append(f"{SSHCONFIG_INDENT_STR}{token} {v}")
                    else:
                        raise Exception("Host parameter is not 'str' or 'list'!!!")
                
                # Add newline after host definition
                lines.append("")

        # If we are running in diff mode, only show the changes, and return without storing new configuration!
        if self.diff:
            generate_diff(self.ssh_config_lines, lines)
            return

        # Store new config lines as actual
        self.ssh_config_lines = lines
        return self


    def write_out(self) -> None:
        """
        Write generated SSH config to target file
        """
        # When we are running in "diff" mode, dont write out anything!
        if self.diff: return

        # Prepare multiline content string for output configuration
        config_content = "\n".join(self.ssh_config_lines)

        if self.stdout:
            # When output is changed to write config to STDOUT, just print all lines
            print(config_content)
        else:
            # Write content to target config file
            # TODO: This is prone to errors, and we should check it target file is writable, and catch exceptions!
            with open(self.ssh_config_file, "w") as out:
                out.write(config_content)


    def check_group_by_name(self, name: str) -> bool:
        """
        Check if specific group name is present in configuration
        """
        return any(group.name == name for group in self.groups)


    def get_group_by_name(self, name: str) -> SSH_Group:
        """
        Find group in configuration that matches the name (strict match, one only!)
        On success returns matched group, on fail depending on 'throw_on_fail' flag
        function will either return 'None' or will throw exception
        """
        for group in self.groups:
            if group.name == name: return group
        raise Exception(f"Requested group '{name}' not found in the SSH configuration")


    def check_host_by_name(self, name: str) -> bool:
        """
        Check if specific host name is present in configuration
        """
        return any(host.name == name for host in self.all_hosts)


    def get_host_by_name(self, name: str) -> SSH_Host:
        """
        Find host in configuration that matches the name (strict match, one only!)
        On success returns host and his assigned group, on fail depending on 'throw_on_fail' flag
        function will either return ('None','None') or will throw exception
        """
        for host in self.all_hosts:
            if host.name == name: return host
        raise Exception(f"Requested host '{name}' not found in the SSH configuration")


    def get_all_host_names(self) -> list[str]:
        """
        Return all host names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        return [host.name for host in self.all_hosts]


    def get_all_group_names(self) -> list[str]:
        """
        Return all group names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        return [group.name for group in self.groups]


    def filter_hosts(self, group_filter: str, name_filter: str) -> list[SSH_Host]:
        """
        Function takes optional group and name regex, and if they are not None or empty,
        function creates a new filtered list of SSH hosts
        """
        filtered_hosts = []

        for host in self.all_hosts:
            # If group filter is defined, check if current host matches the group name to progress
            if group_filter and not re.search(group_filter, host.group): continue
            
            # When host is not skipped, check if name filter is used, and filter out hosts
            if name_filter and not re.search(name_filter, host.name): continue

            # If host is not skipped, add it to filtered list
            filtered_hosts.append(host)

        return filtered_hosts


    def add_host(self, host: SSH_Host):
        """
        Function that will add host to a configuration based on its group definition
        """
        if not host.group:
            raise Exception("Internal ERROR, host group missing, or empty, please report issue!")
        
        try:
            found_group = self.get_group_by_name(host.group)
        except:
            # When group does not exist, we return false
            return False

        # Add host to configuration
        if host.type == HostType.NORMAL:
            found_group.hosts.append(host)
        else:
            found_group.patterns.append(host)
        self.all_hosts.append(host)
        return True


    def move_host_to_group(self, host: SSH_Host, source_group: SSH_Group, target_group: SSH_Group) -> None:
        """
        Function that moves host from one group to other group
        """
        # Change group name inside host
        host.group = target_group.name

        # Move hosts within groups based on type
        if host.type == HostType.NORMAL:
            target_group.hosts.append(host)
            source_group.hosts.remove(host)
        else:
            target_group.patterns.append(host)
            source_group.patterns.remove(host)


    def trace_proxyjump(self, name: str) -> list[SSH_Host] | None:
        """
        Function to trace connected hosts via "proxyjump" SSH parameter
        For target host, return a list of hosts in order of connections to reach the target host
        In case host is directly reachable (no "proxyjump" param), it will return list of single (target) host
        """
        # Keep list of linked hosts via proxyjump option
        traced_hosts = []

        # we are first checking host that is asked, and then check if that host has a "proxy" defined
        # if proxy is defined, we add found host to traced list, and search attached proxy, it this way we
        # can trace full connection path for later graph processing
        while True:
            # Search for host in current configuration
            if (not self.check_host_by_name(name)):
                print(f"Cannot get info for used host '{name}' as next proxyjump, as it is not defined in configuration!")
                return None

            found_host = self.get_host_by_name(name)

            # Add current host, and its table to traced lists
            traced_hosts.append(found_host)

            # Find proxy info if it exists, if not, break the loop
            proxy_val, _ = found_host.get_applied_param("proxyjump")

            if not proxy_val: break
            name = proxy_val

        return traced_hosts
