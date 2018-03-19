#!/usr/bin/env python

# future imports
try:
    from future_builtins import zip
except ImportError:
    pass

# standard libraries
import os
import re
import logging
from io import open

# other libraries
import model_history
import model_background_catalog as backgrounds

import model_object_catalog as objects
import gui_image_opener as imageOpener

import system
import locales
_ = locales._


LOGLEVEL_NONE = -1

class Logger(object):

    def __init__(self):
        self._logFunction = None

    def init(self, logFunction):
        assert self._logFunction == None
        self._logFunction = logFunction
        self.resetMaxUsedLogLevel()

    def log(self, logLevel, msg):
        self._logFunction(logLevel, msg)
        self.setMaxUsedLogLevel(logLevel)

    def setMaxUsedLogLevel(self, logLevel):
        self._maxLogLevel = max(self._maxLogLevel, logLevel)

    def getMaxUsedLogLevel(self):
        return self._maxLogLevel

    def resetMaxUsedLogLevel(self):
        self._maxLogLevel = LOGLEVEL_NONE

    def end(self):
        self._logFunction = None
        return self._maxLogLevel


class CursorList(object):

    # ---------- initialization ----------
    
    def __init__(self):
        self.clear()

    def clear(self):
        self._cursors = list()


    def __str__(self):
        return str(self._cursors)


    # ---------- getters ----------

    def __getitem__(self, i):
        return self._cursors[i]

    def __len__(self):
        return len(self._cursors)

    def __in__(self, cursor):
        return cursor in self._cursors

    def index(self, cursor):
        return self._cursors.index(cursor)


    # ---------- setters ----------

    def __setitem__(self, index, cursor):
        self._cursors[index] = cursor
        
    def setLast(self, cursor):
        fromIndex = self._cursors.index(cursor)
        del self._cursors[fromIndex]
        self._cursors.append(cursor)
        

    def insert(self, index, cursor):
        self._cursors.insert(index, cursor)

    def append(self, cursor):
        self.insert(len(self), cursor)


    def remove(self, cursor):
        i = self._cursors.index(cursor)
        del self[i]

    def __delitem__(self, i):
        del self._cursors[i]
        
    def removeLast(self):
        del self[-1]



class Jump(object):

    def __init__(self, dx, dy):
        self._dx = dx
        self._dy = dy

    def flip(self):
        return Jump(self._dx, -self._dy)

    def jump(self, x, y):
        return x + self._dx, y + self._dy

    def isUncountedJump(self):
        return True

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self._dx == other._dx and self._dy == other._dy

    def __hash__(self):
        return hash((type(self), self._dx, self._dy))

    def __repr__(self):
        return "%s(%s,%s)" % (self.__class__.__name__, self._dx, self._dy)

    def getDistanceX(self):
        return self._dx

    def getDistanceY(self):
        return self._dy


class NormalStep(Jump):

    def __init__(self, dx, dy):
        assert abs(dx) + abs(dy) == 1
        Jump.__init__(self, dx, dy)

    def isUncountedJump(self):
        return False

class AmbiguousJumpStep(Jump):
    
     def isUncountedJump(self):
        return False

class IllegalJumpStep(Jump):
    
     def isUncountedJump(self):
        return False


class PipeJump(Jump):

    def __init__(self):
        pass

    def jump(self, x, y):
        return x, Model.ROWS - 1 - y

    def __repr__(self):
        return "%s()" % (self.__class__.__name__)

class HeliumJump(Jump):

    def __init__(self, dy):
        '''dy < 0. steps are flipped with board therefore a pipe jump must always point upward, which is negative y direction.'''
        assert dy < 0
        Jump.__init__(self, 0, dy)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self._dy)


