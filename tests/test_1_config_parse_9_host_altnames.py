from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

#-----------------------------------
# FILE CONTENT SAMPLES FOR PARSING
#-----------------------------------
# Configuration with all lowercase
config1="""
#@host: testinfo
host test test.example test.example.com
    hostname 1.2.3.4
    port 2222
    user testUSER
"""

# All parsed configuration should result with lowercased keywords for parameters
# while values should be kept case-sensitive
results = [
    SSH_Group(name="default", desc="Default group", hosts=[
        SSH_Host(name="test", group="default", info=["testinfo"], alt_names=["test.example", "test.example.com"], params={
            "hostname":"1.2.3.4",
            "port":"2222",
            "user":"testUSER",
        })
    ])
]


#-----------------------------------
# Tests
#-----------------------------------
def test_parse_lowercase():
    lines = config1.splitlines()
    groups = SSH_Config("none", lines).parse().groups
    assert groups == results
