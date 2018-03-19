#!/usr/bin/env python

# standard
import os.path
import re
import logging

# other
import system
import locales
_ = locales._


def toAbsPath(relPath):
    return os.path.join(os.path.split(os.path.split(__file__)[0])[0], relPath)

PATH = toAbsPath('images/gif')

ENCODING = 'windows-1252'
if system.isPython3():
    def codeToChr(num):
        return bytes((num,)).decode(ENCODING)
else:
    def codeToChr(num):
        return chr(num).decode(ENCODING)


# ========== OBJECTS ==========

OBJ_NONE  = ord('!')
OBJ_START = ord('0')
OBJ_END   = ord('[')

OBJ_HELIUM= ord('b')
OBJ_PIPE  = ord('X')
OBJ_DRUM  = ord('W')
OBJ_WAND  = ord('a')
OBJ_SUN   = ord('c')

OBJ_ARROW_LEFT  = ord('w')
OBJ_ARROW_RIGHT = ord('x')
OBJ_ARROW_UP    = ord('y')
OBJ_ARROW_DOWN  = ord('z')

OBJ_BURNING_CAN = ord('u')
OBJ_FIRE = ord('#')
OBJ_RAIN = ord('$')


# ========== CATEGORIES ==========

TITLE_TO_EAT  = _("To Eat")
TITLE_TO_MOVE = _("To Move")
TITLE_OBSTACLES         = _("Obstacles")
TITLE_OBSTACLES_GRAVITY = _("Obstacles 1")
TITLE_OBSTACLES_FIX     = _("Obstacles 2")
TITLE_MAGIC = _("Other")
TITLE_UNCATEGORIZED = _("Uncategorized")

CATEGORY_TO_EAT    = (65, 66,67,68,69,70,71,72,73,74, 75, 76, 77,78, 123,125)
CATEGORY_TO_MOVE   = (44,55, 45,49, 46,50, 47,89, 51,52, 53,54, 79,80, 103,104, 109,110, 112,113)
CATEGORY_OBSTACLES_GRAVITY = (
    # balls
    37,38,39,40,41,42,
    # others
    43, 81,82, 83,84, 100,101,102,
    # fire
    # exception: 118 [water] does *not* fall
    115,116,117,118,
    # invert
    98,
)
CATEGORY_OBSTACLES_FIX = (
    # normal
    58,59,60, 61,62,
    # combined objects (fix)
    56, 57, 63, 90, 105, 196, 228,
    # combined objects (moveable)
    111, 114,
    # arrows
    119,120,121,122,
    # deadly
    35,36,
)
CATEGORY_OBSTACLES = CATEGORY_OBSTACLES_GRAVITY + CATEGORY_OBSTACLES_FIX
CATEGORY_MAGIC     = (
    # start, end, empty
    48 ,91, 33,
    # explosives
    85,86, 106, 107, 108,
    # magic
    87,88, 97, 99,
)


def getCategory(obj):
    if   obj in CATEGORY_TO_EAT:
        return TITLE_TO_EAT
    elif obj in CATEGORY_TO_MOVE:
        return TITLE_TO_EAT
    elif obj in CATEGORY_MAGIC:
        return TITLE_TO_EAT
    elif obj in CATEGORY_OBSTACLES:
        return TITLE_TO_EAT
    else:
        return TITLE_UNCATEGORIZED
    

def getObjects():
    reo = re.compile(r"^irka(?P<id>\d+)[.][a-z]+$")
    l = os.listdir(PATH)
    for fn in l:
        if fn[0] == '.':
            logging.debug(_("ignoring hidden file {fn} in {path}").format(fn=fn, path=PATH_IMAGES))
            continue
        m = reo.match(fn)
        if not m:
            logging.warning(_("invalid file {fn} in {path}").format(fn=fn, path=PATH_IMAGES))
            continue
        yield int(m.group('id'))

CATEGORY_ALL = list(getObjects())
CATEGORY_ALL.append(OBJ_NONE)
CATEGORY_ALL.remove(93) # open door
CATEGORY_ALL.sort()
CATEGORY_UNCATEGORIZED = list(set(CATEGORY_ALL) - (set(CATEGORY_TO_EAT)|set(CATEGORY_TO_MOVE)|set(CATEGORY_MAGIC)|set(CATEGORY_OBSTACLES)))
CATEGORY_UNCATEGORIZED.sort()

categories = (
    (TITLE_TO_EAT, CATEGORY_TO_EAT),
    (TITLE_TO_MOVE, CATEGORY_TO_MOVE),
    (TITLE_OBSTACLES_GRAVITY, CATEGORY_OBSTACLES_GRAVITY),
    (TITLE_OBSTACLES_FIX, CATEGORY_OBSTACLES_FIX),
    (TITLE_MAGIC, CATEGORY_MAGIC),
)
if len(CATEGORY_UNCATEGORIZED) > 0:
    categories += ((TITLE_UNCATEGORIZED, CATEGORY_UNCATEGORIZED),)

def checkNoDoubles():
    n = 0
    s = set()
    for title, items in categories:
        n += len(items)
        s |= set(items)
    return n == len(s)
assert checkNoDoubles()


# ========== GRAVITY ==========

GRAVITY_OBEYING = (
    # everything to eat
    65, 66,67,68,69,70,71,72,73,74, 75, 76, 77,78, 123,125,
    # some fillings (to be moved)
    44, 45, 46, 47, 79, 109,
    # one container (to be moved on) [money bag]
    80,
    # balls
    37,38,39,40,41,42,
    # other obstacles
    43, 81,82, 83,84, 100,101,102,
    # fire
    115,116,117,
    # explosives
    85,86, 106, 107, 108,
    # magic
    OBJ_DRUM,OBJ_PIPE, OBJ_WAND, OBJ_SUN,
)

