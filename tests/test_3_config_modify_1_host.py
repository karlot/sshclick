from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#------------------------------------------------------------------------------
# Test parsing configuration and add new host then verify rendering output is
# modified as expected - on empty config
#------------------------------------------------------------------------------
config1_modified_lines=[
    "#<<<<< SSH Config file managed by sshclick >>>>>",
    "",
    "#@host: some-host-info",
    "Host testnew",
    "    hostname 2.2.3.3",
    "",
]

def test_add_new_host():
    config = SSH_Config("none", [])     # Start with empty configuration
    config.parse()

    new_host = SSH_Host(name="testnew", info=["some-host-info"], group="default", params={"hostname": "2.2.3.3"})
    assert config.add_host(new_host)

    found_host = config.get_host_by_name("testnew")
    found_group = config.get_group_by_name(found_host.group)

    assert found_host == new_host
    assert found_group == SSH_Group(name="default", desc="Default group", hosts=[new_host])

    config.generate_ssh_config()
    print(config.ssh_config_lines)
    assert config.ssh_config_lines == config1_modified_lines


#------------------------------------------------------------------------------
# Test parsing configuration and add new host then verify rendering output is
# modified as expected - on existing config
#------------------------------------------------------------------------------

config2="""
#@host: some-default-info
Host defaulthost
    hostname 2.2.3.3

#-----------------------
#@group: testgroup
#@desc: this is description
#-----------------------
#@host: test-old host info
Host test-old
    hostname 4.3.2.1
    port 2222
    user test4321
"""

config2_modified_lines=[
    "#<<<<< SSH Config file managed by sshclick >>>>>",
    "",
    "#@host: some-default-info",
    "Host defaulthost",
    "    hostname 2.2.3.3",
    "",
    "",
    "#-------------------------------------------------------------------------------",
    "#@group: testgroup",
    "#@desc: this is description",
    "#-------------------------------------------------------------------------------",
    "#@host: test-old host info",
    "Host test-old",
    "    hostname 4.3.2.1",
    "    port 2222",
    "    user test4321",
    "",
    "#@host: this is a new host",
    "Host test-new",
    "    hostname 1.1.1.1",
    "",
    "Host test-*",
    "    user test4321",
    "",
]

def test_add_new_host_complex():
    config = SSH_Config("none", config2.splitlines())
    config.parse()

    new_host = SSH_Host(name="test-new", info=["this is a new host"], group="testgroup", params={"hostname": "1.1.1.1"})
    new_pattern = SSH_Host(name="test-*", group="testgroup", params={"user": "test4321"})

    assert config.add_host(new_host)
    assert config.add_host(new_pattern)

    config.generate_ssh_config()
    assert config.ssh_config_lines == config2_modified_lines
