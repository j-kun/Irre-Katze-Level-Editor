#!/usr/bin/env python

"""
fallback if tk_tooltip is not installed.
you can get it from http://tkinter.unpythonic.net/wiki/ToolTip
"""

class BalloonTip(dict):

    def __init__(self, *args, **kw):
        pass

    def configure(self, **kw):
        pass
