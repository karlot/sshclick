from dataclasses import dataclass


@dataclass(frozen=True)
class SSHParameterSpec:
    """Guided metadata for SSH config parameters used by the TUI picker."""

    choices: list[str] | None = None
    description: str = ""
    value_kind: str = "text"


ALL_PARAM_SPECS = {
    "AddKeysToAgent": SSHParameterSpec(["no", "yes", "confirm", "ask"], "Controls whether keys are automatically added to ssh-agent.", "choice"),
    "AddressFamily": SSHParameterSpec(["any", "inet", "inet6"], "Restricts connections to IPv4, IPv6, or either address family.", "choice"),
    "BatchMode": SSHParameterSpec(["no", "yes"], "Disables interactive prompts so scripted or unattended sessions fail fast.", "choice"),
    "BindAddress": SSHParameterSpec(description="Uses a specific local source address when opening the connection.", value_kind="address"),
    "BindInterface": SSHParameterSpec(description="Uses a specific local network interface for the connection.", value_kind="interface"),
    "CASignatureAlgorithms": SSHParameterSpec(description="Overrides the accepted CA signature algorithms for host and user certificates."),
    "CertificateFile": SSHParameterSpec(description="Adds a certificate file presented during public key authentication.", value_kind="path"),
    "CheckHostIP": SSHParameterSpec(["no", "yes"], "Checks that the host key also matches the resolved server IP.", "choice"),
    "Ciphers": SSHParameterSpec(description="Overrides the preferred cipher list for the SSH session."),
    "ClearAllForwardings": SSHParameterSpec(["no", "yes"], "Clears any inherited port-forwarding rules for this entry.", "choice"),
    "Compression": SSHParameterSpec(["no", "yes"], "Enables SSH stream compression for slower links.", "choice"),
    "ConnectionAttempts": SSHParameterSpec(description="Retries the initial TCP connection this many times before giving up.", value_kind="integer"),
    "ConnectTimeout": SSHParameterSpec(description="Sets the connection timeout in seconds.", value_kind="integer"),
    "DynamicForward": SSHParameterSpec(description="Creates a local SOCKS proxy listener for dynamic forwarding.", value_kind="endpoint"),
    "EscapeChar": SSHParameterSpec(description="Changes the escape character used in interactive SSH sessions."),
    "ExitOnForwardFailure": SSHParameterSpec(["no", "yes"], "Fails the session if a requested port forwarding cannot be created.", "choice"),
    "FingerprintHash": SSHParameterSpec(["sha256", "md5"], "Selects the hash style used when displaying host key fingerprints.", "choice"),
    "ForkAfterAuthentication": SSHParameterSpec(description="Sends ssh to the background after authentication succeeds."),
    "ForwardAgent": SSHParameterSpec(["no", "yes"], "Allows the remote host to use your local ssh-agent.", "choice"),
    "ForwardX11": SSHParameterSpec(["no", "yes"], "Enables X11 forwarding for graphical applications.", "choice"),
    "ForwardX11Timeout": SSHParameterSpec(description="Controls how long untrusted X11 forwarding remains valid.", value_kind="duration"),
    "ForwardX11Trusted": SSHParameterSpec(["no", "yes"], "Uses trusted X11 forwarding instead of the safer untrusted mode.", "choice"),
    "GatewayPorts": SSHParameterSpec(["no", "yes"], "Lets remotely forwarded ports listen on non-local addresses.", "choice"),
    "HostbasedAcceptedAlgorithms": SSHParameterSpec(description="Overrides accepted algorithms for hostbased authentication."),
    "HostbasedAuthentication": SSHParameterSpec(["no", "yes"], "Enables hostbased authentication if the server supports it.", "choice"),
    "HostKeyAlgorithms": SSHParameterSpec(description="Overrides the preferred host key algorithms."),
    "HostKeyAlias": SSHParameterSpec(description="Uses an alternate host key alias in known_hosts.", value_kind="host"),
    "HostName": SSHParameterSpec(description="Sets the real hostname or IP address used for the connection.", value_kind="host"),
    "IdentityFile": SSHParameterSpec(description="Adds a private key file used for public key authentication.", value_kind="path"),
    "KexAlgorithms": SSHParameterSpec(description="Overrides the preferred key exchange algorithms."),
    "LocalCommand": SSHParameterSpec(description="Runs a local command after the SSH connection is established."),
    "LocalForward": SSHParameterSpec(description="Forwards a local port to a remote address or socket.", value_kind="forward"),
    "MACs": SSHParameterSpec(description="Overrides the preferred message authentication code algorithms."),
    "PasswordAuthentication": SSHParameterSpec(["yes", "no"], "Enables or disables password-based authentication.", "choice"),
    "PermitLocalCommand": SSHParameterSpec(["no", "yes"], "Allows LocalCommand to run for this entry.", "choice"),
    "Port": SSHParameterSpec(description="Sets the remote SSH port.", value_kind="integer"),
    "PreferredAuthentications": SSHParameterSpec(description="Overrides the order of authentication methods ssh should try."),
    "ProxyCommand": SSHParameterSpec(description="Uses an external command as the transport to reach the destination."),
    "ProxyJump": SSHParameterSpec(description="Routes the SSH connection through one or more jump hosts.", value_kind="host"),
    "RemoteCommand": SSHParameterSpec(description="Runs a command on the remote host immediately after connecting."),
    "RemoteForward": SSHParameterSpec(description="Forwards a remote port back to a local address or socket.", value_kind="forward"),
    "RequestTTY": SSHParameterSpec(["no", "yes", "force", "auto"], "Controls whether ssh requests an interactive TTY.", "choice"),
    "ServerAliveCountMax": SSHParameterSpec(description="Limits how many keepalive replies may be missed before disconnecting.", value_kind="integer"),
    "ServerAliveInterval": SSHParameterSpec(description="Sends keepalive packets every N seconds to keep the session alive.", value_kind="integer"),
    "StrictHostKeyChecking": SSHParameterSpec(
        ["ask", "yes", "accept-new", "no", "off"],
        "Controls how ssh reacts to new or changed host keys.",
        "choice",
    ),
    "TCPKeepAlive": SSHParameterSpec(["yes", "no"], "Enables TCP keepalive packets at the socket layer.", "choice"),
    "UpdateHostKeys": SSHParameterSpec(["yes", "no", "ask"], "Lets the server advertise and update additional host keys after trust is established.", "choice"),
    "User": SSHParameterSpec(description="Sets the remote login user for this entry.", value_kind="user"),
    "UserKnownHostsFile": SSHParameterSpec(description="Overrides the known_hosts file used for host key storage.", value_kind="path"),
}

# Keep the legacy structure intact for CLI completion and existing call sites.
ALL_PARAMS = {name: spec.choices for name, spec in ALL_PARAM_SPECS.items()}
ALL_PARAM_LC_NAMES = [name.lower() for name in ALL_PARAMS]


def get_param_spec(name: str) -> SSHParameterSpec | None:
    """Return the richer guided metadata for an SSH config parameter."""

    return ALL_PARAM_SPECS.get(name)


def get_param_choices(name: str) -> list[str] | None:
    """Return the allowed value choices for a parameter when they are known."""

    spec = get_param_spec(name)
    return None if spec is None else spec.choices


def get_param_description(name: str) -> str:
    """Return the short guided description for a parameter."""

    spec = get_param_spec(name)
    return "" if spec is None else spec.description


PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "certificatefile",
    "identityfile",
    "include",
    "localforward",
    "remoteforward",
    "dynamicforward",
]
