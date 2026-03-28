from pathlib import Path
from types import SimpleNamespace

from sshclick.sshc import HostType, SSH_Host
from sshclick.ssht.sshtui import SSHTui
from sshclick.ssht.utils.commands import copy_ssh_keys, reset_fingerprint, run_connect

TEST_CONFIG = Path(__file__).resolve().parent / "config_example"


class DummyTUI:
    def __init__(self):
        self.notifications = []

    def notify(self, message, title=None, severity=None):
        self.notifications.append({"message": message, "title": title, "severity": severity})


def test_run_connect_builds_expected_argv(monkeypatch):
    tui = DummyTUI()
    host = SSH_Host(name="demo", group="default")
    captured = {}

    def fake_run_interactive_command(argv, tui=None):
        captured["argv"] = argv
        captured["tui"] = tui
        return 0

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_interactive_command", fake_run_interactive_command)

    run_connect(tui, "ssh", host)

    assert captured["argv"] == ["ssh", "-o", "ConnectTimeout=3", "demo"]
    assert captured["tui"] is tui
    assert tui.notifications == []


def test_run_connect_reports_missing_program(monkeypatch):
    tui = DummyTUI()
    host = SSH_Host(name="demo", group="default")

    def fake_run_interactive_command(argv, tui=None):
        raise FileNotFoundError

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_interactive_command", fake_run_interactive_command)

    run_connect(tui, "ssh", host)

    assert tui.notifications == [{"message": "'ssh' command not found", "title": "demo", "severity": "error"}]


def test_run_connect_reports_non_zero_exit(monkeypatch):
    tui = DummyTUI()
    host = SSH_Host(name="demo", group="default")

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_interactive_command", lambda argv, tui=None: 255)

    run_connect(tui, "ssh", host)

    assert tui.notifications == [{"message": "ssh exited with code 255", "title": "demo", "severity": "error"}]


def test_reset_fingerprint_uses_hostname_param(monkeypatch):
    tui = DummyTUI()
    host = SSH_Host(name="demo", group="default", params={"hostname": "10.1.1.20"})
    captured = {}

    class DummyResult:
        returncode = 0
        stderr = ""

    def fake_run_captured_command(argv):
        captured["argv"] = argv
        return DummyResult()

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_captured_command", fake_run_captured_command)

    reset_fingerprint(tui, host)

    assert captured["argv"] == ["ssh-keygen", "-R", "10.1.1.20"]
    assert tui.notifications == []


def test_copy_ssh_keys_uses_user_and_hostname(monkeypatch):
    tui = DummyTUI()
    host = SSH_Host(name="demo", group="default", params={"user": "admin", "hostname": "10.1.1.20"})
    captured = {}

    def fake_run_interactive_command(argv, tui=None):
        captured["argv"] = argv
        captured["tui"] = tui
        return 0

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_interactive_command", fake_run_interactive_command)

    copy_ssh_keys(tui, host)

    assert captured["argv"] == ["ssh-copy-id", "admin@10.1.1.20"]
    assert captured["tui"] is tui
    assert tui.notifications == []


def test_tui_commands_ignore_non_normal_hosts(monkeypatch):
    tui = DummyTUI()
    pattern = SSH_Host(name="demo-*", group="default", type=HostType.PATTERN)

    monkeypatch.setattr("sshclick.ssht.utils.commands.run_interactive_command", lambda argv, tui=None: (_ for _ in ()).throw(AssertionError("should not run")))
    monkeypatch.setattr("sshclick.ssht.utils.commands.run_captured_command", lambda argv: (_ for _ in ()).throw(AssertionError("should not run")))

    run_connect(tui, "ssh", pattern)
    reset_fingerprint(tui, pattern)
    copy_ssh_keys(tui, pattern)

    assert tui.notifications == []


def test_sshtui_highlight_ignores_missing_data_view(monkeypatch):
    app = SSHTui(config_file=str(TEST_CONFIG))
    host = SSH_Host(name="demo", group="default")

    monkeypatch.setattr(app, "query_one_optional", lambda selector: None)

    app.on_tree_node_highlighted(SimpleNamespace(node=SimpleNamespace(data=host)))

    assert app.current_node is host
