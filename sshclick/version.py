from importlib.metadata import version, PackageNotFoundError

try:
    VERSION = version("sshclick")
except PackageNotFoundError:
    # Handle the case where the package isn't installed (e.g., local dev)
    VERSION = "0.0.0-dev"

# VERSION = "0.8.0a"