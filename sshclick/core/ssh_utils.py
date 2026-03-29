import os.path
import re
import sys
from typing import List

from ..globals import ENABLED_HOST_STYLES
from .ssh_config import SSH_Config
from .ssh_parameters import ALL_PARAM_LC_NAMES


# Make a copy of input dict with all keys as LC and filtered out based on input filter list
def filter_dict(d: dict, ignored: list = []) -> dict:
    return {k: v for (k, v) in d.items() if k not in ignored}


# Custom parsing trough parent object types until required parameters are found
# Then build config object and bound it to ctx.obj
def build_context_config(ctx) -> None:
    """
    Rebuild `ctx.obj` when Click autocompletion bypasses the normal root setup.

    Click completion does not always preserve the original command context chain,
    so nested commands may need to recover the `--config` path from a parent
    context and parse the SSH config on demand.
    """
    if ctx.obj is not None:
        return

    current_obj = ctx.parent
    while current_obj is not None:
        params = getattr(current_obj, "params", None) or {}
        config = params.get("config")
        if config is not None:
            full_path = os.path.expanduser(config)
            ctx.obj = SSH_Config(file=full_path, stdout=params.get("stdout", False)).read().parse()
            return
        current_obj = current_obj.parent

    print("\nINTERNAL ERROR: Could not reconstruct context for SSH configuration!", file=sys.stderr)
    ctx.exit(1)


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_host_names(ctx, param, incomplete) -> List[str]:
    build_context_config(ctx)
    all_hosts = ctx.obj.get_all_host_names()
    return [k for k in all_hosts if k.startswith(incomplete)]


# For some reason I cant get context object initialized by main app when running autocomplete
# BUG: https://github.com/pallets/click/issues/2303
def complete_ssh_group_names(ctx, param, incomplete) -> List[str]:
    build_context_config(ctx)
    all_groups = ctx.obj.get_all_group_names()
    return [k for k in all_groups if k.startswith(incomplete)]


def complete_params(ctx, param, incomplete) -> List[str]:
    return [k for k in ALL_PARAM_LC_NAMES if k.startswith(incomplete)]


def complete_styles(ctx, param, incomplete) -> List[str]:
    return [k for k in ENABLED_HOST_STYLES if k.startswith(incomplete)]


# We use this functions to give a tuple of group/host names as input, where some names
# can be regexps (with "r:"" prefix), and we evaluate regex based on "all_names" list
# which we use to create a set of expanded host names; direct ones, and expanded ones from
# regex processing. Then return final list...
def expand_names(names: tuple, all_names: list) -> List[str]:
    """
    Expand a mixed list of direct names and `r:` regex selectors.

    The returned list keeps only unique matches, so callers can combine exact
    selections with regex-driven bulk operations without extra deduplication.
    """
    selected = set()

    for name in names:
        if name.startswith("r:"):
            name_re = name.split(":")[1]
            # print(f"Got regex type name def - '{name_re}'")
            for i_name in all_names:
                match = re.search(name_re, i_name)
                if match:
                    selected.add(i_name)
        else:
            selected.add(name)
    return list(selected)
