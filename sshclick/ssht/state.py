from dataclasses import dataclass

from sshclick.core import HostType, SSH_Config, SSH_Group, SSH_Host

# Shared node type used by the tree, details pane, and modal flows.
SSHNode = SSH_Group | SSH_Host | None


@dataclass
class TUIState:
    """Minimal shared state for the current TUI session."""

    config_file: str
    sshconf: SSH_Config
    current_node: SSHNode = None

    @property
    def is_read_only(self) -> bool:
        return self.sshconf.write_locked

    @property
    def read_only_reason(self) -> str:
        return self.sshconf.write_locked_reason

    @property
    def host_count(self) -> int:
        """Return only normal hosts, excluding pattern definitions."""
        return len([host for host in self.sshconf.all_hosts if host.type == HostType.NORMAL])

    @property
    def pattern_count(self) -> int:
        """Return hosts that represent pattern-based definitions."""
        return len([host for host in self.sshconf.all_hosts if host.type == HostType.PATTERN])

    @property
    def include_count(self) -> int:
        return len(self.sshconf.included_files)
