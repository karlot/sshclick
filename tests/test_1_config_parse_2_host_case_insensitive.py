from lib.sshutils import SSH_Config, SSH_Group, SSH_Host

#-----------------------------------
# FILE CONTENT SAMPLES FOR PARSING
#-----------------------------------
# Configuration with all lowercase
config1="""
#@host: testinfo
host test
    hostname 1.2.3.4
    port 2222
    user testUSER
"""
# Configuration with mixed case
config2="""
#@host: testinfo
Host test
    HostName 1.2.3.4
    PORT 2222
    USER testUSER
"""

# All parsed configuration should result with lowercased keywords for parameters
# while values should be kept case-sensitive
results = [
    SSH_Group(name="default", hosts=[
        SSH_Host(name="test", group="default", info=["testinfo"], params={
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

def test_parse_camelcase():
    lines = config2.splitlines()
    groups = SSH_Config("none", lines).parse().groups
    assert groups == results
