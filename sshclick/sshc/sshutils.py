import os.path
from .ssh_config import SSH_Config
from rich.console import Console
err = Console(stderr=True)

# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d: dict, ignored: list = []) -> dict:
    return {k: v for (k, v) in d.items() if k not in ignored}


# Custom parsing trough parent object types until required parameters are found
# Then build config object and bound it to ctx.obj
def build_context_config(ctx):
    if ctx.obj is None:
        current_obj = ctx.parent
        try:
            while True:
                if "sshconfig" in current_obj.params:
                    full_path = os.path.expanduser(current_obj.params["sshconfig"])
                    ctx.obj = SSH_Config(
                        file=full_path,
                        stdout=current_obj.params["stdout"]
                    ).read().parse()
                    break
                else:
                    current_obj = current_obj.parent
        except:
            err.print("INTERNAL ERROR: Could not reconstruct context for SSH configuration!")
            ctx.exit(1)


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_host_names(ctx, param, incomplete):
    build_context_config(ctx)

    all_hosts = ctx.obj.get_all_host_names()
    return [k for k in all_hosts if k.startswith(incomplete)]


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_group_names(ctx, param, incomplete):
    build_context_config(ctx)

    all_groups = ctx.obj.get_all_group_names()
    return [k for k in all_groups if k.startswith(incomplete)]


