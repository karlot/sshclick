import os
import re
import fnmatch
import time
import glob
import shlex
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .ssh_host import SSH_Host, HostType
from .ssh_group import SSH_Group
from .ssh_diff import output_diff
from .ssh_parameters import PARAMS_WITH_ALLOWED_MULTIPLE_VALUES

from sshclick.globals import (
    DEFAULT_GROUP_DESC,
    DEFAULT_GROUP_NAME,
    SSHCONFIG_GLOBAL_KEYWORDS_LINE,
    SSHCONFIG_INDENT,
    SSHCONFIG_META_PREFIX,
    SSHCONFIG_META_SEPARATOR,
    SSHCONFIG_SIGNATURE_LINE,
)
from sshclick.logging import DEBUG, debug, error, warn


class MetaTAG(str, Enum):
    """Supported SSHClick metadata tags embedded in SSH config comments."""

    CONFIG = "config"
    GNAME = "group"
    GDESC = "desc"
    GINFO = "info"
    HINFO = "host"
    HPASS = "pass"


@dataclass(frozen=True)
class ConfigLine:
    """A single config line annotated with its source file and line number."""

    text: str
    source_file: Optional[str]
    source_line: int


class SSH_Config:
    """
    SSH Configuration class

    Main class for handling SSH configuration, reading from file, parsing and
    generating and writing contents back to SSH configuration file
    """
    def __init__(self, file: Optional[str], config_lines: Optional[list[str]] = None, stdout: bool = False, diff: bool = False):
        """
        Create a mutable config model backed by a file path or in-memory lines.

        The same object is used for read-only browsing, write-back generation,
        and test-time in-memory rendering. Parsing state that is only relevant
        while walking the config file is also stored here to keep the parser
        implementation incremental and easy to reset.
        """
        self.ssh_config_file: Optional[str] = file
        self.ssh_config_lines: list[str] = list(config_lines) if config_lines is not None else []
        self.config_lines_full: list[ConfigLine] = []
        self.included_files: list[str] = []

        # configuration representation (array of SSH groups?)
        self.groups: list[SSH_Group] = [SSH_Group(name=DEFAULT_GROUP_NAME, desc=DEFAULT_GROUP_DESC)]
        self.all_hosts: list[SSH_Host] = []

        # options
        self.write_locked: bool = False     # Internal "safety" for not allowing to change original file when writing is unsafe
        self.write_locked_reason: str = ""
        self.stdout: bool = stdout          # Redirect configuration change/write to stdout instead of input file
        self.diff: bool = diff              # Option to only show differences that would be applied to configuration
        self.opts: dict = {}

        # parsing "cache" info
        self.current_grindex: int = 0
        self.current_group: str = DEFAULT_GROUP_NAME
        self.current_host: Optional[SSH_Host] = None
        self.current_host_info: list = []
        self.current_host_pass: str = ""

        # Support for global keywords
        self.global_params: dict = {}


    def _set_write_locked(self, reason: str) -> None:
        self.write_locked = True
        if not self.write_locked_reason:
            self.write_locked_reason = reason


    def _build_line_records(self, lines: list[str], source_file: Optional[str]) -> list[ConfigLine]:
        return [ConfigLine(text=line, source_file=source_file, source_line=index + 1) for index, line in enumerate(lines)]


    def _read_config_lines(self, config_path: str) -> list[str]:
        with open(config_path, "r") as fh:
            return fh.read().split("\n")


    def _resolve_include_paths(self, value: str, base_dir: str) -> list[str]:
        include_paths: list[str] = []

        for pattern in shlex.split(value):
            expanded_pattern = os.path.expandvars(os.path.expanduser(pattern))
            if not os.path.isabs(expanded_pattern):
                expanded_pattern = os.path.join(base_dir, expanded_pattern)

            matched_paths = sorted(glob.glob(expanded_pattern))
            if matched_paths:
                include_paths.extend(matched_paths)
            else:
                warn(f"Included config path did not match any files: {expanded_pattern}")

        return include_paths


    def _load_line_records_from_file(self, config_path: str) -> list[ConfigLine]:
        """
        Load the root config and flatten supported top-level include files.

        This intentionally implements only the current safe feature boundary:
        top-level `Include` directives are read into one ordered parse stream so
        browsing and inheritance work correctly, but the config is write-locked
        as soon as includes are involved.
        """
        root_path = os.path.abspath(config_path)
        root_lines = self._read_config_lines(root_path)
        self.ssh_config_lines = root_lines

        records: list[ConfigLine] = []
        in_top_level_scope = True
        base_dir = os.path.dirname(root_path)

        for line_number, raw_line in enumerate(root_lines, start=1):
            stripped_line = raw_line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                records.append(ConfigLine(text=raw_line, source_file=root_path, source_line=line_number))
                continue

            match = re.search(r"^(\w+)\s*(?:=\s*|\s+)([^=]+)$", stripped_line)
            if not match:
                records.append(ConfigLine(text=raw_line, source_file=root_path, source_line=line_number))
                continue

            keyword, value = match.groups()
            keyword = keyword.lower()

            if keyword in {"host", "match"}:
                in_top_level_scope = False

            if in_top_level_scope and keyword == "include":
                # Includes are currently read-only: we flatten them for browsing,
                # but we do not try to write changes back across multiple files yet.
                self._set_write_locked("Keyword 'Include' found, configuration currently read-only, when this keyword is used!")
                for include_path in self._resolve_include_paths(value, base_dir):
                    include_path = os.path.abspath(include_path)
                    if include_path not in self.included_files:
                        self.included_files.append(include_path)
                    try:
                        records.extend(self._build_line_records(self._read_config_lines(include_path), include_path))
                    except OSError as exc:
                        warn(f"Failed reading included SSH config file ({include_path}): {exc}")
                continue

            records.append(ConfigLine(text=raw_line, source_file=root_path, source_line=line_number))

        return records


    def _get_or_create_group_index(self, name: str, source_file: Optional[str] = None, source_line: int = 0) -> int:
        for index, group in enumerate(self.groups):
            if group.name == name:
                if source_file:
                    source_ref = (source_file, source_line)
                    if source_ref not in group.source_refs:
                        group.source_refs.append(source_ref)
                return index

        new_group = SSH_Group(name=name)
        if source_file:
            new_group.source_refs.append((source_file, source_line))
        self.groups.append(new_group)
        return len(self.groups) - 1


    def read(self):
        """
        Read the source config into annotated line records.

        Missing config files can be created interactively. When the config is
        already in memory only, the current line buffer is simply annotated with
        source metadata and returned.
        """
        config_path = self.ssh_config_file
        if config_path is None:
            self.config_lines_full = self._build_line_records(self.ssh_config_lines, None)
            return self

        try:
            self.config_lines_full = self._load_line_records_from_file(config_path)
        except FileNotFoundError:
            warn(f"SSH config file not found ({config_path})")
            answer = input("Would you like to create it (y/n)? :")
            if answer.lower() in ["y", "yes"]:
                try:
                    # Make sure full path is available
                    config_dir = os.path.dirname(config_path)
                    if config_dir:
                        os.makedirs(config_dir, exist_ok=True)
                    # Write initial config file
                    with open(config_path, "w") as file:
                        file.write(SSHCONFIG_SIGNATURE_LINE)
                    # SSH config must be owner read only
                    os.chmod(config_path, 0o600)
                    
                    # Assume we start with empty lines
                    self.ssh_config_lines = []
                    self.config_lines_full = []
                except OSError as exc:
                    error(f"Failed to create ssh config file in ({config_path}): {exc}")
                    exit(1)
            else:
                error("Cannot proceed without config file")
                exit(1)
        except OSError as exc:
            error(f"Failed reading SSH config file ({config_path}): {exc}")
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
        Parse the config stream into groups, hosts, patterns, and global options.

        SSHClick treats comment metadata as part of the model, so parsing is not
        limited to OpenSSH keywords alone. Once all lines are consumed, a second
        pass resolves inherited parameters from globals and pattern hosts.
        """
        if not self.config_lines_full:
            self.config_lines_full = self._build_line_records(self.ssh_config_lines, self.ssh_config_file)

        # Parse each line of the configuration, line by line
        for config_line in self.config_lines_full:
            source_file = config_line.source_file
            line_number = config_line.source_line
            source_label = f"{source_file}:{line_number}" if source_file else f"line {line_number}"
            line = config_line.text.strip()     # remove start and end whitespace
            if not line:
                continue   # Skip empty lines, go to next...
            
            if line.startswith("#"):
                # Reworked parsing method... special "meta" keys not needed, regex now parses words
                # so its much more "freely" in reading from config file writing is still in legacy style
                # in future, output config write styles could be changed... 
                #
                # Meta regex should match following meta definition styles:
                #>  "#@{meta-key}: {meta-value}
                #>  "# {meta-key}: {meta-value}
                match = re.search(r"^#[ @]{1}(\w+):\s+(.+)$", line)

                # If we didn't find metadata, its just comment or something we dont care about
                if not match:
                    continue
                
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

                    debug(f"META group: '{value}'")
                    self.current_grindex = self._get_or_create_group_index(value, source_file, line_number)
                    self.current_group = value
                    debug(f"META Group index: {self.current_grindex}")
                    continue

                elif metadata == MetaTAG.GDESC:
                    debug(f"META Group description: '{value}'")
                    if not self.groups[self.current_grindex].desc:
                        self.groups[self.current_grindex].desc = value
                    continue

                elif metadata == MetaTAG.GINFO:
                    debug(f"META Group info: '{value}'")
                    if value not in self.groups[self.current_grindex].info:
                        self.groups[self.current_grindex].info.append(value)
                    continue

                elif metadata == MetaTAG.HINFO:
                    debug(f"META Host info cached: '{value}'")
                    self.current_host_info.append(value)
                    continue

                else:
                    warn(f"Unhandled metadata: '{metadata}' on SSH-config {source_label}")
                    continue

            # This NEW regex should fix this spec from ssh_config definition:
            # > "Configuration options may be separated by whitespace or optional whitespace and exactly one ‘=’ "
            # NOTE: I have tested clients like ssh or sftp, they dont complain, and allow multiple "=" symbols. :)
            match = re.search(r"^(\w+)\s*(?:=\s*|\s+)([^=]+)$", line)
            if not match:
                warn(f"Ignoring unmatched keyword in configuration line '{line}' on SSH-config ({source_label})")
                continue

            keyword, value = match.groups()
            keyword = keyword.lower()         # keywords are case insensitive, so we lowercase them
            
            # First we need to handle "top-level" keywords that defines host blocks or special behavior
            # ----- INCLUDE -----
            if keyword == "include":
                self._set_write_locked("Keyword 'Include' found, configuration currently read-only, when this keyword is used!")

            # ----- MATCH -----
            elif keyword == "match":
                warn("Unsupported keyword 'Match' found, ignoring...")

            # ----- HOST -----
            elif keyword == "host":
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
                    source_file=source_file or "",
                    source_line=line_number,
                    type=host_type,
                    info=self.current_host_info,
                )

                # debug(f"SSH Host definition created: {new_host}")
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
                        if keyword not in self.global_params:
                            self.global_params[keyword] = [value]
                        else:
                            self.global_params[keyword].append(value)
                    else:
                        self.global_params[keyword] = value
                else:
                    debug(f"SSH Config keyword for host '{self.current_host.name}': {keyword} -> {value}")
                    if keyword in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
                        if keyword not in self.current_host.params:
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
        Resolve effective parameters for each normal host.

        The algorithm follows SSHClick's current interpretation of OpenSSH order:
        global parameters are applied first, then pattern hosts are considered in
        file order with first-match-wins behavior for each parameter.
        """
        if DEBUG:
            start = time.time()

        for host in self.all_hosts:
            # We only check what "normal" hosts inherits
            if host.type == HostType.PATTERN:
                continue

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
                            if param in host.params:
                                continue
                            if param in host.matched_params:
                                continue
                            # if param not in host.params or param not in host.matched_params:
                            host.matched_params[param] = (value, other_host.name)
        if DEBUG:
            end = time.time() - start
            debug(f"Inheritance check elapsed: {end:0.6f}s")
            # inspect(self, all=True)


    def generate_ssh_config(self) -> bool:
        """
        Render the in-memory model back into SSH config text.

        Depending on the active mode, the rendered output is written back to the
        original file, sent to stdout, or diffed against the original content.
        When the config is write-locked or only exists in memory, rendering still
        happens but disk writes are skipped.
        """
        # If config is write locked, dont allow saving
        if self.write_locked:
            warn("Configuration modification is disabled")
            warn(self.write_locked_reason)
            return False

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
                lines.append(f"Host {host.name}{alt_names}")

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

        # If we are running in diff mode, only show the changes, and return false (dont store new config)
        if self.diff:
            output_diff(self.ssh_config_lines, lines)
            return False

        # Store new config lines as actual
        self.ssh_config_lines = lines

        # Prepare multiline content string for output configuration
        config_content = "\n".join(lines)

        # When output is changed to write config to STDOUT, just print all lines
        if self.stdout:
            print(config_content)
            return False

        # In-memory configuration objects can be rendered and mutated, but must not write to disk
        if self.ssh_config_file is None:
            return False

        # Write content to target config file
        try:
            with open(self.ssh_config_file, "w") as config_file:
                config_file.write(config_content)
                return True
        except OSError as exc:
            error(f"Failed modifying configuration file: {self.ssh_config_file}! ({exc})")
            exit(1)


    def check_group_by_name(self, name: str) -> bool:
        return any(group.name == name for group in self.groups)


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
        return any(host.name == name for host in self.all_hosts)


    def get_host_by_name(self, name: str) -> SSH_Host:
        """
        Find host in configuration that matches the name (strict match, one only!)
        On success returns host and his assigned group, on fail depending on 'throw_on_fail' flag
        function will either return ('None','None') or will throw exception
        """
        for host in self.all_hosts:
            if host.name == name:
                return host
        raise Exception(f"Requested host '{name}' not found in the SSH configuration")


    def get_all_host_names(self) -> list[str]:
        return [host.name for host in self.all_hosts]


    def get_all_group_names(self) -> list[str]:
        return [group.name for group in self.groups]


    def filter_hosts(self, group_filter: str, name_filter: str) -> list[SSH_Host]:
        """
        Function takes optional group and name regex, and if they are not None or empty,
        function creates a new filtered list of SSH hosts
        """
        filtered_hosts = []

        for host in self.all_hosts:
            # If group filter is defined, check if current host matches the group name to progress
            if group_filter and not re.search(group_filter, host.group):
                continue
            
            # When host is not skipped, check if name filter is used, and filter out hosts
            if name_filter and not re.search(name_filter, host.name):
                continue

            # If host is not skipped, add it to filtered list
            filtered_hosts.append(host)

        return filtered_hosts


    def add_host(self, host: SSH_Host):
        """Attach a host to the configured group it declares."""
        if not host.group:
            raise Exception("Internal ERROR, host group missing, or empty, please report issue!")
        
        found_group = next((group for group in self.groups if group.name == host.group), None)
        if found_group is None:
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
        Move a host object between two already-resolved groups.

        The host keeps its identity and parameters; only the owning group and
        the concrete group host/pattern lists are updated.
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
        Trace the effective ProxyJump chain for a host.

        The return value is ordered from the target host backwards through the
        required jump hosts, which matches the expectations of SSHClick's graph
        and network views. If a referenced jump host is missing or a loop is
        detected, the trace fails and returns `None`.
        """
        # Keep list of linked hosts via proxyjump option
        traced_hosts = []
        visited_hosts = set()

        # we are first checking host that is asked, and then check if that host has a "proxy" defined
        # if proxy is defined, we add found host to traced list, and search attached proxy, it this way we
        # can trace full connection path for later graph processing
        while True:
            if name in visited_hosts:
                warn(f"Cannot trace proxyjump for host '{name}', loop detected in proxy chain!")
                return None

            visited_hosts.add(name)

            # Search for host in current configuration
            if (not self.check_host_by_name(name)):
                warn(f"Cannot get info for used host '{name}' as next proxyjump, as it is not defined in configuration!")
                return None

            found_host = self.get_host_by_name(name)

            # Add current host, and its table to traced lists
            traced_hosts.append(found_host)

            # Find proxy info if it exists, if not, break the loop
            proxy_val, _ = found_host.get_applied_param("proxyjump")

            if not proxy_val:
                break
            name = proxy_val

        return traced_hosts
