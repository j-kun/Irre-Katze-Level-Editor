#!/usr/bin/env python

# standard libraries
import os.path

# other libraries
import tkinter_extensions as tkx
tk  = tkx.tk
tkc = tkx.tkc
tkSimpleDialog = tkx.tkSimpleDialog

import locales
_ = locales._

import gui_image_opener as imageOpener
import gui_catalog

import model
import model_object_catalog as objects



# ==================== Raw View ====================

class SolutionViewRaw(tk.Canvas):

    ICON_PATH_SMALL = imageOpener.toAbsPath(os.path.join("icons", "small"))
    ICON_EXT  = '.gif'

    COL_STEP_NUMBER = 0
    COL_ICON = COL_STEP_NUMBER + 1
    COL_TEXT = COL_ICON + 1
    COL_COORDINATES = 'cor'

    PAD_LEFT = 3
    PAD_RIGHT = 3
    PAD_X = 10
    PAD_X_COR  = PAD_X*2
    PAD_X_LINE = 2
    PAD_X_CURSOR = PAD_X_LINE

    PAD_TOP = 3
    PAD_BOTTOM = 3
    PAD_Y =  5
    PAD_Y_SEL = 2
    
    WIDTH_COR = 50
    WIDTH_CURSOR = 16
    HEIGHT_CURSOR = WIDTH_CURSOR
    HEIGHT_ROW = 32

    COLOR_SELECTION_FILL    = '#D1E3F5'
    COLOR_SELECTION_OUTLINE = '#4A90D9'
    
    # canvas text: fill = text color
    KW_COR_UNSELECTED = dict(fill='gray')
    KW_COR_SELECTED   = dict(fill='black')
    KW_COR_INVALID_UNSELECTED = dict(fill='orange')
    KW_COR_INVALID_SELECTED   = dict(fill='red')

    KW_STEP_NUMBER = dict()
    KW_STEP_TEXT   = dict()
    KW_INFO        = dict()

    ALIGN_CENTER = tk.CENTER
    ALIGN_LEFT   = tk.W
    ALIGN_RIGHT  = tk.E

    IMG_CURSOR = 'cursor'
    IMG_DOOR   = 'door'

    TAG_COR = 'coordinate'
    TAG_SEL = 'mycursor'
    TAG_INVALID = 'invalid'


    # ---------- initialization ----------

    def __init__(self, master, model, **kw):
        kw.setdefault('takefocus', True)
        tk.Canvas.__init__(self, master, **kw)
        self.model = model
        self.solution = model.getSolution()
        self.solution.addOnCursorChangeListener(self.onCursorChange)
        self.solution.addOnStepsChangeListener(self.onStepsChange)

        # memory initialization
        self._lastWidth = 1
        self._gridWidgets = list()
        self._colWidths = [0, 0, 0]
        self._colAligns = [self.ALIGN_RIGHT, self.ALIGN_CENTER, self.ALIGN_LEFT]
        self._x         = [0, 0, 0]
        self._x0        = self.PAD_LEFT + self.WIDTH_CURSOR
        self._labelNoStepsExisting = None
        self._lastCursorMain = self.solution.getCursorMain()
        self._lastCursorSecondary = self.solution.getCursorSecondary()        

        # preparation
        self._createIcons()

        # bind
        s = self.solution

        # move cursor
        self.bind('<Button-1>', self._onClick)
        
        for up, down in (('w', 's'), ('a', 'd')):
            seq = lambda key: '<%s>' % key
            self.bind(seq(up),   lambda e: s.moveCursorUp())
            self.bind(seq(down), lambda e: s.moveCursorDown())

            seq = lambda key: '<%s>' % key.upper() if key.islower() else '<Shift-%s>' % key
            self.bind(seq(up),   lambda e: s.expandCursorUp())
            self.bind(seq(down), lambda e: s.expandCursorDown())
        
        self.bind('<Home>', lambda e: s.moveCursorToTop())
        self.bind('<End>',  lambda e: s.moveCursorToBottom())
        
        self.bind('<Shift-Home>', lambda e: s.expandCursorToTop())
        self.bind('<Shift-End>',  lambda e: s.expandCursorToBottom())

        self.bind('<Escape>', lambda e: s.cursorNoRange())

        # change solution
        self.bind('<Left>',  lambda e: self.solution.insertStep(self.solution.STEP_LEFT))
        self.bind('<Right>', lambda e: self.solution.insertStep(self.solution.STEP_RIGHT))
        self.bind('<Up>',    lambda e: self.solution.insertStep(self.solution.STEP_UP))
        self.bind('<Down>',  lambda e: self.solution.insertStep(self.solution.STEP_DOWN))
        
        self.bind('<%s>' % chr(objects.OBJ_PIPE),   lambda e: self.insertPipeJump())
        self.bind('<%s>' % chr(objects.OBJ_HELIUM), lambda e: self.insertHeliumJump())

        self.bind('<BackSpace>', lambda e: self.solution.deleteStepAbove())
        self.bind('<Delete>',    lambda e: self.solution.deleteStepBelow())

        self.bind('<Control-z>', lambda e: self.solution.history.undo())
        self.bind('<Control-Z>', lambda e: self.solution.history.redo())


    def _createIcons(self):
        ffn  = lambda name: os.path.join(self.ICON_PATH_SMALL, name+self.ICON_EXT)
        self._iconsSmall = {
            model.Solution.STEP_LEFT  : tk.PhotoImage(file=ffn('arrow_left')),
            model.Solution.STEP_RIGHT : tk.PhotoImage(file=ffn('arrow_right')),
            model.Solution.STEP_UP    : tk.PhotoImage(file=ffn('arrow_up')),
            model.Solution.STEP_DOWN  : tk.PhotoImage(file=ffn('arrow_down')),
            
            model.PipeJump            : tk.PhotoImage(file=ffn('jump_pipe')),
            model.HeliumJump          : tk.PhotoImage(file=ffn('jump_helium')),
            model.AmbiguousJumpStep   : tk.PhotoImage(file=ffn('jump_ambiguous')),
            model.IllegalJumpStep     : tk.PhotoImage(file=ffn('jump_illegal')),
            
            self.IMG_CURSOR           : tk.PhotoImage(file=ffn('cursor')),
            self.IMG_DOOR             : tk.PhotoImage(file=ffn('door')),
        }


    # ---------- listener ----------

    def onCursorChange(self):
        self.drawSelection()

    def onStepsChange(self):
        self.drawSteps()
        self.update_idletasks()
        self.drawCoordinates(self.winfo_width())

    def _onConfigure(self, event):
        if self._lastWidth != event.width:
            self._lastWidth = event.width
            self.drawCoordinates(event.width)


    def bindOnConfigure(self):
        self.__bindID_configure = self.bind('<Configure>', self._onConfigure)

    def unbindOnConfigure(self):
        self.unbind('<Configure>', self.__bindID_configure)


    # ---------- user input listener ----------

    def _onClick(self, event):
        x = self._xClick
        y = self.canvasy(event.y)
        items = self.find_closest(x, y)
        if len(items) == 1:
            i = self._coordinateIDs.index(items[0])
            if event.state & tkc.MODIFIER_MASK_SHIFT_ONLY:
                setCursor = self.solution.expandCursorTo
            else:
                setCursor = self.solution.moveCursorTo
            assert setCursor(i)
        else:
            assert False

    #TODO: right click: change number of steps of helium jump, resolve ambiguous jump


    def insertHeliumJump(self):
        dy = tkSimpleDialog.askinteger(
            title = iconOpener.getLongName(SolutionEditor.ACT_JUMP_HELIUM),
            prompt = _("Please insert the number of fields which the helium pushes you upward"),
        )
        self.focus_set()
        
        if dy == None:
            return
        if dy <= 0:
            return
        
        self.solution.insertStep(model.HeliumJump(-dy))

    def insertPipeJump(self):
        self.solution.insertStep(model.PipeJump())
    

    # ---------- cursor ----------

    def getCursorCanvasBbox(self):
        """returns (x0, y0, x1, y1) in canvas coordinates [not widget coordinates]"""
        # Canvas.bbox returns (x0, y0, x1, y1)  [unlike grid_bbox which returns (x0, y0, width, height)]
        bbox  = list(self.bbox(self._coordinateIDs[self.solution.getCursorMain()]))
        bbox2 = list(self.bbox(self._coordinateIDs[self.solution.getCursorSecondary()]))
        
        bbox[0] = min(bbox[0], bbox2[0])
        bbox[1] = min(bbox[1], bbox2[1])
        bbox[2] = max(bbox[2], bbox2[2])
        bbox[3] = max(bbox[3], bbox2[3])
        
        return bbox
    

    # ---------- draw ----------
    
    def drawSteps(self):
        n = len(self._gridWidgets)
        
        stepNumber = 0
        row = None
        for row, step in enumerate(self.solution.iterSteps(), 0):
            if row < n:
                widgets = self._gridWidgets[row]
            else:
                y = self.getRowCenterY( row )
                widgets = list()
                widgets.append( self._mycreate(self.create_text,  self.COL_STEP_NUMBER, y, **self.KW_STEP_NUMBER) )
                widgets.append( self._mycreate(self.create_text,  self.COL_TEXT, y, **self.KW_STEP_TEXT) )
                widgets.append( self._mycreate(self.create_image, self.COL_ICON, y) )
                self._gridWidgets.append( widgets )
            
            if not step.isUncountedJump():
                stepNumber += 1
                self.itemconfigure(widgets[0], text="%s)"%stepNumber)
            else:
                self.itemconfigure(widgets[0], text="")
            
            self.itemconfigure(widgets[1], text=self.getText(step))
            self.itemconfigure(widgets[2], image=self.getSmallIcon(step))

        if row == None:
            numberRowsToBeRemoved = n
        else:
            numberRowsToBeRemoved = n - row - 1
        for _dummy in range( numberRowsToBeRemoved ):
            for widget in self._gridWidgets[-1]:
                self.delete(widget)
            del self._gridWidgets[-1]

        # set x coorinate
        x = self._x0 + self.PAD_X_CURSOR
        for col in range(len(self._colWidths)):
            # calculate width
            width = self.getWidth(self.getTagColumn(col))
            self._colWidths[col] = width

            # align
            align = self._colAligns[col]
            if align == self.ALIGN_LEFT:
                newx = x
            elif align == self.ALIGN_CENTER:
                newx = x + width/2
            elif align == self.ALIGN_RIGHT:
                newx = x + width
            else:
                assert False
            
            if newx != self._x[col]:
                dx = newx - self._x[col]
                self._x[col] = newx
                self.move(self.getTagColumn(col), dx, 0)
            
            x += width + self.PAD_X
        
        self._xLast = x - self.PAD_X + self.PAD_X_COR

        if row == None:
            if self._labelNoStepsExisting == None:
                x = self._x0 + self.PAD_X_CURSOR
                y = self.getRowCenterY(0.5)
                #TODO: center (place real label)
                self._labelNoStepsExisting = self.create_text(x,y, anchor=self.ALIGN_LEFT, text=_("(No steps existing yet)"), **self.KW_INFO)
                width = self.getWidth(self._labelNoStepsExisting)
                self._xLast = x + width
            return
        
        elif self._labelNoStepsExisting != None:
            self.delete(self._labelNoStepsExisting)
            self._labelNoStepsExisting = None

    def _mycreate(self, createMethod, col, y, **kw):
        return createMethod(self._x[col], y, tags=[self.getTagColumn(col)], anchor=self._colAligns[col], **kw)


    def drawCoordinates(self, width=None):
        # clear
        self.delete(self.TAG_COR)

        # measure
        if width == None:
            width = self.winfo_width()
        xRight = max(width, self.getReqWidth()) - self.PAD_RIGHT
        xLine = xRight - self.WIDTH_COR - self.PAD_X_LINE
        xCor  = xRight - self.WIDTH_COR/2
        x0    = self._x0

        # save for drawSelection
        self._x1 = xLine

        # save for _onClick
        self._xClick = xCor

        # definition
        self._coordinateIDs = list()
        def drawCoordinate(i):
            y = self.getCoordinateCenterY(i)
            if cor == model.Solution.COR_END:
                corID = self.create_image(xCor, y, image=self.getSmallIcon(self.IMG_DOOR), anchor=tk.CENTER, tags=[self.TAG_COR, self.getTagColumn(self.COL_COORDINATES)])
            else:
                if self.model.isValidField(*cor):
                    kw = self.KW_COR_UNSELECTED
                    tags = (self.TAG_COR,)
                else:
                    kw = self.KW_COR_INVALID_UNSELECTED
                    tags = (self.TAG_COR, self.TAG_INVALID)
                corID = self.create_text(xCor, y, text=self.coordinateToText(cor), anchor=tk.CENTER, tags=tags, **kw)
            self._coordinateIDs.append(corID)
            self.create_line(x0,y, xLine,y, fill="gray", dash=(4, 4), tags=(self.TAG_COR,))

        # execution
        for i, cor in enumerate(self.solution.iterViewCoordinates()):
            drawCoordinate(i)

        # adjust width
        width = self.getWidth( self.getTagColumn(self.COL_COORDINATES) )
        # the width can vary a little depending on the coordinates. this correction is intended to correct platform dependent changes, not dynamic changes. therefore it should stay rather constant at runtime.
        self.WIDTH_COR = max(self.WIDTH_COR, width)

        # draw cursor
        self.drawSelection()


    def drawSelection(self):
        # clear last selection
        self.delete(self.TAG_SEL)

        if self._lastCursorMain < len(self._coordinateIDs):
            itemID = self._coordinateIDs[self._lastCursorMain]
            if self.type(itemID) == tkc.TYPE_TEXT:
                if self.TAG_INVALID not in self.gettags(itemID):
                    kw = self.KW_COR_UNSELECTED
                else:
                    kw = self.KW_COR_INVALID_UNSELECTED
                self.itemconfig(itemID, **kw)

        # configure existing objects
        self._lastCursorMain = self.solution.getCursorMain()
        self._lastCursorSecondary = self.solution.getCursorSecondary()

        itemID = self._coordinateIDs[self._lastCursorMain]
        if self.type(itemID) == tkc.TYPE_TEXT:
            if self.TAG_INVALID not in self.gettags(itemID):
                kw = self.KW_COR_SELECTED
            else:
                kw = self.KW_COR_INVALID_SELECTED
            self.itemconfig(itemID, **kw)

        # measure
        # grid_bbox returns (x0, y0, width, height)  [unlike Canvas.bbox which returns (x0, y0, x1, y1)]
        rowCursorMain = self.solution.getCursorMain()
        rowCursorSecondary = self.solution.getCursorSecondary()
        yStart = self.getCoordinateCenterY( min(rowCursorMain, rowCursorSecondary) )
        if rowCursorMain != rowCursorSecondary:
            yEnd = self.getCoordinateCenterY( max(rowCursorMain, rowCursorSecondary) )
        else:
            yEnd = yStart
        x0 = self._x0
        x1 = self._x1
        y0 = yStart - self.PAD_Y_SEL
        y1 = yEnd   + self.PAD_Y_SEL

        # draw on canvas
        self.create_rectangle(x0,y0, x1,y1, fill=self.COLOR_SELECTION_FILL, outline=self.COLOR_SELECTION_OUTLINE, width=0, tags=(self.TAG_SEL,))
        self.create_line(x0,y0, x1,y0, fill=self.COLOR_SELECTION_OUTLINE, tags=(self.TAG_SEL,))
        self.create_line(x0,y1, x1,y1, fill=self.COLOR_SELECTION_OUTLINE, tags=(self.TAG_SEL,))
        
        self.create_image(0, yEnd, image=self.getSmallIcon(self.IMG_CURSOR), anchor=tk.W, tags=(self.TAG_SEL,))

        self.tag_lower(self.TAG_SEL)
            

    # ---------- support ----------

    def getSmallIcon(self, step):
        return self._iconsSmall[self.getIconID(step)]

    def getTagColumn(self, col):
        return "col %s" % col
    

    def getRowCenterY(self, i):
        return self.PAD_TOP + 0.5*self.PAD_Y + i * (self.HEIGHT_ROW + self.PAD_Y) + 0.5*self.HEIGHT_ROW

    def getCoordinateCenterY(self, i):
        return self.PAD_TOP + i * (self.HEIGHT_ROW + self.PAD_Y)
    
    
    def getWidth(self, tag):
        # Canvas.bbox returns (x0, y0, x1, y1)  [unlike grid_bbox which returns (x0, y0, width, height)]
        bbox = self.bbox( tag )
        if bbox == None:
            return 0
        return bbox[2] - bbox[0]

    def getReqWidth(self):
        return self._xLast + self.WIDTH_COR + self.PAD_RIGHT

    def setWidthToReq(self):
        self.configure( width = self.getReqWidth() )
    
    
    @staticmethod
    def getText(step):
        if step == model.Solution.STEP_LEFT:
            return _("Left")
        if step == model.Solution.STEP_RIGHT:
            return _("Right")
        if step == model.Solution.STEP_UP:
            return _("Up")
        if step == model.Solution.STEP_DOWN:
            return _("Down")
        if isinstance(step, model.PipeJump) or step == model.PipeJump:
            return _("Smoke a pipe")
        if step == model.HeliumJump:
            return _("Carried upward by helium")
        if isinstance(step, model.HeliumJump):
            return _("Carried upward by helium ({dy} fields)").format(dy=abs(step.getDistanceY()))
        if isinstance(step, model.AmbiguousJumpStep):
            return _("Ambiguous Jump ({dx}, {dy})").format(dx=step.getDistanceX(), dy=step.getDistanceY())
        if isinstance(step, model.IllegalJumpStep):
            return _("Illegal Jump ({dx}, {dy})").format(dx=step.getDistanceX(), dy=step.getDistanceY())
        
        assert False

    @staticmethod
    def getIconID(step):
        if model.Solution.isNormalStep(step):
            return step
        elif isinstance(step, str):
            return step
        else:
            return type(step)

    @staticmethod
    def coordinateToText(cor):
        return "({x:2}, {y:2})".format(x=cor[0], y=cor[1])



