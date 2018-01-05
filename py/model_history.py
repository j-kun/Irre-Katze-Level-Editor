#!/usr/bin/env python

UPDATE_LAST = 'update-last'


class History(object):

    # ---------- initialize ----------
    
    def __init__(self, model, attributesToBackup, maxSize, onUndoOrRedoListener=None):
        self.model = model
        self.setAttributesToBackup( attributesToBackup )
        self.maxSize = maxSize
        self.onLoadListener = onUndoOrRedoListener
        self.clear()

    def setAttributesToBackup(self, attributesToBackup):
        '''attributesToBackup: an iterable of attribute specifications.
        each specification is a list/tuple of up to three elements:
            0: the name of the attribute
            1: a function to copy the value of the attribute
            2: a flag whether corresponding value of the last history entry shall be updated.
               this can be useful to save a cursor.
            '''
        self.attributesToBackup = list()
        for attrSpec in attributesToBackup:
            if not isinstance(attrSpec, (tuple, list)) or len(attrSpec) == 1:
                self.attributesToBackup.append((attrSpec, None, None))
            elif len(attrSpec) == 2:
                self.attributesToBackup.append((attrSpec[0], attrSpec[1], None))
            elif len(attrSpec) == 3:
                self.attributesToBackup.append(attrSpec)
            else:
                assert False

    def clear(self):
        self.history = list()
        self.historyIndex = -1


    # ---------- getters ----------

    def __len__(self):
        return len(self.history)


    # ---------- save ----------
    
    def makeBackup(self):
        self.historyIndex += 1
        while self.historyIndex < len(self.history):
            del self.history[-1]
        
        if len(self.history) > 0:
            prior = self.history[-1]
        else:
            prior = None
        d = dict()
        for attr, copy, updateLast in self.attributesToBackup:
            val = getattr(self.model, attr)
            if copy != None:
                val = copy(val)
            d[attr] = val
            if updateLast == UPDATE_LAST and prior != None:
                prior[attr] = val
                
        self.history.append(d)

        while len(self.history) > self.maxSize:
            del self.history[0]
            self.historyIndex -= 1


    # ---------- load ----------
    
    def undo(self):
        if self.historyIndex <= 0:
            return False

        self.historyIndex -= 1
        self._load()
        return True

    def redo(self):
        if self.historyIndex + 1 >= len(self.history):
            return False

        self.historyIndex += 1
        self._load()
        return True

    def _load(self):
        d = self.history[self.historyIndex]
        for attr, copy, updateLast in self.attributesToBackup:
            val = d[attr]
            if copy != None:
                val = copy(val)
            setattr(self.model, attr, val)
        if self.onLoadListener != None:
            self.onLoadListener()



if __name__=='__main__':

    class Model(object):

        ATTRIBUTES_TO_BACKUP = (
            # attribute name, copy function
            ('x', None),
        )

        def __init__(self):
            self.x = 0
            self.history = History(self, self.ATTRIBUTES_TO_BACKUP, 30)
            self.history.makeBackup()

        def increment(self):
            self.x += 1
            self.history.makeBackup()

    N = 3

    m = Model()
    for i in range(N):
        m.increment()
    assert m.x == N
    
    assert m.history.undo()
    assert m.x == N - 1
    assert m.history.redo()
    assert m.x == N
    assert not m.history.redo()

    for i in range(N):
        assert m.history.undo()
        assert m.x == N - 1 - i
    assert not m.history.undo()
    assert m.x == 0
    assert len(m.history) == N + 1

    print("tests successful")
