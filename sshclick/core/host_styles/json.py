from ..ssh_host import SSH_Host
from rich.json import JSON
import json

#------------------------------------------------------------------------------
# Render host data as JSON output
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    """Render the raw host object as Rich JSON output."""
    host_json = json.dumps(host.__dict__)
    return JSON(host_json)
