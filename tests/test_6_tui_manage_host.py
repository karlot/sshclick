import asyncio
import shutil

from textual.widgets import Input, Label, OptionList, Select, Static, Switch, TextArea

from sshclick.tui.screens import AddParameterScreen, HostParameterRequest, ManageHostScreen
from sshclick.tui.sshtui import SSHTui

from .tui_support import TEST_CONFIG


def test_manage_host_screen_prefills_group_from_current_group():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = ManageHostScreen(app.state.sshconf, app.state.sshconf.get_group_by_name("lab-servers"))

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            assert screen.query_one("#manage_host_group_select", Select).value == "lab-servers"
            assert screen.query_one("#manage_host_create_group", Switch).value is False
            assert "Detected type: Host" in str(screen.query_one("#manage_host_detected_type", Label).render())

    asyncio.run(scenario())


def test_manage_host_screen_detects_pattern_type_from_name():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = ManageHostScreen(app.state.sshconf, None)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            screen.query_one("#manage_host_name", Input).value = "lab-*"
            await pilot.pause()

            assert "Detected type: Pattern" in str(screen.query_one("#manage_host_detected_type", Label).render())

    asyncio.run(scenario())


def test_edit_host_screen_prefills_fixed_and_extra_values():
    app = SSHTui(config_file=str(TEST_CONFIG))
    host = app.state.sshconf.get_host_by_name("server-behind-lab")
    screen = ManageHostScreen(app.state.sshconf, host, editing_host=host)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            assert "Edit SSH entry" in str(screen.query_one("#manage_host_title", Label).render())
            assert screen.query_one("#manage_host_name", Input).value == "server-behind-lab"
            assert screen.query_one("#manage_host_info", TextArea).text == "Multi-hop target with local forwarding"
            assert screen.query_one("#manage_host_address", Input).value == "10.30.0.1"
            assert screen.query_one("#manage_host_port", Input).value == "1234"
            assert screen.query_one("#manage_host_user", Input).value == "testuser"
            assert screen.query_one("#manage_host_group_select", Select).value == "lab-servers"
            assert screen.extra_parameters == [
                ("ProxyJump", "lab-serv1"),
                ("LocalForward", "7630 127.0.0.1:7630"),
            ]

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


def test_add_parameter_screen_filters_out_fixed_manage_host_fields():
    screen = AddParameterScreen(excluded_params={"hostname", "port", "user", "identityfile"})
    options = screen._parameter_options()

    assert ("HostName", "HostName") not in options
    assert ("Port", "Port") not in options
    assert ("User", "User") not in options
    assert ("IdentityFile", "IdentityFile") not in options
    assert ("ProxyJump", "ProxyJump") in options


def test_manage_host_screen_can_edit_existing_extra_parameter():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = ManageHostScreen(app.state.sshconf, None)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            screen._handle_parameter_result(HostParameterRequest(name="ProxyJump", value="jumper1"))
            await pilot.pause()

            option_list = screen.query_one("#manage_host_extra_params", OptionList)
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
            assert isinstance(screen, ManageHostScreen)

            screen.query_one("#manage_host_name", Input).value = "lab-new1"
            screen.query_one("#manage_host_address", Input).value = "10.10.0.55"
            screen.query_one("#manage_host_port", Input).value = "2222"
            screen.query_one("#manage_host_user", Input).value = "deploy"
            screen.query_one("#manage_host_group_select", Select).value = "lab-servers"
            screen.query_one("#manage_host_identity", Select).value = identity_file.name
            screen.query_one("#manage_host_info", TextArea).text = "Created from TUI test\nSecond line"
            screen._handle_parameter_result(HostParameterRequest(name="ProxyJump", value="jumper1"))
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-new1"
            rendered = config_path.read_text(encoding="utf-8")
            assert "Host lab-new1" in rendered
            assert "port 2222" in rendered
            assert "user deploy" in rendered
            assert "proxyjump jumper1" in rendered
            assert "#@host: Created from TUI test" in rendered
            assert "#@host: Second line" in rendered
            assert f"identityfile {identity_file.name}" in rendered

    asyncio.run(scenario())


def test_sshtui_edit_host_flow_updates_config_and_selection(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._set_current_node(app.state.sshconf.get_host_by_name("lab-serv1"))
            app._handle_action_menu_result("act_edit_host")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, ManageHostScreen)
            assert "Edit SSH entry" in str(screen.query_one("#manage_host_title", Label).render())

            screen.query_one("#manage_host_name", Input).value = "lab-admin1"
            screen.query_one("#manage_host_address", Input).value = "10.10.0.55"
            screen.query_one("#manage_host_port", Input).value = "2201"
            screen.query_one("#manage_host_user", Input).value = "deploy"
            screen.query_one("#manage_host_group_select", Select).value = "network"
            screen.query_one("#manage_host_info", TextArea).text = "Edited from TUI test\nWith second line"
            screen._handle_parameter_result(HostParameterRequest(name="ProxyJump", value="jumper1"))
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-admin1"
            assert app.current_node.group == "network"
            assert app.state.sshconf.check_host_by_name("lab-serv1") is False
            assert app.state.sshconf.check_host_by_name("lab-admin1") is True

            rendered = config_path.read_text(encoding="utf-8")
            assert "Host lab-admin1" in rendered
            assert "Host lab-serv1" not in rendered
            assert "hostname 10.10.0.55" in rendered
            assert "port 2201" in rendered
            assert "user deploy" in rendered
            assert "proxyjump jumper1" in rendered
            assert "#@host: Edited from TUI test" in rendered
            assert "#@host: With second line" in rendered

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
            assert isinstance(screen, ManageHostScreen)

            screen.query_one("#manage_host_name", Input).value = "dmz-*"
            screen.query_one("#manage_host_create_group", Switch).value = True
            await pilot.pause()
            screen.query_one("#manage_host_group_input", Input).value = "dmz"
            screen.query_one("#manage_host_user", Input).value = "ops"
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "dmz-*"
            assert app.state.sshconf.check_group_by_name("dmz") is True
            assert "Host dmz-*" in config_path.read_text(encoding="utf-8")

    asyncio.run(scenario())
