#!/usr/bin/env python

import os

import tkinter_extensions as tkx
tk  = tkx.tk
tkc = tkx.tkc
import gui_image_opener as imageOpener


class CatalogItem(tk.Canvas):

    PAD_X = 1
    PAD_Y = PAD_X
    
    DISTANCE_BASELINE = 18
    
    def __init__(self, catalog, name, imageOpener):
        tk.Canvas.__init__(self, master=catalog)
        self.catalog = catalog
        self.imageOpener = imageOpener
        self.name = name
        self.img = imageOpener.getImage(name)
        self.shortName = imageOpener.getShortName(name)
        self.longName = imageOpener.getLongName(name)
        self.idImg = self.create_image(0,0, image=self.img, anchor=tk.S)
        self.idBG  = None
        self.idLbl = self.create_text(0,self.DISTANCE_BASELINE, text=self.shortName, anchor=tk.S)
        bbox = self.bbox(tk.ALL)
        bbox = list(bbox)
        bbox[0] -= self.PAD_X
        bbox[2] += self.PAD_X
        bbox[1] -= self.PAD_Y
        bbox[3] += self.PAD_Y
        self.configure( width=bbox[2]-bbox[0], height=bbox[3]-bbox[1], scrollregion=bbox )
        tkx.add_tooltip(self)
        tkx.set_text(self.tooltip, self.longName)

    def updateShortName(self):
        self.shortName = self.imageOpener.getShortName(self.name)
        self.itemconfigure(self.idLbl, text=self.shortName)

    def showBackground(self, flag):
        if flag:
            # shall become visible
            
            if self.idBG != None:
                # is already visible
                return
            if not hasattr(self.imageOpener, "getBackground"):
                # can not create background
                return
            
            self.imgBackground = self.imageOpener.getBackground(self.name)
            self.idBG = self.create_image(0,0, image=self.imgBackground, anchor=tk.S)
            self.tag_lower(self.idBG)

        else:
            # shall be hidden

            if self.idBG == None:
                # is already invisible
                return

            self.delete(self.idBG)
            self.idBG = None

    def __repr__(self):
        return repr(self.name)


class Strut(tk.Label):

    def __init__(self, master):
        tk.Label.__init__(self, master, image = imageOpener.getImage(33),  text = " ", compound = tkc.COMPOUND_TOP)
    

class Catalog(tk.Frame):

    COLUMNS = 18

    ITEM_STRUT = 'strut'

    def __init__(self, master):
        tk.Frame.__init__(self, master)

    def setItems(self, items, imageOpener, onClickListener, onRightClickListener=None):
        for child in self.winfo_children():
            child.destroy()

        listener = lambda event: onClickListener(event, event.widget.name)
        listenerR = lambda event: onRightClickListener(event, event.widget.name)
        i = 0
        for item in items:
            if item ==self.ITEM_STRUT:
                child = Strut(self)
            else:
                child = CatalogItem(self, item, imageOpener)
                child.bind('<Button-1>', listener)
                if onRightClickListener != None:
                    child.bind('<Button-3>', listenerR)
            child.grid(column=i%self.COLUMNS, row=i//self.COLUMNS)
            i += 1

    def updateShortNames(self):
        for child in self.winfo_children():
            if isinstance(child, CatalogItem):
                child.updateShortName()

    def showBackground(self, flag):
        for child in self.winfo_children():
            if isinstance(child, CatalogItem):
                child.showBackground(flag)


if __name__=='__main__':
    import model_object_catalog as objects
    import model_background_catalog as backgrounds

    root = tk.Tk()
    root.title("Object Catalog")

    def onClick(event, name):
        print(name)
        switchCatalog()
    
    def switchCatalog(i=[0], isBackgroundVisibleCatalog=[False]):
        if i[0] % 3 == 2:
            catalog.setItems(backgrounds.CATEGORY_ALL, imageOpener.getBackground, onClick)
            label.configure(text="Background Catalog")
        elif i[0] % 3 == 1:
            isBackgroundVisibleCatalog[0] = not isBackgroundVisibleCatalog[0]
            catalog.showBackground( isBackgroundVisibleCatalog[0] )
        elif i[0] % 3 == 0:
            catalog.setItems(objects.CATEGORY_ALL, imageOpener.getImage, onClick)
            label.configure(text="Object Catalog")
            catalog.showBackground( isBackgroundVisibleCatalog[0] )
        else:
            assert False
        
        i[0] += 1
    
    label = tk.Label()
    label.pack(anchor=tk.W)
    catalog = Catalog(root)
    catalog.pack()
    switchCatalog()

    root.mainloop()
    
