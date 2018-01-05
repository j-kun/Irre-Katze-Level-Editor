#!/usr/bin/env python

import os.path
import logging

import tkinter_extensions as tkx
tk  = tkx.tk
tkc = tkx.tkc
ttk = tkx.ttk
tkFileDialog = tkx.tkFileDialog
tkMessageBox = tkx.tkMessageBox

import gui_catalog
import gui_image_opener as imageOpener
import gui_board
import gui_log_frame
import gui_solution_view

import model
import model_object_catalog as objects
import model_background_catalog as backgrounds

import settings_manager
settings = settings_manager.settings

import locales
_ = locales._


print(settings_manager.get_fullfilename())

FILETYPES = (
    (_("Aufgaben Datei"), "*"+model.Model.EXT_TASK),
    (_("Alle Dateien"), "*"),
)


class KEY:
    DEFAULT_DIRECTORY_OPEN = 'open-default-directory'
    DEFAULT_FILENAME_OPEN  = 'open-default-filename'
    DEFAULT_DIRECTORY_SAVE = 'save-default-directory'
    DEFAULT_FILENAME_SAVE  = 'save-default-filename'
    DEFAULT_DIRECTORY_EXPORT = 'export-default-directory'
    DEFAULT_FILENAME_EXPORT  = 'export-default-filename'

    VIEW_MOVABILITY_INDICATORS  = 'view-movability-indicators'
    AUTO_TRIGGER_SANITY_CHECK   = 'auto-trigger-sanity-check'

    WIDTH_NOTES = 'width-notes'
    WIDTH_LABEL_INFO = 'width-selection-info'



