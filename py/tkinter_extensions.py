#!/usr/bin/env python

# ========== libraries ==========
import system

# standard libraries
import logging
log = logging.getLogger(__name__)
if system.isPython2():
    # Python 2
    import Tkinter as tk
    try:
        import ttk
    except:
        # ttk does not exist on Mac
        logging.log(logging.WARNING, "Failed to load package ttk. Trying to use Tkinter instead.")
        ttk = tk
    import tkFileDialog
    import tkMessageBox
    import tkSimpleDialog
    import tkFont
else:
    # Python 3
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog, messagebox, simpledialog, font
    tkFileDialog = filedialog
    tkMessageBox = messagebox
    tkSimpleDialog = simpledialog
    tkFont = font
import time
import os.path

# other libraries
try:
    import tk_tooltip
except:
    import tk_tooltip_fake as tk_tooltip
    log.warning("did not find tk_tooltip library. tooltips are not displayed.")
ImageTk = tk
import tkinter_constants as tkc
import locales
_ = locales._


# ========== constants ==========

# I am not using the hack from
# taken from /usr/lib/python2.7/lib-tk/ScrolledText.py
# because it overrides too many methods.
# methods like Grid.columnconfigure are suppossed to be executed on self, obviously.
GM_METHODS_TO_BE_CALLED_ON_CHILD = (
    'pack', 'pack_configure', 'pack_forget', 'pack_info',
    'grid', 'grid_configure', 'grid_forget', 'grid_remove', 'grid_info',
    'place', 'place_configure', 'place_forget', 'place_info',
    'forget',
)


# ========== Klassenuebergreifende Funktionen ==========

def set_text(widget, text):
    if isinstance(widget, tk.Entry):
        widget.delete(0, tk.END)
        widget.insert(0, text)
    elif isinstance(widget, tk.Text):
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
    elif isinstance(widget, tk.StringVar):
        widget.set(text)
    elif isinstance(widget, tk.Label):
        widget[tkc.TEXT] = text
    elif isinstance(widget, tk_tooltip.ToolTip):
        widget[tkc.TEXT] = text
    else:
        log.error("set_text is not implemented for {0}".format(type(widget)))
        raise NotImplemented

def append_text(widget, text):
    set_text(widget, get_text(widget) + text)

def get_text(widget):
    if isinstance(widget, tk.Entry):
        return widget.get()
    elif isinstance(widget, tk.Text):
        return widget.get(1.0, tk.END+'-1c')
    elif isinstance(widget, tk.StringVar):
        return widget.get()
    elif isinstance(widget, tk.Label):
        return widget[tkc.TEXT]
    elif isinstance(widget, tk_tooltip.ToolTip):
        return widget[tkc.TEXT]
    else:
        raise NotImplemented


def add_tooltip(widget):
    #TODO: delay as setting
    widget.tooltip = tk_tooltip.ToolTip(widget, delay=500)


def is_open_window(window):
    if window==None:
        return False
    else:
        try:
            return window.winfo_exists()
        except tk.TclError:
            return False

def is_enabled(widget):
    return str(widget[tkc.STATE])!=tkc.STATE_DISABLED

def set_enabled(widget, enabled):
    widget[tkc.STATE] = tkc.STATE_NORMAL if enabled else tkc.STATE_DISABLED

def only(*x):
    '''returns 'break'. This can be used in a lambda expression bound to an event to break out of the event handling chain.'''
    return tkc.RETURNCODE_BREAK


def create_image(imagepath):
    if os.path.splitext(imagepath)[1]=='.xbm':
        image = tk.BitmapImage(file=imagepath)
    else:
        image = ImageTk.PhotoImage(file=imagepath)
    return image

# ========== abstract classes ==========

