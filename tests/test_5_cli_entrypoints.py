from pathlib import Path

import pytest
from click.testing import CliRunner

from sshclick import main_cli, main_tui
from sshclick.sshc import build_context_config


TEST_CONFIG = Path(__file__).resolve().parent / "config_example"


def test_sshc_help_mentions_sshc_config():
    result = CliRunner().invoke(main_cli.cli, ["--help"])

    assert result.exit_code == 0
    assert "SSHC_CONFIG" in result.output


def test_sshc_hosts_uses_sshc_config_envvar():
    result = CliRunner().invoke(main_cli.cli, ["hosts"], env={"SSHC_CONFIG": str(TEST_CONFIG)})

    assert result.exit_code == 0
    assert "lab-serv1" in result.output


def test_sshc_config_set_writes_host_style(tmp_path):
    config_path = tmp_path / "config"
    config_path.write_text("", encoding="utf-8")

    result = CliRunner().invoke(main_cli.cli, ["--config", str(config_path), "config", "set", "--host-style", "simple"])

    assert result.exit_code == 0
    assert "#@config: host-style=simple" in config_path.read_text(encoding="utf-8")


def test_sshc_config_del_removes_host_style(tmp_path):
    config_path = tmp_path / "config"
    config_path.write_text("#<<<<< SSH Config file managed by sshclick >>>>>\n#@config: host-style=simple\n", encoding="utf-8")

    result = CliRunner().invoke(main_cli.cli, ["--config", str(config_path), "config", "del", "--host-style"])

    assert result.exit_code == 0
    assert "#@config: host-style=simple" not in config_path.read_text(encoding="utf-8")


def test_ssht_help_mentions_sshc_config():
    result = CliRunner().invoke(main_tui.tui, ["--help"])

    assert result.exit_code == 0
    assert "SSHC_CONFIG" in result.output


def test_ssht_uses_config_option(monkeypatch):
    captured = {}

    class DummyTUI:
        def __init__(self, config_file: str):
            captured["config_file"] = config_file

        def run(self):
            captured["run_called"] = True

    monkeypatch.setattr(main_tui, "SSHTui", DummyTUI)

    result = CliRunner().invoke(main_tui.tui, ["--config", str(TEST_CONFIG)])

    assert result.exit_code == 0
    assert captured["config_file"] == str(TEST_CONFIG)
    assert captured["run_called"] is True


def test_ssht_uses_sshc_config_envvar(monkeypatch):
    captured = {}

    class DummyTUI:
        def __init__(self, config_file: str):
            captured["config_file"] = config_file

        def run(self):
            captured["run_called"] = True

    monkeypatch.setattr(main_tui, "SSHTui", DummyTUI)

    result = CliRunner().invoke(main_tui.tui, [], env={"SSHC_CONFIG": str(TEST_CONFIG)})

    assert result.exit_code == 0
    assert captured["config_file"] == str(TEST_CONFIG)
    assert captured["run_called"] is True


class DummyCtx:
    def __init__(self, parent=None, params=None):
        self.obj = None
        self.parent = parent
        self.params = params or {}

    def exit(self, code):
        raise SystemExit(code)


def test_build_context_config_loads_from_parent_chain():
    root = DummyCtx(params={"config": str(TEST_CONFIG), "stdout": True})
    child = DummyCtx(parent=root)

    build_context_config(child)

    assert child.obj is not None
    assert child.obj.stdout is True
    assert child.obj.check_host_by_name("lab-serv1") is True


def test_build_context_config_exits_when_parent_chain_has_no_config(capsys):
    ctx = DummyCtx(parent=DummyCtx())

    with pytest.raises(SystemExit) as exc:
        build_context_config(ctx)

    assert exc.value.code == 1
    assert "Could not reconstruct context for SSH configuration" in capsys.readouterr().err