# ==================== Scrollable Frame with Title ====================

class SolutionFrame(tkx.FrameWithTitle):

    PAD_Y_SCROLL = 2.5 * (SolutionViewRaw.HEIGHT_ROW + SolutionViewRaw.PAD_Y)

    # ---------- initialization ----------

    def __init__(self, master, model, **kw):
        tkx.FrameWithTitle.__init__(self, master, **kw)
        self.solution = model.getSolution()
        
        self.scrollbarVer = tkx.AutoScrollbar(self)
        self.scrollbarVer.grid(row=0, column=1, sticky=tk.NS)
        
        self.solutionView = SolutionViewRaw(self, model, selectborderwidth=0, highlightthickness=0)
        self.solutionView.grid(row=0, column=0, sticky=tk.NSEW)
        self.solution.addOnCursorChangeListener(self.onCursorChange)
        self.solution.addOnStepsChangeListener(self.onStepsChange)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.scrollbarVer.config(command = self.solutionView.yview)
        self.solutionView.config(yscrollcommand = self.scrollbarVer.set)
        self.mousewheelBinder = tkx.MousewheelBinder(self.solutionView)


    # ---------- internal methods ----------

    def updateScrollregion(self):
        self.solutionView.configure( scrollregion = self.solutionView.bbox(tk.ALL) )

    # @Override
    def focus_set(self):
        self.solutionView.focus_set()


    def scrollVerTo(self, canvas_bbox, pady=0):
        """canvas_bbox = (x0, y0, x1, y1)"""
        yVis0 = self.solutionView.canvasy(0)
        yVis1 = yVis0 + self._getViewPortHeight()
        yBox0 = canvas_bbox[1] - pady
        yBox1 = canvas_bbox[3] + pady
        if   yBox0 < yVis0:
            self.scrollUp(yBox0)
        elif yBox1 > yVis1:
            self.scrollDown(yBox1)

    def scrollUp(self, y):
        """scroll so that y is at top of visible area"""
        # Canvas.bbox returns (x0, y0, x1, y1)  [unlike grid_bbox which returns (x0, y0, width, height)]
        scrollregion = self.solutionView.bbox(tk.ALL)
        y0 = scrollregion[1]
        y1 = scrollregion[3]
        if y < y0:
            y = y0
        elif y > y1:
            y = y1
        self.solutionView.yview_moveto(float( y - y0 )/(y1 - y0))

    def scrollDown(self, y):
        """scroll so that y is at bottom of visible area"""
        self.scrollUp(y - self.solutionView.winfo_height())

    def _getViewPortHeight(self):
        return self.solutionView.winfo_height()
    

    # ---------- listener ----------
    
    def onCursorChange(self):
        # Canvas.bbox returns (x0, y0, x1, y1)  [unlike grid_bbox which returns (x0, y0, width, height)]
        bbox = self.solutionView.getCursorCanvasBbox()
        selHeight = bbox[3] - bbox[1]
        widgetHeight = self._getViewPortHeight()
        widgetHeight -= 2*self.PAD_Y_SCROLL
        if selHeight > widgetHeight:
            if self.solution.getCursorMain() > self.solution.getCursorSecondary():
                bbox[1] = bbox[3] - widgetHeight
            else:
                bbox[3] = bbox[1] + widgetHeight
        self.scrollVerTo(bbox, pady=self.PAD_Y_SCROLL)

    def onStepsChange(self):
        self.title(_("Solution: {numberSteps} Steps").format(numberSteps=len(self.solution)))
        self.updateScrollregion()
        #self.update_idletasks()
        self.onCursorChange()


    # ---------- methods to be called by controller ----------
    
    def onShow(self):
        self.solutionView.setWidthToReq()
        self.solutionView.focus_set()
        self.solutionView.bindOnConfigure()

    def onHide(self):
        self.solutionView.unbindOnConfigure()