class WidgetWithContextMenu(object):

    default_contextmenu = None
    default_on_contextmenu_open = None
    _contextmenu_bind_sequence = '<Button-3>'

    def __init__(self):
        self._contextmenu_bind_id = None
        self.contextmenu = None
        self._on_contextmenu_open_listeners = set()
        if self.default_on_contextmenu_open!=None:
            self.add_on_contextmenu_open_listener(self.default_on_contextmenu_open)
    
    def process_keywordargs(self, kw):
        self._contextmenu = kw.pop('contextmenu', self.default_contextmenu)
        self._contextmenuadd = kw.pop('contextmenuadd', ())

    def set_contextmenu_from_keywordargs(self):
        menu = self._contextmenu
        if menu==None:
            log.warning("menu==None")
            return
        self.set_contextmenu(menu)

        menu = self._contextmenuadd
        if menu==None:
            return
        for item in menu:
            self.add_to_contextmenu(item)

    def has_contextmenu(self):
        return self._contextmenu_bind_id != None

    def remove_contextmenu(self):
        self.unbind(self._contextmenu_bind_sequence, self._contextmenu_bind_id)
        self._contextmenu_bind_id = None
        self.contextmenu = None

    def set_contextmenu(self, menu):
        '''menu: either tk.Menu|tkx.Menu or iterable like (("label 0", cmd0), ...)\nwith the second option, the function cmd0 gets one parameter: the object it self.'''
        #if self.has_contextmenu():
        #    self.remove_contextmenu()
        if isinstance(menu, tk.Menu):
            self.contextmenu = menu
        else:
            self.contextmenu = Menu(self, tearoff=0)
            for item in menu:
                self.add_to_contextmenu(item)

        if not self.has_contextmenu():
            self._contextmenu_bind_id = self.bind(sequence=self._contextmenu_bind_sequence, func=self.open_contextmenu, add=True)
        #log.debug("bound context menu to sequence {sequence!r} with id {id!r}." % (sequence=self._contextmenu_bind_sequence, id=self._contextmenu_bind_id)
        #TODO: remember focusable, set focusable

    def add_to_contextmenu(self, menuitem):
        '''menuitem: ((['id-0',] "label 0", cmd0), ...)'''
        if len(menuitem)==3:
            name, lbl, cmd = menuitem
        else:
            lbl, cmd = menuitem
            name = lbl
        if hasattr(cmd, '__call__'):
            self.contextmenu.add_named_command(name, label=lbl, command=lambda: cmd(self))
        else:
            #TODO
            raise NotImplemented("sub menus are not yet implemented")
        #else:
        #    lbl, cmd = menuitem
        #    self.contextmenu.add_command(label=lbl, command=cmd)

    def open_contextmenu(self, event):
        '''event must provide screen coordinates x_root and y_root'''
        for listener in self._on_contextmenu_open_listeners:
            listener()
        self.contextmenu.tk_popup(event.x_root, event.y_root)

    def add_on_contextmenu_open_listener(self, listener):
        '''listener: callable object with no parameters'''
        self._on_contextmenu_open_listeners.add(listener)

    def remove_on_contextmenu_open_listener(self, listener):
        self._on_contextmenu_open_listeners.remove(listener)
        

# ========== sub classes ==========


