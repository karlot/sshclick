import asyncio
import shutil
from pathlib import Path
from types import SimpleNamespace
from textwrap import dedent

from textual.widgets import Input, Label, OptionList, Select, Static, Switch

from sshclick.core import HostType, SSH_Host
from sshclick.ssht.sshtui import SSHTui
from sshclick.ssht.screens import AddParameterScreen, CreateHostScreen, HostParameterRequest
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


def test_sshtui_enter_on_group_toggles_expand_without_opening_actions():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            network_group = next(node for node in tree.root.children if node.label.plain == "network")
            assert network_group.label.plain == "network"
            assert network_group.is_expanded is False

            for key in ["down", "down", "enter"]:
                await pilot.press(key)
                await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "network"
            assert network_group.is_expanded is True
            assert len(app.screen_stack) == 1

    asyncio.run(scenario())


def test_sshtui_enter_on_host_opens_action_menu():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down", "enter"]:
                await pilot.press(key)
                await pilot.pause()

            action_screen = app.screen_stack[-1]
            assert type(action_screen).__name__ == "ActionMenuScreen"
            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"
            assert "lab-serv1" in str(action_screen.query_one("#action_menu_context", Static).render())

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


def test_sshtui_delete_host_preserves_expanded_groups_and_selects_parent_group(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            groups = {node.label.plain: node for node in tree.root.children}
            groups["network"].expand()
            groups["lab-servers"].expand()
            await pilot.pause()

            app._set_current_node(app.state.sshconf.get_host_by_name("lab-serv1"))
            app._delete_confirmed(True)
            await pilot.pause()

            tree = app.query_one("#sshtree")
            groups = {node.label.plain: node for node in tree.root.children}

            assert groups["network"].is_expanded is True
            assert groups["lab-servers"].is_expanded is True
            assert app.current_node is not None
            assert app.current_node.name == "lab-servers"
            assert str(app.query_one("#details_header", Label).render()) == "Group: lab-servers"
            assert "Host lab-serv1" not in config_path.read_text(encoding="utf-8")

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


def test_create_host_screen_prefills_group_from_current_group():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = CreateHostScreen(app.state.sshconf, app.state.sshconf.get_group_by_name("lab-servers"))

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            assert screen.query_one("#create_host_group_select", Select).value == "lab-servers"
            assert screen.query_one("#create_host_create_group", Switch).value is False
            assert "Detected type: Host" in str(screen.query_one("#create_host_detected_type", Label).render())

    asyncio.run(scenario())


def test_create_host_screen_detects_pattern_type_from_name():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = CreateHostScreen(app.state.sshconf, None)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            screen.query_one("#create_host_name", Input).value = "lab-*"
            await pilot.pause()

            assert "Detected type: Pattern" in str(screen.query_one("#create_host_detected_type", Label).render())

    asyncio.run(scenario())


def test_add_parameter_screen_uses_choice_select_for_known_values():
    results = []

    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        screen = AddParameterScreen()

        async with app.run_test() as pilot:
            app.push_screen(screen, results.append)
            await pilot.pause()

            screen.query_one("#add_param_name", Select).value = "PasswordAuthentication"
            await pilot.pause()

            assert screen.query_one("#add_param_value_mode").current == "add_param_value_select_mode"

            screen.query_one("#add_param_value_select", Select).value = "yes"
            screen.submit()
            await pilot.pause()

        assert results == [HostParameterRequest(name="PasswordAuthentication", value="yes")]

    asyncio.run(scenario())


def test_add_parameter_screen_shows_description_for_selected_parameter():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        screen = AddParameterScreen()

        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            screen.query_one("#add_param_name", Select).value = "ProxyJump"
            await pilot.pause()

            description = str(screen.query_one("#add_param_description", Static).render())
            assert "jump hosts" in description

    asyncio.run(scenario())


def test_add_parameter_screen_filters_out_fixed_create_host_fields():
    screen = AddParameterScreen(excluded_params={"hostname", "port", "user", "identityfile"})
    options = screen._parameter_options()

    assert ("HostName", "HostName") not in options
    assert ("Port", "Port") not in options
    assert ("User", "User") not in options
    assert ("IdentityFile", "IdentityFile") not in options
    assert ("ProxyJump", "ProxyJump") in options


def test_create_host_screen_can_edit_existing_extra_parameter():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = CreateHostScreen(app.state.sshconf, None)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            screen._handle_parameter_result(HostParameterRequest(name="ProxyJump", value="jumper1"))
            await pilot.pause()

            option_list = screen.query_one("#create_host_extra_params", OptionList)
            option_list.highlighted = 0
            screen.edit_parameter()
            await pilot.pause()

            editor = app.screen_stack[-1]
            assert isinstance(editor, AddParameterScreen)
            assert editor.query_one("#add_param_name", Select).value == "ProxyJump"
            assert "jump hosts" in str(editor.query_one("#add_param_description", Static).render())
            assert editor.query_one("#add_param_value_input", Input).value == "jumper1"

            editor.query_one("#add_param_name", Select).value = "ProxyCommand"
            await pilot.pause()
            editor.query_one("#add_param_value_input", Input).value = "ssh -W %h:%p bastion"
            editor.submit()
            await pilot.pause()

            assert screen.extra_parameters == [("ProxyCommand", "ssh -W %h:%p bastion")]
            assert str(option_list.get_option_at_index(0).prompt) == "ProxyCommand = ssh -W %h:%p bastion"

    asyncio.run(scenario())


def test_sshtui_create_host_flow_updates_config_and_selection(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)
    identity_file = tmp_path / "id_tui_test"
    identity_file.write_text("dummy-key", encoding="utf-8")

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._set_current_node(app.state.sshconf.get_group_by_name("lab-servers"))
            app._handle_action_menu_result("act_create_host")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, CreateHostScreen)

            screen.query_one("#create_host_name", Input).value = "lab-new1"
            screen.query_one("#create_host_address", Input).value = "10.10.0.55"
            screen.query_one("#create_host_port", Input).value = "2222"
            screen.query_one("#create_host_user", Input).value = "deploy"
            screen.query_one("#create_host_group_select", Select).value = "lab-servers"
            screen.query_one("#create_host_identity", Select).value = identity_file.name
            screen.query_one("#create_host_info", Input).value = "Created from TUI test"
            screen._handle_parameter_result(HostParameterRequest(name="ProxyJump", value="jumper1"))
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-new1"
            assert str(app.query_one("#details_header", Label).render()) == "Host: lab-new1"
            rendered = config_path.read_text(encoding="utf-8")
            assert "Host lab-new1" in rendered
            assert "port 2222" in rendered
            assert "user deploy" in rendered
            assert "proxyjump jumper1" in rendered
            assert f"identityfile {identity_file.name}" in rendered

    asyncio.run(scenario())


def test_sshtui_create_host_flow_can_create_new_group(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._handle_action_menu_result("act_create_host")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, CreateHostScreen)

            screen.query_one("#create_host_name", Input).value = "dmz-*"
            screen.query_one("#create_host_create_group", Switch).value = True
            await pilot.pause()
            screen.query_one("#create_host_group_input", Input).value = "dmz"
            screen.query_one("#create_host_user", Input).value = "ops"
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "dmz-*"
            assert app.state.sshconf.check_group_by_name("dmz") is True
            assert "Host dmz-*" in config_path.read_text(encoding="utf-8")

    asyncio.run(scenario())
