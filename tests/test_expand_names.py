from sshclick.core.ssh_utils import expand_names


def test_expand_names_regex_containing_colon_uses_full_pattern():
    all_names = ["a:b", "axb", "other"]

    assert expand_names(("r:^a:b$",), all_names) == ["a:b"]


def test_expand_names_simple_regex_still_matches_prefix():
    all_names = ["test_one", "test_two", "prod"]

    assert sorted(expand_names(("r:^test_",), all_names)) == ["test_one", "test_two"]


def test_expand_names_direct_names_pass_through():
    all_names = ["alpha", "beta"]

    assert sorted(expand_names(("alpha", "missing"), all_names)) == ["alpha", "missing"]
