# SSH Click Config manager (sshclick)

![splash_gif](https://raw.githubusercontent.com/karlot/sshclick/master/tapes/splash.gif)

## Links

- [Intro](https://github.com/karlot/sshclick#intro)
- [Why?](https://github.com/karlot/sshclick#why)
- [What does it do](https://github.com/karlot/sshclick#what-does-it-do)
  - [Installation procedure](https://github.com/karlot/sshclick#installation-procedure)
  - [Upgrade procedure](https://github.com/karlot/sshclick#upgrade-procedure)
  - [Uninstall procedure](https://github.com/karlot/sshclick#uninstall-procedure)
- [SSH Config structure](https://github.com/karlot/sshclick#ssh-config-structure-and-important-note-about-comments)
  - [Comment blocks and metadata](https://github.com/karlot/sshclick#comment-blocks-and-metadata-in-ssh-config)
  - [Include keyword support](https://github.com/karlot/sshclick#include-keyword-support)
- [Example usage and features](https://github.com/karlot/sshclick#example-usage-and-features)
  - [Textual TUI browser (`ssht`)](https://github.com/karlot/sshclick#textual-tui-browser-ssht)
  - [Group commands and options](https://github.com/karlot/sshclick#group-commands-and-options)
  - [Host commands and options](https://github.com/karlot/sshclick#host-commands-and-options)
  - [Config commands and options](https://github.com/karlot/sshclick#config-commands-and-sshclick-configuration-options)
  - [Output styling and user ENV variables](https://github.com/karlot/sshclick#output-styling-and-user-env-variables)
- [Sample configuration](https://github.com/karlot/sshclick#sample-configuration)
- [Author](https://github.com/karlot/sshclick#author)
- [License](https://github.com/karlot/sshclick#license)

## Intro

Terminal-based assisted management of SSH config files.  
Built out of boredom with managing messy and huge `ssh_config` files.  

Backup your SSH config files before using!  
SSHClick can be used with "show" and "list" commands for hosts, without modifying your SSH Config in any way!  

**Only commands that modify configuration will edit and rewrite your SSH config file. In that case, comments and extra information outside the format SSHClick understands may be discarded, and the configuration will be reformatted to match SSHClick style. See the notes below to understand how SSHClick keeps the file organized.**

SSHClick also includes a separate Textual-based TUI browser that can be launched with `ssht`.  

![splash_gif](https://raw.githubusercontent.com/karlot/sshclick/master/tapes/sshc_tui_example.svg)

## Why?

- I need something that works fast and great in terminal, and does not require complex setup.
- SSH config is the only config I need to backup.
- SSH config is already feature-rich with all options the SSH client supports, so there is no need to invent another storage layer
- I need quick way to search, group and visualize all hosts inside SSH configuration (especially since it can grow huge)

## What does it do?

SSHClick (`sshc`) is a tool designed to work with existing SSH configuration files on Linux, Windows, and WSL terminal environments.  
It parses your SSH config, and can provide easy commands to list, filter, modify or view specific Host entries.
Through additional metadata comments it can add abstractions such as groups and extra information that remain readable in the configuration file and can also be parsed and shown by the tool.
The companion `ssht` command opens a Textual TUI on top of the same parsed configuration, so you can browse groups and hosts interactively from the terminal.

### Installation procedure

1. **Check preconditions:**
    - Currently only tested on Linux (Debian 10,11, Ubuntu 20.04,22.04), but should work on other systems as well
    - Minimum Python 3.10 with `pip` installed
        - it is preferable not to use the system Python version; to install a custom user Python on Linux, you can try using `pyenv` (<https://github.com/pyenv/pyenv>)
    - git installed (for installing from source)

2. **Install package:**
    - from PyPI using pip

        ```console
        pip install sshclick
        ```

    - (OR) from source using pip

        ```console
        git clone https://github.com/karlot/sshclick
        cd sshclick
        pip install .
        ```

3. Use it as you like, `sshc` command should be available to access SSHClick application, see below chapter for basic [usage](https://github.com/karlot/sshclick#example-usage-and-features)

4. Install shell autocompletion (*TAB-TAB auto-completes on commands, options, groups and hosts*)
    - **Bash** - Add this line to end of your `~/.profile` file:

      ```sh
      eval "$(_SSHC_COMPLETE=bash_source sshc)"
      ```

    - **Zsh** - Add this line to end of your `~/.zshrc` file:

      ```sh
      eval "$(_SSHC_COMPLETE=zsh_source sshc)"
      ```

### Upgrade procedure

- Upgrade from new PyPI release:  

  ```console
  pip install --upgrade sshclick
  ```

- Upgrade from source:
  Assuming installation is already done, and previous version is cloned in some local folder

  ```console
  cd sshclick
  git pull
  pip install --upgrade .
  ```

### Uninstall procedure

Simply run:

```console
pip uninstall sshclick
```

In case you have installed from cloned source code, you can delete locally cloned repo.

```console
rm -r sshclick
```

---

## SSH Config structure, and important note about comments

When SSHClick edits and writes an SSH config file it must use a specific style, and it internally uses comments to organize the configuration. This means comments outside what SSHClick handles are unsupported and may be lost when SSHClick modifies a file.

### Comment blocks and metadata in SSH Config

SSHClick uses comments to add extra information that it can use for grouping and host metadata. Special metadata lines start with `#@<tag>:` or `# <tag>:` followed by tags such as `group`, `desc`, or `info`. These are considered group metadata tags because they apply on the group level. Note that separator lines above and below the group header are only visual aids: they are ignored during parsing, but are included when modifying or generating the SSH config file.  

These metadata headers can also be added manually in SSH config, or `sshc` can add them and move hosts under a specific group.

Normally start of the "GROUP HEADER" inside SSH Config would look like below.  

- `#@group:` or `# group:` is the key metadata tag that defines that all hosts configured below it belong to this group
- `#@desc:` or `# desc:` is an optional tag that adds a description to the defined group, and will be displayed in normal group display commands
- `#@info:` or `# info:` is optional tag that can appear multiple times, adding extra information lines tied to the group.

Additionally each "host" definition can have optional meta info:

- `#@host:` or `# host:` is an optional tag that can appear multiple times and can hold information about the host. This metadata applies to the next `Host` definition that appears. If this key is added after a `Host` config keyword, it will apply to the next host, so keep host metadata above the actual host definition.

Following is sample how group header is rendered by SSHClick:

```conf
#-------------------------------------------------------------------------------
#@group: <GROUP-NAME>       [MANDATORY]   <-- This line starts new group
#@desc: <GROUP-DESCRIPTION> [OPTIONAL, SINGLE]
#@info: <GROUP-INFO-LINES>  [OPTIONAL,MULTIPLE]
#-------------------------------------------------------------------------------
Host ...    <-- this hosts definitions are part of the defined group
    param1 value1
    param2 value2

#@host: <HOST-INFO-LINES>   [OPTIONAL,MULTIPLE] <-- Adds info to following host
Host ...

<ANOTHER GROUP HEADER>
```

If there are no groups defined, then all hosts are considered to be part of "default" group. SSHClick can be used to move hosts between groups and handle keeping SSH config "tidy" and with consistent format.

### Include keyword support

SSHClick currently supports only top-level `Include` keyword handling. Included files are parsed into one effective read-only view, so hosts and groups from the main file and included files can be browsed together in both `sshc` and `ssht`.

When any `Include` keyword is present, SSHClick intentionally disables configuration modification and rendering back to disk. This is currently a strict feature boundary, until include-aware editing and write-back behavior are designed fully.

## Example usage and features

SSHClick provides the `sshc` CLI tool for interacting with your SSH config file and performing organization, listing, display, and modification of SSH group and host configuration parameters.  
`sshc` provides `--help` at each command level so you can inspect available commands and options quickly.  

For example, to check the version, type: `sshc --version`  
*Sample output:*

```console
$ sshc --version
SSHClick (sshc) - Version: <version>
```

If you run `sshc` alone, or add `-h` or `--help`, it will show what else can be added to the command.  
*Example:*

```console
$ sshc --help
Usage: sshc [OPTIONS] COMMAND [ARGS]...

  SSHClick - SSH Config manager. version <version>

  NOTE: As this will change your SSH config files, make backups before using
  this software, as you might accidentally lose some configuration.

Options:
  --config TEXT  Config file (default: ~/.ssh/config). Can be set with
                 SSHC_CONFIG.
  --stdout          Send changed SSH config to STDOUT instead to original
                    file, can be enabled with setting ENV variable (export
                    SSHC_STDOUT=1)
  --diff            Show only difference is config changes, instead of
                    applying them. Can be enabled with setting ENV variable
                    (export SSHC_DIFF=1)
  --version         Show the version and exit.
  -h, --help        Show this message and exit.

Commands:
  config  Modify SSHClick configuration through SSH Config
  group   Command group for managing groups
  groups  Lists all groups
  host    Command group for managing hosts
  hosts   List configured hosts
```

The Textual interface is launched separately with `ssht`, and you can inspect its options with `ssht --help`. It supports the same `--config` option and `SSHC_CONFIG` environment variable as `sshc`.

### Textual TUI browser (`ssht`)

`ssht` is the interactive browser for the same SSHClick config model used by `sshc`. It is intended for quick navigation, inspection, and common connection actions without leaving the terminal.

Current TUI features:

- left-side tree navigation for groups, normal hosts, and pattern hosts
- polished host and group detail inspector in the main pane
- host `Overview` and `Connectivity` tabs
- direct `ssh`, `sftp`, key-copy, and fingerprint-reset actions for normal hosts
- centered action modal and destructive delete confirmation
- right-side management drawers for creating and editing hosts, groups, and SSHClick config metadata
- guided host editor with multiline info editing and additional SSH parameter picker
- status bar with active config path and writable/read-only mode
- include-aware read-only state when top-level `Include` is present

Current TUI limitations:

- delete is available only when the loaded config is writable
- current `Include` support stays strictly read-only
- connectivity diagnostics are still limited to the existing graph/tunnel-oriented view

Useful key bindings in the current TUI:

- `q` quit
- `a` open actions for the current selection
- `s` open SSH session for the selected host
- `f` open SFTP session for the selected host
- `d` delete selected host or group when writable
- `r` reload configuration from disk
- `Up` / `Down` move through groups and hosts in the tree
- `Left` / `Right` collapse and expand selected groups
- `Left` / `Right` switch selected hosts between `Overview` and `Connectivity`
- `Space` expand/collapse the selected group in the tree
- `Enter` toggles group nodes or opens actions for the selected host

Example:

```console
$ ssht --help
Usage: ssht [OPTIONS]

  SSHClick - SSH Config browser TUI. version <version>

  NOTE: This opens the Textual interface for browsing your SSH configuration.

Options:
  --config TEXT  Config file (default: ~/.ssh/config). Can be set with
                 SSHC_CONFIG.
  --version      Show the version and exit.
  -h, --help     Show this message and exit.
```

You can launch the TUI against a specific config file or through the shared env var:

```console
ssht --config ~/.ssh/config
SSHC_CONFIG=~/.ssh/config ssht
```

When a config uses top-level `Include`, `ssht` will still merge the visible data into one browser view, but it will clearly switch to read-only mode and disable write actions.

### `group` commands and options

To manage groups, type `sshc group --help` to see options.  
*Example:*

```console
$ sshc group --help
Usage: sshc group [OPTIONS] COMMAND [ARGS]...

  Command group for managing groups

Options:
  -h, --help  Show this message and exit.

Commands:
  create  Create new group
  delete  Delete group
  list    Lists all groups
  rename  Rename existing group
  set     Change group parameters
  show    Shows group details
```

### `host` commands and options

To manage hosts, type `sshc host --help` to see options.  
*Example:*

```console
$ sshc host --help
Usage: sshc host [OPTIONS] COMMAND [ARGS]...

  Command group for managing hosts

Options:
  -h, --help  Show this message and exit.

Commands:
  create   Create new host
  delete   Delete host(s)
  install  Install SSH key to hosts (experimental)
  list     List configured hosts
  rename   Rename existing host
  set      Set/Change host configuration
  show     Show current host configuration
```

### `config` commands and SSHClick configuration options

SSHClick does not have its own separate configuration files, so most configuration it understands comes from command arguments and options, environment variables, and the SSH config file itself.

When you want to persist some config options instead of repeating them on the command line, you can use environment variables set through your shell profile.

There is also an option to store such config in the SSH config file itself as metadata comments, so it stays portable and backed up together with the SSH config file.

The `config` command currently supports `show`, `set`, and `del` subcommands.

#### Example

```console
$ sshc config --help
Usage: sshc config [OPTIONS] COMMAND [ARGS]...

  Modify SSHClick configuration through SSH Config

Options:
  -h, --help  Show this message and exit.

Commands:
  del   Delete config option
  set   Set config option
  show  Show all config options
```

#### Example: Set host output style to 'card'

```console
$ sshc config set --help
Usage: sshc config set [OPTIONS]

  Set config option

Options:
  --host-style TEXT  Set how to display hosts in 'show' command.
                     Available:(panels,card,simple,table,table2,json)
                     (default: panels)
  -h, --help         Show this message and exit.

$ sshc config set --host-style card
```

This will now store config in the currently used SSH config file as follows:

```conf
#<<<<< SSH Config file managed by sshclick >>>>>
#@config: host-style=card
```

To delete this config, either remove the line from file manually, or use `sshc` command:

```console
sshc config del --host-style
```

### Output styling and user ENV variables

`sshc host show` can display host output in several formats. You can select one with `sshc host show <host> --style <style>`.  
Available styles are:

| Style              | Description                                       |
|--------------------|---------------------------------------------------|
| `panels` (default) | Display data in several panels                    |
| `card`             | Add data to single "card"                         |
| `simple`           | Simple output with minimal decorations            |
| `table`            | Flat table with 3 columns                         |
| `table2`           | Nested table with separated host SSH params       |
| `json`             | JSON output, useful for binding with other tools  |

If you want to set a default style for your shell, you can export an environment variable such as `export SSHC_HOST_STYLE=table`, and add it to `.profile`, `.bashrc`, or `.zshrc` so it is set when the shell session starts.  
Alternatively, you can use the SSHClick internal config mechanism to store some config data in your SSH config file as commented metadata, so it can be backed up together with your SSH config. For example: `sshc config set --host-style table`.

If you do not like colorized output, you can disable it with `export NO_COLOR=1`. If you want it permanently, add it to your shell startup files as well.

> NOTE! When sending output into non-terminal such as to file, SSHClick will recognize that and will remove all ANSI Escape characters (colors and stuff...) so that output is captured in clear way.

## Sample configuration

The user-facing sample files live in [example/config_sample](example/config_sample) and [example/config_sample_extra](example/config_sample_extra). The main sample demonstrates top-level `Include` usage in read-only mode.

```conf
#<<<<< SSH Config file managed by sshclick >>>>>

Include config_sample_extra

#-------------------------------------------------------------------------------
#@group: network
#@desc: Network devices in my lab
#@info: user='admin' password='password'
#@info: Not really, but for demo it's ok :)
#-------------------------------------------------------------------------------
Host net-switch1
    hostname 10.1.1.1

Host net-switch2
    hostname 10.1.1.2

Host net-switch3
    hostname 10.1.1.3

Host net-*
    user admin


#-------------------------------------------------------------------------------
#@group: jumphost
#@desc: Edge-server / SSH bastion
#@info: Used for jump-proxy from intnet to internal lab servers
#-------------------------------------------------------------------------------
#@host: This host can be used as proxyjump to reach LAB servers
Host jumper1
    hostname 123.123.123.123
    user master
    port 1234


#-------------------------------------------------------------------------------
#@group: lab-servers
#@desc: Testing/Support servers
#@info: Some [red]important[/] detail here!
#@info: We can have color markups in descriptions and info lines
#-------------------------------------------------------------------------------
#@host: This server is [red]not[/] reachable directly, only via [green]jumper1[/]
Host lab-serv1
    hostname 10.10.0.1
    user admin

#@host: This server is [red]not[/] reachable directly, only via [green]jumper1[/]
Host lab-serv2
    hostname 10.10.0.2

#@host: This server is [red]not[/] reachable directly, only via [green]lab-serv1[/]
#@host: SSHClick can represent how end-to-end tunnels will be established
Host server-behind-lab
    hostname 10.30.0.1
    user testuser
    port 1234
    proxyjump lab-serv1
    localforward 7630 127.0.0.1:7630

#@host: This pattern applies to all hosts starting with 'lab-'
#@host: setting 'user' and 'proxyjump' property
Host lab-*
    user user123
    proxyjump jumper1

```

## Author

Karlo Tisaj  
email: <karlot@gmail.com>  
github: <https://github.com/karlot>

## License

MIT License

Copyright (c) 2026 Karlo Tisaj

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
