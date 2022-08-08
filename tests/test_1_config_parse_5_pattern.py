from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# Parsing global pattern
#------------------------------------------------------------------------------
config1="""
Host *
"""

def test_parse_glob_pattern():
    lines = config1.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", patterns=[
            SSH_Host(name="*", type="pattern", group="default")
        ])
    ]


#------------------------------------------------------------------------------
# Parsing multiple patterns with info meta
#------------------------------------------------------------------------------
config2="""
#@host: pattern for test1 hosts
Host test1-*
    user test123

#@host: pattern for test2 hosts
Host test2-*
    user test321
"""

def test_parse_multiple_patterns():
    lines = config2.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", patterns=[
            SSH_Host(name="test1-*", type="pattern", group="default", info=["pattern for test1 hosts"], params={
                "user":"test123",
            }),
            SSH_Host(name="test2-*", type="pattern", group="default", info=["pattern for test2 hosts"], params={
                "user":"test321",
            }),
        ])
    ]
