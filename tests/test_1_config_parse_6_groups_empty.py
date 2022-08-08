from sshclick.sshc import SSH_Config, SSH_Group

#------------------------------------------------------------------------------
# Test parsing groups
#------------------------------------------------------------------------------
config1="""
#-----------------------
#@group: testgroup-1
#-----------------------

#-----------------------
#@group: testgroup-2
#-----------------------
"""

def test_parse_groups():
    lines = config1.splitlines()
    config = SSH_Config("none", lines).parse().groups

    assert config == [
        SSH_Group(name="default", desc="Default group"),
        SSH_Group(name="testgroup-1"),
        SSH_Group(name="testgroup-2"),
    ], "All groups should be parsed correctly"


#------------------------------------------------------------------------------
# Test parsing groups with group metadata (desc and multi-info)
#------------------------------------------------------------------------------
config2="""
#-----------------------
#@group: testgroup-1
#@desc: this is description 1
#@info: info line 1-1
#@info: info line 1-2
#-----------------------

#-----------------------
#@group: testgroup-2
#@desc: this is description 2
#@info: info line 2-1
#@info: info line 2-2
#-----------------------
"""

def test_parse_groups_with_meta():
    lines = config2.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group"),
        SSH_Group(name="testgroup-1", desc="this is description 1", info=["info line 1-1", "info line 1-2"]),
        SSH_Group(name="testgroup-2", desc="this is description 2", info=["info line 2-1", "info line 2-2"]),
    ], "All group metadata should be parsed correctly"

