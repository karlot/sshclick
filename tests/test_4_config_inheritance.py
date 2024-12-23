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

    inherited1 = config._find_inherited_params("test-data")
    assert inherited1 == [
        ("test-*", {"port": "1111", "user": "test1234"}),
    ]

    inherited2 = config._find_inherited_params("test-app")
    assert inherited2 == [
        ("test-a*", {"port": "2222"}),
        ("test-*", {"port": "1111", "user": "test1234"}),
    ]


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
                inherited_params=[
                    ("test-a*", {"port": "2222"}),
                    ("test-*", {"port": "1111", "user": "test1234"})
                ]
            ),
            SSH_Host(name="test-data", group="group1",
                params={"hostname":"10.1.1.30"},
                inherited_params=[
                    ("test-*", {"port": "1111", "user": "test1234"})
                ]
            ),
        ],
        patterns=[
            SSH_Host(name='test-a*', group='group1', type=HostType.PATTERN, params={'port': '2222'}),
            SSH_Host(name='test-*', group='group1', type=HostType.PATTERN, params={'port': '1111', 'user': 'test1234'}),
        ]
    )
