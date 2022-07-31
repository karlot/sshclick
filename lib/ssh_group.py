from dataclasses import dataclass, field
from lib.ssh_host import SSH_Host

@dataclass
class SSH_Group:
    """ Class for SSH Group config structure """
    name: str
    desc: str = ""
    info: list[str] = field(default_factory=list)
    hosts: list[SSH_Host] = field(default_factory=list)
    patterns: list[SSH_Host] = field(default_factory=list)

    print_style: str = ""

    def __rich__():
        pass


