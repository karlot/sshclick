# !!! Currently not working, as output is not friendly with Textual :) !!!
# Output and initial configuration
Output tui_demo.gif
Set Padding 20
Set FontSize 16
Set Width 900
Set Height 600
Set Theme "Elementary"

# Show comment and run SSHClick TUI
Sleep 200ms
Type "# Start interactive TUI for sshc"
Enter
Sleep 2s
Type "sshc tui"
Enter
Sleep 5s

# On open TUI, go down to "network" group and press enter to open it
Down
Sleep 500ms
Down
Sleep 500ms
Enter
Sleep 1s

# Move down to "lab-servers" group and press enter to open it
Down
Sleep 500ms
Down
Sleep 500ms
Down
Sleep 500ms
Down
Sleep 500ms
Down
Sleep 500ms
Down
Sleep 500ms
Enter
Sleep 500ms

# Move down to "server-behind-lab" host and wait a bit, then exit
Down
Sleep 500ms
Down
Sleep 500ms
Down
Sleep 3s
Type "q"
Sleep 2s