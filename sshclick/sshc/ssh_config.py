import os
import re, fnmatch, copy
from typing import List, Optional, Tuple
from enum import Enum

import logging
logging.basicConfig(level=logging.INFO)

from .ssh_host import SSH_Host, HostType
from .ssh_group import SSH_Group
from .ssh_parameters import PARAMS_WITH_ALLOWED_MULTIPLE_VALUES

from sshclick.globals import *
HOST_KEYWORD = "host"

DEFAULT_GROUP_NAME = "default"
DEFAULT_GROUP_DESC = "Default group"

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
    DEF_GROUP_NAME: str = DEFAULT_GROUP_NAME

    def __init__(self, file: str, config_lines: List[str] = [], stdout: bool = False):
        self.ssh_config_file: str = file
        self.ssh_config_lines: List[str] = config_lines

        # configuration representation (array of SSH groups?)
        self.groups: List[SSH_Group] = [SSH_Group(name=self.DEF_GROUP_NAME, desc=DEFAULT_GROUP_DESC)]

        # options
        self.stdout: bool = stdout
        self.opts: dict = {}

        # parsing "cache" info
        self.current_grindex: int = 0
        self.current_group: str = self.DEF_GROUP_NAME
        self.current_host: Optional[SSH_Host] = None
        self.current_host_info: list = []
        self.current_host_pass: str = ""


    def read(self):
        """
        Read content of SSH config file
        """
        config_path = self.ssh_config_file
        try:
            with open(config_path, "r") as fh:
                self.ssh_config_lines = fh.readlines()
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
                match = re.search(r"^#[\s@]*(\w+)[\s:]+(.+)$", line)

                # In case special comment is unreadable
                if not match:
                    logging.debug(f"DROPING COMMENT: '{line}'")
                    continue
                
                # extract two items expected in matching group
                metadata, value = match.groups()

                if metadata == MetaTAG.CONFIG:
                    # Config options are configured as key=value within config line...
                    logging.debug(f"META: Config line found '{value}'")
                    conf_key, conf_val = value.split("=")
                    self.opts[conf_key] = conf_val
                    continue

                elif metadata == MetaTAG.GNAME:
                    # New group found... flush any previous data and create new baseline
                    self._config_flush_host()

                    logging.debug(f"META: Starting new group: {value}")
                    self.groups.append(SSH_Group(name=value))

                    self.current_grindex = len(self.groups) - 1
                    self.current_group = value
                    logging.debug(f"META: Group index set to: {self.current_grindex}")
                    continue

                elif metadata == MetaTAG.GDESC:
                    logging.debug(f"META: Setting group description to '{value}' for group '{self.groups[self.current_grindex].name}'")
                    self.groups[self.current_grindex].desc = value
                    continue

                elif metadata == MetaTAG.GINFO:
                    logging.debug(f"META: Adding group info '{value}' for group '{self.groups[self.current_grindex].name}'")
                    self.groups[self.current_grindex].info.append(value)
                    continue

                elif metadata == MetaTAG.HINFO:
                    logging.debug(f"META: Host info found '{value}' Caching for next host definition...'")
                    self.current_host_info.append(value)
                    continue

                else:
                    logging.warning(f"META: Unhandled metadata '{metadata}' on SSH-config line number: {config_line_index + 1}")
                    continue

            # Here we expect only normal ssh config lines "Host" is usually the keyword that begins definition
            # if we find any other keyword before first host keyword is defined, configuration is wrong probably
            # This NEW regex should fix this spec from ssh_config definition:
            #     "Configuration options may be separated by whitespace or optional whitespace and exactly one ‘=’ ""
            # ... although I have tested clients like ssh or sftp, and they dont complain, and allow multiple "=" symbols. :D
            match = re.search(r"^(\w+)\s*(?:=\s*|\s+)([^=]+)$", line)
            if not match:
                logging.warning(f"KEYWORD: Incorrect configuration line '{line}' on SSH-config line number {config_line_index + 1}")
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
                self.current_host = SSH_Host(name=name, alt_names=names, password=self.current_host_pass, group=self.current_group, type=host_type, info=self.current_host_info)

                # Reset global host info cache when we find new host (from this line, any host comments will apply to next host)
                self.current_host_info = []
                self.current_host_pass = ""
                continue
            else:
                # any other normal line we just use as it is, wrong or not... :)
                # Currently there is no support for keyword validation
                if not self.current_host:
                    logging.warning(f"Config info without Host definition on SSH-config line number {config_line_index + 1}")
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

        # Second stage, check any inheritances and fill them
        # start = time.time()
        for group in self.groups:
            for host in group.hosts:
                inherited_params: List[Tuple[str, dict]] = []
                if host.type == HostType.NORMAL:
                    inherited_params = self.find_inherited_params(host.name)
                    host.inherited_params = inherited_params
        # end = time.time() - start
        # print(f"Inheritance check elapsed: {end:0.3f}s")
        return self


    def generate_ssh_config(self):
        """
        SSH config generation function

        Function takes config data structure, and target file information.
        Then generates SSH config compatible file with all data, compatible with
        internal object model.
        """

        # First we lines before we flush them into file
        lines: List[str] = [SSHCONFIG_SIGNATURE_LINE]

        # Dump any saved configuration
        for option in self.opts:
            lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.CONFIG.value}{SSHCONFIG_META_SEPARATOR} {option}={self.opts[option]}\n")

        # Add separation from header/config and rest of ssh-config
        lines.append("\n")

        # Render all groups
        for group in self.groups:
            # Ship default group as it does not have to be specified
            render_header = False if group.name == self.DEF_GROUP_NAME else True
            
            if render_header:
                # Add extra blank line when outputting new group header
                lines.append("\n")
                comment_hline = f"#{'-' * 79}\n"

                # Start header line for the group with known metadata
                lines.append(comment_hline)
                lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GNAME.value}{SSHCONFIG_META_SEPARATOR} {group.name}\n")

                if group.desc:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GDESC.value}{SSHCONFIG_META_SEPARATOR} {group.desc}\n")

                for info in group.info:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.GINFO.value}{SSHCONFIG_META_SEPARATOR} {info}\n")

                lines.append(comment_hline)

            # Append hosts and patterns items from group
            for host in group.hosts + group.patterns:
                # If there is host-info assigned to host, add it before adding "host" definition
                for host_info in host.info:
                    lines.append(f"#{SSHCONFIG_META_PREFIX}{MetaTAG.HINFO.value}{SSHCONFIG_META_SEPARATOR} {host_info}\n")

                # Add "host" line definition
                alt_names = " " + " ".join(host.alt_names) if host.alt_names else ""
                lines.append(f"{HOST_KEYWORD.capitalize()} {host.name}{alt_names}\n")

                # Add all assigned host params
                for token, value in host.params.items():
                    SSHCONFIG_INDENT_STR = ' ' * SSHCONFIG_INDENT
                    if type(value) is str:
                        lines.append(f"{SSHCONFIG_INDENT_STR}{token} {value}\n")
                    elif type(value) is list:
                        for v in value:
                            lines.append(f"{SSHCONFIG_INDENT_STR}{token} {v}\n")
                    else:
                        raise Exception("Host parameter is not 'str' or 'list'!!!")
                
                # Add newline after host definition
                lines.append("\n")
            
        # Store output lines
        self.ssh_config_lines = lines
        return self


    def write_out(self) -> None:
        """
        Write generated SSH config to target file
        """
        if self.stdout:
            print("".join(self.ssh_config_lines))
        else:
            with open(self.ssh_config_file, "w") as out:
                out.writelines(self.ssh_config_lines)


    def check_group_by_name(self, name: str) -> bool:
        """
        Check if specific group name is present in configuration
        """
        for group in self.groups:
            if group.name == name:
                return True
        return False


    def get_group_by_name(self, name: str) -> SSH_Group:
        """
        Find group in configuration that matches the name (strict match, one only!)
        On success returns matched group, on fail depending on 'throw_on_fail' flag
        function will either return 'None' or will throw exception
        """
        for group in self.groups:
            if group.name == name:
                return group
        raise Exception(f"Requested group '{name}' not found in the SSH configuration")


    def check_host_by_name(self, name: str) -> bool:
        """
        Check if specific host name is present in configuration
        """
        for group in self.groups:
            all_hosts = group.hosts + group.patterns
            for host in all_hosts:
                if host.name == name:
                    return True
        return False


    def get_host_by_name(self, name: str) -> Tuple[SSH_Host, SSH_Group]:
        """
        Find host in configuration that matches the name (strict match, one only!)
        On success returns host and his assigned group, on fail depending on 'throw_on_fail' flag
        function will either return ('None','None') or will throw exception
        """
        for group in self.groups:
            all_hosts = group.hosts + group.patterns
            for host in all_hosts:
                if host.name == name:
                    return host, group
        raise Exception(f"Requested host '{name}' not found in the SSH configuration")


    def get_all_host_names(self) -> List[str]:
        """
        Return all host names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        all_hosts: List[str] = []
        for group in self.groups:
            for host in group.hosts + group.patterns:
                all_hosts.append(host.name)
        return all_hosts


    def get_all_group_names(self) -> List[str]:
        """
        Return all group names from current configuration
        Useful for auto-completion, or for quick checking if name already exists
        """
        all_groups: List[str] = []
        for group in self.groups:
            all_groups.append(group.name)
        return all_groups


    def find_inherited_params(self, host_name: str) -> List[Tuple[str,dict]]:
        """
        Given a host name, finds and returns list of 2-item tuples, where first item is name of pattern from
        which params are inherited, and second item is parameters dictionary from the pattern
        """
        inherited: List[Tuple[str,dict]] = []
        for group in self.groups:
            for pattern in group.patterns:
                # Check if any one of pattern (from all groups) will match host name
                if fnmatch.fnmatch(host_name, pattern.name):
                    inherited.append((pattern.name, pattern.params))
        
        return inherited


    def filter_config(self, group_filter: str, name_filter: str) -> List[SSH_Group]:
        """
        Function takes optional group and name regex, and if they are not None or empty,
        function creates a new list of SSH groups and their SSH hosts, but with all
        non-matching items removed.
        """
        filtered_groups: List[SSH_Group] = []
        for group in self.groups:
            # If group filter is defined, check if current group matches the name to progress
            if group_filter:
                group_match = re.search(group_filter, group.name)
                if not group_match:
                    continue
            
            # When group is not skipped, check if name filter is used, and filter out groups
            if name_filter:
                # Make a new copy of group, so we dont mess original config
                group_copy = copy.copy(group)
                group_copy.hosts = []
                group_copy.patterns = []
                include_group = False

                for host in group.hosts + group.patterns:
                    match = re.search(name_filter, host.name)
                    if match:
                        include_group = True
                        if host.type == HostType.NORMAL:
                            group_copy.hosts.append(host)
                        else:
                            group_copy.patterns.append(host)
                if include_group:
                    filtered_groups.append(group_copy)
            else:
                filtered_groups.append(group)
        return filtered_groups


    def move_host_to_group(self, found_host: SSH_Host, found_group: SSH_Group, target_group: SSH_Group) -> None:
        """
        Function that moves host from one group to other group
        """
        if found_host.type == HostType.NORMAL:
            target_group.hosts.append(found_host)
            found_group.hosts.remove(found_host)
        else:
            target_group.patterns.append(found_host)
            found_group.patterns.remove(found_host)
