from textwrap import dedent

from sshclick.core import SSH_Config


def test_parse_top_level_include_merges_groups_and_tracks_sources(tmp_path):
    included_config = tmp_path / "included.conf"
    included_config.write_text(
        dedent("""
            #@group: test
            #@desc: shared group
            #@host: from included file
            Host included-host
                hostname 10.10.10.10
        """).strip(),
        encoding="utf-8",
    )

    main_config = tmp_path / "main.conf"
    main_config.write_text(
        dedent(f"""
            Include {included_config.name}

            #@group: test
            #@desc: shared group
            #@host: from main file
            Host main-host
                hostname 20.20.20.20
        """).strip(),
        encoding="utf-8",
    )

    config = SSH_Config(str(main_config)).read().parse()
    group = config.get_group_by_name("test")
    included_host = config.get_host_by_name("included-host")
    main_host = config.get_host_by_name("main-host")

    assert config.write_locked is True
    assert config.included_files == [str(included_config.resolve())]
    assert [host.name for host in group.hosts] == ["included-host", "main-host"]
    assert group.source_refs == [
        (str(included_config.resolve()), 1),
        (str(main_config.resolve()), 3),
    ]
    assert included_host.source_file == str(included_config.resolve())
    assert included_host.source_line == 4
    assert main_host.source_file == str(main_config.resolve())
    assert main_host.source_line == 6


def test_generate_ssh_config_stays_read_only_when_include_is_used(tmp_path):
    included_config = tmp_path / "included.conf"
    included_config.write_text("Host included-host\n    hostname 10.10.10.10\n", encoding="utf-8")

    main_config = tmp_path / "main.conf"
    initial_content = f"Include {included_config.name}\n"
    main_config.write_text(initial_content, encoding="utf-8")

    config = SSH_Config(str(main_config)).read().parse()

    assert config.generate_ssh_config() is False
    assert main_config.read_text(encoding="utf-8") == initial_content


def test_include_inside_host_block_is_not_expanded(tmp_path):
    included_config = tmp_path / "included.conf"
    included_config.write_text("Host included-host\n    hostname 10.10.10.10\n", encoding="utf-8")

    main_config = tmp_path / "main.conf"
    main_config.write_text(dedent(f"""
        Host main-host
            hostname 20.20.20.20
        Include {included_config.name}
    """).strip(), encoding="utf-8")

    config = SSH_Config(str(main_config)).read().parse()

    assert config.write_locked is True
    assert config.check_host_by_name("main-host") is True
    assert config.check_host_by_name("included-host") is False
