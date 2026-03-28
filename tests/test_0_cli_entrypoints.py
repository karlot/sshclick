from pathlib import Path

from click.testing import CliRunner

from sshclick import main_cli, main_tui


EXAMPLE_CONFIG = Path(__file__).resolve().parent.parent / "example" / "config_sample"


def test_sshc_help_mentions_sshc_config():
    result = CliRunner().invoke(main_cli.cli, ["--help"])

    assert result.exit_code == 0
    assert "SSHC_CONFIG" in result.output


def test_sshc_hosts_uses_sshc_config_envvar():
    result = CliRunner().invoke(main_cli.cli, ["hosts"], env={"SSHC_CONFIG": str(EXAMPLE_CONFIG)})

    assert result.exit_code == 0
    assert "lab-serv1" in result.output


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

    result = CliRunner().invoke(main_tui.tui, ["--config", str(EXAMPLE_CONFIG)])

    assert result.exit_code == 0
    assert captured["config_file"] == str(EXAMPLE_CONFIG)
    assert captured["run_called"] is True


def test_ssht_uses_sshc_config_envvar(monkeypatch):
    captured = {}

    class DummyTUI:
        def __init__(self, config_file: str):
            captured["config_file"] = config_file

        def run(self):
            captured["run_called"] = True

    monkeypatch.setattr(main_tui, "SSHTui", DummyTUI)

    result = CliRunner().invoke(main_tui.tui, [], env={"SSHC_CONFIG": str(EXAMPLE_CONFIG)})

    assert result.exit_code == 0
    assert captured["config_file"] == str(EXAMPLE_CONFIG)
    assert captured["run_called"] is True
