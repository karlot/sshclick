from rich.console import Console
from difflib import unified_diff

# We use console to get nice colors
out = Console()

def generate_diff(original: list[str], modified: list[str]) -> None:
    """
    Print out what would be difference after config change is applied
    """
    
    # Generate diff line object iterator
    diff = unified_diff(original, modified, fromfile="original", tofile="modified", lineterm="")

    # Print colored diff
    for line in diff:
        if line.startswith("+"):
            out.print(line, style="green", markup=False, highlight=False)
        elif line.startswith("-"):
            out.print(line, style="red", markup=False, highlight=False)
        elif line.startswith("@@"):
            out.print(line, style="cyan", markup=False, highlight=False)
        else:
            out.print(line, markup=False, highlight=False)