# ==================== Solution Catalog ====================

class SolutionEditor(object):

    ACT_STEP_UP      = 'arrow_up'
    ACT_STEP_LEFT    = 'arrow_left'
    ACT_STEP_DOWN    = 'arrow_down'
    ACT_STEP_RIGHT   = 'arrow_right'

    ACT_JUMP_PIPE    = 'jump_pipe'
    ACT_JUMP_HELIUM  = 'jump_helium'

    ACT_DELETE_ABOVE = 'delete_above'
    ACT_DELETE_BELOW = 'delete_below'
    
    ACT_EXIT = 'exit'


SOLUTION_ACTIONS = (
    SolutionEditor.ACT_STEP_UP,
    SolutionEditor.ACT_STEP_LEFT,
    SolutionEditor.ACT_STEP_DOWN,
    SolutionEditor.ACT_STEP_RIGHT,

    gui_catalog.Catalog.ITEM_STRUT,

    SolutionEditor.ACT_JUMP_HELIUM,
    SolutionEditor.ACT_JUMP_PIPE,

    gui_catalog.Catalog.ITEM_STRUT,

    SolutionEditor.ACT_DELETE_ABOVE,
    SolutionEditor.ACT_DELETE_BELOW,

    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,
    gui_catalog.Catalog.ITEM_STRUT,

    SolutionEditor.ACT_EXIT,
)


