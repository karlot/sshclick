from dataclasses import dataclass, field
from enum import Enum
import importlib
import socket

from ..globals import DEFAULT_HOST_STYLE

from rich.console import Console
console = Console()

class HostType(str, Enum):
    NORMAL = "normal"
    PATTERN = "pattern"

DEBUG_STYLES = False


@dataclass
class SSH_Host:
    """ Class for SSH host config structure """
    name: str
    group: str
    password: str = ""
    type: HostType = HostType.NORMAL
    alt_names: list = field(default_factory=list)
    info: list = field(default_factory=list)
    print_style: str = DEFAULT_HOST_STYLE

    # Parameters separation, from directly configured under host definition, global
    # patterns that apply to every host defined after it (unless explicitly overridden)
    # and ones matched by pattern definition
    params: dict = field(default_factory=dict)

    # Map indicating source of the parameter
    # inherited_params: list[tuple[str, dict]] = field(default_factory=list)

    # {"user": ("testUSER", "testhost*")}
    matched_params: dict[str, tuple[str, str]] = field(default_factory=dict)


    def get_all_params(self) -> list[str]:
        """
        Method returns all parameters that will be used for given host, both directly configured and inherited
        """
        return list({ **self.params, **self.matched_params}.keys())
    

    def get_applied_param(self, param) -> tuple[str, str]:
        """
        Function that checks for specific host, about requested parameter, and
        returns value and source from where its pulled. If its not found, returns empty value
        """
        if param in self.matched_params:
            # Requested parameter for the host comes from outside host definition
            return self.matched_params[param]
        elif param in self.params:
            # Requested parameter for the host is defined only locally for the 
            value = self.params[param]
            return (value, "local")
        # There is no requested parameter for this host
        return ("", "")


    # Method for interaction with printing the object via Rich library
    # Each supported style should be located in defined folder (by default under "host_styles")
    # Each module must have "render" function, and return "rich renderable" object
    def __rich__(self):
        try:
            # If current host "print_style" is set to "panels", we will try
            # to import module from "./host_styles/panels.py"
            style = importlib.import_module(f'sshclick.sshc.host_styles.{self.print_style}')
            return style.render(self)
        except ModuleNotFoundError:
            return f"SSH_Host style [bright_red]'{self.print_style}'[/] is not implemented!"
        except Exception:
            if DEBUG_STYLES:
                console.print_exception(show_locals=False, max_frames=1, suppress=[importlib])
            return f"SSH_Host style [bright_red]'{self.print_style}'[/] is broken!"
