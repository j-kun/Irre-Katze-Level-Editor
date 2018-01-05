#!/usr/bin/env python

import os.path

import logging
import locales
_ = locales._

from gui_image_opener import toAbsPath, getBackground

PATH_BACKGROUNDS = toAbsPath('backgrounds/gif')

TITLE_BORDER  = _("BG Border")
TITLE_TOUCHED = _("BG Touched")
TITLE_UNTOUCHED = _("BG Untouched")

CATEGORY_BORDER  = list()
CATEGORY_TOUCHED = list()
CATEGORY_UNTOUCHED = list()

def getBackgrounds():
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

if __name__=='__main__':
    print(CATEGORY_ALL)
