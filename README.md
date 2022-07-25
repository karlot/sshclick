# SSH Click Config manager (sshclick)

Terminal based assisted management of your SSH config files.  
Built out of my own frustration with managing messy and huge ssh_config files.

VERY EARLY VERSION, backup your SSH config files before using! :D

## Why?

There are plentiful of tools that try to approach managing and organizing remote host configuration in different ways. Many of them implement their specific configurations, and/or full UIs how to save and organize various configuration information.
Problem is that many of such management tools do not work in standard server terminal, or control actual users SSH config (some have option to render "their" configuration to SSH config, or some weird piping or aliases setup to workaround the problem).

Why is this problem (at least for me), and what am I trying to solve with this tool?
* I need something that works fast and great in terminal, and does not require complex setup.
* Managing some other configuration that renders to SSH config is extra step that I don't like.
* SSH config is already feature-full with all options SSH client support, why inventing extra layer?
* SSH config is the only config I need to backup.
* I need quick way to search, group and visualize all hosts inside configuration (especially since it can grow huge)

If you have same thoughts, this tool might be for you.

## What does it do?

sshclick is just a tool designed to work with existing SSH configuration on your Linux/Windows/WSL terminal environment.  
It basically parses your SSH config, and can provide easy commands to list, filter, modify or view specific Host entries.

## Installation procedure

Should be straight forward...  
1. Check preconditions:
    - python3 & pip installed
    - git installed

2. Clone this repo and run pip install
    ```console
    git clone https://github.com/karlot/sshclick
    cd sshclick
    pip install --editable .
    ```
    NOTE: optionally you can install it in virtualenv if you like

3. Use it as you like, "sshc" command should be available to access SSHClick application
    ```
    $ sshc --help
    Usage: sshc [OPTIONS] COMMAND [ARGS]...

      SSHClick - SSH Config manager

      Note: As this is early alpha, backup your SSH config files before this
      software, as you might accidentally lose some configuration

    Options:
      --sshconfig PATH  Config file, default is ~/.ssh/config
      --stdout          Send changed SSH config to STDOUT instead to original file
      --version         Show current version
      -h, --help        Show this message and exit.

    Commands:
      group  Manage groups
      host   Manage hosts
    ```
4. Install shell autocompletion (TAB autocompletes on commands, options, and hosts)
    * __Bash__ - Add this line to your `~/.bashrc` file:
      ```
      eval "$(_SSHC_COMPLETE=bash_source sshc)"
      ```
    * __Zsh__ - Add this line to your `~/.zshrc` file:
      ```
      eval "$(_SSHC_COMPLETE=zsh_source sshc)"
      ```


## Upgrade procedure
Assuming installation is already done, and previous version is cloned in some local folder

```console
cd sshclick    # existing cloned repo
git pull
pip install --editable .
```

## Uninstall procedure
Assuming installation is already done, and previous version is cloned in some local folder

```console
pip uninstall sshclick
rm -rf sshclick    # existing cloned repo
```

## SSH Config structure, and important note about comments

sshclick when editing and writing to SSH config file must use specific style, and is internally using comments to "organize" configuration itself. This means comments outside of what sshclick is handling are unsupported and will be lost when sshclick modifies a file.)


## Comment blocks and metadata in SSH Config

sshclick uses comments to add extra information which it can use to add concept of grouping to hosts.  
Special "metadata" lines start with "#@" followed by some of meta-tags like "group", "desc", "info". This are all considered group metadata tags, as they apply on the group. Note that line separations are added only for visual aid, they are ignored at parsing, but are included when modifying SSH config.  
**Currently host based tags are not supported**

This "headers" can be added manually in SSH config, or sshclick can add them and move hosts under specific group.

Start of the "GROUP HEADER" looks like this:
```
#-------------------------------------------------------------------------------
#@group: <GROUP-NAME>       [MANDATORY]   <-- This line starts new group
#@desc: <GROUP-DESCRIPTION> [OPTIONAL]
#@info: <GROUP-INFO-LINES>  [OPTIONAL,MULTIPLE]
#-------------------------------------------------------------------------------
Host ...    <-- this hosts definitions are part of the defined group
Host ...

<ANOTHER GROUP HEADER>
```

If there are no groups, then all hosts are considered to be part of "default" group.


## License
MIT License
