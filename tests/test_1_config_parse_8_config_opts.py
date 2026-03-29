from sshclick.core import SSH_Config

#------------------------------------------------------------------------------
# Test parsing groups with group metadata (desc and multi-info)
# And nested hosts with parameters
#------------------------------------------------------------------------------
config1 = """
#<<<<< SSH Config file managed by sshclick >>>>>
#@config: host-style=simple
#@config: something=nice
"""

def test_parse_config_opts():
    config = SSH_Config(None, config1.splitlines()).parse()

    # Verify parsed config options
    assert config.opts == {
        "host-style": "simple",
        "something": "nice",
    }
