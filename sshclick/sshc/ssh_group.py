from typing import List
from dataclasses import dataclass, field
from .ssh_host import SSH_Host

@dataclass
class SSH_Group:
    """ Class for SSH Group config structure """
    name: str
    desc: str = ""
    info: list = field(default_factory=list)
    hosts: List[SSH_Host] = field(default_factory=list)
    patterns: List[SSH_Host] = field(default_factory=list)

    print_style: str = ""

    def __rich__(self):
        pass


