#!/usr/bin/env python

import time

import tkinter_extensions as tkx
tk = tkx.tk
tkc = tkx.tkc
tkSimpleDialog = tkx.tkSimpleDialog

import gui_image_opener as imageOpener

import model_object_catalog as objects
import model_background_catalog as backgrounds

import locales
_ = locales._


class Board(tk.Canvas):

    MODE_EDIT_LEVEL    = 'level-editor'
    MODE_EDIT_SOLUTION = 'solution-editor'

    TAG_CURSOR = 'cursor'
    TAG_BORDER = 'border'
    TAG_BOARD  = 'board'

    cursorWidth = 2
    cursorColor = 'blue'
    cursorFill  = cursorColor
    cursorStipple = tkc.STIPPLE_GRAY_25

    virtualCursorWidth = 2
    virtualCursorColor = 'green'
    virtualCursorFill  = virtualCursorColor
    virtualCursorStipple = tkc.STIPPLE_GRAY_12

    textStipple = tkc.STIPPLE_GRAY_25
    textFill    = 'white'

    DEBUG_CURSOR_OFF  = 0
    DEBUG_CURSOR_REAL = 1
    DEBUG_CURSOR_LEFT_TO_RIGHT = 2
    DEBUG_CURSOR_RIGHT_TO_LEFT = 3
    DEBUG_CURSOR_TOP_TO_BOTTOM = 4
    DEBUG_CURSOR_BOTTOM_TO_TOP = 5

    OBJECT_CODE_OFF    = 0
    OBJECT_CODE_NUMBER = 1
    OBJECT_CODE_CHAR   = 2

    OBJ_CAT = objects.OBJ_START
    OBJ_DOOR_OPEN = 93
    

    # ---------- initialization ----------
    
    def __init__(self, master, model):
        tk.Canvas.__init__(self, master,
            width  = (model.COLS+2)*imageOpener.FLD_SIZE,
            height = (model.ROWS+2)*imageOpener.FLD_SIZE,
            offset = "%s,%s" % (-imageOpener.FLD_SIZE, -imageOpener.FLD_SIZE),
            borderwidth = 0,
            highlightthickness = 1,
            takefocus = True,
        )
        self.model = model
        self._mode = self.MODE_EDIT_LEVEL
        self._last_cmd = None
        self.isEndActive = False
        
        self.canvas = self
        self.canvas.bindToKey = tkx.KeyBinder(self.canvas)
        self.widgetToFocus = self
        self.entry = None
        self.debugCursor = False
        self.viewObjectCode = self.OBJECT_CODE_OFF
        self.onObjectCodeChangeListener = set()
        
        self.drawBorder()
        self.drawBoard()
        self.drawCursor()

        model.addOnChangeListener(self.onChangeListener)
        model.solution.addOnStepsChangeListener(self.onSolutionChangeListener)
        model.solution.addOnCursorChangeListener(self.onSolutionChangeListener)

        # move cursor
        self.canvas.bind('<Right>', lambda e: model.moveCursorRight() if not self.isEndActive else model.moveCursorToRight())
        self.canvas.bind('<Left>' , lambda e: model.moveCursorLeft()  if not self.isEndActive else model.moveCursorToLeft())
        self.canvas.bind('<Up>'   , lambda e: model.moveCursorUp()    if not self.isEndActive else model.moveCursorToTop())
        self.canvas.bind('<Down>' , lambda e: model.moveCursorDown()  if not self.isEndActive else model.moveCursorToBottom())
        
        self.canvas.bind('<KeyPress-Control_L>', lambda e:   model.newCursorBegin())
        self.canvas.bind('<KeyRelease-Control_L>', lambda e: model.newCursorEnd())
        self.canvas.bind('<KeyPress-Control_R>', lambda e:   model.newCursorBegin())
        self.canvas.bind('<KeyRelease-Control_R>', lambda e: model.newCursorEnd())
        self.canvas.bind('<Control-Right>', lambda e: model.newCursorRight() if not self.isEndActive else model.newCursorToRight())
        self.canvas.bind('<Control-Left>' , lambda e: model.newCursorLeft()  if not self.isEndActive else model.newCursorToLeft())
        self.canvas.bind('<Control-Up>'   , lambda e: model.newCursorAbove() if not self.isEndActive else model.newCursorToTop())
        self.canvas.bind('<Control-Down>' , lambda e: model.newCursorBelow() if not self.isEndActive else model.newCursorToBottom())

        self.canvas.bind('<Shift-Right>', lambda e: model.addOrRemoveCursorRight() if not self.isEndActive else model.addCursorsTowardsRight())
        self.canvas.bind('<Shift-Left>' , lambda e: model.addOrRemoveCursorLeft()  if not self.isEndActive else model.addCursorsTowardsLeft())
        self.canvas.bind('<Shift-Up>'   , lambda e: model.addOrRemoveCursorAbove() if not self.isEndActive else model.addCursorsTowardsTop())
        self.canvas.bind('<Shift-Down>' , lambda e: model.addOrRemoveCursorBelow() if not self.isEndActive else model.addCursorsTowardsBottom())

        self.canvas.bind('<Shift-Control-Right>', lambda e: model.addOrRemoveCursorsRight() if not self.isEndActive else model.addCursorAreaTowardsRight())
        self.canvas.bind('<Shift-Control-Left>' , lambda e: model.addOrRemoveCursorsLeft()  if not self.isEndActive else model.addCursorAreaTowardsLeft())
        self.canvas.bind('<Shift-Control-Up>'   , lambda e: model.addOrRemoveCursorsAbove() if not self.isEndActive else model.addCursorAreaTowardsTop())
        self.canvas.bind('<Shift-Control-Down>' , lambda e: model.addOrRemoveCursorsBelow() if not self.isEndActive else model.addCursorAreaTowardsBottom())
        
        self.canvas.bind('<BackSpace>' , lambda e: model.removeLastCursor())
        self.canvas.bind('<Home>' , lambda e: model.moveCursorToCenter())
        self.canvas.bind('<End>', self.onEndPress)
        
        self.canvas.bind('<Button-1>', self.onClick)
        self.canvas.bind('<Escape>' , lambda e: model.newCursorCancel() or model.selectOne() or model.selectNone())
        self.canvas.bind('<Control-a>' , lambda e: model.selectAll())

        self.canvas.bindToKey('F1' , lambda key: self.setViewObjectCode(self.OBJECT_CODE_CHAR),   lambda key: self.setViewObjectCode(self.OBJECT_CODE_OFF))
        self.canvas.bindToKey('F2' , lambda key: self.setViewObjectCode(self.OBJECT_CODE_NUMBER), lambda key: self.setViewObjectCode(self.OBJECT_CODE_OFF))
        self.canvas.bind('<F4>' , lambda e: self.toggleDebugCursor(self.DEBUG_CURSOR_REAL))
        self.canvas.bind('<F5>' , lambda e: self.toggleDebugCursor(self.DEBUG_CURSOR_LEFT_TO_RIGHT))
        self.canvas.bind('<F6>' , lambda e: self.toggleDebugCursor(self.DEBUG_CURSOR_TOP_TO_BOTTOM))
        self.canvas.bind('<F7>' , lambda e: self.toggleDebugCursor(self.DEBUG_CURSOR_RIGHT_TO_LEFT))
        self.canvas.bind('<F8>' , lambda e: self.toggleDebugCursor(self.DEBUG_CURSOR_BOTTOM_TO_TOP))

        # edit board
        self.canvas.bind('<Delete>' , lambda e: model.setFieldAtCursor(model.FLD_EMPTY))
        self.canvas.bind('<Return>' ,  lambda e: self.enterNewObject())
        self.canvas.bind('<Key>' ,  self.onKeyListener)
        
        #TODO: respect isEndActive
        self.canvas.bind('<Alt-Right>', lambda e: model.moveFieldRight())
        self.canvas.bind('<Alt-Left>', lambda e: model.moveFieldLeft())
        self.canvas.bind('<Alt-Up>', lambda e: model.moveFieldUp())
        self.canvas.bind('<Alt-Down>', lambda e: model.moveFieldDown())

        self.canvas.bind('<Control-c>' ,  lambda e: self.model.copy())
        self.canvas.bind('<Control-v>' ,  lambda e: self.model.paste(False))
        self.canvas.bind('<Control-x>' ,  lambda e: self.model.cut())

        self.canvas.bind('<Control-r>' ,  lambda e: self.repeatLastCommand())

        #TODO: +/- to change last inserted object
        #TODO: invert/mirror?
        
        self.widgetToFocus.focus_set()

    def center(self):
        self.update_idletasks()
        bbox = self.bbox(tk.ALL)
        xCenter = (bbox[0] + bbox[2]) / 2.0
        w = self.winfo_width()
        x0 = xCenter - w/2.0
        x1 = xCenter + w/2.0
        #TODO: why is it shifted?
        x0 -= 1
        x1 -= 1
        bbox = list(bbox)
        bbox[0] = int(x0)
        bbox[2] = int(x1)
        self.configure(scrollregion=bbox)


    # ---------- modes ----------

    def setMode(self, mode):
        self._mode = mode

    def isModeEditSolution(self):
        return self._mode == self.MODE_EDIT_SOLUTION

    def isModeEditLevel(self):
        return self._mode == self.MODE_EDIT_LEVEL


    # ---------- listener ----------

    def addOnObjectCodeChangeListener(self, listener):
        self.onObjectCodeChangeListener.add(listener)

    def notifyObjectCodeChanged(self, newObjectCode):
        for listener in self.onObjectCodeChangeListener:
            listener(newObjectCode)
    

    # ---------- listen to model ----------

    def onChangeListener(self, change):
        self.isEndActive = False

        model = self.model
        done = False
        if change in (model.CHANGE_BG_BORDER, model.CHANGE_BG):
            self.canvas.delete(self.TAG_BORDER)
            self.drawBorder()
            if change == model.CHANGE_BG_BORDER:
                done = True

        if done:
            pass
        elif change == model.CHANGE_CURSOR:
            self.canvas.delete(self.TAG_CURSOR)
            self.drawCursor()
        elif change == model.CHANGE_ALL:
            self.canvas.delete(tk.ALL)
            self.drawBorder()
            self.drawBoard()
            self.drawCursor()
        elif change == model.CHANGE_HAS_CHANGED:
            return
        elif change == model.CHANGE_AUTHOR:
            return
        else:
            self.canvas.delete(self.TAG_BOARD, self.TAG_CURSOR)
            self.drawBoard()
            self.drawCursor()
        self.update_idletasks()

    def onSolutionChangeListener(self):
        assert self.isModeEditSolution()
        self.canvas.delete(self.TAG_BOARD, self.TAG_CURSOR)
        self.drawBoard()


    # ---------- listen to gui ----------

    def onEndPress(self, event=None):
        self.isEndActive = True

    def onClick(self, event):
        if self.isModeEditSolution():
            return
        
        x = self.eventToModelX(event)
        y = self.eventToModelY(event)
        if event.state & tkc.MODIFIER_MASK_SHIFT_ONLY:
            self.model.addCursorRange(x, y)
        elif event.state & tkc.MODIFIER_MASK_CTRL:
            self.model.toggleCursor(x, y)
        else:
            self.model.setCursor(x, y)

    def onKeyListener(self, event):
        #print("char: {e.char}, keycode: {e.keycode}, keysym: {e.keysym}, keysym_num: {e.keysym_num}, state: {e.state}, type: {e.type}".format(e=event))
        if event.state&tkc.MODIFIER_MASK_CTRL==0 and event.state&tkc.MODIFIER_MASK_ALT==0:
            #self.enterNewObject()
            #tkx.append_text(self.entry, event.char)
            value = event.keysym_num
            if not imageOpener.getImage.isValid(value):
                return
            self.model.setFieldAtCursor(value)
            return tkc.RETURNCODE_BREAK

    def toggleDebugCursor(self, mode):
        if mode == self.debugCursor:
            self.debugCursor = self.DEBUG_CURSOR_OFF
        else:
            self.debugCursor = mode
        self.onChangeListener(self.model.CHANGE_CURSOR)
        return tkc.RETURNCODE_BREAK

    def setViewObjectCode(self, value):
        if value != self.OBJECT_CODE_OFF:
            self.notifyObjectCodeChanged(value)
        if value != self.viewObjectCode:
            self.viewObjectCode = value
            self.onChangeListener(self.model.CHANGE_BOARD)
        return tkc.RETURNCODE_BREAK

    def repeatLastCommand(self):
        if self._last_cmd == None:
            return
        self.evaluateCommand(self._last_cmd)


    # ---------- enter object code ----------

    def enterNewObject(self):
        if self.entry != None:
            self.entry.focus_set()
            return
        
        if self.model.hasCursor() and not self.isModeEditSolution():
            x = self.model.getLastCursorX()
            y = self.model.getLastCursorY()
            x = self.modelToPlaceX(x)
            y = self.modelToPlaceY(y)
            x += imageOpener.FLD_SIZE/2
            y += imageOpener.FLD_SIZE/2
            width = 3
        else:
            x = self.winfo_width() / 2
            y = self.winfo_height() / 2
            width = len(self.CODE_SET_AUTHOR) + 20
        self.entry = tkx.Entry(self, width=width)
        self.entry.place(x=x, y=y, anchor=tk.CENTER)
        self.entry.focus_set()
        self.entry.bind('<Return>', self.enterNewObjectDone)
        self.entry.bind('<Escape>', self.enterNewObjectCancel)
        self.entry.bind('<Key>', lambda e: self.entry.configure(fg='black'), '+')
        def onKey(e):
            #print("char: {e.char}, keycode: {e.keycode}, keysym: {e.keysym}, keysym_num: {e.keysym_num}, state: {e.state}, type: {e.type}".format(e=e))
            if e.keycode in tkc.KEYCODES_ARROWS:
                if self.enterNewObjectDone():
                    self.event_generate("<Key>", keycode=e.keycode, keysym=e.keysym, state=e.state)
                    return tkc.RETURNCODE_BREAK
        self.entry.bind('<Key>', onKey, '+')


    CODE_ENTER_AUTHOR = "author"
    CODE_SET_AUTHOR   = CODE_ENTER_AUTHOR + "="
    CODE_SET_BG       = "bg="
    CODE_BG_INC       = "bg++"
    CODE_BG_DEC       = "bg--"
    
    def enterNewObjectDone(self, event=None):
        code = tkx.get_text(self.entry)
        if self.evaluateCommand(code):
            self.enterNewObjectSuccess()
            return True
        else:
            self.enterNewObjectError()
            return False

    def evaluateCommand(self, code):
        if len(code)==1:
            value = ord(code)
        elif code == self.CODE_ENTER_AUTHOR:
            self.enterAuthor()
            return True
        elif code[:len(self.CODE_SET_AUTHOR)] == self.CODE_SET_AUTHOR:
            self.model.setAuthor(code[len(self.CODE_SET_AUTHOR):].strip())
            return True
        elif code[:len(self.CODE_SET_BG)] == self.CODE_SET_BG:
            bg = code[len(self.CODE_SET_BG):].strip()
            return self.model.setBgScheme(bg)
        elif code == self.CODE_BG_INC:
            self.model.nextBg()
            return True
        elif code == self.CODE_BG_DEC:
            self.model.prevBg()
            return True
        else:
            try:
                value = int(code)
            except:
                value = imageOpener.getBackground.shortNameToValue(code)
                if value in backgrounds.CATEGORY_BORDER:
                    self.model.setBgBorder(value)
                elif value in backgrounds.CATEGORY_UNTOUCHED:
                    self.model.setBgUntouched(value)
                elif value in backgrounds.CATEGORY_TOUCHED:
                    self.model.setBgTouched(value)
                else:
                    return False
                return True

        if self.isModeEditSolution():
            return False
        if not self.model.hasCursor():
            return False
        if imageOpener.getImage.isValid(value):
            self.model.setFieldAtCursor(value)
        else:
            return False
        return True

    def enterNewObjectSuccess(self):
        self._last_cmd = tkx.get_text(self.entry)
        self.enterNewObjectCancel()

    def enterNewObjectError(self):
        self.entry.configure(fg='red')

    def enterNewObjectCancel(self, event=None):
        self.entry.place_forget()
        self.widgetToFocus.focus_set()
        self.entry = None


    def enterAuthor(self):
        author = tkSimpleDialog.askstring(
            title = _("Author"),
            prompt = _("Please enter the name of the author:"),
            initialvalue = self.model.getAuthor(),
        )
        self.widgetToFocus.focus_set()
        if author != None:
            self.model.setAuthor(author)
            return True
        return False


    # ---------- coordinate conversions ----------

    def modelToCanvasX(self, x):
        return x * imageOpener.FLD_SIZE
    def modelToCanvasY(self, y):
        return y * imageOpener.FLD_SIZE

    def modelToPlaceX(self, x):
        return self.modelToCanvasX(x) - self.canvas.canvasx(0)
    def modelToPlaceY(self, y):
        return self.modelToCanvasY(y) - self.canvas.canvasy(0)

    def eventToModelX(self, event):
        return int(self.canvas.canvasx(event.x)) // imageOpener.FLD_SIZE
    def eventToModelY(self, event):
        return int(self.canvas.canvasx(event.y)) // imageOpener.FLD_SIZE

    
    # ---------- drawing ----------

    def drawImage(self, x, y, image, **kw):
        self.canvas.create_image(self.modelToCanvasX(x), self.modelToCanvasY(y), anchor='nw', image=image, **kw)

    def drawRectangle(self, x, y, **kw):
        self.canvas.create_rectangle(
            self.modelToCanvasX(x), self.modelToCanvasY(y),
            self.modelToCanvasX(x+1), self.modelToCanvasY(y+1),
            **kw
        )

    def drawText(self, x, y, **kw):
        self.canvas.create_text(
            self.modelToCanvasX(x) + imageOpener.FLD_SIZE/2,
            self.modelToCanvasY(y) + imageOpener.FLD_SIZE/2,
            **kw
        )
    
    
    def drawBorder(self):
        model = self.model
        imageBG = imageOpener.getBackground(model.getBgBorder())
        # horizontal
        for x in range(-1, model.COLS+1):
            for y in (-1, model.ROWS):
                self.drawImage(x, y, imageBG, tags=(self.TAG_BORDER,))
        # vertical
        for x in (-2,-1, model.COLS,model.COLS+1):
            for y in range(-1, model.ROWS+1):
                self.drawImage(x, y, imageBG, tags=(self.TAG_BORDER,))
        
    def drawBoard(self):
        model = self.model
        isModeSolution = self.isModeEditSolution()
        
        if isModeSolution:
            solution = model.getSolution()
            visitedFields = solution.getBoardCoordinates()
            isFlipped     = solution.isFlipped()
        else:
            visitedFields = tuple(model.findAll(model.FLD_START))
            isFlipped     = False
        
        imageBg = imageOpener.getBackground(model.getBgUntouched())
        imageBgTouched = imageOpener.getBackground(model.getBgTouched())
        for x in range(model.COLS):
            for y in range(model.ROWS):
                fld = model.getField(x=x, y=y)
                if (x,y) in visitedFields:
                    tmp = imageBgTouched
                else:
                    tmp = imageBg

                if isFlipped:
                    y = model.ROWS - y - 1
                
                self.drawImage(x, y, image=tmp, tags=(self.TAG_BOARD,))
                if fld == model.FLD_EMPTY:
                    continue
                if fld == model.FLD_START and isModeSolution:
                    fld = self.OBJ_DOOR_OPEN
                    #TODO: do I want to draw the door or continue?
                    continue
                self.drawImage(x, y, image=imageOpener.getImage(fld), tags=(self.TAG_BOARD,))
                
                if not isModeSolution and self.viewObjectCode != self.OBJECT_CODE_OFF:
                    text = imageOpener.getImage.getShortName(fld),
                    self.drawRectangle(x, y, fill=self.textFill, stipple=self.textStipple, width=0)
                    self.drawText(x, y, text=text, font="-weight bold", tags=(self.TAG_BOARD,))

        if isModeSolution:
            x, y = visitedFields[-1]
            if isFlipped:
                y = model.ROWS - y - 1
            if self.model.isValidField(x, y):
                self.drawImage(x, y, image=imageOpener.getImage(self.OBJ_CAT), tags=(self.TAG_BOARD,))
            #TODO: else: draw indicator in which direction the cat is


    def drawCursor(self):
        if self.isModeEditSolution():
            return
        if   self.debugCursor == self.DEBUG_CURSOR_OFF:
            fill = self.cursorFill
            stipple = self.cursorStipple
            virtualCursorFill    = self.virtualCursorFill
            virtualCursorStipple = self.virtualCursorStipple
        elif self.debugCursor == self.DEBUG_CURSOR_REAL:
            fill       = self.textFill
            debugColor = self.cursorColor
            stipple    = self.textStipple
            virtualCursorFill       = self.textFill
            virtualCursorDebugColor = self.virtualCursorColor
            virtualCursorStipple    = self.textStipple
            indices = tuple(range(len(self.model.getCursors())))
        else:
            fill       = 'yellow'
            debugColor = 'red'
            stipple    = tkc.STIPPLE_GRAY_50
            if   self.debugCursor == self.DEBUG_CURSOR_LEFT_TO_RIGHT:
                indices = self.model.getCursors().getIndicesSortedLeftToRight()
            elif self.debugCursor == self.DEBUG_CURSOR_RIGHT_TO_LEFT:
                indices = self.model.getCursors().getIndicesSortedRightToLeft()
            elif self.debugCursor == self.DEBUG_CURSOR_TOP_TO_BOTTOM:
                indices = self.model.getCursors().getIndicesSortedTopToBottom()
            elif self.debugCursor == self.DEBUG_CURSOR_BOTTOM_TO_TOP:
                indices = self.model.getCursors().getIndicesSortedBottomToTop()
            else:
                assert False
        i = 0
        for x,y in self.model.getCursors():
            self.drawRectangle(x, y,
                width   = self.cursorWidth,
                outline = self.cursorColor,
                stipple = stipple,
                fill    = fill,
                tags = (self.TAG_CURSOR),
            )
            if self.debugCursor:
                self.drawText(x, y,
                    text = str(indices.index(i)),
                    font = "-weight bold",
                    fill = debugColor,
                    tags = (self.TAG_CURSOR),
                )
                i += 1

        if self.model.hasVirtualCursor():
            x,y = self.model.getVirtualCursor()

            self.drawRectangle(x, y,
                width   = self.virtualCursorWidth,
                outline = self.virtualCursorColor,
                stipple = virtualCursorStipple,
                fill    = virtualCursorFill,
                tags = (self.TAG_CURSOR),
            )
            if self.debugCursor:
                self.drawText(x, y,
                    text = 'v',
                    font = "-weight bold",
                    fill = virtualCursorDebugColor,
                    tags = (self.TAG_CURSOR),
                )
                i += 1

                


if __name__=='__main__':
    import model
    import logging
    
    ffn = "../_level-vorlagen/irka-%03d.afg" % 15
    m = model.Model()
    m.readFile(ffn, log=logging.log)

    b = Board(master=None, model=m)
    b.pack()
    b.update()
    b.center()
    b.mainloop()
