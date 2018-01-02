#!/bin/sh

################################################################################
# EasyWorkspace git integration
#
# Sublime's EasyWorkspace can be integrated with git to easily maintain
#   a workspace for each branch in the repo.
#
# Included here are some helpful functions and examples of how one can
# integrate EasyWorkspace with git!
#
# *NOTE: These features only work if sublime is already running. Sublime can
#        only execute window commands and plugin commands if the application is
#        already running (otherwise, windows and plugins are not
#        loaded/created!)
#
#        One could modify the below functions to manage this issue by adding
#        a check and delay, but we leave this exercise up to the user.
#
# Usage
# ==============================================================================
# To use these EasyWorkspace/git integration examples in your own project,
# follow the following steps:
#
# 1. Save this file to your local machine
# 2. Add the following aliases to your .gitconfig file
#       '~/.easy-ws-git-integration.sh' should be the path to your local copy in #1.
#
#     [alias]
#          edit = !. ~/.easy-ws-git-integration.sh && easy_ws_git_edit
#          save = !. ~/.easy-ws-git-integration.sh && easy_ws_git_save
#
# 3. Now you can use 'git edit' or 'git save' to easily integrate git with
#    sublime EasyWorkspaces!
#
# 4. Lastly, for autocomplete on these git aliases, add the following functions
#    to your .bashrc file (or equivalent)
#
#        _git_edit() {
#            _git_checkout
#        }
#        _git_save() {
#            _git_checkout
#        }
#
# 5. Profit! Now you can autocomplete which branch to edit or save
#
################################################################################

##
# When run inside a git repo, outputs to stdout the EasyWorkspace filename
# associated with the repo's current branch.
#
# If a branchname is provided as the first argument, we output this branchname's
# associated EasyWorkspace filename
#
# Arguments:
#   branch-name (optional) -- identifies the branch to get associated workspace file
##
easy_ws_git_workspace_name() {
    # check for valid repo root
    local gitRepoRoot
    local gitRepoName

    gitRepoRoot=$(git rev-parse --show-toplevel)

    # check valid repo root
    if [ $? -ne 0 ]; then
        return 1
    fi

    gitRepoName=$(basename "$gitRepoRoot")

    # use optional or current branch name
    if [ ! -z "$1" ]; then
        gitBranchName="$1"
    else
        gitBranchName=$(git rev-parse --abbrev-ref HEAD)
    fi

    # write to stdout the result
    echo "$gitRepoName"/"$gitBranchName"
}

##
# When run inside a git repo, opens in a new sublime window the easyworkspace
# associated with the current git repo and branch
#
# If no corresponding workspace exists, it will open an empty workspace
# and create the association.
#
# Arguments:
#   branch-name (optional) - identifies the branch workspace to edit
##
easy_ws_git_edit() {
    local workspaceName

    # try to determine the current repo/branch workspace name
    workspaceName=$(easy_ws_git_workspace_name "$1")
    if [ $? -ne 0 ]; then
        return 1
    fi

    # open the easy workspace in sublime
    subl --command "open_easy_workspace { \"filename\": \"$workspaceName\"}"
}

##
# When run inside a git repo, forces the most recently active sublime window
# to try to save its current workspace as an EasyWorkspace with the provided
# branch name.
#
# If no branch name is provided, the branch defaults to the current repo HEAD
#
# Arguments:
#   branch-name (optional) - identifies the branch workspace to save as
##
easy_ws_git_save() {
    local workspaceName

    # try to determine the current repo/branch workspace name
    workspaceName=$(easy_ws_git_workspace_name "$1")
    if [ $? -ne 0 ]; then
        return 1
    fi

    # open the easy workspace in sublime
    subl --command "save_as_easy_workspace { \"filename\": \"$workspaceName\"}"
}

##
# Add git autocompletion
##
_git_edit() {
    _git_checkout
}
_git_save() {
    _git_checkout
}
