#!/usr/bin/env python

"""A sublime-text plugin for saving and loading easy workspaces

This module contains code for the sublime-text plugin EasyWorkspace.

EasyWorkspace aims to provide an easier way for saving and loading workspaces
in sublime-text. The native sublime-text workspace functionality, while useful in
some situations, has a few drawbacks that this plugin wishes to alleviate.

Particularly, EasyWorkspace provides the following features:

    1. Save and Load your current workspace!
        - save your window folders, layout, and views with a quick key command!

    2. No need for a sublime project!
        - While native sublime-workspace support requires you to be working
        within a sublime-project, EasyWorkspace does not!

    2. Simpler Files
        - An EasyWorkspace workspace file only contains a window layout and a series
        of views within each. That's it!

"""

################################################################################
# Imports

import sublime
import sublime_plugin

import os
import datetime
import time

################################################################################
# Workspace Data
################################################################################

class EasyWorkspace:
    """ represents an easy workspace """

    def __init__(self):
        self.layout  = dict(rows=[0.0, 1.0], cells=[[0, 0, 1, 1]], cols=[0.0, 1.0])
        self.folders = []
        self.active  = ()
        self.groups  = []

        self.filename = ""

    ############################################################################
    # File IO

    def saveToFile(self, filename):
        """ Saves this workspace to a file

        Arguments:
            filename -- the workspace file to write

        Returns: true if file was saved, false otherwise
        """

        # ensure path exists
        fileDir = os.path.dirname(filename)
        if not os.path.isdir(fileDir):
            os.makedirs(fileDir)

        # write the file
        with open(filename, 'w') as f:
            wsJSON = sublime.encode_value(vars(self), True)
            f.write(wsJSON)

            self.filename = filename


    def loadFromFile(self, filename):
        """ Loads a workspace from a file

        Arguments:
            filename -- the workspace file to load
        """

        # open file
        wsJSON = ""
        try:
            with open(filename) as f:
                wsJSON = f.read()
                self.buildFromJSON(sublime.decode_value(wsJSON))

        except FileNotFoundError:
            sublime.status_message("File {} does not exist. Opening as New Workspace.".format(filename))

        self.filename = filename


    ############################################################################
    # Operations

    def buildFromWindow(self, window):
        """ Populates this workspace data from a sublime-text window

        Arguments:
            window -- the window to populate from
        """

        # save the layout
        self.layout  = window.layout()
        self.folders = window.folders()
        self.active  = window.get_view_index(window.active_view())

        # iterate over all groups
        for i in range(window.num_groups()):
            sViews      = window.views_in_group(i)
            activeSView = window.active_view_in_group(i)

            # create the group
            group = dict()
            group['active'] = sViews.index(activeSView) if sViews else 0
            group['views']  = []

            # fill with views
            for sView in sViews:
                # ignore any temporary or unsaved views
                fileExistsOnDisk = sView.file_name()
                if not fileExistsOnDisk:
                    continue

                view = dict()

                view['file']      = sView.file_name()
                view['visible']   = (sView.visible_region().a, sView.visible_region().b)
                view['selection'] = (sView.sel()[0].a, sView.sel()[0].b)
                view['read_only'] = sView.is_read_only()

                group['views'].append(view)

            self.groups.append(group)

    def applyToWindow(self, window):
        """ Opens this workspace in the provided sublime-text window

        Arguments:
            window - window in which to open the easy workspace (will close existing files)
        """
        settings = sublime.load_settings("EasyWorkspace.sublime-settings")

        # make sure the window is empty
        window.run_command("close_all")
        window.run_command("close_folder_list")

        # open layout
        window.set_layout(self.layout)

        # open folders
        for folder in self.folders:
            self.__openFolderInWindow(window, folder)

        # open views
        for i, group in enumerate(self.groups):
            for j, view in enumerate(group['views']):

                # open the file and set group properly
                sView = window.open_file(view['file'])
                window.set_view_index(sView, i, j)

                # add slight delay to ensure view is fully opened
                # and ready to have 'visible'/'selection' modified
                time.sleep(0.05)

                # set view attributes, region and selection
                sView.set_read_only(view.get('read_only', False))

                # when setting the visible region, we want the top of the
                # view to match saved workspace. We achieve this by showing
                # bottom, then top of view region.
                if settings.get("easy_ws_read_view_region", False):
                    r = sublime.Region(*view['visible'])
                    sView.show(r.end(),   False)
                    sView.show(r.begin(), False)

                if settings.get("easy_ws_read_view_selection", False):
                    sView.sel().add(sublime.Region(*view['selection']))

        # set active views per group

        for i, group in enumerate(self.groups):
            if group['active']:
                window.focus_view(window.views_in_group(i)[group['active']])
        if self.active:
            window.focus_group(self.active[0])

        # all done

        sublime.status_message("Opened " + self.filename)

    def buildFromJSON(self, json):
        """ Constructs a workspace from a provided JSON string

        Arguments:
            json -- the JSON string representation of a workspace
        """
        self.layout  = json['layout']
        self.folders = json['folders']
        self.active  = json['active']
        self.groups  = json['groups']

        return self

    ############################################################################

    def __openFolderInWindow(self, window, folder):
        """ opens a folder in the provided sublime text window

        Arguments:
            window - where the folder should be opened
            folder - the folder path to open
        """
        if not (window and folder and os.path.isdir(folder)):
            return

        # get current folders list
        project_data = window.project_data() if window.project_data() else {'folders': []}
        folder = os.path.normpath(folder)

        # check if it already exists
        for f in project_data['folders']:
            if f['path'] and folder == f['path']:
                return # already exists

        # create folder data
        folder_struct = { 'path': folder, 'follow_symlinks': True }

        # add folder data to window
        project_data['folders'].append(folder_struct)
        window.set_project_data(project_data)


