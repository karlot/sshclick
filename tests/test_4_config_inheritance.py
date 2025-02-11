from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host, HostType

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

def test_host_pattern_matching_manual():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    assert config.get_host_by_name("test-data").matched_params == {
        "port": ("1111", "test-*"),
        "user": ("test1234", "test-*"),
    }

    assert config.get_host_by_name("test-app").matched_params == {
        "port": ("2222", "test-a*"),        # Taken from first matched pattern
        "user": ("test1234", "test-*"),     # Taken from later pattern
    }


def test_host_pattern_matching_parsed():
    config = SSH_Config("none", config1.splitlines())
    config.parse()

    # Default group is always first
    assert config.groups[0] == SSH_Group(name="default", desc="Default group")

    # group1 should look like this...
    assert config.groups[1] == SSH_Group(name="group1", desc="",
        hosts=[
            SSH_Host(name="test-app", group="group1",
                params={"hostname":"10.1.1.20"},
                matched_params={
                    "port": ("2222", "test-a*"),
                    "user": ("test1234", "test-*"),
                }
            ),
            SSH_Host(name="test-data", group="group1",
                params={"hostname":"10.1.1.30"},
                matched_params={
                    "port": ("1111", "test-*"),
                    "user": ("test1234", "test-*"),
                }
            ),
        ],
        patterns=[
            SSH_Host(name='test-a*', group='group1', type=HostType.PATTERN, params={'port': '2222'}),
            SSH_Host(name='test-*', group='group1', type=HostType.PATTERN, params={'port': '1111', 'user': 'test1234'}),
        ]
    )
