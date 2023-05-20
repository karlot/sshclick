# Output and initial configuration
Output splash.gif
Set Padding 20
Set FontSize 16
Set Width 900
Set Height 600
Set Theme "Elementary"

# Show comment and output of listing hosts
Sleep 200ms
Type "# List defined hosts in SSH Config file"
Enter
Sleep 1s
Type "sshc hosts"
Enter
Sleep 5s

# Show comment and output of filtering with host list
Type@1ms "clear"
Enter@1ms
Type "# Filter 'hosts' output based on host name (regex)"
Enter
Sleep 1s
Type "sshc hosts --name lab"
Enter
Sleep 5s

# Show comment and output of showing host details with graph of linked connections
Type@1ms "clear"
Enter@1ms
Type "# 'host show' command can visualize connection graphs if 'ProxyJump' is used"
Enter
Sleep 1s
Type "sshc host show lab-serv1 --graph"
Enter
Sleep 5s

# Show comment and output of built-in help
Type@1ms "clear"
Enter@1ms
Type "# Detailed help included in all commands"
Enter
Sleep 1s
Type "sshc -h"
Enter
Sleep 5s