class IconOpener(imageOpener.ImageOpener):

    NO_SHORTCUT = " "

    def __init__(self):
        imageOpener.ImageOpener.__init__(self,
            path = imageOpener.toAbsPath(os.path.join("icons", "big")),
            pattern = "{0}.gif",
            getLongName = SolutionViewRaw.getText,
        )

    # @Override
    def getShortName(self, name):
        '''Returns the shortcut to be displayed below the icon'''
        if name == SolutionEditor.ACT_JUMP_PIPE:
            return chr(objects.OBJ_PIPE)
        if name == SolutionEditor.ACT_JUMP_HELIUM:
            return chr(objects.OBJ_HELIUM)
        
        if name == SolutionEditor.ACT_STEP_UP:
            return _("Up")
        if name == SolutionEditor.ACT_STEP_LEFT:
            return _("Left")
        if name == SolutionEditor.ACT_STEP_DOWN:
            return _("Down")
        if name == SolutionEditor.ACT_STEP_RIGHT:
            return _("Right")
        
        if name == SolutionEditor.ACT_DELETE_ABOVE:
            return self.NO_SHORTCUT
            return _("Backspace")
        if name == SolutionEditor.ACT_DELETE_BELOW:
            return self.NO_SHORTCUT
            return _("Delete")

        if name == SolutionEditor.ACT_EXIT:
            return self.NO_SHORTCUT

        assert False


    # @Override
    def getLongName(self, name):
        '''Returns the tooltip to be displayed when hovering above the icon'''
        if name == SolutionEditor.ACT_JUMP_PIPE:
            return SolutionViewRaw.getText(model.PipeJump)
        if name == SolutionEditor.ACT_JUMP_HELIUM:
            return SolutionViewRaw.getText(model.HeliumJump)
        
        if name == SolutionEditor.ACT_STEP_UP:
            return SolutionViewRaw.getText(model.Solution.STEP_UP)
        if name == SolutionEditor.ACT_STEP_LEFT:
            return SolutionViewRaw.getText(model.Solution.STEP_LEFT)
        if name == SolutionEditor.ACT_STEP_DOWN:
            return SolutionViewRaw.getText(model.Solution.STEP_DOWN)
        if name == SolutionEditor.ACT_STEP_RIGHT:
            return SolutionViewRaw.getText(model.Solution.STEP_RIGHT)
        
        if name == SolutionEditor.ACT_DELETE_ABOVE:
            return _("Delete Step Above")
        if name == SolutionEditor.ACT_DELETE_BELOW:
            return _("Delete Step Below")

        if name == SolutionEditor.ACT_EXIT:
            return _("Exit Solution Editor")

        assert False

iconOpener = IconOpener()



# ==================== Test ====================

if __name__=='__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)-7s  %(message)s')
    
    m = model.Model()
    #m.setField(0, 0, m.FLD_START)
    m.readFile(imageOpener.toAbsPath(os.path.join('level-vorlagen', 'irka-013.afg')), logging.log)

    s = m.getSolution()
    
    root = tk.Tk()
    v = SolutionFrame(root, m, padx=5, pady=5)
    s.init(m)
    v.pack(expand=tk.YES, fill=tk.BOTH)
    v.onShow()
    
    root.mainloop()
