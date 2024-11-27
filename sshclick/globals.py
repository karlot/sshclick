# -----------------------------------------------------------------------------
# SSH Configuration
# -----------------------------------------------------------------------------
USER_SSH_CONFIG = "~/.ssh/config"
# USER_SSH_CONFIG  = "~/.ssh/config_demo"


# -----------------------------------------------------------------------------
# Output Styling
# -----------------------------------------------------------------------------
DEFAULT_HOST_STYLE = "panels"
ENABLED_HOST_STYLES = ["panels", "card", "simple", "table", "table2", "json"]


# -----------------------------------------------------------------------------
# SSH Config write options
# -----------------------------------------------------------------------------
SSHCONFIG_SIGNATURE_LINE = "#<<<<< SSH Config file managed by sshclick >>>>>\n"
SSHCONFIG_INDENT = 4
SSHCONFIG_META_PREFIX = "@"
SSHCONFIG_META_SEPARATOR = ":"


# -----------------------------------------------------------------------------
# SSH Connection options
# -----------------------------------------------------------------------------
SSH_CONNECT_TIMEOUT = 3