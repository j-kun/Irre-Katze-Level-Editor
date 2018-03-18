#!/usr/bin/env python

import tkinter_extensions as tkx
tk  = tkx.tk

import logging

import locales
_ = locales._


class LogFrame(tkx.FrameWithTitle):

    BULLET = u'\u2B25' # black medium diamond
    #BULLET = u'\u25B3' # white up-pointing triangle
    BULLET = u'\u26A0' # warning sign
    #BULLET = u'\u2043' # hyphen bullet
    #BULLET = u'\u25AA' # square bullet
    #BULLET = u'\u2B1D' # small square bullet
    BULLET = u'\u2023' # triangular bullet
    #BULLET = u'\u2022' # circular bullet
    #BULLET = u'\u26AB' # medium black circle
    

    PAD_Y = 2

    COL_BULLET = 0
    COL_MSG = 1
    COL_BTN = 2


    # ---------- initialization ----------
    
    def __init__(self, master, autoReload=True, **kw):
        self.__takefocus = kw.get('takefocus', True)
        tkx.FrameWithTitle.__init__(self, master, **kw)
        self.msgFrame = tk.Frame(self)
        self.msgFrame.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.msgFrame.grid_columnconfigure(self.COL_MSG, weight=1)
        self.row = 1

        self.setTextColors(normal = 'black', error = 'red', warning = 'orange')

        self.command = None
        self.reloadButton = None
        self.varAutoReload = tk.BooleanVar(value=autoReload)
        self.varState = tk.BooleanVar(value=False)

    def setTextColors(self, normal, warning, error):
        if error == None:
            error = normal
        if warning == None:
            warning = normal

        self.textColorNormal  = normal
        self.textColorError   = error
        self.textColorWarning = warning



    # ---------- reload ----------

    def setReloadCommand(self, command):
        self.command = command
        if command == None:
            if self.reloadButton != None:
                self.btnFrame.destroy()
                self.padding.destroy()
                self.btnFrame = None
                self.autoReloadCheckbox = None
                self.autoReloadLabel = None
                self.reloadButton = None
            return
        
        if self.reloadButton == None:
            bg = self['bg']
            fg = self.textColorNormal

            self.btnFrame = tk.Frame(self, bg=bg)
            self.btnFrame.pack(side=tk.TOP, before=self.msgFrame, anchor=tk.CENTER)
            self.padding = tk.Frame(self, height=self['pady'], bg=bg)
            self.padding.pack(side=tk.TOP, before=self.msgFrame, anchor=tk.CENTER)

            #TODO: activebackground, activeforeground
            self.autoReloadCheckbox = tkx.Checkbutton(self.btnFrame, command=self._onReloadModeChange, variable=self.varAutoReload, bg=bg, selectcolor=bg, fg=fg, bd=0, highlightthickness=0, takefocus=self.__takefocus)
            self.autoReloadCheckbox.bind('<Map>', self.onMap)
            self.autoReloadCheckbox.bind('<Unmap>', self.onUnMap)
            self.autoReloadCheckbox.pack(side=tk.LEFT)

            self.autoReloadLabel = tk.Label(self.btnFrame, text=_("Auto Reload"), bg=bg, fg=fg)
            self.reloadButton = tk.Button(self.btnFrame, text=_("Reload"), bg=bg, fg=fg, takefocus=self.__takefocus)

            self._onReloadModeChange()
            
        self.reloadButton.configure(command=command)

    def _onReloadModeChange(self):
        if self.autoReloadCheckbox.get_value():
            self.reloadButton.pack_forget()
            self.autoReloadLabel.pack(side=tk.LEFT)
        else:
            self.autoReloadLabel.pack_forget()
            self.reloadButton.pack(side=tk.LEFT)

    def autoReload(self):
        if self.command != None and self.winfo_viewable() and self.autoReloadCheckbox.get_value():
            self.command()


    # ---------- statevar ----------

    def onMap(self, event):
        self.varState.set(value=1)

    def onUnMap(self, event):
        self.varState.set(value=0)


    # ---------- messages ----------

    def addMessage(self, level, msg):
        bg = self['bg']
        fg = self.textColorNormal
        if level >= logging.ERROR:
            color = self.textColorError
        elif level >= logging.WARNING:
            color = self.textColorWarning
        else:
            color = self.textColorNormal
        
        blt = tk.Label(self.msgFrame, text=self.BULLET, bg=bg, fg=color, padx=0)
        lbl = tk.Label(self.msgFrame, text=msg, bg=bg, fg=color, justify=tk.LEFT, padx=0)
        btn = tkx.SmallCloseButton(self.msgFrame, takefocus=self.__takefocus, bg=bg, fg=fg)
        btn.configure(command=lambda: self._rmMessage(blt, lbl, btn))

        blt.grid(row=self.row, column=self.COL_BULLET, sticky=tk.NE, pady=self.PAD_Y)
        lbl.grid(row=self.row, column=self.COL_MSG, sticky=tk.NW, pady=self.PAD_Y)
        btn.grid(row=self.row, column=self.COL_BTN, sticky=tk.NE, pady=self.PAD_Y)

        self.row += 1

    def _rmMessage(self, blt, lbl, btn):
        blt.destroy()
        lbl.destroy()
        btn.destroy()
        self._messageIfEmpty(_("(all found problems\nhave been removed)"), 'orange')

    def _messageIfEmpty(self, msg, color):
        if self.isEmpty():
            tk.Label(self.msgFrame, text="\n"+msg, fg=color, anchor=tk.CENTER).pack(side=tk.TOP)

    def complete(self):
        self._messageIfEmpty(_("(no problems\nhave been found)"), 'green')

    def isEmpty(self):
        return len(self.msgFrame.winfo_children()) == 0

    def clear(self):
        for w in self.msgFrame.winfo_children():
            w.destroy()
        


if __name__=='__main__':
    root = tk.Tk()
    root.title("Test")

    def fillLog():
        print("reload")
        log.clear()
        for i in range(10):
            log.addMessage(logging.ERROR, "test %s" % i)
        log.complete()

    log = LogFrame(root)
    log.setReloadCommand(fillLog)
    #log.setReloadCommand(None)
    log.title("Tests")
    def showLog():
        log.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.BOTH)
    showLog()

    frame = tk.Frame(root)
    frame.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)

    buttonShow = tk.Button(frame, text="Show", command=showLog)
    buttonShow.pack(side=tk.TOP)
    buttonAutoReload = tk.Button(frame, text="Auto Reload", command=log.autoReload)
    buttonAutoReload.pack(side=tk.TOP)

    tk.Frame(frame).pack(side=tk.TOP, expand=tk.YES, fill=tk.Y)
    
    buttonClear = tk.Button(frame, text="Clear", command=log.clear)
    buttonClear.pack(side=tk.TOP)
    
    entry = tk.Entry(frame)
    entry.pack()

    buttonAdd = tk.Button(frame, text="Add", command=lambda: log.addMessage(logging.WARNING, tkx.get_text(entry)))
    buttonAdd.pack(side=tk.TOP)

    tk.Frame(frame).pack(side=tk.TOP, expand=tk.YES, fill=tk.Y)
    
    buttonComplete = tk.Button(frame, text="Complete", command=log.complete)
    buttonComplete.pack(side=tk.TOP)

    fillLog()
    
    root.mainloop()
