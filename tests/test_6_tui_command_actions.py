import asyncio
from pathlib import Path
from types import SimpleNamespace
from textwrap import dedent

from textual.widgets import Label, OptionList, Static

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


def test_sshtui_initial_view_shows_status_and_tree_stats():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            assert app.focused.id == "sshtree"
            assert "config_example" in str(app.query_one("#status_config", Static).render())
            assert "Writable" in str(app.query_one("#status_mode", Static).render())

            stats = str(app.query_one("#tree_stats", Static).render())
            assert "Groups   : 4" in stats
            assert "Hosts    : 5" in stats
            assert "Patterns : 2" in stats
            assert "Includes : 0" in stats

    asyncio.run(scenario())


def test_sshtui_tree_navigation_can_expand_group_and_select_host():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down"]:
                await pilot.press(key)
                await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"
            assert str(app.query_one("#details_header", Label).render()) == "Host: lab-serv1"

    asyncio.run(scenario())


def test_sshtui_action_menu_opens_for_selected_host():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down"]:
                await pilot.press(key)
                await pilot.pause()

            await pilot.press("a")
            await pilot.pause()

            action_screen = app.screen_stack[-1]
            assert type(action_screen).__name__ == "ActionMenuScreen"
            assert "lab-serv1" in str(action_screen.query_one("#action_menu_context", Static).render())
            assert action_screen.query_one("#action_menu_options", OptionList) is not None

    asyncio.run(scenario())


def test_sshtui_reload_preserves_selected_node():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down"]:
                await pilot.press(key)
                await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"

            await pilot.press("r")
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"
            assert str(app.query_one("#details_header", Label).render()) == "Host: lab-serv1"

    asyncio.run(scenario())


def test_sshtui_include_config_shows_read_only_mode(tmp_path):
    included_config = tmp_path / "included.conf"
    included_config.write_text(
        dedent(
            """
            Host included-host
                hostname 10.10.10.10
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    main_config = tmp_path / "main.conf"
    main_config.write_text(
        dedent(
            f"""
            Include {included_config.name}

            Host main-host
                hostname 20.20.20.20
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    async def scenario():
        app = SSHTui(config_file=str(main_config))
        async with app.run_test() as pilot:
            await pilot.pause()

            assert "READ ONLY" in str(app.query_one("#status_mode", Static).render())
            assert "Includes : 1" in str(app.query_one("#tree_stats", Static).render())

    asyncio.run(scenario())
