import asyncio
import shutil

from textual.widgets import Label, Select

from sshclick.tui.screens import ManageConfigScreen
from sshclick.tui.sshtui import SSHTui

from .tui_support import TEST_CONFIG


def test_manage_config_screen_prefills_current_host_style():
    app = SSHTui(config_file=str(TEST_CONFIG))
    screen = ManageConfigScreen(app.state.sshconf.opts.get("host-style"))

    async def scenario():
        async with app.run_test() as pilot:
            app.push_screen(screen)
            await pilot.pause()

            assert "SSHClick config" in str(screen.query_one("#manage_config_title", Label).render())
            assert screen.query_one("#manage_config_host_style", Select).value == "simple"

    asyncio.run(scenario())


def test_sshtui_edit_config_flow_updates_host_style(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._handle_action_menu_result("act_edit_config")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, ManageConfigScreen)

            screen.query_one("#manage_config_host_style", Select).value = "panels"
            screen.submit()
            await pilot.pause()

            assert app.state.sshconf.opts["host-style"] == "panels"
            rendered = config_path.read_text(encoding="utf-8")
            assert "#@config: host-style=panels" in rendered
            assert "#@config: host-style=simple" not in rendered

    asyncio.run(scenario())


def test_sshtui_edit_config_flow_can_unset_host_style(tmp_path):
    config_path = tmp_path / "config_example"
    shutil.copyfile(TEST_CONFIG, config_path)

    async def scenario():
        app = SSHTui(config_file=str(config_path))
        async with app.run_test() as pilot:
            await pilot.pause()

            app._handle_action_menu_result("act_edit_config")
            await pilot.pause()

            screen = app.screen_stack[-1]
            assert isinstance(screen, ManageConfigScreen)

            screen.query_one("#manage_config_host_style", Select).value = "__default__"
            screen.submit()
            await pilot.pause()

            assert "host-style" not in app.state.sshconf.opts
            rendered = config_path.read_text(encoding="utf-8")
            assert "#@config: host-style=" not in rendered

    asyncio.run(scenario())
