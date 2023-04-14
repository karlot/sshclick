import pytest
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#-----------------------------------
# FILE CONTENT SAMPLES FOR PARSING
#-----------------------------------

config1=""

config2="""
#<<<<< SSH Config file managed by sshclick >>>>>
#@host: testinfo
host test
    hostname 1.2.3.4
    port 2222
    user testUSER
"""

config3="""
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
def test_check_host_bad():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    assert not config.check_host_by_name("test")


def test_get_host_exception():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    with pytest.raises(Exception):
        config.get_host_by_name("test")


def test_get_host_ok():
    config = SSH_Config("none", config2.splitlines())
    config.parse()

    host, group = config.get_host_by_name("test")
    
    expected_host = SSH_Host(name='test', group="default", info=["testinfo"], params={
        "hostname": "1.2.3.4",
        "port": "2222",
        "user": "testUSER",
    })

    assert host == expected_host
    assert group == SSH_Group(name='default', desc="Default group", info=[], hosts=[expected_host], patterns=[])


def test_get_all_host_names():
    config = SSH_Config("none", config3.splitlines())
    config.parse()

    all_names = config.get_all_host_names()
    
    assert all_names == ["defaulthost", "test2"]

    