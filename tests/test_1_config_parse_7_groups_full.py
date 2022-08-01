from lib.sshutils import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# Test parsing groups with group metadata (desc and multi-info)
# And nested hosts with parameters
#------------------------------------------------------------------------------
config1 = """
#-----------------------
#@group: testgroup-1
#@desc: this is description 1
#@info: info line 1-1
#@info: info line 1-2
#-----------------------
#@host: hostinfo1
Host test1
    hostname 1.2.3.4
    port 1111
    user test1234

#-----------------------
#@group: testgroup-2
#@desc: this is description 2
#@info: info line 2-1
#@info: info line 2-2
#-----------------------
#@host: hostinfo2
Host test2
    hostname 4.3.2.1
    port 2222
    user test4321
"""

def test_parse_groups_with_hosts():
    lines = config1.splitlines()
    config = SSH_Config("none", lines).parse().groups

    assert config == [
        SSH_Group(name="default"),
        SSH_Group(name="testgroup-1", desc="this is description 1", info=["info line 1-1", "info line 1-2"], hosts=[
            SSH_Host(name="test1", group="testgroup-1", info=["hostinfo1"], params={
                "hostname":"1.2.3.4",
                "port":"1111",
                "user":"test1234",
            }),
        ]),
        SSH_Group(name="testgroup-2", desc="this is description 2", info=["info line 2-1", "info line 2-2"], hosts=[
            SSH_Host(name="test2", group="testgroup-2", info=["hostinfo2"], params={
                "hostname":"4.3.2.1",
                "port":"2222",
                "user":"test4321",
            }),
        ]),
    ], "All group metadata should be parsed correctly, and hosts within groups with parameters"

#------------------------------------------------------------------------------
# Test parsing groups with metadata (desc and multi-info)
# And nested hosts with parameters, host information, and pattern
#------------------------------------------------------------------------------
config2 = """
#@host: some-host-info
Host defaulthost
    hostname 2.2.3.3

#-----------------------
#@group: testgroup-1
#@desc: this is description 1
#@info: info line 1-1
#@info: info line 1-2
#-----------------------
#@host: hostinfo1-application
Host test1-app
    hostname 1.2.3.4

#@host: hostinfo1-database
Host test1-data
    hostname 2.4.6.8

#@host: common params for test-1
Host test1-*
    port 1111
    user test1234
 
#-----------------------
#@group: testgroup-2
#@desc: this is description 2
#@info: info line 2-1
#@info: info line 2-2
#-----------------------
#@host: hostinfo2
Host test2
    hostname 4.3.2.1
    port 2222
    user test4321
"""

def test_parse_groups_with_hosts_full():
    lines = config2.splitlines()
    groups = SSH_Config("none", lines).parse().groups

    assert groups == [
        SSH_Group(name="default", hosts=[
            SSH_Host(name="defaulthost", group="default", info=["some-host-info"], params={
                "hostname":"2.2.3.3",
            }),
        ]),
        SSH_Group(name="testgroup-1", desc="this is description 1", info=["info line 1-1", "info line 1-2"], hosts=[
            SSH_Host(name="test1-app", group="testgroup-1", info=["hostinfo1-application"], params={
                "hostname":"1.2.3.4",
            }),
            SSH_Host(name="test1-data", group="testgroup-1", info=["hostinfo1-database"], params={
                "hostname":"2.4.6.8",
            }),
        ], patterns=[
            SSH_Host(name="test1-*", type="pattern", group="testgroup-1", info=["common params for test-1"], params={
                "port":"1111",
                "user":"test1234",
            }),
        ]),
        SSH_Group(name="testgroup-2", desc="this is description 2", info=["info line 2-1", "info line 2-2"], hosts=[
            SSH_Host(name="test2", group="testgroup-2", info=["hostinfo2"], params={
                "hostname":"4.3.2.1",
                "port":"2222",
                "user":"test4321",
            }),
        ]),
    ], "All groups metadata should be parsed correctly, and all hosts within groups with their parameters"


