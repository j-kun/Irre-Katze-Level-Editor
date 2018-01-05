#!/usr/bin/env python

import os

import tkinter_extensions as tkx
tk  = tkx.tk
tkc = tkx.tkc
import gui_image_opener as imageOpener

import locales
_ = locales._

import model_object_catalog as objects
import model


class ObjectChoice(tk.Label):
    
    def __init__(self, catalog, name):
        tk.Label.__init__(self, master=catalog)
        self.catalog = catalog
        self.name = name
        self.lbl = "%03d (%s)" % (name, chr(name))
        self.img = imageOpener.getImage(name)
        self.configure(image=self.img, text=str(name), compound=tkc.COMPOUND_TOP)
        tkx.add_tooltip(self)
        tkx.set_text(self.tooltip, self.lbl)

    def __repr__(self):
        return self.name
    

class ObjectCatalog(tk.Frame):

    COLUMNS = 5

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)

        self.choices = list()
        self.objects = list(objects.getObjects())
        self.objects.sort()
        i = 0
        for obj in self.objects:
            c = ObjectChoice(self, obj)
            c.grid(column=i%self.COLUMNS, row=i//self.COLUMNS)
            if i < 3:
                self.choices.append(c)
            i += 1

if __name__=='__main__':
    root = tk.Tk()
    root.title(_("Object Catalog"))
    catalog = ObjectCatalog(root)
    catalog.pack()
    catalog.mainloop()
    print catalog.choices
