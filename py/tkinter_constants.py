#!/usr/bin/env python
# -*- coding: utf8 -*-

import system

if system.isPython2():
    import Tkinter as tk
else:
    import tkinter as tk

TEXT = 'text'
TEXTVARIABLE = 'textvariable'
STATE = 'state'
COMMAND = 'command'
STATE_NORMAL = tk.NORMAL
STATE_ACTIVE = tk.ACTIVE
STATE_DISABLED = tk.DISABLED
STATE_READONLY = 'readonly'
# seems to work for Entry but not for Text
# as work around use something like
# text.bind("<Key>", lambda event: "break")

TAGS = 'tags'

COLOR_FOREGROUND = 'foreground'
COLOR_BACKGROUND = 'background'
COLOR_OUTLINE    = 'outline'
COLOR_FILL       = 'fill'

N = tk.N
S = tk.S
W = tk.W
E = tk.E
WNSE = W+N+S+E

#.keycode:
#   http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/key-names.html
#.state (modifier masks):
#   http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/event-handlers.html
#   does not seem reliable: https://stackoverflow.com/a/19863837
MODIFIER_MASK_SHIFT_ONLY= 0x0001
MODIFIER_MASK_CAPSLOCK  = 0x0002
MODIFIER_MASK_CTRL      = 0x0004
if system.isWindows():
    MODIFIER_MASK_ALT   = 0x20000
else:
    MODIFIER_MASK_ALT   = 0x0008
MODIFIER_MASK_NUMLOCK   = 0x0010
MODIFIER_MASK_ALT_GR    = 0x0080
MODIFIER_MASK_MOUSEBTN1 = 0x0100
MODIFIER_MASK_MOUSEBTN2 = 0x0200
MODIFIER_MASK_MOUSEBTN3 = 0x0400

MODIFIER_MASK_SHIFT = MODIFIER_MASK_SHIFT_ONLY | MODIFIER_MASK_CAPSLOCK


KEYCODE_ARROW_UP    = 111
KEYCODE_ARROW_DOWN  = 116
KEYCODE_ARROW_LEFT  = 113
KEYCODE_ARROW_RIGHT = 114
KEYCODES_ARROWS = (KEYCODE_ARROW_UP, KEYCODE_ARROW_DOWN, KEYCODE_ARROW_LEFT, KEYCODE_ARROW_RIGHT)
KEYCODE_HOME = 110
KEYCODE_END  = 115
KEYCODES_MOVE_CURSOR = KEYCODES_ARROWS + (KEYCODE_HOME, KEYCODE_END)
KEYCODE_TAB = 23


KEY_SYMBOLS = dict(
    #https://www.tcl.tk/man/tcl8.6/TkCmd/keysyms.htm
    # special key
    plus         =  '+',
    numbersign   =  '#',
    minus        =  '-',
    period       =  '.',
    comma        =  ',',
    space        = u'␣',
    less         =  '<',
    asciicircum  =  '^',
    # Shift + special key
    asterisk     =  '*',
    quoteright   =  "'",
    underscore   =  '_',
    colon        =  ':',
    semicolon    =  ';',
    greater      =  '>',
    degree       = u'°',
    # Shift + number key
    exclam       =  '!',
    quotedbl     =  '"',
    dollar       =  '$',
    percent      =  '%',
    ampersand    =  '&',
    slash        =  '/',
    parenleft    =  '(',
    parenright   =  ')',
    equal        =  '=',
    question     =  '?',
    # AltGr
    at           =  '@',
    braceleft    =  '{',
    bracketleft  =  '[',
    bracketright =  ']',
    braceright   =  '}',
    backslash    =  '\\',
    asciitilde   =  '~',
    bar          =  '|',
)


KEY_CURSOR = 'cursor'
CURSOR_ARROW = 'arrow'
CURSOR_WATCH = 'watch'

# Protocols:
WM_DELETE_WINDOW = 'WM_DELETE_WINDOW'
WM_TAKE_FOCUS    = 'WM_TAKE_FOCUS'
WM_SAVE_YOURSELF = 'WM_SAVE_YOURSELF'

# Menu:
KEY_TEAROFF = 'tearoff'
KEY_MENU = 'menu'

# Style
RELIEF_FLAT   = tk.FLAT
RELIEF_RAISED = tk.RAISED
RELIEF_SUNKEN = tk.SUNKEN
RELIEF_GROOVE = tk.GROOVE
RELIEF_RIDGE  = tk.RIDGE

DEFAULT = 'default'
DEFAULT_ACTIVE   = tk.ACTIVE    # In active state, the button is drawn with the platform specific appearance for a default button.
DEFAULT_NORMAL   = tk.NORMAL    # In normal state, the button is drawn with the platform specific appearance for a non-default button, leaving enough space to draw the default button appearance. The normal and active states will result in buttons of the same size.
DEFAULT_DISABLED = tk.DISABLED  # In disabled state, the button is drawn with the non-default button appearance without leaving space for the default appearance. The disabled state may result in a smaller button than the active state.
                                # https://www.tcl.tk/man/tcl8.4/TkCmd/button.htm#M7

# Compound
COMPOUND_LEFT = tk.LEFT
COMPOUND_RIGHT = tk.RIGHT
COMPOUND_TOP = tk.TOP
COMPOUND_BOTTOM = tk.BOTTOM
COMPOUND_NONE = tk.NONE

# stipple:
STIPPLE = 'stipple'
STIPPLE_GRAY_75 = 'gray75'
STIPPLE_GRAY_50 = 'gray50'
STIPPLE_GRAY_25 = 'gray25'
STIPPLE_GRAY_12 = 'gray12'
#http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/bitmaps.html

# Types of Canvas items:
TYPE_ARC       = 'arc'
TYPE_BITMAP    = 'bitmap'
TYPE_IMAGE     = 'image'
TYPE_LINE      = 'line'
TYPE_OVAL      = 'oval'
TYPE_POLYGON   = 'polygon'
TYPE_RECTANGLE = 'rectangle'
TYPE_TEXT      = 'text'
TYPE_WINDOW    = 'window'
#http://effbot.org/tkinterbook/canvas.htm#Tkinter.Canvas.type-method

# Variables:
TRACE_WRITE = 'w'
TRACE_READ  = 'r'
TRACE_UNDEFINE = 'u'

# Listener:
BREAK = 'break'
RETURNCODE_BREAK = BREAK

# Fonts:
FONT = 'font'
FONT_WEIGHT_BOLD = 'bold'
FONT_WEIGHT_NORMAL = 'normal'
FONT_SLANT_ITALIC = 'italic'
FONT_SLANT_ROMAN = 'roman'
