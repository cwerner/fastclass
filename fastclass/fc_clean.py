#!/usr/bin/env python 
#
# fastclass - fc_clean.py
# 
# Christian Werner, 2018-10-23

import click
import glob
import itertools
import os
from PIL import ImageTk, Image
import tkinter as tk
import shutil

from . imageprocessing import image_pad

EPILOG = """::: FastClass fcc :::\r
...a fast way to cleanup/ sort your images when building a\r
dataset for deep learning.\r
\r
Note:\r
In the application use the following keys:\r
<1>, <2>, ... <9> for class assignments or quality ratings\r
<space> assigns <1>\r
<d> to mark a deletion\r
<x> to terminate the app/ write output\r
\r
Use the buttons to navigate back and forth without changing\r
the classification. The current classification of an image\r
is given in the title bar (X indicated a mark for deletion).\r
The counter in the titlebar gives number of classified images\r
vs the total number in the input folder.\r

In the output csv file 1,2 depcit class assignments/ ratings, 
-1 indicates files marked for deletion (if not excluded with -d)."""


class AppTk(tk.Frame):
    def __init__(self, *args, **kwargs):

        INFOLDER = kwargs['infolder']
        OUTFOLDER = kwargs['outfolder']

        if OUTFOLDER:
            pass
        else:
            OUTFOLDER = INFOLDER + '.clean'
            os.makedirs(OUTFOLDER, exist_ok=True)

        NOCOPY = kwargs['nocopy']
 
        for e in ['infolder', 'outfolder', 'nocopy']:
            kwargs.pop(e)

        tk.Frame.__init__(self,*args,**kwargs)

        # bind keys
        args[0].bind('<Key>', self.callback)
        self.root = args[0]

        # store classification
        self._class = {f'c{c}': set() for c in range(1,10)}
        self._delete = set()

        # config settings
        suffixes = ['jpg', 'jpeg', 'png', 'tif', 'tiff']
        suffixes += [x.upper() for x in suffixes]
        files = list(itertools.chain(*[glob.glob(f'{INFOLDER}/*.{x}') for x in suffixes]))

        self.filelist = sorted(set(files))
        if len(self.filelist) == 0:
            print('No files in infolder.')
            exit(-1)

        self.outfolder = OUTFOLDER
        self.infolder = INFOLDER
        self.nocopy = NOCOPY

        self._classified = 0
        self._index=-1
        
        self.size = (299, 299)

        # basic setup
        self.setup()

        # raise window to top
        self.root.lift()
        self.root.attributes("-topmost", True)
        
        # show first image
        self.display_next()
    
    @property
    def total(self):
        return len(self.filelist)
        
    @property
    def classified(self):
        cnt = 0
        for c in '123456789':
            if self.filelist[self._index] in self._class[f'c{c}']:
                cnt += len(self._class[f'c{c}'])            
        if self.filelist[self._index] in self._delete: 
            cnt += len(self._delete)
        return cnt 

    @property
    def title(self):

        def get_class():
            for c in '123456789':
                if self.filelist[self._index] in self._class[f'c{c}']:
                    return f'[ {c} ] '
            if self.filelist[self._index] in self._delete: 
                return '[ X ] '
            return '[   ] '

        return (os.path.basename( self.filelist[self._index]) + 
                " - " +
                get_class() + 
                f" ({self.classified}/{self.total})")

    def print_titlebar(self):
        self.root.title(self.title)

    def callback(self, event=None):
        def button_action(char):
            self._class[f'c{char}'].add(self.filelist[self._index]) 
            self.display_next()

        if event.keysym in '123456789':
            button_action(event.keysym)
        elif event.keysym == 'space': #'<space>':
            button_action('1')
        elif event.keysym == 'd':
            self._delete.add(self.filelist[self._index])
            self.display_next()
        elif event.keysym == 'Left': #'<Left>':
            self.display_prev()
        elif event.keysym == 'Right': #'<Right>':
            self.display_next()
        elif event.keysym == "x":

            # write report file
            rows_all = []
            rows_clean = []
            for f in self.filelist:
                row = (f, '?')
                for c in '123456789':
                    if f in self._class[f'c{c}']:
                        row = (f, c)
                if f in self._delete: 
                    row = (f, 'D')
                else:
                    rows_clean.append(row) 
                rows_all.append(row)

            with open(os.path.join(self.infolder.replace(' ','_') + '_report_all.csv'), 'w') as f:
                f.write('file;rank\n')
                for row in rows_all: f.write(';'.join(row) + '\n')

            with open(os.path.join(self.infolder.replace(' ','_') + '_report_clean.csv'), 'w') as f:
                f.write('file;rank\n')
                for row in rows_clean: f.write(';'.join(row) + '\n')                

            if not self.nocopy:
                for r in rows_clean:
                    shutil.copy(r[0], self.outfolder)    

            self.root.destroy()
        else:
            pass

    def setup(self):
        self.Label=tk.Label(self)
        self.Label.grid(row=0, column=0, columnspan=6, rowspan=6) #, sticky=tk.N+tk.S)
        self.Button=tk.Button(self, text="Prev", command=self.display_prev)
        self.Button.grid(row=5, column=7, sticky=tk.S)
        self.Button=tk.Button(self, text="Next", command=self.display_next)
        self.Button.grid(row=5, column=8, sticky=tk.S)

    def display_next(self):
        self.print_titlebar()
        self._index+=1
        try:
            f=self.filelist[self._index]
        except IndexError:
            self._index=-1  #go back to the beginning of the list.
            self.display_next()
            return

        padded_im = image_pad(f, self.size)

        photoimage = ImageTk.PhotoImage(padded_im)
        self.Label.config(image=photoimage)
        self.Label.image=photoimage
        self.print_titlebar()

    def display_prev(self):

        self._index-=1
        try:
            f=self.filelist[self._index]
        except IndexError:
            self._index=-1  #go back to the beginning of the list.
            self.display_next()
            return

        padded_im = image_pad(f, self.size)

        photoimage = ImageTk.PhotoImage(padded_im)
        self.Label.config(image=photoimage)
        self.Label.image=photoimage
        self.print_titlebar()


def main(INFOLDER, OUTFOLDER, nocopy):
    root = tk.Tk()
    root.title('FastClass')
    
    app = AppTk(root, infolder=INFOLDER, outfolder=OUTFOLDER, nocopy=nocopy)

    app.grid(row=0,column=0)

    # start event loop
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)

    from os import system
    from platform import system as platform

    if platform() == 'Darwin':  # How Mac OS X is identified by Python
        script = 'tell application "System Events" \
        to set frontmost of the first process whose unix id is {pid} to true'.format(pid=os.getpid())
        os.system("/usr/bin/osascript -e '{script}'".format(script=script))

    root.mainloop()

# Cli - command line arguments
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
click.Context.get_usage = click.Context.get_help

@click.command(context_settings=CONTEXT_SETTINGS, epilog=EPILOG)

@click.option('--nocopy',  default=False, show_default=True,
                    help='disable filecopy for cleaned image set')

@click.argument('infolder', type=click.Path(exists=True), required=True)
@click.argument('outfolder', type=click.Path(exists=False), required=False)

def cli(infolder, outfolder, nocopy):
    """FastClass fcc"""

    main(infolder, outfolder, nocopy)

if __name__ == "__main__":
    cli()
