from pathlib import Path


IDENTITY_FILE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
IGNORED_IDENTITY_NAMES = {"authorized_keys", "config", "known_hosts", "known_hosts.old"}


def discover_identity_files(config_file: str | None) -> list[tuple[str, str]]:
    """Return likely SSH identity files near the active config file."""

    if not config_file:
        return []

    config_dir = Path(config_file).expanduser().resolve().parent
    if not config_dir.exists():
        return []

    options: list[tuple[str, str]] = []
    seen_values: set[str] = set()

    for path in sorted(config_dir.rglob("*")):
        if not path.is_file() or path.name in IGNORED_IDENTITY_NAMES or path.suffix == ".pub":
            continue
        if not _looks_like_identity_file(path):
            continue

        value = _config_identity_value(path, config_dir)
        if value in seen_values:
            continue

        seen_values.add(value)
        options.append((_display_identity_label(path, config_dir), value))

    return options


def _looks_like_identity_file(path: Path) -> bool:
    """Filter directory contents down to likely private key files."""

    return path.name.startswith("id_") or path.suffix.lower() in IDENTITY_FILE_SUFFIXES


def _display_identity_label(path: Path, config_dir: Path) -> str:
    """Show identity file paths relative to the main config directory when possible."""

    try:
        return path.relative_to(config_dir).as_posix()
    except ValueError:
        return path.as_posix()


def _config_identity_value(path: Path, config_dir: Path) -> str:
    """Render a config-friendly identity path value."""

    try:
        home_relative = path.resolve().relative_to(Path.home())
    except ValueError:
        home_relative = None

    if home_relative is not None:
        return f"~/{home_relative.as_posix()}"

    try:
        return path.relative_to(config_dir).as_posix()
    except ValueError:
        return path.as_posix()
