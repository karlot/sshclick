from pathlib import Path

import pytest
from click.testing import CliRunner

from sshclick import main_cli
from sshclick.core import SSH_Config


TEST_CONFIG = Path(__file__).resolve().parent / "config_example"


class TestDryRunHostOperations:
    """Test dry-run mode for host-related write operations."""

    def test_dryrun_host_create_does_not_modify_config(self, tmp_path):
        """--dry-run with host create should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = "Host existing-host\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "host", "create",
                "-a", "192.168.1.1",
                "-u", "testuser",
                "new-host"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+Host new-host" in result.output
        assert "Created host:" not in result.output

    def test_diff_option_alias_works_same_as_dryrun(self, tmp_path):
        """--diff should work as alias for --dry-run."""
        config_path = tmp_path / "config"
        config_content = "Host existing-host\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--diff",
                "host", "create",
                "-a", "192.168.1.1",
                "new-host"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+Host new-host" in result.output

    def test_dryrun_host_delete_does_not_modify_config(self, tmp_path):
        """--dry-run with host delete should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = "Host host-to-delete\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "host", "delete",
                "host-to-delete"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-Host host-to-delete" in result.output
        assert "Deleted hosts:" not in result.output

    def test_dryrun_host_rename_does_not_modify_config(self, tmp_path):
        """--dry-run with host rename should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = "Host old-name\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "host", "rename",
                "old-name", "new-name"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-Host old-name" in result.output
        assert "+Host new-name" in result.output
        assert "Renamed host:" not in result.output

    def test_dryrun_host_set_does_not_modify_config(self, tmp_path):
        """--dry-run with host set should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = "Host test-host\n    hostname 10.0.0.1\n    user olduser\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "host", "set",
                "-p", "user", "newuser",
                "test-host"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-    user olduser" in result.output
        assert "+    user newuser" in result.output
        assert "Modified host:" not in result.output

    def test_dryrun_host_delete_skips_confirmation(self, tmp_path):
        """--dry-run should skip confirmation dialog for host delete."""
        config_path = tmp_path / "config"
        config_content = "Host host1\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "host", "delete",
                "host1"
            ],
            input="n\n"
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "Are you sure?" not in result.output


class TestDryRunGroupOperations:
    """Test dry-run mode for group-related write operations."""

    def test_dryrun_group_create_does_not_modify_config(self, tmp_path):
        """--dry-run with group create should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = "Host existing-host\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "group", "create",
                "-d", "Test description",
                "new-group"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+#@group: new-group" in result.output
        assert "Created group:" not in result.output

    def test_dryrun_group_delete_does_not_modify_config(self, tmp_path):
        """--dry-run with group delete should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = (
            "#@group: group-to-delete\n"
            "#@desc: Test group\n"
            "Host test-host\n    hostname 10.0.0.1\n"
        )
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "group", "delete",
                "group-to-delete"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-#@group: group-to-delete" in result.output
        assert "Deleted group:" not in result.output

    def test_dryrun_group_rename_does_not_modify_config(self, tmp_path):
        """--dry-run with group rename should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = (
            "#@group: old-group\n"
            "Host test-host\n    hostname 10.0.0.1\n"
        )
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "group", "rename",
                "old-group", "new-group"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-#@group: old-group" in result.output
        assert "+#@group: new-group" in result.output
        assert "Renamed group:" not in result.output

    def test_dryrun_group_set_does_not_modify_config(self, tmp_path):
        """--dry-run with group set should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = (
            "#@group: test-group\n"
            "#@desc: Old description\n"
            "Host test-host\n    hostname 10.0.0.1\n"
        )
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "group", "set",
                "-d", "New description",
                "test-group"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-#@desc: Old description" in result.output
        assert "+#@desc: New description" in result.output
        assert "Modified group:" not in result.output


class TestDryRunConfigOperations:
    """Test dry-run mode for config-related write operations."""

    def test_dryrun_config_set_does_not_modify_config(self, tmp_path):
        """--dry-run with config set should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = ""
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "config", "set",
                "--host-style", "simple"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+#@config: host-style=simple" in result.output
        assert "Set config:" not in result.output

    def test_dryrun_config_del_does_not_modify_config(self, tmp_path):
        """--dry-run with config del should show diff but not modify config."""
        config_path = tmp_path / "config"
        config_content = (
            "#<<<<< SSH Config file managed by sshclick >>>>>\n"
            "#@config: host-style=simple\n"
        )
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "--dry-run",
                "config", "del",
                "--host-style"
            ]
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "-#@config: host-style=simple" in result.output
        assert "Deleted config:" not in result.output


class TestDryRunEnvironmentVariables:
    """Test dry-run mode via environment variables."""

    def test_sshc_dryrun_envvar_enables_dryrun(self, tmp_path):
        """SSHC_DRYRUN environment variable should enable dry-run mode."""
        config_path = tmp_path / "config"
        config_content = "Host existing-host\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "host", "create",
                "-a", "192.168.1.1",
                "new-host"
            ],
            env={"SSHC_DRYRUN": "1"}
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+Host new-host" in result.output

    def test_sshc_diff_envvar_enables_dryrun(self, tmp_path):
        """SSHC_DIFF environment variable should enable dry-run mode (backward compatible)."""
        config_path = tmp_path / "config"
        config_content = "Host existing-host\n    hostname 10.0.0.1\n"
        config_path.write_text(config_content, encoding="utf-8")
        original_content = config_path.read_text(encoding="utf-8")

        result = CliRunner().invoke(
            main_cli.cli,
            [
                "--config", str(config_path),
                "host", "create",
                "-a", "192.168.1.1",
                "new-host"
            ],
            env={"SSHC_DIFF": "1"}
        )

        assert result.exit_code == 0
        assert config_path.read_text(encoding="utf-8") == original_content
        assert "+Host new-host" in result.output


class TestDryRunHelpText:
    """Test that help text mentions dry-run options."""

    def test_help_mentions_dry_run(self):
        """Main help should mention --dry-run option."""
        result = CliRunner().invoke(main_cli.cli, ["--help"])

        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--dryrun" in result.output
        assert "--diff" in result.output
