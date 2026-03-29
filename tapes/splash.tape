# Output and initial configuration
Output splash.gif
Set Padding 20
Set FontSize 16
Set Width 1000
Set Height 650
Set Theme "Elementary"

# Show listing hosts from config
Sleep 300ms
Type "# Browse hosts from SSH config"
Enter
Sleep 700ms
Type "sshc hosts"
Enter
Sleep 4s

# Filter hosts based on regex from name
Type@1ms "clear"
Enter@1ms
Type "# Filter 'hosts' based on regex from name"
Enter
Sleep 700ms
Type "sshc hosts --name lab"
Enter
Sleep 4s

# Show group details with metadata and member hosts
Type@1ms "clear"
Enter@1ms
Type "# Inspect a group with metadata and member hosts"
Enter
Sleep 700ms
Type "sshc group show lab-servers"
Enter
Sleep 4s


# Show host details with connection graph
Type@1ms "clear"
Enter@1ms
Type "# Visualize proxy jumps and tunnels for a host"
Enter
Sleep 700ms
Type "sshc host show server-behind-lab --graph"
Enter
Sleep 5s


# Detailed help
Type@1ms "clear"
Enter@1ms
Type "# Simple help with autocomplete available out of the box"
Enter
Sleep 700ms
Type "sshc --help"
Enter
Sleep 5s
