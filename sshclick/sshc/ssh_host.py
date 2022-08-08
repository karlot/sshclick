from dataclasses import dataclass, field
import importlib

from rich.console import Console
console = Console()

DEBUG_STYLES = False

@dataclass
class SSH_Host:
    """ Class for SSH host config structure """
    name: str
    group: str
    type: str = "normal"
    info: list = field(default_factory=list)
    params: dict = field(default_factory=dict)

    inherited_params: list = field(default_factory=list)
    print_style: str = "panels"


    # Method for interaction with printing the object via Rich library
    # Each supported style should be located in defined folder (by default under "host_styles")
    # Each module must have "render" function, and return "rich renderable" object
    def __rich__(self):
        try:
            # If current host "print_style" for is set to "panels", we will try
            # to import module from "./host_styles/panels.py"
            style = importlib.import_module(f'sshclick.sshc.host_styles.{self.print_style}')
            return style.render(self)
        except ModuleNotFoundError:
            return f"SSH_Host style [bright_red]'{self.print_style}'[/] is not implemented!"
        except Exception:
            if DEBUG_STYLES:
                console.print_exception(show_locals=False, max_frames=1, suppress=[importlib])
            return f"SSH_Host style [bright_red]'{self.print_style}'[/] is broken!"