class MainWindow(tk.Tk):

    titlePattern = _("Irre Katze - Level Editor - {filename}{hasChanged}")

    PAD_X = 5
    PAD_Y = 5


    # ---------- initialization ----------
    
    def __init__(self, model):
        tk.Tk.__init__(self)
        self.model = model
        self.model.addOnChangeListener(self.onModelChange)
        self.initSettings()

        self.cursorManager = tkx.CursorManager(self)

        self.frameMain = tk.Frame()
        self.frameMain.pack(side=tk.LEFT, padx=self.PAD_X, pady=self.PAD_Y)

        self._levelEditorChildPanes = list()
        self._solutionEditorChildPanes = list()

        # catalogs
        self.notebook = ttk.Notebook(self.frameMain)
        #self.notebook.configure(takefocus=False) # only affects tab, makes no difference when clicked on
        self.notebook.pack()
        self.objectCatalogs = list()

        for title, items in objects.categories:
            cat = self.addTab(title, items, imageOpener.getImage, self.onClickObject, appendTo=(self._levelEditorChildPanes,))
            self.objectCatalogs.append(cat)
        
        self.addTab(_("Solution Editor"), gui_solution_view.SOLUTION_ACTIONS, gui_solution_view.iconOpener, self.onClickSolution, appendTo=(self._solutionEditorChildPanes,))
        
        for title, items in backgrounds.categories:
            self.addTab(title, items, imageOpener.getBackground, self.onClickBackground, self.onRightClickBackground, appendTo=(self._levelEditorChildPanes, self._solutionEditorChildPanes))

        for title, widget in self._levelEditorChildPanes:
            self.notebook.add(widget, text=title)

        if settings[KEY.VIEW_MOVABILITY_INDICATORS]:
            self.showMovabilityIndicators(True)

        self.update()

        # board
        self.board = gui_board.Board(master=self.frameMain, model=self.model)
        self.board.addOnObjectCodeChangeListener(self.onObjectCodeChangeListener)
        self.board.pack(expand=tk.YES, fill=tk.X, pady=self.PAD_Y)
        self.board.center()

        # author
        frame = tk.Frame(self.frameMain)
        frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.labelAuthor = tk.Label(frame, anchor=tk.W)
        self.labelAuthor.pack(side=tk.LEFT, expand=True, fill=tk.X)
        #self.labelAuthor.bind('<Button-1>', self.onAuthorClick)
        self.labelAuthor.bind('<Double-Button-1>', self.onAuthorClick)

        # info for selected fields
        self.labelInfo = tk.Label(frame, anchor=tk.E)
        self.labelInfo.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        tkx.add_tooltip(self.labelInfo)

        # incident log
        self.sideFrame = gui_log_frame.LogFrame(self, padx=self.PAD_X, pady=self.PAD_Y, closecommand=self.closeSideFrame, autoReload=settings[KEY.AUTO_TRIGGER_SANITY_CHECK], takefocus=False)
        self.sideFrame.title(_("Sanity Check Incident Log"))
        # (pack happens in self.openSideFrame)

        # notes
        self.frameNotes = tkx.FrameWithTitle(self, padx=self.PAD_X, pady=self.PAD_Y, closecommand=lambda: self.showNotes(False))
        self.frameNotes.title(_("Notes"))
        # (pack happens in self.showNotes)
        self.textNotes = tk.Text(self.frameNotes, width=settings[KEY.WIDTH_NOTES], undo=True)
        self.textNotes.pack(expand=tk.YES, fill=tk.BOTH)
        self.notesActive = False
        self.notesIsMapped = False # self.frameNotes.winfo_ismapped() returned 0 instead of True. wrong timing?
        
        # solution frame
        self.solutionFrame = gui_solution_view.SolutionFrame(self, self.model, padx=self.PAD_X, pady=self.PAD_Y, highlightthickness = 1)
        
        self.model.solution.addOnStepsChangeListener(self.sideFrame.autoReload)
        

        self.createMenuBackgroundUsage()
        self.createMenubar()
        self.onModelChange(model.CHANGE_AUTHOR)

        self.menubar.menu_edit.entryconfigure('mode', label=_("Solution"), command=self.switchModeToSolutionEditor)

        self.solutionFrame.solutionView.bind('<Return>' , lambda e: self.board.enterNewObject())
        self.bind('<Button-1>', self.onClickAnywhere, '+')
        self.board.bind('<Button-1>', self.setReturnFocusToBoard, '+')
        self.board.bind('<FocusIn>',  self.setReturnFocusToBoard, '+')
        self.textNotes.bind('<Button-1>', self.setReturnFocusToNotes, '+')
        self.textNotes.bind('<FocusIn>',  self.setReturnFocusToNotes, '+')
        self.textNotes.bind('<Tab>', lambda event: tkx.only(event.widget.tk_focusNext().focus_set()))
        self.protocol(tkc.WM_DELETE_WINDOW, self.myExit)

    def updateTitle(self):
        self.title(self.titlePattern.format(
            filename = _("<unsaved>") if self.model.getFileName() == None else self.model.getFileName(),
            hasChanged = "*" if self.model.hasChanged() else "",
        ))
        
    def createMenuBackgroundUsage(self):
        menu = tk.Menu(self.notebook, tearoff=False)
        menu.add_command(label=_("Use for Border"), command=lambda: self.model.setBgBorder(self.selectedBackground))
        menu.add_command(label=_("Use for Untouched Fields"), command=lambda: self.model.setBgUntouched(self.selectedBackground))
        menu.add_command(label=_("Use for Touched Fields"), command=lambda: self.model.setBgTouched(self.selectedBackground))
        self.menuBgUsage = menu

    def createMenubar(self):
        self.menubar = tkx.Menu(self)
        self.configure(menu=self.menubar)

        m = self.menubar.add_named_cascade('file', label=_("File"), underline=0)
        m.add_named_command('new', label=_("New"), command=self.newFile, event='<Control-n>')
        m.add_named_command('open', label=_("Open..."), command=self.openFile, event='<Control-o>')
        m.add_named_command('check', label=_("Check"), command=self.sanityCheck, event='<F12>')
        m.add_named_command('save', label=_("Save"), command=self.save, event='<Control-s>')
        m.add_named_command('saveAs', label=_("Save As..."), command=self.saveAs)
        m.add_named_command('saveCopyAs', label=_("Save Copy As..."), command=self.saveCopyAs, event='<Control-S>')

        m = self.menubar.add_named_cascade('edit', label=_("Edit"), underline=0)
        m.add_named_command('mode', event='<F11>')
        m.add_named_checkbutton('autoReloadLog', variable=self.sideFrame.varAutoReload, statevariable=self.sideFrame.varState, label=_("Auto Reload Log"), event='<Control-u>')
        m.add_named_command('settings', label=_("Settings"), command=self.openSettings)

        m = self.menubar.add_named_cascade('view', label=_("View"), underline=0)
        m.add_named_checkbutton('movability-indicators', label=_("Movability Indicators"), command=self.showMovabilityIndicators, value=settings[KEY.VIEW_MOVABILITY_INDICATORS], event='<F3>')
        m.add_named_checkbutton('notes', label=_("Notes"), command=self.showNotes, event='<F10>')
        m.add_named_checkbutton('log', label=_("Sanity Check Incident Log"), command=lambda flag: self.sanityCheck() if flag else self.closeSideFrame())
        

    def addTab(self, title, items, imageOpener, onClick, onRightClick=None, appendTo=list()):
        catalog = gui_catalog.Catalog(self.notebook)
        catalog.setItems(items, imageOpener, onClick, onRightClick)
        #self.notebook.add(catalog, text=title)
        item = (title, catalog)
        for l in appendTo:
            l.append(item)
        
        return catalog


    def initSettings(self):
        settings.setdefault(KEY.DEFAULT_DIRECTORY_OPEN, imageOpener.toAbsPath("level-vorlagen"))
        settings.setdefault(KEY.DEFAULT_FILENAME_OPEN, None)
        settings.setdefault(KEY.DEFAULT_DIRECTORY_SAVE, os.path.expanduser("~"))
        settings.setdefault(KEY.DEFAULT_FILENAME_SAVE, None)
        settings.setdefault(KEY.DEFAULT_DIRECTORY_EXPORT, os.path.expanduser("~"))
        settings.setdefault(KEY.DEFAULT_FILENAME_EXPORT, None)

        settings.setdefault(KEY.VIEW_MOVABILITY_INDICATORS, False)
        settings.setdefault(KEY.AUTO_TRIGGER_SANITY_CHECK, True)
        settings.setdefault(KEY.WIDTH_NOTES, 40)
        settings.setdefault(KEY.WIDTH_LABEL_INFO, 50)
        
        settings.setdefault(settings_manager.KEY.UPDATE_SETTINGS, True)


    # ---------- modes ----------
    
    def switchModeToLevelEditor(self, askUserIfProblemsExist=True):
        # checks
        if self.board.isModeEditLevel():
            return
        if askUserIfProblemsExist and not self.sanityCheckBeforeExitSolutionEditor():
            return

        #print("========== switchModeToLevelEditor ==========")

        # disable last widget
        self.solutionFrame.onHide()
        self.solutionFrame.pack_forget()
        self.closeSideFrame()
        self.model.solution.history.clear()

        # model
        self.board.setMode(self.board.MODE_EDIT_LEVEL)
        self.menubar.menu_edit.entryconfigure('mode', label=_("Solution"), command=self.switchModeToSolutionEditor)

        # catalog
        for title, widget in self._solutionEditorChildPanes:
            self.notebook.forget(widget)
        for title, widget in self._levelEditorChildPanes:
            self.notebook.add(widget, text=title)

        # update new widget
        self.board.onChangeListener(self.model.CHANGE_BOARD)
        self.model.history.makeBackup()

        # sanity check
        if self.implicitSanityCheck() != model.LOGLEVEL_NONE:
            self.openSideFrame()

        # enable new widget
        self.board.widgetToFocus = self.board
        self.board.configure(takefocus = tk.YES)
        self.board.focus_set()
        

    def switchModeToSolutionEditor(self):
        # checks
        if self.board.isModeEditSolution():
            return
        if not self.sanityCheckBeforeOpenSolutionEditor():
            return

        #print("========== switchModeToSolutionEditor ==========")

        # hourglass cursor
        self.cursorManager.set_cursor()

        # disable last widget
        self.board.configure(takefocus = tk.NO)
        self.closeSideFrame()
        self.model.history.clear()

        # model
        self.board.setMode(self.board.MODE_EDIT_SOLUTION)
        self.menubar.menu_edit.entryconfigure('mode', label=_("Level"), command=self.switchModeToLevelEditor)

        # catalog
        for title, widget in self._levelEditorChildPanes:
            self.notebook.forget(widget)
        for title, widget in self._solutionEditorChildPanes:
            self.notebook.add(widget, text=title)

        # update new widget
        self.model.solution.init(self.model)
        self.model.disableNotifications()
        self.model.solution.notifyOnStepsChangedListener()
        self.model.enableNotifications()

        # sanity check
        if self.implicitSanityCheck() != model.LOGLEVEL_NONE:
            self.openSideFrame()

        # enable new widget
        self.board.widgetToFocus = self.solutionFrame
        self.solutionFrame.pack(side=tk.LEFT, anchor=tk.N, padx=self.PAD_X, pady=self.PAD_Y, expand=tk.YES, fill=tk.BOTH)
        self.solutionFrame.onShow()

        # normal cursor
        self.cursorManager.reset_cursor()


    def toggleMode(self):
        if self.board.isModeEditSolution():
            self.switchModeToLevelEditor()
        else:
            self.switchModeToSolutionEditor()


    # ---------- destructor ----------

    def myExit(self):
        self.saveSettings()

        if not self.saveIfUserAgrees():
            return

        if self.board.isModeEditSolution():
            self.solutionFrame.forget()

        # "root.quit() causes mainloop to exit. The interpreter is still intact, as are all the widgets. If you call this function, you can have code that executes after the call to root.mainloop(), and that code can interact with the widgets (for example, get a value from an entry widget).
        # Calling root.destroy() will destroy all the widgets and exit mainloop. Any code after the call to root.mainloop() will run, but any attempt to access any widgets (for example, get a value from an entry widget) will fail because the widget no longer exists."
        # Bryan Oakley, https://stackoverflow.com/a/42928131
        self.destroy()

    def saveSettings(self, force=False):
        if force or settings_manager.are_updates_wanted():
            path = self.model.getFileName()
            if path != None:
                path, fn = os.path.split(path)
                settings[KEY.DEFAULT_DIRECTORY_OPEN] = path
                settings[KEY.DEFAULT_DIRECTORY_SAVE] = path
                settings[KEY.DEFAULT_FILENAME_OPEN]  = fn
                settings[KEY.DEFAULT_FILENAME_SAVE]  = fn
            
            settings[KEY.VIEW_MOVABILITY_INDICATORS] = bool(self.menubar.menu_view.get_named_checkbutton('movability-indicators'))
            settings[KEY.AUTO_TRIGGER_SANITY_CHECK] = bool(self.sideFrame.varAutoReload.get())
        
        settings_manager.save_settings(
            settings = settings,
            force = force,
            ask_overwrite_handler = lambda: tkMessageBox.askyesno(
                title=_("Save Settings?"),
                message=_("You have opened the settings in an external editor. If you have changed the settings there and proceed those changes will be overwritten. Do you want to save the currently active settings?"),
                default=tkMessageBox.NO,
                icon=tkMessageBox.WARNING,
            )
        )

        


    # ---------- model listener ----------

    def onModelChange(self, change):
        model = self.model
        
        self.updateSelectionInfo()
            
        if change in (model.CHANGE_CURSOR,):
            return
        
        if change in (model.CHANGE_AUTHOR, model.CHANGE_ALL):
            tkx.set_text(self.labelAuthor, _("Author: {name}").format(name=model.getAuthor()))
        
        self.updateTitle()

        if change in (model.CHANGE_HAS_CHANGED,):
            return

        self.sideFrame.autoReload()

    def updateSelectionInfo(self):
        info = self.getSelectionInfo()
        tkx.set_text(self.labelInfo.tooltip, _("Selected object: {descr}").format(descr=info))
        
        maxWidth = settings[KEY.WIDTH_LABEL_INFO]
        if len(info) > maxWidth:
            tkx.set_text(self.labelInfo.tooltip, info)
            info = info[:maxWidth-3] + "..."
        else:
            tkx.set_text(self.labelInfo.tooltip, None)
        tkx.set_text(self.labelInfo, _("Selected object: {descr}").format(descr=info))
        

    def getSelectionInfo(self):
        obj = None
        for x, y in self.model.getCursors():
            tmp = self.model.getField(x, y)
            if obj == None:
                obj = tmp
            elif tmp == objects.OBJ_NONE or tmp == obj:
                pass
            elif obj == objects.OBJ_NONE:
                obj = tmp
            else:
                return _("<multiple different objects>")

        if obj == None:
            return _("<none>")
        
        return imageOpener.getImage.getLongName(obj)
    

    # ---------- gui listener ----------

    def onClickObject(self, event, name):
        self.model.setFieldAtCursor(name)

    def onClickBackground(self, event, name):
        if name in backgrounds.CATEGORY_BORDER:
            self.model.setBgBorder(name)
        elif name in backgrounds.CATEGORY_UNTOUCHED:
            self.model.setBgUntouched(name)
        elif name in backgrounds.CATEGORY_TOUCHED:
            self.model.setBgTouched(name)
        else:
            self.selectedBackground = name
            self.menuBgUsage.tk_popup(event.x_root,event.y_root)

    def onClickSolution(self, event, action):
        solution = self.model.getSolution()
        if action == gui_solution_view.SolutionEditor.ACT_STEP_LEFT:
            solution.insertStep(solution.STEP_LEFT)
        elif action == gui_solution_view.SolutionEditor.ACT_STEP_RIGHT:
            solution.insertStep(solution.STEP_RIGHT)
        elif action == gui_solution_view.SolutionEditor.ACT_STEP_UP:
            solution.insertStep(solution.STEP_UP)
        elif action == gui_solution_view.SolutionEditor.ACT_STEP_DOWN:
            solution.insertStep(solution.STEP_DOWN)
        
        elif action == gui_solution_view.SolutionEditor.ACT_JUMP_PIPE:
            self.solutionFrame.solutionView.insertPipeJump()
        elif action == gui_solution_view.SolutionEditor.ACT_JUMP_HELIUM:
            self.solutionFrame.solutionView.insertHeliumJump()

        elif action == gui_solution_view.SolutionEditor.ACT_DELETE_ABOVE:
            solution.deleteStepAbove()
        elif action == gui_solution_view.SolutionEditor.ACT_DELETE_BELOW:
            solution.deleteStepBelow()

        elif action == gui_solution_view.SolutionEditor.ACT_EXIT:
            self.switchModeToLevelEditor()

        else:
            logging.error("action %r not yet implemented" % action)


    def onClickAnywhere(self, event):
        if self.board.isModeEditSolution():
            self.solutionFrame.focus_set()
        else:
            if self.notesActive:
                self.textNotes.focus_set()
            else:
                self.board.focus_set()
    
    
    def onRightClickBackground(self, event, name):
        self.selectedBackground = name
        self.menuBgUsage.tk_popup(event.x_root,event.y_root)

    def onAuthorClick(self, event=None):
        self.board.enterAuthor()


    def onObjectCodeChangeListener(self, newObjectCode):
        if   newObjectCode == self.board.OBJECT_CODE_NUMBER:
            imageOpener.setObjectCodeNumber()
        elif newObjectCode == self.board.OBJECT_CODE_CHAR:
            imageOpener.setObjectCodeCharacter()
        else:
            assert False
        
        for cat in self.objectCatalogs:
            cat.updateShortNames()


    def openSettings(self):
        self.saveSettings()
        settings_manager.open_settings()

    def showMovabilityIndicators(self, flag):
        for cat in self.objectCatalogs:
            cat.showBackground(flag)


    # ---------- save & open ----------

    def newFile(self):
        if not self.saveIfUserAgrees():
            return
        
        self.switchModeToLevelEditor( askUserIfProblemsExist = False )
        self.model.reset()
        self.loadNotes()

    def openFile(self):
        if not self.saveIfUserAgrees():
            return
        
        path = self.model.getFileName()
        if path != None:
            path,fn = os.path.split(path)
        else:
            path = settings[KEY.DEFAULT_DIRECTORY_OPEN]
            fn   = settings[KEY.DEFAULT_FILENAME_OPEN]
        
        ffn = tkFileDialog.askopenfilename(
            title = _("Open"),
            filetypes = FILETYPES,
            initialdir = path,
            initialfile = fn,
        )
        if len(ffn) == 0:
            return

        self.openTheFile(ffn)

    def openTheFile(self, ffn):
        self.switchModeToLevelEditor( askUserIfProblemsExist = False )
        msgs = list()
        lv = self.model.readFile(ffn, log=lambda lv, msg: msgs.append(msg))
        self.loadNotes()
        if lv >= logging.WARNING:
            tkMessageBox.showwarning(
                title = _("Problems while trying to load file"),
                message = _("Problems have occured while trying to read the file {ffn!r}.").format(ffn=ffn),
                detail  = "\n".join("- "+msg for msg in msgs),
            )
        
        if self.implicitSanityCheck() != model.LOGLEVEL_NONE:
            self.openSideFrame()


    def saveIfUserAgrees(self):
        """returns true if user has made a decision whether the level shall be changed and the appropriate action has been performed. returns false on cancel."""
        if not self.model.hasChanged() and not self.notesHaveChanged():
            return True
        
        choice = tkMessageBox.askyesnocancel(
            title = _("Save Changes?"),
            message = _("Do you want to save changes?"),
            default = tkMessageBox.YES,
        )
        if choice == None:
            return False
        if choice:
            return self.save()
        else:
            return True


    def save(self):
        if not self.sanityCheckBeforeSave():
            return False
        return self.saveWithoutCheck()

    def saveAs(self):
        if not self.sanityCheckBeforeSave():
            return False
        return self.saveAsWithoutCheck()

    def saveCopyAs(self):
        if not self.sanityCheckBeforeSave():
            return False
        return self.saveCopyAsWithoutCheck()

        
    def saveWithoutCheck(self):
        ffn = self.model.getFileName()
        if ffn == None:
            logging.warning(_("I don't know a filename yet"))
            return self.saveAsWithoutCheck()
        
        if not os.path.isfile(ffn):
            reply = tkMessageBox.askyesnocancel(
                title = _("Save with same name?"),
                message = _("The file \"{fn}\" does not exist anymore. Are you sure you want to use this name?").format(fn=ffn),
                default = tkMessageBox.NO,
                icon = tkMessageBox.WARNING,
            )
            if reply == None: # cancel
                return False
            if not reply:
                return self.saveAsWithoutCheck()
        
        return self._save(ffn)
    
    def saveAsWithoutCheck(self):
        path = self.model.getFileName()
        if path != None:
            path, fn = os.path.split(path)
        else:
            path = settings[KEY.DEFAULT_DIRECTORY_SAVE]
            fn   = settings[KEY.DEFAULT_FILENAME_SAVE]
        
        ffn = tkFileDialog.asksaveasfilename(
            title = _("Save"),
            filetypes = FILETYPES,
            defaultextension = model.Model.EXT_TASK,
            initialdir = path,
            initialfile = fn,
        )
        if len(ffn) == 0:
            return False
        
        return self._save(ffn)

    def saveCopyAsWithoutCheck(self):
        path = self.model.getFileName()
        if path != None:
            path, fn = os.path.split(path)
        else:
            fn   = settings[KEY.DEFAULT_FILENAME_EXPORT]
        path = settings[KEY.DEFAULT_DIRECTORY_EXPORT]
        
        ffn = tkFileDialog.asksaveasfilename(
            title = _("Save Copy"),
            filetypes = FILETYPES,
            defaultextension = model.Model.EXT_TASK,
            initialdir = path,
            initialfile = fn,
        )
        if len(ffn) == 0:
            return False

        path, fn = os.path.split(ffn)
        settings[KEY.DEFAULT_DIRECTORY_EXPORT] = path
        settings[KEY.DEFAULT_FILENAME_EXPORT]  = fn
        
        return self._save(ffn, update=False)
    

    def _save(self, ffn, update=True):
        try:
            if update:
                self.saveNotes()
                self.model.writeFile(ffn)
            else:
                self.model.writeCopy(ffn)
            return True
        except IOError as e:
            logging.error(_("Failed to write to {fn}").format(fn=ffn), exc_info=True)
            tkMessageBox.showerror(
                title = _("Failed to save"),
                message = _("Failed to write file '{fn}'.").format(fn=ffn),
            )
            return self.saveAs()


    # ---------- sanity check ----------

    MSG_LEVEL_CONTAINS_PROBLEMS = _("The level contains problems and won't work as is. Please see '{logName}' for more details.") + "\n\n"
    MSG_LEVEL_CONTAINS_WARNINGS = _("The level has warnings. Please see '{logName}' for more details.") + "\n\n"

    MSG_SOLUTION_CONTAINS_PROBLEMS = _("The solution contains problems and won't work as is. Please see '{logName}' for more details.") + "\n\n"
    MSG_SOLUTION_CONTAINS_WARNINGS = _("The solution has warnings. Please see '{logName}' for more details.") + "\n\n"

    def sanityCheckBeforeSave(self):
        logLevel = self.implicitSanityCheck()

        QST_SAVE_ANYWAY = _("Do you want to save the file anyway?")
        
        if logLevel >= logging.ERROR:
            self.openSideFrame()
            if self.board.isModeEditSolution():
                MSG_PROBLEMS = self.MSG_SOLUTION_CONTAINS_PROBLEMS
            else:
                MSG_PROBLEMS = self.MSG_LEVEL_CONTAINS_PROBLEMS
            
            choice = tkMessageBox.askyesnocancel(
                title = _("Save Changes despite Problems?"),
                message = MSG_PROBLEMS.format(logName=self.sideFrame.getTitle()) + QST_SAVE_ANYWAY,
                default = tkMessageBox.YES,
            )

        elif logLevel >= logging.WARNING:
            self.openSideFrame()
            if self.board.isModeEditSolution():
                MSG_WARNINGS = self.MSG_SOLUTION_CONTAINS_WARNINGS
            else:
                MSG_WARNINGS = self.MSG_LEVEL_CONTAINS_WARNINGS
            
            choice = tkMessageBox.askyesnocancel(
                title = _("Save Changes despite Warnings?"),
                message = MSG_WARNINGS.format(logName=self.sideFrame.getTitle()) + QST_SAVE_ANYWAY,
                default = tkMessageBox.YES,
            )

        else:
            return True
            
        if choice == None:
            # cancel
            return False
        if choice:
            # yes
            return True
        else:
            # no
            return False


    def sanityCheckBeforeOpenSolutionEditor(self):
        logLevel = self.performChecks(
            self.model.sanityCheckBoard,
        )
        
        if logLevel >= logging.ERROR:
            self.openSideFrame()
            tkMessageBox.showerror(
                title = _("Level contains problems"),
                message = self.MSG_LEVEL_CONTAINS_PROBLEMS.format(logName=self.sideFrame.getTitle()) + _("Please resolve the problems before creating/editing a solution for this level."),
            )
            return False
        
        elif logLevel >= logging.WARNING:
            self.openSideFrame()
            tkMessageBox.showerror(
                title = _("Level has warnings"),
                message = self.MSG_LEVEL_CONTAINS_WARNINGS.format(logName=self.sideFrame.getTitle()) + _("Please resolve the warnings before creating/editing a solution for this level."),
            )
            return False
        
        else:
            return True


    def sanityCheckBeforeExitSolutionEditor(self):
        logLevel = self.performChecks(
            self.model.sanityCheckSolution,
        )
        
        if logLevel >= logging.ERROR:
            self.openSideFrame()
            choice = tkMessageBox.askyesnocancel(
                title = _("Solution contains problems"),
                message = self.MSG_SOLUTION_CONTAINS_PROBLEMS.format(logName=self.sideFrame.getTitle()) + _("Do you want to exit the solution editor anyway?"),
                default = tkMessageBox.NO,
            )
        
        elif logLevel >= logging.WARNING:
            self.openSideFrame()
            choice = tkMessageBox.askyesnocancel(
                title = _("Solution has warnings"),
                message = self.MSG_SOLUTION_CONTAINS_WARNINGS.format(logName=self.sideFrame.getTitle()) + _("Do you want to exit the solution editor anyway?"),
                default = tkMessageBox.NO,
            )
        
        else:
            return True

        if choice == None:
            # cancel
            return False
        if choice:
            # yes
            return True
        else:
            # no
            return False
    

    def sanityCheck(self):
        logLevel = self.implicitSanityCheck()

        self.openSideFrame()
        
        if logLevel != model.LOGLEVEL_NONE:
            return True
        
        return False


    def implicitSanityCheck(self):
        if self.board.isModeEditSolution():
            return self.performChecks(
                self.model.sanityCheckSolution,
                self.model.sanityCheckBackgrounds,
                self.model.sanityCheckAuthor,
            )
        else:
            return self.performChecks(
                self.model.sanityCheckBoard,
                self.model.sanityCheckSolutionUpdated,
                self.model.sanityCheckBackgrounds,
                self.model.sanityCheckAuthor,
            )
        
    
    def performChecks(self, *checks):
        assert len(checks) > 0
        self.sideFrame.clear()
        self.sideFrame.setReloadCommand(lambda: self.performChecks(*checks))
        out = model.LOGLEVEL_NONE
        for check in checks:
            out = max(out, check(self.sideFrame.addMessage))
        self.sideFrame.complete()
        return out

    def openSideFrame(self):
        self.sideFrame.pack(side=tk.RIGHT, anchor=tk.N, padx=self.PAD_X, pady=self.PAD_Y, expand=tk.YES, fill=tk.BOTH)
        self.menubar.menu_view.set_named_checkbutton('log', True)

    def closeSideFrame(self):
        self.sideFrame.pack_forget()
        self.menubar.menu_view.set_named_checkbutton('log', False)


    # ---------- notes ----------

    def showNotes(self, flag, setFocus=True):
        if flag == self.notesIsMapped:
            return
        
        if flag:
            self.frameNotes.pack(side=tk.RIGHT, anchor=tk.N, padx=self.PAD_X, pady=self.PAD_Y, expand=tk.YES, fill=tk.BOTH)
            self.notesIsMapped = True
            if setFocus:
                self.textNotes.focus_set()
        else:
            self.frameNotes.pack_forget()
            self.notesIsMapped = False
            self.board.focus_set()
        self.menubar.menu_view.set_named_checkbutton('notes', flag)

    def setReturnFocusToBoard(self, event=None):
        self.notesActive = False
    
    def setReturnFocusToNotes(self, event=None):
        self.notesActive = True
    

    def saveNotes(self):
        self.model.setNotes( self.getCurrentNotes() )
    
    def getCurrentNotes(self):
        notes = tkx.get_text(self.textNotes)
        notes = notes.rstrip() # model strips whitespace from end of notes when reading a file, too. therefore it makes no sense to ask whether this shall be saved.
        if notes == "":
            return None
        else:
            return notes

    def loadNotes(self):
        notes = self.model.getNotes()
        if notes == None:
            tkx.set_text(self.textNotes, "")
        else:
            tkx.set_text(self.textNotes, notes)
            self.showNotes(True, setFocus=False)

    def notesHaveChanged(self):
        savedNotes = self.model.getNotes()
        currentNotes = self.getCurrentNotes()
        return savedNotes != currentNotes


if __name__=='__main__':
    import sys
    error = logging.error

    def printUsage():
        error("usage:")
        error("%s [level.afg]" % (sys.argv[0],))
    
    m = model.Model()
    w = MainWindow(model=m)

    numberArguments = len(sys.argv) - 1 
    if numberArguments > 1:
        error("too many command line arguments given")
        error(repr(sys.argv))
        printUsage()
    elif numberArguments == 1:
        fn = sys.argv[1]
        fn = os.path.abspath(fn)
        w.openTheFile(fn)
    
    w.mainloop()
