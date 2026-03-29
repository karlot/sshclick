import asyncio
import shutil
from types import SimpleNamespace
from textwrap import dedent

from textual.widgets import OptionList, Static, TabbedContent

from sshclick.core import SSH_Host
from sshclick.tui.sshtui import SSHTui

from .tui_support import TEST_CONFIG


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


def test_sshtui_left_and_right_expand_and_collapse_selected_group():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            network_group = next(node for node in tree.root.children if node.label.plain == "network")
            assert network_group.is_expanded is False

            for key in ["down", "down"]:
                await pilot.press(key)
                await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "network"

            await pilot.press("right")
            await pilot.pause()
            assert network_group.is_expanded is True

            await pilot.press("left")
            await pilot.pause()
            assert network_group.is_expanded is False

            assert app.focused.id == "sshtree"

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


def test_sshtui_left_click_on_group_only_selects_it():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            network_group = next(node for node in tree.root.children if node.label.plain == "network")
            label_region = tree._get_label_region(network_group._line)

            assert label_region is not None
            assert network_group.is_expanded is False

            await pilot.click("#sshtree", offset=(label_region.x + 2, label_region.y), button=1)
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "network"
            assert network_group.is_expanded is False
            assert len(app.screen_stack) == 1

    asyncio.run(scenario())


def test_sshtui_right_click_on_group_opens_action_menu_without_expanding():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            network_group = next(node for node in tree.root.children if node.label.plain == "network")
            label_region = tree._get_label_region(network_group._line)

            assert label_region is not None
            assert network_group.is_expanded is False

            await pilot.click("#sshtree", offset=(label_region.x + 2, label_region.y), button=3)
            await pilot.pause()

            action_screen = app.screen_stack[-1]
            assert type(action_screen).__name__ == "ActionMenuScreen"
            assert app.current_node is not None
            assert app.current_node.name == "network"
            assert network_group.is_expanded is False
            assert "network" in str(action_screen.query_one("#action_menu_context", Static).render())

    asyncio.run(scenario())


def test_sshtui_left_click_on_host_only_selects_it():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            lab_group = next(node for node in tree.root.children if node.label.plain == "lab-servers")
            lab_group.expand()
            await pilot.pause()

            lab_serv1 = next(node for node in lab_group.children if node.label.plain == "lab-serv1")
            label_region = tree._get_label_region(lab_serv1._line)

            assert label_region is not None

            await pilot.click("#sshtree", offset=(label_region.x + 2, label_region.y), button=1)
            await pilot.pause()

            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"
            assert len(app.screen_stack) == 1

    asyncio.run(scenario())


def test_sshtui_right_click_on_host_opens_action_menu():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            tree = app.query_one("#sshtree")
            lab_group = next(node for node in tree.root.children if node.label.plain == "lab-servers")
            lab_group.expand()
            await pilot.pause()

            lab_serv1 = next(node for node in lab_group.children if node.label.plain == "lab-serv1")
            label_region = tree._get_label_region(lab_serv1._line)

            assert label_region is not None

            await pilot.click("#sshtree", offset=(label_region.x + 2, label_region.y), button=3)
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


def test_sshtui_edit_shortcut_opens_host_editor():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down"]:
                await pilot.press(key)
                await pilot.pause()

            await pilot.press("e")
            await pilot.pause()

            edit_screen = app.screen_stack[-1]
            assert type(edit_screen).__name__ == "ManageHostScreen"
            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"

    asyncio.run(scenario())


def test_sshtui_edit_shortcut_opens_group_editor():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down"]:
                await pilot.press(key)
                await pilot.pause()

            await pilot.press("e")
            await pilot.pause()

            edit_screen = app.screen_stack[-1]
            assert type(edit_screen).__name__ == "ManageGroupScreen"
            assert app.current_node is not None
            assert app.current_node.name == "network"

    asyncio.run(scenario())


def test_sshtui_left_and_right_switch_host_detail_tabs_from_tree_focus():
    async def scenario():
        app = SSHTui(config_file=str(TEST_CONFIG))
        async with app.run_test() as pilot:
            await pilot.pause()

            for key in ["down", "down", "down", "down", "space", "down"]:
                await pilot.press(key)
                await pilot.pause()

            tabs = app.query_one("#host_tabs", TabbedContent)
            assert tabs.active == "host_overview_tab"

            await pilot.press("right")
            await pilot.pause()
            assert tabs.active == "host_connectivity_tab"

            await pilot.press("left")
            await pilot.pause()
            assert tabs.active == "host_overview_tab"

            assert app.focused.id == "sshtree"
            assert app.current_node is not None
            assert app.current_node.name == "lab-serv1"

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
