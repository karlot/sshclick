from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# Parsing single host
#------------------------------------------------------------------------------
config1="""
Host test
"""

def test_parse_host():
    lines = config1.splitlines()
    config = SSH_Config("none", lines).parse().groups

    assert config == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test", group="default")
        ])
    ]


#------------------------------------------------------------------------------
# Parsing host with parameters
#------------------------------------------------------------------------------
config2="""
Host test
    hostname 1.2.3.4
    port 2222
    user testuser
"""

def test_parse_host_with_params():
    lines = config2.splitlines()
    config = SSH_Config("none", lines).parse().groups

    assert config == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test", group="default", params={
                "hostname":"1.2.3.4",
                "port":"2222",
                "user":"testuser",
            })
        ])
    ]


#------------------------------------------------------------------------------
# Parsing host with information detail
#------------------------------------------------------------------------------
config3="""
#@host: testinfo
Host test
"""

def test_parse_host_with_info():
    lines = config3.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test", group="default", info=["testinfo"])
        ])
    ]


#------------------------------------------------------------------------------
# Parsing host with information detail, and parameters
#------------------------------------------------------------------------------
config4="""
#@host: testinfo
Host test
    hostname 1.2.3.4
    port 2222
    user testuser
"""

def test_parse_host_with_info_and_params():
    lines = config4.splitlines()
    groups = SSH_Config("none", lines).parse().groups
    
    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test", group="default", info=["testinfo"], params={
                "hostname":"1.2.3.4",
                "port":"2222",
                "user":"testuser",
            })
        ])
    ]