class Solution(object):

    COR_END = 'end'

    STEP_UP    = NormalStep( 0, -1)
    STEP_DOWN  = NormalStep( 0,  1)
    STEP_LEFT  = NormalStep(-1,  0)
    STEP_RIGHT = NormalStep( 1,  0)

    _ATTRIBUTES_TO_BACKUP = (
        ('_coordinates', list),
        ('_steps', list),
        ('_cursorMain', None, model_history.UPDATE_LAST),
        ('_cursorSecondary', None, model_history.UPDATE_LAST),
    )


    # ---------- initialization ----------
    
    def __init__(self):
        self._onCursorChangeListener = list()
        self._onStepsChangeListener = list()
        self.history = model_history.History(self, self._ATTRIBUTES_TO_BACKUP, 30, self._onUndoOrRedo)
        self.clear()

    def clear(self):
        self.history.clear()
        self._coordinates = list()
        self._steps = None
        self._start = None
        self.isDirty = False
        
        # selection are indeces of self._steps which are not necessarily the same as for self._coordinates (because self._steps includes uncounted jumps)
        self._cursorMain = 0
        self._cursorSecondary = self._cursorMain
        

    def init(self, model):
        self.model = model
        self.model._hasChangedSinceSolutionEdit = False
        
        numberStartFields = model.count(model.FLD_START)
        assert numberStartFields == 1
        self._start = model.find(model.FLD_START)

        self._numberExistingPipes  = model.count(objects.OBJ_PIPE)
        self._numberExistingHelium = model.count(objects.OBJ_HELIUM)

        if self._steps == None:
            self._calculateSteps()
        else:
            self._updateCoordinates()

        if len(self.history) == 0:
            self.history.makeBackup()


    # ---------- listener ----------

    def addOnCursorChangeListener(self, listener):
        self._onCursorChangeListener.append(listener)

    def addOnStepsChangeListener(self, listener):
        self._onStepsChangeListener.append(listener)

    def _onCursorChanged(self):
        for listener in self._onCursorChangeListener:
            listener()

    def _onStepsChanged(self):
        self._updateCoordinates()
        self.history.makeBackup()
        self.notifyOnStepsChangedListener()

    def notifyOnStepsChangedListener(self):
        for listener in self._onStepsChangeListener:
            listener()


    def _onUndoOrRedo(self):
        self.notifyOnStepsChangedListener()
        self._onCursorChanged()


    # ---------- cursor ----------

    def cursorNoRange(self):
        if self._cursorSecondary == self._cursorMain:
            return False
        self._cursorSecondary = self._cursorMain
        self._onCursorChanged()
        return True

    
    # move cursor

    def moveCursorTo(self, i):
        if i < self.getCursorMin() or i > self.getCursorMax():
            return False
        self._cursorMain = i
        self._cursorSecondary = i
        self._onCursorChanged()
        return True
    
    def moveCursorUp(self):
        if self._cursorsCanBeDecreased(self._cursorMain, self._cursorSecondary):
            self._cursorMain      -= 1
            self._cursorSecondary -= 1
            self._onCursorChanged()
            return True
        return False

    def moveCursorDown(self):
        if self._cursorsCanBeIncreased(self._cursorMain, self._cursorSecondary):
            self._cursorMain      += 1
            self._cursorSecondary += 1
            self._onCursorChanged()
            return True
        return False

    def moveCursorToTop(self):
        dy = self.getCursorMin() - min(self._cursorMain, self._cursorSecondary)
        if dy == 0:
            return False
        self._cursorMain += dy
        self._cursorSecondary += dy
        self._onCursorChanged()

    def moveCursorToBottom(self):
        dy = self.getCursorMax() - max(self._cursorMain, self._cursorSecondary)
        if dy == 0:
            return False
        self._cursorMain += dy
        self._cursorSecondary += dy
        self._onCursorChanged()


    # expand cursor

    def expandCursorTo(self, i):
        if i < self.getCursorMin() or i > self.getCursorMax():
            return False
        self._cursorMain = i
        self._onCursorChanged()
        return True
    
    def expandCursorUp(self):
        if self._cursorsCanBeDecreased(self._cursorMain):
            self._cursorMain -= 1
            self._onCursorChanged()
            return True
        return False

    def expandCursorDown(self):
        if self._cursorsCanBeIncreased(self._cursorMain):
            self._cursorMain += 1
            self._onCursorChanged()
            return True
        return False

    def expandCursorToTop(self):
        y = self.getCursorMin()
        if self._cursorMain != y:
            self._cursorMain = y
            self._onCursorChanged()
            return True
        return False

    def expandCursorToBottom(self):
        y = self.getCursorMax()
        if self._cursorMain != y:
            self._cursorMain = y
            self._onCursorChanged()
            return True
        return False


    # internal helper

    def _cursorsCanBeDecreased(self, *cursors):
        n = self.getCursorMin()
        for c in cursors:
            if c <= n:
                return False
        return True
    
    def _cursorsCanBeIncreased(self, *cursors):
        n = self.getCursorMax()
        for c in cursors:
            if c >= n:
                return False
        return True


    def getCursorMin(self):
        return 0

    def getCursorMax(self):
        return len(self._steps)


    # ---------- getters ----------
    
    def __len__(self):
        return len(self._coordinates)

    def isInitialized(self):
        return self._steps != None

    def iterCoordinates(self):
        return self._coordinates

    def iterSteps(self):
        return self._steps


    def getCursorMain(self):
        return self._cursorMain

    def getCursorSecondary(self):
        return self._cursorSecondary
    

    def isFlipped(self):
        n = 0
        for i in range(self._cursorMain):
            if isinstance(self._steps[i], PipeJump):
                n += 1
        return n % 2


    # ---------- setters ----------

    def appendCoordinate(self, cor):
        self._coordinates.append(cor)
    

    def insertStep(self, step):
        if self._cursorMain != self._cursorSecondary:
            i0 = min(self._cursorMain, self._cursorSecondary)
            i1 = max(self._cursorMain, self._cursorSecondary)
            for i in range(i0, i1):
                self._steps[i] = step
            self._onStepsChanged()
            return
        
        index = self._cursorMain
        self._cursorMain      += 1
        self._cursorSecondary += 1
        self._steps.insert(index, step)
        self._onStepsChanged()


    def deleteStepAbove(self):
        if self._cursorMain != self._cursorSecondary:
            return self._deleteSelectedRange()

        if self._cursorMain <= self.getCursorMin():
            # cursor is at top => can not remove something above
            return False

        self._cursorMain      -= 1
        self._cursorSecondary -= 1
        del self._steps[self._cursorMain]
        self._onStepsChanged()
        return True

    def deleteStepBelow(self):
        if self._cursorMain != self._cursorSecondary:
            return self._deleteSelectedRange()

        if self._cursorMain >= self.getCursorMax():
            # cursor is at bottom => can not remove something below
            return False
        
        del self._steps[self._cursorMain]
        self._onStepsChanged()
        return True

    def _deleteSelectedRange(self):
        i0 = min(self._cursorMain, self._cursorSecondary)
        i1 = max(self._cursorMain, self._cursorSecondary)
        
        for i in range(i0, i1):
            del self._steps[i0]
            # because I am removing element i0, the initially i-th element becomes element i0
        
        self._cursorMain      = i0
        self._cursorSecondary = i0
        self._onStepsChanged()
        return True


    # ---------- calculations ----------

    def _updateCoordinates(self):
        self._coordinates = self._calculateCoordinates()

    def _calculateSteps(self):
        self._steps = list()
        lastX, lastY = self._start
        isFlipped = False
        notIsFlipped = lambda: not isFlipped if isFlipped != None else None
        for x, y in self.iterCoordinates():
            dx = x - lastX
            dy = y - lastY
            
            if (dx == 0 and abs(dy) == 1) or (dy == 0 and abs(dx) == 1):
                # normal step
                step = NormalStep(dx, dy)
                
                # combined jump
                # (1) pipe jump (2) helium jump (3) normal step
                if self._numberExistingPipes > 0  and  self._numberExistingHelium > 0:
                    # the following checks are not all-encompassing but if they are positive there is a good chance this really is a combined jump
                    # pipes can fall
                    # helium can float upward from deeper below (or it's way might be blocked by other objects or it's way might be free because other objects in between have fallen away)
                    # to say anything for sure I would need to implement the entire game physics including all exceptions which certain objects have
                    if self.model.getField(lastX, lastY) == objects.OBJ_PIPE:
                        # check if field above is helium. above, because the pipe flips the board before the helium jump can happen.
                        _step = self.STEP_UP
                        if isFlipped:
                            _step = _step.flip()
                        xAbovePipe, yAbovePipe = _step.jump(lastX, lastY)
                        if self.model.isValidField(xAbovePipe, yAbovePipe) and self.model.getField(xAbovePipe, yAbovePipe) == objects.OBJ_HELIUM:
                            pipeJump = PipeJump()
                            xAfterPipe, yAfterPipe = pipeJump.jump(lastX, lastY)
                            dyPipe = yAfterPipe - lastY
                            if dx == 0:
                                # you can not move down after a helium jump, because the helium is below you
                                step = self.STEP_UP
                            dyHelium = dy - dyPipe - step.getDistanceY()
                            if dyHelium < 0:
                                self._steps.append(pipeJump)
                                self._steps.append(HeliumJump(dyHelium))
                                isFlipped = notIsFlipped()
                
                self._steps.append(step)
            
            elif abs(dx) > 1:
                # illegal jump
                self._steps.append(IllegalJumpStep(dx, dy))

            else:
                pipeJump = None
                heliumJump = None
                dyCombinedJump = None

                # pipe jump
                if self.isPipeJumpPossible(lastX, lastY, isFlipped):
                    pipeJump = PipeJump()
                    xAfterPipe, yAfterPipe = pipeJump.jump(lastX, lastY)
                    try:
                        step = NormalStep(x - xAfterPipe, y - yAfterPipe)
                    except AssertionError:
                        pipeJump = None
                        step = None

                # combined jump
                    if self.isHeliumJumpPossible(xAfterPipe, yAfterPipe, notIsFlipped()):
                        # (1) pipe jump (2) helium jump (3) normal step
                        if dx == 0:
                            # you can not move down after a helium jump, because the helium is below you
                            stepAfterCombinedJump = self.STEP_UP
                        else:
                            stepAfterCombinedJump = NormalStep(dx, 0)
                        dyCombinedJump = y - yAfterPipe - stepAfterCombinedJump.getDistanceY()

                # helium jump
                if self.isHeliumJumpPossible(lastX, lastY, isFlipped) \
                and dy < 0:
                    if dx == 0:
                        # you can not move down after a helium jump, because the helium is below you
                        step = self.STEP_UP
                        heliumJump = HeliumJump(dy - step.getDistanceY())
                    elif abs(dx) == 1:
                        step = NormalStep(dx, 0)
                        heliumJump = HeliumJump(dy)

                # decide which possibility to assume
                if heliumJump == None and pipeJump == None and dyCombinedJump == None:
                    # not possible
                    self._steps.append(IllegalJumpStep(dx, dy))
                    isFlipped = None
                
                elif heliumJump == None and pipeJump == None:
                    # combined jump
                    self._steps.append(PipeJump())
                    self._steps.append(HeliumJump(dyCombinedJump))
                    self._steps.append(stepAfterCombinedJump)
                    isFlipped = notIsFlipped()
                
                elif pipeJump == None and dyCombinedJump == None:
                    # helium jump
                    self._steps.append(heliumJump)
                    self._steps.append(step)
                    
                elif heliumJump == None and dyCombinedJump == None:
                    # pipe jump
                    self._steps.append(pipeJump)
                    self._steps.append(step)
                    isFlipped = notIsFlipped()

                elif heliumJump == None:
                    # either pipe jump or combined jump
                    # doesn't really matter which one, important is that board is flipped
                    # therefore I am choosing the easier one
                    #TODO: which one is more likely?

                    # pipe jump
                    self._steps.append(pipeJump)
                    self._steps.append(step)
                    isFlipped = notIsFlipped()
                    
                else:
                    # unsure
                    self._steps.append(AmbiguousJumpStep(dx, dy))
                    isFlipped = None
                
            lastX = x
            lastY = y


    def isPipeJumpPossible(self, lastX, lastY, isFlipped):
        #TODO? improve accuracy: pipe must be in a triangle above (from where it can fall down), *if* there are no other pipes
        return self._numberExistingPipes  > 0

    def isHeliumJumpPossible(self, lastX, lastY, isFlipped):
        #TODO? improve accuracy: no unmovable objects in between => change isBelow
        return self._numberExistingHelium > 0 and self.model.isBelow((lastX, lastY), objects.OBJ_HELIUM, isFlipped = isFlipped)


    def _calculateCoordinates(self):
        '''Coordinates are flipped after pipe jump, fitting to how it is drawn on the board.
        Coordinates corresponds to step number.
        Omits start coordinate.
        '''
        cors = list()
        cor = self._start
        for i, step in enumerate(self._steps):
            cor = step.jump(*cor)
            if not step.isUncountedJump():
                cors.append(cor)
        return cors

    def getBoardCoordinates(self):
        '''Absolute board coordinates (unflipped).
        Includes intermediate results of uncounted jumps.
        Breaks at cursor!'''
        cors = list()
        cor = self._start
        isFlipped = False
        
        cors.append(cor)
        for i, step in enumerate(self._steps):
            if i == self._cursorMain:
                break
            if isinstance(step, PipeJump):
                isFlipped = not isFlipped
            else:
                if isFlipped:
                    cor = step.flip().jump(*cor)
                else:
                    cor = step.jump(*cor)
            cors.append(cor)
        return cors

    def iterViewCoordinates(self):
        '''Coordinates are flipped after pipe jump, fitting to how it is drawn on the board.
        Includes intermediate results of uncounted jumps.
        Yields COR_END instead of coordinate on a door.'''
        cor = self._start
        isFlipped = False
        
        yield cor
        for i, step in enumerate(self._steps):
            if isinstance(step, PipeJump):
                isFlipped = not isFlipped
            cor = step.jump(*cor)
            if self.model.isEndField(cor, isFlipped):
                yield self.COR_END
            else:
                yield cor

    def iterIsFlipped(self):
        '''corresponds to iterCoordinates (_calculateCoordinates):
        corresponds to step number.
        Omits start coordinate.'''
        isFlipped = False
        for step in self._steps:
            if isinstance(step, PipeJump):
                isFlipped = not isFlipped
            elif not step.isUncountedJump():
                yield isFlipped


    # ---------- sanity check ----------

    @staticmethod
    def isNormalStep(step):
        if step in (Solution.STEP_UP, Solution.STEP_DOWN, Solution.STEP_LEFT, Solution.STEP_RIGHT):
            return True
        return False

    @classmethod
    def isValidStepOrJump(cls, step):
        if cls.isNormalStep(step):
            return True
        if isinstance(step, (PipeJump, HeliumJump, AmbiguousJumpStep)):
            return True
        return False

    def sanityCheck(self, log):
        self.model._logger.init(log)
        log = self.model._logger.log
        error = lambda msg: log(logging.ERROR, msg)

        i = 1
        numberPipeJumps = 0
        numberHeliumJumps = 0
        lastStep = None
        for step in self.iterSteps():
            if lastStep == None:
                if isinstance(step, PipeJump):
                    error(_("first step can not be a pipe jump"))
                elif isinstance(step, HeliumJump):
                    error(_("first step can not be a helium jump"))
            
            if not self.isValidStepOrJump(step):
                error(_("invalid jump in step {stepNumber}: {jump}").format(stepNumber=i, jump=step))
            elif isinstance(step, AmbiguousJumpStep):
                log(logging.WARNING, _("ambiguous jump in step {stepNumber}").format(stepNumber=i))
            elif isinstance(step, PipeJump):
                numberPipeJumps += 1
            elif isinstance(step, HeliumJump):
                numberHeliumJumps += 1
            
            if not step.isUncountedJump():
                i += 1
            
            lastStep = step
        assert i-1 == len(self)

        if numberHeliumJumps >= 1 and self._numberExistingHelium == 0:
            error(_("{numberHeliumJumps} helium jump(s) without helium").format(numberHeliumJumps=numberHeliumJumps))

        if numberPipeJumps > self._numberExistingPipes:
            error(_("smoked more pipes than are existing: {numberSmokedPipes}/{numberExistingPipes}").format(numberSmokedPipes=numberPipeJumps, numberExistingPipes=self._numberExistingPipes))

        forbiddenFields = self.model.getForbiddenFields()
        lastCor = (None, None)
        lastCorIsFlipped = False
        i = 1
        for cor, isFlipped in zip(self.iterCoordinates(), self.iterIsFlipped()):
            if self.model.isEndField(lastCor, lastCorIsFlipped):
                # I am checking this for the last performed step because this is not an error for the last step of the solution
                iLast = i - 1
                error(_("steps on door in step {i} ({x},{y})").format(i=iLast, x=lastCor[0], y=lastCor[1]))

            x, y = cor

            corBoard = self.model.flipCoordinate(cor) if isFlipped else cor
            if corBoard in forbiddenFields:
                # forbidden fields are on board => x,y can not be illegal coordinate => calling getField is save
                objDescr = objects.getObjectDescription(self.model.getField(*cor))
                error(_("steps on unmovable obstacle in step {i} ({x},{y}): {obj}").format(i=i, x=x, y=y, obj=objDescr))
            elif self.model.isAboveFire(cor, isFlipped):
                error(_("steps above fire in step {i} ({x},{y})").format(i=i, x=x, y=y))
            elif self.model.isBelowRain(cor, isFlipped):
                error(_("steps under rain in step {i} ({x},{y})").format(i=i, x=x, y=y))
            
            if x < 0:
                error(_("x coordinate too small after step {i} ({x},{y})").format(i=i, x=x, y=y))
            elif x >= Model.COLS:
                error(_("x coordinate too large after step {i} ({x},{y})").format(i=i, x=x, y=y))
            if y < 0:
                error(_("y coordinate too small after step {i} ({x},{y})").format(i=i, x=x, y=y))
            elif y >= Model.ROWS:
                error(_("y coordinate too large after step {i} ({x},{y})").format(i=i, x=x, y=y))

            lastCor = cor
            lastCorIsFlipped = isFlipped
            i += 1

        if self.model.hasEndField() and not self.model.isEndField(lastCor, isFlipped=lastCorIsFlipped):
            error(_("does not end on door"))

        #TODO: warning if helium makes you float over unvisited fields (this is not necessarily an error, though, because they might have been activated by moving objects or explosions)

        out = self.model._logger.end()
        self.isDirty = not out == LOGLEVEL_NONE
        return out



