from sshclick.sshc import SSH_Config, SSH_Group

#------------------------------------------------------------------------------
# Test parsing configuration and add new group then verify rendering output is
# modified as expected - on empty config
#------------------------------------------------------------------------------
config1=""
config1_modified_lines=[
    "#<<<<< SSH Config file managed by sshclick >>>>>\n",
    "#@config: host-style=simple\n",
    "#@config: something=nice\n",
]

def test_add_new_group():
    config = SSH_Config("none", config1.splitlines()).parse()

    config.opts["host-style"] = "simple"
    config.opts["something"] = "nice"
    config.generate_ssh_config()

    assert config.ssh_config_lines == config1_modified_lines