################################################################################
# Plugin Commands
################################################################################

class EasyWorkspaceCommand:
    """ An interface for easy workspace commands """

    # shared dictionary which stores the currently open workspace file for each
    # open window in sublime
    _openWorkspaceFiles = dict()

    # store the last workspace to reopen as needed
    _reopenWorkspace = ""

    def run(self, **kwargs):
        """ runs a command and garbage collects openWorkspaceFiles """
        self.__garbageCollectOpenWorkspaceFiles()

    ############################################################################

    def __garbageCollectOpenWorkspaceFiles(self):
        """ removes all closed window ids from our shared state data """
        openIds    = [window.id() for window in sublime.windows()]
        invalidIds = [wid for wid in self._openWorkspaceFiles if wid not in openIds]
        for wid in invalidIds:
            del self._openWorkspaceFiles[wid]


    ############################################################################

    def getWorkspacesDir(self):
        """ returns the EasyWorkspace workspaces directory from settings """
        settings = sublime.load_settings("EasyWorkspace.sublime-settings")
        wsFolder = settings.get("easy_ws_save_directory", "EasyWorkspace/workspaces")
        return os.path.join(sublime.packages_path(), wsFolder + os.path.sep)

    def getWorkspaceFilepath(self, filename):
        """ Resolves a filename into its full easyworkspace path,
            including directory and extension

        Arguments:
            filename - the filename to resolve as full workspace file
        """
        settings = sublime.load_settings("EasyWorkspace.sublime-settings")

        workspacesDir = self.getWorkspacesDir()
        baseName, extension = os.path.splitext(filename)
        if not extension:
            extension = settings.get('easy_ws_file_extension', '.ws')
        return os.path.join(workspacesDir, baseName+extension)

    def getAllWorkspaceFiles(self):
        """ returns a list of all easy workspace files """
        workspacesDir  = self.getWorkspacesDir()
        workspaceFiles = []
        for root, dirs, files in os.walk(workspacesDir):
            for file in files:
                # ignore any hidden files
                if file.startswith('.'):
                    continue

                # trim base workspace directory for display
                subdir = root[len(workspacesDir):]
                workspaceFiles.append(os.path.join(subdir, file))

        return workspaceFiles

################################################################################

class SaveEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which saves an easy workspace """

    def run(self, **kwargs):
        """ Save this window's workspace

        Keyword Arguments:
            filename        = workspace file to save
            promptOverwrite = indicates if we should prompt before overwriting a file
            promptSave      = indicates if we should prompt before saving a new file
        """
        super().run(**kwargs)

        # are we saving a new workspace?
        isNewWorkspace = self.window.id() not in EasyWorkspaceCommand._openWorkspaceFiles
        noFileProvided = kwargs.get('filename', None) == None

        if isNewWorkspace and noFileProvided:
            # use save-as to get the filename!
            self.window.run_command("save_as_easy_workspace", kwargs)

        else:
            self.window.status_message("Saving workspace...")

            ws = EasyWorkspace()
            ws.buildFromWindow(self.window)

            # resolve the full filepath
            fullFilePath = self.getWorkspaceFilepath(kwargs.get('filename', EasyWorkspaceCommand._openWorkspaceFiles.get(self.window.id())))

            # prompt for overwrite or create new
            doSaveDialogResult = sublime.DIALOG_YES
            if (kwargs.get("promptOverwrite", False) and os.path.isfile(fullFilePath)):
                doSaveDialogResult = sublime.yes_no_cancel_dialog("Overwrite Easy Workspace?\n\n{}".format(fullFilePath))
            elif (kwargs.get("promptSave", False)):
                doSaveDialogResult = sublime.yes_no_cancel_dialog("Save New Workspace?\n\n{}".format(fullFilePath))

            # save if not cancelled
            if doSaveDialogResult != sublime.DIALOG_YES:
                self.window.status_message("Canceled")
            else:
                ws.saveToFile(fullFilePath)
                EasyWorkspaceCommand._openWorkspaceFiles[self.window.id()] = fullFilePath
                self.window.status_message("Saved " + fullFilePath)


################################################################################

class SaveAsEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which saves an easy workspace """

    def run(self, **kwargs):
        """ Save this window's workspace, prompt for filename if necessary

        Arguments:
            filename - if present, will save directly to the provided filename
                       without prompting
        """
        super().run(**kwargs)

        # where do we want to save?
        if kwargs.get("filename", None):
            self.onUserEntersFilename(kwargs.get("filename"))
        else:
            self.window.show_input_panel("Save Workspace:",
                                         "",
                                         self.onUserEntersFilename,
                                         None,
                                         None)

    def onUserEntersFilename(self, filename):
        """ callback when user enters the filename via the input dialog

        Arguments:
            filename -- text user entered for filename
        """
        userCanceled = filename is None
        if userCanceled:
            self.window.status_message("Canceled")
        else:
            self.window.run_command("save_easy_workspace", dict(filename=filename, promptOverwrite=True))


################################################################################

class OpenEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which opens an easy workspace """

    def run(self, **kwargs):
        """ Opens an easy workspace and may prompt user to choose which

        * if the current window is empty, will open the workspace in the current window
        * otherwise, the workspace will be opened in a new window

        Arguments:
            filename - identifies which workspace to open directly
        """
        super().run(**kwargs)

        sublime.status_message("Opening workspace...")

        # prompt for filename if needed
        filename = kwargs.get('filename', None)
        if not filename:
            # prompt the user for the filename
            # the callback will return to this function from the top with
            # filename specified
            self.promptUserForFilename()
            return

        # open in current or new window as needed
        targetWindow = self.window if self.windowEmpty() else self.openNewWindow()

        # build and open the workspace
        fullFilePath = self.getWorkspaceFilepath(filename)

        ws = EasyWorkspace()
        ws.loadFromFile(fullFilePath)
        ws.applyToWindow(targetWindow)

        EasyWorkspaceCommand._openWorkspaceFiles[targetWindow.id()] = fullFilePath

        sublime.status_message("Opened {}".format(fullFilePath))

    def promptUserForFilename(self):
        """ prompts a user to select an easyworkspace file from the workspace directory """
        workspaceFiles = self.getAllWorkspaceFiles()

        # create callback
        def onWorkspaceFileSelected(index):
            noSelection = index < 0
            if noSelection:
                self.window.status_message("Canceled")
            else:
                # rerun the open command with file specified
                self.window.run_command("open_easy_workspace", dict(filename=workspaceFiles[index]))
        self.window.show_quick_panel(workspaceFiles, onWorkspaceFileSelected)

    def windowEmpty(self):
        """ returns true if this command's sublime window is empty """
        return len(self.window.views()) == len(self.window.folders()) == 0

    def openNewWindow(self):
        """ opens a new sublime window and returns the resulting handle """
        preWindows = sublime.windows()
        sublime.run_command("new_window")
        newWindow = [window for window in sublime.windows() if not window in preWindows][0]
        return newWindow


