import asyncio
import shutil

from textual.widgets import Input, Label, TextArea

from sshclick.tui.screens import ManageGroupScreen
from sshclick.tui.sshtui import SSHTui

from .tui_support import TEST_CONFIG


def test_manage_group_screen_prefills_existing_group_metadata():
    app = SSHTui(config_file=str(TEST_CONFIG))
    group = app.state.sshconf.get_group_by_name("network")
    screen = ManageGroupScreen(app.state.sshconf, group, editing_group=group)

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            assert "Edit group" in str(screen.query_one("#manage_group_title", Label).render())
            assert screen.query_one("#manage_group_name", Input).value == "network"
            assert screen.query_one("#manage_group_desc", Input).value == "Network devices in the test lab"
            assert screen.query_one("#manage_group_info", TextArea).text == "Group info line for parser and UI tests"

    asyncio.run(scenario())


def test_sshtui_create_group_flow_updates_config_and_selection(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._handle_action_menu_result("act_create_group")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, ManageGroupScreen)

            screen.query_one("#manage_group_name", Input).value = "dmz"
            screen.query_one("#manage_group_desc", Input).value = "External systems"
            screen.query_one("#manage_group_info", TextArea).text = "Created from TUI test\nSecond group line"
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "dmz"
            assert app.state.sshconf.check_group_by_name("dmz") is True

            rendered = config_path.read_text(encoding="utf-8")
            assert "#@group: dmz" in rendered
            assert "#@desc: External systems" in rendered
            assert "#@info: Created from TUI test" in rendered
            assert "#@info: Second group line" in rendered

    asyncio.run(scenario())


def test_sshtui_edit_group_flow_updates_group_metadata_and_host_refs(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._set_current_node(app.state.sshconf.get_group_by_name("lab-servers"))
            app._handle_action_menu_result("act_edit_group")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, ManageGroupScreen)
            assert "Edit group" in str(screen.query_one("#manage_group_title", Label).render())

            screen.query_one("#manage_group_name", Input).value = "dmz"
            screen.query_one("#manage_group_desc", Input).value = "DMZ systems"
            screen.query_one("#manage_group_info", TextArea).text = "Renamed from TUI test\nWith second line"
            screen.submit()
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "dmz"
            assert app.state.sshconf.check_group_by_name("lab-servers") is False
            assert app.state.sshconf.check_group_by_name("dmz") is True
            assert app.state.sshconf.get_host_by_name("lab-serv1").group == "dmz"

            rendered = config_path.read_text(encoding="utf-8")
            assert "#@group: dmz" in rendered
            assert "#@group: lab-servers" not in rendered
            assert "#@desc: DMZ systems" in rendered
            assert "#@info: Renamed from TUI test" in rendered
            assert "#@info: With second line" in rendered

    asyncio.run(scenario())
