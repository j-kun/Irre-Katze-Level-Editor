#!/usr/bin/env python

import gettext
import locale # ist umstritten. siehe http://stackoverflow.com/questions/3425294/how-to-detect-the-os-default-language-in-python
locale.setlocale(locale.LC_ALL, '') #TODO: was genau macht das? braucht man das? schadet das?

# locale of program != system locale
#   as python locale has not been set, locale.getlocale() should return None
#   but locale.getdefaultlocale() SHOULD always return system locale
def locale_to_language (locale):
    if locale == None:
        return None
    i = locale.index('_')
    return locale[:i]
languages = [ locale_to_language(locale.getdefaultlocale()[0]) ]
if languages[0]==None:
    del languages[0]
languages.append("en")

# Set up message catalog access
domain = 'messages' #'youtube-dl-gui'
locales_directory = 'locales'
t = gettext.translation(domain, locales_directory, languages=languages, fallback=True)
try:
    # Python 2
    _ = t.ugettext
except:
    # Python 3
    _ = t.gettext

def format_date(date):
    #frmt = "%x"
    frmt = "%d.%m.%Y"
    return date.strftime(frmt)

def format_int(i):
    frmt = "%i"
    #print "locale.format(%r, %r, grouping=True)" % (frmt, i)
    return locale.format(frmt, i, grouping=True)

def format_float(f):
    frmt = "%0.2f"
    #print "locale.format(%r, %r, grouping=True)" % (frmt, f)
    return locale.format(frmt, f, grouping=True)

if __name__=='__main__':
    print(_('download'))
