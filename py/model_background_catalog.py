#!/usr/bin/env python

import os.path

import logging
import locales
_ = locales._
import re

from gui_image_opener import toAbsPath, getBackground

PATH_BACKGROUNDS = toAbsPath('backgrounds/gif')

TITLE_BORDER  = _("BG Border")
TITLE_TOUCHED = _("BG Touched")
TITLE_UNTOUCHED = _("BG Untouched")

CATEGORY_BORDER  = list()
CATEGORY_TOUCHED = list()
CATEGORY_UNTOUCHED = list()

__backgrounds = None
def getBackgrounds():
    global __backgrounds
    if __backgrounds == None:
        __backgrounds = tuple(__getBackgrounds())
    return __backgrounds

def __getBackgrounds():
    l = os.listdir(PATH_BACKGROUNDS)
    for fn in l:
        if fn[0] == '.':
            logging.debug(_("ignoring hidden file {fn} in {path}").format(fn=fn, path=PATH_IMAGES))
            continue
        fn = os.path.splitext(fn)[0] + ".fld"
        yield fn

CATEGORY_ALL = list(getBackgrounds())
CATEGORY_ALL.sort()

for bg in CATEGORY_ALL:
    short = getBackground.getShortName(bg)
    if   "1" in short:
        CATEGORY_BORDER.append(bg)
    elif "2" in short:
        CATEGORY_UNTOUCHED.append(bg)
    elif "3" in short:
        CATEGORY_TOUCHED.append(bg)
    else:
        logging.error("background with invalid name can not be categorized: %r" % (bg,))

categories = (
   #(_("Background"), CATEGORY_ALL),
    (TITLE_BORDER, CATEGORY_BORDER),
    (TITLE_UNTOUCHED, CATEGORY_UNTOUCHED),
    (TITLE_TOUCHED, CATEGORY_TOUCHED),
)


# next/previous background
reo_fn     = re.compile('irka3_(?P<fld>1|2|3)(?P<scheme>[a-zA-Z]).fld')
pattern_fn = 'irka3_{fld}{scheme}.fld'

def __next_bg(bg, inc):
    m = reo_fn.match(bg)
    if m == None:
        print("failed to parse %s" % bg)
        return bg
    fld = m.group('fld')
    scheme = m.group('scheme')
    scheme = ord(scheme)
    scheme += inc
    scheme = chr(scheme)
    value = pattern_fn.format(fld=fld, scheme=scheme)
    if value not in getBackgrounds():
        scheme = 'a'
        value = pattern_fn.format(fld=fld, scheme=scheme)
    return value

def nextBg(bg):
    return __next_bg(bg, +1)

def prevBg(bg):
    return __next_bg(bg, -1)

if __name__=='__main__':
    print(CATEGORY_ALL)
