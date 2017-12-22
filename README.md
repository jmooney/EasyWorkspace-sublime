
Easy workspace management for sublime!

Save and reopen files and folders with less hassle.

Features:
 - Quick and Easy interface for saving/loading workspaces
 - No sublime-project required
 - Usable from command line (see git integration below)

Requirements
------------
* Sublime Text 3 (recent build)

Installing
----------
### With Package Control
1. Install [Package Control](https://packagecontrol.io/installation)
2. Run "Package Control: Install Package" command
3. Find and install the 'EasyWorkspace' plugin
4. Restart Sublime Text if there are issues

### Manually
Clone the repository in your Sublime Text "Packages" directory:

    git clone https://github.com/jmooney/EasyWorkspace-sublime.git

The "Packages" directory is located at:

* OS X: `~/Library/Application Support/Sublime Text 3/Packages/`
* Linux: `~/.config/sublime-text-3/Packages/`
* Windows: `%APPDATA%\Sublime Text 3\Packages\`

Usage
-----
EasyWorkspace can save your open files and folders for easy access!

    Save Workspace    | ctrl+alt+s       | Save open files and folders as an easy workspace
    Save As Workspace | ctrl+alt+shift+s | Save easy workspace to specified file
    Open Workspace    | ctrl+alt+o       | Open an existing workspace

EasyWorkspace commands are also available from the command palette or the menu!

Tools->Packages->EasyWorkspace

Commands
--------

    OpenEasyWorkspace   | Opens an existing easy workspace
    SaveEasyWorkspace   | Saves open files and folders to an easy workspace file
    SaveAsEasyWorkspace | Saves open files and folders to a specified easy workspace file
    DeleteEasyWorkspace | Delete an existing easy workspace

Git Integration
---------------

    For explicit examples on integrating git with EasyWorkspace, see 'easy-ws-git-integration.sh'
    included in this repository's root directory.

Have you ever been knee-deep in adding a new feature to your git-versioned project
when suddenly a critical bug pops up? You save your current changes in your feature
branch, then start a new branch to tackle the bug. Git is happy, but what about
sublime!? All your open files/folders are just clutter while you work to fix
the new bug.

Wouldn't it be great if you could save your sublime workspace for your feature branch
and restore it when you come back to work on it? Well, with EasyWorkspace, you can!

EasyWorkspace commands are runnable from the command line. This allows one to easily
integrate EasyWorkspace with the shell and/or git to automatically manage workspaces.

For instance, one can create git aliases to do the following:

1. Save the active sublime workspace as an EasyWorkspace file associated with
   the current or specified git repo and branch.

2. Automatically open the EasyWorkspace associated with either the current or a
   specified git branch

To see these examples in action, check out the easy-ws-git-integration.sh file
included in this repositories root directory. This file details and exemplifies
script functions and git aliases which perform the above actions!