################################################################################

class DeleteEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which allows a user to delete a workspace """

    def run(self, **kwargs):
        """ Delete an easy workspace """
        super().run(**kwargs)

        # get list of all saved workspaces
        workspaceFiles = self.getAllWorkspaceFiles()

        def onWorkspaceFileSelected(index):
            noSelection = index < 0
            if noSelection:
                self.window.status_message("Canceled")
            else:
                fullFilePath = self.getWorkspaceFilepath(workspaceFiles[index])

                # are we sure we want to delete?
                if sublime.yes_no_cancel_dialog("Delete Workspace {}?".format(fullFilePath)) == sublime.DIALOG_YES:
                    os.remove(fullFilePath)
                    self.window.status_message("Deleted")
                else:
                    self.window.status_message("Canceled")

        # display list to user
        self.window.status_message("Deleting workspace...")
        self.window.show_quick_panel(workspaceFiles, onWorkspaceFileSelected)


################################################################################

class ShowOpenedEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which shows the user this window's current opened workspace """

    def run(self, **kwargs):
        """ Show the opened easy workspace """
        super().run(**kwargs)

        # get open workspace files relative to workspaces directory
        openWorkspaces = {k:v.replace(self.getWorkspacesDir(), "") for k,v in EasyWorkspaceCommand._openWorkspaceFiles.items()}

        # prepend an "*" to our window's open workspace if applicable
        if self.window.id() in openWorkspaces:
            openWorkspaces[self.window.id()] = " * " + openWorkspaces[self.window.id()]

        # show the open workspaces
        self.window.show_quick_panel(list(openWorkspaces.values()), None)

################################################################################

class ReopenLastEasyWorkspaceCommand(EasyWorkspaceCommand, sublime_plugin.WindowCommand):
    """ A sublime window command which reopens the last easy workspace """

    def run(self, **kwargs):
        """ Reopen the last easy workspace """
        super().run(**kwargs)

        if EasyWorkspaceCommand._reopenWorkspace and os.path.isfile(EasyWorkspaceCommand._reopenWorkspace):
            self.window.run_command("open_easy_workspace", dict(filename=EasyWorkspaceCommand._reopenWorkspace))
        else:
            self.window.status_message("Unable to Reopen Workspace " + EasyWorkspaceCommand._reopenWorkspace)

################################################################################
# Plugin Listeners
################################################################################

class AutoSaveEasyWorkspace(EasyWorkspaceCommand, sublime_plugin.EventListener):
    """ plugin class which autosaves easy workspaces as needed """

    def on_window_command(self, window, command_name, args):
        """ saves the current easy workspace if the user closes part of it """
        settings = sublime.load_settings("EasyWorkspace.sublime-settings")

        # should we autosave?
        usingEasyWs = window.id() in EasyWorkspaceCommand._openWorkspaceFiles
        saveEnabled = settings.get('easy_ws_save_on', False)
        if not (usingEasyWs and saveEnabled):
            return

        #
        # certain commands will prompt EasyWorkspace to autosave the current workspace
        # the following lists highlight these commands, and are ordered for easy
        # comparison of command-setting
        #
        # these commands are considered to 'close' the workspace, and will also
        # store the current workspace to be reopened via the OpenLastWorkspace command
        #
        commandsThatCloseWorkspace = ["close_folder_list", "close_project",
                                      "prompt_open_project_or_workspace",
                                      "prompt_switch_project_or_workspace",
                                      "prompt_select_workspace",
                                      "close_all", "close_window"]

        if command_name in commandsThatCloseWorkspace:
            EasyWorkspaceCommand._reopenWorkspace = EasyWorkspaceCommand._openWorkspaceFiles[window.id()]

            # Are autosave settings enabled for this command?
            autosaveSettingName = "easy_ws_save_on_" + command_name
            if settings.get(autosaveSettingName, False):
                result = window.run_command("save_easy_workspace", dict(promptOverwrite=True, promptSave=True))
