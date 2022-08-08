import re
import fnmatch

from ..globals import *
from .ssh_host import SSH_Host
from .ssh_group import SSH_Group

import logging
logging.basicConfig(level=logging.INFO)

class SSH_Config:
    """
    SSH Configuration class

    Main class for handling SSH configuration, reading from file, parsing and
    generating and writing contents back to SSH configuration file
    """

    def __init__(self, file: str, config_lines: list = [], stdout: bool = DEFAULT_STDOUT):
        self.ssh_config_file: str = file
        self.ssh_config_lines: list = config_lines

        # configuration representation (array of SSH groups?)
        self.groups: list = [SSH_Group(name=DEFAULT_GROUP_NAME, desc="Default group")]

        # options
        self.stdout: bool = stdout

        # parsing "cache" info
        self.current_grindex: int = 0
        self.current_group: str = DEFAULT_GROUP_NAME
        self.current_host: SSH_Host = None
        self.current_host_info: list = []


    def read(self):
        """
        Read content of SSH config file
        """
        with open(self.ssh_config_file) as fh:
            self.ssh_config_lines = fh.readlines()
        return self


    def _config_flush_host(self) -> None:
        """
        Internal function used to flush host configuration while parsing config file
        """
        if self.current_host:
            if self.current_host.type == "normal":
                self.groups[self.current_grindex].hosts.append(self.current_host)
            else:
                self.groups[self.current_grindex].patterns.append(self.current_host)
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
            
            # Process special metadata for grouping: "#@group", "#@desc", "#@info"
            if line.startswith("#@"):
                match = re.search(r"^#@(\w+):\s*(.+)$", line)

                # In case special comment is unreadable
                if not match:
                    logging.warning(f"META: Unmatched metadata line {line} on SSH-config line number {config_line_index}")
                    continue
                
                metadata, value = match.groups()
                if metadata == "group":
                    # New group found... flush any previous data and create new baseline
                    self._config_flush_host()

                    logging.debug(f"META: Starting new group: {value}")
                    self.groups.append(SSH_Group(name=value))

                    self.current_grindex = len(self.groups) - 1
                    self.current_group = value
                    logging.debug(f"META: Group index set to: {self.current_grindex}")
                    continue

                elif metadata == "desc":
                    logging.debug(f"META: Setting 'desc' param to '{value}' for group '{self.groups[self.current_grindex].name}'")
                    self.groups[self.current_grindex].desc = value
                    continue

                elif metadata == "info":
                    logging.debug(f"META: Setting 'info' param to '{value}' for group '{self.groups[self.current_grindex].name}'")
                    self.groups[self.current_grindex].info.append(value)
                    continue

                elif metadata == "host":
                    logging.debug(f"META: Host comment found '{value}' Caching for next host definition...'")
                    self.current_host_info.append(value)
                    continue

                else:
                    logging.warning(f"META: Unhandled metadata metadata '{metadata}' on SSH-config line number {config_line_index}")
                    continue

            # Ignore rest of commented lines
            if line.startswith("#"):
                logging.debug(f"DROP COMMENT: '{line}'")
                continue

            # Here we expect only normal ssh config lines "Host" is usually the keyword that begins definition
            # if we find any other keyword before first host keyword is defined, configuration is wrong probably
            match = re.search(r"^(\w+)\s+(.+)$", line)
            if not match:
                logging.warning(f"KEYWORD: Incorrect configuration line '{line}' on SSH-config line number {config_line_index}")
                continue

            keyword, value = match.groups()
            keyword = keyword.lower()         # keywords are case insensitive, so we lowercase them

            # --- Found "host" keyword, that defines new block, usually followed with name
            if keyword == "host":
                self._config_flush_host()

                host_type = "pattern" if "*" in value else "normal"
                logging.debug(f"Host '{value}' is '{host_type}' type!")

                self.current_host = SSH_Host(name=value, group=self.current_group, type=host_type, info=self.current_host_info)

                # Reset global host info cache when we find new host (from this line, any host comments will apply to next host)
                self.current_host_info = []
                continue
            else:
                # any other normal line we just use as it is, wrong or not... :)
                # Currently there is no support for keyword validation
                if not self.current_host:
                    logging.warning(f"Config info without Host definition on SSH-config line number {config_line_index}")
                    exit(1)
                else:
                    logging.debug(f"Config keyword for host '{self.current_host}': {keyword} -> {value}")
                    # Save any specific info...
                    if keyword in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                        if not keyword in self.current_host.params:
                            self.current_host.params[keyword] = [value]
                        else:
                            self.current_host.params[keyword].append(value)
                    else:
                        self.current_host.params[keyword] = value
                        continue
        
        # Last entries must be flushed manually as there are no new "hosts" to trigger storing parsed data into config struct
        self._config_flush_host()
        return self


    def generate_ssh_config(self):
        """
        SSH config generation function

        Function takes config data structure, and target file information.
        Then generates SSH config compatible file with all data, compatible with
        internal object model.
        """
        SSHCONFIG_INDENT = "    "

        # First we lines before we flush them into file
        lines = ["#<<<<< SSH Config file managed by sshclick >>>>>\n"]

        for group in self.groups:
            # Ship default group as it does not have to be specified
            render_header = False if group.name == DEFAULT_GROUP_NAME else True
            
            if render_header:
                # Add extra blank line when outputting new group header
                lines.append("\n")
                # Start header line for the group with known metadata
                lines.append(f"#{'-'*79}\n")        # add horizontal decoration line
                lines.append(f"#@group: {group.name}\n")
                if group.desc:
                    lines.append(f"#@desc: {group.desc}\n")
                for info in group.info:
                    lines.append(f"#@info: {info}\n")
                lines.append(f"#{'-'*79}\n")        # add horizontal decoration line

            # Append hosts and patterns items from group
            for host in group.hosts + group.patterns:
                # If there is host-info assigned to host, add it before adding "host" definition
                for host_info in host.info:
                    lines.append(f"#@host: {host_info}\n")
                
                # Add "host" line definition
                lines.append(f"Host {host.name}\n")

                # Add all assigned host params
                for token, value in host.params.items():
                    if type(value) is str:
                        lines.append(f"{SSHCONFIG_INDENT}{token} {value}\n")
                    elif type(value) is list:
                        for v in value:
                            lines.append(f"{SSHCONFIG_INDENT}{token} {v}\n")
                    else:
                        raise Exception("Host parameter is not 'str' or 'list'!!!")
                
                # Add newline after host definition
                lines.append("\n")
            
        # Store output lines
        self.ssh_config_lines = lines
        return self
        

    def write_out(self):
        """
        Write generated SSH config to target file
        """
        if self.stdout:
            print("".join(self.ssh_config_lines))
        else:
            with open(self.ssh_config_file, "w") as out:
                out.writelines(self.ssh_config_lines)
        

    def find_group_by_name(self, name: str, throw_on_fail: bool = True):
        """
        Find group in configuration that matches the name (strict match, one only!)
        On success returns matched group, on fail depending on 'throw_on_fail' flag
        function will either return 'None' or will throw exception
        """
        for group in self.groups:
            if group.name == name:
                return group
        if not throw_on_fail:
            return None
        raise Exception(f"Requested group '{name}' not found in the SSH configuration")


    def find_host_by_name(self, name: str, throw_on_fail: bool = True):
        """
        Find host in configuration that matches the name (strict match, one only!)
        On success returns host and his assigned group, on fail depending on 'throw_on_fail' flag
        function will either return ('None','None') or will throw exception
        """
        found_host = None
        found_group = None
        
        for group in self.groups:
            all_hosts = group.hosts + group.patterns
            for host in all_hosts:
                if host.name == name:
                    found_host = host
                    found_group = group
        
        if not found_host and throw_on_fail:
            raise Exception(f"Requested host '{name}' not found in the SSH configuration")

        return found_host, found_group


    def get_all_host_names(self) -> list:
        """
        Return all host names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        all_hosts: list = []
        for group in self.groups:
            for host in group.hosts:
                all_hosts.append(host.name)
        return all_hosts


    def get_all_group_names(self) -> list:
        """
        Return all group names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        all_groups: list = []
        for group in self.groups:
            all_groups.append(group.name)
        return all_groups


    def find_inherited_params(self, host_name: str) -> list:
        """
        Returns array of 2-item tuples, where first item is name of pattern from
        which params are inherited, and second item is parameters dictionary from the pattern
        """
        inherited: list = []
        for group in self.groups:
            for pattern in group.patterns:
                # Check if any one of pattern (from all groups) will match host name
                if fnmatch.fnmatch(host_name, pattern.name):
                    inherited.append((pattern.name, pattern.params))

        return inherited

