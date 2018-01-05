#!/usr/bin/env python

# standard
import os.path

# other
import model_object_catalog as objects
import system
from locales import _

import tkinter_extensions as tkx
tk = tkx.tk


ENCODING = 'windows-1252'
if system.isPython3():
    def objCodeToChr(num):
        return bytes((num,)).decode(ENCODING)
else:
    def objCodeToChr(num):
        return chr(num).decode(ENCODING)

toAbsPath = objects.toAbsPath
PATH_BACKGROUNDS = toAbsPath('backgrounds/gif')
PATH_IMAGES      = objects.PATH

EXT_BACKGROUND = '.fld'

FLD_SIZE = 32


class ImageOpener(object):

    def __init__(self, path, pattern, splitOldExtension=False, isEmptyImage=None, getShortName=None, getLongName=None, shortNameToValue=None):
        self.path = path
        self.pattern = pattern
        self.splitOldExtension = splitOldExtension
        self.isEmptyImage = isEmptyImage
        self._getShortName = getShortName
        self._getLongName = getLongName
        self._shortNameToValue = shortNameToValue
        self.images = dict()

    def getImage(self, name):
        if self.isEmptyImage!=None and self.isEmptyImage(name):
            return None
        
        img = self.images.get(name, None)
        if img == None:
            ffn = os.path.join(self.path, self.toFilename(name))
            img = tk.PhotoImage(file=ffn)
            self.images[name] = img

        return img
            
    __call__ = getImage

    def toFilename(self, name):
        if self.splitOldExtension:
            name = os.path.splitext(name)[0]
        return self.pattern.format(name)

    def isValid(self, name):
        if self.isEmptyImage!=None and self.isEmptyImage(name):
            return True
        
        ffn = os.path.join(self.path, self.toFilename(name))
        return os.path.isfile(ffn)

    def getShortName(self, name):
        if self._getShortName == None:
            return str(name)
        else:
            return self._getShortName(self, name)

    def getLongName(self, name):
        if self._getLongName == None:
            return str(name)
        else:
            return self._getLongName(self, name)

    def shortNameToValue(self, name):
        if self._shortNameToValue == None:
            return name
        else:
            return self._shortNameToValue(self, name)

def setObjectCodeCharacter():
    getImage._getShortName = lambda self, value: objCodeToChr(value)

def setObjectCodeNumber():
    getImage._getShortName = None


def getObjectDescription(self, obj):
    out = "%03d (%s)"%(obj, objCodeToChr(obj))

    comments = list()
    
    if obj in objects.GRAVITY_OBEYING:
        comments.append(_("obeys gravity"))
    elif obj in objects.GRAVITY_RESISTANT:
        comments.append(_("gravity resistant"))

    if obj in objects.ATTR_MOVABLE:
        comments.append(_("movable"))
    elif obj in objects.ATTR_EATABLE:
        comments.append(_("eatable"))
    elif obj in objects.ATTR_FIXED:
        comments.append(_("*not* movable"))
    elif obj in objects.ATTR_KILLING:
        comments.append(_("kills you when stepping on it"))

    tmp = objects.getComment(obj)
    if tmp != "":
        comments.append(tmp)

    if len(comments) > 0:
        out += ": " + ", ".join(comments)
    
    return out

getImage = ImageOpener(
    path = PATH_IMAGES,
    pattern = "irka{0}.gif",
    getLongName = getObjectDescription,
)
getBackground = ImageOpener(
    path = PATH_BACKGROUNDS,
    pattern = "{0}.gif",
    splitOldExtension = True,
    getShortName=lambda self,name: os.path.splitext(name[6:] if name[:6]=="irka3_" else name)[0],
    shortNameToValue = lambda self,name: "irka3_{name}{ext}".format(name=name, ext=EXT_BACKGROUND),
)



class BitmapOpener(object):

    PATH = toAbsPath('icons/backgrounds/xbm')

    FN_GRAVITY_OBEYING   = 'ver-1-4.xbm'
    FN_GRAVITY_RESISTANT = 'hor-1-4.xbm'
    FN_GRAVITY_UNKNOWN   = 'gray25.xbm'

    COLOR_MOVABLE = 'lime green'
    COLOR_EATABLE = 'yellow green'
    COLOR_FIXED   = 'DarkOrange3' # 'dark goldenrod'
    COLOR_DEADLY  = 'red'
    COLOR_UNKNOWN = 'blue'

    def __init__(self):
        self.path = self.PATH
        self.images = dict()

    def getImage(self, obj):
        if obj in objects.GRAVITY_OBEYING:
            fn = self.FN_GRAVITY_OBEYING
        elif obj in objects.GRAVITY_RESISTANT:
            fn = self.FN_GRAVITY_RESISTANT
        else:
            fn = self.FN_GRAVITY_UNKNOWN

        if obj in objects.ATTR_MOVABLE:
            color = self.COLOR_MOVABLE
        elif obj in objects.ATTR_EATABLE:
            color = self.COLOR_EATABLE
        elif obj in objects.ATTR_FIXED:
            color = self.COLOR_FIXED
        elif obj in objects.ATTR_KILLING:
            color = self.COLOR_DEADLY
        else:
            if fn == self.FN_GRAVITY_UNKNOWN:
                return None
            color = self.COLOR_UNKNOWN

        key = (fn, obj)
        img = self.images.get(key, None)
        if img != None:
            return img

        ffn = os.path.join(self.path, fn)
        img = tk.BitmapImage(file=ffn, foreground=color)
        self.images[key] = img
        
        return img
            
    __call__ = getImage


##getImage.getBackground = ImageOpener(
##    path = PATH_INFO_IMAGES,
##    pattern = "gravity-{0[gravity]}_movable{0[movable]}.gif",
##)

getImage.getBackground = BitmapOpener()

setObjectCodeCharacter()


if __name__=='__main__':
    import model
    c = tk.Canvas()
    x, y = 0, 0
    c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getBackground('irka3_2a.fld'))
    c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getImage(model.Model.FLD_START))
    x += 1
    c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getBackground('irka3_1a.fld'))
    c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getImage(model.Model.FLD_EMPTY))

    y = y + 1
    x = 0
    for obj in (65, 83, 84, 98, 117):
        c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getImage.getBackground(obj))
        c.create_image(x*FLD_SIZE, y*FLD_SIZE, anchor='nw', image=getImage(obj))
        x += 1
    
    c.pack()
    c.mainloop()
    pass
