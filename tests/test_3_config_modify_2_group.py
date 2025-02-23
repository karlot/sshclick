from sshclick.sshc import SSH_Config, SSH_Group

#------------------------------------------------------------------------------
# Test parsing configuration and add new group then verify rendering output is
# modified as expected - on empty config
#------------------------------------------------------------------------------
config1=""
config1_modified_lines=[
    "#<<<<< SSH Config file managed by sshclick >>>>>",
    "",
    "",
    "#-------------------------------------------------------------------------------",
    "#@group: testgroup",
    "#-------------------------------------------------------------------------------",
]

def test_add_new_group():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    new_group = SSH_Group(name="testgroup")
    config.groups.append(new_group)

    found_group = config.get_group_by_name("testgroup")
    assert found_group == new_group

    config.generate_ssh_config()
    assert config.ssh_config_lines == config1_modified_lines


#------------------------------------------------------------------------------
# Test parsing configuration and add new group then verify rendering output is
# modified as expected - on existing config
#------------------------------------------------------------------------------

config2="""
#@host: some-host-info
Host defaulthost
    hostname 2.2.3.3
"""
config2_modified_lines=[
    "#<<<<< SSH Config file managed by sshclick >>>>>",
    "",
    "#@host: some-host-info",
    "Host defaulthost",
    "    hostname 2.2.3.3",
    "",
    "",
    "#-------------------------------------------------------------------------------",
    "#@group: testgroup",
    "#@desc: description123",
    "#-------------------------------------------------------------------------------",
]

def test_add_new_group_complex():
    config = SSH_Config("none", config2.splitlines())
    config.parse()

    new_group = SSH_Group(name="testgroup", desc="description123")
    config.groups.append(new_group)

    found_group = config.get_group_by_name("testgroup")
    assert found_group == new_group

    config.generate_ssh_config()
    assert config.ssh_config_lines == config2_modified_lines
