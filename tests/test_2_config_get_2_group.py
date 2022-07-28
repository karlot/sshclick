import pytest
from lib.sshutils import SSH_Config, SSH_Group, SSH_Host

#-----------------------------------
# FILE CONTENT SAMPLES FOR PARSING
#-----------------------------------

config1="""
#@host: some-host-info
Host defaulthost
    hostname 2.2.3.3
"""

config2="""
#@host: some-host-info
Host defaulthost
    hostname 2.2.3.3

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

#-----------------------------------
# Tests
#-----------------------------------
def test_get_group_nok_nofail():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    group = config.find_group_by_name("testgroup-2", throw_on_fail=False)
    assert group == None


def test_get_group_nok_exception():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    with pytest.raises(Exception):
        _ = config.find_group_by_name("testgroup-2", throw_on_fail=True)
    

def test_get_group_ok():
    config = SSH_Config("none", config2.splitlines())
    config.parse()

    group = config.find_group_by_name("testgroup-2", throw_on_fail=True)
    
    assert group == SSH_Group(name="testgroup-2", desc="this is description 2", info=["info line 2-1", "info line 2-2"], hosts=[
        SSH_Host(name='test2', group="testgroup-2", info=["hostinfo2"], params={
            "hostname": "4.3.2.1",
            "port": "2222",
            "user": "test4321",
        }),
    ])
