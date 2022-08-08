from sshclick.sshc import SSH_Config


#------------------------------------------------------------------------------
# Test parsing configuration and add new group then verify rendering output is
# modified as expected - on empty config
#------------------------------------------------------------------------------
config1 = """
#-----------------------
#@group: group1
#-----------------------
Host test-app
    hostname 10.1.1.20

Host test-data
    hostname 10.1.1.30

Host test-a*
    port 2222

Host test-*
    port 1111
    user test1234
"""

def test_host_pattern_matching():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    inherited1 = config.find_inherited_params("test-app")
    assert inherited1 == [
        ("test-a*", {"port": "2222"}),
        ("test-*", {"port": "1111", "user": "test1234"}),
    ]

    inherited2 = config.find_inherited_params("test-data")
    assert inherited2 == [
        ("test-*", {"port": "1111", "user": "test1234"}),
    ]
