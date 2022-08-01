from dataclasses import dataclass, field
import importlib

@dataclass
class SSH_Host:
    """ Class for SSH host config structure """
    name: str
    group: str
    type: str = "normal"
    info: list[str] = field(default_factory=list)
    params: dict[str, str] = field(default_factory=dict)

    inherited_params: list[tuple[str, dict]] = field(default_factory=list)
    print_style: str = "panel1"

    # Method for interaction with printing the object via Rich library
    def __rich__(self):
        try:
            style = importlib.import_module(f'lib.host_styles.{self.print_style}')
            return style.render(self)
        except:
            # Normally this would be filtered by click library so we never output this
            return f"SSH_Host style [bright_red]'{self.print_style}'[/] is not implemented, or is broken!"