class AutoScrollbar(tk.Scrollbar):
    '''
    A scrollbar that hides itself if it's not needed. 
    Only works if you use the grid geometry manager.
    '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)

    def pack(self, *args, **kwargs):
        raise TclError('Cannot use pack with this widget.')

    def place(self, *args, **kwargs):
        raise TclError('Cannot use place with this widget.')



class Checkbutton(tk.Checkbutton):
    def __init__(self, master=None, cnf={}, **kwargs):
        value = kwargs.pop('value', None)
        command = kwargs.pop('command', None)
        # original command argument is *not* always called! works with mouse-click and invoke but not whith set_value and toggle
        if 'variable' in kwargs:
            self.var = kwargs['variable']
        else:
            self.var = tk.BooleanVar()
            kwargs['variable'] = self.var
        tk.Checkbutton.__init__(self, master, cnf, **kwargs)
        if value!=None:
            self.set_value(value)
        self._slaves = set()
        self.var.trace("w", self._on_change) # w means when variable is written
        if command!=None:
            self.var.trace("w", lambda varname=None, index=None, operation=None: command())

    def get_value(self):
        return bool(self.var.get())

    def set_value(self, value):
        self.var.set(1 if value else 0)

    def trace(self, command):
        '''command(new_value) will be called when value changes'''
        self.var.trace(tkc.TRACE_WRITE, lambda varname,index,operation: command(self.get_value()))

    def add_slave(self, widget):
        """widget will be enabled|disabled as this checkbutton is checked|unchecked"""
        self._slaves.add(widget)
        widget[tkc.STATE] = self._get_slaves_state()

    def _get_slaves_state(self):
        if self.get_value():
            return tkc.STATE_NORMAL
        else:
            return tkc.STATE_DISABLED

    def _on_change(self, varname=None, index=None, operation=None):
        state = self._get_slaves_state()
        for widget in self._slaves:
            widget[tkc.STATE] = state


class Menubutton(ttk.Menubutton):
    
    def __init__(self, master=None, **kw):
        KEY_DEFAULT_VALUE = 'default'
        KEY_DEFAULT_VALUE_ID = 'defaultid'
        values = kw.pop('values', None)
        default = kw.pop(KEY_DEFAULT_VALUE, None)
        default_id = kw.pop(KEY_DEFAULT_VALUE_ID, None)
        if kw.pop("autofixedwidth", 'width' not in kw):
            kw['width'] = self._get_auto_width(values)
        tearoff = kw.pop('tearoff', False)
        kw.setdefault('direction', 'flush') # 'flush', 'below' #TODO: test which one is better on windows. Settings?
        ttk.Menubutton.__init__(self, master, **kw)
        self.menu = tk.Menu(self, tearoff=tearoff)
        self.configure(menu=self.menu)
        self.set_values(values)
        if default!=None:
            if default_id!=None:
                raise TypeError("got value for keywords {0} and {1} but you can only specify one of them".format(KEY_DEFAULT_VALUE, KEY_DEFAULT_VALUE_ID))
            self.set_value(default)
        elif default_id!=None:
            self.set_value_id(default_id)
            

    def _get_auto_width(self, values):
        width = 0
        if values!=None:
            for v in values:
                width = max(len(v), width)
        return width

    def set_values(self, values, current_value_id=0):
        self.values = values
        self.menu.delete(0, tk.END)
        if self.values!=None and len(self.values)>0:
            self.set_value_id(current_value_id)
            for i in range(len(values)):
                v = self.values[i]
                self.menu.add_command(label=v, command=lambda i=i: self.set_value_id(i))
        else:
            self._current_value_id = None

    def get_values(self):
        return self.values

    def set_value(self, value):
        self.set_value_id(self.values.index(value))
        
        
    def set_value_id(self, index):
        if self.values==None:
            raise ValueError("cannot set current value because it has no values at all")
        elif not 0 <= index < len(self.values):
            raise IndexError("values with length of {n} has no index {i}".format(n=len(self.values), i=index))
        self._current_value_id = index
        self[tkc.TEXT] = self.values[self._current_value_id]

    def get_value(self):
        if self._current_value_id == None:
            return None
        else:
            return self.values[self._current_value_id]

    def get_value_id(self):
        return self._current_value_id


RETURN_CODE_BREAK = "break"


class Entry(tk.Entry, WidgetWithContextMenu):
    def __init__(self, master=None, **kw):
        text = kw.pop('text', None)
        if tkc.TEXTVARIABLE in kw:
            self.var = kw[tkc.TEXTVARIABLE]
        else:
            self.var = tk.StringVar()
            kw[tkc.TEXTVARIABLE] = self.var
        WidgetWithContextMenu.__init__(self)
        self.process_keywordargs(kw)
        tk.Entry.__init__(self, master, **kw)
        self.set_contextmenu_from_keywordargs()
        if text:
            self.set_value(self, text, force=True)

    def get_value(self):
        return get_text(self)

    def set_value(self, text, force=True):
        '''force=True: set text regardless of state. force=False: does *not* set text if state is disabled.'''
        if force:
            self.var.set(text)
        else:
            self.delete(0, tk.END)
            self.insert(0, text)

    def text_copy_selection(self, event=None):
        '''copies the selection to clipboard if text is selected,\ndoes nothing otherwise.\nreturn: true if it has copied to clipboard, false if nothing was selected.'''
        if self.selection_present():
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
            return True
        return False

    def text_delete_selection(self, event=None):
        '''deletes the selected text if text is selected,\ndoes nothing otherwise.\nreturn: true if it has deleted, false if nothing was selected.'''
        try:
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return False
        return True

    def text_paste(self, event=None):
        '''pastes text from clipboard if can_paste() returns True. replaces the current selection if text is selected. Returns true if text has been pasted.'''
        if self.can_paste():
            self.text_delete_selection()
            self.insert(tk.INSERT, self.clipboard_get())
            return True
        return False

    def can_paste(self):
        '''True if clipboard is not empty'''
        try:
            return self.clipboard_get()!=''
        except tk.TclError:
            return False


class Button(tk.Button):
    def __init__(self, master=None, **kw):
        imagepath = kw.pop('imagepath', None)
        tk.Button.__init__(self, master, **kw)
        if imagepath!=None:
            self.image = create_image(imagepath)
            self.configure(image=self.image)

class ButtonsFrame(tk.Frame):

    BTN_OK     = 'ok'
    BTN_YES    = 'yes'
    BTN_NO     = 'no'
    BTN_CANCEL = 'cancel'
    
    def __init__(self, master, **kw):
        '''This frame should be packed to fill x direction.
            If default=True (and it is initially True) the yes or ok button will be marked as the default button (unless the keyword arguments for the buttons suggest otherwise).
            If a button is marked as default it is bound to the <Return> event on the toplevel window.
            If escape=True (and it is initially True) the event <Escape> will be bound to the cancel button on the toplevel window (if there is a cancel button).'''
        #TODO: padding
        default = kw.pop(tkc.DEFAULT, True)
        escape  = kw.pop('escape', True)
        kw_cancel = kw.pop(self.BTN_CANCEL, None)
        if self.BTN_YES in kw:
            mode = self.BTN_YES
            kw_yes = kw.pop(self.BTN_YES)
            kw_no  = kw.pop(self.BTN_NO)
            if default and not tkc.DEFAULT_ACTIVE in (
                    kw_yes.get(tkc.DEFAULT, tk.DISABLED),
                    kw_no.get(tkc.DEFAULT, tk.DISABLED),
                    kw_cancel.get(tkc.DEFAULT, tk.DISABLED) if kw_cancel!=None else tk.DISABLED,
            ):
                kw_yes.setdefault(tkc.DEFAULT, tkc.DEFAULT_ACTIVE)
        else:
            mode = self.BTN_OK
            kw_ok = kw.pop(self.BTN_OK)
            if default and not tkc.DEFAULT_ACTIVE in (
                    kw_ok.get(tkc.DEFAULT, tk.DISABLED),
                    kw_cancel.get(tkc.DEFAULT, tk.DISABLED) if kw_cancel!=None else tk.DISABLED,
            ):
                kw_ok.setdefault(tkc.DEFAULT, tkc.DEFAULT_ACTIVE)

        tk.Frame.__init__(self, master, **kw)

        if kw_cancel!=None:
            self.button_cancel = Button(self, **kw_cancel)
        else:
            self.button_cancel = None

        # I am using the same order like tkMessageBox
        if mode==self.BTN_YES:
            self.button_yes = Button(self, **kw_yes)
            self.button_no  = Button(self, **kw_no)
            self._bind_if_default(self.button_yes) or self._bind_if_default(self.button_no) or self._bind_if_default(self.button_cancel)
            if system.isMac():
                self.button_yes.pack(side=tk.RIGHT)
                self.button_no.pack(side=tk.RIGHT)
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.LEFT)
            else:
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
                self.button_no.pack(side=tk.RIGHT)
                self.button_yes.pack(side=tk.RIGHT)
        else:
            self.button_ok = Button(self, **kw_ok)
            self._bind_if_default(self.button_ok) or self._bind_if_default(self.button_cancel)
            if system.isMac():
                self.button_ok.pack(side=tk.RIGHT)
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
            else:
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
                self.button_ok.pack(side=tk.RIGHT)
        if escape and self.button_cancel!=None:
            self.winfo_toplevel().bind('<Escape>', lambda e: only(self.button_cancel.invoke()))

    def _bind_if_default(self, btn):
        if btn==None:
            return False
        if btn[tkc.DEFAULT]==tkc.DEFAULT_ACTIVE:
            log.debug("bind default button: {0!r}".format(btn['text']))
            self.winfo_toplevel().bind('<Return>', lambda e: only(btn.invoke()))
            return True
        return False



class SmallCloseButton(tk.Button):

    XBM_DATA = """
#define x_width 11
#define x_height 11
static unsigned char x_bits[] = {
   0x01, 0x04, 0x02, 0x02, 0x04, 0x01, 0x88, 0x00, 0x50, 0x00, 0x20, 0x00,
   0x50, 0x00, 0x88, 0x00, 0x04, 0x01, 0x02, 0x02, 0x01, 0x04 };
   """

    def __init__(self, master, **kw):
        self.img = tk.BitmapImage(data=self.XBM_DATA)
        kw.setdefault('relief', tkc.RELIEF_FLAT)
        kw.setdefault('highlightthickness', 0)
        tk.Button.__init__(self, master, image=self.img, **kw)


class FrameWithTitle(tk.Frame):

    KEY_TITLE_BG = 'titlebackground'

    def __init__(self, master=None, **kwargs):
        kwargs.setdefault('padx', 1)
        kwargs.setdefault('relief', tkc.RELIEF_GROOVE)
        kwargs.setdefault('borderwidth', 2)
        titleBG = kwargs.pop(self.KEY_TITLE_BG, 'gray')
        
        kwParent = dict()
        for key in ('borderwidth', 'bd', 'relief'):
            if key in kwargs:
                kwParent[key] = kwargs.pop(key)
        self.frameParent = tk.Frame(master, **kwParent)
        closecommand = kwargs.pop('closecommand', self.frameParent.forget)
        tk.Frame.__init__(self, self.frameParent, **kwargs)

        padx = kwargs.get('padx', 0)
        pady = padx
        self.canvasTitle = tk.Canvas(self.frameParent, bg=titleBG)
        self.canvasTitle.pack(side=tk.TOP, expand=tk.NO, fill=tk.X)
        self.labelTitle = tk.Label(self.canvasTitle, bg=self.canvasTitle['bg'])
        self.labelTitle.pack(side=tk.LEFT, padx=padx, pady=pady)
        tk.Frame(self.canvasTitle, bg=self.canvasTitle['bg'], width=20).pack(side=tk.LEFT)
        self.closeButton = SmallCloseButton(self.canvasTitle, bg=self.canvasTitle['bg'], command=closecommand, takefocus=False)
        self.closeButton.pack(side=tk.RIGHT, padx=padx, pady=pady)
        
        self.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

        for m in GM_METHODS_TO_BE_CALLED_ON_CHILD:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frameParent, m))

    def title(self, title):
        self.labelTitle.configure(text=title)

    def getTitle(self):
        return get_text(self.labelTitle)

##    def __init__(self, master=None, **kwargs):
##        #tkText.Text.pack(self, side=tk.TOP, fill=tkText.BOTH, expand=True)
##        self.notebook = ttk.Notebook(master, takefocus=False)
##        tk.Frame.__init__(self, self.notebook, **kwargs)
##
##        self.notebook.add(self)
##
##        for m in GM_METHODS_TO_BE_CALLED_ON_CHILD:
##            if m[0] != '_' and m != 'config' and m != 'configure':
##                setattr(self, m, getattr(self.notebook, m))
##
##    def title(self, title):
##        self.notebook.tab(0, text=title)


class Menu(tk.Menu):

    _PREFIX_INDEX = '_index_'
    _PREFIX_MENU = 'menu_'

    tearoff = False

    def __init__(self, master=None, **kw):
        if tkc.KEY_TEAROFF not in kw:
            kw[tkc.KEY_TEAROFF] = self.tearoff
        self._widgetToBindTo = kw.pop('widgetToBindTo', master)
        tk.Menu.__init__(self, master, kw)

    def add_named_command(self, name, **kw):
        kw.setdefault('label', name)
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        event = kw.pop('event', None)
        self.add_command(**kw)
        if event != None:
            self.bindElement(name, event)

    def add_named_checkbutton(self, name, **kw):
        if 'variable' in kw:
            var = kw['variable']
        else:
            var = tk.BooleanVar(value=kw.pop('value', False))
            kw['variable'] = var
        command = kw.pop('command', None)
        statevar = kw.pop('statevariable', None)
        event = kw.pop('event', None)
        
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        setattr(self, self._PREFIX_INDEX+name+'_variable', var)
        self.add_checkbutton(**kw)
        
        if command != None:
            var.trace(tkc.TRACE_WRITE, lambda varname,index,operation: command(bool(var.get())))
        
        if statevar != None:
            stateListener = lambda a,b,c: self.entry_enable(name) if statevar.get() else self.entry_disable(name)
            stateListener(None, None, None)
            statevar.trace('w', stateListener)
        
        if event != None:
            self.bindElement(name, event, wrapper=only)

    def bindElement(self, name, eventSequence, wrapper=lambda x: x):
        self._widgetToBindTo.bind(eventSequence, lambda e: wrapper(self.invoke(name)))
        self.entryconfigure(name, accelerator=self.eventSequenceToAccelerator(eventSequence))

    _KEY_NAMES = dict(
        Control = _('Ctrl'),
        Alt     = _('Alt'),
        Shift   = _('Shift'),
    )

    @classmethod
    def eventSequenceToAccelerator(cls, eventSequence):
        accelerator = eventSequence.lstrip('<').rstrip('>')
        accelerator = accelerator.split('-')

        # last key
        if len(accelerator[-1]) == 1:
            if accelerator[-1].isupper():
                accelerator.insert(-1, 'Shift')
            else:
                accelerator[-1] = accelerator[-1].upper()
        else:
            if accelerator[-1] in tkc.KEY_SYMBOLS:
                accelerator[-1] = tkc.KEY_SYMBOLS[accelerator[-1]]

        # modifiers
        if not system.isMac():
            for i in range(len(accelerator)-1):
                if accelerator[i] in cls._KEY_NAMES:
                    accelerator[i] = cls._KEY_NAMES[accelerator[i]]
        
        accelerator = '+'.join(accelerator)
        return accelerator

    def set_named_checkbutton(self, name, value):
        var = getattr(self, self._PREFIX_INDEX+name+'_variable')
        var.set(value)

    def get_named_checkbutton(self, name):
        var = getattr(self, self._PREFIX_INDEX+name+'_variable')
        return var.get()

    def add_named_cascade(self, name, **kw):
        menu = kw.pop(tkc.KEY_MENU, None)
        if menu==None:
            tearoff = kw.pop(tkc.KEY_TEAROFF, self.tearoff)
            menu = Menu(self, tearoff=tearoff, widgetToBindTo=self._widgetToBindTo)
        kw[tkc.KEY_MENU] = menu
        visible = bool(kw.pop('visible', True))
        menu.label = kw['label']
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        setattr(self, self._PREFIX_MENU+name, menu)
        if visible:
            self.add_cascade(**kw)
        menu._visible = visible
        return menu

    def set_cascade_visibility(self, menu, visible):
        visible = bool(visible)
        if visible == menu._visible:
            return
        if visible:
            self.add_cascade(menu=menu, label=menu.label)
            menu._visible = True
        else:
            self.delete(menu.label)
            menu._visible = False


    def entryconfig(self, name, **kw):
        i = self.to_index(name)
        if 'label' in kw:
            setattr(self, self._PREFIX_INDEX+name, kw['label'])
        tk.Menu.entryconfig(self, i, **kw)
    entryconfigure = entryconfig

    def entrycget(self, name, option):
        i = self.to_index(name)
        return tk.Menu.entrycget(self, i, option)
            

    def entry_disable(self, name):
        self.entryconfig(name, state=tk.DISABLED)

    def entry_enable(self, name):
        self.entryconfig(name, state=tk.NORMAL)

    def set_entry_enabled(self, name, enabled):
        if enabled:
            self.entry_enable(name)
        else:
            self.entry_disable(name)

    def entries_disable(self, *names):
        for name in names:
            self.entry_disable(name)

    def entries_enable(self, *names):
        for name in names:
            self.entry_enable(name)

    def invoke(self, btn):
        i = self.to_index(btn)
        tk.Menu.invoke(self, i)

    def to_index(self, name):
        if isinstance(name, int) or name==tk.END:
            return name
        else:
            return getattr(self, self._PREFIX_INDEX+name)

    def shortcut(self, name, key):
        '''create a shortcut Alt+key by underlining one character of the label. This is mainly intended for the main-menus of the window-menubar. If key is not contained in the label, no shortcut can be created. In that case an error is logged and this function returns False.'''
        label = self.entrycget(name, 'label')
        i = label.find(key)
        if i<0:
            i = label.find(key.swapcase())
        if i<0:
            log.error("cannot create shortcut {key!r} to menu entry {label!r} because key is not contained in label".format(key=key, label=label))
            return False
        self.entryconfig(name, underline=i)
        return True

    def open_menu(self, menu):
        log.debug("open_menu({menu})".format(menu=menu.label))
        #TODO: pause update screen in this function (is that even possible?)
        # init
        focussed_widget = self.focus_displayof()
        t = tk.Toplevel(menu)
        t.overrideredirect(True)
        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        x += self.master.winfo_width()
        if not hasattr(menu, 'width'):
            menu.tk_popup(x,y)
            menu.width = menu.winfo_width()
            #print("background: "+menu.entrycget(0, 'background'))
            #print("activebackground: "+menu.entrycget(0, 'activebackground'))
            menu.unpost()
            menu.update()
        padding = 6
        l = tk.Label(t, text=menu.label, relief=tkc.RELIEF_RAISED, padx=padding, pady=padding)
        l['background'] = l['activebackground']
        l.pack()
        t.update_idletasks()
        t.width = t.winfo_width()
        t.height = t.winfo_height()

        # correct setup
        t.geometry('{width}x{height}+{x}+{y}'.format(x=x-t.width, y=y-t.height, width=t.width, height=t.height))
        menu.tk_popup(x-menu.width,y)
        menu.focus_force()# yes, I really need a focus_force here because the update above seems to pass the focus to a different application
        def close(event=None):
            log.debug("close")
            menu.unbind('<Escape>', fid_esc) # to avoid conflict when menu is opened normally
            menu.unbind('<FocusOut>', fid_foc) # to avoid double close
            #menu.unbind('<Button-1>', fid_clk) # to avoid double close
            #TODO: menu_open, Escape, Alt-f, Escape returns focus but does not close menu
            menu.unpost()
            t.destroy()
            focussed_widget.focus()
            return tkc.BREAK
        fid_esc = menu.bind('<Escape>', close, add=True)
        fid_foc = menu.bind('<FocusOut>', close, add=True)
        #menu.bind('<Button-1>', lambda event: None, add=True)
        #TODO: does not close on FIRST open
        l.bind('<Button-1>', close)
        self.update()


# ========== other classes ==========

# http://effbot.org/zone/tkinter-busy.htm
class CursorManager(object):

    def __init__(self, widget, set_cursor=tkc.CURSOR_WATCH, reset_cursor=tkc.CURSOR_ARROW):
        self.toplevel = widget.winfo_toplevel()
        self.default_set_cursor = set_cursor
        self.default_reset_cursor = reset_cursor
        self._w_cursors = dict()
        self._is_cursor_changed = False

    def set_cursor(self, cursor=None, widget=None):
        if cursor is None:
            cursor = self.default_set_cursor
        if widget is None:
            w = self.toplevel
        else:
            w = widget

        #log.debug("=====   set cursor =====")
        self._is_cursor_changed = True
        try:
            w_cursor = w.cget(tkc.KEY_CURSOR)
            if w_cursor != cursor:
                # originally it was str(w).
                # however str(ScrolledText)==str(ScrolledText.frame) # how can that be???
                # repr(ScrolledText)!=repr(ScrolledText.frame) # if this is not valid for str, are there exceptions for repr, too?
                # id(ScrolledText)!=id(ScrolledText.frame) # is this more difficult than str or repr?
                key = repr(w)
                if key not in self._w_cursors:
                    self._w_cursors[key] = (w, w_cursor) #TODO: only if not contained
                    #log.debug("set cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=cursor))
                else:
                    log.debug("{widget!r} already contained".format(widget=w))
                w.config(cursor=cursor)
        except tk.TclError:
            log.warning("failed to set cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=cursor))
        
        for w in w.children.values():
            self.set_cursor(cursor, w)

    def reset_cursor(self):
        log.debug("===== reset cursor =====")
        self._is_cursor_changed = False
        for w, w_cursor in self._w_cursors.values():
            if w_cursor=="":
                w_cursor = self.default_reset_cursor
            try:
                w.config(cursor=w_cursor)
                #log.debug("reset cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=w_cursor))
            except tk.TclError:
                log.warning("failed to reset cursor for {widget!r}".format(widget=w))
        self._w_cursors = dict()

    def is_cursor_changed(self):
        return self._is_cursor_changed


class MousewheelBinder(object):

    def __init__(self, widget, yview_scroll=None):
        self.widget = widget
        if yview_scroll == None:
            self.yview_scroll = self.widget.yview_scroll
        else:
            self.yview_scroll = yview_scroll

        self.widget.bind('<Enter>', self._bindMousewheel)
        self.widget.bind('<Leave>', self._unbindMousewheel)

    def _bindMousewheel(self, event):
        # Windows
        self.widget.bind_all('<MouseWheel>', self._onMousewheel)
        # Linux
        self.widget.bind_all('<Button-4>', self._onMousewheel)
        self.widget.bind_all('<Button-5>', self._onMousewheel)

    def _unbindMousewheel(self, event):
        # Windows
        self.widget.unbind_all('<MouseWheel>')
        # Linux
        self.widget.unbind_all('<Button-4>')
        self.widget.unbind_all('<Button-5>')

    def _onMousewheel(self, event):
        if event.delta < 0 or event.num == 5:
            dy = +1
        elif event.delta > 0 or event.num == 4:
            dy = -1
        else:
            assert False

        if (dy < 0 and self.widget.yview()[0] > 0.0) \
        or (dy > 0 and self.widget.yview()[1] < 1.0):
            self.yview_scroll(dy, tk.UNITS)
        
        return tkc.RETURNCODE_BREAK


class KeyBinder(object):

    TIMEOUT_FIRST = 1
    TIMEOUT = .1
    ACCURACY = .99

    WIDGET = '_widget'
    LAST_TIME = 'lastTime'
    PRESS_COUNT = 'pressCount'
    AFTER_ID = 'afterID'

    ON_PRESS = 'onPress'
    ON_RELEASE = 'onRelease'

    def __init__(self, widget):
        self.widget = widget
        self.onPress = dict()
        self.onRelease = dict()

    def bindToKey(self, key, onPress, onRelease):
        self.onPress[key] = onPress
        self.onRelease[key] = lambda: self.callRelease(key, onRelease)
        self.reset()
        
        self.widget.bind('<KeyPress-{0}>'.format(key), lambda e: self.onPressEvent(e, key))
        self.widget.bind('<KeyRelease-{0}>'.format(key), lambda e: self.onReleaseEvent(e, key))

    __call__ = bindToKey

    def reset(self):
        self.lastTime   = 0
        self.pressCount = 0
        self.afterID    = None

    def callRelease(self, key, func):
        self.reset()
        func(key)

    
    def onReleaseEvent(self, event, key):
        now = time.time()
        if self.pressCount >= 2 \
            or ( self.afterID != None  and  now - self.lastTime >= self.TIMEOUT * self.ACCURACY ) \
            or now - self.lastTime >= self.TIMEOUT_FIRST * self.ACCURACY:
            self.onRelease[key]()
        else:
            if self.afterID!= None:
                self.widget.after_cancel(self.afterID)
            self.afterID = self.widget.after(int(1000*self.TIMEOUT), self.onRelease[key])
            self.lastTime = now
        self.pressCount = 0
        return tkc.RETURNCODE_BREAK

    def onPressEvent(self, event, key):
        now = time.time()
        if self.afterID == None:
            if now - self.lastTime >= self.TIMEOUT * self.ACCURACY:
                self.onPress[key](key)
        else:
            self.widget.after_cancel(self.afterID)
            self.afterID = self.widget.after(int(1000*self.TIMEOUT), self.onRelease[key])
        self.pressCount += 1
        self.lastTime = now
        return tkc.RETURNCODE_BREAK


# ========== test ==========

if __name__=='__main__':
    import sys
    logging.basicConfig(level=0, format="[%(levelname)-8s] %(message)s", stream=sys.stdout, disable_existing_loggers=True)
    import time
    #_ = lambda x: x
    toggle_readonly = True
    class Test:
        i = 0
        def fill(self):
            b = buttons_frame.button_ok
            b[tkc.TEXT] = "pause"
            b[tkc.COMMAND] = self.pause
            if toggle_readonly: t.readonly(True)
            menu_edit.entries_disable('add', 'remove')
            self.is_running = True
            while self.is_running:
                t.append(str(self.i)+"\n")
                self.i += 1
                if self.i<25:
                    continue
                for i in xrange(10):
                    t.update()
                    time.sleep(0.1)


        def pause(self):
            b = buttons_frame.button_ok
            self.is_running = False
            b[tkc.TEXT] = "continue"
            b[tkc.COMMAND] = self.fill
            if toggle_readonly: t.readonly(False)
            menu_edit.entries_enable('add', 'remove')

    AutoScrolledText.default_contextmenu = (
        ('copy', 'copy', AutoScrolledText.text_copy_selection),
        ('paste', 'paste', AutoScrolledText.text_paste)
    )
    def on_contextmenu_open(self):
        self.contextmenu.set_entry_enabled('copy', self.selection_present())
        self.contextmenu.set_entry_enabled('paste', self.can_paste())
    AutoScrolledText.default_on_contextmenu_open = on_contextmenu_open
    AutoScrolledText.default_on_readonly_enabled = lambda self: self.contextmenu.entry_disable('paste')
    AutoScrolledText.default_on_readonly_disabled = lambda self: self.contextmenu.set_entry_enabled('paste', self.can_paste())

    LabelSelectable.default_contextmenu = (
        ('copy', 'copy', LabelSelectable.text_copy_selection),
    )

    def ask_to_close():
        t = tk.Toplevel()
        LabelSelectable(t, text="Are you sure you want to quit?").pack()
        ButtonsFrame(t,
            yes = dict(text="Yes", command=lambda: only(t.destroy(), r.destroy(), r.quit())),
            no  = dict(text="No", command=lambda: only(t.destroy())),
            cancel = dict(text="Cancel", command=lambda: only(t.destroy()))
        ).pack(side=tk.BOTTOM, fill=tk.X)

    def toggle():
        logging.info("toggle")
        label = menu_toggle.entrycget('toggle', 'label')
        if label == 'False':
            label = "True"
        else:
            label = "False"
        menu_toggle.entryconfig('toggle', label=label)

    m = Test()
    r = tk.Tk()
    t = AutoScrolledText(r,
        readonly=not toggle_readonly,
        #on_readonly_enabled = lambda self: self.contextmenu.entries_disable('*')
    )
    
    menu = Menu(r, widgetToBindTo=t)
    menu_file = menu.add_named_cascade('file', label="File")
    menu_file.add_named_command('save', label="Save", command=lambda: log.info("save"), event='<Control-s>')
    menu_file.add_named_command('saveAs', label="Save As...", command=lambda: log.info("save as"), event='<Control-S>')
    menu_file.add_named_command('open', label="Open...", command=lambda: log.info("open"), event='<Control-o>')
    menu_edit = menu.add_named_cascade('edit', label="Edit")
    menu_edit.add_named_command('add', label="Add", command=lambda: log.info("add"), event='<Control-plus>')
    menu_edit.add_named_command('remove', label="Remove", command=lambda: log.info("rm"), event='<Control-minus>')
    menu_toggle = menu.add_named_cascade('toggle', label="Toggle")
    menu_toggle.add_named_command('fake0', label='Fake 0')
    menu_toggle.add_named_command('toggle', command=toggle, event='<Control-space>')
    menu_toggle.add_named_command('fake1', label='Fake 1')
    menu_toggle.entryconfig('toggle', label='True')
    menu.shortcut('file', 'f')
    menu.shortcut('edit', 'e')
    r.bind('<Control-f>', lambda event: menu.open_menu(menu_file))
    r.bind('<Control-e>', lambda event: menu.open_menu(menu_edit))
    
    r.config(menu=menu)
    l = LabelSelectableWithLabel(r,
        text="bla bla bla",
        #imagepath="symbole/resized/count.png"
    )# textvariable=tk.StringVar(value="some test app:"))
    l.pack(side=tk.TOP, fill=tk.X)
    t.pack(expand=True, fill=tk.BOTH)
    details = DetailsFrame(r, label='Details', label_expand='Expand Details', label_collapse='Collapse Details')
    details.pack(expand=True, fill=tk.X)
    LabelSelectable(details, text="This is just a test. Nothing more.").pack(side=tk.LEFT)
    buttons_frame = ButtonsFrame(r,
        ok = dict(text="Start", command=m.fill),
        cancel = dict(text="Close", command=ask_to_close)
    )
    buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)

    sideFrame = FrameWithTitle(r, padx=5, pady=5)
    sideFrame.title("Information")
    sideFrame.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.BOTH, before=l)
    sideFrame.columnconfigure(1, weight=1)
    for i in range(10):
        l = tk.Label(sideFrame, text="information %s" % i)
        b = SmallCloseButton(sideFrame)
        l.grid(row=i, column=0, sticky=tk.W)
        b.grid(row=i, column=1, sticky=tk.E)
        def rmRow(l=l, b=b):
            l.grid_forget()
            b.grid_forget()
        b.configure(command=rmRow)
        
        
        #l.pack(anchor=tk.W)
    r.mainloop()
