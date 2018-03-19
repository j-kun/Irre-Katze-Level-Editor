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

    ASK_BEFORE_SAVE       = 'check-and-ask-if-wrong-before-save'
    ASK_BEFORE_SAVE_AS    = 'check-and-ask-if-wrong-before-save-as'
    ASK_BEFORE_SAVE_COPY  = 'check-and-ask-if-wrong-before-save-copy'
    CHECK_AFTER_SAVE      = 'check-after-save'
    CHECK_AFTER_SAVE_AS   = 'check-after-save-as'
    CHECK_AFTER_SAVE_COPY = 'check-after-save-copy'

    COLOR_BG          = 'color-background'
    COLOR_BG_SELECTED = 'color-background-selected'
    COLOR_BG_ACTIVE   = 'color-background-active'
    COLOR_BG_ENTRY    = 'color-background-entry'
    COLOR_BG_SOLUTION_SELECTION     = 'color-background-solution-selection'

    COLOR_BORDER_SOLUTION_SELECTION = 'color-border-solution-selection'
    COLOR_HIGHLIGHT   = 'color-border-highlight'

    COLOR_TEXT          = 'color-text'
    COLOR_TEXT_SELECTED = 'color-text-selected'
    COLOR_TEXT_ACTIVE   = 'color-text-active'
    COLOR_TEXT_ENTRY    = 'color-text-entry'
    COLOR_TEXT_SUCCESS  = 'color-text-log-success'
    COLOR_TEXT_WARNING  = 'color-text-log-warning'
    COLOR_TEXT_ERROR    = 'color-text-log-error'
    COLOR_TEXT_COR_UNSELECTED         = 'color-text-solution-coordinate'
    COLOR_TEXT_COR_SELECTED           = 'color-text-solution-coordinate-selected'
    COLOR_TEXT_COR_INVALID_UNSELECTED = 'color-text-solution-coordinate-invalid'
    COLOR_TEXT_COR_INVALID_SELECTED   = 'color-text-solution-coordinate-invalid-selected'

    CURSOR_BORDER_WIDTH = 'cursor-normal-border-width'
    CURSOR_BORDER_COLOR = 'cursor-normal-border-color'
    CURSOR_FILL_COLOR   = 'cursor-normal-fill-color'
    CURSOR_FILL_STIPPLE = 'cursor-normal-fill-stipple'

    CURSOR_LAST_BORDER_WIDTH = 'cursor-last-border-width'
    CURSOR_LAST_BORDER_COLOR = 'cursor-last-border-color'
    CURSOR_LAST_FILL_COLOR   = 'cursor-last-fill-color'
    CURSOR_LAST_FILL_STIPPLE = 'cursor-last-fill-stipple'

    CURSOR_VIRTUAL_BORDER_WIDTH = 'cursor-virtual-border-width'
    CURSOR_VIRTUAL_BORDER_COLOR = 'cursor-virtual-border-color'
    CURSOR_VIRTUAL_FILL_COLOR   = 'cursor-virtual-fill-color'
    CURSOR_VIRTUAL_FILL_STIPPLE = 'cursor-virtual-fill-stipple'
    
    CURSOR_IS_TEXT_FG_COLOR_DOMINANT = 'cursor-is-overlay-text-color-dominant'
    CURSOR_IS_TEXT_BG_COLOR_DOMINANT = 'cursor-is-overlay-text-background-color-dominant'
    CURSOR_IS_TEXT_BG_STIPPLE_DOMINANT = 'cursor-is-overlay-text-background-stipple-dominant'

    OVERLAY_TEXT_FG_COLOR   = 'overlay-text-color'
    OVERLAY_TEXT_BG_COLOR   = 'overlay-text-background-color'
    OVERLAY_TEXT_BG_STIPPLE = 'overlay-text-background-stipple'

    WIDTH_NOTES = 'width-notes'
    WIDTH_LABEL_INFO = 'width-selection-info'
    
    SELECTION_INFO_PATTERN         = 'statusbar-selection-info-pattern'
    SELECTION_INFO_PROP_PATTERN    = 'statusbar-selection-info-property-pattern'
    SELECTION_INFO_PROP_SEP        = 'statusbar-selection-info-property-separator'
    SELECTION_INFO_TOOLTIP_PATTERN      = 'statusbar-selection-info-tooltip-pattern'
    SELECTION_INFO_TOOLTIP_PROP_PATTERN = 'statusbar-selection-info-tooltip-property-pattern'
    SELECTION_INFO_TOOLTIP_PROP_SEP     = 'statusbar-selection-info-tooltip-property-separator'
    SELECTION_INFO_TOOLTIP_ALWAYS  = 'statusbar-selection-info-tooltip-always'

    OBJECT_DESCRIPTION_FORMAT          = 'object-description-format'
    OBJECT_DESCRIPTION_PROPERTY_SEP    = 'object-description-property-separator'
    OBJECT_DESCRIPTION_PROPERTY_FORMAT = 'object-description-property-format'



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
        self.frameMain.pack(side=tk.LEFT, padx=self.PAD_X, pady=self.PAD_Y, anchor=tkc.N)

        self._levelEditorChildPanes = list()
        self._solutionEditorChildPanes = list()

        # catalogs
        self.notebook = ttk.Notebook(self.frameMain, style='TNotebook')
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
        self.applySettings()

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
        m.add_named_command('undo', label=_("Undo"), command=self.model.undo, event='<Control-z>')
        m.add_named_command('redo', label=_("Redo"), command=self.model.redo, event='<Control-Z>')
        m.add_named_command('mode', event='<F11>')
        m.add_separator()
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

        settings.setdefault(KEY.ASK_BEFORE_SAVE,      False)
        settings.setdefault(KEY.ASK_BEFORE_SAVE_AS,   False)
        settings.setdefault(KEY.ASK_BEFORE_SAVE_COPY, False)

        # will only be checked if ASK_BEFORE_SAVE settings are deactivated
        # so these can be activated without the risk of double checking due to the above settings
        settings.setdefault(KEY.CHECK_AFTER_SAVE,      True)
        settings.setdefault(KEY.CHECK_AFTER_SAVE_AS,   True)
        settings.setdefault(KEY.CHECK_AFTER_SAVE_COPY, True)

        settings.setdefault(KEY.COLOR_BG,          None)
        settings.setdefault(KEY.COLOR_BG_SELECTED, None)
        settings.setdefault(KEY.COLOR_BG_ACTIVE,   None)
        settings.setdefault(KEY.COLOR_BG_ENTRY,    None)
        settings.setdefault(KEY.COLOR_BG_SOLUTION_SELECTION,     '#D1E3F5')

        settings.setdefault(KEY.COLOR_BORDER_SOLUTION_SELECTION, '#4A90D9')
        settings.setdefault(KEY.COLOR_HIGHLIGHT,   None)

        settings.setdefault(KEY.COLOR_TEXT,          None)
        settings.setdefault(KEY.COLOR_TEXT_SELECTED, None)
        settings.setdefault(KEY.COLOR_TEXT_ACTIVE,   None)
        settings.setdefault(KEY.COLOR_TEXT_ENTRY,    None)
        settings.setdefault(KEY.COLOR_TEXT_SUCCESS,  'green')
        settings.setdefault(KEY.COLOR_TEXT_WARNING,  'orange')
        settings.setdefault(KEY.COLOR_TEXT_ERROR,    'red')
        settings.setdefault(KEY.COLOR_TEXT_COR_UNSELECTED,         'gray')
        settings.setdefault(KEY.COLOR_TEXT_COR_SELECTED,           None)
        settings.setdefault(KEY.COLOR_TEXT_COR_INVALID_UNSELECTED, 'orange')
        settings.setdefault(KEY.COLOR_TEXT_COR_INVALID_SELECTED,   'red')

        settings.setdefault(KEY.CURSOR_BORDER_WIDTH, gui_board.Board.cursorWidth)
        settings.setdefault(KEY.CURSOR_BORDER_COLOR, gui_board.Board.cursorColor)
        settings.setdefault(KEY.CURSOR_FILL_COLOR  , gui_board.Board.cursorFill)
        settings.setdefault(KEY.CURSOR_FILL_STIPPLE, gui_board.Board.cursorStipple)

        settings.setdefault(KEY.CURSOR_LAST_BORDER_WIDTH, gui_board.Board.lastCursorWidth)
        settings.setdefault(KEY.CURSOR_LAST_BORDER_COLOR, gui_board.Board.lastCursorColor)
        settings.setdefault(KEY.CURSOR_LAST_FILL_COLOR  , gui_board.Board.lastCursorFill)
        settings.setdefault(KEY.CURSOR_LAST_FILL_STIPPLE, gui_board.Board.lastCursorStipple)

        settings.setdefault(KEY.CURSOR_VIRTUAL_BORDER_WIDTH, gui_board.Board.virtualCursorWidth)
        settings.setdefault(KEY.CURSOR_VIRTUAL_BORDER_COLOR, gui_board.Board.virtualCursorColor)
        settings.setdefault(KEY.CURSOR_VIRTUAL_FILL_COLOR  , gui_board.Board.virtualCursorFill)
        settings.setdefault(KEY.CURSOR_VIRTUAL_FILL_STIPPLE, gui_board.Board.virtualCursorStipple)

        settings.setdefault(KEY.CURSOR_IS_TEXT_FG_COLOR_DOMINANT, gui_board.Board.isTextColorDominant)
        settings.setdefault(KEY.CURSOR_IS_TEXT_BG_COLOR_DOMINANT, gui_board.Board.isTextFillDominant)
        settings.setdefault(KEY.CURSOR_IS_TEXT_BG_STIPPLE_DOMINANT, gui_board.Board.isTextStippleDominant)

        settings.setdefault(KEY.OVERLAY_TEXT_FG_COLOR  , gui_board.Board.textColor)
        settings.setdefault(KEY.OVERLAY_TEXT_BG_COLOR  , gui_board.Board.textFill)
        settings.setdefault(KEY.OVERLAY_TEXT_BG_STIPPLE, gui_board.Board.textStipple)

        settings.setdefault(KEY.VIEW_MOVABILITY_INDICATORS, False)
        settings.setdefault(KEY.AUTO_TRIGGER_SANITY_CHECK, True)
        settings.setdefault(KEY.WIDTH_NOTES, 40)
        settings.setdefault(KEY.WIDTH_LABEL_INFO, 50)
        
        settings.setdefault(KEY.SELECTION_INFO_PATTERN,         u"{cursorName} [{x},{y}]: {objCode:03d} ({objChr}): {properties}")
        settings.setdefault(KEY.SELECTION_INFO_PROP_PATTERN,    u"{}")
        settings.setdefault(KEY.SELECTION_INFO_PROP_SEP,        u", ")
        settings.setdefault(KEY.SELECTION_INFO_TOOLTIP_PATTERN,         u"{cursorName} [{x},{y}]\n{objCode:03d} ({objChr}): {properties}")
        settings.setdefault(KEY.SELECTION_INFO_TOOLTIP_PROP_PATTERN,    u"\n - {}")
        settings.setdefault(KEY.SELECTION_INFO_TOOLTIP_PROP_SEP,        u"")
        settings.setdefault(KEY.SELECTION_INFO_TOOLTIP_ALWAYS,   False)
        
        settings.setdefault(KEY.OBJECT_DESCRIPTION_FORMAT,          objects.OBJECT_DESCRIPTION_FORMAT)
        settings.setdefault(KEY.OBJECT_DESCRIPTION_PROPERTY_SEP,    objects.OBJECT_DESCRIPTION_PROPERTY_SEP)
        settings.setdefault(KEY.OBJECT_DESCRIPTION_PROPERTY_FORMAT, objects.OBJECT_DESCRIPTION_PROPERTY_FORMAT)
        
        
        settings.setdefault(settings_manager.KEY.UPDATE_SETTINGS, True)
        
        
        # this would actually belong in applySettings but there it would be executed too late
        
        objects.OBJECT_DESCRIPTION_FORMAT          = settings[KEY.OBJECT_DESCRIPTION_FORMAT]
        objects.OBJECT_DESCRIPTION_PROPERTY_SEP    = settings[KEY.OBJECT_DESCRIPTION_PROPERTY_SEP]
        objects.OBJECT_DESCRIPTION_PROPERTY_FORMAT = settings[KEY.OBJECT_DESCRIPTION_PROPERTY_FORMAT]
        

    def applySettings(self):
        bg         = settings[KEY.COLOR_BG]
        bgSelected = settings[KEY.COLOR_BG_SELECTED]
        bgActive   = settings[KEY.COLOR_BG_ACTIVE]
        bgEntry    = settings[KEY.COLOR_BG_ENTRY]

        text         = settings[KEY.COLOR_TEXT]
        textSelected = settings[KEY.COLOR_TEXT_SELECTED]
        textActive   = settings[KEY.COLOR_TEXT_ACTIVE]
        textEntry    = settings[KEY.COLOR_TEXT_ENTRY]
        textSuccess  = settings[KEY.COLOR_TEXT_SUCCESS]
        textWarning  = settings[KEY.COLOR_TEXT_WARNING]
        textError    = settings[KEY.COLOR_TEXT_ERROR]
        textCor                = settings[KEY.COLOR_TEXT_COR_UNSELECTED]
        textCorSelected        = settings[KEY.COLOR_TEXT_COR_SELECTED]
        textCorInvalid         = settings[KEY.COLOR_TEXT_COR_INVALID_UNSELECTED]
        textCorInvalidSelected = settings[KEY.COLOR_TEXT_COR_INVALID_SELECTED]

        highlight    = settings[KEY.COLOR_HIGHLIGHT]
        borderSolutionSelection = settings[KEY.COLOR_BORDER_SOLUTION_SELECTION]
        bgSolutionSelection     = settings[KEY.COLOR_BG_SOLUTION_SELECTION]

        self.sideFrame.setTextColors(normal=text, success=textSuccess, warning=textWarning, error=textError)

        if bg != None:
            self.configAll(self, dict(bg=bg))
            self.configAll(self, dict(highlightbackground=bg))
        if bgActive != None:
            self.configAll(self, dict(activebackground=bgActive))

        if textActive != None:
            self.configAll(self, dict(activeforeground=textActive))
        if text != None:
            self.configAll(self, dict(fg=text))
            #WARNING: selectcolor is foreground in menu checkbuttons but background in normal checkbuttons
            self.configAll(self.menubar, dict(selectcolor=text))

            gui_solution_view.SolutionViewRaw.KW_STEP_NUMBER ['fill'] = text
            gui_solution_view.SolutionViewRaw.KW_STEP_TEXT   ['fill'] = text
            gui_solution_view.SolutionViewRaw.KW_INFO        ['fill'] = text

        if highlight == None:
            highlight = text
        if highlight != None:
            self.configAll(self, dict(highlightcolor=highlight))

        if bgSelected != None:
            for title,cat in set(self._levelEditorChildPanes + self._solutionEditorChildPanes):
                # I am consciously *not* setting the text color to selected
                self.configAll(cat, dict(bg=bgSelected))

        if bg != None or text != None or bgSelected != None or bgActive != None or textSelected != None or textActive != None:
            noteStyler = ttk.Style()
            
            # https://stackoverflow.com/a/29572789
            # Import the Notebook.tab element from the default theme
            noteStyler.element_create('Plain.Notebook.tab', "from", 'default')
            # Redefine the TNotebook Tab layout to use the new element
            noteStyler.layout("TNotebook.Tab",
                [('Plain.Notebook.tab', {'children':
                    [('Notebook.padding', {'side': 'top', 'children':
                        [('Notebook.focus', {'side': 'top', 'children':
                            [('Notebook.label', {'side': 'top', 'sticky': ''})],
                        'sticky': 'nswe'})],
                    'sticky': 'nswe'})],
                'sticky': 'nswe'})])

            kw = dict()
            if bg != None:
                kw['background'] = bg
            noteStyler.configure("TNotebook", borderwidth=1, **kw)
            if text != None:
                kw['foreground'] = text
            noteStyler.configure("TNotebook.Tab", borderwidth=1, **kw)

            #http://page.sourceforge.net/html/themes.html
            #https://wiki.tcl.tk/37973#pagetoc31f1638c
            bgs = list()
            if bgSelected != None:
                bgs.append(('selected', bgSelected))
            if bgActive != None:
                bgs.append(('active', bgActive))

            fgs = list()
            if textSelected != None:
                fgs.append(('selected', textSelected))
            if textActive != None:
                fgs.append(('active', textActive))

            noteStyler.map('TNotebook.Tab', background=bgs, foreground=fgs)


        # commandline & notes

        if bgEntry != None:
            self.textNotes.config(bg = bgEntry)
            self.board.setCommandlineBackgroundColor(bgEntry)

        if textEntry != None:
            #insertbackground: cursor color
            self.textNotes.config(fg = textEntry, insertbackground = textEntry)
            self.board.setCommandlineTextColorNormal(textEntry)

        if textError != None:
            self.board.setCommandlineTextColorError(textError)


        # solution settings

        if textCorSelected == None:
            textCorSelected = text
        if textCor == None:
            textCor = text
        if textCorInvalidSelected == None:
            textCorInvalidSelected = text
        if textCorInvalid == None:
            textCorInvalid = text

        gui_solution_view.SolutionViewRaw.KW_COR_SELECTED['fill'] = textCorSelected
        gui_solution_view.SolutionViewRaw.KW_COR_UNSELECTED['fill'] = textCor
        gui_solution_view.SolutionViewRaw.KW_COR_INVALID_SELECTED['fill'] = textCorInvalidSelected
        gui_solution_view.SolutionViewRaw.KW_COR_INVALID_UNSELECTED['fill'] = textCorInvalid

        if bgSolutionSelection != None:
            gui_solution_view.SolutionViewRaw.COLOR_SELECTION_FILL = bgSolutionSelection
        if borderSolutionSelection != None:
            gui_solution_view.SolutionViewRaw.COLOR_SELECTION_OUTLINE = borderSolutionSelection


        # cursor settings

        v = settings[KEY.CURSOR_BORDER_WIDTH]
        if v != None:
            gui_board.Board.cursorWidth = v
        v = settings[KEY.CURSOR_BORDER_COLOR]
        if v != None:
            gui_board.Board.cursorColor = v
        v = settings[KEY.CURSOR_FILL_COLOR]
        if v != None:
            gui_board.Board.cursorFill = v
        v = settings[KEY.CURSOR_FILL_STIPPLE]
        if v != None:
            gui_board.Board.cursorStipple = v
        
        v = settings[KEY.CURSOR_LAST_BORDER_WIDTH]
        if v != None:
            gui_board.Board.lastCursorWidth = v
        v = settings[KEY.CURSOR_LAST_BORDER_COLOR]
        if v != None:
            gui_board.Board.lastCursorColor = v
        v = settings[KEY.CURSOR_LAST_FILL_COLOR]
        if v != None:
            gui_board.Board.lastCursorFill = v
        v = settings[KEY.CURSOR_LAST_FILL_STIPPLE]
        if v != None:
            gui_board.Board.lastCursorStipple = v
        
        v = settings[KEY.CURSOR_VIRTUAL_BORDER_WIDTH]
        if v != None:
            gui_board.Board.virtualCursorWidth = v
        v = settings[KEY.CURSOR_VIRTUAL_BORDER_COLOR]
        if v != None:
            gui_board.Board.virtualCursorColor = v
        v = settings[KEY.CURSOR_VIRTUAL_FILL_COLOR]
        if v != None:
            gui_board.Board.virtualCursorFill = v
        v = settings[KEY.CURSOR_VIRTUAL_FILL_STIPPLE]
        if v != None:
            gui_board.Board.virtualCursorStipple = v

        v = settings[KEY.OVERLAY_TEXT_FG_COLOR]
        if v != None:
            gui_board.Board.textColor = v
        v = settings[KEY.OVERLAY_TEXT_BG_COLOR]
        if v != None:
            gui_board.Board.textFill = v
        v = settings[KEY.OVERLAY_TEXT_BG_STIPPLE]
        if v != None:
            gui_board.Board.textStipple = v

        gui_board.Board.isTextColorDominant   = settings[KEY.CURSOR_IS_TEXT_FG_COLOR_DOMINANT]
        gui_board.Board.isTextFillDominant    = settings[KEY.CURSOR_IS_TEXT_BG_COLOR_DOMINANT]
        gui_board.Board.isTextStippleDominant = settings[KEY.CURSOR_IS_TEXT_BG_STIPPLE_DOMINANT]


    def configAll(self, widget, kw):
        try:
            widget.config(kw)
        except:
            pass

        for child in widget.children.values():
            self.configAll(child, kw)



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
        if self.model.hasVirtualCursor():
            cor = self.model.getVirtualCursor()
            cursorName = _("Virtual Cursor")
        elif self.model.hasCursor():
            cor = self.model.getLastCursor()
            cursorName = _("Last Cursor")
        else:
            msg = _("<no cursors>")
            tkx.set_text(self.labelInfo.tooltip, None)
            tkx.set_text(self.labelInfo, msg)
            return
        
        obj = self.model.getField(*cor)
        objChr = objects.codeToChr(obj)
        propertiesList = objects.getPropertiesList(obj)
        
        properties = lambda sep, p: objects.formatList(propertiesList, sep=sep, form=p)
        msg = lambda properties: pattern.format(cursorName=cursorName, x=cor[0], y=cor[1], objCode=obj, objChr=objChr, properties=properties)
        
        info = properties(sep=settings[KEY.SELECTION_INFO_PROP_SEP], p=settings[KEY.SELECTION_INFO_PROP_PATTERN])
        infoTooltip = lambda: properties(sep=settings[KEY.SELECTION_INFO_TOOLTIP_PROP_SEP], p=settings[KEY.SELECTION_INFO_TOOLTIP_PROP_PATTERN])
        
        pattern = settings[KEY.SELECTION_INFO_TOOLTIP_PATTERN]
        maxWidth = settings[KEY.WIDTH_LABEL_INFO]
        if len(info) > maxWidth:
            tkx.set_text(self.labelInfo.tooltip, msg(infoTooltip()))
            info = info[:maxWidth-3] + "..."
        else:
            if settings[KEY.SELECTION_INFO_TOOLTIP_ALWAYS]:
                tkx.set_text(self.labelInfo.tooltip, msg(infoTooltip()))
            else:
                tkx.set_text(self.labelInfo.tooltip, None)
        
        pattern = settings[KEY.SELECTION_INFO_PATTERN]
        tkx.set_text(self.labelInfo, msg(info))
        

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
        if self.notesActive:
                self.textNotes.focus_set()
        else:
            if self.board.isModeEditSolution():
                self.solutionFrame.focus_set()
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
        if settings[KEY.ASK_BEFORE_SAVE] and not self.sanityCheckBeforeSave():
            return False

        out = self.saveWithoutCheck()

        if out and not settings[KEY.ASK_BEFORE_SAVE] and settings[KEY.CHECK_AFTER_SAVE]:
            self.sanityCheckAfterSave()

        return out

    def saveAs(self):
        if settings[KEY.ASK_BEFORE_SAVE_AS] and not self.sanityCheckBeforeSave():
            return False

        out = self.saveAsWithoutCheck()

        if out and not settings[KEY.ASK_BEFORE_SAVE_AS] and settings[KEY.CHECK_AFTER_SAVE_AS]:
            self.sanityCheckAfterSave()

        return out

    def saveCopyAs(self):
        if settings[KEY.ASK_BEFORE_SAVE_COPY] and not self.sanityCheckBeforeSave():
            return False

        out = self.saveCopyAsWithoutCheck()

        if out and not settings[KEY.ASK_BEFORE_SAVE_COPY] and settings[KEY.CHECK_AFTER_SAVE_COPY]:
            self.sanityCheckAfterSave()

        return out

        
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
            return self.saveAsWithoutCheck()


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


    def sanityCheckAfterSave(self):
        logLevel = self.implicitSanityCheck()

        if logLevel >= logging.WARNING:
            self.openSideFrame()
            return False

        return True



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