GRAVITY_RESISTANT = (
    # some fillings (to be moved)
    51, 53, 103, 112,
    # almost all containers (to be moved on)
    55, 49, 50, 89, 52, 54, 104, 110, 113,
    # normal not-falling obstacles
    58,59,60, 61,62,
    # water
    118,
    # combined objects (fix)
    56, 57, 63, 90, 105, 196, 228,
    # combined objects (moveable)
    111, 114,
    # arrows
    119,120,121,122,
    # deadly
    35,36,
    # doors
    91, 93
)

assert set(GRAVITY_OBEYING) & set(GRAVITY_RESISTANT) == set()


# ========== MOVABILITY ==========

ATTR_MOVABLE = (
    # all fillings (to be moved)
    44, 45, 46, 47, 51, 53, 79, 103, 109, 112,
    # some containers (to be moved on)
    49, 50, 52, 80, 110, 113,
    # some combined objects (after moved on)
    111, 114,
    # balls
    37,38,39,40,41,42,
    # other obstacles
    43, 81,82, 83, 100,101,102,
    # match, can, water
    115,116, 118,
    # explosives
    86, 106, 107, 108,
)
ATTR_EATABLE = CATEGORY_TO_EAT + (OBJ_DRUM, OBJ_PIPE, OBJ_WAND, OBJ_SUN, 93)
ATTR_FIXED = (
    # obstacles
    OBJ_HELIUM, 58, 59, 60, 61, 62, 84,
    # some containers (to be moved on)
    55, 89, 54, 104,
    # most combined objects (after moved on)
    56, 57, 63, 90, 105, 196, 228,
    # arrows
    119,120,121,122,
    # trigger for dynamite
    85,
    # closed door
    91,
)
ATTR_KILLING = (OBJ_FIRE, OBJ_RAIN, OBJ_BURNING_CAN)

# no duplicates
##assert len(set(ATTR_MOVABLE)) == len(ATTR_MOVABLE)
##assert len(set(ATTR_EATABLE)) == len(ATTR_EATABLE)
##assert len(set(ATTR_FIXED)) == len(ATTR_FIXED)
##assert len(set(ATTR_KILLING)) == len(ATTR_KILLING)
assert len( set(ATTR_MOVABLE) | set(ATTR_EATABLE) | set(ATTR_FIXED) | set(ATTR_KILLING) ) \
       == len(ATTR_MOVABLE) + len(ATTR_EATABLE) + len(ATTR_FIXED) + len(ATTR_KILLING)


# ========== COMMENTS ==========

def getObjectDescription(self, obj):
    out = codeAndChr(obj)

    comments = getPropertiesList(obj)

    if len(comments) > 0:
        out += ": " + ", ".join(comments)
    
    return out

def codeAndChr(obj):
    return "%03d (%s)" % (obj, codeToChr(obj))

def getPropertiesList(obj):
    properties = list()
    
    if obj in GRAVITY_OBEYING:
        properties.append(_("obeys gravity"))
    elif obj in GRAVITY_RESISTANT:
        properties.append(_("gravity resistant"))

    if obj in ATTR_MOVABLE:
        properties.append(_("movable"))
    elif obj in ATTR_EATABLE:
        properties.append(_("eatable"))
    elif obj in ATTR_FIXED:
        properties.append(_("*not* movable"))
    elif obj in ATTR_KILLING:
        properties.append(_("kills you when stepping on it"))
    
    tmp = getComment(obj)
    if tmp != "":
        properties.append(tmp)
    
    return properties

def getComment(obj):
    # special fields
    if obj == OBJ_NONE:
        return _("empty field")
    elif obj == OBJ_START:
        return _("start field")
    elif obj == OBJ_END:
        return _("end field (optional)")

    elif obj == OBJ_PIPE:
        return _("flips the board vertically")
    elif obj == OBJ_HELIUM:
        return _("floats upward")
    # keys
    elif obj == 123:
        return _("last key must be eaten last (but before last bell)")
    # bell
    elif obj == 125:
        return _("last bell must be eaten last (even after last key)")
    # wand
    elif obj == 97:
        return _("disables gravity for two steps")
    # drum
    elif obj == 87:
        return _("converts all 061 (=) into 040 (()")
    # sun
    elif obj == 99:
        return _("removes all movable balls")
    
    # red-yellow ball
    elif obj == 61:
        return _("is converted by 087 (W)")
    elif obj == OBJ_FIRE or obj == OBJ_BURNING_CAN:
        return _("kills you when stepping over it")
    elif obj == OBJ_RAIN:
        return _("kills you when stepping under it")

    return ""


# ========== TEST ==========

if __name__=='__main__':
    #for i in getObjects():
    #    print(i)
    print(TITLE_UNCATEGORIZED)
    print(CATEGORY_UNCATEGORIZED)

    print()
    print("unkown reaction to gravity:")
    print(set(CATEGORY_ALL) - set(GRAVITY_OBEYING) - set(GRAVITY_RESISTANT))

    print()
    print("unkown attribute (movable, eatable, fixed, killing):")
    print(set(CATEGORY_ALL) - set(ATTR_MOVABLE) - set(ATTR_EATABLE) - set(ATTR_FIXED) - set(ATTR_KILLING))
