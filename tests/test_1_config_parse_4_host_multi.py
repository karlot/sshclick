from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# Test parsing multiple hosts
#------------------------------------------------------------------------------
config1="""
Host test1
Host test2
"""

def test_parse_single_host():
    lines = config1.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test1", group="default"),
            SSH_Host(name="test2", group="default"),
        ])
    ]


#------------------------------------------------------------------------------
# Test parsing multiple hosts with parameters
#------------------------------------------------------------------------------
config2="""
Host test1
    hostname 1.2.3.4
    port 2222
    user testuser

Host test2
    hostname 2.3.4.5
    port 3333
    user usertest
"""

def test_parse_single_host_with_params():
    lines = config2.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test1", group="default", params={
                "hostname": "1.2.3.4",
                "port": "2222",
                "user": "testuser",
            }),
            SSH_Host(name="test2", group="default", params={
                "hostname": "2.3.4.5",
                "port": "3333",
                "user": "usertest",
            })
        ])
    ]

#------------------------------------------------------------------------------
# Test parsing multiple hosts with host information
#------------------------------------------------------------------------------
config3="""
#@host: testinfo1
Host test1

#@host: testinfo2
Host test2
"""

def test_parse_single_host_with_info():
    lines = config3.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test1", group="default", info=["testinfo1"]),
            SSH_Host(name="test2", group="default", info=["testinfo2"])
        ])
    ]

#------------------------------------------------------------------------------
# test_parse_single_host_with_info_and_params
#------------------------------------------------------------------------------
config4="""
#@host: testinfo1
Host test1
    hostname 1.2.3.4
    port 1111
    user test1234

#@host: testinfo2
Host test2
    hostname 4.3.2.1
    port 2222
    user test4321
"""

def test_parse_single_host_with_info_and_params():
    lines = config4.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", desc="Default group", hosts=[
            SSH_Host(name="test1", group="default", info=["testinfo1"], params={
                "hostname":"1.2.3.4",
                "port":"1111",
                "user":"test1234",
            }),
            SSH_Host(name="test2", group="default", info=["testinfo2"], params={
                "hostname":"4.3.2.1",
                "port":"2222",
                "user":"test4321",
            })
        ])
    ]