class Model(object):

    """
    The origin is in the top left corner.
    """

    EXT_TASK = '.afg'
    ENCODING = objects.ENCODING

    HEADER = u'35+\xa1\xb3/r\xe7!\xe6\xa7'

    COLS = 18
    ROWS = 10

    OFFSET_X = 1
    OFFSET_Y = 2

    FLD_EMPTY = objects.OBJ_NONE
    FLD_PIPE  = objects.OBJ_PIPE
    FLD_START = objects.OBJ_START
    FLD_END   = objects.OBJ_END

    CHANGE_CURSOR       = "cursor"
    CHANGE_BOARD        = "board"
    CHANGE_BG_TOUCHED   = "touched"
    CHANGE_BG_UNTOUCHED = "untouched"
    CHANGE_BG_BORDER    = "border"
    CHANGE_BG           = "backgrounds.all"
    CHANGE_AUTHOR       = "author"
    CHANGE_HAS_CHANGED  = "has-changed"
    CHANGE_ALL          = "*"
    

    # ---------- initialization ----------

    def __init__(self):
        self.onChangeListeners = set()
        self._logger = Logger()
        self.history = model_history.History(self, self._ATTRIBUTES_TO_BACKUP, 30, self._onUndoOrRedo)
        self.clipboard = None
        self.solution = Solution()
        self.solution.addOnStepsChangeListener( self.onSolutionChange )
        self.reset()

    def reset(self):
        self.history.clear()
        self.board     = self._createEmptyBoard()
        self._tmpBoard = self._createEmptyBoard()
        self.bgMargin    = "irka3_1a.fld"
        self.bgUntouched = "irka3_2a.fld"
        self.bgTouched   = "irka3_3a.fld"
        self.solution.clear()
        self.ffn = None
        self.author = ""
        self.notes = None

        if self.clipboard == None:
            self.cursors = CursorList()
            self.virtualCursor = None
            self._saveSelection()

        self._notificationsDisabled = False

        self._hasChanged = False
        self._hasChangedSinceSolutionEdit = False
        self.onChange(self.CHANGE_ALL, updateChangedFlag=False)

    def _createEmptyBoard(self):
        return list(list(self.FLD_EMPTY for i in range(self.ROWS)) for i in range(self.COLS))

    
    # ---------- history ----------

    _ATTRIBUTES_TO_BACKUP = (
        # name, function to make copy
        ('board',       lambda l: list(list(i) for i in l)),
        ('author',      None),
        ('bgMargin',    None),
        ('bgUntouched', None),
        ('bgTouched',   None),
        ('_hasChanged',   None),
        ('_hasChangedSinceSolutionEdit', None),
    )

    def makeBackup(self, change):
        if change in (self.CHANGE_CURSOR,):
            return
        self.history.makeBackup()

    def undo(self):
        self.history.undo()

    def redo(self):
        self.history.redo()
    
    def _onUndoOrRedo(self):
        self.onChange(self.CHANGE_ALL, performBackup=False, updateChangedFlag=False)
    

    # ---------- listener ----------

    def enableNotifications(self):
        '''remember to call onChange afterwards'''
        self._notificationsDisabled = False

    def disableNotifications(self):
        self._notificationsDisabled = True

    def notificationsAreDisabled(self):
        return self._notificationsDisabled

    def addOnChangeListener(self, func):
        self.onChangeListeners.add(func)

    def onCursorMoved(self):
        self.onChange(self.CHANGE_CURSOR)

    def onChange(self, change, performBackup=True, updateChangedFlag=True, clearTmpBoard=True):
        if self._notificationsDisabled:
            return
        if updateChangedFlag and change not in (self.CHANGE_CURSOR, self.CHANGE_HAS_CHANGED):
            self._hasChanged = True
            if clearTmpBoard:
                self._clearTmpBoard()
            if change in (self.CHANGE_BOARD, self.CHANGE_ALL):
                self._hasChangedSinceSolutionEdit = True
        for listener in self.onChangeListeners:
            listener(change)
        if performBackup:
            self.makeBackup(change)

    def onSolutionChange(self):
        if self._notificationsDisabled:
            return
        self._hasChanged = True
        # no, I do not want to change _hasChangedSinceSolutionEdit here
        self.onChange(self.CHANGE_HAS_CHANGED, performBackup=False)


    # ---------- setters & getters ----------
    
    def getField(self, x, y):
        return self.board[x][y]
        
    def setField(self, x, y, value):
        self.board[x][y] = value
        self.onChange(self.CHANGE_BOARD)

    def setFieldAtCursor(self, value):
        for x,y in self.cursors:
            self.board[x][y] = value
        self.onChange(self.CHANGE_BOARD)

    def count(self, value):
        return sum(l.count(value) for l in self.board)

    def isBelow(self, cor, value, isFlipped = False):
        # untested
        x, y = cor
        if isFlipped == None:
            rows = range(0, self.ROWS)
        elif isFlipped:
            rows = range(0, y)
        else:
            rows = range(y+1, self.ROWS)
        for y in rows:
            if self.getField(x, y) == value:
                return True
        return False

    def isAboveFire(self, cor, isFlipped):
        cor = Solution.STEP_DOWN.jump(*cor)
        if isFlipped:
            cor = self.flipCoordinate(cor)
        if not self.isValidField(*cor):
            return False
        return self.getField(*cor) == objects.OBJ_FIRE

    def isBelowRain(self, cor, isFlipped):
        cor = Solution.STEP_UP.jump(*cor)
        if isFlipped:
            cor = self.flipCoordinate(cor)
        if not self.isValidField(*cor):
            return False
        return self.getField(*cor) == objects.OBJ_RAIN

    def isEndField(self, cor, isFlipped=False):
        if not self.isValidField(*cor):
            return False
        if isFlipped:
            cor = self.flipCoordinate(cor)
        return self.getField(*cor) == self.FLD_END

    def find(self, value):
        for x in range(self.COLS):
            for y in range(self.ROWS):
                if self.getField(x, y) == value:
                    return x, y
        return None, None

    def findAll(self, value):
        for x in range(self.COLS):
            for y in range(self.ROWS):
                if self.getField(x, y) == value:
                    yield x, y

    def getStartField(self):
        return self.find(self.FLD_START)

    def getEndField(self):
        return self.find(self.FLD_END)

    def hasEndField(self):
        return self.getEndField()[0] != None

    def getBgBorder(self):
        return self.bgMargin
    def getBgUntouched(self):
        return self.bgUntouched
    def getBgTouched(self):
        return self.bgTouched

    def setBgBorder(self, name):
        self.bgMargin = name
        self.onChange(self.CHANGE_BG_BORDER)
    def setBgUntouched(self, name):
        self.bgUntouched = name
        self.onChange(self.CHANGE_BG_UNTOUCHED)
    def setBgTouched(self, name):
        self.bgTouched = name
        self.onChange(self.CHANGE_BG_TOUCHED)

    def getAuthor(self):
        return self.author
        
    def setAuthor(self, name):
        self.author = name
        self.onChange(self.CHANGE_AUTHOR)


    def getNotes(self):
        return self.notes

    def setNotes(self, notes):
        self.notes = notes


    def getFileName(self):
        return self.ffn

    def hasChanged(self):
        return self._hasChanged

    def getSolution(self):
        return self.solution


    def has(self, obj):
        return self.find(obj)[0] != None

    def hasOneOf(self, *objs):
        for obj in objs:
            if self.has(obj):
                return True
        return False

    def getForbiddenFields(self):
        # explosives can destroy any obstacle
        if (self.has(85) and self.has(86)) or self.has(106) or self.has(107) or self.has(108):
            return list()

        forbiddenFields = list()

        # --- unmovable obstacles ---
        for obj in (
            objects.OBJ_FIRE,
            objects.OBJ_RAIN,
            58, 59, # Rote Steine
            62,  # Blau-Gelbe Kugel
            55, 56,  # Buecher Regal
            57,  # Voller Muelleimer (leerer faellt auch nicht, ist aber verschiebbar)
            63,  # Volle Naehmaschine (leere faellt auch nicht, ist aber verschiebbar)
            89,  90, # Kassettenrekorder
            49, 105, # Diaprojektor
            196, # Voller Koffer (leerer faellt auch nicht, ist aber verschiebbar)
            228, # Voller Briefumschlag (leerer faellt auch nicht, ist aber verschiebbar)
        ):
            self.appendManyTo(forbiddenFields, self.findAll( obj ))


        # --- transformable unmovable obstacles ---
        
        # Hammer
        if not self.has(81):
            self.appendManyTo(forbiddenFields, self.findAll( 60 ))

        # Trommel verwandelt rot-gelb gemusterte Kugel in gelbe Kugel
        if not self.has(87):
            self.appendManyTo(forbiddenFields, self.findAll( 61 ))

        return forbiddenFields

    @staticmethod
    def appendManyTo(l, elements):
        for e in elements:
            l.append(e)


    # ---------- coordinates ----------

    def getFieldRightOf(self, cursor):
        x, y = cursor
        x += 1
        if x >= self.COLS:
            x = 0
        return x, y

    def getFieldLeftOf(self, cursor):
        x, y = cursor
        x -= 1
        if x < 0:
            x += self.COLS
        return x, y

    def getFieldBelowOf(self, cursor):
        x, y = cursor
        y += 1
        if y >= self.ROWS:
            y = 0
        return x, y

    def getFieldAboveOf(self, cursor):
        x, y = cursor
        y -= 1
        if y < 0:
            y += self.ROWS
        return x, y

    

    # ---------- clipboard ----------

    def copy(self):
        self.clipboard = list()
        for x,y in self.getCursors():
            self.clipboard.append(self.getField(x,y))
        logging.debug(_("copied %d values to clipboard") % len(self.clipboard))

    def paste(self, pasteEmpty):
        if self.clipboard == None:
            logging.warning(_("clipboard is empty"))
            return
        if len(self.clipboard) > len(self.cursors):
            logging.error(_("too many values in clipboard"))
            return
        elif len(self.clipboard) < len(self.cursors):
            logging.error(_("not enough values in clipboard"))
            return
        for i in range(len(self.cursors)):
            x,y = self.cursors[i]
            val = self.clipboard[i]
            if pasteEmpty or val != self.FLD_EMPTY:
                self.board[x][y] = val
        self.onChange(self.CHANGE_BOARD)

    def cut(self):
        self.copy()
        self.setFieldAtCursor(self.FLD_EMPTY)


    # ---------- make changes ----------

    # swap fields (Alt + Arrow)

    def swapFieldLeft(self):
        self._swapField(self.getFieldLeftOf , self.getCursorsForSwapLeft())
    
    def swapFieldRight(self):
        self._swapField(self.getFieldRightOf, self.getCursorsForSwapRight())
    
    def swapFieldUp(self):
        self._swapField(self.getFieldAboveOf, self.getCursorsForSwapUp())
    
    def swapFieldDown(self):
        self._swapField(self.getFieldBelowOf, self.getCursorsForSwapDown())
    
    def _swapField(self, getNextField, cursors):
        self.disableNotifications()

        cursors = tuple(cursors)
        self.moveCursor(getNextField)

        for c in cursors:
            n = getNextField(c)
            toBeMoved = self.getField(*c)
            tmp = self.getField(*n)
            self.setField(*c, value=tmp)
            self.setField(*n, value=toBeMoved)

        self.enableNotifications()
        self.onChange(self.CHANGE_BOARD)


    def getCursorsForSwapLeft(self):
        return self._getCursorsForSwap(
            getPrevField = self.getFieldRightOf,
            direction = -1,
            xy = lambda c0, c1: (c0, c1),
        )
            
    def getCursorsForSwapRight(self):
        return self._getCursorsForSwap(
            getPrevField = self.getFieldLeftOf,
            direction = +1,
            xy = lambda c0, c1: (c0, c1),
        )
            
    def getCursorsForSwapUp(self):
        return self._getCursorsForSwap(
            getPrevField = self.getFieldBelowOf,
            direction = -1,
            xy = lambda c0, c1: (c1, c0),
        )
            
    def getCursorsForSwapDown(self):
        return self._getCursorsForSwap(
            getPrevField = self.getFieldAboveOf,
            direction = +1,
            xy = lambda c0, c1: (c1, c0),
        )
            

    def _getCursorsForSwap(self, getPrevField, direction, xy):
        size0, size1 = xy(self.COLS, self.ROWS)
        if direction < 0:
            line = range(size0-1)
        else:
            line = range(size0-2, -1, -1)

        for c1 in range(size1):
            c0 = 0
            while xy(c0,c1) in self.cursors:
                c0 += 1
                if c0 >= size0:
                    break
            else:
                # (x,y) is *not* a cursor
                startField = xy(c0,c1)
                n = getPrevField(startField)
                while n != startField:
                    if n in self.cursors:
                        yield n
                    n = getPrevField(n)
                
                continue

            # entire row is selected
            for c0 in line:
                yield xy(c0,c1)


    # move fields (Shift + Alt + Arrow)

    def moveFieldLeft(self):
        self._moveField(self.getFieldLeftOf)
    
    def moveFieldRight(self):
        self._moveField(self.getFieldRightOf)
    
    def moveFieldUp(self):
        self._moveField(self.getFieldAboveOf)
    
    def moveFieldDown(self):
        self._moveField(self.getFieldBelowOf)
    

    def _moveField(self, getNextField):
        if not self.hasCursor():
            return

        if self._hasSelectionChanged():
            self._clearTmpBoard()

        selectedValues = list()
        for c in self.cursors:
            selectedValues.append(self.getField(*c))

        for x in range(0, self.COLS):
            for y in range(0, self.ROWS):
                if (x,y) not in self.cursors:
                    self._tmpBoard[x][y] = self.board[x][y]

        newCursors = CursorList()
        for c,v in zip(self.cursors, selectedValues):
            x,y = getNextField(c)
            self.board[x][y] = v
            newCursors.append((x,y))
        self.cursors = newCursors

        for x in range(0, self.COLS):
            for y in range(0, self.ROWS):
                if (x,y) not in self.cursors:
                    self.board[x][y] = self._tmpBoard[x][y]

        self._saveSelection()

        self.onChange(self.CHANGE_BOARD, clearTmpBoard=False)


    def _clearTmpBoard(self):
        self._tmpBoard = self._createEmptyBoard()

    def _saveSelection(self):
        self._tmpCursors = tuple(self.cursors)

    def _hasSelectionChanged(self):
        return len(self._tmpCursors) != len(self.cursors) \
            or not all(c0 == c1 for c0, c1 in zip(self._tmpCursors, self.cursors))

    
    # move fields to border (End + Shift + Alt + Arrow)
    
    def moveFieldToLeft(self):
        self.disableNotifications()
        
        for x in range(self.getCursorDistanceToLeft()):
            self.moveFieldLeft()
        
        self.enableNotifications()
        self.onChange(self.CHANGE_BOARD, clearTmpBoard=False)

    def moveFieldToRight(self):
        self.disableNotifications()
        
        for x in range(self.getCursorDistanceToRight()):
            self.moveFieldRight()
        
        self.enableNotifications()
        self.onChange(self.CHANGE_BOARD, clearTmpBoard=False)

    def moveFieldToTop(self):
        self.disableNotifications()
        
        for x in range(self.getCursorDistanceToTop()):
            self.moveFieldUp()
        
        self.enableNotifications()
        self.onChange(self.CHANGE_BOARD, clearTmpBoard=False)

    def moveFieldToBottom(self):
        self.disableNotifications()
        
        for x in range(self.getCursorDistanceToBottom()):
            self.moveFieldDown()
        
        self.enableNotifications()
        self.onChange(self.CHANGE_BOARD, clearTmpBoard=False)


    # ---------- background ----------

    __nextElement = staticmethod( lambda l, e, inc:  l[(l.index(e) + inc) % len(l)] )
    
    nextBgBorder    = lambda self:  self.setBgBorder(    self.__nextElement(backgrounds.CATEGORY_BORDER,    self.getBgBorder(),    +1) )
    nextBgUntouched = lambda self:  self.setBgUntouched( self.__nextElement(backgrounds.CATEGORY_UNTOUCHED, self.getBgUntouched(), +1) )
    nextBgTouched   = lambda self:  self.setBgTouched(   self.__nextElement(backgrounds.CATEGORY_TOUCHED,   self.getBgTouched(),   +1) )
    
    prevBgBorder    = lambda self:  self.setBgBorder(    self.__nextElement(backgrounds.CATEGORY_BORDER,    self.getBgBorder(),    -1) )
    prevBgUntouched = lambda self:  self.setBgUntouched( self.__nextElement(backgrounds.CATEGORY_UNTOUCHED, self.getBgUntouched(), -1) )
    prevBgTouched   = lambda self:  self.setBgTouched(   self.__nextElement(backgrounds.CATEGORY_TOUCHED,   self.getBgTouched(),   -1) )
    
    def nextBg(self):
        self.disableNotifications()

        self.nextBgBorder()
        self.nextBgUntouched()
        self.nextBgTouched()

        self.enableNotifications()
        self.onChange(self.CHANGE_BG)
    
    def prevBg(self):
        self.disableNotifications()

        self.prevBgBorder()
        self.prevBgUntouched()
        self.prevBgTouched()

        self.enableNotifications()
        self.onChange(self.CHANGE_BG)

    
    def setBgScheme(self, scheme):
        self.disableNotifications()

        out = False
        value = backgrounds.pattern_fn.format(fld=1, scheme=scheme)
        if value in backgrounds.CATEGORY_BORDER:
            self.setBgBorder(value)
            value = backgrounds.pattern_fn.format(fld=2, scheme=scheme)
            if value in backgrounds.CATEGORY_UNTOUCHED:
                self.setBgUntouched(value)
                value = backgrounds.pattern_fn.format(fld=3, scheme=scheme)
                if value in backgrounds.CATEGORY_TOUCHED:
                    self.setBgTouched(value)
                    out = True

        self.enableNotifications()
        self.onChange(self.CHANGE_BG)
        return out


    # ---------- cursor ----------

    # getters

    def getCursors(self):
        return self.cursors

    def getLastCursor(self):
        return self.cursors[-1]

    def getLastCursorX(self):
        return self.cursors[-1][0]

    def getLastCursorY(self):
        return self.cursors[-1][1]

    def hasCursor(self):
        return len(self.cursors) > 0
    
    
    def getCursorDistanceToLeft(self):
        return min(self.cursors, key=lambda p: p[0])[0]
    
    def getCursorDistanceToRight(self):
        return self.COLS - 1 - max(self.cursors, key=lambda p: p[0])[0]
    
    def getCursorDistanceToTop(self):
        return min(self.cursors, key=lambda p: p[1])[1]
    
    def getCursorDistanceToBottom(self):
        return self.ROWS - 1 - max(self.cursors, key=lambda p: p[1])[1]
    

    # explicit coordinates (Mouse Click)

    def setCursor(self, x, y):
        if not self.isValidField(x, y):
            return False
        self.cursors.clear()
        self.cursors.append((x, y))
        self.onCursorMoved()
        return True

    def addCursor(self, x, y):
        if not self.isValidField(x, y):
            return False
        if (x, y) in self.cursors:
            self.cursors.remove((x, y))
        self.cursors.append((x, y))
        self.onCursorMoved()
        return True

    def addCursorRange(self, x, y):
        if not self.isValidField(x, y):
            return False
        x0 = self.getLastCursorX()
        y0 = self.getLastCursorY()
        if x != x0 and y != y:
            return False

        dx = 1 if x > x0 else -1
        dy = 1 if y > y0 else -1
        for x1 in range(x0, x+dx, dx):
            for y1 in range(y0, y+dy, dy):
                if (x1, y1) not in self.cursors:
                    self.cursors.append((x1, y1))
        self.cursors.setLast((x,y))
        self.onCursorMoved()
        return True


    def toggleCursor(self, x, y):
        if not self.isValidField(x, y):
            return False
        if (x, y) in self.cursors:
            self.cursors.remove((x, y))
        else:
            self.cursors.append((x, y))
        self.onCursorMoved()
        return True



    # start fields

    CURSOR_START_FOR_RIGHT = (0, 0)
    CURSOR_START_FOR_DOWN  = (0, 0)
    CURSOR_START_FOR_LEFT  = (COLS-1, ROWS-1)
    CURSOR_START_FOR_UP    = (COLS-1, ROWS-1)
    COR_CENTER             = ((COLS-1)//2, (ROWS-1)//2)

    def moveCursorToStartForLeft(self):
        assert self.setCursor(*self.CURSOR_START_FOR_LEFT)
        self.onCursorMoved()

    def moveCursorToStartForRight(self):
        assert self.setCursor(*self.CURSOR_START_FOR_RIGHT)
        self.onCursorMoved()

    def moveCursorToStartForUp(self):
        assert self.setCursor(*self.CURSOR_START_FOR_UP)
        self.onCursorMoved()

    def moveCursorToStartForDown(self):
        assert self.setCursor(*self.CURSOR_START_FOR_DOWN)
        self.onCursorMoved()

    def moveCursorToCenter(self):
        assert self.setCursor(*self.COR_CENTER)
        self.onCursorMoved()
    

    # select object

    def moveCursorToField(self, fld):
        out = False
        for x, y in self.findAll(fld):
            self.setCursor(x, y)
            out = True
        return out


    # change number of cursors

    def selectNone(self):
        if len(self.cursors) == 0:
            return False
        self.cursors.clear()
        self.onCursorMoved()
        return True

    def selectFirst(self):
        if len(self.cursors) <= 1:
            return False
        cursor = self.cursors[0]
        self.cursors.clear()
        self.cursors.append(cursor)
        self.onCursorMoved()
        return True

    def selectLast(self):
        if len(self.cursors) <= 1:
            return False
        cursor = self.cursors[-1]
        self.cursors.clear()
        self.cursors.append(cursor)
        self.onCursorMoved()
        return True

    def selectAll(self):
        self.cursors.clear()
        for x in range(self.COLS):
            for y in range(self.ROWS):
                self.cursors.append((x, y))
        self.onCursorMoved()

    def removeLastCursor(self):
        if len(self.cursors) == 0:
            return False
        self.cursors.removeLast()
        self.onCursorMoved()
        return True


    # move cursors by one field (Arrow without modifiers)
    
    def moveCursorRight(self):
        if not self.hasCursor():
            self.moveCursorToStartForRight()
            return

        self.moveCursor(self.getFieldRightOf)

    def moveCursorLeft(self):
        if not self.hasCursor():
            self.moveCursorToStartForLeft()
            return

        self.moveCursor(self.getFieldLeftOf)

    def moveCursorDown(self):
        if not self.hasCursor():
            self.moveCursorToStartForDown()
            return

        self.moveCursor(self.getFieldBelowOf)

    def moveCursorUp(self):
        if not self.hasCursor():
            self.moveCursorToStartForUp()
            return

        self.moveCursor(self.getFieldAboveOf)


    def moveCursor(self, getNextField):
        for i in range(len(self.cursors)):
            self.cursors[i] = getNextField(self.cursors[i])

        self.onCursorMoved()


    # move cursors to border (End + Arrow)

    def moveCursorToLeft(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_LEFT)
        dx = - self.getCursorDistanceToLeft()
        self._moveCursors(dx, 0)

    def moveCursorToRight(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_RIGHT)
        dx = self.getCursorDistanceToRight()
        self._moveCursors(dx, 0)
    
    def moveCursorToTop(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_UP)
        dy = - self.getCursorDistanceToTop()
        self._moveCursors(0, dy)

    def moveCursorToBottom(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_DOWN)
        dy = self.getCursorDistanceToBottom()
        self._moveCursors(0, dy)

    def _moveCursors(self, dx, dy):
        '''WARNING: this function does not check for borders'''
        for i in range(len(self.cursors)):
            x, y = self.cursors[i]
            x += dx
            y += dy
            self.cursors[i] = (x, y)
        self.onCursorMoved()
        

    # select range (Shift + Arrow)

    def addOrRemoveCursorLeft(self):
        if not self.hasCursor():
            self.moveCursorToStartForLeft()
            return

        x, y = self.getFieldLeftOf(self.getLastCursor())
        self.addOrRemoveCursor(x, y)

    def addOrRemoveCursorRight(self):
        if not self.hasCursor():
            self.moveCursorToStartForRight()
            return

        x, y = self.getFieldRightOf(self.getLastCursor())
        self.addOrRemoveCursor(x, y)

    def addOrRemoveCursorAbove(self):
        if not self.hasCursor():
            self.moveCursorToStartForUp()
            return

        x, y = self.getFieldAboveOf(self.getLastCursor())
        self.addOrRemoveCursor(x, y)

    def addOrRemoveCursorBelow(self):
        if not self.hasCursor():
            self.moveCursorToStartForDown()
            return

        x, y = self.getFieldBelowOf(self.getLastCursor())
        self.addOrRemoveCursor(x, y)


    def addOrRemoveCursor(self, x, y):
        if not self.hasCursor():
            self.moveCursorToStartForRight()
            return

        cursor = (x, y)
        if not self.isValidField(x, y):
            return
        if cursor not in self.cursors:
            self.cursors.append(cursor)
        elif len(self.cursors)>=2 and cursor == self.cursors[-2]:
            self.cursors.removeLast()
        else:
            self.cursors.setLast(cursor)
        self.onCursorMoved()


    # select range to border (End + Shift + Arrow)

    def addCursorsTowardsLeft(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_LEFT)

        y = self.getLastCursorY()
        cursors = ((x,y) for x in range(self.getLastCursorX()-1, -1, -1))
        self.addCursorsIfNotExisting(cursors)

    def addCursorsTowardsRight(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_RIGHT)

        y = self.getLastCursorY()
        cursors = ((x,y) for x in range(self.getLastCursorX()+1, self.COLS))
        self.addCursorsIfNotExisting(cursors)

    def addCursorsTowardsTop(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_UP)

        x = self.getLastCursorX()
        cursors = ((x,y) for y in range(self.getLastCursorY()-1, -1, -1))
        self.addCursorsIfNotExisting(cursors)

    def addCursorsTowardsBottom(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_DOWN)

        x = self.getLastCursorX()
        cursors = ((x,y) for y in range(self.getLastCursorY()+1, self.ROWS))
        self.addCursorsIfNotExisting(cursors)

    def addCursorsIfNotExisting(self, cursors):
        for cursor in cursors:
            if cursor not in self.cursors:
                self.cursors.append(cursor)

        ##TODO: do I want this?
        #if self.getLastCursor() != cursor:
        #    self.cursors.setLast(cursor)

        self.onCursorMoved()


    # select area (Control + Shift + Arrow)

    def addOrRemoveCursorsLeft(self):
        if self.hasVirtualCursor():
            self.newCursorEnd()

        if not self.hasCursor():
            self.moveCursorToStartForLeft()
            return

        self.addOrRemoveCursors(self.getFieldLeftOf)

    def addOrRemoveCursorsRight(self):
        if self.hasVirtualCursor():
            self.newCursorEnd()

        if not self.hasCursor():
            self.moveCursorToStartForRight()
            return

        self.addOrRemoveCursors(self.getFieldRightOf)

    def addOrRemoveCursorsAbove(self):
        if self.hasVirtualCursor():
            self.newCursorEnd()

        if not self.hasCursor():
            self.moveCursorToStartForUp()
            return

        self.addOrRemoveCursors(self.getFieldAboveOf)

    def addOrRemoveCursorsBelow(self):
        if self.hasVirtualCursor():
            self.newCursorEnd()

        if not self.hasCursor():
            self.moveCursorToStartForDown()
            return

        self.addOrRemoveCursors(self.getFieldBelowOf)

    def addOrRemoveCursors(self, getNextField):
        getPrevField = self.getGetPrevField(getNextField)
        cursor = getNextField(self.getLastCursor())
        cursorPrev = getPrevField(self.getLastCursor())
        if len(self.cursors)>=2 and cursor in self.cursors and (cursorPrev not in self.cursors or self.cursors.index(cursor) > self.cursors.index(cursorPrev)):
            self.removeCursors(getPrevField)
        else:
            self.addCursors(getNextField)
        self.onCursorMoved()


    def addCursors(self, getNextField):
        i = len(self.cursors) - 1
        hasChanged = False
        while i >= 0:
            oldCursor = self.cursors[i]
            newCursor = getNextField(oldCursor)

            while newCursor in self.cursors:
                i1 = self.cursors.index(newCursor)
                if i1 < i:
                    del self.cursors[i1]
                    self.cursors.insert(i, newCursor)

                    if newCursor == oldCursor:
                        break
                    newCursor = getNextField(newCursor)
                else:
                    break

            else:
                self.cursors.insert(i+1, newCursor)
                hasChanged = True

            i -= 1

        if not hasChanged:
            oldCursor = self.cursors[-1]
            newCursor = getNextField(oldCursor)
            i1 = self.cursors.index(newCursor)
            del self.cursors[i1]
            self.cursors.append(newCursor)


    def getGetPrevField(self, getNextField):
        if getNextField == self.getFieldRightOf:
            getPrevField = self.getFieldLeftOf
        elif getNextField == self.getFieldBelowOf:
            getPrevField = self.getFieldAboveOf
        elif getNextField == self.getFieldLeftOf:
            getPrevField = self.getFieldRightOf
        elif getNextField == self.getFieldAboveOf:
            getPrevField = self.getFieldBelowOf
        else:
            assert False
        return getPrevField

    def removeCursors(self, getPrevField):
        toBeRemoved = list()
        for i in range(len(self.cursors)-1, -1, -1):
            c = self.cursors[i]
            c = getPrevField(c)
            if c not in self.cursors:
                toBeRemoved.append(i)

        if len(toBeRemoved) == 0:
            last = self.getLastCursor()
            if getPrevField == self.getFieldRightOf or getPrevField == self.getFieldLeftOf:
                shallBeRemoved = lambda c: c[0] == last[0]
            else:
                shallBeRemoved = lambda c: c[1] == last[1]
            for i in range(len(self.cursors)-1, -1, -1):
                if shallBeRemoved(self.cursors[i]):
                    toBeRemoved.append(i)

        for i in toBeRemoved:
            del self.cursors[i]


    # select area to border (End + Control + Shift + Arrow)

    def addCursorAreaTowardsLeft(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_LEFT)

        self.addCursorArea(-1, 0)
        
    def addCursorAreaTowardsRight(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_RIGHT)

        self.addCursorArea(+1, 0)

    def addCursorAreaTowardsTop(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_UP)

        self.addCursorArea(0, -1)

    def addCursorAreaTowardsBottom(self):
        if not self.hasCursor():
            self.cursors.append(self.CURSOR_START_FOR_DOWN)

        self.addCursorArea(0, +1)


    def addCursorArea(self, dx, dy):
        for i in range(len(self.cursors)-1, -1, -1):
            x,y = self.cursors[i]
            x += dx
            y += dy
            
            while self.isValidField(x, y) and (x,y) not in self.cursors:
                i += 1
                self.cursors.insert(i, (x,y))
                x += dx
                y += dy

        #TODO: set last cursor?

        self.onCursorMoved()


    # new cursor / virtual cursor (Control + Arrow)

    def hasVirtualCursor(self):
        return self.virtualCursor != None

    def getVirtualCursor(self):
        return self.virtualCursor


    def newCursorBegin(self):
        pass

    def newCursorApply(self):
        if self.virtualCursor == None:
            return

        if self.virtualCursor in self.cursors:
            self.cursors.remove(self.virtualCursor)

        self.cursors.append(self.virtualCursor)
        self.virtualCursor = None
        self.onCursorMoved()

    def newCursorCancel(self):
        if self.virtualCursor == None:
            return False

        self.virtualCursor = None
        self.onCursorMoved()
        return True

    #TODO: setting
    newCursorEnd = newCursorCancel


    def newCursorRight(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_RIGHT
                self.onCursorMoved()
                return
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = self.getFieldRightOf(self.virtualCursor)
        self.onCursorMoved()

    def newCursorLeft(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_LEFT
                self.onCursorMoved()
                return
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = self.getFieldLeftOf(self.virtualCursor)
        self.onCursorMoved()

    def newCursorBelow(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_DOWN
                self.onCursorMoved()
                return
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = self.getFieldBelowOf(self.virtualCursor)
        self.onCursorMoved()

    def newCursorAbove(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_UP
                self.onCursorMoved()
                return
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = self.getFieldAboveOf(self.virtualCursor)
        self.onCursorMoved()


    # new cursor / virtual cursor to border (End + Control + Arrow)

    def newCursorToRight(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_RIGHT
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = (self.COLS-1, self.virtualCursor[1])
        self.onCursorMoved()

    def newCursorToLeft(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_LEFT
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = (0, self.virtualCursor[1])
        self.onCursorMoved()

    def newCursorToBottom(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_DOWN
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = (self.virtualCursor[0], self.ROWS-1)
        self.onCursorMoved()

    def newCursorToTop(self):
        if self.virtualCursor == None:
            if len(self.cursors) == 0:
                self.virtualCursor = self.CURSOR_START_FOR_UP
            else:
                self.virtualCursor = self.cursors[-1]

        self.virtualCursor = (self.virtualCursor[0], 0)
        self.onCursorMoved()



    # ---------- input & output ----------

    SENTINEL_NOTES = '# ---------- NOTES ----------'

    RE_NUMBER = "-?[0-9]{1,2}"
    RE_STEP = "^#(?P<instantiation>(?P<class>[A-Z][A-Za-z]+)[(]((?P<dx>%s),[ ]?)?(?P<dy>%s)?[)])$" % (RE_NUMBER, RE_NUMBER)

    RO_STEP = re.compile(RE_STEP)

    JUMP_TYPES = tuple(cls.__name__ for cls in (NormalStep, HeliumJump, PipeJump, AmbiguousJumpStep, IllegalJumpStep))

    def readFile(self, ffn, log):
        _logger = Logger() # I am not using self._logger because that is used by the sanity check which I am calling
        _logger.init(log)
        log = _logger.log

        try:
            with open(ffn, 'r', encoding=self.ENCODING) as f:
                self.disableNotifications()
                readln = lambda: f.readline().rstrip('\n')
                
                # line 1: header
                header = readln()
                if header != self.HEADER:
                    log(logging.WARNING, _("invalid header {got!r}. should be {expected!r}.").format(got=header, expected=self.HEADER))

                # line 2: board
                for row in range(self.ROWS):
                    line = readln()
                    cols = len(line)
                    if cols != self.COLS:
                        log(logging.ERROR, _("invalid number of columns in row {row}: {got} (should be {expected}) in line \"{line}\"").format(row=row, got=cols, expected=self.COLS, line=line))
                    for col in range(min(self.COLS, cols)):
                        value = ord(line[col])
                        if imageOpener.getImage.isValid(value):
                            self.setField(x=col, y=row, value=value)
                        else:
                            log(logging.ERROR, _("invalid object at field (row={row}, col={col}): {objChar} ({objCode})").format(row=row, col=col, objCode=value, objChar=line[col]))

                # line 12: author
                self.setAuthor(readln())

                # lines 13--15: backgrounds
                self.bgMargin    = readln()
                self.bgUntouched = readln()
                self.bgTouched   = readln()
                self.sanityCheckBackgrounds(log)

                # line 16: solution
                numberStepsSolution = int(readln())
                self.solution.clear()
                for i in range(numberStepsSolution):
                    line = readln()
                    try:
                        x = int(line)
                    except ValueError:
                        log(logging.ERROR, _("illegal value for x coordinate in solution: {value}. I am breaking here.").format(value=line))
                        break
                    x -= self.OFFSET_X
                    
                    line = readln()
                    try:
                        y = int(line)
                    except ValueError:
                        log(logging.ERROR, _("illegal value for y coordinate in solution: {value}. I am breaking here.").format(value=line))
                        break
                    y -= self.OFFSET_Y
                    
                    self.solution.appendCoordinate((x, y))
                
                if len(self.solution) != numberStepsSolution:
                    log(logging.ERROR, _("inconsistent number of steps in solution. declared {declared}, actual {actual}.").format(declared=numberStepsSolution, actual=len(self.solution)))

                # [optionally] steps
                maxUsedLogLevel = _logger.getMaxUsedLogLevel()
                _logger.resetMaxUsedLogLevel()
                solutionSteps = list()
                while True:
                    line = readln()
                    if line == "" or line == self.SENTINEL_NOTES:
                        break
                    m = self.RO_STEP.match(line)
                    if m == None:
                        log(logging.ERROR, _("failed to parse step: {line!r}. I am stopping here.").format(line=line))
                        break
                    className = m.group('class')
                    if className not in self.JUMP_TYPES:
                        log(logging.ERROR, _("unknown step type {cls!r} in line: {line!r}. I am stopping here.").format(line=line, cls=className))
                        break
                    code = m.group('instantiation')
                    try:
                        step = eval(code)
                    except Exception as e:
                        log(logging.ERROR, _("error occured while trying to parse {code!r}: {error}. I am stopping here.").format(code=code, error=e))
                        break
                    solutionSteps.append(step)

                if _logger.getMaxUsedLogLevel() == LOGLEVEL_NONE and len(solutionSteps) > 0:
                    cors = self.solution._coordinates
                    self.solution._steps = solutionSteps
                    try:
                        self.solution.init(self)
                    except AssertionError:
                        log(logging.WARNING, _("read file has solution steps but no start field"))
                        self.solution._coordinates = cors
                    if cors != self.solution._coordinates:
                        log(logging.WARNING, _("solution coordinates and solution steps do not match. I am deciding for the steps."))
                    cors = None

                _logger.setMaxUsedLogLevel(maxUsedLogLevel)

                # notes
                if line == self.SENTINEL_NOTES:
                    #TODO: respect whitespace. requires that writing the file does not append a linebreak anymore. remember to update MainWindow.getCurrentNotes, too.
                    self.setNotes( f.read().rstrip() )
                else:
                    self.setNotes( None )
                    
                # check that eof has been reached
                if f.read(1) != "":
                    log(logging.WARNING, _("did not reach end of file."))

        except EnvironmentError as e:
            log(logging.ERROR, _("failed to read file: {error}").format(error=e))

        except Exception as e:
            log(logging.ERROR, _("unforeseen exception while trying to read file: {error}. This ends my attempt to read this file.").format(error=e))

        if self.notificationsAreDisabled():
            self.history.clear()
            self.ffn = ffn
            self._hasChanged = _logger.getMaxUsedLogLevel() != LOGLEVEL_NONE
            self.enableNotifications()
            self.onChange(self.CHANGE_ALL, updateChangedFlag=False)

        return _logger.end()


    def writeCopy(self, ffn):
        path = os.path.split(ffn)[0]
        if not os.path.isdir(path):
            os.makedirs(path)
        with open(ffn, 'w', encoding=self.ENCODING) as f:
            if system.isWindows():
                writeln = lambda ln: f.write(u'%s\n' % ln)
            else:
                writeln = lambda ln: f.write(u'%s\r\n' % ln)
            
            # line 1: header
            writeln(self.HEADER)

            # line 2: board
            for ln in self.boardToString().split('\n'):
                writeln(ln)

            # line 12: author
            writeln(self.getAuthor())

            # lines 13--15: backgrounds
            writeln(self.bgMargin)
            writeln(self.bgUntouched)
            writeln(self.bgTouched)

            # line 16: solution
            writeln(len(self.solution))
            for x,y in self.solution.iterCoordinates():
                writeln(x+self.OFFSET_X)
                writeln(y+self.OFFSET_Y)

            if self.solution.isInitialized():
                for step in self.solution.iterSteps():
                    writeln("#%r" % (step,))

            # afterwards: notes
            if self.notes != None:
                writeln(self.SENTINEL_NOTES)
                for ln in self.notes.split("\n"):
                    writeln(ln)

    def writeFile(self, ffn):
            self.writeCopy(ffn)
            self.ffn = ffn
            self._hasChanged = False
            # no, I do not want to reset _hasChangedSinceSolutionEdit here
            self.onChange(self.CHANGE_HAS_CHANGED)

    def boardToString(self):
        out = u""
        for row in range(self.ROWS):
            for col in range(self.COLS):
                out += objects.codeToChr(self.getField(x=col, y=row))
            out += "\n"
        return out.rstrip('\n')

    __str__ = boardToString


    # ---------- sanity checks ----------
    
    def sanityCheckSolution(self, log):
        return self.solution.sanityCheck(log)

    def sanityCheckSolutionUpdated(self, log):
        self._logger.init(log)
        log = self._logger.log

        if len(self.solution) == 0:
            log(logging.WARNING, _("no solution specified"))

        else:
            if self._hasChangedSinceSolutionEdit:
                log(logging.WARNING, _("level has been changed\nsince editing the solution"))

            elif self.solution.isDirty:
                log(logging.WARNING, _("solution has issues"))
        
        return self._logger.end()

    def sanityCheckBackgrounds(self, log):
        self._logger.init(log)
        log = self._logger.log
        
        for attr in ('margin', 'untouched', 'touched'):
            attr = "bg" + attr.capitalize()
            v = getattr(self, attr)
            if not imageOpener.getBackground.isValid(v):
                log(logging.ERROR, _("invalid value for {attr}: '{value}'").format(attr=attr, value=v))

        if self.bgTouched == self.bgUntouched:
            log(logging.WARNING, _("backgrounds for touched and\nuntouched fields are the same"))
                
##        if not "1" in self.bgMargin[6:]:
##            log(logging.INFO, "bgMargin is not from\nmargin catalog: "+self.bgMargin)
##        if not "2" in self.bgUntouched[6:]:
##            log(logging.INFO, "bgUntouched is not from\nuntouched catalog: "+self.bgUntouched)
##        if not "3" in self.bgTouched[6:]:
##            log(logging.INFO, "bgTouched is not from\ntouched catalog: "+self.bgTouched)
        
        return self._logger.end()


    def sanityCheckBoard(self, log):
        self._logger.init(log)
        log = self._logger.log
        error = lambda msg: log(logging.ERROR, msg)
        
        # start
        n = self.count(self.FLD_START)
        if n == 0:
            error(_("no start field specified"))
        elif n >= 2:
            error(_("too many start fields specified"))

        # end
        n = self.count(self.FLD_END)
        # (no door is fine)
        if n >= 2:
            error(_("too many end fields specified"))

        # task
        if not self.containsObjectsToEatOrMove():
            error(_("nothing to eat or move"))

        return self._logger.end()

    def sanityCheckAuthor(self, log):
        self._logger.init(log)
        log = self._logger.log

        if self.getAuthor() == "":
            log(logging.WARNING, _("no author specified"))

        return self._logger.end()


    # ---------- support ----------

    def isValidField(self, x, y):
        if x == None or y == None:
            return False
        return 0 <= x < self.COLS and 0 <= y < self.ROWS

    def flipCoordinate(self, cor):
        return (cor[0], self.ROWS-1 - cor[1])

    def containsObjectsToEatOrMove(self):
        if self.getNumberObjectsToEat() > 0:
            return True
        if self.getNumberObjectsToMove() > 0:
            return True
        return False

    def getNumberObjectsToEat(self):
        n = 0
        for t in self.board:
            for o in t:
                if o in objects.CATEGORY_TO_EAT:
                    n += 1
        return n

    def getNumberObjectsToMove(self):
        #TODO: check counter part
        n = 0
        for t in self.board:
            for o in t:
                if o in objects.CATEGORY_TO_MOVE:
                    n += 1
        return n


if __name__=='__main__':
    logging.basicConfig(
        level = 0,
        format = "[%(levelname)-8s] %(message)s",
    )
    
    m = Model()
    tasks = list()
    def appendTasks(path):
        fns = os.listdir(path)
        fns.sort()
        for fn in fns:
            if os.path.splitext(fn)[1] != '.afg':
                continue
            ffn = os.path.join(path, fn)
            tasks.append(ffn)
    appendTasks("../_level-vorlagen")
    appendTasks("../_level-eigene/finished")
    appendTasks("../_level-tests")
    for ffn in tasks:
        print(ffn)
        m.readFile(ffn, logging.log)
        m.sanityCheckBoard(logging.log)
        #m.sanityCheckBackgrounds(logging.log) # is already performed in open
        m.sanityCheckSolutionUpdated(logging.log)
        m.solution.init(m)
        m.sanityCheckSolution(logging.log)

    import tempfile
    ffn_in = "../_level-vorlagen/irka-%03d.afg" % 15
    m = Model()
    print("read "+ffn_in)
    m.readFile(ffn_in, logging.log)
    m.solution.init(m)
    m.sanityCheckSolution(logging.log)
    #ffn_out = os.path.expanduser("~/desktop/test.afg")
    f, ffn_out = tempfile.mkstemp()
    m.setNotes("foo")
    print("write "+ffn_out)
    m.writeFile(ffn_out)

    m2 = Model()
    print("read "+ffn_out)
    m2.readFile(ffn_out, logging.log)
    print("m2.getNotes(): %r" % m2.getNotes())
    assert m.getNotes() == m2.getNotes()
    
    os.remove(ffn_out)
