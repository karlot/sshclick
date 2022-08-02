from dataclasses import dataclass, field

@dataclass
class SSH_Group:
    """ Class for SSH Group config structure """
    name: str
    desc: str = ""
    info: list = field(default_factory=list)
    hosts: list = field(default_factory=list)
    patterns: list = field(default_factory=list)

    print_style: str = ""

    def __rich__():
        pass


