# TODO: Do we need to keyword consider "scope" ?
# TODO: We can make few "types" that would give out possible values for completions or
#       validations. For instance "Choice('yes', 'no')", or FilePath(), or "Cyphers()"

# Updated for last version: https://man.openbsd.org/OpenBSD-7.1/ssh_config

# Brainstorming...
# ----------------
# class ParamChoice:
#     def __init__(self, *choices):
#         self.list = choices
#         self.default = choices[0]

# class ParamInt:
#     def __init__(self, default):
#         self.list = ()
#         self.default = default

# All SSH parameters
# ------------------
# Idea is to have key, for which we can provide auto-completion, and known values
# which we potentially can autocomplete, or at least provide validation that value
# one of the possible ones. SSH config is extremely verbose
ALL_PARAMS = {
    "AddKeysToAgent": ["no", "yes", "confirm", "ask"],
    "AddressFamily": ["any", "inet", "inet6"],
    "BatchMode": ["no", "yes"],
    "BindAddress": None,
    "BindInterface": None,
    # --- not sure how to support these ---
    # "CanonicalDomains": None,
    # "CanonicalizeFallbackLocal": ["yes", "no"],
    # "CanonicalizeHostname": ["no", "yes", "always", "none"],
    # "CanonicalizeMaxDots": None,
    # "CanonicalizePermittedCNAMEs": None,
    "CASignatureAlgorithms": None,
    "CertificateFile": None,
    "CheckHostIP": ["no", "yes"],
    "Ciphers": None,
    "ClearAllForwardings": ["no", "yes"],
    "Compression": ["no", "yes"],
    "ConnectionAttempts": None,
    "ConnectTimeout": None,
    # "ControlMaster": ["no", "yes", "ask", "auto", "autoask"],
    # "ControlPath": None,
    # "ControlPersist": ["no", "yes"],
    "DynamicForward": None,
    "EscapeChar": None,
    "ExitOnForwardFailure": ["no", "yes"],
    "FingerprintHash": ["sha256", "md5"],
    "ForkAfterAuthentication": None,
    "ForwardAgent": ["no", "yes"],
    "ForwardX11": ["no", "yes"],
    "ForwardX11Timeout": None,
    "ForwardX11Trusted": ["no", "yes"],
    "GatewayPorts": ["no", "yes"],
    # "GlobalKnownHostsFile": None,
    # "GSSAPIAuthentication": ["no", "yes"],
    # "GSSAPIDelegateCredentials": ["no", "yes"],
    # "HashKnownHosts": ["no", "yes"],
    "HostbasedAcceptedAlgorithms": None,
    "HostbasedAuthentication": ["no", "yes"],
    "HostKeyAlgorithms": None,
    "HostKeyAlias": None,
    "HostName": None,
    # "IdentitiesOnly": ["no", "yes"],
    # "IdentityAgent": None,
    "IdentityFile": None,
    # "IgnoreUnknown": None,
    # "IPQoS": None,
    # "KbdInteractiveAuthentication": ["yes", "no"],
    # "KbdInteractiveDevices": ["bsdauth", "pam", "skey"],
    "KexAlgorithms": None,
    # "KnownHostsCommand": None,
    "LocalCommand": None,
    "LocalForward": None,
    # "LogLevel": ["QUIET", "FATAL", "ERROR", "INFO", "VERBOSE", "DEBUG", "DEBUG1", "DEBUG2", "DEBUG3"],
    # "LogVerbose": None,
    "MACs": None,
    # "NoHostAuthenticationForLocalhost": ["no", "yes"],
    # "NumberOfPasswordPrompts": None,
    "PasswordAuthentication": ["yes", "no"],
    "PermitLocalCommand": ["no", "yes"],
    # "PermitRemoteOpen": None,
    # "PKCS11Provider": None,
    "Port": None,
    "PreferredAuthentications": None,
    "ProxyCommand": None,
    "ProxyJump": None,
    # "ProxyUseFdpass": ["no", "yes"],
    # "PubkeyAcceptedAlgorithms": None,
    # "PubkeyAuthentication": ["yes", "np", "unbound", "host-bound"],
    # "RekeyLimit": None,
    "RemoteCommand": None,
    "RemoteForward": None,
    "RequestTTY": ["no", "yes", "force", "auto"],
    # "RevokedHostKeys": None,
    # "SecurityKeyProvider": None,
    # "SendEnv": None,
    "ServerAliveCountMax": None,
    "ServerAliveInterval": None,
    # "SessionType": None,
    # "SetEnv": None,
    # "StdinNull": ["no", "yes"]
    # "StreamLocalBindMask": None,
    # "StreamLocalBindUnlink": ["no", "yes"]
    "StrictHostKeyChecking": ["ask", "yes", "accept-new", "no", "off"],
    # "SyslogFacility": ["DAEMON", "USER", "AUTH", "LOCAL0", "LOCAL1", "LOCAL2", "LOCAL3", "LOCAL4", "LOCAL5", "LOCAL6", "LOCAL7"],
    "TCPKeepAlive": ["yes", "no"],
    # "Tunnel": ["no", "yes", "point-to-point", "ethernet"],
    # "TunnelDevice": None,
    "UpdateHostKeys": ["yes", "no", "ask"],
    "User": None,
    "UserKnownHostsFile": None,
    # "VerifyHostKeyDNS": None,
    # "VisualHostKey": ["no", "yes"]
    # "XAuthLocation": None,
}

ALL_PARAM_LC_NAMES = [x.lower() for x in ALL_PARAMS.keys()]


# Update this as needed
PARAMS_WITH_ALLOWED_MULTIPLE_VALUES = [
    "localforward",
    "remoteforward",
    "dynamicforward",
]

