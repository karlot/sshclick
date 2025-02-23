from sshclick.sshc import SSH_Config, SSH_Group

#-----------------------------------
# FILE CONTENT SAMPLES FOR PARSING
#-----------------------------------
# Various of config that should produce "empty config"
config1=""
config2="""
#<<<<< SSH Config file managed by sshclick >>>>>
# something something
# something lalalala...

# comment after empty line
"""

# Expected empty result after parsing (containing single default SSH group)
result_empty = [SSH_Group(name='default', desc="Default group")]

#-----------------------------------
# Tests
#-----------------------------------
def test_parse_empty():
    lines = config1.splitlines()
    cfg = SSH_Config("none", lines).parse()
    assert cfg.groups == result_empty
    assert cfg.all_hosts == []

def test_parse_only_comments():
    lines = config2.splitlines()
    cfg = SSH_Config("none", lines).parse()
    assert cfg.groups == result_empty
    assert cfg.all_hosts == []
