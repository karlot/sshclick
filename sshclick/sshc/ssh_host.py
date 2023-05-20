from typing import List, Tuple, Dict
from dataclasses import dataclass, field
import importlib
import socket

from ..globals import DEFAULT_HOST_STYLE

from rich.console import Console
console = Console()

DEBUG_STYLES = False

@dataclass
class SSH_Host:
    """ Class for SSH host config structure """
    name: str
    group: str
    password: str = ""
    type: str = "normal"
    info: list = field(default_factory=list)
    params: dict = field(default_factory=dict)

    inherited_params: list = field(default_factory=list)
    print_style: str = DEFAULT_HOST_STYLE


    def get_all_params(self) -> Dict[str, str]:
        """
        Method combines configured host parameters with all
        host inherited parameters, and returns them as dictionary
        """
        return {
            **self.params,
            **{ k: v for d in self.inherited_params for k, v in d[1].items()}
        }
    

    def get_target(self) -> str:
        """
        Method returns whatever host has defined as target for connection.
        If name is just alias, and host has defined "hostname" then hostname will be returned
        When there is no hostname, only host name is returned
        """
        return self.name if not "hostname" in self.params else self.params["hostname"]


    def resolve_target(self) -> Tuple[str, bool]:
        """
        Method returns tuple of resolved IP address for this host, and error as bool value,
        that is set to true if host cannot be resolved
        """
        target = self.get_target()
        try:
            target_ip = socket.gethostbyname(target)
            return (target_ip, False)
        except socket.error:
            return ("", True)


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
