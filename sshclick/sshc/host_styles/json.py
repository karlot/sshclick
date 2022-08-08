from ..ssh_host import SSH_Host
from rich.json import JSON
import json

#------------------------------------------------------------------------------
# Render host data as JSON output
#------------------------------------------------------------------------------
def render(host: SSH_Host):
    host_json = json.dumps(host.__dict__)
    return JSON(host_json)
